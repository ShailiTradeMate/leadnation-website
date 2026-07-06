# LeadNation — Changelog

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
