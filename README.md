# parcel-lineage

Resolve messy county parcel owner names to their controlling parent entity, then
detect how ownership and boundaries change between time-stamped snapshots.

County tax rolls are filed inconsistently: the same company appears under dozens
of spellings ("ACME TIMBER LLC", "Acme Timber, L.L.C.", "ACME TIMBERR LLC"), and
multi-tier LLC structures hide who actually controls large contiguous blocks of
land. `parcel-lineage` reconciles those raw strings against a corporate-family
table built from public filings, rolls each parcel up to its ultimate parent,
then compares two snapshots to flag the changes that matter: who is acquiring
land, who is selling it off in pieces, and how fast the landscape is turning over.

It ships with synthetic sample data so it runs with no downloads and no accounts.

## What it does

1. **Entity resolution** (`resolve_owners`): fuzzy-match raw owner strings to
   canonical child LLCs (order- and punctuation-insensitive), roll up to the
   parent, and flag low-confidence matches for human review instead of trusting
   them blindly.
2. **Change detection** (`classify_changes`): compare two resolved snapshots per
   parcel and bucket each into one of four cases, keeping the three that
   represent real change and filtering the no-change case:
   - different owner, same boundary
   - different owner, different boundary (partial sell-offs)
   - same owner, different boundary
   - same owner, same boundary *(filtered out)*

   An area threshold removes trivial geometry noise (survey corrections,
   coordinate jitter) so only meaningful boundary edits are flagged.

## Quickstart

```bash
pip install -e ".[dev]"
python examples/demo.py
pytest
```

`examples/demo.py` runs the full pipeline on the synthetic 2020 and 2024
snapshots and prints the detected changes.

## Using real data

Swap `parcel_lineage.sample_data` for a real public county parcel export:

- **Parcels:** most counties publish parcel geometry + owner attributes through
  an ArcGIS REST feature service or an open-data portal. Load into a GeoDataFrame
  with an owner-name column and a `parcel_id`.
- **Corporate family:** build the `child_llc -> parent_llc` table from public
  Secretary of State LLC filings, or wire in an API such as OpenCorporates.

The resolver takes a plain `pandas.Series` of owner strings and the change
detector takes any DataFrame carrying a shapely geometry column, so no code
changes are needed to point at live data.

## Roadmap

- [ ] Snapshot loaders for a real county (public ArcGIS REST service)
- [ ] Corporate-family graph: resolve multi-tier child -> parent -> ultimate parent
- [ ] Analytics: parcelization rate, ownership consolidation, transfer velocity
- [ ] Streamlit demo mirroring the cogsieve interactive surface
- [ ] GitHub Actions CI on Python 3.11 and 3.12

## License

MIT
