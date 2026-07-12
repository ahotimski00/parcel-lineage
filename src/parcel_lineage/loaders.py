"""Pull parcels from a public ArcGIS REST parcel service, paginated.

Real county and state parcel layers are usually exposed as ArcGIS REST feature
or map services. :func:`fetch_parcels` pages through one and returns a plain
attribute table (owner, parcel id, acreage) ready for
:func:`parcel_lineage.entity_resolution.cluster_owners`.

``NY_TAX_PARCELS`` is a ready-to-use public source: New York State's statewide
tax-parcel layer, which carries owner names and acreage and needs no account.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pandas as pd
import requests

if TYPE_CHECKING:
    import geopandas as gpd


@dataclass(frozen=True)
class ParcelSource:
    """Points the loader at one ArcGIS REST parcel layer and names its fields."""

    query_url: str  # the layer's /query endpoint
    owner_field: str
    id_field: str
    acres_field: str
    extra_fields: tuple[str, ...] = field(default_factory=tuple)


NY_TAX_PARCELS = ParcelSource(
    query_url=(
        "https://gisservices.its.ny.gov/arcgis/rest/services/"
        "NYS_Tax_Parcels_Public/MapServer/1/query"
    ),
    owner_field="PRIMARY_OWNER",
    id_field="PRINT_KEY",
    acres_field="ACRES",
    extra_fields=("COUNTY_NAME", "PROP_CLASS"),
)


def fetch_parcels(
    source: ParcelSource,
    where: str = "1=1",
    *,
    page_size: int = 2000,
    max_records: int | None = None,
    timeout: int = 60,
) -> pd.DataFrame:
    """Page through an ArcGIS REST query and return an attribute DataFrame.

    Geometry is not requested (the ownership analysis is attribute-only), which
    keeps each page small and the pull fast. The owner, id, and acres columns are
    renamed to ``owner``, ``parcel_id``, and ``acres`` regardless of source.
    """
    out_fields = ",".join(
        [source.id_field, source.owner_field, source.acres_field, *source.extra_fields]
    )
    rows: list[dict] = []
    offset = 0
    while True:
        params = {
            "where": where,
            "outFields": out_fields,
            "returnGeometry": "false",
            "resultOffset": str(offset),
            "resultRecordCount": str(page_size),
            "f": "json",
        }
        resp = requests.get(source.query_url, params=params, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise RuntimeError(f"ArcGIS query failed: {data['error']}")
        features = data.get("features", [])
        rows.extend(f["attributes"] for f in features)
        more = data.get("exceededTransferLimit") or len(features) == page_size
        if not more or (max_records is not None and len(rows) >= max_records):
            break
        offset += page_size

    df = pd.DataFrame(rows)
    if max_records is not None:
        df = df.head(max_records)
    return df.rename(
        columns={
            source.id_field: "parcel_id",
            source.owner_field: "owner",
            source.acres_field: "acres",
        }
    )


def fetch_parcels_gdf(
    source: ParcelSource,
    where: str = "1=1",
    *,
    page_size: int = 2000,
    max_records: int | None = None,
    timeout: int = 120,
) -> gpd.GeoDataFrame:
    """Like :func:`fetch_parcels` but returns a GeoDataFrame with parcel polygons.

    Requires the ``[viz]`` extra (geopandas). Geometry adds weight, so keep the
    ``where`` clause tight (a county, a minimum acreage).
    """
    import geopandas as gpd

    out_fields = ",".join(
        [source.id_field, source.owner_field, source.acres_field, *source.extra_fields]
    )
    features: list[dict] = []
    offset = 0
    while True:
        params = {
            "where": where,
            "outFields": out_fields,
            "returnGeometry": "true",
            "outSR": "4326",
            "resultOffset": str(offset),
            "resultRecordCount": str(page_size),
            "f": "geojson",
        }
        resp = requests.get(source.query_url, params=params, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise RuntimeError(f"ArcGIS query failed: {data['error']}")
        page = data.get("features", [])
        features.extend(page)
        more = data.get("exceededTransferLimit") or len(page) == page_size
        if not more or (max_records is not None and len(features) >= max_records):
            break
        offset += page_size

    gdf = gpd.GeoDataFrame.from_features(features, crs="EPSG:4326")
    if max_records is not None:
        gdf = gdf.head(max_records)
    return gdf.rename(
        columns={
            source.id_field: "parcel_id",
            source.owner_field: "owner",
            source.acres_field: "acres",
        }
    )
