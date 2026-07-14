# VBIE Phase 4 — Doc 1/2: Unified Buyer Intelligence Database (Collections, Schema, Indexes)
## (Section: Data Model · incorporates the 10 approved additions)

> **Status:** Architecture/design only. NO production code. Review before Phase 5 (Brain).
> **Principle:** startup-friendly now, Knowledge-Graph-ready later. Some collections/fields ship **dormant** in MVP (structure exists; logic activates later). Marked **[MVP]** = active in MVP; **[READY]** = schema present, inactive until later.

---

## §1. Modeling stance: document store, graph-shaped
MongoDB stays the single store (per shared-infra rule). We model **graph-natively inside Mongo**: **nodes** (entities, products/HS, countries, industries, events, people) and **edges** (`relationships`). This lets us run today on Mongo and **export/mirror to a native graph DB (Neo4j/Neptune) later** with zero remodeling — the Global Trade Knowledge Graph is a *projection* of these collections.

Every node carries: `id`, `type`, provenance-wrapped attributes, `confidence`, `source_reliability_rollup`, timestamps. Every edge carries: `from`, `to`, `type`, `evidence[]`, `confidence`, `first_seen`, `last_seen`.

---

## §2. Collections (full set)

### Core entity & identity
- **`buyers`** [MVP] — canonical buyer/entity (the product object). *Node.*
- **`companies`** [READY] — alias of buyers for non-buyer entities (suppliers/exporters/agencies) so the graph holds all trade actors, not just buyers. In MVP, `buyers` suffices; `entity_role` field distinguishes; split later if needed.
- **`contacts`** [MVP, gated] — segregated personal data, lawful-basis stamped.
- **`raw_records`** [MVP] — immutable ingestion log (audit + reproducibility).

### Evidence, versioning, audit
- **`provenance`** [MVP] — per-attribute evidence (Evidence Engine, Phase 3 §6).
- **`buyer_sources`** [MVP] — M:N link buyer↔source with per-source contribution + reliability at time of capture.
- **`entity_versions`** [READY] — point-in-time snapshots for full version history/rollback.
- **`match_decisions`** [MVP] — entity-resolution audit (reversible merges).
- **`verification_logs`** [MVP] — every verification check + result + method.
- **`access_log`** [MVP] — who/what/when reads & mutations.

### Graph & knowledge layer
- **`relationships`** [READY] — typed edges between any nodes (Relationship Graph, addition #2/#8/#9). *Edge collection.*
- **`products`** [MVP-lite] — HS-code nodes (code, description, industry links).
- **`industries`** [READY] — industry nodes + `industry↔industry` and `industry↔HS` edges (Industry Relationship Graph #8).
- **`countries`** [MVP-lite] — country nodes + corridor edges (Country Intelligence relationships #9).
- **`trade_events`** [READY] — expos/tenders/delegations as nodes; link buyers via edges + as intent signals.

### Time & signals
- **`signals`** [MVP] — time-series activity feed (shipments/tenders/news/registry changes).
- **`company_timeline`** [MVP-lite] — derived, ordered life-events per buyer (Company Timeline #1).
- **`refresh_log`** [MVP] — per-entity refresh history (freshness).

### Scoring
- **`trust_history`** [MVP] — Trust Score over time (calibration/audit).
- **(scores live on the `buyers` doc)** — trust, confidence (#3), freshness (#7), source-reliability rollup (#6).

### Brain (modularized #10)
- **`brain_logs`** [MVP] — explainable decision log for ALL five brains (`brain_type` field). AI Explainability (#4).
- **`crawler_logs` / `connector_runs`** [MVP] — ingestion telemetry.

### Config / registry
- **`sources`** [MVP] — the master source registry (from `sources_seed.json`) incl. `reliability_score` (#6).

---

## §3. `buyers` document (canonical node) — key fields
```
buyers {
  _id (Buyer ID, stable),
  entity_role: "buyer|supplier|agency|manufacturer|distributor",   # graph holds all actors
  canonical_name, name_variants[], name_romanized[],               # multilingual (resolution)
  country, jurisdiction,
  attributes: {                                                    # each provenance-wrapped
    registry_id:{value,confidence,sources[],first_seen,last_verified},
    website:{...}, address:{...}, industry:{...},
    hs_codes:[{code,confidence,sources[]}],
    products:[...], certifications:[...],
    import_history:[{hs,corridor,volume,date,source_ref}],
    export_history:[...]
  },
  contact_refs:[contact_id],                                       # personal data segregated

  # ---- SCORES (additions #3,#6,#7 + trust) ----
  trust_score, trust_band, verification_tier,                     # [MVP]
  confidence_score,        # overall data confidence (#3) [MVP]
  freshness_score,         # decay of last_verified across attrs (#7) [MVP]
  source_reliability_rollup, # weighted avg of contributing sources' reliability (#6) [MVP-lite]
  ai_match_readiness: bool,  # gate for post-MVP match engine

  # ---- GRAPH READINESS (#2,#5,#8,#9) ----
  relationship_summary:{buyers:n, suppliers:n, corridors:[...], industries:[...]}, # [READY] denorm cache
  knowledge_graph_id,       # stable node id for graph export [READY]

  # ---- TIMELINE (#1) ----
  timeline_ref: company_timeline,   # or embedded recent events [MVP-lite]

  status: "active|dormant|dissolved|merged|suppressed",
  merged_into,
  created_at, updated_at, last_refreshed
}
```

## §4. `relationships` edge collection (#2, #5, #8, #9) — [READY]
```
relationships {
  _id, from_node:{type,id}, to_node:{type,id},
  type: "trades_with | imports_from | supplies_to | subsidiary_of | same_group |
         member_of(association) | exhibited_at(event) | operates_in(country) |
         classified_as(industry) | deals_in(hs) | corridor(country->country) |
         industry_related(industry<->industry)",
  direction: "directed|undirected",
  evidence:[provenance_ref], confidence, weight,
  first_seen, last_seen, source_ids[]
}
```
- Buyer↔Supplier (`trades_with`/`imports_from`) → **Relationship Graph** (#2).
- Industry↔Industry / Industry↔HS (`industry_related`/`deals_in`) → **Industry Relationship Graph** (#8).
- Country↔Country / Country↔HS (`corridor`/`operates_in`) → **Country Intelligence relationships** (#9).
- All edges evidence-backed (no unsupported relationship). **Dormant in MVP** (populated as data accrues); querying/traversal activates later.

## §5. `company_timeline` (#1) — [MVP-lite]
```
company_timeline {
  _id, buyer_id, events:[
    { ts, type:"first_seen|registry_change|first_shipment|new_corridor|
                tender_awarded|verified_tier_change|trust_change|claimed|sanction_flag|dissolved",
      detail, source_ref, confidence }
  ]
}
```
Derived from `signals` + `refresh_log` + `match_decisions` + status changes. MVP shows a basic timeline (first seen → registry-verified → trade-verified → contact-verified); richer events accrue over time. Powers the Buyer Card "Verification Timeline".

## §6. `sources` + Source Reliability Score (#6) — [MVP-lite]
```
sources { ...registry fields...,
  reliability_score,   # 0-1: f(historical accuracy vs corroboration, uptime, freshness, user-correction rate)
  reliability_history:[{ts,score}], trust_weight (prior) }
```
Reliability starts at a prior from `trust_weight` (official > licensed > crawled) and is **learned** over time (how often this source agrees with corroborated truth; how often its data triggers "wrong" feedback). Feeds per-attribute `confidence` and the entity `source_reliability_rollup`. Nightly recompute.

## §7. Scoring model summary (how the four scores relate)
| Score | Lives on | Inputs | MVP |
|-------|----------|--------|:--:|
| **Trust Score** | buyers | identity+trade+recency+corroboration+reach+standing × risk gate | ✅ v0 |
| **Confidence Score** (#3) | per-attribute + buyers rollup | source reliability × recency × corroboration | ✅ |
| **Freshness Score** (#7) | buyers | decay of last_verified across attributes (half-life ~12mo) | ✅ |
| **Source Reliability** (#6) | sources | accuracy vs corroborated truth, uptime, feedback | ✅ lite |
Trust consumes Confidence + Freshness + Source Reliability → single explainable number.

## §8. Indexes & sharding
- Shard key: `buyers` on `{country, hs_family}` (co-locates corridor queries).
- Indexes: `attributes.registry_id.value`, `attributes.website.value`, `hs_codes.code`, `trust_band`, `freshness_score`, `status`, `entity_role`, `knowledge_graph_id`.
- `relationships`: indexes on `{from_node}`, `{to_node}`, `{type}` (graph traversal-ready).
- `signals`, `trust_history`, `company_timeline`: time-series / compound `{buyer_id, ts}`.
- Atlas Search index: `canonical_name` + `name_variants` + `products` + `country` (discovery + fuzzy).
- `provenance`: `{entity_id, attribute_path}`.

## §9. MVP-active vs dormant summary
**Active [MVP]:** buyers, contacts(gated), raw_records, provenance, buyer_sources, match_decisions, verification_logs, signals, refresh_log, trust_history, brain_logs, sources, crawler_logs; scores: trust, confidence, freshness, source-reliability(lite); basic company_timeline; products/countries(lite).
**Dormant-but-ready [READY]:** relationships (graph edges), industries graph, trade_events graph, entity_versions (full snapshots), companies split, ai_match, full knowledge_graph export.
Nothing needs re-modeling to activate the dormant layer — only turn on population + query logic.
