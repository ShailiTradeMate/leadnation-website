# VBIE Phase 2 — Global System Architecture

> **Status:** Architecture design (Phase 2). **No production code.** For review & approval before Phase 3 (Connectors).
> **Incorporates approved Phase-1 updates:** free-first, provider-agnostic licensing, expanded sources, Claim-this-Company, mandatory Source Evidence, future AI Match Score (post-MVP).
> **Shared-infra rule (from handoff):** ONE backend, ONE MongoDB, ONE Firebase, ONE Brain, ONE Customer ID — website + app are thin clients. Firebase/Mongo are shared with the DigitalOcean identity backend → reuse identity, never fork.

---

## §1. Architecture principles (the constitution)
1. **One source of truth.** Web + app consume the same `/api`; no duplicated data or logic.
2. **Free-first.** Free/official sources are always tried before any licensed module.
3. **Provider-agnostic.** Licensed feeds are hot-swappable adapters behind interfaces; enabled via config, not code.
4. **Legality-as-data.** The `sources` registry encodes access/license/storage/attribution/personal rules; the pipeline obeys it automatically.
5. **Evidence or it doesn't exist.** No attribute without provenance; no buyer shown without a Source Evidence trail.
6. **Grounded AI only.** Brain reasons over the graph + provenance, never the open web → no hallucinations.
7. **Compliance-by-construction.** Personal data gated; sanctions screened; opt-out/DSAR built in.

## §2. System topology
```
        Website (React)                 Mobile App (Expo)
              │                                 │
              └──────────────┬──────────────────┘
                             ▼   HTTPS /api/*
                 ┌───────────────────────────────┐
                 │   SHARED FastAPI BACKEND        │
                 │  Auth(Firebase) · Customer IDs  │
                 │  Search · Buyer · Trust ·       │
                 │  Verification · Claim · Admin   │
                 └───────────┬───────────────────┘
                             ▼
                 ┌───────────────────────────────┐
                 │   BRAIN (intelligence layer)    │
                 │  resolve · score · verify ·     │
                 │  ground summaries · match(later)│
                 └───────────┬───────────────────┘
                             ▼
        ┌────────────────────┴─────────────────────┐
        ▼                                           ▼
 MongoDB Atlas (Buyer Graph + provenance)   Firebase Auth (shared identity)
        ▲
        │
 ┌──────┴───────────────────────────────────────────────┐
 │  INGESTION PLANE (nightly orchestrator + connectors)   │
 │  reads sources_seed.json (the registry)                │
 │  FREE tier ─────────────────  LICENSED tier (optional) │
 │  API · CSV · XML · RSS · OCR · SmartCrawler  MirrorBoL │
 └────────────────────────────────────────────────────────┘
```

## §3. Layered responsibilities
| Layer | Responsibility | Shared by web+app? |
|-------|----------------|:---:|
| Clients | Presentation only; no business logic | — |
| API Gateway (FastAPI `/api/*`) | Auth, routing, rate-limit, response shaping | ✅ |
| Services | Search, Buyer, Trust, Verification, Claim, Admin | ✅ |
| Brain | Resolution, scoring, grounded summaries, (future) match | ✅ |
| Data (MongoDB) | Buyer Graph + provenance + sources + audit | ✅ |
| Identity (Firebase) | One auth, one Customer ID | ✅ |
| Ingestion plane | Connectors + orchestrator (offline) | n/a |

## §4. Connector abstraction (provider-agnostic — approved update #2)
All ingestion goes through **typed connectors** (detailed in Phase 3), each driven by a `sources` registry entry:
```
ConnectorType = API | CSV | XML | RSS | OCR | SmartCrawler | MirrorBoLProvider
```
- **Free connectors** (API/CSV/XML/RSS/OCR/SmartCrawler) power the ~6,000 free-first buyers.
- **`MirrorBoLProvider`** is an interface with interchangeable adapters: `VolzaAdapter`, `ImportGeniusAdapter`, `PanjivaAdapter`, `DatamyneAdapter`. All `active:false` until licensed. Switching a provider = flip a config flag, no code change.
- Each connector: declares cadence, respects license/attribution/personal flags, stamps provenance, quarantines personal data.

## §5. Data flow (one buyer's journey)
```
source (registry entry) → connector → raw_records (immutable, provenance)
  → normalize → candidate (Tier 0, quarantined)
  → entity resolution (merge/dedupe) → verification (registry+trade+web+sanctions gate)
  → Trust Score + tier → PROMOTE (Tier≥2) → Buyer Graph
  → Search API / Buyer Card (with Source Evidence) / Alerts
  ← feedback loops (user reports, deliverability, Claim-this-Company) recalibrate
```

## §6. Source Evidence — mandatory on every Buyer Card (approved update #5)
Every Buyer Intelligence Card renders a **Source Evidence** panel, backed by the `provenance` ledger:
- Per attribute: **which source verified it, when, and a link/snippet** ("Website verified via company site 2026-05-28", "Import activity: US CBP ocean BoL 2026-04").
- Shows **verification tier**, **last updated**, and **attribution text** where the source license requires it (UN Comtrade, INSEE Sirene, gBizINFO, ITC, etc.).
- Licensed-feed rows shown as **evidence-of-existence** (not verbatim resale) per license.
- This panel is the trust moat and the AEO-citable surface. **No buyer is displayable without it.**

## §7. Claim-this-Company workflow (approved update #4)
A consent-based enrichment loop that improves data **without requiring generic user signups** (companies claim *their own* profile):
```
1. Company finds its Buyer Card → "Claim this company"
2. Ownership proof: domain-matched email (verify link) OR registry-number match OR Firebase-auth business account
3. On verify → source `claimed_company_data` attached (lawful basis = CONSENT, trust_weight 0.85)
4. Company can correct/enrich: products, HS codes, certifications, contact (consented), export interests
5. Brain re-resolves + re-scores; claimed attributes get a "Verified by owner" badge + freshness boost
6. Consent + opt-out recorded; contact data lawful under consent (cleanest GDPR/DPDP basis)
```
Benefits: highest-freshness data, consented contacts (solves GDPR + accuracy together), two-sided network effect, and a future onboarding funnel for exporter-side customers.

## §8. Future AI Match Score (exporter ↔ buyer) — POST-MVP (approved update #6)
Planned module, **explicitly excluded from MVP**:
- Inputs: exporter profile (products/HS/capacity/certs/target markets) × buyer graph (HS overlap, corridor, import volume/frequency, recency, trust, risk flags).
- Output: a 0–100 **Match Score** + explanation ("92% — imports your HS 3004 from India monthly, verified, no sanctions").
- Design constraint: must be **grounded + explainable** (same anti-hallucination rules as Brain); reuses Trust Score + provenance.
- Sequencing: build after the buyer graph + trust engine are stable (Phase 5 defines Brain; match sits on top later). MVP ships discovery + verification + trust only.

## §9. Environment & deployment posture (fits current stack)
- Backend: existing FastAPI, all routes `/api/*`. Frontend uses `REACT_APP_BACKEND_URL`; app uses configured base URL → same gateway.
- DB: existing MongoDB Atlas (shared) — add VBIE collections (Phase 3/4) without touching auth/identity collections.
- Auth: existing Firebase (shared with DO backend) — reuse; do not modify identity logic.
- Ingestion plane runs as scheduled jobs (nightly orchestrator, Phase 7) — isolated from the request path so it never impacts web/app latency.
- Secrets/keys via env only (per platform rules); source API keys stored server-side, referenced by `sources` registry.

## §10. Non-functional targets
| Concern | Target |
|---------|--------|
| Read latency (Buyer Card/search) | fast via cached hot cards + Atlas Search index |
| Ingestion isolation | offline plane; zero impact on request path |
| Scale | shard `entities` by `{country, hs_family}`; millions of entities |
| Provider lock-in | zero (config-swap adapters) |
| Compliance | enforced by `sources` registry + gated `contacts` + sanctions gate |
| Auditability | immutable `raw_records` + `provenance` + `ai_decisions` |

## §11. What Phase 2 deliberately defers
- Connector internals & crawler engineering → **Phase 3**.
- Full collection schemas & indexes → **Phase 4** (drafted in `A4_DATABASE_DESIGN.md` / `P1_DATABASE_AND_BRAIN.md`).
- Brain resolution/scoring algorithms → **Phase 5**.
- Orchestrator DAG details → **Phase 7** (drafted in `P2_PLATFORM_UX_ORCHESTRATOR.md`).
- AI Match Score model → post-MVP.

## §12. Review gate — approve to proceed to Phase 3
Please confirm:
1. **Topology & shared-infra rule** (one backend/DB/Firebase/Brain; app+web thin clients) — approved?
2. **Provider-agnostic `MirrorBoLProvider` interface** with config-flag activation — approved?
3. **Claim-this-Company** as designed (domain/registry proof + consent basis) — approved?
4. **Mandatory Source Evidence panel** on every card — approved?
5. **AI Match Score deferred to post-MVP** — confirmed?

On approval → **Phase 3: Advanced Connectors & Crawlers** (reusable connector types: API/CSV/XML/RSS/OCR/SmartCrawler + provider adapters, with robots/ToS/rate-limit/delta-crawl/AI-extraction design).
