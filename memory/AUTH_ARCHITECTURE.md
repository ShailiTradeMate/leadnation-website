# LeadNation — Auth & Profiles Architecture (SOURCE OF TRUTH)
> Read this before ANY change to login, account settings, profiles, or admin user-management.

## Strict rule
The website is a **FRONTEND ONLY**. It calls the **already-deployed shared backend**.
DO NOT create a new backend, a new database, or a new Firebase project. The website must
**NEVER connect to MongoDB directly**.

## Shared infrastructure (do not recreate)
- **Deployed backend (API base for ALL auth/profile/admin-user calls):**
  `https://leadnation-lfrhs.ondigitalocean.app`  → endpoints under `/api/...`
- **Shared DB:** MongoDB Atlas, DB `leadnation` (only the deployed backend touches it).
- **Shared auth:** Firebase project `trademate-new` (Email/Password + Google).
- **Join key:** Firebase `uid`. **Human key:** `customer_id` (00001…). One user = one Firebase UID = one Customer ID = one profile (shared with the mobile app).

## Frontend Firebase web config (client SDK) — REACT_APP_FIREBASE_* in frontend/.env
- API_KEY=AIzaSyCHQaCkzlfOdVB1-bzuJ_NnCE7vRFmT5WA
- AUTH_DOMAIN=trademate-new.firebaseapp.com · PROJECT_ID=trademate-new
- STORAGE_BUCKET=trademate-new.firebasestorage.app · SENDER_ID=17751684107
- APP_ID=1:17751684107:web:6e4f12ea8a2b47fac7030e

## Auth flow
1. Firebase client SDK sign-up/login → get Firebase **ID token**.
2. Send `Authorization: Bearer <idToken>` on every protected backend call.
3. First signup → `POST /api/onboarding/register` (Bearer; {full_name, role, mobile_number, provider}) → backend allocates the shared Customer ID. NEVER generate Customer IDs on the website.
4. Login with Customer ID → `POST /api/auth/resolve-customer-id` {customer_id} → email → Firebase email/password login.
- Support: Email/Password, Google, Password Reset, Email Verification, session persistence.

## Key backend endpoints (already exist — just call them)
- POST `/api/onboarding/register` (Bearer)
- POST `/api/auth/resolve-customer-id`
- GET `/api/v1/profiles/{uid}` · POST `/api/v1/profiles`
- GET `/api/admin_v2/users` (+ `/{customer_id}`)
- POST `/api/admin_v2/users/{customer_id}/suspend|reactivate|approve|override-verification`
- DELETE `/api/admin_v2/users/{customer_id}/hard-delete` (system-wide: Mongo+Firebase+Firestore)

## Roles (verbatim)
Business: exporter, importer, supplier, manufacturer, farmer, cha, export_agent, consultant.
Platform: `role` = "user" | "admin". manufacturer/farmer may stay hidden in UI for now.

## Profile fields (backend owns schema)
users: uid, customer_id, email, full_name, role, user_role, mobile_number, provider,
  is_email_verified, onboarding_status, verification_status, subscription_status, country, country_code, state, city.
profiles: uid, customer_id, name, mobile, email, role, country, city, hsn_codes[], products[],
  business_media{images[],videos[]}, company_details{company_name,description}, verification_status.
Role-specific: exporter→iec_number,gst_number · supplier/manufacturer→gst_number · cha→cha_license_no · farmer→farm_id,crop_types.

## Admin (shared identity)
admin = Firebase user `admin@leadnation.app` (customer_id 00001, role=admin), protected.
Same admin works on the website automatically. Admin panel manages the website AND any user
(suspend/reactivate/approve/verify/role/subscription/hard-delete) — reflects across app + website.

## Domain authorization (2 places)
1. Firebase Console → Authentication → Authorized domains (for login). leadnation.app/www allowed; preview domain `global-trade-hub-176.preview.emergentagent.com` added.
2. Deployed backend **CORS allow-list** — leadnation.app allowed. ANY other domain (incl. the Emergent preview) must be added by the app owner, else auth calls are CORS-blocked.

## Frontend wiring in THIS repo (IMPLEMENTED — direct calls, NO proxy)
- `REACT_APP_AUTH_API_BASE` (frontend/.env) = `https://leadnation-lfrhs.ondigitalocean.app/api` → ALL auth/profile/admin-user calls go here directly (see `src/lib/authApi.js` + `AuthContext.jsx`). Firebase `Bearer` token attached automatically.
- `REACT_APP_BACKEND_URL` → our own content backend (Brain, trade-intel, duty, compile, customs, CMS settings/leads). It owns NO identity.
- Local `accounts.py` DELETED. The website performs NO identity DB writes. Local `core.require_admin` only READS the shared `users.role` (same Atlas) to gate website-only CMS endpoints.

## Verified DO backend contract (June 2026 — empirically confirmed)
- POST `/api/auth/resolve-customer-id` {customer_id} → {email, customer_id}  ✅
- POST `/api/onboarding/register` (Bearer) → idempotent; returns {customer_id, role, onboarding_status, verification_status, is_existing}  ✅
- GET `/api/v1/profiles/{uid}` (Bearer) → full current-user profile {customer_id, role, email, name, verification_status, ...}. **Used as the "current user" source — DO backend has NO `/api/auth/me`.**  ✅
- POST `/api/auth/send-otp` {type:"email", value:<email>} (Bearer) → sends email OTP. (There is NO `/api/auth/request-otp`.)  ✅
- POST `/api/auth/verify-otp` {type:"email", value:<email>, otp} (Bearer) → verifies.  ✅
- GET `/api/admin_v2/users` (admin Bearer) + DELETE `/{cid}/hard-delete`  ✅

## CORS status (June 2026)
- ✅ Production `https://www.leadnation.app` / `https://leadnation.app` → preflight 200 + allow-origin. Login works in production.
- ❌ Emergent preview origin `https://global-trade-hub-176.preview.emergentagent.com` → preflight 400, NO allow-origin. **Browser login in the Emergent preview is CORS-blocked.** The backend owner must add the exact preview origin to the DO CORS allow-list to test in-preview. (Integration is correct — verified server-side via curl.)

## Scope (this phase)
Login/auth + profile + admin (incl. hard delete) ONLY. No payments/reports/marketplace yet.
