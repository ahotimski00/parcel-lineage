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


def _normalize(name: str) -> str:
    """Cheap, deterministic cleanup applied before fuzzy scoring."""
    text = name.upper().strip().replace(",", " ").replace(".", "")
    # Collapse common legal-suffix spellings to one token. Dots are already
    # stripped above, so "L.L.C." arrives here as "LLC".
    for variant in ("L L C", "LIMITED LIABILITY COMPANY"):
        text = text.replace(variant, "LLC")
    # Final split/join collapses any repeated whitespace to single spaces.
    return " ".join(text.split())


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
