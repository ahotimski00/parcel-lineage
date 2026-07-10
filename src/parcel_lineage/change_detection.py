"""Classify how each parcel changed between two resolved ownership snapshots.

Given two snapshots of the same parcels (each already run through
:mod:`parcel_lineage.entity_resolution`), compare owner and geometry per parcel
and bucket every parcel into one of four scenarios. The three that represent
real change are returned; the no-change case is filtered out.
"""

from __future__ import annotations

from enum import Enum

import pandas as pd
from shapely.geometry.base import BaseGeometry


class ChangeType(Enum):
    OWNER_ONLY = "different_owner_same_boundary"
    OWNER_AND_BOUNDARY = "different_owner_different_boundary"
    BOUNDARY_ONLY = "same_owner_different_boundary"
    NO_CHANGE = "same_owner_same_boundary"


def _boundary_changed(
    geom_a: BaseGeometry, geom_b: BaseGeometry, area_threshold: float
) -> bool:
    """True if the symmetric difference exceeds ``area_threshold``.

    The threshold filters out trivial geometry noise (survey corrections,
    coordinate-precision jitter) so only meaningful boundary edits, including
    partial sell-offs, are flagged.
    """
    return geom_a.symmetric_difference(geom_b).area > area_threshold


def classify_changes(
    snapshot_a: pd.DataFrame,
    snapshot_b: pd.DataFrame,
    *,
    parcel_id: str = "parcel_id",
    owner_col: str = "parent",
    geometry_col: str = "geometry",
    area_threshold: float = 0.0,
    keep_no_change: bool = False,
) -> pd.DataFrame:
    """Compare two resolved snapshots and label each parcel's change type.

    Both frames must share ``parcel_id`` values and carry a resolved owner
    column and a shapely geometry column. Parcels absent from either snapshot
    are ignored here (appearance/disappearance is a separate signal).

    Returns a DataFrame keyed on ``parcel_id`` with the owner and geometry from
    both snapshots and a ``change_type`` column. By default the no-change rows
    are dropped.
    """
    merged = snapshot_a.merge(
        snapshot_b, on=parcel_id, suffixes=("_a", "_b"), how="inner"
    )

    def _label(row: pd.Series) -> ChangeType:
        owner_changed = row[f"{owner_col}_a"] != row[f"{owner_col}_b"]
        geom_changed = _boundary_changed(
            row[f"{geometry_col}_a"], row[f"{geometry_col}_b"], area_threshold
        )
        if owner_changed and geom_changed:
            return ChangeType.OWNER_AND_BOUNDARY
        if owner_changed:
            return ChangeType.OWNER_ONLY
        if geom_changed:
            return ChangeType.BOUNDARY_ONLY
        return ChangeType.NO_CHANGE

    merged["change_type"] = merged.apply(_label, axis=1)

    if not keep_no_change:
        # Build the mask in plain Python so filtering never depends on how
        # pandas vectorizes equality against an Enum member.
        mask = [ct != ChangeType.NO_CHANGE for ct in merged["change_type"]]
        merged = merged[mask]

    return merged.reset_index(drop=True)
