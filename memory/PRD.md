# LeadNation — Global Trade Intelligence Portal

## 🔒 RELEASE FREEZE (2026-07-05) — Deployment Prep + Mobile Handoff
Feature development STOPPED. Baseline = **Volume 1 + Volume 2 Phase 2A** → first production release, tag `v1.0-leadnation-command-center-production-ready`. Do NOT start Volume 2B/2C/2D, Volume 3 or 4 until website + mobile app are live.
- **Cookie Consent (GDPR/CCPA) DONE:** `CookieConsent.jsx` + consent-aware `analytics.js` — Accept All / Reject Non-Essential / Manage Preferences; Essential always-on, Analytics (GA4/GTM/Clarity) + Marketing (Meta) opt-in; analytics load ONLY after consent; stored in localStorage; footer "Cookie Preferences" to change; first-party anonymous `/api/track` retained (PII-scrubbed). Verified E2E.
- **Analytics activation DONE:** env-driven, consent-gated, standard EVENTS wired, privacy scrubber, first-party pipeline → `db.events` (admin-dashboard-ready). See `ANALYTICS.md`.
- **App build prompt:** `/app/memory/APP_BUILD_PROMPT.md` — paste-ready Emergent prompt to build the RN/Expo Command Center connected to the same backend/Firebase/Mongo (thin client). Full contracts in `TRADE_COMMAND_CENTER_APP_INTEGRATION_GUIDE.md`.
- Delivered earlier: mobile integration guide, `PRODUCTION_READINESS.md`, 5 legal pages, MongoDB indexes.

## Implemented (2026-07-05) — VOLUME 2 PHASE 2A: Simulation & Decision Engine
Layered architecture (permanent): **Trade Project → Reactive Graph → Simulation Engine → Decision Engine → LeadNation Brain → Report**. Deterministic maths run on the backend; the Brain only explains/interprets (never fabricates numbers). Verified iteration_24 (backend 19/19 pytest; UI module renders; Brain-crash bug FIXED).
- **Separate collections (permanent):** `trade_project_scenarios`, `trade_project_events`, `trade_project_brain_history` (+ existing `trade_projects`). Scenarios are NOT embedded in the project doc.
- **Live Data Adapter Framework (`adapters.py`):** one standard interface (`Adapter.fetch → AdapterResult{value,source,sourceTier,confidence,aiEstimated,reason,assumptions}`); tiers gov>official>live_commercial>knowledge_base>historical>ai_estimate. Wired adapters: duty(WITS·gov), fx(official), trade_stats(OEC), incentives(DGFT/CBIC·gov), freight(ai_estimate). Future feeds `register()` and plug in. `GET /api/adapters`, `POST /api/adapters/run`.
- **Simulation Engine + Scenario Builder (`simulation.py`):** `POST /api/simulation/twin` (Digital Twin what-if, instant recompute, no save); scenario CRUD `/api/simulation/scenarios` (+duplicate, merge, archive, delete, versioning); `/api/simulation/compare` (rows + winners per metric). Each scenario stores inputs/outputs/scores/decision/confidence/parentId/version.
- **Trade Score Engine (`scores.py`):** 8 explainable deterministic scores (profitability, risk, compliance, competition, market, buyer, supplier, overall) — each with value/color/factors/explanation.
- **Decision Engine (`decision_engine.py`):** `build_decision` consolidates outputs into structured decision objects (6 domains) + recommendedActions + verdict + confidence. `POST /api/decision`. `POST /api/decision/recommendations` → Brain reasons over STRUCTURED objects (+ deterministic fallback so output is never empty).
- **Universal Audit Trail (`events.py`):** `trade_project_events` logs project_created/scenario_*/decision_computed/brain_recommendation/quote_generated/buyer|supplier|currency|route_changed etc. `GET /api/events?projectId=`.
- **Frontend Simulation module** (Command Center tab `cc-mod-simulation`): Trade Score Engine (expandable factor explanations), Decision Engine (prioritised actions + Brain recommendations), Scenario Builder with Digital Twin inline editing (margin/freight/insurance/incoterm), compare table + recharts bar chart + winners. Renders whenever product/HS present.
- **PDF integration (Volume 2):** `CommandCenterReport.jsx` self-fetches /decision + /simulation/compare and adds Trade Scores, Scenario Comparison, Decision recommendations, Report ID + QR code, generation date.
- Bug FIXED: Brain provider crashed on list `data` payloads (providers.py now tolerates list/dict; decision_engine passes dict-shaped data).

## Implemented (2026-07-01 PM) — Pricing Engine + Subscriptions + India Globe fix
- **P0 FIXED — 3D Trade Globe India map:** now overlays the official India political boundary (includes J&K & Ladakh, extent to lat ~37°) from a locally-served TopoJSON (`/geo/india-states.json`, merged via topojson-client). World-atlas India (truncated) is filtered out; India is highlighted in violet. Verified visually via screenshot. (`TradeGlobe.jsx`)
- **Centralized Pricing Engine (`backend/pricing.py`)** — SINGLE SOURCE OF TRUTH for all prices. Mongo `pricing_config` doc; endpoints `/pricing/config` (public, per-region), `/pricing/track` + `/pricing/lead` (funnel + email capture, guest), `/pricing/admin` GET+PUT (admin), `/pricing/admin/analytics`. Helpers `resolve()`, `gateway_for()`, `get_config()`. **NOTHING is hardcoded downstream** — `monetize.py` now reads every price from the engine (download / monthly / annual, IN & INTL). Verified iteration_23 (11/11 backend 100%).
- **Admin Pricing tab (`PricingManager.jsx`)** — Admin edits India+International prices for all plans, plan labels/taglines/active, gateway enable toggles (Stripe/Razorpay + future), settings (freeFirstDownload, emailCaptureBeforePaywall, Most Popular plan) + live paywall funnel analytics. New tab in `/admin-cms`.
- **Public Pricing page (`/pricing`, `Pricing.jsx`)** — region toggle (IN₹/INTL$), 3 plan cards, Most Popular badge, annual-savings %, feature comparison table, conversion tracking. Added to top nav.
- **Subscription system:** monthly (30d) + annual (365d) passes via Stripe; `create_checkout` supports kind download|monthly|annual|subscription; sub duration from `SUB_DAYS`.
- **Paywall UX upgrade (CommandCenter Reports + AccountPage Billing):** email capture before paywall, annual+monthly plan options with Most Popular badge, dynamic prices, "just this once" pay-per-report link, conversion tracking events. AccountPage billing shows dynamic monthly/annual cards.

## PERMANENT ARCHITECTURAL RULE — Customer IDs (option c, user-mandated)
- The website NEVER generates/modifies/reserves/enforces Customer IDs. Allocation is owned SOLELY by the shared LeadNation DigitalOcean backend (`/api/onboarding/register`, `_counters`).
- Backend rule (to be enforced on DO backend, OUT OF THIS CODEBASE'S REACH): IDs are numeric, exactly 5 digits (00002–99999), `00001` reserved for Super Admin, immutable, unique across web+mobile.
- Website responsibility: only VALIDATE the returned ID matches `^\d{5}$` before display; never create/modify. (⚠️ DO-backend change is a user/backend-team action; front/local backend cannot alter it.)

## Implemented (2026-07-01 AM) — Monetization + Account + Costing UX + dropdown fix
- **Dropdown white-bg bug FIXED** (index.css `select option` dark styling) + **Product→HSN autocomplete** on Start screen (verified iteration_21, 100%).
- **Costing UX:** current-stage indicator ("Stage X of 9"), sidebar tooltips, ⌘K button renamed **"Menu"**, **(i) info tooltips** on all cost fields, **Unit dropdown** (MT/KG/Ton/Container…), **Destination Port dropdown** (per country), 11 Incoterms + info, **Autofill with Brain** button (verified iteration_20, 100%).
- **Monetization (`monetize.py`):** Stripe pay-per-download (first download FREE, then ₹25 IN / $1 INTL) + monthly unlimited pass; `/payments/checkout|status|pricing`, `/webhook/stripe`, `/downloads/check|record` (first-free logic), GST-style invoices, referral codes. Owner = Firebase UID or guest Trade-Session. **Razorpay slot ready (RAZORPAY_KEY_ID env) — keys pending from user (2-3 days).** Verified iteration_22 backend 100% (8/8).
- **Account page (`AccountPage.jsx`, /account):** Instagram-style header (avatar, name, **role badge**, **country+flag**, **User ID**, mobile, email), stats, tabs: Downloads / Projects / Saved Buyers / Invoices / Billing (monthly pass) / Referral. Profile edit (role/country/mobile) with local override on DO profile. Post-Stripe-redirect auto-completes the paid download + prints PDF. Verified iteration_22 (account 100%).
- **Paywall gate** on Command Center Export PDF: not-signed-in → "Sign in to download" modal; signed-in → free/pass → download, else pay modal (₹25/$1 or monthly pass). Verified working via reproduction (login-gated E2E to be validated on production — login CORS-blocked in preview).
- **Admin:** `/account/admin/users` + `/account/admin/{owner}` (require_admin) — revenue, downloads, per-user view.
- Known cosmetic: a React dev-only "span in option" console warning (no functional impact).

## Monetization plan (agreed)
- Free: build quotes/projects. Paid: PDF download — first free, then ₹25 (IN, Razorpay) / $1 (INTL, Stripe), or monthly unlimited (₹499 / $9). Geo by profile country. Referral + credit-pack/subscription upsell.

## Backlog / next
- **Razorpay wiring** (awaiting user keys) — INR ₹25 + ₹499/mo via Razorpay; Stripe handles INTL.
- Stripe webhook secret + production verification of login-gated download & account sync.
- Vol 2 (Digital Twin), Vol 3 (live data adapters, proactive alerts, Knowledge-Quality), Vol 4 (collaboration, white-label PDF, ERP).


- New full-screen workspace at **`/command-center`** (sidebar · center · right Brain panel). Home CTA + customs tab now point here.
- **Trade Projects** (`backend/projects.py`, `trade_projects` collection): create/autosave/load/recent/pin/duplicate/templates/delete; **guest (anonymous UUID) ↔ Firebase UID ownership with auto-merge on login** (`/projects/merge`). Production-ready + testable in preview without login.
- **Universal Project Context** (`frontend/src/lib/ProjectContext.jsx`): one state spine, **reactive computation graph** (change any input → quote/duty/tax/currency/markets/health/Brain recompute, no re-click), `patchCosts` (stale-closure-safe nested edits), persist-merge preserving freshest lastQuote/costs.
- **Modules**: Overview (Executive Dashboard + Project Summary + 7 health score rings + alerts + timeline), Trade Costing (reactive FOB→CIF waterfall + Explain on every KPI), Market Research (buyer comparison), Compliance (per-country duty+docs+Brain brief), Documents (checklist), Routes, Risk (score bars), Buyers/Suppliers (Brain + app CTA), Reports (PDF export + version history), Brain (project-aware chat), Settings (assumptions panel + project fields).
- **Workflow engine** (9 stages, clickable stepper, Brain-aware), **Activity Timeline**, **Version History**, **Assumptions Panel**, **Data-Source badges** (Govt/Live/Brain/Manual/Historical/Estimate), **Command Palette (⌘K)**, **Explain Everything** (`/command-center/explain`).
- **PDF export** (`CommandCenterReport.jsx`): branded Quote + cost waterfall + buyer comparison + **per-destination-country compliance report**.
- Backend: `/command-center/quote` (parallelized 8-market comparison), `/explain`, `/compliance`, `/markets`; `duty_engine` WITS year-window narrowed to 6 for latency. Client timeout raised to 90s for cold lanes.
- Docs: `TRADE_COMMAND_CENTER_VOL1.md` (blueprint) + `TRADE_COMMAND_CENTER_VOL1_COMPLETION.md` (as-built report, 10 diagrams, checklist, Volumes 2–4 roadmap).
- **Permanent rule adopted:** every feature must belong to / enhance a Trade Project. **3-Click Rule** for major tasks.
- Verified: test_reports/iteration_19.json — 100% backend (18/18), 100% frontend functional. Minor (fixed): strokeLinecap warning, sort tiebreaker. Known: cold first-run lane ~15-25s (cached after); compliance first-load shows spinner.

## Earlier (2026-06-30) — Trade Command Center calculator (iteration_18, 100% pass)
- Renamed Compile Data → Trade Command Center tab; world-class FOB/CIF/landed calculator; buyer-landed-cost comparison; dual+global currency; AI advisor; Home section before Services.

## Backlog → mapped to Volumes 2–4 (see completion report)
- **Vol 2** Digital Twin scenario simulation (consumes Assumptions Panel) + confidence scoring + math models.
- **Vol 3** Live data adapters (freight/buyer/supplier/govt/customs/shipping/banking APIs), proactive Brain alerts, Brain co-pilot site-wide, Knowledge-Quality confidence engine.
- **Vol 4** Collaboration (teams/comments/approvals), white-label Quote PDF + My Reports + shareable links, ERP integration, security/deploy hardening.
- Pending/partial: real Buyers/Suppliers datasets, per-value confidence+timestamp, live shipment tracker, cold-latency bulk-tariff store.


- Delivered **Volume 1 — Master Product Blueprint** (`/app/memory/TRADE_COMMAND_CENTER_VOL1.md`): full product architecture (vision, philosophy, user journeys, dashboard, workspaces, Brain integration, knowledge flow, Trade Projects, Digital Twin, system + dependency diagrams, ImpexQ competitor analysis, 2026–2035 roadmap). All future features reference this.
- **Backend `costing_engine.py`** (`/api/command-center/*`), registered in server.py:
  - `POST /quote` — 100% deterministic, instant: Ex-Works→FOB→CIF 9-row waterfall, destination duty (WITS) + VAT (`VAT_BY_CODE`, ~55 countries) + landed cost, margin→selling price, **buyer-landed-cost comparison** across up to 8 markets (sorted ascending), **dual + global + exporter-local currency** conversion (live FX), export incentives (RoDTEP/GST/Drawback/Adv. Auth for India origin), indicative routes/transit. Verified FOB=80500/CIF=85600 for HS 100630 India→Germany ×1000.
  - `POST /insights` — separate call so numbers render first; LeadNation Brain (live `gpt-5.4-mini`) returns grounded markdown advisor (insights, best market, savings, risks). Verified live + grounded.
  - `GET /markets` — 146 countries.
- **Frontend** `CustomsCompliance.jsx` → `CommandCenterTool`: tab renamed "Compile Data" → **"Trade Command Center"** (first tab). Lane setup (product autocomplete, export/import, qty+unit, **transaction currency + user-picked global currency**, margin), editable BLANK cost build-up with **live FOB/CIF preview as you type**, KPI cards (3 currencies each), cost waterfall, duty/tax panel, ranked buyer-comparison table (★ best), multi-currency quote, incentives+routes, **AI Trade Advisor** (Brain, progressive), Print/Save quote (PDF via `#cc-print` print CSS), Ask the Brain.
- **Home**: new `home-command-center` section BEFORE Services, tagline "The World's First AI-Powered Global Trade Operating System." + CTA to /customs-compliance.
- Hero/SEO of /customs-compliance updated to Command Center framing.
- Verified: test_reports/iteration_18.json — 100% backend (11/11) + 100% frontend + 4 regression tabs, zero issues.
- User choices honoured: build-all (1a), user picks global currency (2c), blank cost fields (3b). Latency: deterministic instant + Brain streams in via separate /insights call.

## Backlog directly from Vol 1 (next priorities)
- **P1** Trade Projects: save/load/duplicate stateful projects to the account; templates; shareable client links.
- **P1** Quote PDF polish (branded white-theme proposal) + My Reports history.
- **P1** Digital Twin scenario simulation (currency/freight/duty/delay deltas → live profit).
- **P1** Proactive Brain alerts (duty/FX/freight/policy thresholds).
- **P1** Increase Brain involvement across other tools (context co-pilot) + Knowledge Quality (live vs estimated) + feedback → Admin Knowledge Gaps.
- **P2** Live data adapters (real freight indices, premium buyer/supplier data, govt APIs); Vols 2–4.
- **P1** Legal pages; Analytics activation (GA4/GTM/Clarity/Meta env scaffolding present).


## Implemented (2026-06-30) — P1: Dual currency + Premium Trade Intelligence Report
- [x] **Dual currency (Compile Data)**: backend auto-detects the exporter country's local currency (`duty_engine.CURRENCY_BY_CODE`) + user's transaction currency; `/api/compile/report` returns live FX + landed cost in USD, exporter currency AND transaction currency. UI panel shows all three. (cache bumped to `v2:`). Verified: India→INR, USA→USD.
- [x] **Premium Trade Intelligence Report** (`frontend/src/components/TradeIntelReport.jsx`): branded, white-theme, 12-section printable report (cover, snapshot KPIs, executive brief, HS classification, global stats + trend bars, top importers/exporters, duty & benefits, tariff comparison, dual-currency FX, landed cost, logistics, next steps, sources+disclaimer). Client-side **Print / Save as PDF** via `@media print` in index.css (renders only `#trade-report-print`). Overlays use React portals to escape transformed ancestors.
- [x] **Lead Capture gate**: signed-out users must submit Name/Email/Company/Country (+optional phone) → `POST /api/leads` (source `trade-intelligence-report`, report context in message) → saved to Lead CMS, then report opens. Signed-in users skip the gate. Verified end-to-end in-browser + lead persisted to CMS.
- NOTE: HSN Google-style autocomplete was already present in Compile/Duty/TradeStats tabs (pre-existing).
- ⏳ Pending user input: increase Brain involvement + add more to Brain replies (user reported Brain latency; will share specifics).

## Implemented (2026-06-30) — Auth FINALIZED: website is a pure client of the deployed shared backend (NO proxy, NO local DB)
- [x] Frontend now calls `https://leadnation-lfrhs.ondigitalocean.app/api` DIRECTLY for ALL identity (env `REACT_APP_AUTH_API_BASE`, never hardcoded). New `src/lib/authApi.js` (Firebase Bearer interceptor); `AuthContext` repointed.
- [x] Endpoints wired & E2E-verified server-side: resolve-customer-id → Firebase login → `GET /api/v1/profiles/{uid}` (current-user source; DO has NO `/auth/me`) → idempotent `onboarding/register` → admin `admin_v2/users`. OTP via `send-otp`/`verify-otp` (body `{type:"email",value,otp}`; DO has NO `request-otp`).
- [x] Deleted local `accounts.py` — website does ZERO identity DB writes. Local backend retained ONLY for website content (Brain, trade-intel, duty, compile, customs, CMS). `core.require_admin` only READS shared `users.role`.
- ⚠️ CORS: production `leadnation.app` allowed (login works in prod); **Emergent preview origin still CORS-blocked (400)** → backend owner must whitelist `global-trade-hub-176.preview.emergentagent.com` to test login in-preview. Integration verified via curl.


## Problem Statement (verbatim)
Build a premium 3D website for the LeadNation app to drive organic traffic, account registrations and app downloads. Tabs: Home (3D animated globe, moving pictures/videos, search bar), Customs & Compliance, Trade News, Contact Us (with map + Instagram), Expo, Product Info. Floating WhatsApp on all pages. India-focused features. Every page has Download App + Create Account CTAs. References: Apple, Jacob & Co, Tesla, Stripe, OpenAI. Color palette: #0A2540 / #00C2FF / #7C3AED / #050816. Hosting: DigitalOcean (deployment-ready). Engines are mocked Phase-1; API-ready for real backend later.

## Architecture
- **Frontend**: React 19 + react-router 7, react-globe.gl (Three.js), framer-motion (available), Tailwind CSS, @phosphor-icons/react, topojson-client (country outlines on globe). Dark cinematic theme (Manrope display + IBM Plex Sans + JetBrains Mono).
- **Backend**: FastAPI + Motor (MongoDB). All endpoints under `/api/*`. Engines (`/customs-compliance`, `/trade-news`, `/expos`, `/product-info`, `/india-features`, `/search`) return curated mock data — replace with real engine calls later.
- **Storage**: MongoDB (`leads` collection persists contact submissions).
- **Routing**: `/`, `/customs-compliance`, `/product-info`, `/expo`, `/trade-news`, `/contact`.

## User Personas
- **Indian SME exporters** — need GST, DGFT, RoDTEP, FTA help.
- **Global importers & wholesalers** — need country-specific duty + cert info.
- **Investors & partners** — need an investor-grade landing experience.

## Core Requirements (static)
1. 3D animated globe with arcs from Indian cities to global trade hubs.
2. Search bar (products + countries).
3. Six dedicated tabs.
4. Floating WhatsApp button (number +91 82371 61088).
5. Every page CTAs: Download App (Coming Soon · App Store + Play Store) + Create Account.
6. Contact page with email/whatsapp/Instagram/address + embedded OpenStreetMap.
7. India-first features section.

## Fixed (2026-06-29) — Auth bug fixes (email verification + Google)
- [x] **Email verification via TEST OTP**: `/api/auth/request-otp` + `/api/auth/verify-otp` (code `123456`, env `TEST_OTP`) marks Firebase `email_verified` + Mongo `users.is_email_verified`. Account page shows a verify card (enter 123456 → flips to Verified); frontend force-refreshes the ID token. Verified for account 00009. (Swap TEST_OTP for a real OTP/SMS provider later.)
- [x] **Google sign-in graceful failure**: `googleErr()` maps `auth/unauthorized-domain` etc. to a friendly message instead of crashing. ROOT CAUSE: the Emergent preview domain is not in Firebase Authorized Domains — Google works on leadnation.app/Vercel (already whitelisted). To test Google in preview, add `global-trade-hub-176.preview.emergentagent.com` in Firebase Console → Auth → Settings → Authorized domains.
- Verified: test_reports/iteration_17.json — 3/3 backend + UI flows PASS. Throwaway users cleaned (DB = 00001 + 00009).


## Implemented (2026-06-29) — SHARED LOGIN PHASE (Firebase + Atlas, app-interoperable)
- [x] **ONE identity, ONE database** with the mobile app: switched backend to shared **MongoDB Atlas DB `leadnation`** + shared **Firebase project `trademate-new`** (Email/Password + Google). Passwords live ONLY in Firebase.
- [x] `firebase_auth.py` — inits Firebase Admin from `FIREBASE_SERVICE_ACCOUNT_B64`, verifies `Authorization: Bearer <firebaseIdToken>` on protected routes.
- [x] `accounts.py` — `/api/auth/resolve-customer-id`, `/api/onboarding/register` (idempotent Customer-ID allocation via shared `_counters`, one uid→one customer_id), `/api/auth/me`, `/api/admin_v2/users`, `DELETE /api/admin_v2/users/{cid}/hard-delete` (purges Mongo + Firebase Auth + Firestore; protects 00001 & self). users/profiles schema matches the app exactly (additive).
- [x] Admin migrated from JWT/bcrypt → **shared Firebase admin** (`admin@leadnation.app` / `00001` / role:admin). `core.require_admin` now verifies Firebase token + `users.role=='admin'` (legacy X-Admin-Token kept as emergency fallback only). Removed the separate `admin_users` store.
- [x] Frontend: `firebase.js` + `AuthContext` (email/pw, Google, Customer-ID login, password reset, email verify, session persistence) + axios Bearer interceptor. New `/login`, `/signup` (with business role), `/forgot-password`, `/account` pages. Nav shows Sign in/Account. Admin login at `/admin-login` now uses Firebase.
- Verified end-to-end against PRODUCTION shared Firebase+Atlas: test_reports/iteration_16.json — 9/9 backend + all UI flows PASS (resolve, token gate, admin list, register idempotency, hard-delete + 00001 protection). Throwaway test users cleaned up (DB back to 1 user = admin).
- ⏳ Firebase authorized domains already include leadnation.app/Vercel; add any NEW website domain in Firebase Console → Auth → Settings → Authorized domains.

## Deferred (next phases, per user's production-readiness spec)
- Compile Data → premium 19-section Trade Intelligence Report; PDF download + Print (client-side) + Lead Capture gate.
- My Reports history + shareable public/private links (uses the now-live accounts).
- Legal pages (Privacy/Terms/Cookie/Disclaimer/Refund); Analytics activation (env scaffolding present: GA4/GTM/Clarity/Meta).
- Brain rich feedback → Admin "Knowledge Gaps"; Knowledge-quality indicators (engines used, live vs estimated).
- Security review, SEO/perf/a11y reports, Integration Matrix, Go-Live checklist.


## Implemented (2026-06-29) — Brain goes GLOBAL + Compile Data + Phase C
- [x] **BUG FIX — Brain global & non-repetitive**: rewrote `brain/providers.py` SYSTEM prompt (global, answer-the-specific-question, ground numbers in live engines, use own expertise for any country's compliance, never default to India). Made `trade_news/market_intelligence/logistics/policy/tariff` engines global & dynamic (removed hardcoded India boilerplate like "$450B exports", "Mundra"). Tightened `router.py` engine selection (cap 5, dropped legacy `tariff`/`network`/`marketplace` from auto-select) and added global country detection (scans `duty_engine.COUNTRIES`). Verified: 3 distinct queries → 3 distinct, country-specific, non-India answers.
- [x] **Compile Data master tab** (`compile_engine.py`, `/api/compile/report`): one-click brief for product + export country + import country + currency → aggregates trade stats, duty & benefits, tariff comparison across 6 markets, live FX, sample landed-cost, freight, + a Brain-written **Executive Brief** (LLM). New default tab `CompileDataTool` on `/customs-compliance` with `MarkdownLite` renderer.
- [x] **Phase C — CBIC notified customs FX**: `/api/customs/cbic-fx` returns India CBIC notified import/export rates + notifiedDate. (Data layer live; calculator-UI wiring is a small follow-up.)
- Verified: test_reports/iteration_15.json — 11/11 backend + all UI flows PASS.


## Implemented (2026-06-29) — Phase B: Duty & Benefits engine (real, weekly-refreshed)
- [x] New backend `duty_engine.py`: unified **global import tariffs** (World Bank WITS / UNCTAD TRAINS, reporter=destination × partner=origin × HS6), **India duty breakdown** (BCD from WITS + IGST slab + 10% SWS), and **DGFT RoDTEP** export benefit (chapter-level, Mongo `rodtep_rates`). Endpoints: `/api/duty/countries`, `/duty/meta`, `/duty/lookup?hs=&origin=&destination=`, POST `/duty/refresh` (admin-gated).
- [x] Origin↔destination country filter (56 major countries). Real verified data: USA→India coffee 100% MFN; USA→Germany cars 10%; India→Germany coffee RoDTEP 1.4%.
- [x] **Weekly APScheduler** (7-day) auto-refresh clears tariff cache + restamps `duty_meta.lastRefresh`; "updated on" shown to users; manual **"Refresh data now"** button in Admin Control Center.
- [x] Brain engine `duty_benefits` wired (keywords duty/tariff/rodtep + country pairs) — Brain answers duty questions with real numbers.
- [x] Frontend: new **"Duty & Benefits"** tab on `/customs-compliance` (DutyBenefitsTool) + admin "Trade & Duty Data" refresh card.
- Verified: test_reports/iteration_14.json — 9/9 backend + all UI + admin refresh + Brain PASS.


## Implemented (2026-06-29) — Phase A: Live Global Trade Intelligence
- [x] New backend engine `trade_intel.py`: REAL global trade stats by HS code. Two sources, freshest wins: **OEC World API** (free, no key, always on) + **UN Comtrade** (activates when `COMTRADE_API_KEY` env set). Endpoints: `/api/trade-intel/status`, `/hs-search?q=`, `/stats?hs=`. HS6 directory (5606 codes) built from OEC and cached in Mongo `trade_hs_map`. Results cached in `trade_cache` (14-day TTL ≈ bi-weekly).
- [x] Returns: total world trade value, top importing & exporting countries (value + share), multi-year trend, source + year + freshness. GLOBAL (not India-only).
- [x] Brain engine `trade_statistics` wired into `brain/engines.py` + `router.py` selection (keywords + HS code presence). Brain answers trade-stat questions with real numbers.
- [x] Frontend: new **"Trade Statistics"** tab on `/customs-compliance` (TradeStatsTool) — product/HS search w/ autocomplete, world value, importer/exporter bars, trend chart, Ask-the-Brain CTA. Customs hero/SEO updated to global framing.
- Verified: test_reports/iteration_13.json — 8/8 backend + all UI flows PASS (live OEC data).
- ⏳ Pending: user to add UN Comtrade API key (`COMTRADE_API_KEY` in backend/.env) for fresher data.


## Implemented (2026-06-28) — Unified Admin Control Center + Trade Terms
**Admin auth unified under JWT** (ID `00001` / pwd `Shiv@12345`)
- [x] AdminLogin now uses ID + password → POST `/api/auth/admin/login`, JWT stored as `ln_admin_jwt`, sent as `Authorization: Bearer`. Legacy `X-Admin-Token` still accepted server-side; CSV export accepts JWT in `?token=`.
- [x] Unified `/admin-cms` dashboard: Dashboard, Content, Leads, Service Requests, Events, **Control Center**, Brain.
- [x] **Control Center** (new tab): live accent colour (CSS var `--ln-secondary`), maintenance mode + message, feature toggles (tools/services/brain/customs/intelligence/expo/academy/blog/trade_news), service-rate overrides, change-password. Saves via PUT `/api/admin/settings`.
- [x] **Live propagation**: `SettingsContext` fetches `/api/settings`; Nav hides toggled-off features; Layout renders maintenance screen for public site (admin stays accessible).
- [x] **Brain widget**: typing "I am admin" redirects to `/admin-login`.
- [x] **Customs Trade Terms** tab on `/customs-compliance`: Incoterms 2020, Payment Terms, Cargo Insurance, Key Trade Terms (from `/api/customs/trade-terms`).
- Verified end-to-end (test_reports/iteration_12.json — all 7 items PASS, site restored clean).


## Implemented (2026-06)
**Batch — Product Info Engine + cleanup + search fix** (Jun 2026)
- [x] **#1 Product Info Engine** (`/product-info`) rebuilt: free-text filters (Import/Export · Product · Origin · Destination · HSN optional), NO dropdowns, fully Brain-powered — works for ANY product worldwide (verified: saffron→USA, lithium battery→Germany). Clean markdown rendering (headings/bullets), sources + related + CTAs.
- [x] **#5** Home hero search fixed — was always navigating to /product-info; now routes the typed query to `/brain?q=` (Brain auto-answers). Different queries → different answers.
- [x] **#2** Removed Suppliers + Directory (fake data) — nav/footer links gone; `/suppliers` + `/directory` redirect to home.
- [x] **#3** Removed Network + Marketplace from nav/footer; pages now show an "in the app" note (`AppFeatureNote`) with download CTAs.
- [x] **#6** Home "Business Services" highlight section (Explore Services + IEC/GST/RCMC/Company tiles).
- [x] Nav "Platform" menu removed; Intelligence moved into Explore. Brain page + widget markdown rendering upgraded.
- Verified: testing_agent iteration_11 — 100% (6/6 areas), zero issues.
- DEFERRED to next batch: #4 (Incoterms/Insurance/Payment/CIF/FOB in Customs) and #7 (admin login 00001/Shiv@12345 via "I am admin" in Brain + Admin Control Center). Auth playbook (JWT) already obtained.


- [x] **Global back button** — top-left on every page except Home and Admin (`BackButton.jsx` in Layout; navigate(-1) with home fallback).
- [x] **Rebuilt `/customs-compliance`** as a product-based India hub with 8 tools (all buttons functional, loop closed):
  - **Compliance Report** — filters: product / direction (Export·Import) / country / HSN(optional) → `POST /api/customs/profile`: BCD+IGST+SWS, FTA detection, documents (product-specific), CHA clearance steps, government benefits, official ICEGATE/DGFT/Indian-Trade-Portal deep links + "Ask the Brain".
  - **Currency Exchange** — `GET /api/customs/fx` GENUINELY LIVE via open.er-api.com (no key, 1h cache).
  - **CBM Calculator**, **CHA Charges Estimator**, **Landed/Selling Price Calculator**, **Freight Routes**, **Government Benefits Finder**, **CHA Directory** (WhatsApp connect).
- [x] **Real-Time Trade Data Engine** (`customs.py`): live FX + curated India ruleset + Brain; **paid-API adapter** (`TradeDataProvider`, env `TRADE_DATA_PROVIDER`/`TRADE_DATA_API_KEY`) ready to flip on Seair/Export Genius/Volza with zero code change (Option C).
- Note: DGFT/ICEGATE have NO free public API and scraping isn't allowed — duty data is curated+Brain, clearly labelled "indicative" with official deep-links; upgradeable via the adapter.
- Verified: testing_agent iteration_10 — 100% (14/14 backend + all 8 tabs + back button), zero issues.


- Root cause: several cards looked clickable (cursor/arrow/play affordances) but had no destination. Core flows (nav, forms, detail pages, search, Brain) were actually working.
- Built automated full-site interaction audit via testing_agent (clicks every button/link/form, reports dead elements) — iterations 8 (audit) + 9 (verify).
- [x] **Academy**: new `/academy/:slug` lesson page (backend `GET /api/academy/{slug}` with generated curriculum + related courses); course cards now link; per-lesson "Ask the Brain to teach this" + "Learn with the Brain" → `/brain?q=` auto-ask.
- [x] **Trade News**: new `/trade-news/:id` detail page; featured + cards now link; "Ask the Brain about this story" + "More headlines".
- [x] **Marketplace**: listings → WhatsApp enquiry links; reels → `#download` with "Watch in app" badge.
- [x] **Suppliers**: per-card "Connect with supplier" WhatsApp action. **Network**: per-member "Connect" → /contact.
- [x] **Brain page** reads `?q=` and auto-submits.
- Verified: testing_agent iteration_9 — 100%, zero dead elements remaining, zero console/network errors, no regressions.


- [x] **Global Brain Widget** on every page (desktop floating bottom-right above WhatsApp; mobile FAB). Hidden on /admin and /brain. Mounted in Layout.
- [x] **Context-aware**: widget detects current route → page_context {type, slug}; backend `_resolve_page_entity` injects the country/product/HSN/service entity so short questions ("What documents are required?") work in-context.
- [x] **Page-specific suggested prompts** per page type (country/product/hsn/service/corridor/industry/marketplace/academy/default).
- [x] **Recommendation engine**: `recommendations` (related products/countries/HSN/services/blogs/academy/corridors/industries from KB) on every answer.
- [x] **Smart lead-gen CTAs**: `ctas` (Create Account, Download App, Book Consultation, Apply IEC, Contact) surfaced naturally by detected intent — no pop-ups.
- [x] **Personalization by role** (exporter/importer/cha/buyer/supplier) from user_context → boosts relevant engines.
- [x] **Multilingual-ready** (`language` param → en/hi/ar/fr/es prompt instruction) + **voice-ready** architecture (no STT implemented). Cache key includes page+lang+role.
- [x] Same Brain APIs reused by web/app/portals. Tested: testing_agent iteration_7 — 100% backend + frontend, zero issues.


- [x] **Live AI ON** via Emergent Universal LLM key. Default model `gpt-5.4-mini` (cheapest reliable). Env-configurable: `BRAIN_AI_PROVIDER` (openai/anthropic/gemini/local), `BRAIN_AI_MODEL`, `BRAIN_AI_ENABLED`. Zero app-code change to switch providers.
- [x] **RAG**: every answer retrieves Knowledge Base + engine context BEFORE generation; LLM reasons over LeadNation data only and states when info is insufficient (no fabrication). Source attribution preserved (enginesUsed + sources).
- [x] **Cost controls (CTO)**: 24h response caching (`brain_cache`) → repeat questions cost $0; deterministic engine-composition fallback if LLM fails/zero-budget → never breaks. Retry-once on transient errors.
- [x] **Brain Universal Search** replaces global search: KB → DB(CMS) → Engines/Network(suppliers,buyers,tools) → External APIs(off) → Web(off); relevance-ranked; new types: supplier, buyer, faq, learning, compliance, scheme. Frontend `/search` now calls `/api/brain/search`.
- [x] **Memory**: conversation_memory + user_context (preferred country/products/industries, role, recent searches, saved items) injected into RAG context.
- [x] **Monitoring**: `brain_usage` logs tokens + estimated cost + cached flag per call. Rate limiting (20 req/60s per session). Logging + retry.
- [x] **Admin `/admin/brain` expanded**: AI Health (live status, cache hit rate, degraded calls), Cost Monitoring (total + by model), Token Usage, Engine Health, KB stats (79 entries incl FAQs), Most Asked / Trending, Top + Most-Viewed Countries/Products, Most Used Services, Failed Queries, Knowledge Gaps, Reseed.
- [x] **Tested**: testing_agent iteration_6 — 100% (62/62 backend + all frontend), zero issues.
- Approx cost @ gpt-5.4-mini ≈ $0.0004–0.0005 per uncached query (caching drives effective cost far lower).


- [x] **Backend refactor**: monolithic `server.py` (1.7k lines) split into thin entrypoint + domain modules — `core.py`, `reference.py`, `engines.py`, `search.py`, `leads.py`, `trade_tools.py`, `ai.py`, `content.py`, `services.py`, `admin.py`, `analytics.py`. ZERO regressions (38/38 backend tests pass).
- [x] **`brain/` package** — the central reusable intelligence layer (shared by website, app, future portals):
  - `knowledge.py` — `knowledge_base` collection as Single Source of Truth (SSOT); auto-seeds ~61 entries from countries/products/HSN/corridors/industries/services/blog/academy + curated compliance & schemes. `kb_search` / `kb_get` / `kb_stats`.
  - `engines.py` — 12 engines: country_context, trade_news, market_intelligence, learning, compliance, tariff, logistics, policy, product_intelligence, business_services, marketplace, network.
  - `router.py` — `orchestrate()`: intent detection + entity extraction (country/product/HSN/service) + engine selection + multi-engine composition. Logs `brain_queries` + `brain_usage` for analytics.
  - `providers.py` — configurable AI provider (env `BRAIN_AI_PROVIDER`, default `mock`; supports openai/anthropic/gemini/local). Live calls DEFERRED — deterministic engine composition for now.
  - `memory.py` — `conversation_memory`, `user_context`, `saved_preferences` (preferred country/products/industries, role, recent searches, saved items).
  - `search_layer.py` — Universal Search with 5-tier priority (KB → DB → Engines → External APIs [disabled] → Public Web [disabled, no scraping]).
  - `context.py` — retrieval/context builder seam for future live AI.
- [x] **Brain API**: `/api/brain/ask`, `/search`, `/engines`, `/status`, `/context/{uid}`, `/conversation/{sid}`, `/save`, `/knowledge`.
- [x] **Admin Brain API**: `/api/admin/brain/overview` (engine health, KB status, AI usage, most-asked, top countries/products/HSN/services, trending, failed queries, knowledge gaps), `/knowledge`, `/knowledge/reseed`.
- [x] **Frontend**: flagship `/brain` page (multi-engine unified answers, engine pills, source cards, session memory, suggested prompts); `/ai-assistant` → redirects to `/brain`; nav "AI Copilot" → "LeadNation Brain"; admin `/admin/brain` dashboard + Brain tab in CMS.
- [x] **Tested**: testing_agent iteration_5 — 100% backend + frontend, zero issues.

## Implemented (2026-01)
**Phase 1 — Core portal**
- [x] Cinematic dark UI, Manrope + IBM Plex font pairing, custom logo, gradient text.
- [x] Animated 3D globe with country outlines + 10 trade-route arcs + 12 hub points.
- [x] Home: hero, search w/ live autocomplete, suggestion chips, stats, marquee, feature bento (6), India features (6 dynamic), Apple-style image storytelling, download CTA.
- [x] Customs & Compliance: country selector, Import/Export toggle, duty/documents/incoterms/tip — auto-refresh on change.
- [x] Trade News: hero featured article + masonry-style grid of 5 more.
- [x] Expo: category filter chips, 8 expo cards w/ image, date, city, attendees.
- [x] Product Info: 4-select form, auto-initial result, market size/buyers/suppliers/certs/incoterms/insights.
- [x] Contact: lead form (persists to Mongo), contact rows, embedded OSM map at Ahilyanagar coords, Instagram link.
- [x] Floating WhatsApp button on every page.
- [x] Production-ready App Store / Play Store CTA badges (Coming Soon).
- [x] Footer with all contact + nav + download badges.
- [x] data-testid attributes throughout for QA.

**Phase 2 — SEO Growth Engine** (Jan 2026)
- [x] **Customs Duty Calculator** `/tools/duty-calculator` — country, category, value, currency → duty, VAT, handling, landed cost. FTA detection per corridor.
- [x] **Country Profile Pages** `/countries/{slug}` for India, UAE, USA, Australia, Armenia + index at `/countries`. Each has overview, imports, exports, opportunities, customs, compliance, news, events, marketplaces. Built to scale to 250+ countries.
- [x] **Learning Academy** `/academy` — Beginner / Intermediate / Advanced. 9 premium course cards with topics on import/export process, documentation, customs clearance, FTA arbitrage, supply chain finance, global compliance.
- [x] **Trade Intelligence Hub** `/intelligence` — gold, silver, oil (Brent + WTI), copper, natural gas + 8 currency pairs + 6 global market trends.
- [x] **SEO Infrastructure** — sitemap.xml, robots.txt, react-helmet-async dynamic meta (title + description + keywords + canonical), Open Graph + Twitter cards, JSON-LD structured schema (Organization, WebApplication, Country, EducationalOrganization) on each page.
- [x] **Nav Tools dropdown** + Footer expanded with new tool links.

**Phase 3 + 4 — Trade Intelligence Ecosystem** (Jan 2026)
- [x] **Trade Tools Hub** `/tools` + 7 individual tools: HSN Finder, Duty Calculator, Landed Cost Calculator, Export Incentive Finder, Product Research, Buyer Discovery, Export Readiness Score (3-step funnel with lead capture).
- [x] **AI Trade Copilot** `/ai-assistant` — chat UI with suggested prompts; mocked-but-realistic responses with `MOCKED RESPONSE — LIVE AI COMING SOON` badge; suggested-tools links per answer. Ready for GPT integration.
- [x] **Product Trade Profiles** `/products` + `/products/{slug}` — Basmati Rice, Agarbatti, Spices, Textiles, Pharmaceuticals.
- [x] **Trade Corridor Pages** `/corridors` + `/corridors/{slug}` — India-to-UAE/USA/Australia/Armenia.
- [x] **HSN Landing Pages** `/hsn/{code}` — 5 codes with GST, RoDTEP, drawback, benefits, docs, customs notes, related products.
- [x] **Industries** `/industries` + `/industries/{slug}` — 8 sectors.
- [x] **Blog / Knowledge Center** `/blog` + `/blog/{slug}` — 6 long-form posts.
- [x] **Supplier Discovery** `/suppliers`, **Marketplace** `/marketplace`, **Network** `/network`.
- [x] **Mega-Nav** rebuilt: Home · Tools · AI Copilot · Explore▾ · Platform▾ · Learn▾ · Contact.

**Phase 5 — Revenue Engine, Admin CMS & Business Scale** (Jan 2026)
- [x] **Analytics architecture**: env-driven loaders for GA4 / GTM / Microsoft Clarity / Meta Pixel + first-party event tracking via `/api/track` + `trackEvent()` wired into Create-Account, Download-App, WhatsApp, Contact form, Service Request submissions, page views.
- [x] **Admin CMS** `/admin-login` → `/admin-cms` (token-gated, default `leadnation-admin-2026`): Dashboard (8 stat cards), Content (6 collections with create/edit/delete via JSON editor — countries, products, corridors, hsn_codes, industries, blog), Leads tab (search + CSV export at `/api/admin/leads.csv`), Service Requests tab (status dropdown + CA assignment input), Events tab (page views + custom events).
- [x] **MongoDB content migration**: all 6 collections auto-seeded on startup if empty; CMS reads/writes go to MongoDB; no more hardcoded reads for those collections.
- [x] **Business Services** `/services` + `/services/{slug}` — 10 services (RCMC, GST, IEC, Company Registration + 6 consulting: Export, Import, Compliance, Market Entry, Product Sourcing, Buyer Discovery Service). FAQ accordion + lead form → creates `service_request` + `lead` (linked CA workflow: new → assigned → in-progress → completed/cancelled).
- [x] **Directory** `/directory` + `/directory/{kind}` — exporters, importers, suppliers, CHA, export-agents with search + country filter + locked-CTA.
- [x] **Global Search** `/search` — searches products, countries, corridors, industries, blogs, HSN, services, tools with typed result badges.
- [x] **Sitemap.xml** expanded to ~70 URLs (services + directories + everything from Phase 1–4).
- [x] All admin endpoints token-gated via `X-Admin-Token` header (query token for CSV downloads only).
- [x] **Testing**: 29/30 backend pytest pass · all frontend flows verified · 2 bugs caught and fixed (Home Globe regression + global-search type singularisation).

## Backlog / Next
- **P0** Connect real engines (customs, trade news, expo, product info, search) once API docs are shared by user.
- **P0** Replace coming-soon URLs with live App Store + Play Store URLs.
- **P0** Add real logo + brand assets when ready.
- **P1** Add Hindi + regional language toggle (string already mentioned in India features).
- **P1** Add Trade Intelligence Engine + Learning Academy Engine endpoints.
- **P1** Add video hero (port cranes / trade montage) instead of static images for moving-pictures section.
- **P1** Email/transactional integration (SendGrid/Resend) so leads also email the team.
- **P1** Sitemap / SEO meta tags / OG images (critical for organic-traffic goal).
- **P2** Pydantic model for `product-info` request; tighten CORS.
- **P2** Cap `/search` empty-q response.
- **P2** Replace OpenStreetMap iframe with Mapbox / Google Maps when API key provided.
- **P2** PWA / install banner on web.

## Deployment Notes
- Build with `yarn build` (CRA) and host static `build/` on DigitalOcean App Platform / nginx.
- Backend runs as ASGI (uvicorn server:app) — Docker-friendly. MongoDB via `MONGO_URL`.
- Update `REACT_APP_BACKEND_URL` to production domain when deploying.
