"""Synthetic sample data so the pipeline runs with no downloads.

Nothing here is real. The owner strings deliberately mimic the messiness of
county tax rolls (typos, punctuation, reordering, shell LLCs) so the resolver
and change detector have something realistic to chew on. Swap these builders
out for a real public county parcel export to run on live data; see the README.
"""

from __future__ import annotations

import pandas as pd
from shapely.geometry import Polygon


def corporate_family() -> pd.DataFrame:
    """Child-LLC -> parent-LLC table, as if built from public filings."""
    rows = [
        ("ACME TIMBER LLC", "ACME HOLDINGS INC"),
        ("ACME PINE LLC", "ACME HOLDINGS INC"),
        ("EVERGREEN LAND CO LLC", "EVERGREEN CAPITAL LP"),
        ("EVERGREEN RIDGE LLC", "EVERGREEN CAPITAL LP"),
        ("SOUTHERN OAK PROPERTIES LLC", "SOUTHERN OAK CAPITAL"),
    ]
    return pd.DataFrame(rows, columns=["child_llc", "parent_llc"])


def _square(x: float, y: float, size: float = 1.0) -> Polygon:
    return Polygon([(x, y), (x + size, y), (x + size, y + size), (x, y + size)])


def snapshot(year: int) -> pd.DataFrame:
    """One year's parcel roll with raw owner strings and geometries.

    2020 and 2024 differ so the change detector has real cases to find:
      - parcel 3 is sold (Evergreen -> Southern Oak): owner change
      - parcel 4 is partially sold off: boundary shrinks (boundary change)
      - parcel 5 is both re-owned and re-drawn: owner + boundary change
    """
    if year == 2020:
        rows = [
            (1, "ACME TIMBER LLC", _square(0, 0)),
            (2, "Acme Pine, L.L.C.", _square(1, 0)),
            (3, "EVERGREEN LAND CO LLC", _square(2, 0)),
            (4, "Evergreen Ridge LLC", _square(3, 0, size=2.0)),
            (5, "SOUTHERN OAK PROPERTIES LLC", _square(5, 0)),
        ]
    elif year == 2024:
        rows = [
            (1, "ACME TIMBERR LLC", _square(0, 0)),  # typo, same owner+boundary
            (2, "ACME PINE LLC", _square(1, 0)),  # normalized spelling, no change
            (3, "SOUTHERN OAK PROPERTIES LLC", _square(2, 0)),  # owner change
            (4, "Evergreen Ridge L.L.C.", _square(3, 0, size=1.0)),  # partial sale
            (5, "ACME TIMBER LLC", _square(5.5, 0)),  # owner + boundary change
        ]
    else:  # pragma: no cover - guard
        raise ValueError(f"no sample snapshot for {year}")

    return pd.DataFrame(rows, columns=["parcel_id", "raw_owner", "geometry"])
