# Deliverable 8 — Database Design (Proprietary Buyer Database)

> Conceptual data model (R&D). Fits LeadNation's existing FastAPI + MongoDB Atlas stack. No code implemented.

## §1. Design goals
1. **Entity-centric**, not record-centric — one canonical buyer, many source records.
2. **Provenance-native** — every fact traces to a source + timestamp + license.
3. **Time-aware** — attributes have validity windows; nothing is silently overwritten.
4. **Mergeable & reversible** — duplicates merge; merges can be undone (audit).
5. **Compliance-partitioned** — personal data segregated + lawful-basis stamped.

## §2. Core collections (MongoDB)

### `raw_records` (immutable ingestion log — the source of truth)
```
{ _id, source_id, source_category, fetch_ts, method(api|bulk|license|crawl),
  license_ref, raw_payload, source_url, personal_data:bool, corridor_hint }
```
Never mutated. Everything downstream is derived and reproducible from here.

### `entities` (canonical buyers — the product object)
```
{ _id, canonical_name, country, entity_type(importer|exporter|distributor|gov_buyer|mfr),
  attributes: {                       # each attribute is provenance-wrapped
     registry_id:   {value, confidence, sources:[record_ref], first_seen, last_verified},
     website:       {value, confidence, sources, ...},
     address:       {...}, industry:{...}, hs_codes:[{code, confidence, sources}],
     import_history:[{hs, corridor, volume, date, source_ref}],
     export_history:[...], certifications:[...]
  },
  contact_refs:[contact_id],          # personal data lives in separate collection
  trust_score, trust_band, verification_tier,
  status(active|dormant|dissolved|merged|suppressed),
  merged_into,                        # if this entity was merged away
  created_at, updated_at, last_refreshed }
```

### `contacts` (SEGREGATED personal data — lawful-basis gated)
```
{ _id, entity_id, channel(email|phone|linkedin|person), value,
  person_name?, role?, lawful_basis, lia_ref, jurisdiction,
  verified_state(valid|risky|invalid|unverified), verify_ts,
  opt_out:bool, retention_expiry, sources:[record_ref] }
```
Physically/logically separable for GDPR erasure & geo-partitioning.

### `provenance` (evidence ledger)
```
{ _id, entity_id, attribute_path, source_id, source_url, fetch_ts, license_ref, snippet }
```
Powers the citable evidence trail on every buyer page/API.

### `match_decisions` (entity-resolution audit)
```
{ _id, entity_a, entity_b, decision(merge|distinct), score, features, method, decided_at, reversible:true }
```

### `signals` (time-series intent/activity feed)
```
{ _id, entity_id, type(shipment|tender|expo|news|registry_change|sanction), detail,
  event_date, source_ref, ingested_at }
```

### `suppression` (opt-out & confidentiality registry)
```
{ _id, match_key(name/domain/email/reg_id), reason(gdpr_objection|us_confidentiality|sanction|erasure), effective_date }
```

## §3. How buyers are STORED
- Ingest → `raw_records` (immutable) → normalize → resolve → canonical `entities`.
- **Never** store a shipment row as a "buyer." A buyer is a resolved entity referencing many records.
- Personal data → `contacts` only, with lawful basis; entity holds only `contact_refs`.

## §4. How DUPLICATES are MERGED (entity resolution)
1. **Blocking:** group candidates by strong keys (registry_id, VAT/VIES, domain, normalized name+country).
2. **Pairwise scoring:** features = exact reg_id match (decisive), domain match, fuzzy name (Jaro-Winkler), address proximity, shared HS/corridor, shared counterparty.
3. **Decision:** score ≥ merge-threshold → merge; mid-band → human-QA queue; below → distinct.
4. **Merge operation:** pick surviving canonical id, union attributes (keep all provenance), set losers' `status=merged`, `merged_into=survivor`; record in `match_decisions` (reversible).
5. **Conflict resolution:** when two sources disagree on an attribute, keep both with confidences; surface the higher-trust/fresher value as primary.

## §5. How UPDATES happen
- **Append, don't overwrite.** New value → new provenance record; attribute keeps `last_verified` + history.
- **Freshness stamp** updated on every re-verification (even if value unchanged → raises confidence).
- **Status transitions** driven by signals: registry "dissolved" → `status=dissolved`; sanctions hit → `suppressed`.
- Idempotent: re-ingesting the same source record is a no-op (dedup on source_id + hash).

## §6. How OLD companies are REMOVED (or demoted)
- **Soft lifecycle, not hard delete:** `active → dormant (no signal 18–24 mo) → dissolved (registry-confirmed) → archived`.
- Dormant/dissolved entities are **hidden from discovery** but retained for history/provenance.
- **Hard delete** only for legal erasure (DSAR) or confidentiality opt-out → purge personal data, keep anonymized skeleton if lawful.
- Trust decay (below) naturally pushes stale entities out of top results without deletion.

## §7. How TRUST SCORES change over time
- Recomputed on: new signal, scheduled refresh, user feedback, sanctions update.
- **Time-decay** on recency sub-score (half-life ~12 mo) → silent buyers drift down.
- **Corroboration** raises score as independent sources agree.
- **Negative feedback** (bounced email, "wrong company") lowers relevant sub-score + triggers re-verify.
- Full score history retained (`entities.trust_history` optional) for calibration/audit.

## §8. How SOURCE ATTRIBUTION works
- Every attribute carries `sources:[record_ref]`; every record has URL + timestamp + license in `provenance`.
- Product/API/AEO page renders "Evidence" = the provenance list → this is the **trust + citability** feature.
- License-aware rendering: fields under restrictive license show evidence-of-existence without re-publishing restricted raw data.

## §9. Indexing & performance
- Indexes: `entities.country+entity_type`, `attributes.registry_id.value`, `attributes.website.value`, `hs_codes.code`, `trust_band`, `status`.
- Full-text / vector search (Atlas Search) for name + fuzzy discovery and semantic corridor queries.
- `signals` as time-series for fast "recent activity" queries and alerts.
