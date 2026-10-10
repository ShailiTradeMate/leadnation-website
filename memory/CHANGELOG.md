# LeadNation — Changelog

## 2026-09-30 — Mobile dropdown repair + complete location reference
- Shared touch/search/keyboard picker replaced 58 native selects across 22 pages; added country selectors to remaining country text fields. Responsive signup/header fixes, mobile Explore/Learn groups, pointer-aware navigation, no mobile floating-button obstruction, bounded decoration.
- 250 countries/territories, 4,963 subdivisions, 148,038 city records; on-demand per-country loading, dependent resets, missing-locality custom entry. Offline ODbL dataset, no new external API keys. Country APIs aligned to 250 and Expo ISO/full-name/legacy aliases match.
- Agent iteration67 followed by 15/15 API retest, real onboarding country/state/city/role checks (no mutation), mobile touch and desktop keyboard/focus checks, admin-modal layering, zero overflow in final mobile/desktop checks. Safari binary unavailable: physical-device acceptance still required.
- Full current details: `PRD.md`; previous 721-line PRD retained in `PRD_HISTORY_PRE_MOBILE_2026-09-30.md` to preserve historical evidence without continuing to grow the requirements file.
- No auth credentials, prices, user profiles, or verification statuses changed. Latest Business Services pricing and Academy/Brain/marketing backlog remain unchanged.


## 2026-08-07 (later) — Payment emails (user + admin) + Admin CMS Payments table
Reported: user paid ₹499 (India Razorpay) but received no email. Root cause: checkout never passed the buyer email → email send was skipped. Verified iteration_42 (8/8 backend PASS + CMS renders); emails confirmed dispatching via Resend (sent:True).
- Unified `_finalize_paid()` in monetize.py for BOTH gateways (Razorpay IN + Stripe INTL): atomic-idempotent, activates subscription, enriches the TX, and sends TWO emails.
- Order creation now resolves the user's profile server-side (email, name, mobile, country, uid, customerId) and stores on the TX — so receipts always have the buyer's details even if the client didn't pass them. Razorpay payment.fetch also supplies method (UPI/card/netbanking), email, contact.
- emailer.py: rich `subscription_success` (user) email — detail table (plan, amount, period, active-until, payment mode, transaction id, invoice, user id, customer id, email), benefits list, LeadNation logo + app name + parent company 'Vametra AI Technologies Pvt. Ltd.'. New `admin_payment_alert` email to ADMIN_EMAIL with full user + payment details + transaction id.
- Admin CMS: new **Payments** tab (`PaymentsManager.jsx`) — summary cards (paid count, revenue INR, revenue USD), search, status filters, and a table of every transaction with transaction id, customer, user/customer id, mobile, country, gateway·mode, plan, amount, status, invoice. Endpoint `GET /api/payments/admin/transactions`.
- REDEPLOY required to activate on production. NOTE: the ₹499 payment already made on production was finalized by the OLD code (no email); only payments AFTER redeploy will send emails + log to the new CMS table.


## 2026-08-07 — FIX: India checkout routed to Stripe instead of Razorpay (production)
Reported: on leadnation.app, India Pricing (₹499) opened a Stripe cs_test checkout instead of Razorpay.
- Diagnosis (via live prod curl): production HAD the Razorpay keys (razorpayEnabled=true, /payments/razorpay/order → 200) but the stored pricing_config gateways.razorpay.enabled was stale/false in the production Mongo, so gateway_for() fell back to Stripe.
- Fix (`pricing.py gateway_for`): key-presence is now the source of truth — IN region returns 'razorpay' whenever RAZORPAY_KEY_ID is set (unless admin force_disabled), INTL → stripe. Removes dependency on the stale DB flag.
- Verified iteration_41: preview IN→razorpay (₹499 Razorpay modal), INTL→stripe ($9). No live payment made.
- ACTION: production must REDEPLOY to pick up this routing fix (keys already present on prod, no re-add needed).
- Note: production STRIPE_API_KEY is a TEST/sandbox key (cs_test) — INTL live payments won't capture until swapped to a live Stripe key. India/Razorpay unaffected.


## 2026-08-06 (later) — Razorpay LIVE keys activated + verified
- Added LIVE `RAZORPAY_KEY_ID`/`RAZORPAY_KEY_SECRET`/`RAZORPAY_WEBHOOK_SECRET` to backend/.env (env-only, never logged). Restarted. gateway_for(IN) now returns 'razorpay', razorpayEnabled=true.
- Verified (iteration_40, 13/13 backend PASS, no real payment made): live order creation with correct paise (download 2500 / monthly 49900 / annual 399900 INR), TX persisted, /verify rejects bad signature (400), /webhook rejects bad signature (400), Stripe INTL regression OK, professional services (GST/IEC) confirmed enquiry-only (excluded from Razorpay).
- Bug fixed (found by testing agent): Pricing.jsx local handler was named `startCheckout`, shadowing the imported helper → recursion; renamed local to `handleCheckout`. Razorpay modal now opens with live checkout (₹499, UPI/Cards/Netbanking). CommandCenter/AccountPage unaffected.
- Webhook URL registered in dashboard = https://leadnation.app/api/webhook/razorpay (production). NOTE: keys/code are in PREVIEW; production (leadnation.app) gets them only after REDEPLOY. Handler-path verification works on preview immediately; webhook backup only reaches production post-redeploy.


## 2026-08-06 — Razorpay Standard Checkout (build-ready, dormant pending keys)
Verified via curl: gateway resolves to Stripe while no key (razorpayEnabled=false); /payments/razorpay/order & /verify return 503 until configured; Stripe checkout regression OK ($9 monthly returns url). Happy-path NOT yet tested (awaiting Razorpay TEST keys).
- Used integration_expert verified playbook. Backend (`monetize.py`): `POST /payments/razorpay/order` (server-side price from pricing engine, amount in paise, creates Razorpay Order + TX row _id=order_id, gateway="razorpay"), `POST /payments/razorpay/verify` (server-side `verify_payment_signature` using DB order_id + `payment.fetch` captured check → idempotent entitlement), `POST /webhook/razorpay` (`verify_webhook_signature`, order.paid/payment.captured, idempotent). `_apply_paid_razorpay()` mirrors Stripe paid branch (activate 30/365-day sub + receipt email). `_sync_status` short-circuits for gateway=="razorpay" so downloads reuse existing flow.
- Frontend: new `lib/checkout.js` `startCheckout()` auto-routes IN→Razorpay (when keys present) else Stripe; Razorpay success funnels back to the SAME `/account?session_id=<order_id>` URL so all post-payment logic (sub activation, PDF download record) stays unified. Wired into Pricing.jsx, CommandCenter.jsx, AccountPage.jsx.
- Scope guard: Razorpay used ONLY for subscription/report/download/event checkout. **Professional services (GST/IEC registration in services.py) are enquiry/lead-based with NO online checkout — they will NOT use these keys** (separate keys later, per user).
- Pricing config `gateways.razorpay.enabled=true` (default + live doc) — still gated by env `RAZORPAY_KEY_ID` so live users stay on Stripe until keys added.
- Env vars needed: `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET`. Razorpay SDK added to requirements.txt.
- Deploy note: built in PREVIEW; needs redeploy to reach production (leadnation.app).



## 2026-08-04 — VBIE Production Recurring Intelligence Service + new GREEN sources + phased CH bulk + auto-filters
Verified: test_reports/iteration_39.json (11/11 backend PASS + full frontend PASS) + manual curl hardening (422/400/409).
- **Root cause found & reported**: 0 new buyers added because (a) only the WEEKLY cycle fetched new buyers — the daily job just re-scored; and (b) APScheduler used an in-memory jobstore that reset on every backend restart, so the weekly job never actually fired (`vbie_cycles` had only manual runs).
- **NEW `vbie_scheduler.py`** — production DB-backed recurring engine (replaces in-memory APScheduler). Persistent job store in Mongo (`vbie_jobs`), survives restarts, automatic catch-up (persisted `next_due_at`), retry queue w/ exp backoff, failure alerts (admin notification + email), health heartbeat (`vbie_engine_health`), per-source incremental checkpoints (`vbie_checkpoints`), source-specific interval schedules, job history (`vbie_job_history`). 30s asyncio tick loop; single-runner locks; reclaims stuck locks on boot. No cycle silently skipped.
- Jobs: weekly_full (Sun 02:00), daily_brain reconcile (05:00: dedupe·LEI·brain·change-detect·alerts·audit·daily digest), monthly_bulk (1st 04:00), + per-source discovery jobs (eu_ted, uk_companies_house, cid_canada, no_brreg, cz_ares). Checkpointed discovery grows the DB daily (CH pages via start_index; Norway/Czech paginate; TED rolling window).
- **New GREEN sources ENABLED**: Norway Brønnøysund Enhetsregisteret (NLOD, no key) + Czechia ARES (MoF open data, no key — walks CZ-NACE 46 wholesale codes ≤1000/query). Scaffolded DORMANT pending keys: France SIRENE, Japan NTA, Australia ABN, Denmark CVR, Singapore ACRA, Finland PRH (added to source registry; run once key+legal approval supplied).
- **Companies House phased bulk** (`run_ch_bulk_phase`, targets 100K→500K→1M→5M) with QA snapshot (counts, dedupe, search latency, audit). Bulk connector now STREAMS to disk (pod-safe, no 500MB in RAM) and FILTERS by importer/wholesaler SIC 46xxx (quality: never labels the whole register as buyers). Endpoint hardened: target required (no default), 409 if a phase is running, detached task.
- **Auto-updating filters** confirmed: `/api/buyers/meta` uses live `db.distinct` → Market/Sectors/Corridors/Trust auto-include new data (Norway + Czechia now appear; corridors 30→31).
- **Admin monitoring dashboard** in BuyersManager.jsx: engine health badge, jobs table (Run now / Pause per job), source checkpoints, job history, CH phased-bulk controls. Endpoints under `/api/buyers/admin/engine/*` + `/bulk/*`.
- Integrity fix: removed 36,485 generic non-SIC-filtered UK records accidentally ingested during QA (mislabeled sector) — restored evidence-first accuracy. Post-fix: 13,368 buyers, audit 0 quarantined.
- Files: vbie_scheduler.py (new), vbie_engine.py (run_reconcile, run_incremental discovery, run_ch_bulk_phase), vbie_connectors.py (connector_norway, connector_ares_cz, DISCOVERY_ADAPTERS, discover_source, streaming SIC-filtered CH bulk), vbie_core.py (sources+approvals), vbie_admin.py (monitoring+bulk endpoints, audit vbie-bulk prefix), server.py (wire scheduler+indexes), BuyersManager.jsx (dashboard).



## 2026-07-14 (later) — Brand logo + Tagline lock + AI Search Optimization (AEO/LLM) — frontend + email
Verified: test_reports/iteration_28.json (all PASS after footer tagline fix).
- **Tagline LOCKED** to "Intelligence Beyond Borders" everywhere: `lib/brand.js`, footer (visible sub-brand line), Organization JSON-LD slogan (dynamic + static index.html), meta description, email header (emailer.py), llms.txt. Removed stray "Without Borders" from brand guidelines. Confirmed 0 occurrences of wrong tagline in DOM.
- **Real LeadNation logo** wired from user assets: generated clean transparent LN mark (`public/brand/ln-mark.png`) used in Nav + Footer (replaced old SVG globe); built favicons (16/32/ico), apple-touch-icon, PWA icons (192/512), `manifest.json`, and a branded 1200×630 `og-default.png` (LN icon + LEAD/NATION wordmark + tagline) via PIL. index.html head now links favicons/apple-touch/manifest. Logo assets built from user's transparent app-icon (correct "Beyond Borders").
- **AEO / Entity SEO**: enriched `organizationSchema` (@id, founder=Vaibhav Deshmane, foundingDate 2025, foundingLocation, knowsAbout[13], areaServed, PostalAddress, logo ImageObject, sameAs) in SEO.jsx + static index.html. Added reusable builders `articleSchema`, `productSchema`, `howToSchema`. Wired NewsArticle (TradeNewsDetail), BlogPosting (Blog), Event (EventDetail). Expanded `llms.txt` with entity summary/founder/mission/citation guidance.
- Deliverables: `AI_SEARCH_AEO_REPORT_2026-07-14.md` (AI Search Readiness, AEO 86/100, LLM 88/100, KG readiness, structured-data report, entity SEO, content strategy §7, audit §8).
- OPEN follow-ups: wire productSchema on /products/:slug + howToSchema on tool pages; owner: Crunchbase/Wikidata/LinkedIn About for KG authority; publish 20 flagship guides.


## 2026-07-14 — Production Polish Sprint (UX · SEO · Performance · Marketing) — frontend-only
No new features; no backend/auth/DB/Firebase changes. Verified: test_reports/iteration_27.json (13/13 PASS).
- **P0 Global scroll fix**: new `components/ScrollToTop.jsx` (useLayoutEffect + `history.scrollRestoration='manual'`) mounted in `App.js` router. Every navigation opens at top (navbar/footer/cards/Back-Forward, desktop+mobile); hash anchors (`/#download`) still scroll to section.
- **Performance**: `App.js` rewritten with `React.lazy` + `<Suspense>` for all ~40 routes (Home eager). Accessible route loader (`role=status` + sr-only).
- **SEO**: `SEO.jsx` rewritten with reusable JSON-LD builders (organization/website/softwareApplication/faq/breadcrumb/event); `schema` prop accepts arrays; added og/twitter image:alt, richer robots. Home now renders `<SEO>` (was imported-but-unused) with FAQ schema; Pricing gets Breadcrumb+FAQ; added SEO to Marketplace/Network. Deduped site-wide schema (kept static in index.html). Added `public/llms.txt` for AI-search discoverability. index.html Organization gets legalName+slogan+LinkedIn sameAs + SoftwareApplication block.
- **Marketing / social**: new `src/lib/brand.js` single-source config (TAGLINE="Intelligence Beyond Borders", SOCIALS[], SAME_AS). Instagram + LinkedIn wired in Footer, Contact, JSON-LD sameAs, OG/Twitter. Adding a future platform = one array entry. `data/contact.js` now sources socials from brand.js.
- **Auth UX** (earlier this session): login shows Google-only guidance on `auth/invalid-credential` (Firebase enumeration protection blocks pre-detection). App-team fix documented in `GOOGLE_ONLY_ACCOUNT_FIX.md`.
- Deliverables: `POLISH_SPRINT_REPORT_2026-07-14.md` (UX/SEO/Perf/Marketing/A11y/CWV/before-after/growth recs).
- Branding: logos/favicon/app-icon UNTOUCHED pending owner's final assets.


## 2026-07-06 — Expo & Events Engine + Real-time Trade News + Uploads/Payments/Email (v1.1)
Feature freeze temporarily lifted for user-requested build. All shared with mobile app (same backend/DB/Firebase).

### Expo & Global Events Engine
- New backend `event_listings.py` (router `/api/events`). Collections: `expo_listings`, `event_submissions`, `event_payments`.
- Admin-curated + user-submitted + admin-approved lifecycle: payment_pending → under_review → published → expired / rejected.
- Public: `/events/list` (filters: category/country/industry/audience/q), `/events/filters` (dropdowns), `/events/{id}`, `/events/mine`, `/events/pricing`.
- Paid listings: India ₹10,000/30d (Razorpay), International $105/30d (Stripe). Pricing in Pricing Engine (`eventPricing`), admin-editable — never hardcoded. Razorpay falls back to Stripe(INR) until keys added.
- Admin: approve/reject(reason)/feature/extend/delete/create + pricing editor. 6 real starter expos seeded.
- Frontend: rewrote `Expo.jsx` (filters + featured), new `EventSubmit.jsx` (form + uploads + Stripe/Razorpay), new `EventDetail.jsx`.

### Trade News Engine (real-time + personalized)
- New backend `news_engine.py` (router `/api/news`). Hybrid: NewsData.io adapter + LeadNation Brain + admin editorial.
- `/news/feed` personalizes by signed-in user's country + role (guests get global); badges live/ai/admin.
- `/news/{id}` returns Brain "what does this mean for my trade?" impact (personalized when authed).
- Admin news CRUD + feature. Frontend `TradeNews.jsx` + `TradeNewsDetail.jsx` rewritten.

### Infrastructure
- New `storage.py` — provider-abstracted object storage (Emergent now; S3/Firebase/Spaces later). `/api/storage/upload` + `/file/{id}`.
- New `emailer.py` — Resend, 8 branded lifecycle templates, non-blocking (no-ops if key unset). `llm_util.py` helper.
- Env added (all optional in preview): NEWSDATA_API_KEY, RESEND_API_KEY, SENDER_EMAIL, PUBLIC_SITE_URL, RAZORPAY_KEY_ID/SECRET/WEBHOOK_SECRET, STORAGE_PROVIDER.

### Removals (UI only; backend kept)
- Home: "Built for India" card removed ("Five engines" heading).
- Customs & Compliance: removed CHA Charges, Price Calculator, CHA Directory tabs.

### Docs
- Updated `TRADE_COMMAND_CENTER_APP_INTEGRATION_GUIDE.md` (ADDENDUM v1.1) + `APP_BUILD_PROMPT.md` with Events/News/Uploads/Payments/Email APIs.

### Testing — iteration_25.json
- Backend 17/17 pytest PASS; Frontend 7/7 public flows PASS. No issues. Admin UI not testable in preview (Firebase CORS) — admin backend endpoints PASS via X-Admin-Token.

## 2026-07-06 (later) — Resend email LIVE + deployment prep
- Reworked `emailer.py`: general service, all templates (user/events/reports/payments/admin), branded
  "LeadNation by Vametra AI Technologies Pvt Ltd" (serif wordmark, NO logo), Privacy/Terms/Contact footer,
  non-blocking + auto-retry on Resend 2/sec limit. Added `notify_admin` + `/events/admin/email-test`.
- Wired triggers: event admin-submission alert, 12h expiry sweep (expiring/expired), leads + service-request
  admin alerts, subscription_success/payment_failed + report_generated in monetize (best-effort via optional email).
- ENV live: RESEND_API_KEY (leadnation.app domain verified), SENDER_EMAIL, ADMIN_EMAIL=admin@leadnation.app.
  Test-delivered all templates to multiple inboxes — confirmed by user.
- Deployment prep: deployment_agent = PASS. Set prod `CORS_ORIGINS` (explicit domains, no wildcard).
  Task 7 SEO already correct (canonical/robots/sitemap/OG → leadnation.app). Payments stay TEST for launch
  (live Stripe/Razorpay keys post-deploy; code already env-ready, Razorpay auto-activates for IN).
  ADMIN_TOKEN/PASSWORD unchanged per user (rotate before public launch). Created LEADNATION_PRODUCTION_DEPLOYMENT_REPORT.md.
- Docs updated: PRODUCTION_READINESS.md (email LIVE), APP_BUILD_PROMPT.md + INTEGRATION_GUIDE (v1.1 APIs).

### Not yet done (owner action required) — Production deployment Tasks 1–8
- Emergent deploy, GoDaddy DNS for leadnation.app, Firebase authorized domains, prod CORS_ORIGINS, live Stripe/Razorpay/Resend/NewsData keys, SEO canonical/sitemap to leadnation.app, final deployment report.

## 2026-06 — Brand refresh: new Vametra AI logo + Orbitron wordmark
- New circular "VAMETRA AI" logo applied site-wide: /brand/vametra-mark.png (nav + footer LogoMark),
  /brand/vametra-logo.png, app_icon, splash_screen, favicon.ico/16/32, apple-touch-icon,
  icon-192, icon-512, og-default.png (all regenerated from the supplied artwork).
- Brand font: Orbitron added to the Google Fonts import; new `.font-brand`, `.brand-wordmark`,
  `.brand-wordmark-ai` utilities in index.css. Applied to Nav, Footer, Auth shell, BrainWidget,
  DownloadCTA phone mock, TradeIntelReport and CommandCenterReport (PDF header).
- Home hero: big "VAMETRA AI" wordmark + "Intelligence Beyond Borders" rule placed in the blank
  area above the eyebrow (user-highlighted spot); h1 trimmed to lg:text-[56px] for hierarchy.
- Nav de-crowded: brand block gets lg:pr-5 xl:pr-8, links use px-2.5/xl:px-3 + whitespace-nowrap
  so the wordmark no longer touches the Home tab. Verified desktop 1920 and mobile 390.

## 2026-10-01 — LeadNation marketing stack removed (fresh start for vametra.com)
- Cleared `REACT_APP_GA4_ID`, `REACT_APP_GTM_ID`, `REACT_APP_CLARITY_ID` in frontend/.env
  (were leadnation.app properties: G-H5809GHQXW, GTM-5JM23MH4, y2xx93q69j). Meta Pixel already empty.
- Verified after restart: accepting cookies loads NO googletagmanager/clarity/facebook scripts;
  window.gtag/dataLayer/clarity/fbq all absent. Home + Tools pages, nav, consent banner unaffected.
- Deleted legacy LeadNation brand artwork: brand/ln-icon.png, ln-mark.png, logo_mark.png,
  logo_horizontal_dark.png, logo_horizontal_light.png (all unreferenced in src).
- Deleted legacy marketing docs: memory/ANALYTICS.md, AI_SEARCH_AEO_REPORT_2026-07-14.md,
  LEADNATION_BRAND_GUIDELINES.md. MARKETING_SETUP_GUIDE.md section 0 rewritten.
- Outbound scraper UA rebranded: "Vametra-VBIE/1.0 (+https://vametra.com)" (backend/vbie_connectors.py).
- Untouched on purpose (functional, not marketing): consent storage key `ln_cookie_consent`,
  DB_NAME, ADMIN_TOKEN, AUTH_API_BASE / DO identity API, Firebase keys, backend test fixtures.

## 2026-10-02 — Vametra GTM + GA4 wired and verified
- Keys set in frontend/.env: REACT_APP_GTM_ID=GTM-KWNFXB47, REACT_APP_GA4_ID=G-S858BWLS7P.
- GTM container v2 (exported JSON reviewed): 2 tags (Google Tag → Initialization-All Pages;
  GA4 - Vametra Events (gaawe) eventName={{Event}}, measurementIdOverride=G-S858BWLS7P,
  eventSettingsVariable=GA4 Event Settings - Vametra) + 1 regex Custom Event trigger covering all
  13 app events + 8 Data Layer variables (location, plan, tool, country, hs_code, amount, currency, buyers).
- Verified on preview after consent accept: gtm.js?id=GTM-KWNFXB47 and gtag/js?id=G-S858BWLS7P load,
  window.gtag true, and clicking Download App pushed `download_app_click` into dataLayer.
- PENDING: same two env vars must be set in the deployed environment + redeploy; then Clarity,
  GSC + Bing verification tokens, IndexNow key.

## 2026-10-05 — Sitemap consolidation + Clarity live
- REACT_APP_CLARITY_ID=ysliy7aa8k wired and verified (clarity.ms/tag/ysliy7aa8k loads after consent).
- Diffed the two production sitemaps: static had 77 URLs, dynamic /api/sitemap.xml had 67, and they
  disagreed on 42 URLs. Static wrongly listed /directory, /directory/*, /suppliers (all redirect to /)
  and /search; dynamic was missing /services/*, /legal/*, /marketplace, /network.
- backend/seo.py: added /marketplace, /network and the 5 /legal/* pages to _static_routes, and the
  11 SERVICES_DB slugs to _dynamic_routes → /api/sitemap.xml now emits 85 real URLs.
- Regenerated frontend/public/sitemap.xml from that output so both are byte-identical (85 URLs,
  no redirecting or noindex URLs). Needs a redeploy to go live.
- GSC "Couldn't fetch" on https://vametra.com/sitemap.xml investigated: production returns HTTP 200,
  valid XML, correct content-type, for Googlebot UA / empty UA / gzip / HTTP1.1 (edge is Cloudflare).
  Treated as a GSC fetch-lag, not a site defect. /api/sitemap.xml already reads Success.

## 2026-10-06 — IndexNow auto-ping wired (Bing/Yandex) + honest lastmod for Google
- backend/seo.py: notify_content_change() fire-and-forget helper; _ping_and_log() stamps
  db.seo_lastmod and audits to db.seo_pings, then submits to api.indexnow.org; cms_paths()/CMS_URL_MAP
  map CMS collections to public URL prefixes + hub pages.
- Hooks: admin.py CMS create/update/delete (blog, countries, products, corridors, industries,
  hsn_codes); event_listings.py admin create / admin edit / approve (/expo/{id} + /expo);
  news_engine.refresh_news() (/trade-news + /intelligence).
- Sitemap now also lists published expo detail pages (155 URLs total, was 85) and uses the real
  recorded lastmod per URL instead of today-for-everything.
- Weekly sweep Mondays 01:10 UTC + boot warm-up (boot sweep self-skips if swept within 24h, so
  restarts don't spam IndexNow). Admin audit endpoint GET /api/seo/ping-log (403 without token).
- frontend/public/sitemap.xml is now a <sitemapindex> pointing at /api/sitemap.xml, so the root-level
  file can never go stale; robots.txt comments updated.
- Google: no ping exists (sitemap ping deprecated 2023, Indexing API is JobPosting/BroadcastEvent
  only) — handled via accurate per-URL lastmod + GSC instead.
- Testing: iteration_68 — tests/test_iter68_seo_autoping.py, 16/16 passed; live IndexNow responses
  ok (200/202). Re-ran after the boot-sweep throttle fix: 16/16 passed.

## 2026-10-06 — GEO phase 1: llms.txt refresh + AI-referral tracking + keyword strategy
- frontend/public/llms.txt rewritten: added an "Answers to common questions" block (the text AI
  engines quote), priority corridor list, services/academy/buyers/corridors URLs, a Last-updated
  line, citation instructions ("cite the as-of date") and the canonical /api/sitemap.xml.
- frontend/src/lib/analytics.js: AI answer-engine referral detection for 17 hosts (ChatGPT,
  Perplexity, Gemini, Copilot, Claude, Grok, Meta AI, DeepSeek, Mistral, You.com, Phind, Poe, Andi)
  + utm_source fallback. Sticky per session (sessionStorage vm_ai_referral), fires an `ai_referral`
  event once per session and stamps `ai_engine` on EVERY later event and page_view, so AI-sourced
  conversions are segmentable in GA4/GTM/Clarity. Fires only with analytics consent.
- Verified on preview: ?utm_source=chatgpt → stored 'chatgpt', dataLayer rows
  [ai_referral, download_app_click] both carrying ai_engine; detection stays sticky across SPA navs.
- New doc memory/SEO_KEYWORDS.md: 40 target keywords (tiered T1/T2/T3, one page each, with target
  URLs), the top-10 country/corridor priority list backed by FY2025-26 DGCIS trade values, and a
  10-prompt monthly GEO audit list.

## 2026-10-07 — SEO/GEO Part 1: data foundation for product x country pages
- NEW backend/seo_pages.py (router /api/seo): /catalogue (8 products, 56 countries, 5 regions),
  /page-data/{product}/{country} (duty + preferential + RoDTEP + world/country demand + buyers +
  expos + news + sources[] + disclaimer + dataScore + indexable), /matrix (scores every combination,
  24h cache, concurrency 8), POST /refresh-all (admin: WITS + RoDTEP + trade cache + HS directory +
  news + expo engines, per-source report).
- Data sufficiency gate: duty 40 + demand 30 + buyers 15 + expos 8 + news 7; indexable needs >=70
  AND a real tariff record AND real demand. Low-score pages render noindex and are never submitted
  to sitemap/IndexNow; they flip automatically when data lands.
- FIXED: trade_intel returned "No trade data found" for every HS code (stale in-memory HS directory,
  5,606 of 16,818 codes; OEC members endpoint 307s). Now falls back to Mongo, rebuilds, and uses
  follow_redirects.
- NEW trade_intel.importer_table()/importer_detail(): per-country import value, world rank and share
  (222 reporting countries, OEC/BACI 2024), cached 14 days — gives every page unique real data.
- FIXED: /seo/matrix exceeded the 60s gateway limit; now asyncio.gather with semaphore(8) + cache.
  Verified: agarbatti x middle-east = 9 combos in 8.5s, 8 indexable, Bahrain correctly excluded
  (score 37, no tariff record). basmati->germany score 100 (duty 0% WITS 2023, RoDTEP 1.0%,
  $462.7M imports rank 20/222 OEC 2024, 5,280 buyers, 4 expos, 4 news).
- Docs: memory/seo/EXECUTION_PLAN.md (6-part plan + status board + 7-item owner backlog).

## 2026-10-07 — SEO/GEO Part 2: full HS directory + product x country page template
HS CODES EVERYWHERE (owner request)
- trade_intel: hs_search() now queries Mongo (was a stale in-memory map), new GET /hs-directory
  (search by code prefix or description, chapter/section filter, paging) and GET /hs-chapters
  (96 chapters with counts + WCO section names). ensure_hs_directory() runs at startup: creates a
  unique index on hs6, rebuilds if the directory is partial.
- Deduped db.trade_hs_map 16,818 -> 5,606 unique codes = the complete WCO HS-2022 six-digit
  nomenclature. Every HS suggestion field on the site now searches all 5,606 codes.
- NEW components/HsCodePicker.jsx — shared searchable picker (debounced server search, keyboard
  nav, clear, mobile-friendly, data-testids). Wired into /tools/hsn-finder, /tools/duty-calculator
  and the /buyers HS filter. Customs & Compliance + Command Center suggestion inputs inherit the fix.

PART 2 — PRODUCT x COUNTRY TEMPLATE
- NEW pages/ExportProductCountry.jsx at route /export/:product/to/:country. Answer-first opener,
  trade snapshot, duty table with SOURCE/AS-OF line, demand (world + country + rank of 222), document
  checklist, buyer panel, landed-cost explainer, expos, news, 8-question FAQ, and a sticky action rail
  linking Brain / HS finder / duty / landed cost / buyers / Command Center / country / corridor.
- noindex is driven by the API's `indexable` flag; thin pages show an explicit notice.
- Buyer honesty: real counts in Europe; "coverage expanding + notify me" panel elsewhere. No invented counts.
- seo.py _product_country_routes(): only indexable=true rows enter the sitemap and the IndexNow sweep
  (sitemap now 182 URLs incl. 27 /export guides; agarbatti/bahrain correctly excluded).

SEO BUG FIXED SITE-WIDE
- public/index.html carried a static robots meta AND a canonical pointing at the homepage, so EVERY
  route emitted two robots tags and two canonicals (one wrong). Both removed — react-helmet is now
  authoritative. Verified: exactly one robots + one self-referencing canonical per page.

TESTING — iteration_69: backend 20/21 pytest (one transient 502 flake, endpoint verified by sibling
tests), frontend 100%, zero issues raised. tests/test_iter69_seo_hs_export.py.


## 2026-10-08 — Tools rewire (iteration 70)
- `/tools/*` embed real Customs & Compliance Engine components; mock backend removed; HSN Finder on full 5,606-code directory with RoDTEP/IGST/WITS duty; Buyer Discovery on real buyer records; `LaneCountrySelect` fixes wrong (alpha-2) lane codes in Customs Engine + Command Center; `BrainNextSteps` panel + `POST /api/tools/next-steps`; `/customs-compliance?tab=` deep links; export-guide tool rail pre-filled with lane params; `HsCodePicker` mobile overflow fix.
- Tests: `backend/tests/test_iter70_tools_rewire.py` 25/25; frontend flows all green (`test_reports/iteration_70.json`).

- 2026-10-08 (follow-up): HSN Finder made global — Exporting-from + Importing-to selectors; cards = destination MFN duty, preferential rate for the chosen origin, destination VAT/GST; India RoDTEP/GST shown only when origin/destination is India; HS code highlighted large; Brain steps carry `from=` origin. Verified US→Canada laptop (847130, 0% MFN, 5% GST).

## 2026-06 — Brain chat reliability fix
- `/brain?q=...` deep links no longer fire the question twice (React double-effect guard via presetDone ref + inFlight ref instead of loading state).
- Brain requests now use a 180s timeout (was global 30s axios timeout) in Brain page, BrainWidget and Command Center brain panel — this was the cause of "Something went wrong reaching the Brain".
- Errors now distinguish timeout vs 429 vs generic, and show a "Retry this question" button (data-testid brain-retry-N).
- Verified in browser: /brain deep link renders one question and a full sourced answer, no error.
- Open: Brain still defaults an unspecified market to India (tracked under "Global Tool Copy" backlog item).

## 2026-06 — Global tool copy, country benefits map, GEO answer layer
### Global tool copy (origin-aware)
- Duty Calculator, Landed Cost Calculator, Export Incentive Finder, HSN Finder and Tools hub copy rewritten: no India-only wording for non-Indian exporters. Incentive finder no longer fixes origin to India.
- `duty_engine.duty_and_benefits()` now returns `exportSupport` for ANY origin; RoDTEP `exportBenefit` stays India-only.
- `trade_tools.hsn_finder()` returns `exportSupport` + origin-aware `sources` (DGFT only listed when origin=India).
- `tools_brain.deterministic_steps()` origin-aware; `_export_page(hs, dest, origin)` only offers the India-export guides for India origin; added an "Export support in {country}" next step.
- Removed the expired Interest Equalisation scheme from /api/customs/benefits; that card relabelled "Indian Government Schemes (DGFT)".

### Country benefits map (NEW backend/export_incentives.py)
- Curated registry of 52 exporting countries, ~100 schemes: scheme name + administering authority + OFFICIAL url + what it gives + kind (remission/drawback/tax-refund/temporary-import/finance/insurance/grant). Official URLs web-verified Jun 2026.
- CTO decision: directory-level coverage with official links; NO percentage is ever shown unless the government publishes an official rate schedule (today only India RoDTEP, flagged `hasRateSchedule`). Uncovered countries return an honest "not yet verified" note instead of invented schemes.
- Routes: GET /api/incentives/countries, GET /api/incentives/{code}. UI: `frontend/src/components/CountryIncentiveMap.jsx` on the Export Incentive Finder.

### SEO/GEO answer layer (NEW backend/seo_answers.py)
- Platform constraint: Emergent CRA deploys serve the frontend from Cloudflare with SPA routing, so pre-rendered nested HTML files are NOT served. True prerender needs the platform "Enable Search Engine Crawling and Optimisation" toggle (user to switch on) or a Next.js/external deploy.
- Built instead: crawlable answer documents with the full page text — GET /api/answers/index, /api/answers/md/{path}, /api/answers/html/{path}, /api/answers/json/{path}. 8 tool/Brain pages + every indexable export guide (106 docs today).
- Each HTML doc carries exactly one canonical back to the human page, keeps source + as-of year on every figure, and is listed in /api/sitemap.xml and public/llms.txt.

### Verification
- Testing agent iteration 71: backend 19/19 pytest (`backend/tests/test_iter71_origin_geo.py`), frontend 100%, no mobile overflow. `schemes` count field renamed to `schemeCount` after review; re-verified in browser.

## 2026-06 — SEO/GEO Part 4: region hubs
- NEW `/regions` index + `/regions/europe`, `/regions/middle-east`, `/regions/asia-pacific` hubs (`frontend/src/pages/RegionsIndex.jsx`, `RegionHub.jsx`, routes in App.js).
- Backend `seo_pages.py`: REGION_HUBS (intro + 4 verified facts each), `_region_rows()` reading the 24h matrix cache, GET /api/seo/regions and GET /api/seo/region/{slug}. Per country: indexable guides, top import demand, applied duty range, buyer count or honest "coverage expanding", plus prefilled duty/landed-cost/buyers links and country-profile/corridor links only where those pages exist.
- Same indexability gate: a hub is only submitted for indexing with >=3 real-data guides and real demand (`indexNote` explains when not).
- GEO answer docs for hubs: /api/answers/md|html/regions/{slug}; added to /api/sitemap.xml (+ /regions static route) and public/llms.txt.
- Internal links (no orphans): Explore nav + footer -> /regions; export guide breadcrumb -> its region hub (epc-region-link).
- Added a daily 02:30 UTC + boot+5min matrix cache warm job (`seo._warm_matrix_cache`) so hubs never build on a user request (fixes the cold 502 the tester saw).
- Live data: Europe 20 markets / 38 guides / US$2.97B demand / 23,702 buyer records; Middle East 9 markets / 16 guides / US$4.03B demand / 0 buyers (coverage expanding); Asia Pacific 14 markets / 26 guides.
- Verified: testing agent iteration 72 — 14/14 new backend tests + 19/19 iter71 regression, frontend 100%, no mobile overflow. Local re-run after the warm-job fix: 33 passed.

## 2026-06 — SEO/GEO Part 5: publish batch 1 + internal link graph
### Published set
- 392 gate-approved guides live (8 product families x 49 markets avg) across 5 regions: Europe 152, Asia Pacific 104, Middle East 64, Americas 40, Africa 32.
- Added `americas` and `africa` REGION_HUBS (4 verified facts each) so every guide has a region parent — no region-orphan guides.
- Sitemap now ~975 URLs: /export, 8 product hubs, 392 guides, /regions + 5 hubs, 413 GEO answer docs.
- `POST /api/seo/publish-batch` (admin) submitted 562 URLs to IndexNow in 2 chunks, both HTTP 200.

### New pages
- `/export` — ExportGuidesIndex.jsx: all guides grouped by product, market search, region chips.
- `/export/:product` — ExportProductHub.jsx: per-product hub with stats (markets, demand, duty range, zero-duty markets, buyer records), all markets with duty/demand/rank, tool deep links, region + related-product links.

### Link graph (zero orphans)
- `backend/seo_pages.py`: MARKETING_PRODUCT_SLUG, `_approved_rows()`, `_related_links()`, GET /api/seo/guides, /api/seo/product-hub/{product}, /api/seo/guides-by-country/{country}; `page-data` now returns `related`.
- `frontend/src/components/LinkGraph.jsx`: RelatedGuides (same product other markets, same market other products, region hub, corridor, country profile, product overview) + CountryGuides.
- Guides: breadcrumb now points to /export/{product} (previously linked a NON-EXISTENT /products/{seo-slug} for 5 of 8 products — real broken-link bug, fixed).
- Country profiles, corridor pages and marketing product pages now list their published guides; nav + footer carry "Export Guides".
- GEO answer docs added for the 8 product hubs (413 docs total); llms.txt documents /export, product hubs and all 5 region hubs.

### Verification
- Testing agent iteration 73: 16/16 new backend tests, frontend 100%, zero-orphan reachability confirmed, no mobile overflow. Low-priority testids added afterwards (hub-duty/hub-landed/hub-buyers/hub-market-region/hub-market-corridor) and the stale iter72 3-region assertion updated. Local re-run: 49 passed.

## 2026-06 — Live HTTP audit of all 975 sitemap URLs + two SEO fixes
### Audit (prod, Googlebot UA, redirects not followed, 2026-10-09 22:27 UTC)
- 975/975 = HTTP 200. Zero 3xx, zero 404, zero 5xx, zero timeouts.
- 562 landing pages / 413 machine-readable answer docs.
- Answer docs: 413/413 exactly one canonical, zero canonical mismatches, h1 on all, median 280 words, min 127 — no thin docs. Median 430ms.
- Landing pages: every page type rendered for Googlebot EXCEPT export guides — only 67/392 rendered; 325 returned the ~202-word SPA shell (no h1, no canonical). Rendered pages avg 1.6s vs 11s for the shell ones = edge pre-render worker render timeout. API itself was fast (page-data 0.35-0.93s), so the cause was third-party analytics keeping the page off network-idle.
- Also found: /marketplace and /network emitted TWO canonical + TWO robots tags (page <SEO> plus AppFeatureNote <SEO>).

### Fixes applied
- NEW `frontend/src/lib/crawler.js`: `isSearchBot()` (strict bot/AI-crawler UA list) and `isCrawler()` (bots + headless renderers).
- `analytics.js applyConsent()` short-circuits for crawlers → GTM, GA4, Clarity, Meta Pixel are never injected into a crawler/pre-render render.
- `Layout.jsx` hides the floating Brain + WhatsApp widgets only for strict search bots (headless browsers keep the full UI so UI automation still works).
- `AppFeatureNote.jsx`: removed its `<SEO>`; the page-level SEO is authoritative.
- Verified by testing agent iteration 74 (frontend 100%): single canonical/robots on both pages with the correct page titles, analytics globals undefined under headless, widgets still render, cookie banner + content pages unaffected, no mobile overflow.
- PENDING: re-run the 392-guide audit after the next production deploy to confirm the rendered count rises from 67.

## 2026-10-10 — Export-guide pre-render root cause FOUND AND FIXED (page-data cache)
### Post-deploy re-audit (prod, Googlebot UA, 30-URL random sample)
- 26/30 guides rendered (87%) vs 21% (69/335) before the crawler-lean deploy — the crawler fix worked.
- Per-product probe exposed the remaining failures as product-specific, not random:
  basmati-rice 6/6, fresh-fruits 5/6, engineering-machinery 3/6, **pharmaceuticals 0/6**.

### Real root cause (ours, not the platform)
- `GET /api/seo/page-data/{product}/{country}` had NO response cache and ran its five
  sections sequentially. Timed on prod: pharmaceuticals/germany 13.8s, engineering-machinery/germany
  12.4s, basmati-rice/germany 0.35s. Section profile: `_duty_section` 14.58s cold / 0.92s warm —
  the whole cost is the WITS tariff lookup.
- `duty_cache` has a 7-day TTL AND the weekly refresh job CLEARS it, so after every weekly
  refresh each product x country duty lookup is cold again (~15s) until something warms it.
  Products users/matrix touched recently were fast; untouched ones (pharma) were always cold
  and always exceeded what the edge pre-render worker waits for -> bare SPA shell.

### Fixes
- `seo_pages.py` NEW `_build_page_data()`: the 5 sections + `_related_links` now run under
  one `asyncio.gather` instead of sequentially.
- `seo_pages.py` `product_country_page()`: 24h response cache in `db.seo_page_cache`
  (`PAGE_CACHE_TTL`), `?force=true` to rebuild, cached responses carry `cachedAt`.
- `seo_pages.py` NEW `warm_page_cache()` + admin route `POST /api/seo/warm-pages`
  (x-admin-token). Pre-builds all 448 product x country payloads, semaphore 3.
- `seo.py` NEW `_warm_page_cache()` scheduled 8 min after boot and daily 03:10 UTC, so a
  deploy or a weekly duty-cache clear self-heals without anyone touching it.
- `duty_engine.py` NEW `_WITS_GATE` (asyncio.Semaphore(4)) around `_wits_obs`. Without it the
  warmers fanned out hundreds of concurrent WITS calls and starved the event loop — that is
  exactly what made 27/29 of the first test run time out at 30s.
- `seo_pages.py` `matrix()` now coerces a non-int `min_score` to 0, fixing
  `'>= not supported between int and Query'` when called directly by the warmer
  (reported by the deployer agent; cosmetic for warming, not the shell cause).

### Verification
- Warm run: 448/448 built, 400 indexable (up from 392).
- page-data after warm: 0.229-0.242s across all 8 products incl. every URL that was a shell.
- API stays sub-second (0.39-0.58s) WHILE the background matrix force-rebuild runs — the
  WITS gate holds.
- `backend/tests/test_seo_page_cache.py`: **29 passed** (first run before the WITS gate: 27 failed
  on ReadTimeout).
- Preview `/export/pharmaceuticals/to/germany`: h1 + epc-related + epc-hub-crumb + real
  numbers (HS 300490, 0% MFN 2023, 0.7% RoDTEP, $25.75B imports rank #3).
- NOT yet live: needs a production deploy, then the boot warmer runs 8 min later. Re-audit after that.

### GSC state (owner screenshot, 10 Oct 2026)
- Both sitemaps Success, 975 discovered pages each. Discovery was never the problem; keep ONE
  canonical submission (`/api/sitemap.xml`) and do not resubmit as a remedy.

### Deployer agent verdict (run b5226749) — superseded
- Attributed the shell to the managed Cloudflare pre-render worker (cache/quota/route depth)
  because it has no Cloudflare visibility. The real cause was our own cold-cache latency.
  Lesson: profile the API per product before escalating to the platform.
