"""Fetch Hamilton County, NY parcels, reconcile owners, and save a chart.

    pip install parcel-lineage[viz]
    python examples/ny_timberland_plot.py
"""

from __future__ import annotations

from pathlib import Path

from parcel_lineage.entity_resolution import cluster_owners
from parcel_lineage.loaders import NY_TAX_PARCELS, fetch_parcels
from parcel_lineage.viz import plot_top_owners


def main() -> None:
    df = fetch_parcels(NY_TAX_PARCELS, where="COUNTY_NAME='Hamilton' AND ACRES>25")
    df = df.dropna(subset=["owner", "acres"])
    df = df[df["owner"].str.strip() != ""]
    df["canonical"] = cluster_owners(df["owner"]).to_numpy()

    fig = plot_top_owners(
        df,
        exclude=("State Of New York",),
        title="Largest private landowners, Hamilton County, NY (Adirondacks)",
    )
    out = Path("docs")
    out.mkdir(exist_ok=True)
    fig.savefig(out / "hamilton_landowners.png", dpi=140)
    print(f"Wrote {out / 'hamilton_landowners.png'}")


if __name__ == "__main__":
    main()
