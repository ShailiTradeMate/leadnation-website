# LeadNation Trade Command Center™ — Mobile App Integration Guide

**Audience:** LeadNation React Native (Expo) app team
**Backend owner:** Vaibhav Deshmane · Vametra AI Technologies Pvt Ltd
**Release frozen for this baseline:** **Volume 1 Complete + Volume 2 Phase 2A Complete**
**Golden rule:** The mobile app is a **thin client**. It must **NOT duplicate any business logic** (costing, scoring, simulation, decisions, Brain). All maths and AI happen on the shared backend. The app only renders, edits inputs, and calls APIs.

---

## 1. Product Overview

The Trade Command Center turns international-trade planning into a stateful workspace built around **Trade Projects**. Every calculation, scenario, decision and report belongs to a project.

- **Trade Projects** — the spine. A project holds product/HS, exporter & importer countries, Incoterm, quantity, cost inputs, margin, buyer/supplier, payment method, documents, workflow stage and the last computed quote. Everything else references a project.
- **Costing (Reactive Computation Graph)** — deterministic FOB → CIF → Landed Cost + buyer-market comparison. Changing any input recomputes the whole graph.
- **Digital Twin** — a "what-if" recompute: send a full set of inputs, get an instant quote + scores + decision, **without saving**.
- **Scenario Engine** — unlimited versioned scenarios per project (Scenario A/B/C…): create, duplicate, merge, archive, compare. Stored in their own collection, linked to the project.
- **Trade Score Engine** — 8 deterministic, explainable scores (profitability, risk, compliance, competition, market, buyer, supplier, overall) — each with a value 0-100, colour band, contributing factors and a plain explanation.
- **Decision Engine** — consolidates costing + scores + comparison into structured **decision objects** (per domain) plus prioritised **recommended actions**. This is the layer the Brain reasons over.
- **LeadNation Brain** — the single orchestration/advisory AI. It **explains, interprets, recommends, summarises** — it **never fabricates numbers**. Deterministic engines produce the figures; the Brain narrates them.

**Layered architecture (never bypass a layer):**
```
Trade Project → Reactive Computation Graph → Simulation Engine → Decision Engine → LeadNation Brain → Executive Report → User
```

---

## 2. Architecture Diagram

```
 ┌─────────────────┐        ┌─────────────────┐
 │  React Website  │        │ React Native App│   ← thin clients, NO business logic
 └────────┬────────┘        └────────┬────────┘
          │  HTTPS (REACT_APP_BACKEND_URL + /api)   │
          └───────────────┬───────────────────────┘
                          ▼
             ┌──────────────────────────┐
             │   Shared Backend (FastAPI)│   base path: /api
             │  Command Center Engines:  │
             │  costing · projects ·     │
             │  simulation · decision ·  │
             │  scores · events ·        │
             │  adapters · Brain         │
             └────────────┬─────────────┘
                          ▼
                 ┌──────────────────┐
                 │   MongoDB Atlas  │  (single shared DB — DB_NAME)
                 └──────────────────┘

 Auth (shared, do NOT replace):
   Firebase project  ──►  DigitalOcean auth backend (REACT_APP_AUTH_API_BASE)
                          issues profile + 5-digit Customer ID
   Firebase ID token ──►  sent as `Authorization: Bearer <idToken>` to the FastAPI backend
```

- **Website and app talk to the SAME FastAPI backend and the SAME MongoDB.** A project created on one surface is instantly visible on the other.
- Business logic lives **only** in the backend engines. The app must never re-implement FOB/CIF/duty/score/decision maths.

---

## 3. Backend Modules (responsibilities)

| Module | Responsibility |
|---|---|
| `projects.py` | Trade Project CRUD, templates, pin, duplicate, version snapshots, autosave (via PUT), workflow stage + `compute_health()` (project-level quick scores). Also owns `_owner()` identity resolution and emits audit events. |
| `costing_engine.py` | The Reactive Computation Graph. `POST /command-center/quote` computes FOB→CIF→Landed + buyer comparison; markets, ports, insights, explain, compliance, autofill. **Deterministic.** |
| `simulation.py` | Simulation Engine + Scenario Builder. Digital Twin (`/simulation/twin`), scenario CRUD, duplicate/merge/archive/versioning, `/simulation/compare`. Uses `costing_engine.compute_quote` + `scores` + `decision_engine`. |
| `decision_engine.py` | Consolidates outputs into structured decision objects + recommended actions; `POST /decision` (deterministic) and `POST /decision/recommendations` (Brain narrates the structured objects, with deterministic fallback). |
| `scores.py` | Trade Score Engine — `compute_scores(project, quote)` → 8 explainable deterministic scores. |
| `events.py` | Universal Audit Trail — `log_event()` writes to `trade_project_events`; `GET /events` lists a project's timeline. |
| `adapters.py` | Live Data Adapter Framework — one standard interface (`Adapter.fetch → AdapterResult{value, source, sourceTier, confidence, aiEstimated, reason, assumptions}`). Wraps existing free/gov feeds (WITS duty, FX, OEC, incentives) and keeps AI estimates separate from facts. New feeds `register()` in — nothing else changes. |
| `brain/` (`routes.py`, `providers.py`, `router.py`, `context.py`, `memory.py`, `engines.py`, `search_layer.py`) | The LeadNation Brain: intent routing, provider (Emergent LLM key), conversation memory, engine-output grounding. `POST /brain/ask` etc. **Never computes numbers.** |
| `monetize.py` | Stripe checkout, download paywall, account/profile, subscriptions. |
| `pricing.py` | Centralized Pricing Engine (single source of truth for all prices; admin-controlled). |

---

## 4. API Documentation

**Base URL:** `${REACT_APP_BACKEND_URL}` (same value the app should store in its env). **Every path below is prefixed with `/api`.**

**Authentication:** Send the Firebase ID token as `Authorization: Bearer <idToken>` on every authenticated call. For unauthenticated/guest usage the backend accepts a header `X-Trade-Session: <uuid>` to scope guest data. **Mobile should always send the Firebase Bearer token** (guest sessions are a website convenience only). Identity resolution: `Authorization` (Firebase UID) wins; otherwise `X-Trade-Session`.

> Legend: 🔒 = requires Firebase Bearer token (or X-Trade-Session for guests). Amounts/prices are always resolved server-side.

### 4.1 Trade Projects

| Action | Method | Path | Auth |
|---|---|---|---|
| List projects | GET | `/api/projects` | 🔒 |
| Create project | POST | `/api/projects` | 🔒 |
| Templates | GET | `/api/projects/templates` | 🔒 |
| Load project | GET | `/api/projects/{pid}` | 🔒 |
| Update / Autosave | PUT | `/api/projects/{pid}` | 🔒 |
| Delete project | DELETE | `/api/projects/{pid}` | 🔒 |
| Pin / unpin | POST | `/api/projects/{pid}/pin` | 🔒 |
| Duplicate | POST | `/api/projects/{pid}/duplicate` | 🔒 |
| Save version snapshot | POST | `/api/projects/{pid}/version` | 🔒 |

**Create project — request**
```json
{
  "title": "Basmati Rice → UAE",
  "product": "Basmati Rice", "hs": "100630",
  "exporter": "356", "importer": "784",
  "incoterm": "CIF", "quantity": 25000, "unit": "kg",
  "destinationPort": "Jebel Ali",
  "transactionCurrency": "USD", "globalCurrency": "INR",
  "marginPct": 15, "buyer": "Gulf Foods LLC", "supplier": "Punjab Mills",
  "paymentMethod": "LC", "shipmentMode": "Sea FCL", "containerType": "40ft",
  "costs": {"exw": 0.8, "packing": 0.05, "inland": 0.03, "thc": 0.02, "customsDocs": 0.01, "freight": 0.06, "insurance": 0.01},
  "assumptions": {}, "notes": "", "stage": "Created", "isTemplate": false
}
```
**Create project — response (abridged)** — returns the public project doc:
```json
{
  "id": "c911...", "title": "Basmati Rice → UAE", "product": "Basmati Rice",
  "hs": "100630", "exporter": "356", "importer": "784", "incoterm": "CIF",
  "quantity": 25000, "unit": "kg", "marginPct": 15, "costs": { ... },
  "stage": "Created", "nextAction": "Add product & HS code",
  "health": {"overall": {"value": 42, "color": "amber"}, "profitability": {...}, "...": {}},
  "lastQuote": null, "versions": [], "pinned": false,
  "createdAt": "2026-...Z", "updatedAt": "2026-...Z"
}
```
**Update / Autosave — request** (partial patch; use for debounced autosave):
```json
{ "patch": { "marginPct": 18, "costs": { "freight": 0.07 } }, "activity": "Adjusted freight" }
```
**Save version — request:** `{ "kind": "quote", "label": "Quote 2026-07-05", "snapshot": { ... } }`

### 4.2 Costing (Reactive Computation Graph)  — prefix `/api/command-center`

| Action | Method | Path |
|---|---|---|
| Full quote (FOB/CIF/Landed/comparison) | POST | `/api/command-center/quote` |
| Buyer-market comparison list | GET | `/api/command-center/markets` |
| Insights (Brain-explained) | POST | `/api/command-center/insights` |
| Explain a line item | POST | `/api/command-center/explain` |
| Compliance report | POST | `/api/command-center/compliance` |
| Ports lookup | GET | `/api/command-center/ports` |
| Autofill costs (Brain estimate) | POST | `/api/command-center/autofill` |

**Quote — request**
```json
{
  "hs": "100630", "product": "Basmati Rice", "exporter": "356", "importer": "784",
  "quantity": 25000, "unit": "kg",
  "costs": {"exw": 0.8, "packing": 0.05, "inland": 0.03, "thc": 0.02, "customsDocs": 0.01, "freight": 0.06, "insurance": 0.01},
  "marginPct": 15, "transactionCurrency": "USD", "globalCurrency": "INR", "compareMarkets": true
}
```
**Quote — response (abridged)**
```json
{
  "ok": true, "hsCode": "100630", "description": "Basmati Rice",
  "exporter": {"code": "356", "name": "India"}, "importer": {"code": "784", "name": "United Arab Emirates"},
  "currency": {"transaction": "USD", "global": "INR"},
  "fob": {"perUnit": 0.9, "total": 22500, "lines": [{"label": "Ex-Works", "total": 20000}, ...]},
  "cif": {"perUnit": 0.97, "total": 24250, "lines": [ ... ]},
  "destination": {"dutyRate": 0, "dutyType": "MFN", "fta": true, "vatRate": 5, "landed": 25462.5},
  "pricing": {"marginPct": 15, "selling": 27882, "profit": 3632},
  "comparison": [{"code": "784", "country": "UAE", "buyerTotal": 25462.5, "fta": true}, ...],
  "routes": { ... }, "sources": ["World Bank WITS", "OEC", "open.er-api.com"]
}
```
> **First call on a fresh HS+lane can take ~15-25s** (cold WITS tariff fetch). It is cached afterwards. Show a loading state; consider a client timeout ≥ 30s for the first quote.

### 4.3 Simulation  — prefix `/api/simulation`

| Action | Method | Path |
|---|---|---|
| Digital Twin (what-if, no save) | POST | `/api/simulation/twin` |
| Create scenario | POST | `/api/simulation/scenarios` |
| List scenarios | GET | `/api/simulation/scenarios?projectId=&includeArchived=false` |
| Get scenario | GET | `/api/simulation/scenarios/{sid}` |
| Update scenario (recompute + version++) | PUT | `/api/simulation/scenarios/{sid}` |
| Duplicate scenario | POST | `/api/simulation/scenarios/{sid}/duplicate` |
| Merge scenarios | POST | `/api/simulation/scenarios/merge` |
| Delete scenario | DELETE | `/api/simulation/scenarios/{sid}` |
| Compare scenarios | POST | `/api/simulation/compare` |

**Digital Twin — request:** `{ "inputs": { ...same fields as project + costs{} + incoterm/paymentMethod/buyer/supplier... } }`
**Digital Twin — response:** `{ "ok": true, "quote": {...}, "summary": {fob,cif,landed,selling,profit,marginPct,dutyRate,bestMarket}, "scores": { 8 scores }, "decision": {...}, "confidence": 0.7 }`

**Create scenario — request:** `{ "projectId": "c911...", "label": "Scenario B", "inputs": {...}, "parentId": null }` — if `inputs` omitted, the scenario is created from the project's current inputs. Auto-labels "Scenario A/B/C…".
**Merge — request:** `{ "projectId": "c911...", "ids": ["sid1","sid2"], "label": "Merged Scenario" }` (best-of: lowest freight/insurance, highest margin).
**Compare — request:** `{ "projectId": "c911..." }` (or `{ "ids": [...] }`) → `{ "ok": true, "rows": [{id,label,version,summary,scores,confidence,overall}], "winners": {profit,landed,selling,margin,overall} }`.

### 4.4 Decision & Scores  — prefix `/api/decision`

| Action | Method | Path |
|---|---|---|
| Decision object + all Trade Scores | POST | `/api/decision` |
| Brain recommendations + action plan | POST | `/api/decision/recommendations` |

**Request (both):** `{ "projectId": "c911..." }`
**`/api/decision` response:**
```json
{
  "ok": true,
  "scores": {
    "overall": {"label":"Overall Trade Health","value":73,"color":"emerald","factors":[...],"explanation":"..."},
    "profitability": {...}, "risk": {...}, "compliance": {...}, "competition": {...},
    "market": {...}, "buyer": {...}, "supplier": {...}
  },
  "decision": {
    "objects": [{"domain":"profitability","score":72,"verdict":"strong","signal":"...","evidence":{...}}, ... 6 domains],
    "recommendedActions": [{"type":"market","priority":"high","title":"...","detail":"..."}],
    "overallVerdict": "strong", "overallScore": 73, "confidence": 0.85, "bestMarket": {...},
    "dataSources": ["WITS","OEC","..."]
  }
}
```
**`/api/decision/recommendations`** adds `"recommendations": "<markdown exec summary + recommendations + action plan>"` (Brain-authored; deterministic fallback if the LLM is unavailable — never empty).

### 4.5 PDF / Report

The **PDF is generated client-side** (print-to-PDF of the branded `#cc-doc-print` layout) on the **website**. There is no server PDF binary endpoint. For the **app**, reproduce the report by fetching the same data and rendering it (see §10):
- `POST /api/decision` (scores + decision), `POST /api/simulation/compare` (scenario table), plus the project + last quote.
- Report identity is deterministic: `Report ID = LN-TCC-<first6 of projectId uppercased>-<YYYYMMDD>`; QR encodes `LeadNation Trade Report <reportId> | <exporter>-><importer> | HS <hs>`.
- Compliance report data: `POST /api/command-center/compliance`.
- Download entitlement (paywall): `GET /api/downloads/check?projectId=&region=` → `{allowed, freeAvailable, hasSubscription, price, currency}`; record a download with `POST /api/downloads/record`.

### 4.6 Brain  — prefix `/api/brain`

| Action | Method | Path |
|---|---|---|
| Ask (grounded answer) | POST | `/api/brain/ask` |
| Search knowledge | GET | `/api/brain/search?q=` |
| List engines | GET | `/api/brain/engines` |
| Status | GET | `/api/brain/status` |
| Conversation history | GET | `/api/brain/conversation/{session_id}` |
| Save conversation | POST | `/api/brain/save` |
| Get / set user context | GET `/api/brain/context/{user_id}` · POST `/api/brain/context` |

**Ask — request:** `{ "question": "Is UAE better than Saudi for this?", "session_id": "<uuid>", "user_id": "<firebase-uid>", "project_id": "c911...", "language": "en" }`
**Ask — response:** `{ "answer": "<markdown>", "sources": [...], "intent": {...} }`
> The app **sends context** (question + project_id + session_id + user_id); the **backend Brain responds**. Do NOT build a mobile AI.

---

## 5. Database Collections (shared MongoDB)

All documents store `_id` as a string (hex uuid), surfaced as `id`. Datetimes are ISO-8601 UTC strings. Ownership fields: `owner` (Firebase UID or guest session id), `ownerType`.

**`trade_projects`**
```
id, owner, ownerType, title, product, hs, exporter, importer, incoterm,
quantity, unit, destinationPort, transactionCurrency, globalCurrency, marginPct,
buyer, supplier, paymentMethod, shipmentMode, containerType,
costs:{exw,packing,inland,thc,customsDocs,freight,insurance},
assumptions:{}, notes, documents:[], stage, pinned:bool, isTemplate:bool,
lastQuote:{<quote response>}, timeline:[{at,activity}], createdAt, updatedAt
```

**`trade_project_scenarios`**
```
id, projectId, owner, createdBy, parentId, mergedFrom:[ids]?, version,
label, archived:bool, assumptions:{}, inputs:{<quote inputs + incoterm/paymentMethod/buyer/supplier/documents>},
outputs:{fob,cif,landed,selling,profit,marginPct,dutyRate,vatRate,currency,bestMarket},
quote:{<full quote>}, simulation:{}, scores:{8 scores}, decision:{...},
risk:number, profit:number, market:{...}, compliance:number,
executiveSummary, brainAnalysis, confidence:0..1, createdAt, updatedAt
```

**`trade_project_events`** (audit trail)
```
id, projectId, owner, type, text, meta:{}, at
// types: project_created, scenario_created/updated/compared/merged/archived,
//        simulation_executed, decision_computed, brain_recommendation,
//        quote_generated, buyer_changed, supplier_changed, currency_changed,
//        route_changed, document_uploaded, pdf_generated, admin_action, subscription_change
```

**`trade_project_brain_history`**
```
projectId, owner, kind ("recommendations" | "ask" | ...), advisor:"<markdown>", at
```

**`trade_project_versions`** — *reserved.* Version snapshots currently live in `trade_projects.versions[]` via `POST /projects/{pid}/version` (`{id,kind,label,snapshot,at}`). If the app needs standalone version records, migrate to this collection in a later phase (keep the API contract stable).

**`trade_project_reports`** — *reserved for the "My Reports history + shareable links" backlog item* (not yet populated). PDFs are currently generated client-side and not persisted server-side.

**Other relevant collections:** `pricing_config`, `payment_transactions`, `subscriptions`, `downloads`, `email_captures`, `paywall_events` (monetization) and the auth/profile store owned by the DigitalOcean backend.

---

## 6. React Native Implementation Guide (screens)

1. **Trade Command Center Home** — list of Trade Projects (`GET /api/projects`), pinned first, health badge per card, "New project" + templates. Pull-to-refresh.
2. **Project Dashboard** — header (title, exporter→importer, Incoterm, stage + `nextAction`), health rings from `project.health`, quick links to modules, activity timeline (`GET /api/events?projectId=`).
3. **Costing** — form for product/HS, countries, quantity, cost inputs, margin; on change debounce → `POST /api/command-center/quote`; render FOB/CIF/Landed waterfall + buyer comparison. Autosave patches via `PUT /api/projects/{pid}`.
4. **Simulation** — Digital Twin what-if (`/simulation/twin`) with sliders; scenario list with create/duplicate/merge/archive; version + confidence badges.
5. **Scenarios / Compare** — multi-select scenarios → `POST /api/simulation/compare`; render comparison table + winners; bar chart of profit/overall.
6. **Reports** — render the report from live data (§4.5); paywall check via `/api/downloads/check`; export/share PDF (Expo Print + Sharing).
7. **Brain Panel** — chat surface calling `/api/brain/ask` with `project_id` + `session_id`; show markdown; history via `/api/brain/conversation/{session_id}`.
8. **Settings** — profile (from shared auth), region/currency defaults, subscription status (`/api/account/me`).

State: use React Query (TanStack) for server cache + optimistic autosave; a `ProjectContext` equivalent holds the active project id + guest/auth session.

---

## 7. UI/UX Mapping (Website → Mobile)

| Website component | Mobile equivalent |
|---|---|
| Left sidebar module switcher | **Bottom tab bar** (Dashboard · Costing · Simulation · Reports) |
| Right/inline Brain panel | **Floating Brain button** → slide-up chat sheet |
| Command palette / global search | **Universal search screen** (products, HS, projects) |
| Score rings + expandable factor rows | **Collapsible score cards** (tap to expand explanation) |
| Scenario compare table (wide) | **Horizontally scrollable table** or stacked per-scenario cards |
| Print-to-PDF (`#cc-doc-print`) | **Expo Print → Share sheet** with the same layout |
| Modal paywall | **Bottom-sheet paywall** (email capture + plans) |
| Toasts (sonner) | Native toast / snackbar |

---

## 8. Authentication Integration (DO NOT replace)

Use the **existing LeadNation auth only**:
- **Same Firebase project** — **`trademate-new`**. Configure the Expo app with the identical Firebase config (env `EXPO_PUBLIC_FIREBASE_*` mirroring the website's `REACT_APP_FIREBASE_*`); add the app's iOS/Android bundle IDs to the `trademate-new` Firebase project.
- **Same DigitalOcean auth backend** — `REACT_APP_AUTH_API_BASE = https://leadnation-lfrhs.ondigitalocean.app/api`. This backend owns login/OTP, the **profile**, and the **5-digit Customer ID**.
- **Same Firebase UID → same MongoDB user/profile.** The FastAPI backend resolves identity from the Firebase ID token (`Authorization: Bearer <idToken>`), so a user's projects/scenarios/reports are automatically shared across web and app.

**Customer ID rule (permanent architecture):** IDs are numeric, exactly 5 digits (`00002`–`99999`), `00001` reserved for Super Admin, immutable, unique across web+mobile. The **backend allocates them** — the app must only **consume and display** the returned ID (validate `^\d{5}$` before showing). Never generate/modify IDs client-side.

**Do NOT create:** a new auth system, a new database, or a new user store.

**Auth flow in the app:** Firebase sign-in (email OTP via `POST {AUTH_API_BASE}/auth/send-otp` then `/auth/verify-otp`, or Firebase SDK email/password + Google) → obtain Firebase `idToken` → register/onboard via `POST {AUTH_API_BASE}/onboarding/register` (allocates the 5-digit Customer ID) → fetch profile `GET {AUTH_API_BASE}/v1/profiles/{uid}` → attach `Authorization: Bearer <idToken>` to all FastAPI `/api/*` calls.

**Business roles (select at signup):** `exporter`, `importer`, `supplier`, `manufacturer`, `farmer`, `cha` (Customs House Agent), `export_agent`, `consultant`. The app must offer the same role list.

**Profile sync (shared, two documents):**
- `users` collection — identity/platform record (Firebase UID, Customer ID, platform role user/admin).
- `profiles` collection — business profile (full name, business role, mobile, country, provider). `profiles.role` is the PLATFORM role (user/admin) and does NOT carry the business role — the business role (`user_role`) comes from onboarding/register. The app must read the profile from `GET /v1/profiles/{uid}` and preserve `user_role` from register, exactly as the website does.

---

## 9. Offline / Mobile Requirements

- **AsyncStorage caching:** cache the projects list and the active project (+ last quote) so the Dashboard opens instantly offline; revalidate on reconnect (React Query `staleTime`).
- **Draft projects:** allow creating/editing a project locally when offline; queue a `POST/PUT` and flush on reconnect. Mark drafts with a local `pendingSync` flag.
- **Resume incomplete projects:** persist the active project id + form state; on relaunch, restore the last screen and inputs.
- **Network failure handling:** the first quote can be slow (cold lane) — use a ≥30s timeout, show skeleton loaders, and retry with backoff. Never block the UI on the Brain; render deterministic results first, stream the Brain narrative after.
- **Never compute locally as a fallback.** If offline, show cached numbers with an "offline / last synced <time>" badge — do not approximate costing on-device.

---

## 10. PDF Sync

Same data, either direction:
- **Website → App:** a project (and its scenarios/decision) generated on the website is stored in MongoDB; the app opens the same project and re-renders the identical report from `/api/decision` + `/api/simulation/compare` + project data.
- **App → Website:** a project created in the app is immediately available on the website for print-to-PDF.
- **Deterministic report identity** guarantees both surfaces show the same **Report ID** and **QR** for the same project on the same date.
- Backlog: persist generated reports to `trade_project_reports` with shareable public/private links + expiry (so a report opened on web/app is byte-identical and shareable). Until then, both surfaces regenerate from the same live data.

---

## 11. Brain Integration

- **One Brain, on the backend.** The app sends **context** (question + `project_id` + `session_id` + `user_id` + `language`); the backend Brain returns grounded markdown.
- The Brain **explains/interprets/recommends/summarises** — it never invents numbers. Deterministic engines (costing, scores, decision) produce all figures.
- Persist chat via `/api/brain/save`; retrieve via `/api/brain/conversation/{session_id}`. Recommendation history is in `trade_project_brain_history`.
- **Do NOT** embed an on-device LLM or a separate mobile AI.

---

## 12. Testing Checklist (cross-surface parity)

- [ ] **Website creates project → App opens it** (same `id`, fields, health).
- [ ] **App edits project → Website sees update** (autosave via `PUT /projects/{pid}`; refresh reflects change).
- [ ] **Scenario sync** — scenario created/edited/merged on one surface appears on the other (`/simulation/scenarios`).
- [ ] **Decision/score parity** — `/api/decision` returns identical scores & verdict on both surfaces for the same project.
- [ ] **Brain history sync** — `/brain/conversation/{session_id}` and `trade_project_brain_history` consistent across surfaces.
- [ ] **PDF sync** — same Report ID + QR + figures on web print and app export.
- [ ] **User ID sync** — same 5-digit Customer ID shown on web and app (validated `^\d{5}$`).
- [ ] **Profile sync** — profile edits on one surface reflect on the other (shared DO auth backend).
- [ ] **Auth parity** — same Firebase UID resolves to the same projects on both surfaces.
- [ ] **Offline** — draft created offline flushes on reconnect; no client-side number fabrication.

---

---

## 13. Deep Linking (future — mobile production phase; NOT in website v1.0)

**Permanent LeadNation deep-linking architecture. Do NOT use Firebase Dynamic Links (deprecated).** Use native app links + Expo Linking + website canonical URLs.

- **Android App Links** — host `/.well-known/assetlinks.json` on `leadnation.app` (SHA-256 fingerprints of the app signing keys).
- **iOS Universal Links** — host `/.well-known/apple-app-site-association` on `leadnation.app` (app's Team ID + bundle ID, path patterns).
- **Expo Linking** — configure the `scheme` + `associatedDomains` (iOS) and `intentFilters` (Android) in `app.json`; parse inbound URLs with `expo-linking`.
- **Website canonical URLs** — the single source of truth for every shareable entity:
  - `https://leadnation.app/project/{project_id}`
  - `https://leadnation.app/report/{report_id}`

**Behaviour:**
- App installed → the OS opens the LeadNation app → routes to Trade Command Center → same Project/Report (fetched by the SAME `project_id`/`report_id` from the SAME backend).
- App not installed → the website opens → shows a content preview → "Download App" CTA (Play Store / App Store).

**Rules:** no data duplication, no mobile-only projects; the same Firebase UID, Customer ID, MongoDB `project_id`/`report_id` and backend APIs are used everywhere. *(Website v1.0 does NOT implement `/project/{id}` or `/report/{id}` deep-link routes yet — that is a mobile-phase task. Backend already keys everything by these IDs.)*

## 14. Mobile Analytics (mirror the website, env-driven, consent-gated)

- **Website:** GA4, Google Tag Manager, Microsoft Clarity, Meta Pixel (opt-in via cookie consent).
- **Mobile:** **Firebase Analytics**, **Crashlytics**, **Performance Monitoring** (same `trademate-new` Firebase project). Gate analytics/marketing behind an on-first-launch consent screen (Essential always on).
- **Use the SAME event names** for cross-surface funnels: `trade_project_created`, `quote_generated`, `brain_query`, `pdf_downloaded` (website uses `pdf_report_downloaded` — align on one name during app build), `subscription_started` (+ `user_registered`, `user_login`, `command_center_opened`, `scenario_created`, `payment_success`).
- **Privacy:** never send Customer ID, email, phone, documents or confidential trade data. Only anonymous params (region, incoterm, plan, event name).

## 15. Final Handoff Checklists

### 15.1 API checklist (verify each is documented above with URL/method/request/response/auth)
- [ ] Projects API — list, create, templates, load, update/autosave, delete, pin, duplicate, version (§4.1)
- [ ] Costing API — quote, markets, insights, explain, compliance, ports, autofill (§4.2)
- [ ] Simulation API — twin, scenarios CRUD, duplicate, merge, delete, compare (§4.3)
- [ ] Decision API — /decision, /decision/recommendations (§4.4)
- [ ] Scores — returned inside decision/twin responses (8 explainable scores) (§4.4)
- [ ] Reports/PDF — data via decision + compare + project; download check/record; compliance (§4.5)
- [ ] Brain API — ask, search, engines, status, conversation, save, context (§4.6)
- [ ] Profile API — `{AUTH_API_BASE}` onboarding/register, /v1/profiles/{uid}, OTP (§8)
- [ ] Admin API — admin-protected endpoints (Firebase admin claim or X-Admin-Token); events at `/api/admin/events`

### 15.2 App screen checklist
- [ ] Auth: Login · Signup · Google Login · Forgot Password · Email verification
- [ ] Profile: role select (8 roles) · users+profiles sync · Customer ID display (validate `^\d{5}$`)
- [ ] Dashboard · Trade Projects · Project Overview
- [ ] Trade Costing: FOB · CIF · Landed Cost · Currency Conversion · Market Comparison
- [ ] Compliance · Documents · Routes · Risk
- [ ] Simulation · Decision Scores · Reports · PDF Download
- [ ] Brain Assistant (floating)

### 15.3 Shared auth verification checklist
- [ ] Same Firebase project `trademate-new`
- [ ] Same Firebase UID resolves to the same Mongo user/profile on web + app
- [ ] Same 5-digit Customer ID (backend-allocated; app only displays/validates; `00001` = Admin reserved)
- [ ] No duplicate user creation; app never generates/mutates Customer IDs
- [ ] `Authorization: Bearer <idToken>` on every `/api/*` call

### 15.4 Database collection checklist (shared MongoDB `leadnation`)
- [ ] `trade_projects` · `trade_project_scenarios` · `trade_project_events` · `trade_project_brain_history`
- [ ] `users` · `profiles` (shared identity/profile)
- [ ] `pricing_config` · `payment_transactions` · `subscriptions` · `downloads` · `email_captures` · `paywall_events` · `events` (analytics)
- [ ] Reserved: `trade_project_reports`, `trade_project_versions`

### 15.5 Production deployment checklist (website v1.0)
- [ ] Save to GitHub → tag `v1.0-leadnation-command-center-production-ready`
- [ ] Set `CORS_ORIGINS` to prod web + app origins
- [ ] Add prod domain to Firebase Authorized domains + DO backend CORS allow-list
- [ ] Rotate `ADMIN_TOKEN` / `ADMIN_PASSWORD`
- [ ] Stripe live key + webhook `{host}/api/webhook/stripe`
- [ ] Confirm `MONGO_URL`/`DB_NAME` = production Atlas (shared with app)
- [ ] Verify Mongo indexes on first boot ("MongoDB indexes ensured")
- [ ] Set analytics IDs when ready (GA4/GTM/Clarity/Meta)
- [ ] Smoke test: create project → quote → scenario → decision → recommendations → PDF

*Baseline: Volume 1 + Volume 2 Phase 2A. No new feature work until website + mobile are live. Keep API contracts stable; extend, never break.*
