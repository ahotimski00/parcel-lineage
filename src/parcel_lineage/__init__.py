"""parcel-lineage: resolve messy parcel owners and track ownership change."""

from parcel_lineage.change_detection import ChangeType, classify_changes
from parcel_lineage.entity_resolution import (
    LEGAL_TOKENS,
    ResolverConfig,
    cluster_owners,
    resolve_owners,
)
from parcel_lineage.loaders import (
    NY_COUNTIES_QUERY,
    NY_TAX_PARCELS,
    ParcelSource,
    fetch_geojson,
    fetch_parcels,
    fetch_parcels_gdf,
)

__all__ = [
    "LEGAL_TOKENS",
    "NY_COUNTIES_QUERY",
    "NY_TAX_PARCELS",
    "ChangeType",
    "ParcelSource",
    "ResolverConfig",
    "classify_changes",
    "cluster_owners",
    "fetch_geojson",
    "fetch_parcels",
    "fetch_parcels_gdf",
    "resolve_owners",
]

__version__ = "0.1.0"
