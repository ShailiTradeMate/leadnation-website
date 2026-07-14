# Phases 2, 3, 4 — Data Strategy · Global Buyer DB · Brain Integration

> Extends `/app/memory/research/acquisition/A4_DATABASE_DESIGN.md`. Conceptual only; no code.

---

# PHASE 2 — DATA STRATEGY (lifecycle decision per data class)

Every data class is assigned exactly one lifecycle policy. This table is the contract the system enforces.

| Data class | Permanently stored | Refreshed nightly | Cached (TTL) | Queried live | Licensed | Auto-expire / delete |
|------------|:---:|:---:|:---:|:---:|:---:|:---:|
| Company identity (name, reg#, addr, industry) | ✅ | — | — | — | — | on dissolution → archive |
| Government registration status | ✅ | ✅ (event/stream) | — | — | — | — |
| Trade activity (public BoL, CID, tenders) | ✅ | ✅ (weekly/daily) | — | — | — | — |
| Trade statistics (Comtrade/national) | ✅ (as reference) | — (monthly) | — | — | — | — |
| Licensed shipment rows (Volza etc.) | ⚠️ per licence | ✅ (weekly) | — | — | ✅ | delete on licence end (if required) |
| HS codes / products | ✅ | — | — | — | — | — |
| Website / domain / MX | ✅ (fact) | — | ✅ re-verify monthly | — | — | — |
| Email (personal/role) | ⚠️ gated | — | ✅ re-verify + decay | on-access verify | — | **auto-expire (retention window)** |
| Phone (personal) | ⚠️ gated | — | ✅ | — | — | **auto-expire** |
| Person names / LinkedIn | ⚠️ minimal, gated | — | — | — | official API | erasure on request |
| VIES VAT validation | — | — | ✅ short TTL | ✅ live | — | expire fast |
| KYB live-API results (ToS-restricted) | — | — | ✅ short TTL | ✅ live | ✅ | expire per ToS |
| Sanctions/PEP screening result | ✅ (audit) | ✅ (daily re-screen) | — | — | — | — |
| Trust Score + history | ✅ | ✅ (nightly recompute) | — | — | — | — |
| Provenance / evidence | ✅ (immutable) | — | — | — | — | keep for audit |
| AI summaries | ✅ | ✅ (regen on change) | — | — | — | regenerate |

**Guiding rules:** Non-personal facts → permanent + versioned. Personal data → cache/expire/erasable. ToS-restricted API data → live/cache-only, never permanent. Licensed data → store per contract, delete-on-end if required.

---

# PHASE 3 — GLOBAL BUYER INTELLIGENCE DATABASE (195 countries, millions of buyers)

Full collection specs are in `A4_DATABASE_DESIGN.md`. Phase-3 additions for scale + all required capabilities:

## §3.1 Required capabilities → design mapping
| Requirement | How it's supported |
|-------------|--------------------|
| 195 countries | `country` + `jurisdiction` on every entity; connector registry is country-scoped; geo-partitioning for EU personal data |
| Millions of buyers | MongoDB sharding by `country`+`hs_family`; Atlas Search for discovery; time-series `signals` |
| Duplicate resolution | `match_decisions` + entity-resolution pipeline (strong keys + fuzzy/ML) |
| Version history | attributes are append-only with `{value, confidence, sources, first_seen, last_verified}`; optional `entity_versions` snapshots |
| Source attribution | `provenance` ledger; every attribute has `sources[]` |
| Trust Score | `trust_score`, `trust_band`, `trust_history` |
| Verification status | `verification_tier` (0–4) |
| Refresh history | `refresh_log` per entity: {source, ts, changed_fields} |
| Evidence | `provenance.snippet` + source_url rendered on Buyer Card |
| Audit trail | immutable `raw_records` + `match_decisions` + `access_log` |
| AI confidence | per-attribute `confidence` + Brain's `ai_confidence` on merge/display decisions |

## §3.2 Collections (superset)
`raw_records` (immutable) · `entities` (canonical) · `contacts` (gated personal) · `provenance` (evidence) · `match_decisions` (resolution audit) · `signals` (time-series activity) · `suppression` (opt-out/confidentiality/sanctions) · `refresh_log` · `sources` (source registry: license, attribution, ToS, cadence, personal-flag) · `access_log` (audit) · `ai_decisions` (Brain explainability records).

## §3.3 `sources` collection — the compliance backbone
```
{ _id, name, category, country, official:bool, base_url, access(api|bulk|license|crawl),
  license_type, attribution_required:bool, attribution_text, tos_url,
  storage_policy(permanent|cache|live|licensed), cache_ttl, personal_data:bool,
  refresh_cadence, trust_weight, active:bool }
```
Every `raw_record` references a `source_id`; the storage/attribution/personal rules are enforced from here → **legal policy becomes data, not tribal knowledge.**

## §3.4 Scale & performance
- Shard `entities` on `{country, hs_family}`; index `registry_id`, `website`, `hs_codes.code`, `trust_band`, `status`.
- Atlas Search (or OpenSearch) for name/fuzzy/semantic discovery.
- `signals` as time-series collection for fast "recent activity" + alerts.
- Cold-storage archive for dormant/dissolved entities (kept for provenance, excluded from search).

---

# PHASE 4 — BRAIN INTEGRATION (the intelligence layer)

**Principle: Brain decides *with evidence*, never *by hallucination*.** Every Brain decision writes an `ai_decisions` record with inputs, rule/model, confidence, and the evidence used.

## §4.1 What Brain decides
| Decision | How Brain does it (evidence-bound) |
|----------|-----------------------------------|
| Which sources are trustworthy | `sources.trust_weight` (official > licensed > crawled), calibrated by historical accuracy/feedback |
| Which records should merge | Entity-resolution scoring (strong keys decisive; fuzzy features); mid-band → human QA; every merge logged & reversible |
| Which buyer to display | Ranking = Trust × corridor relevance × recency × verification tier; only Tier ≥2 shown |
| Which source has highest confidence | Per-attribute confidence = f(source trust_weight, recency, corroboration count) |
| How Trust Score changes | Factor model + time-decay + corroboration + feedback (see `05_TRUST_AND_VERIFICATION.md`) |
| How duplicates merge | See resolution pipeline; conflicts keep both values, surface higher-confidence |
| How AI explains its answer | Generates the AI Summary strictly from stored attributes + provenance; cites sources; no external invention |

## §4.2 Anti-hallucination guardrails (hard requirements)
1. **Grounded generation only:** AI summaries are produced from the entity's stored, provenance-backed attributes — never free-form web recall. (RAG over the entity record, not the open internet.)
2. **Citation-required:** every claim in a summary maps to a `provenance` record; unsupported claims are dropped.
3. **Confidence surfaced:** low-confidence attributes are labeled, not asserted.
4. **No invented contacts:** Brain never generates emails/phones — only displays verified, lawful-basis contacts.
5. **Decision log:** merges, displays, and score changes are auditable via `ai_decisions`.
6. **Human-in-the-loop:** mid-confidence merges and Tier-4 promotions require QA sampling.

## §4.3 Brain tech posture
- Uses the **Emergent LLM key** for extraction, reconciliation, and summary generation.
- Retrieval-augmented over the Buyer Graph (entity record + provenance), not the open web.
- Deterministic rule layer for merges/scoring; LLM assists reconciliation and natural-language explanation only.
- Single Brain service consumed by **both website and app** (Phase 5) — one source of truth.
