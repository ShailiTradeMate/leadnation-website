# LeadNation Unified Identity & Architecture Standard — v1 (CANONICAL, BINDING)

> **Decision owner:** Website Emergent (final call, per user approval June 2026).
> **Applies to:** Website (`leadnation.app`) + Mobile App (Expo) + DigitalOcean identity backend. **This is the ONE way. No divergence permitted.**
> **Principle:** ONE identity, ONE allocator, ONE database, ONE Firebase, ONE Customer ID, ONE company identity (GEID). Website & app are thin clients; the DO backend owns identity.

---

## 1. FINAL DECISION — the single architecture
| Concern | Canonical decision | Rationale |
|---------|--------------------|-----------|
| **Identity provider** | ONE Firebase project `trademate-new` (Google + Email/Password + **Phone**) | Already shared; single credential store, passwords only in Firebase |
| **Database** | ONE Atlas DB `leadnation` (shared) | Already shared; both clients read/write the same |
| **Identity/business API** | ONE backend owns identity = **DigitalOcean** (`leadnation-lfrhs.ondigitalocean.app/api`). Website content/Brain backend (`leadnation.app/api`) is SEPARATE and does NOT own identity | Prevents two allocators / race conditions |
| **Customer ID** | 5-digit `users.customer_id`, allocated **ONLY** by DO backend via atomic `_counters` at `POST /api/onboarding/register`. `00001` reserved (admin) | Single allocator = no collisions across web/app |
| **Website role** | **Pure client.** Never mints IDs, never forks auth. On signup/first-login it *calls* the DO allocator; self-heals if `customer_id` missing | Already implemented in `AuthContext.jsx` ✅ |
| **App role** | Pure client to the same DO backend | Already true |
| **Company identity (CANONICAL)** | ONE `entities` collection keyed by **GEID** is the *sole, immutable identity layer* for any company. Identity (who a company IS, resolution, trust, provenance, relationships) lives ONLY here. | Single source of truth for identity |
| **Company profile data** | `company_profiles` stores **only editable/business profile fields** (logo, description, products, certs, contact prefs, etc.) and **references** its `entities.GEID` via a foreign key. It is NOT identity, NOT a source of truth for identity, and MUST NOT be used to resolve/merge companies. `profiles` = personal user profile only | Editable data is decoupled from identity; profiles never define identity |
| **Identity ↔ profile ↔ user join** | `members_bridge` { uid, customer_id, geid } is the ONLY join. company_profiles/user data point AT a GEID; they never own it | One join, GEID is the anchor |
| **Networking store** | **Mongo only.** Retire Firestore `user_connections`; all connections/requests/chats/messages on Mongo (`v1`/`v1b`) | One store; VBIE-ready |
| **Reports & user data** | Keyed by `customer_id` (+ `uid`) in shared DB → identical access on web & app | Already works once ID exists |

**Verdict:** the architecture is ratified as-is. The only build work is **(a) add Phone/mobile login** and **(b) reconcile the two networking stores + the company-profile canonical** — specified below.

---

## 2. FINAL DECISION — the single login method (works identically on web & app)
A user signs in with **any** of these; all resolve to the same Firebase identity → same `customer_id` → same data:

| Method | Flow | Status |
|--------|------|--------|
| **Google** | Firebase Google provider | ✅ web + app |
| **Email + password** | Firebase email/password | ✅ web + app |
| **Customer ID + password** | `POST /auth/resolve-customer-id` → email → Firebase sign-in | ✅ web (`loginWithCustomerId`) |
| **Mobile number (OTP)** | Firebase **Phone Auth** (`signInWithPhoneNumber` + reCAPTCHA on web / native on app) → same `uid` | ⛔ **TO ADD (both)** |

**Allocation rule (unchanged, canonical):** first successful login by ANY method → website/app calls DO `/onboarding/register` → 5-digit `customer_id` minted once, stored on the shared `users` record → visible to both platforms immediately (self-heal covers eventual consistency).

**Mobile as a login key:** capture `mobile` at register (E.164) → store on `users`. Add DO endpoint `POST /auth/resolve-mobile` (mirror of `resolve-customer-id`) so "login by mobile" resolves to the account even for password users. Phone-OTP sign-in links to the same `uid` (Firebase account linking) so one person = one identity regardless of method.

---

## 3. CHANGE-SET — Website Emergent (this repo) — I OWN THIS
1. **Add Phone/mobile login** to `AuthContext.jsx`: `signInWithPhoneNumber` + invisible `RecaptchaVerifier`; expose `startPhoneLogin(e164)` + `confirmPhoneOtp(code)`. Link phone to existing account when signed in (`linkWithPhoneNumber`).
2. **Auth UI** (`pages/Auth.jsx`): add "Mobile number" tab alongside Email / Customer-ID / Google. Add `data-testid`s.
3. **Capture mobile** at signup → pass `mobile` (E.164) in the `/onboarding/register` body.
4. **"Login by anything" resolver**: one input that detects email / 5-digit ID / phone and routes to the right flow.
5. Keep website a pure client — no ID minting, no new identity collection.
**Prerequisite (needs owner action — see §5).**

## 4. CHANGE-SET — App Emergent (DO backend + Expo) — COPY-PASTE ORDER
```
UNIFY IDENTITY TO THE CANONICAL STANDARD v1 (read-only where possible; additive changes only).

BACKEND (DigitalOcean, owns identity):
1. users: add field `mobile` (E.164, unique sparse index). Populate from /onboarding/register body.
2. Add POST /api/auth/resolve-mobile  { mobile } -> { email, uid, customer_id }  (mirror of /auth/resolve-customer-id). Rate-limit + no enumeration leak.
3. /onboarding/register: accept optional `mobile`; store on users; keep 5-digit customer_id allocation via _counters as the SINGLE allocator (do NOT let the website mint IDs).
4. Ensure a Firebase phone-auth user (same person) links to the SAME users doc by uid; if a phone sign-in has no users doc, allocate customer_id once (same self-heal contract the website uses).
5. NETWORKING: migrate networkDB.ts OFF Firestore. All connections/requests/chats/messages -> Mongo (v1/v1b). Retire Firestore `user_connections` after backfill.
6. COMPANY IDENTITY (CANONICAL = entities/GEID ONLY):
   - `entities` (GEID) is the SOLE identity layer. All company identity, resolution, merging, trust, provenance, and relationships live ONLY on entities. Never derive/resolve identity from company_profiles.
   - `company_profiles` = EDITABLE business-profile data ONLY (logo, description, products, certs, contact prefs). Add a `geid` FOREIGN KEY that points to entities. company_profiles MUST NOT be treated as identity or a source of truth for identity, and MUST NOT be used to dedupe/merge companies.
   - `profiles` = personal user profile only.
   - `members_bridge` { uid, customer_id, geid } is the ONLY join tying a user + customer_id to a company entity. Everything references the GEID; nothing owns identity except entities.
   - Do not fork users. Do not create a second company-identity store.

EXPO APP:
7. Add mobile-number (Phone OTP) sign-in using the SAME Firebase project trademate-new, linking to the same uid.
8. Confirm login by email / Google / mobile / Customer-ID all resolve to the same customer_id + data.

DO NOT: create a second Firebase, a second users store, or a second customer_id allocator. DO NOT change existing customer_id values.
```

## 5. ⚠️ THE ONE DECISION THAT NEEDS YOUR REVIEW
**Enable "Phone Authentication" in the Firebase console for project `trademate-new`.** Mobile-number login cannot work until this provider is switched on (it has SMS-quota/billing + reCAPTCHA implications, and only the project owner can enable it). Everything else I can build without you. 
👉 Please enable Firebase → Authentication → Sign-in method → **Phone**, and confirm. Then I ship the website mobile-login and hand the app team the order above.

## 6. Future-ready guarantees
- New VBIE collections (`entities`, `relationships`, `provenance`, `sources`, `members_bridge`, `signals`, `score_history`, `brain_logs`, `geo`, `search_analytics`) are **additive** to the shared Mongo — never touch `users`/auth/`_counters`. You can add entities/fields anytime with no breaking change.
- One identity → one GEID linkage → the same buyer/company appears identically on web + app, in Networking, Buyer Search, and future Supplier Intelligence.
