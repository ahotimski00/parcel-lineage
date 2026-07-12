"""parcel-lineage: resolve messy parcel owners and track ownership change."""

from parcel_lineage.change_detection import ChangeType, classify_changes
from parcel_lineage.entity_resolution import (
    ResolverConfig,
    cluster_owners,
    resolve_owners,
)
from parcel_lineage.loaders import NY_TAX_PARCELS, ParcelSource, fetch_parcels

__all__ = [
    "NY_TAX_PARCELS",
    "ChangeType",
    "ParcelSource",
    "ResolverConfig",
    "classify_changes",
    "cluster_owners",
    "fetch_parcels",
    "resolve_owners",
]

__version__ = "0.1.0"
