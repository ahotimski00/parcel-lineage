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

It runs on live public parcel services or on synthetic sample data, with no
downloads and no accounts.

## What it does

1. **Owner-name reconciliation** (`cluster_owners`): with no lookup table, collapse
   the spelling variants of a raw county roll ("Northway Forests, LLC" vs "NORTHWAY
   FORESTS LLC") into one canonical owner, so the true largest holders surface.
2. **Entity resolution** (`resolve_owners`): when a corporate-family table is
   available, fuzzy-match raw owner strings to canonical child LLCs and roll up to
   the ultimate parent, flagging low-confidence matches for human review.
3. **Change detection** (`classify_changes`): compare two resolved snapshots per
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
python examples/demo.py          # synthetic end-to-end (no network)
python examples/ny_timberland.py # live: real Hamilton County, NY parcels
pytest
```

## Real data: who owns the Adirondacks

`examples/ny_timberland.py` pulls the live New York statewide tax-parcel service
(`parcel_lineage.loaders.NY_TAX_PARCELS`, no account needed) for Hamilton County,
reconciles the owner-name variants, and re-ranks the largest landowners. Recent
run: 3,512 parcels over 25 acres, 711 raw owner strings reconciled to 690, with
the reconciliation merging spelling variants of the big timberland LLCs, for
example Lyme Adirondack Timberlands II (3 spellings) and Whitney Industries LLC.

`loaders.fetch_parcels` takes any ArcGIS REST parcel layer via a `ParcelSource`
(service URL plus owner/id/acres field names), so pointing it at another county
or state is a config change, not a code change. Supply a `child_llc -> parent_llc`
table (from public Secretary of State filings or an API such as OpenCorporates)
to `resolve_owners` when you need to roll spelling-clean owners up to their
ultimate corporate parent.

## Roadmap

- [x] Owner-name reconciliation on a live public parcel service (NY statewide)
- [ ] Corporate-family graph: resolve multi-tier child -> parent -> ultimate parent
- [ ] Change detection on two real time-stamped snapshots
- [ ] Analytics: parcelization rate, ownership consolidation, transfer velocity
- [ ] Streamlit demo mirroring the cogsieve interactive surface
- [ ] GitHub Actions CI on Python 3.11 and 3.12

## License

MIT
