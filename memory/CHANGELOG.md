# LeadNation — Changelog

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
