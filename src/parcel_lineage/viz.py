"""Optional plotting helpers. Requires matplotlib: ``pip install parcel-lineage[viz]``.

Kept out of the core dependencies so the library and its tests stay lightweight.
"""

from __future__ import annotations

import pandas as pd


def plot_top_owners(
    df: pd.DataFrame,
    *,
    canonical: str = "canonical",
    owner: str = "owner",
    acres: str = "acres",
    n: int = 12,
    exclude: tuple[str, ...] = (),
    title: str = "Largest landowners (reconciled)",
):
    """Horizontal bar chart of the largest holders after owner reconciliation.

    Bars whose owner had more than one raw spelling merged are highlighted and
    labeled, so the payoff of reconciliation is visible at a glance. Returns the
    matplotlib Figure.
    """
    import matplotlib.pyplot as plt

    totals = df.groupby(canonical)[acres].sum()
    for name in exclude:
        totals = totals.drop(name, errors="ignore")
    totals = totals.sort_values(ascending=False).head(n)[::-1]
    names = list(totals.index)

    variants = {
        name: df.loc[df[canonical] == name, owner].nunique() for name in names
    }
    merged = "#2f6f4e"
    single = "#a9c9a9"
    colors = [merged if variants[name] > 1 else single for name in names]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(range(len(names)), totals.to_numpy(), color=colors)
    ax.set_yticks(range(len(names)), names)
    for i, name in enumerate(names):
        value = totals.iloc[i]
        note = f"   [{variants[name]} names merged]" if variants[name] > 1 else ""
        ax.text(value, i, f"  {value:,.0f} ac{note}", va="center", fontsize=9)

    ax.set_xlabel("Acres owned (names reconciled)")
    ax.set_title(title)
    ax.margins(x=0.22)
    handles = [
        plt.Rectangle((0, 0), 1, 1, color=merged),
        plt.Rectangle((0, 0), 1, 1, color=single),
    ]
    ax.legend(handles, ["names merged", "single name"], loc="lower right")
    fig.tight_layout()
    return fig
