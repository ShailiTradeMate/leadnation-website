# LeadNation — Global Trade Intelligence Portal

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
