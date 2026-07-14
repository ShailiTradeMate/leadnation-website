# VBIE Phase 4 (FINAL) — Networking↔VBIE Unification + GEID + 10 Future-Ready Additions + Entity-Centric Decision

> Architecture only. NO code. This finalizes the data model before Phase 5. Supersedes ambiguous points in `phase4/P11`.

---

## PART A — NEW REQUIREMENT: Networking becomes a living extension of VBIE

### A.1 Principle
Networking is **not** a separate user directory. It is a **view over the Buyer Intelligence graph** where some nodes are *claimed by* LeadNation members. One company identity across the entire ecosystem — website, app, Brain, Networking, Buyer Search, future Supplier Intelligence.

### A.2 Onboarding & claim workflow (unified)
```
Verified Buyer/Company (VBIE entity, has GEID)
        ↓  user signs up → we SEARCH VBIE by domain/name/registry
   Company already in VBIE?
     ├ YES → "Claim this company" (domain-email / registry / auth proof) → link user↔entity
     └ NO  → create NEW entity (GEID minted) → mark self-declared → verify → link
        ↓
   LeadNation User (Firebase Customer ID)
        ↓  claim verified
   Verified Member (member profile linked to entity GEID)
        ↓
   Networking (shows Verified Companies + Verified Members)
        ↓
   Trade Intelligence (buyer search, trust, relationships)
```
**Anti-duplication:** onboarding *always* offers matching VBIE entities first (Matching Brain runs on sign-up). Creating a new entity is the fallback, not the default.

### A.3 User ↔ Entity linkage model
- **`members`** collection (LeadNation users) links to **one entity GEID** via `claimed_entity_geid`.
- An entity gains `claimed_by:[member_id]`, `member_verified:true`, and a `claim` provenance record (lawful basis = consent).
- Networking queries the SAME `entities` graph, filtered/annotated by claim status:
  - **Verified Companies** = VBIE entities (discovered), Tier ≥2.
  - **Verified Members** = entities with `member_verified=true` (a claimed subset).
- Member-contributed data (products, certs, consented contacts) attaches via source `claimed_company_data` (high trust_weight, freshness boost).

### A.4 Shared identity guarantee
`GEID` + `Buyer ID` are the SAME identifier used by web, app, Brain, Networking, Buyer Search, Supplier Intelligence. No feature keeps its own company table. Firebase Customer ID (user) ≠ GEID (company); a member row bridges them. This is the "ONE company identity" mandate.

---

## PART B — ENTITY-CENTRIC MODEL DECISION (evaluation requested)

### B.1 Recommendation: **Adopt the entity-centric model NOW.**
Collapse `buyers` + `companies` into a **single `entities` collection** with `entity_type` (buyer | supplier | manufacturer | agency | member_company | prospect) and **typed relationships**. Reasons:
- The Networking requirement *demands* one identity for companies that are simultaneously a discovered buyer AND a claimed member AND a potential supplier — separate collections would fracture that identity.
- It is **simpler**, not more complex: one node type, one ID space (GEID), one resolution pipeline, one Trust/Confidence/Freshness engine. The buyers/companies split we drafted earlier actually *added* branching.
- It is the natural Global Trade Knowledge Graph shape → zero future migration.

### B.2 MVP simplicity preserved
- MVP still primarily populates `entity_type=buyer`. Other types exist but stay sparse.
- Queries default to `entity_type=buyer` for Buyer Search; Networking adds `member_verified`/`entity_type in [buyer,member_company]`.
- No extra collections vs. the entity-centric merge; it removes one.

### B.3 Verdict
**Entity-centric `entities` collection is the frozen canonical model.** `buyers`/`companies` from P11 are unified into it; `entity_role`→`entity_type`. Everything else in P11/P12 stands.

---

## PART C — 10 FUTURE-READY ADDITIONS (folded into the frozen model)

| # | Addition | Design | MVP |
|---|----------|--------|:--:|
| 1 | **Global Entity ID (GEID)** | Primary stable ID on every node (entities, and referenced by edges/members). Format: `LN-<type>-<ULID>`. Immutable; survives merges (merged node keeps GEID + `merged_into`). Shared across all features. | ✅ |
| 2 | **Relationship weight + confidence on every edge** | `relationships.weight` (strength) + `.confidence` (evidence certainty) mandatory on all edges. | ✅ (schema) |
| 3 | **Historical score timeline** | `score_history` collection: `{geid, ts, trust, confidence, freshness, source_reliability}` — append-only. (Generalizes `trust_history`.) | ✅ |
| 4 | **Persistent AI reasoning history** | `brain_logs` retained permanently (never purged); indexed by `{geid, ts, brain_type}` → full reasoning replay. | ✅ |
| 5 | **Relationship versioning (no deletion)** | Edges are append-only + `valid_from/valid_to` + `status(active|superseded)`. "Removing" a relationship = closing its validity window, never deleting → full history. | ✅ (schema) |
| 6 | **Geographic hierarchy** | `geo` collection: Country→State/Region→City→Port→Coordinates, each a node; entities link `located_in`/`ships_via`. Enables port-level corridor intelligence. | READY (Country/City lite in MVP) |
| 7 | **Brain Cache collection** | `brain_cache`: `{key(hash of prompt+context+model), response, model, ts, ttl, hits}` → memoize AI summaries/answers; cost + latency optimization. | ✅ lite |
| 8 | **Search Analytics collection** | `search_analytics`: `{query, filters, results_shown, clicked_geids, customer_id, ts}` → future demand intelligence, ranking training, "trending corridors". | ✅ (capture only) |
| 9 | **Relationship strength metadata** | On edges: `{frequency, recency, volume, monetary_value?, source_count, decay}` → computed strength beyond raw weight. | READY |
| 10 | **Future AI Agent readiness** | Tool-callable interfaces over the graph: read (`get_entity/search/traverse/evidence`) + propose (`suggest_merge/suggest_edge`) — proposals gated to candidate/QA, never auto-mutate. `brain_logs` + `brain_cache` give agents memory. | READY |

### C.1 Updated `entities` node (frozen)
```
entities {
  _id: GEID,                              # #1 Global Entity ID (primary, immutable)
  entity_type: "buyer|supplier|manufacturer|agency|member_company|prospect",
  canonical_name, name_variants[], name_romanized[],
  country, geo_refs:{country,state,city,port,coordinates},   # #6
  attributes:{...provenance-wrapped...},
  contact_refs:[contact_id],
  # scores
  trust_score, confidence_score, freshness_score, source_reliability_rollup,
  # networking / claim
  claimed_by:[member_id], member_verified:bool, claim_provenance,
  # graph
  relationship_summary:{...}, knowledge_graph_id: GEID,
  status, merged_into, created_at, updated_at, last_refreshed
}
```

### C.2 New/updated collections
- **`entities`** (unified, GEID-keyed) — replaces buyers/companies.
- **`members`** — LeadNation users ↔ `claimed_entity_geid` (Firebase Customer ID bridge).
- **`relationships`** — now with `weight, confidence, valid_from, valid_to, status, strength_meta` (#2,#5,#9).
- **`score_history`** (#3), **`brain_cache`** (#7), **`search_analytics`** (#8), **`geo`** (#6).
- All others from P11/P12 unchanged. `brain_logs` retained permanently (#4).

### C.3 Indexes added
`entities._id(GEID)`, `entities.entity_type+country`, `entities.member_verified`, `entities.attributes.website.value` (claim matching), `relationships.{from,to,type,status}`, `score_history.{geid,ts}`, `brain_cache.key(unique)`, `search_analytics.{ts,customer_id}`, `geo` hierarchy + geospatial index on coordinates.

---

## PART D — Freeze statement
Data model is **FROZEN** as: entity-centric `entities` (GEID) + typed versioned `relationships` + evidence/scoring/brain collections + networking `members` bridge + the 10 future-ready structures (active or READY). Evolves to full GTKG + AI agents with **no breaking changes**. Proceed to Phase 5.
