# Vametra AI / LeadNation — Product Requirements & Current State

Last updated: **2026-09-30**. Historical detailed requirements and implementation evidence formerly in this file are preserved verbatim in `PRD_HISTORY_PRE_MOBILE_2026-09-30.md`. See `CHANGELOG.md` for milestones and `ROADMAP.md` for the prioritized backlog.

## Original product and users
Vametra AI is a global trade-intelligence website for importers, exporters, suppliers, learners, and administrative staff. It provides AI trade advice, a project-based Trade Command Center, verified buyer discovery, customs/duty/landed-cost tools, country/product intelligence, trade news, upcoming expos, business services and a free Trade Academy. The public brand/domain is Vametra AI / vametra.com; internal LeadNation identifiers remain unchanged.

## Architecture and non-negotiable contracts
- React 19 / React Router frontend, FastAPI backend (`backend/server.py`), MongoDB local overlays/cache/settings/service data.
- Frontend APIs use `REACT_APP_BACKEND_URL`; backend routes are `/api/*`. Database uses existing `MONGO_URL` and `DB_NAME` without renaming either.
- DigitalOcean shared identity APIs own canonical user/company identity, Customer ID, GEID and authoritative profile readbacks. Firebase handles buyer sign-in. Website-local staff use separate JWT auth. No competing identity stores.
- Never treat local `members_bridge` snapshot as authoritative identity truth. Canonical verification statuses are `approved` / `rejected` (some legacy UI uses verified).
- Preserve subscription/contact gates, source privacy, legal acknowledgment, admin sign-off rules, pricing overrides and established design language.
- New dropdowns must use `components/ui/responsive-select.jsx`; geographic fields use `components/LocationSelect.jsx` and `data/geo.js`. Do not add short hardcoded country arrays or browser-native form selects to app pages.
- Use unique `data-testid` values for interactive/critical UI elements. Preserve API value contracts (ISO codes vs names; lowercase codes for news).

## Latest owner request — verbatim
“The website is currently not functioning well in mobile view. If the user is checking the website on mobile, in that case the user is not able to select any dropdown, nor are they able to see the options in the dropdown on any page/function/tab/onboarding process anywhere.

Also from now on, please add all the 195 countries/states/cities, etc in the in all the respective dropdowns.

make sure the mobile view should be the perfect for all the users.”

Owner approved proceeding with a site-wide mobile dropdown repair, comprehensive countries plus territories, dependent state/city choices and manual entry for missing localities. Unrelated Academy/Brain, marketing, and prior admin workflow engineering remain parked.

## Latest milestone — implemented and verified, awaiting owner acceptance
### Mobile dropdowns and geography (2026-09-30)
- Replaced all **58 native select call sites in 22 pages** with a shared Radix Dialog + cmdk picker: touch targets, searchable readable options, independent scrolling, keyboard navigation, Escape/cancel, focus return, high stacking above admin modals/cookies, and visual-viewport keyboard sizing. Existing handlers/value contracts preserved.
- Applied across signup roles/dial codes, verification role/doc/location, account, Expo, news, buyers, customs/tools, Command Center and admin/pricing/action forms. Country text inputs in Brain, account, directories/suppliers and CMS also use the common country selector.
- **250 countries/territories** (including all 195), **4,963 subdivisions**, **148,038 city records** from country-state-city 3.2.1 (ODbL). This is NOT a claim to list every settlement worldwide. State/city search permits explicit custom entries and retains manual entry if loading fails.
- Country list bundled locally; each country's states/cities loaded on demand from `/geo/{ISO}.json`. No third-party geo credentials/network API. Generator `frontend/scripts/generate-geography.cjs` reproduces frontend/backend catalogs and license files.
- Country change clears state/city; state change clears city. Explicit empty locality fields included in verification/admin profile save payloads so old localities are not silently retained. Existing profile values remain displayed; no saved user profiles changed during tests.
- `/api/countries`, `/api/duty/countries`, `/api/command-center/markets`, `/api/news/countries` each return 250 unique countries. Existing business-calculation coverage/rate data are NOT fabricated or expanded. Event queries match ISO/full-name/legacy aliases (e.g. AE/UAE/United Arab Emirates).
- Mobile header no longer overflows: fixed `.btn-*` overriding hidden utilities, accessible menu toggle, mobile account link, Explore/Learn tap groups, pointer-aware wide-screen navigation. Floating Brain/WhatsApp launchers hidden on small screens so they cannot obstruct form controls; Brain/contact access remains in navigation/site content.
- Fixed signup flex-width overflow, bounded decorative effects, and stabilized Expo country choices during asynchronous hydration.

### Test evidence
- `test_reports/iteration_67.json`: initial agent run, 14/15 API tests plus broad mobile touch/public/auth/admin selector regression; identified country endpoint mismatch, Expo first-open concern, tablet grouping and an onboarding test gap.
- **Final API rerun: 15/15 passed**, `test_reports/pytest/iter67_retest.xml`, `test_reports/iter67-retest.log`. Four country endpoints each independently checked for 250 unique codes. All three UAE aliases returned the same 5 events.
- Main-agent browser follow-up resolved onboarding test gap using the REAL existing account (no fixture): France → Île-de-France → Paris, country reset, role selection. Save payload check intercepted and **aborted** the PUT before the server; verified country/state/city keys, without writing user data.
- Mobile touch signup selection (Armenia/Zimbabwe) and role options, desktop keyboard Arrow/Enter, Escape and focus return, mobile Explore/Learn groups, and first-tap wide-screen touch navigation passed.
- Expo initial-open options checked repeatedly (251/252 entries including All/legacy labels), country selection/clear passed. No persistent empty list reproduced when waiting for visible options; country-choice memoization removes unnecessary hydration churn.
- **Zero horizontal overflow** in final 390×844 verification/Expo checks and 1920×800 Expo check. Screenshots: `onboarding-mobile-check.jpg`, `mobile-final.jpg`, `expo-desktop-final.jpg`, `dropdowns-mobile.jpg`.
- Production frontend build passed (pre-existing hook-dependency warnings / large-main-bundle warning remain). Latest payload-only changes also exercised in browser.
- Safari/WebKit browser binary is unavailable in this environment; actual iPhone/Safari and physical Android testing remain owner acceptance checks. Do not claim all physical devices were tested.
- No app APIs/integrations were mocked for this milestone. No auth credentials created/changed; no prices, user profiles or verification statuses mutated. Full verification submission, payments and email delivery were intentionally not exercised.

## Previous completed milestones
- Business Services pricing editor + Business Website service (India ₹35,000/year, international US$2,500/year, 11 scope items), iteration66: 9/9 backend + frontend verified; owner acceptance pending.
- Homepage visual redesign/motion/mobile work, free Trade Academy section replacing “See trade happen”; “Engineered for India” removed.
- Verified Buyers source categories + required legal/data-usage acknowledgment, frontend-only; buyer data/verification logic preserved.
- Product Info frontend retired; product intelligence consolidated into Brain. News country/topic/live freshness; Expo live/upcoming refresh and admin notification records.

## Integration status and limitations
- DigitalOcean + Firebase: existing authoritative identity/auth, untouched by this milestone.
- Resend: admin notification records evidenced; actual recipient inbox delivery remains unconfirmed.
- NewsData key was empty in previous checks; Google News RSS + GDELT provide live news; GDELT may fail gracefully.
- Government registry matching remains **MOCKED / not live-validated** from prior work; requires authorized registry access. This is unrelated to location data, which is real offline reference data.
- Never rerun destructive old tests57–62 against deleted fixtures. Credential/status source: `test_credentials.md` (private).

## Tools rewire — 8 Oct 2026 (iteration 70, 25/25 backend + all frontend flows passed)
- Every `/tools/*` page now embeds the REAL Customs & Compliance Engine components (shared `components/engines/CustomsEngineTools.jsx`): Duty (WITS+RoDTEP), Landed Cost = Command Center quote, Product Research = OEC Trade Statistics, Incentives = RoDTEP+Govt benefits, Buyer Discovery = real `/api/buyers/search`. No duplicated logic; each page has "Open in full Customs & Compliance Engine" (`/customs-compliance?tab=`).
- HSN Finder: all 5,606 HS codes + trade-name alias layer (`TRADE_ALIASES`) + DGFT RoDTEP + IGST slab + live WITS duty at destination. `/api/hsn/{code}` now works for any HS6 (curated knowledge merged for 5 flagship lines).
- Country dropdowns for duty/command-center lanes use `/api/duty/countries` (56 WITS countries, ISO-numeric) via `LaneCountrySelect` — the old alpha-2 list silently returned no data.
- "Vametra AI Brain · next steps" panel (`POST /api/tools/next-steps`) under every result: AI read of the user's numbers (Emergent key, falls back to deterministic text) + pre-filled links to the next tool/buyers/export guide/Brain + plan upsell. Fires `tool_next_step` / `upgrade_cta_click` analytics events.
- Removed mock endpoints: `/duty-calc`, `/landed-cost`, `/export-incentive`, `/product-research`, `/find-buyers` (legacy tests in `tests/test_leadnation_api.py` for these are obsolete).
- **Global, not India-centric (owner rule 8 Oct):** every tool must take exporting + importing country; India-specific schemes (RoDTEP, IGST) appear only when India is the origin/destination. HSN Finder updated accordingly.
- Rule going forward (owner): never build duplicates; every feature must be useful for marketing and route to signup/plan.

## SEO pre-render reliability — 10 Oct 2026 (29/29 pytest)
- Export guides were served as a bare SPA shell to Googlebot because `/api/seo/page-data` had no
  cache and a cold WITS duty lookup took ~15s, longer than the edge pre-render worker waits.
- Now: 24h `db.seo_page_cache`, concurrent section fetch, `POST /api/seo/warm-pages`, a boot+daily
  warm job, and a global WITS concurrency gate so warmers cannot starve the event loop.
- All 448 product x country payloads pre-built (400 indexable); page-data responses ~0.23s.
- **Needs a production deploy** — the boot warmer then runs 8 min later. Re-audit afterwards.
- Full detail in `CHANGELOG.md` (2026-10-10) and `PRERENDER_ESCALATION.md`.

## GSC rich-result + head hygiene — 10 Oct 2026 (preview verified, needs deploy)
- GSC confirmed `/export/indian-spices/to/chile` is indexed and fully rendered (prerender fix worked).
- GSC "Product snippets: 1 invalid item" → `about` was `@type: Product` without offers; now `Thing`
  (ExportProductCountry, Products.jsx, SEO.productSchema).
- Crawled HTML had two `<title>`/description/og sets: React 19 hoists Helmet tags and does not dedupe
  the static ones in `public/index.html` → static title/description/og/twitter removed; every public
  page renders `<SEO>`; admin pages got `<SEO noindex>`.
- BreadcrumbList pointed at `/products/indian-spices` (not a real page) → now `/export` → `/export/{product}`.
- New `/api/answers/index.html` (HTML directory of 413 answer docs) for AI browsing tools that refuse JSON.

## Production verification — 10 Oct 2026 late (`memory/audit_2026-10-10/REPORT.md`)
- Googlebot full audit: 392 guides → 381 rendered / 11 shell / 0 errors; 15 hubs OK. Shells = cold page-data
  holes that the edge then cached (`x-rendered-by: crawler-cache`, max-age 3600). 413 answer docs all clean.
- Fixes (preview only, NOT deployed): stale-while-revalidate page cache + 6-hourly retrying warm;
  rail links only to existing `/countries/*` (5) and `/corridors/*` (4) — 44/49 countries were soft-404s.
- Open owner decision: SoftwareApplication `aggregateRating 4.8/126` provenance.

## Brand consistency + AI readability + cache warming — 15 Oct 2026 (preview verified, NOT deployed)
- Brand facts everywhere: founded 2026, HQ "Savedi, Ahilyanagar, Maharashtra 414003, India" (short form,
  also Legal.jsx + llms.txt), founder Vaibhav Deshmane, LinkedIn display `linkedin.com/company/vametra.com`.
- "195+ countries" removed from all 22 places (12 files) → "contact-verified buyers across 32 countries" /
  "56 tariff-reporting countries". Camera/imaging FAQ + paragraph removed from /about.
- llms.txt: fixed false "Platforms: Web, iOS, Android" → web only; added /about + its answer doc.
- New `/api/answers/{md,html,json}/about` entity document (index now 414; sitemap unchanged at 974).
- Cache warming: page-data warm now oldest-first, 4 concurrent, 250 ms stagger, run log in `seo_warm_runs`;
  NEW prerender warm of 34 key static pages (Googlebot UA → vametra.com) every 45 min (:05/:50) + 2 min
  after boot; admin `GET /api/seo/warm-status`, `POST /api/seo/warm-prerender`. First run: 34/34 OK,
  7 were cold (6–12 s) and are now cached — this was the "cache miss" ChatGPT hit on /about.
- Backlog: Google Business Profile (revisit when eligible); Home "32K HS Codes" / "1.2M Data points" stats unverified.

## Part 6 — answer-first rewrites — 16 Oct 2026 (preview verified, iteration_75, NOT deployed)
- 71 pages: keyword-led titles ≤60 + H1 with keyword (`data/seoTitles.js`, `seo/PART6_PAGE_PLAN.md`), `AnswerFirst`
  block (direct answer + dated data table from new `GET /api/seo/facts` + 5 links) on 28 templates, FAQPage/Breadcrumb.
- Soft-404 hardening on 8 detail templates via `loadEntity()`; genuine not-found now `noindex`; loading state = final title.
- Nav bell only when logged in. CTARow "Download app" removed. Home stats → 5,606 HS codes / 56 tariff countries.
- Prerender warm now 56 key pages. Acceptance report: `memory/seo/PART6_ACCEPTANCE.md` (15/16 pass, #16 after deploy).

## Priorities / next actions
- **P0:** Deploy, then Googlebot-render audit of the 71 Part-6 URLs + `/about` as GPTBot; `/api/answers/md/about`.
- **P0:** Deploy, then: GSC "Validate fix" on Product snippets, re-run `audit_2026-10-10/guides_audit.py`
  once the edge shell cache has expired (or ask platform to purge the 14 URLs), re-inspect 3 guides.
- **P0:** Deploy, then re-audit the export guides with Googlebot UA and report rendered/shell counts.
- **P0 (marketing Part 6):** answer-first rewrites of the older pages + the 16-item acceptance report.
- **P0:** Owner mobile-device acceptance (iPhone/Safari and Android); latest admin-pricing acceptance still pending. Any newly reported mobile defect takes priority.
- **P0 (SEO plan):** Part 3 server-side pre-rendering for SEO routes → Part 4 region hubs/country pages → Part 5 product×country batch. See `memory/seo/EXECUTION_PLAN.md`.
- **P1:** Fresh vametra.com marketing/SEO/GEO plan (do not recycle leadnation.app plan); Academy ↔ Brain coordination remains backlog-only; Expo email inbox validation.
- **P2:** International Expo pricing; localized location names and reproducible geographic-data refresh; optional remembered recent countries.
- Frozen until expressly requested: broad admin/buyer approval regression, hard-delete consistency, CMS volume/timeouts, live registry integration, subscription/payment changes.
## 2026-06 Nav fix
- Fixed clipped "Explore Vametra AI" CTA in desktop nav (Nav.jsx): tightened logo/link padding and action gaps; CTA shows short "Explore" label between lg and xl widths, full "Explore Vametra AI" at 2xl+, so the nav row now fits inside the max-w-7xl container at every desktop width.

## 2026-06 Smart HS resolution (any product name)
- New backend/hs_resolver.py: HS6 resolution tiers — directory phrase match -> LLM classifier -> Gemini web-grounded lookup -> residual "n.e.c." heading in the same HS heading; every candidate validated against the HS directory, results cached in Mongo (hs_resolver_cache, 180d hits / 3d misses).
- Wired everywhere: /api/trade-intel/hs-search (typeahead fallback), /api/hsn-finder (+resolution banner), brain/explore (hsResolution + classification note), brain/engines, costing_engine, compile_engine.
- Local/misspelled names now work: brinjal & bringle -> 070930, okra & bhindi -> 070999, basmati rice -> 100630; nonsense input stays unresolved (no fabricated code). Duty/demand still only from WITS/OEC.
- Also added BrainThinking loading animation on /brain/explore. Verified by testing agent iteration_77 (backend 7/8 - one cold-start timing bound, frontend 100%).
