# Phase 8 — Implementation Plan (only after Phase 1 approval)

> Blueprint for when LeadNation moves research → build. No code written here.

## §8.1 System Architecture
```
CLIENTS: Website (React) + App (Expo)  ── HTTPS /api/* ──▶  API GATEWAY (FastAPI)
                                                              │
        ┌─────────────────────────────────────────────────────┼───────────────────────────┐
        ▼                     ▼                    ▼            ▼                 ▼
  Search/Discovery API   Buyer/Trust API      Verification API   Admin API      Auth (Firebase)
        └─────────────────────┴────────────────────┴────────────┘
                                    ▼
                         BRAIN SERVICE (resolution, scoring, grounded summaries)
                                    ▼
                         MongoDB Atlas (Buyer Graph + provenance + sources)
                                    ▲
        ┌───────────────────────────┴───────────────────────────┐
        │              NIGHTLY ORCHESTRATOR (scheduler/queue)      │
        └───────────────────────────┬───────────────────────────┘
                                     ▼
   CONNECTOR LAYER: gov-API connectors · customs/BoL · tenders · registries ·
                    trade-stats · RSS/news · licensed feeds · crawler (guarded)
```

## §8.2 MongoDB Collections (from Phases 3–4)
`sources` · `raw_records` · `entities` · `contacts` (gated) · `provenance` · `match_decisions` · `signals` (time-series) · `suppression` · `refresh_log` · `ai_decisions` · `access_log` · `customers` (shared web+app). 
Sharding: `entities` on `{country, hs_family}`. Search: Atlas Search index on name/products/country.

## §8.3 Backend APIs (`/api/*`, shared by web + app)
| Endpoint | Purpose |
|----------|---------|
| `GET /api/buyers/search` | Discovery: filters (country, HS, corridor, trust band, tier) |
| `GET /api/buyers/{id}` | Buyer Intelligence Card (entity + evidence + timeline) |
| `GET /api/buyers/{id}/evidence` | Provenance list (citable) |
| `GET /api/buyers/{id}/trust` | Trust breakdown + history |
| `POST /api/buyers/{id}/feedback` | User "bad data" report → feedback loop |
| `GET /api/verification/{id}` | Verification status/tier |
| `GET /api/trust-api/*` | External citable Trust API (later; AEO asset) |
| `POST /api/claim` | Buyer self-claim (consent-based contact freshness) |
| `GET /api/admin/*` | Orchestrator status, QA queue, source health, KPIs |

## §8.4 Crawler Architecture (guarded — see `A3_CRAWLING_LEGAL.md`)
- Allowlist-gated (domain approved only after ToS review) · robots + crawl-delay · honest UA.
- Prefer RSS/sitemap/JSON-LD over HTML · per-domain rate caps · auto-halt 403/429.
- Provenance capture per field · personal-data → lawful-basis quarantine · no login/anti-circumvention.

## §8.5 API Connectors (priority order)
P0: UN Comtrade, UK Companies House, SAM.gov, Canada CID/Corporations, trade.gov CSL, VIES, TED, US CBP BoL.
P1: gBizINFO, Japan Corporate Number, ABN, Eurostat/HMRC/e-Stat, UNGM, INSEE Sirene, email-verify, Volza (licensed).
P2: Wathq, ACRA live, OpenCorporates, handelsregister.ai, Panjiva/Datamyne (enterprise).

## §8.6 Admin Dashboard
Source health (last run, error rate, quota) · orchestrator DAG status · QA queue (mid-confidence merges, Tier-4 promotions) · Trust calibration charts · acquisition KPIs · suppression/DSAR management · license/attribution registry.

## §8.7 Brain Integration
Single service: rule-based resolution + scoring; LLM (Emergent key) for reconciliation + grounded summaries (RAG over entity+provenance, never open web). Writes `ai_decisions` for every merge/display/score. Consumed identically by web + app.

## §8.8 Performance & Scalability
- Read-heavy: cache hot buyer cards + search results (short TTL); CDN for public AEO pages.
- Sharded Mongo + search index for millions of entities across 195 countries.
- Orchestrator scales horizontally per connector; queue-based backpressure.
- Cost guardrails on paid verifications/LLM per night.

## §8.9 Estimated Cost (grounded 2026)
| Item | MVP/yr | Growth/yr |
|------|--------|-----------|
| Free gov/stats/procurement APIs | $0 | $0 |
| US CBP ocean BoL | $0–low | low |
| Licensed shipment (Volza entry) | $0 (deferred) | ~$1,500 (→$5k–25k tiers) |
| Registry gap-fill (OpenCorporates/handelsregister) | — | ~$1k–5k |
| Email verification | ~$0.002–0.008/email (100k ≈ $500–650) | scales |
| LLM (Emergent key) | usage-based | scales |
| MongoDB Atlas + search + compute | existing | scales |
| **Data cost total** | **< ~$1k** | **~$3k–10k** (enterprise feeds extra, pass-through) |
Engineering: MVP ~8–12 person-weeks; Phase 2 ~10–14; Phase 3 ~14–20.

## §8.10 Implementation Timeline
| Phase | Duration | Milestone |
|-------|----------|-----------|
| Legal sign-off (Phase 1) | now | **This report approved** |
| Foundations | Wk 1–2 | Connector framework, `sources` registry, provenance + lawful-basis + suppression, sanctions screening |
| MVP corridor (India→USA) | Wk 3–8 | 1,000 verified US buyers, Trust v0, Buyer Card, nightly orchestrator v0 |
| Trust & Intent | Wk 9–16 | Trust v1, tenders, contact verify, +2 corridors, admin dashboard |
| Fusion depth | Wk 17–28 | Licensed feeds, ML resolution, Trust API, buyer self-claim |
| Scale | ongoing | 195 countries by corridor, QA loop, enterprise features |

## §8.11 What must be true before writing production code (checklist)
- [ ] This report approved by stakeholder.
- [ ] `sources` registry populated with license/attribution/storage policy per source (legal-reviewed).
- [ ] Lawful-basis engine + LIA templates ready for any personal data.
- [ ] Suppression/opt-out + DSAR/erasure workflow designed.
- [ ] Sanctions screening connector selected (trade.gov CSL).
- [ ] Confirmed reuse of shared Firebase/Mongo/Customer IDs (no forking).
- [ ] Licensed-feed contracts reviewed for storage/redistribution terms (before ingesting any paid data).

## §8.12 Final go/no-go
**GO — scoped as company/entity intelligence with gated personal data.** The architecture enforces legal boundaries structurally (source registry policy, provenance, lawful-basis gate, license registry, sanctions screening). Build the MVP on free/official sources first; introduce licensed feeds only under reviewed contracts; never ingest confidential customs or scrape gated personal data. Under these conditions LeadNation can **legally and commercially launch** and operate the world's most trusted Global Buyer Intelligence Platform.
