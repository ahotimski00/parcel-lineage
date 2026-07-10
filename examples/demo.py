"""End-to-end run on synthetic data: resolve owners, then detect change.

    python examples/demo.py
"""

from __future__ import annotations

from parcel_lineage import classify_changes, resolve_owners
from parcel_lineage.sample_data import corporate_family, snapshot


def resolve_snapshot(year: int):
    family = corporate_family()
    parcels = snapshot(year)
    resolved = resolve_owners(parcels["raw_owner"], family)
    return parcels.join(resolved[["parent", "score", "needs_review"]])


def main() -> None:
    a = resolve_snapshot(2020)
    b = resolve_snapshot(2024)

    flagged = b[b["needs_review"]]
    print(f"Resolved {len(b)} parcels for 2024; {len(flagged)} flagged for review.")

    changes = classify_changes(a, b)
    print(f"\nParcels with real change: {len(changes)}")
    for _, row in changes.iterrows():
        print(
            f"  parcel {row['parcel_id']}: {row['change_type'].value}"
            f"  ({row['parent_a']} -> {row['parent_b']})"
        )


if __name__ == "__main__":
    main()
