# LeadNation — Analytics Implementation Report
**Scope:** Production analytics activation only. No feature/logic/architecture changes. Date: 2026-07-05

## 1. Overview
Analytics is fully **environment-driven** and **privacy-safe**. Nothing loads or fires unless the relevant ID is set. Four channels are wired through a single reusable layer (`src/lib/analytics.js`), mounted app-wide via `AnalyticsProvider` (`src/components/Analytics.jsx`):
- **Google Tag Manager (GTM)** — central tag manager; all future marketing pixels route through GTM.
- **Google Analytics 4 (GA4)** — page views + custom events.
- **Microsoft Clarity** — heatmaps & session insights.
- **Meta Pixel** — optional; loads only if its ID exists; uses standard events where applicable.
- **First-party** — every event is also POSTed to `/api/track` → `db.events` (works regardless of external IDs; powers the future Admin analytics dashboard).

## 2. Environment Variables Required (all env-driven; leave blank to disable)
Set these in `frontend/.env` (CRA requires the `REACT_APP_` prefix), then rebuild/redeploy:

| Purpose | Variable | Example format |
|---|---|---|
| GA4 Measurement ID | `REACT_APP_GA4_ID` | `G-XXXXXXX` |
| GTM Container ID | `REACT_APP_GTM_ID` | `GTM-XXXXXXX` |
| Microsoft Clarity Project ID | `REACT_APP_CLARITY_ID` | `xxxxxxxxxx` |
| Meta Pixel ID (optional) | `REACT_APP_META_PIXEL_ID` | `1234567890` |

> The blueprint referenced `GA4_MEASUREMENT_ID / GTM_CONTAINER_ID / CLARITY_PROJECT_ID / META_PIXEL_ID`. In this Create-React-App frontend those map to the `REACT_APP_*` names above (browser env vars must be `REACT_APP_`-prefixed). No IDs are hardcoded.

## 3. Standard LeadNation Event System
Reusable API in `src/lib/analytics.js`:
- `trackEvent(name, meta)` — fans out to GA4 + GTM dataLayer + Meta Pixel + Clarity + first-party `/api/track` (all wrapped in try/catch; safe no-ops when a channel is absent).
- `trackPageView(path)` — auto-fired on every route change (SPA).
- `EVENTS` — named constants (below).

### Event List (implemented)
| Constant / name | Fires when | Where |
|---|---|---|
| `page_view` | every route change (all pages: country/product/HSN/blog/etc.) | AnalyticsProvider |
| `command_center_opened` | Command Center mounts | CommandCenter |
| `user_registered` | signup success (password/google) | Auth |
| `user_login` | login success (password/google) | Auth |
| `trade_project_created` | project created | ProjectContext |
| `quote_generated` | costing quote computed | ProjectContext |
| `scenario_created` | scenario created | CommandCenter · Simulation |
| `brain_query` | Brain question asked | CommandCenter · Brain |
| `pdf_report_created` | paywall shown for a report | CommandCenter · Reports |
| `pdf_report_downloaded` | report downloaded (free/subscription) | CommandCenter · Reports |
| `payment_attempt` | checkout initiated | CommandCenter · Account |
| `subscription_started` | monthly/annual checkout initiated | CommandCenter · Account |
| `payment_success` | Stripe redirect confirms paid | Account |
| `payment_failure` | payment not completed | Account |

### Meta Pixel standard-event mapping
`user_registered→CompleteRegistration`, `user_login→Lead`, `trade_project_created→Lead`, `command_center_opened→ViewContent`, `subscription_started→Subscribe`, `payment_success→Purchase`. All others use `trackCustom`.

### GTM conversion funnel (dataLayer events ready)
`page_view → user_registered → trade_project_created → pdf_report_downloaded → subscription_started/payment_success`. Build these as GTM triggers/conversions once the container ID is set.

## 4. Privacy (enforced in code)
`trackEvent` runs a **scrubber** that blocks any key containing: email, phone, mobile, name, customerId/customer_id, uid, token, password, address, buyer, supplier, notes, document(s), company, product, title — and drops all nested objects. Only safe non-identifying primitives (e.g., region, incoterm, plan, method, kind, currency) are ever sent. This aligns with the Cookie Policy and Privacy Policy. **Customer ID, email, phone, documents and business-confidential data are never sent to analytics.**

## 5. Clarity flows
Clarity records sessions site-wide when enabled; key flows to review: Homepage, Command Center, Pricing, Signup, Reports. Each `trackEvent` also tags the Clarity session (`clarity("event", name)`) for filtering.

## 6. Admin-future-ready
First-party events persist to `db.events` and are readable at `GET /api/admin/events` (admin-only). This is the data source for a future Admin analytics dashboard: total/active users, country-wise users, popular products/countries, reports generated, Brain usage, conversion rate and revenue funnel — buildable without further client changes (the events are already flowing).

## 7. Testing Result
- Frontend compiles cleanly (1 pre-existing Tailwind warning, unrelated).
- `POST /api/track` verified → `{ "ok": true }`; event persisted to `db.events` and returned via admin events endpoint.
- Privacy scrubber verified (only region/incoterm forwarded in the test event; no PII).
- External channels (GA4/GTM/Clarity/Meta) are dormant until their IDs are set — no scripts load with blank env (verified via env-gated `initAnalytics`).

## 9. Cookie Consent (GDPR / CCPA) — DONE
`src/components/CookieConsent.jsx` + consent-aware `analytics.js`:
- Banner for new visitors: "LeadNation uses cookies and analytics to improve your global trade experience." with **Accept All**, **Reject Non-Essential**, **Manage Preferences**.
- Categories: **Essential** (auth/security/session — always on), **Analytics** (GA4/GTM/Clarity — opt-in), **Marketing** (Meta Pixel + future pixels — opt-in).
- **Enforcement:** before consent, `initAnalytics()` loads NOTHING. On approval, only consented categories load (`loadAnalyticsScripts` / `loadMarketingScripts`). Opt-in model (GDPR).
- Preference stored in `localStorage` (`ln_cookie_consent = {essential, analytics, marketing, ts}`); banner not shown again.
- **Change anytime:** footer "Cookie Preferences" button (`openCookiePreferences()`) reopens the manager.
- First-party anonymous `/api/track` continues (privacy-scrubbed: never Customer ID, email, phone, documents, or confidential trade data).
- Verified: banner shows for fresh visitor → Manage modal renders → Save persists consent → banner dismissed → gating confirmed.

## 10. Suggestions
- Add a lightweight **cookie-consent banner** (EEA/GDPR): gate GA4/Clarity/Meta behind consent while keeping essential + first-party analytics. Recommended before EU marketing.
- Set **GA4 + GTM first** (biggest signal for lowest effort); add Clarity for UX; keep Meta Pixel for when paid ads start.
- Later, build the **Admin analytics dashboard** on `db.events` (already capturing the full funnel) to visualize conversion and revenue without third-party tools.
