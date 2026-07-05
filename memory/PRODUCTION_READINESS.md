# LeadNation — Production Readiness & Deployment Report
**Baseline:** Volume 1 + Volume 2 Phase 2A (feature-frozen) · Tag target: `v1.0-leadnation-command-center` · Date: 2026-07-05

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
| Legal pages | ❌ BACKLOG | Privacy, Terms, Cookie, Disclaimer, Refund not yet built. |

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
