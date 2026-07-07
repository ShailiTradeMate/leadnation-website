# LEADNATION — PRODUCTION DEPLOYMENT REPORT

_Product: **LeadNation** · Company: **Vametra AI Technologies Pvt Ltd** · Prepared: 2026-07-06_

> Fill the `<LIVE_...>` placeholders after Emergent "Deploy Now" completes.

---

## 1. URLs — ✅ LIVE
- **Website (public):** https://leadnation.app  (apex is canonical; https://www.leadnation.app → 308 redirect → apex) ✅ SSL valid (HTTP/2)
- **Emergent deployment URL (internal ref):** https://trade-brain-ai.emergent.host  (users must NOT use this)
- **Backend API:** https://leadnation.app/api  (health `GET /api/events/list` → 200) ✅
- **Firebase Authorized Domains:** leadnation.app + www.leadnation.app added; Google login verified ✅

## 2. Database
- **MongoDB Atlas**, DB = `leadnation` (shared with mobile app). Connected via `MONGO_URL` env.
- New collections this release: `expo_listings`, `event_submissions`, `event_payments`,
  `trade_news_admin`, `news_items`, `uploaded_files`. (Analytics uses `events` — separate.)

## 3. Firebase
- Project `trademate-new` (shared web + app). Service account via `FIREBASE_SERVICE_ACCOUNT_B64`.
- **ACTION (owner):** Firebase Console → Authentication → Settings → Authorized domains →
  add `leadnation.app` and `www.leadnation.app`.

## 4. Email (Resend) — LIVE
- Sender: `LeadNation by Vametra AI Technologies Pvt Ltd <noreply@leadnation.app>` (domain verified).
- Admin alerts → `admin@leadnation.app`. All lifecycle/report/payment/admin templates test-delivered OK.
- Non-blocking + auto-retry on rate limit. Free tier = 100/day, 2/sec (upgrade for volume).

## 5. Mobile app connection values (thin client — same backend/DB/Firebase)
- `EXPO_PUBLIC_API_BASE = https://www.leadnation.app/api`   ← Events, News, Uploads, Brain, Command Center, Pricing
- `EXPO_PUBLIC_AUTH_API_BASE = https://leadnation-lfrhs.ondigitalocean.app/api`   ← identity / Customer ID / onboarding
- Firebase config: project `trademate-new` (same as web). One login, one Customer ID (00001 = admin).
- App can call: `/events/*`, `/news/*`, `/storage/*`, `/brain/*`, `/projects/*`, `/pricing/config`, `/downloads/*`.
- Full contracts: `TRADE_COMMAND_CENTER_APP_INTEGRATION_GUIDE.md` (ADDENDUM v1.1).

## 6. Production ENV checklist (set in Emergent deploy env)
| Var | Status |
|---|---|
| MONGO_URL / DB_NAME / FIREBASE_SERVICE_ACCOUNT_B64 / EMERGENT_LLM_KEY | ✅ keep |
| CORS_ORIGINS = https://www.leadnation.app,https://leadnation.app,<preview> | ✅ set |
| RESEND_API_KEY / SENDER_EMAIL / ADMIN_EMAIL | ✅ live |
| PUBLIC_SITE_URL = https://leadnation.app | ✅ |
| STRIPE_API_KEY | ⚠️ TEST now — add LIVE key post-deploy |
| RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET | ⛔ add live post-deploy (India ₹; falls back to Stripe-INR until then) |
| NEWSDATA_API_KEY | ⛔ optional — add for live wire news (AI/curated fallback until then) |
| ADMIN_TOKEN / ADMIN_PASSWORD | ⚠️ unchanged for now — **ROTATE before public launch** |

## 7. SEO — PASS
- Canonical, OG, Twitter, robots.txt, sitemap.xml, JSON-LD all → https://leadnation.app.
- **Next (owner):** Google Search Console → add property `https://www.leadnation.app` (or domain property
  `leadnation.app`) → verify via DNS TXT → submit `https://leadnation.app/sitemap.xml`.

## 8. Remaining manual actions (owner)
1. ~~Deploy~~ ✅ DONE — live at trade-brain-ai.emergent.host.
2. ~~Link www.leadnation.app~~ ✅ DONE — apex live, www redirects, SSL valid, email DNS untouched.
3. ~~Firebase authorized domains~~ ✅ DONE — leadnation.app + www added; Google login verified.
4. ⏳ **PENDING** — Add LIVE Stripe + Razorpay keys (Secrets tab) + Redeploy. (User sourcing keys.)
5. ⏳ Google Search Console → submit https://leadnation.app/sitemap.xml.
6. 🔒 **Before public launch:** rotate ADMIN_TOKEN + ADMIN_PASSWORD (Secrets tab) + Redeploy.

**Note (mobile app EXPO_PUBLIC_API_BASE):** point Events/News/Uploads/Brain/Command Center/Pricing to
`https://leadnation.app/api`; identity to the DigitalOcean base. Same MongoDB Atlas = consistent data.

## 9. App deployment checklist (separate job)
- Build React Native (Expo) per `APP_BUILD_PROMPT.md`; set the two env bases from §5.
- Events/News/Uploads created on web appear in app and vice-versa (shared Atlas DB); app submissions
  are reviewed by web admin. Emails fire server-side for both.

## 10. Future migration (Emergent → DigitalOcean / VPS)
- App is portable: FastAPI (uvicorn) + React static build + MongoDB Atlas (unchanged).
- VPS: Ubuntu + Nginx (reverse proxy `/api` → uvicorn:8001, serve React build) + PM2/systemd + Certbot SSL.
- Or PaaS (Render/Railway): backend web service (`uvicorn server:app`) + static site; set same env vars.
- Object storage is provider-abstracted (`STORAGE_PROVIDER`) → swap to S3/Spaces/Firebase without code rewrite.
- Repoint GoDaddy A/CNAME to the new host; keep the same MongoDB Atlas + Firebase + Resend.
