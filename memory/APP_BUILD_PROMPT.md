# LeadNation Mobile App — Command Center Build Prompt (paste into Emergent)

> Copy everything in the "PROMPT" block below into a new Emergent app job to build the
> React Native (Expo) mobile app. It is written so the app connects to the SAME backend,
> SAME Firebase, SAME MongoDB and SAME data as the website — no duplicated business logic.
> Full technical contracts are in `/app/memory/TRADE_COMMAND_CENTER_APP_INTEGRATION_GUIDE.md`.

---

## ══════════ PROMPT (copy from here) ══════════

**Project:** Build the **LeadNation Trade Command Center** mobile app in **React Native (Expo, TypeScript)**.

**Golden rule — thin client:** The app must **NOT duplicate any business logic**. All costing, scoring, simulation, decisions, pricing and AI run on our existing shared backend. The app only renders data, edits inputs, and calls APIs. Do NOT build a second AI, a second database, or a second auth system.

### 1) Connect to the existing shared backend (do not create new infra)
- **Backend base URL:** store `EXPO_PUBLIC_API_BASE` in env; all calls hit `${EXPO_PUBLIC_API_BASE}/api/...`. (Use our production backend URL; never hardcode.)
- **Auth backend (profiles + Customer ID):** `EXPO_PUBLIC_AUTH_API_BASE = https://leadnation-lfrhs.ondigitalocean.app/api`.
- **Same MongoDB, same data:** a project created on the website must be visible in the app and vice-versa. Nothing is stored in a new database.

### 2) Authentication (shared, do NOT replace)
- Use **Firebase Authentication** with the SAME Firebase project as the website (config from env: `EXPO_PUBLIC_FIREBASE_*`).
- Flow: Firebase sign-in (email/password or Google) → get Firebase **ID token** → fetch profile `GET {AUTH_API_BASE}/v1/profiles/{uid}` → attach `Authorization: Bearer <idToken>` to every `/api/*` call.
- **Customer ID rule (permanent):** numeric, exactly 5 digits (`00002`–`99999`), `00001` reserved for Super Admin, immutable, unique across web + app. The **backend allocates it** — the app only **displays and validates** it (`^\d{5}$`). Never generate/modify IDs on device.
- One Firebase UID → one shared Mongo profile → one identity. No duplicate user creation.

### 3) Screens (bottom-tab navigation)
Build these screens; each maps to existing APIs (see contracts doc):
1. **Home / Command Center** — list Trade Projects (`GET /api/projects`), pinned first, health badge per card, "New Project" + templates (`GET /api/projects/templates`). Pull-to-refresh.
2. **Project Dashboard** — header (title, exporter→importer, Incoterm, workflow stage + `nextAction`), health rings from `project.health`, activity timeline (`GET /api/events?projectId=`), quick links to modules.
3. **Costing** — inputs (product/HS, countries, quantity, unit, cost inputs, margin); debounce → `POST /api/command-center/quote`; render FOB → CIF → Landed waterfall + buyer-market comparison. Autosave via `PUT /api/projects/{pid}` ({patch, activity}).
4. **Simulation / Digital Twin** — what-if via `POST /api/simulation/twin` (sliders for margin/freight/insurance/incoterm); scenario list (`/api/simulation/scenarios` CRUD, duplicate, merge, archive), version + confidence badges.
5. **Scenarios / Compare** — multi-select → `POST /api/simulation/compare`; comparison table + winners + a simple bar chart.
6. **Decision & Scores** — `POST /api/decision` (8 explainable Trade Scores + decision objects + recommended actions); "Generate recommendations" → `POST /api/decision/recommendations` (Brain markdown; deterministic fallback).
7. **Reports** — render the report from live data (`/api/decision` + `/api/simulation/compare` + project); paywall check `GET /api/downloads/check`; export via **Expo Print + Sharing** (same layout, Report ID `LN-TCC-<first6 pid>-<YYYYMMDD>` + QR).
8. **Brain Panel** — floating Brain button → chat sheet calling `POST /api/brain/ask` ({question, session_id, user_id, project_id, language}); render markdown; history via `GET /api/brain/conversation/{session_id}`.
9. **Account / Settings** — profile (shared auth), subscription status (`GET /api/account/me`), region/currency defaults, plans (`GET /api/pricing/config?region=`), checkout via `POST /api/payments/checkout`.

### 4) UI/UX mapping (from website)
- Website left sidebar → **mobile bottom tabs** (Dashboard · Costing · Simulation · Reports).
- Right Brain panel → **floating Brain button** → slide-up sheet.
- Command palette → **universal search screen** (products, HS, projects).
- Score rings + factor rows → **collapsible score cards**.
- Wide compare table → **horizontally scrollable table** or stacked cards.
- Aesthetic: dark, premium, cyan (#00C2FF) accent, glass surfaces, rounded-2xl, subtle motion — match the website’s "trade OS" feel.

### 5) State, offline & performance
- Use **React Query (TanStack)** for server cache + optimistic autosave; a light `ProjectContext` holds the active project id + session.
- **AsyncStorage** caching for the projects list + active project (offline read); **draft projects** editable offline and flushed on reconnect (`pendingSync` flag).
- **Never compute numbers on device** — if offline, show cached values with an "offline / last synced" badge.
- First quote per fresh HS+lane can take ~15-25s (cold backend cache) — use ≥30s timeout, skeletons, retry with backoff. Render deterministic results first; stream the Brain narrative after.

### 6) Analytics & privacy (mirror website)
- Env-driven analytics only (Firebase Analytics / GA4). Respect a **cookie/tracking consent** screen on first launch (opt-in for analytics/marketing; essential always on).
- **Never send** Customer ID, email, phone, documents or confidential trade data to analytics. Only anonymous events (region, incoterm, plan, event name).
- Reuse our event names: user_registered, user_login, command_center_opened, trade_project_created, quote_generated, scenario_created, brain_query, pdf_report_created, pdf_report_downloaded, payment_attempt, subscription_started, payment_success.

### 7) Legal
- Link the existing hosted legal pages (Privacy, Terms, Cookie, Disclaimer, Refund) in Settings + signup + checkout (same URLs as the website: `/legal/*`).

### 8) Acceptance / parity tests
- Website creates project → app opens it (same id/fields/health).
- App edits project → website sees the update.
- Scenario, decision/score, Brain history, PDF (Report ID + QR), Customer ID and profile all match across web + app.
- Auth: same Firebase UID resolves to the same projects on both surfaces; no duplicate users.

**Deliverables:** Expo app (TypeScript) with the screens above wired to the existing backend, shared Firebase auth, React Query caching, offline drafts, consent-gated analytics, legal links, and a short README listing all required `EXPO_PUBLIC_*` env vars. Do NOT modify backend logic, Brain, database, auth, pricing or user flows — the app is a client of the existing v1.0 backend.

## ══════════ END PROMPT ══════════

---

### Why this builds easily on Emergent
- The backend, auth, DB and business logic already exist and are documented — the app job is pure UI + API wiring, which Emergent handles well.
- Every screen maps 1:1 to a documented endpoint (no guesswork).
- Shared Firebase + Mongo + Customer-ID means zero backend duplication; connection is guaranteed by using the same env values.
- Keep `TRADE_COMMAND_CENTER_APP_INTEGRATION_GUIDE.md` open alongside this prompt for exact request/response JSON.
