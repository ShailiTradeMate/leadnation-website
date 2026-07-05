# LeadNation — Production Readiness & Deployment Report
**Baseline:** Volume 1 + Volume 2 Phase 2A (feature-frozen) · Tag target: `v1.0-leadnation-command-center-production-ready` · Updated: 2026-07-05 (Final launch wrap-up)

## 0. Final Launch Wrap-up — status
| Item | Status |
|---|---|
| Legal pages (Privacy, Terms, Cookie, Disclaimer, Refund) | ✅ DONE — `/legal/*` routes, reusable `LEGAL_LINKS`, footer + signup + checkout links, sitemap entries. Company: Vametra AI Technologies Pvt Ltd. |
| App store / payment readiness | ✅ Legal links reusable in footer, signup (`signup-legal`), checkout (`pricing-legal`); shareable URLs for Play Store / App Store / Stripe / Razorpay verification. |
| Admin security final check | ✅ Reviewed — see §A. |
| Auth production checklist | ✅ Documented — see §B and the App Integration Guide. |
| SEO | ✅ robots.txt, sitemap.xml (+pricing/legal), meta/OG/Twitter/canonical present; default `<title>` fixed to LeadNation; per-page `<SEO>`/Helmet on legal + pricing. |
| Performance | 🟡 Reviewed — see §C. |
| Analytics placeholders | ✅ Env-driven (GTM/Clarity/Meta); no fake IDs; activate when real IDs provided. |

## A. Admin Security (reviewed)
- `require_admin` (core.py): Firebase Bearer token → verify → Mongo `users.role == "admin"` and not deleted. Legacy `X-Admin-Token` (env `ADMIN_TOKEN`) kept only as emergency fallback.
- No hardcoded secrets/tokens/keys in source (verified). All secrets env-driven.
- Super Admin / Customer ID `00001` protection is owned by the shared DigitalOcean auth backend (the website never allocates or mutates Customer IDs — by design). No `00001` logic exists in this codebase (correct).
- ⚠️ Production action: rotate `ADMIN_TOKEN` + `ADMIN_PASSWORD`; consider disabling the legacy token fallback in prod (a static token grants admin).

## B. Auth Production Checklist (documented)
- Add production website domain to **Firebase Authorized domains** and to the **DO backend CORS allow-list**.
- Shared Firebase UID → shared Mongo profile → shared 5-digit Customer ID across web + app. No duplicate user creation (backend resolves identity from the Firebase token).
- Set backend `CORS_ORIGINS` to the production web + app origins (not `*`).

## C. Performance (reviewed)
- Images: stock via Unsplash CDN (auto-format/compressed); report QR via external image API.
- 3D Globe: react-globe.gl with auto-rotate; India overlay served locally (`/geo/india-states.json`). Acceptable on desktop; consider a static map fallback for low-end mobile.
- Mobile responsiveness (web): Tailwind responsive across pages.
- Bundle: CRA/craco default; recharts + globe are the heaviest deps. Consider route-level lazy-loading of CommandCenter/Globe post-launch.
- Caching: costing/duty results cached server-side; first quote per fresh HS+lane ~15-25s (cold WITS), cached after.
- Brain loading states: present; deterministic results render first, Brain narrative after.

---

## 1. Website Production Readiness Report

| Area | Status | Notes |
|---|---|---|
| Deployment blocker scan | ✅ PASS | deployment_agent: no hardcoded secrets/URLs; all secrets env-driven. |
| Environment variables | ✅ | Backend: MONGO_URL, DB_NAME, CORS_ORIGINS, ADMIN_TOKEN/EMAIL/PASSWORD, EMERGENT_LLM_KEY, STRIPE_API_KEY, BRAIN_* . Frontend: REACT_APP_BACKEND_URL, REACT_APP_AUTH_API_BASE, REACT_APP_FIREBASE_*, analytics IDs. |
| Backend binding / routing | ✅ | 0.0.0.0:8001, all routes under `/api`, supervisor-managed. |
| CORS | ✅ (action at deploy) | `CORS_ORIGINS` env (defaults `*`). **Set to the production web + app origins at deploy.** |
| Firebase authorized domains | ⚠️ ACTION | Add the production website domain (and app) to Firebase Auth → Authorized domains, and to the DO backend CORS allow-list. Preview host is currently blocked by design. |
| Mongo indexes | ✅ ADDED | Idempotent indexes on trade_projects, trade_project_scenarios, trade_project_events, trade_project_brain_history, payment_transactions, downloads, subscriptions, email_captures, paywall_events (server startup). |
| Admin protection | ✅ | `require_admin` (Firebase admin claim OR X-Admin-Token). Rotate `ADMIN_TOKEN`/`ADMIN_PASSWORD` for production. |
| Error handling | ✅ | Engines degrade gracefully; Brain has deterministic fallback; adapters return ok=false without crashing. |
| API rate limits | ⚠️ BACKLOG | No app-level rate limiting yet — rely on ingress/CDN limits initially; add per-IP limits post-launch. |
| SEO | 🟡 PARTIAL | react-helmet-async titles present; sitemap/robots/meta audit pending (run seo audit separately). |
| Performance | 🟡 | First quote per HS+lane cold ~15-25s (WITS), cached after. Consider pre-warming top lanes. |
| Mobile responsiveness (web) | ✅ | Tailwind responsive layouts across Command Center + pages. |
| Analytics placeholders | ✅ READY | GTM/Clarity/Meta Pixel wired via env (`REACT_APP_GTM_ID`, `REACT_APP_CLARITY_ID`, `REACT_APP_META_PIXEL_ID`) in `components/Analytics.jsx` — set IDs to activate. |
| Legal pages | ✅ DONE | Privacy, Terms, Cookie, Disclaimer, Refund at `/legal/*` — global scope, covers Firebase/Mongo/AI/Stripe/Razorpay/analytics/cookies/UGC/marketplace/reports/subscriptions/trade-data disclaimer. |

## 2. App Integration Report
- Full technical handoff delivered: **`/app/memory/TRADE_COMMAND_CENTER_APP_INTEGRATION_GUIDE.md`** — product overview, architecture, backend module responsibilities, complete API contracts (Projects, Costing, Simulation, Decision/Scores, PDF, Brain), DB schemas, RN screens, UI/UX mapping, shared-auth rules, offline reqs, PDF sync, Brain rules, and a cross-surface testing checklist.
- **Thin-client contract:** the app duplicates no business logic; it calls the shared FastAPI backend and shares one Firebase project, one MongoDB, one Customer-ID sequence, one auth, one identity.
- Auth: same Firebase UID + DO auth backend (`REACT_APP_AUTH_API_BASE`), 5-digit Customer ID consumed/validated client-side only.

## 3. Remaining Backlog (post-launch, no new features until live)
- P1: Razorpay wiring for India (awaiting API keys) — pricing/gateway toggle already ready.
- P1: My Reports history + shareable public/private links with expiry (`trade_project_reports`).
- P1: Legal pages (Privacy/Terms/Cookie/Disclaimer/Refund).
- P1: Activate analytics (set GTM/Clarity/Meta IDs).
- P1: API rate limiting + basic abuse protection.
- P2: Volume 2B (Monte Carlo + Sensitivity), 2C (Recommendation/Risk/Forecast), 2D (World Map + charts), Volumes 3 & 4.
- P2: SEO/Lighthouse audit; pre-warm hot trade lanes.

## 4. Known Issues
- Firebase in-browser login is CORS-blocked in the **Emergent preview** (works in production once domains are authorized). Admin/authed UI flows are validated via backend token + guest sessions in preview.
- First quote per fresh HS+lane is slow (cold WITS fetch ~15-25s), then cached. Show loading state; use ≥30s client timeout.
- PDFs are generated client-side (print-to-PDF); not yet persisted server-side (blocks shareable links until the reports collection is populated — backlog).
- `trade_project_reports` / `trade_project_versions` collections are reserved (versions currently stored inline on the project doc).

## 5. Deployment Checklist
- [ ] Set `CORS_ORIGINS` to production web + app origins (not `*`).
- [ ] Rotate `ADMIN_TOKEN` and `ADMIN_PASSWORD`; confirm `ADMIN_EMAIL`.
- [ ] Add production domain(s) to Firebase Authorized domains + DO backend CORS allow-list.
- [ ] Confirm `MONGO_URL` / `DB_NAME` point to the production Atlas cluster (shared with app).
- [ ] Verify `STRIPE_API_KEY` (live) + Stripe webhook URL `{host}/api/webhook/stripe`.
- [ ] Confirm `EMERGENT_LLM_KEY` balance / auto top-up for the Brain.
- [ ] Set analytics IDs (GTM/Clarity/Meta) if launching with tracking.
- [ ] Verify Mongo indexes created on first prod boot (startup log: "MongoDB indexes ensured").
- [ ] Smoke test: create project → quote → scenario → decision → recommendations → export PDF.
- [ ] Commit stable version via **Save to GitHub**; then create tag `v1.0-leadnation-command-center` on GitHub as the production baseline.
