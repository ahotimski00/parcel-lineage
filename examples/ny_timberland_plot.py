"""Fetch Hamilton County, NY parcels, reconcile owners, and save a chart + map.

    pip install parcel-lineage[viz]
    python examples/ny_timberland_plot.py
"""

from __future__ import annotations

from pathlib import Path

from parcel_lineage.entity_resolution import cluster_owners
from parcel_lineage.loaders import NY_TAX_PARCELS, fetch_parcels_gdf
from parcel_lineage.viz import plot_owner_map, plot_top_owners

# Curated corporate-family aliases for known Adirondack timberland owners.
ADIRONDACK_ALIASES = {"LYME": "Lyme Timber", "LAT": "Lyme Timber"}


def main() -> None:
    gdf = fetch_parcels_gdf(NY_TAX_PARCELS, where="COUNTY_NAME='Hamilton' AND ACRES>25")
    gdf = gdf[gdf.geometry.notna()].dropna(subset=["owner", "acres"])
    gdf = gdf[gdf["owner"].str.strip() != ""]
    gdf["canonical"] = cluster_owners(gdf["owner"], aliases=ADIRONDACK_ALIASES).to_numpy()

    out = Path("docs")
    out.mkdir(exist_ok=True)

    bars = plot_top_owners(
        gdf,
        exclude=("State Of New York",),
        title="Largest private landowners, Hamilton County, NY (Adirondacks)",
    )
    bars.savefig(out / "hamilton_landowners.png", dpi=140)

    private = gdf[gdf["canonical"] != "State Of New York"]
    top = list(private.groupby("canonical")["acres"].sum().sort_values().tail(6).index)
    owner_map = plot_owner_map(
        gdf,
        top[::-1],
        title="Where the largest private landowners hold, Hamilton County, NY",
    )
    owner_map.savefig(out / "hamilton_owner_map.png", dpi=140)
    print(f"Wrote {out}/hamilton_landowners.png and {out}/hamilton_owner_map.png")


if __name__ == "__main__":
    main()
