# Deliverable 9 — Recommended Architecture

> Conceptual architecture only (R&D). No implementation was performed. This is what LeadNation *should* build when it moves from research to engineering.

## §1. North-star design
A pipeline that turns heterogeneous, messy, multi-jurisdiction sources into **canonical, trust-scored, provenance-carrying Buyer entities** — the **Buyer Identity Graph**.

```
                 ┌────────────────────────────────────────────────────────┐
   SOURCES  ───▶ │ 1. INGESTION (connectors: API / bulk / licensed / crawl)│
                 └───────────────┬────────────────────────────────────────┘
                                 ▼
                 ┌────────────────────────────────────────────────────────┐
                 │ 2. NORMALIZATION → canonical event schema + provenance  │
                 └───────────────┬────────────────────────────────────────┘
                                 ▼
                 ┌────────────────────────────────────────────────────────┐
                 │ 3. ENTITY RESOLUTION (dedupe/merge → canonical entities) │
                 └───────────────┬────────────────────────────────────────┘
                                 ▼
                 ┌────────────────────────────────────────────────────────┐
                 │ 4. VERIFICATION + TRUST SCORING (+ sanctions gate)      │
                 └───────────────┬────────────────────────────────────────┘
                                 ▼
                 ┌────────────────────────────────────────────────────────┐
                 │ 5. BUYER IDENTITY GRAPH (canonical store + provenance)  │
                 └───────────────┬────────────────────────────────────────┘
                                 ▼
        ┌────────────────────────┴───────────────────────────┐
        ▼                        ▼                            ▼
   Search/Discovery API     Trust/Provenance API        Intent Alerts
   (LeadNation web/app)     (citable, AEO asset)        (real-time signals)
```

## §2. Layer-by-layer

### Layer 1 — Ingestion (connector framework)
- One **connector interface** with adapter types: `api`, `bulk`, `licensed_feed`, `crawl`.
- Each connector declares: source ID, category, cost/license, refresh cadence, personal-data flag, jurisdiction.
- **Provenance stamped at ingestion** (source URL, license, fetch time, method).
- Rate-limit + retry + backoff per source; crawl connectors honor robots + legal gate.
- **Personal-data quarantine:** connectors flagged personal route into the lawful-basis pipeline, not the general store.

### Layer 2 — Normalization
- Map every source into a **canonical event schema**, e.g.:
  - `TradeEvent` {entity_ref, role(buyer/seller), hs_code, corridor, volume, date, source_ref}
  - `RegistryRecord` {entity_ref, registry_id, status, incorp_date, address, directors?}
  - `IntentEvent` {entity_ref, type(tender/expo/hiring), detail, date, source_ref}
  - `ContactAttribute` {entity_ref, channel, value, lawful_basis, verified_state}
- HS-code harmonization, address standardization, country/port normalization, name cleansing.

### Layer 3 — Entity Resolution (the hard, valuable core)
- **Blocking** (candidate generation) → **pairwise matching** (name + address + registry ID + domain + fuzzy) → **clustering** into canonical entities.
- Use registry IDs / VAT (VIES) / ABN / UEI as **strong keys** when present; fuzzy + ML for the rest.
- Output: canonical `Entity` with merged attributes, each attribute retaining its provenance and a per-attribute confidence.
- Store merge decisions (reversible) for auditability.
- This is where LeadNation beats every "row reseller" — they never do this well.

### Layer 4 — Verification + Trust Scoring
- Run verification checks (Deliverable 8), compute attribute confidences, compose Trust Score (Deliverable 7).
- **Sanctions/PEP screening gate** applied here (hard multiplier).
- Emits the explainability payload.

### Layer 5 — Buyer Identity Graph (canonical store)
- **Graph-shaped model**: nodes = entities/people/products(HS)/events; edges = trades-with, imports, registered-as, contacted-via, member-of.
- Backed by a document/graph store; each fact linked to provenance records.
- Serves search, trust API, and alerts.

### Serving layer
- **Discovery/Search API** for LeadNation web + Expo app (corridor/HS/country filters, Trust band filters).
- **Trust & Provenance API** — the *citable* asset; returns entity + score breakdown + sources. Feeds AEO/LLM citations (aligns with existing `SEO.jsx`/`llms.txt` strategy).
- **Intent alert service** — pub/sub on new signals for a watched buyer/corridor.

## §3. Refresh cadence (Deliverable 7 requirement)
| Source class | Cadence | Why |
|--------------|---------|-----|
| Sanctions / screening lists | **Real-time / daily** | Compliance-critical |
| Procurement/tenders (TED, SAM, UNGM) | **Daily** | Intent is time-sensitive |
| Shipment/BoL feeds (licensed + US CBP) | **Weekly** | Vendor update cycles; corridors shift slowly |
| Trade statistics (Comtrade, national) | **Monthly** | Published monthly/quarterly |
| Company registries | **Weekly–monthly** (event-driven where streaming exists, e.g. Companies House stream) | Status changes matter for Trust |
| Contact/web enrichment | **Monthly + on-demand** | Decay ~30%/yr; re-verify on access |
| Expo/event lists | **Per event calendar** | Seasonal |

## §4. Continuous new-buyer discovery (Deliverable 10, Q10) — the "always-on" engine
1. **New-record watchers** on each connector detect never-seen entity signatures (new consignee on a BoL, new tender bidder, new registry incorporation in target SIC/HS).
2. **Auto-enrich + resolve + score** candidate → if ≥ Tier 2, promote to graph; else park in Tier 0.
3. **Corridor crawlers** expand from a known buyer to its counterparties (graph expansion).
4. **HS/expansion seeds:** for a customer's product HS code, monitor all corridors for fresh importers.
5. **LLM-assisted extraction** for unstructured sources (news, expo PDFs, press releases) into `IntentEvent`s — with human/heuristic validation before promotion.
6. **Daily "New Verified Buyers" digest** per customer corridor = a recurring product hook.

## §5. Tech posture (fits existing LeadNation stack)
- Reuse FastAPI + MongoDB (already in production). MongoDB Atlas suits the flexible entity/provenance model; add a search index (Atlas Search / OpenSearch) for discovery.
- Batch/stream orchestration (a scheduler/queue) for connectors + refresh jobs.
- Keep LLM use **on the Emergent LLM key** for extraction/summarization/entity-matching assists.
- **Compliance-by-design**: lawful-basis engine, provenance ledger, opt-out registry are first-class services, not add-ons.

## §6. What NOT to build
- A bigger raw BoL warehouse (license it).
- A generic company directory (that's the commodity trap).
- Any uncontrolled personal-data lake (legal liability).
