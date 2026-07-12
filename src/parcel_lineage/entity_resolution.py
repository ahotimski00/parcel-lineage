"""Resolve messy county parcel owner strings to their controlling parent entity.

County tax rolls record the same company under many spellings ("ACME TIMBER
LLC", "Acme Timber, L.L.C.", "ACME TIMBERR LLC") and bury the true owner under
tiers of shell LLCs. This module reconciles raw owner strings against a known
corporate-family table and rolls each match up to its ultimate parent.

The public entry point is :func:`resolve_owners`.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd
from rapidfuzz import fuzz, process


@dataclass(frozen=True)
class ResolverConfig:
    """Configuration for a resolution run.

    threshold: minimum fuzzy score (0-100) to auto-accept a child-LLC match.
        Anything below is kept but flagged ``needs_review`` so a human confirms
        it before it is trusted downstream.
    scorer: rapidfuzz scorer. ``token_sort_ratio`` is order-insensitive, which
        handles "TIMBER ACME LLC" vs "ACME TIMBER LLC".
    """

    threshold: float = 90.0
    scorer: Callable[[str, str], float] = fuzz.token_sort_ratio


# Unambiguous legal-entity suffixes, dropped before matching so that
# "Northway Forests" and "Northway Forests LLC" compare as the same core name.
# Deliberately excludes meaningful words like TRUST, CLUB, or ASSOCIATION.
LEGAL_TOKENS = frozenset(
    {"LLC", "INC", "CO", "CORP", "CORPORATION", "LP", "LLP", "LTD", "COMPANY", "INCORPORATED"}
)


def _normalize(name: str, drop_tokens: frozenset[str] = frozenset()) -> str:
    """Cheap, deterministic cleanup applied before fuzzy scoring.

    ``drop_tokens`` removes whole tokens (typically legal suffixes like LLC or
    INC) so the distinctive part of the name drives the match.
    """
    text = name.upper().strip().replace(",", " ").replace(".", "")
    # Collapse common legal-suffix spellings to one token before splitting.
    for variant in ("L L C", "LIMITED LIABILITY COMPANY"):
        text = text.replace(variant, "LLC")
    tokens = [t for t in text.split() if t not in drop_tokens]
    return " ".join(tokens)


def resolve_owners(
    raw_owners: pd.Series,
    family: pd.DataFrame,
    config: ResolverConfig | None = None,
) -> pd.DataFrame:
    """Map raw owner strings to a canonical child LLC and its ultimate parent.

    Parameters
    ----------
    raw_owners:
        Series of owner strings as they appear in the parcel roll.
    family:
        Corporate-family table with at least ``child_llc`` and ``parent_llc``
        columns, built from public LLC filings.
    config:
        Optional :class:`ResolverConfig`.

    Returns
    -------
    DataFrame indexed like ``raw_owners`` with columns:
    ``raw_owner``, ``matched_child``, ``parent``, ``score``, ``needs_review``.
    """
    config = config or ResolverConfig()

    children = family["child_llc"].tolist()
    normalized_children = [_normalize(c) for c in children]
    child_to_parent = dict(zip(family["child_llc"], family["parent_llc"]))

    records = []
    for raw in raw_owners:
        query = _normalize(raw)
        # rapidfuzz's scorer protocol is stricter than a plain 2-arg callable;
        # the config type keeps the public surface simple.
        match = process.extractOne(
            query, normalized_children, scorer=config.scorer  # type: ignore[arg-type]
        )
        # extractOne returns (choice, score, index) or None if choices empty.
        if match is None:
            records.append((raw, None, None, 0.0, True))
            continue
        _, score, idx = match
        child = children[idx]
        records.append(
            (
                raw,
                child,
                child_to_parent[child],
                float(score),
                score < config.threshold,
            )
        )

    return pd.DataFrame(
        records,
        index=raw_owners.index,
        columns=["raw_owner", "matched_child", "parent", "score", "needs_review"],
    )


def cluster_owners(
    owners: pd.Series,
    *,
    threshold: float = 92.0,
    scorer: object = fuzz.token_sort_ratio,
    drop_tokens: frozenset[str] = LEGAL_TOKENS,
    aliases: dict[str, str] | None = None,
) -> pd.Series:
    """Collapse messy owner strings into canonical groups without a lookup table.

    Runs two passes and returns a Series aligned to ``owners`` giving the
    canonical owner per row, so ``df.groupby(cluster_owners(df["owner"])).sum()``
    reveals the true largest holders.

    1. **Curated aliases** (optional): ``aliases`` maps a keyword to a parent
       label, rolling up distinct names that share a corporate brand. For example
       ``{"LYME": "Lyme Timber", "LAT": "Lyme Timber"}`` groups "Lyme Adirondack
       Timberlands II" and "Lyme / LAT I, LLC" under one owner. Keywords are
       matched as whole tokens. This is a human-curated input, not inferred, so it
       does not fabricate corporate relationships.
    2. **Fuzzy variant merging**: everything an alias did not claim is normalized
       (dropping legal tokens like LLC via ``drop_tokens``), then near-duplicate
       spellings are greedily merged above ``threshold`` and labeled with the most
       common original spelling.
    """
    raw = owners.astype(str)
    norm = raw.map(lambda s: _normalize(s, drop_tokens))
    result: pd.Series = pd.Series(index=raw.index, dtype=object)

    if aliases:
        alias_map = {kw.upper(): parent for kw, parent in aliases.items()}
        for idx, name in norm.items():
            tokens = set(name.split())
            for keyword, parent in alias_map.items():
                if keyword in tokens:
                    result.loc[idx] = parent
                    break

    remaining = result.isna()
    rem_norm = norm[remaining]

    reps: list[str] = []  # one normalized representative per cluster
    rep_of: dict[str, int] = {}  # normalized string -> cluster index
    for value in dict.fromkeys(rem_norm):  # unique normalized names, first-seen
        match = (
            process.extractOne(value, reps, scorer=scorer)  # type: ignore[arg-type]
            if reps
            else None
        )
        if match is not None and match[1] >= threshold:
            rep_of[value] = match[2]
        else:
            rep_of[value] = len(reps)
            reps.append(value)

    cluster = rem_norm.map(rep_of)
    # Canonical label per cluster: the most frequent raw spelling in it.
    canonical = {
        idx: group.value_counts().index[0]
        for idx, group in raw[remaining].groupby(cluster)
    }
    result.loc[remaining] = cluster.map(canonical)
    return result
