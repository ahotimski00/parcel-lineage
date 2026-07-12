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
    handles = [
        plt.Rectangle((0, 0), 1, 1, color=merged),
        plt.Rectangle((0, 0), 1, 1, color=single),
    ]
    ax.legend(handles, ["names merged", "single name"], loc="lower right")
    fig.tight_layout()

    # Expand the x-axis so no value label overflows the axes. Solve, per bar,
    # for the axis range at which the bar plus its fixed-width label still fits.
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()  # type: ignore[attr-defined]
    axis_w = ax.get_window_extent(renderer).width
    needed = float(totals.max())
    for i, txt in enumerate(ax.texts):
        label_w = txt.get_window_extent(renderer).width
        if label_w < axis_w:
            needed = max(needed, float(totals.iloc[i]) / (1 - label_w / axis_w))
    ax.set_xlim(0, needed * 1.03)
    return fig


def _north_arrow(ax, x: float, y: float) -> None:
    ax.annotate(
        "", xy=(x, y + 0.11), xytext=(x, y), xycoords="axes fraction",
        arrowprops=dict(arrowstyle="-|>", color="black", lw=1.8),
    )
    ax.text(x, y + 0.13, "N", transform=ax.transAxes, ha="center", va="bottom",
            fontsize=11, fontweight="bold")


def plot_owner_map(
    gdf,
    highlight: list[str],
    *,
    canonical: str = "canonical",
    title: str = "Parcel ownership",
    locator=None,
    locator_focus=None,
    author: str | None = None,
    sources: str | None = None,
    created: str | None = None,
    north_arrow: tuple[float, float] = (0.055, 0.83),
    locator_box: tuple[float, float, float, float] = (0.68, 0.66, 0.28, 0.28),
    legend_loc: str = "lower left",
    footer_y: float = 0.015,
):
    """Map the parcels, coloring the largest owners and greying out the rest.

    ``gdf`` is a GeoDataFrame from :func:`parcel_lineage.loaders.fetch_parcels_gdf`
    with a reconciled ``canonical`` column; ``highlight`` is the ordered list of
    owners to color. Optional cartographic furniture: a north arrow, a locator
    inset (``locator`` = context polygons, ``locator_focus`` = the area to
    highlight), and an attribution line (``author``, ``sources``, ``created``;
    ``created`` defaults to today).

    The element positions are parameters (``north_arrow`` in axes fraction,
    ``locator_box`` as a figure-fraction ``(left, bottom, w, h)`` rect,
    ``legend_loc``, ``footer_y``) so they can be tuned per map.
    """
    from datetime import date

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9, 9.6))
    gdf.plot(ax=ax, color="#ededed", edgecolor="white", linewidth=0.15)
    cmap = plt.get_cmap("tab10")
    for i, owner in enumerate(highlight):
        subset = gdf[gdf[canonical] == owner]
        if not subset.empty:
            subset.plot(ax=ax, color=cmap(i % 10), edgecolor="none", label=owner)
    ax.set_title(title)
    ax.set_axis_off()
    ax.legend(  # type: ignore[call-overload]
        loc=legend_loc, fontsize=8, title="Largest owners", frameon=True
    )
    _north_arrow(ax, *north_arrow)

    if locator is not None:
        inset = fig.add_axes(locator_box)
        locator.plot(ax=inset, color="#f2f2f2", edgecolor="#b8b8b8", linewidth=0.3)
        if locator_focus is not None:
            locator_focus.plot(ax=inset, color="#c0392b", edgecolor="black", linewidth=0.4)
        inset.set_axis_off()
        inset.set_title("Location in New York", fontsize=8)

    created = created or date.today().isoformat()
    footer = f"Author: {author}   |   Created: {created}"
    if sources:
        footer += f"   |   {sources}"
    fig.text(0.5, footer_y, footer, ha="center", va="bottom", fontsize=7, color="#444444")
    fig.subplots_adjust(bottom=0.06)
    return fig
