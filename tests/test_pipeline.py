"""Hermetic tests: no network, no downloads, run in well under a second."""

from __future__ import annotations

import pandas as pd

from parcel_lineage import ChangeType, classify_changes, cluster_owners, resolve_owners
from parcel_lineage.sample_data import corporate_family, snapshot


def _resolved(year: int):
    parcels = snapshot(year)
    resolved = resolve_owners(parcels["raw_owner"], corporate_family())
    return parcels.join(resolved[["parent", "score", "needs_review"]])


def test_typo_resolves_to_correct_parent() -> None:
    # "ACME TIMBERR LLC" (typo) should still roll up to ACME HOLDINGS INC.
    resolved = _resolved(2024)
    row = resolved.loc[resolved["parcel_id"] == 1].iloc[0]
    assert row["parent"] == "ACME HOLDINGS INC"


def test_reordered_and_punctuated_names_match() -> None:
    # "Acme Pine, L.L.C." must match "ACME PINE LLC".
    resolved = _resolved(2020)
    row = resolved.loc[resolved["parcel_id"] == 2].iloc[0]
    assert row["parent"] == "ACME HOLDINGS INC"
    assert not row["needs_review"]


def test_cluster_owners_merges_spelling_variants() -> None:
    owners = pd.Series([
        "Northway Forests, LLC",
        "NORTHWAY FORESTS LLC",
        "Northway Forests L.L.C.",
        "Whitney Industries LLC",
        "State of New York",
    ])
    canon = cluster_owners(owners)
    # The three Northway spellings collapse to one canonical label.
    assert canon.iloc[:3].nunique() == 1
    # Distinct entities stay distinct.
    assert canon.nunique() == 3


def test_cluster_owners_ignores_legal_suffix() -> None:
    # A missing legal suffix should not split an owner.
    canon = cluster_owners(pd.Series(["Northway Forests LLC", "Northway Forests"]))
    assert canon.nunique() == 1


def test_cluster_owners_aliases_group_a_family() -> None:
    owners = pd.Series([
        "Lyme Adirondack Timberlands II",
        "Lyme / LAT I, LLC",
        "Whitney Industries LLC",
    ])
    canon = cluster_owners(owners, aliases={"LYME": "Lyme Timber", "LAT": "Lyme Timber"})
    # The two distinct Lyme names roll up to one parent; Whitney stays separate.
    assert canon.iloc[0] == canon.iloc[1] == "Lyme Timber"
    assert canon.iloc[2] != "Lyme Timber"


def test_change_types_are_detected() -> None:
    changes = classify_changes(_resolved(2020), _resolved(2024))
    by_parcel = dict(zip(changes["parcel_id"], changes["change_type"]))

    assert by_parcel[3] == ChangeType.OWNER_ONLY
    assert by_parcel[4] == ChangeType.BOUNDARY_ONLY
    assert by_parcel[5] == ChangeType.OWNER_AND_BOUNDARY
    # Parcels 1 and 2 are unchanged and must be filtered out.
    assert 1 not in by_parcel
    assert 2 not in by_parcel
