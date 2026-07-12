"""Real-data demo: who actually owns the most land in Hamilton County, NY.

Hamilton County sits in the Adirondacks, where large timberland and
conservation holdings are recorded under LLCs whose names appear in several
spellings across the roll. This pulls the live NY statewide parcel layer,
reconciles the owner-name variants, and re-ranks the largest landowners,
showing how much the ranking moves once the variants are merged.

    python examples/ny_timberland.py
"""

from __future__ import annotations

from parcel_lineage.entity_resolution import cluster_owners
from parcel_lineage.loaders import NY_TAX_PARCELS, fetch_parcels

# Curated corporate-family aliases for known Adirondack timberland owners whose
# holdings are recorded under several distinct LLC names. Keyword -> parent.
ADIRONDACK_ALIASES = {"LYME": "Lyme Timber", "LAT": "Lyme Timber"}


def main() -> None:
    df = fetch_parcels(NY_TAX_PARCELS, where="COUNTY_NAME='Hamilton' AND ACRES>25")
    df = df.dropna(subset=["owner", "acres"])
    df = df[df["owner"].str.strip() != ""]
    print(f"Fetched {len(df)} parcels over 25 acres in Hamilton County, NY.")

    df["canonical"] = cluster_owners(df["owner"], aliases=ADIRONDACK_ALIASES).to_numpy()
    print(
        f"Distinct owners: {df['owner'].nunique()} raw -> "
        f"{df['canonical'].nunique()} after reconciliation."
    )

    totals = df.groupby("canonical")["acres"].sum().sort_values(ascending=False)
    print("\nTop 12 landowners (acres, distinct names merged):")
    for name, acres in totals.head(12).items():
        merged = df.loc[df["canonical"] == name, "owner"].nunique()
        note = f"   [{merged} names merged]" if merged > 1 else ""
        print(f"  {acres:>10,.0f} ac  {name}{note}")


if __name__ == "__main__":
    main()
