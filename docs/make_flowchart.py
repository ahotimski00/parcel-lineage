"""Draw the parcel-lineage ownership-reconciliation workflow to docs/workflow.png.

    python docs/make_flowchart.py
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

STEPS = [
    ("Public parcel service", "ArcGIS REST layer (e.g. NY statewide parcels)"),
    ("Fetch parcels", "owner name, acreage, geometry"),
    ("Normalize names", "drop legal suffixes: LLC, CO, INC"),
    ("Reconcile owners", "fuzzy-cluster spellings + curated aliases"),
    ("Aggregate acreage", "sum holdings, rank the true owners"),
    ("Rank and map", "landowner bar chart + ownership map"),
]


def main() -> None:
    n = len(STEPS)
    fig, ax = plt.subplots(figsize=(16, 3.1))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    box_w = 0.142
    cy = 0.52
    half_h = 0.34
    centers = np.linspace(0.085, 0.915, n)
    for i, (title, sub) in enumerate(STEPS):
        cx = centers[i]
        ax.add_patch(
            FancyBboxPatch(
                (cx - box_w / 2, cy - half_h), box_w, half_h * 2,
                boxstyle="round,pad=0.004,rounding_size=0.02",
                facecolor="#eaf3ec", edgecolor="#3a7d44", linewidth=1.4,
            )
        )
        ax.text(cx, cy + 0.15, "\n".join(textwrap.wrap(title, 16)),
                ha="center", va="center", fontsize=11, fontweight="bold",
                color="#1f3d29")
        ax.text(cx, cy - 0.13, textwrap.fill(sub, 22),
                ha="center", va="center", fontsize=8, color="#496b57")
        if i < n - 1:
            ax.annotate(
                "", xy=(centers[i + 1] - box_w / 2, cy), xytext=(cx + box_w / 2, cy),
                arrowprops=dict(arrowstyle="-|>", color="#3a7d44", lw=1.8),
            )

    ax.set_title("parcel-lineage: ownership reconciliation workflow",
                 fontsize=13, fontweight="bold", pad=10)
    out = Path("docs") / "workflow.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
