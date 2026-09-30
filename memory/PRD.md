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

## Priorities / next actions
- **P0:** Owner mobile-device acceptance (iPhone/Safari and Android); latest admin-pricing acceptance still pending. Any newly reported mobile defect takes priority.
- **P1:** Fresh vametra.com marketing/SEO/GEO plan (do not recycle leadnation.app plan); Academy ↔ Brain coordination remains backlog-only; Expo email inbox validation.
- **P2:** International Expo pricing; localized location names and reproducible geographic-data refresh; optional remembered recent countries.
- Frozen until expressly requested: broad admin/buyer approval regression, hard-delete consistency, CMS volume/timeouts, live registry integration, subscription/payment changes.