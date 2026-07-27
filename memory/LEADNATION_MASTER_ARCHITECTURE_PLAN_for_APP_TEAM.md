# LeadNation — Master Architecture Plan (for the App Team)
> Shared, binding blueprint so the **Mobile App**, **Website**, and **DigitalOcean identity backend** grow as ONE system. Pairs with `LEADNATION_UNIFIED_IDENTITY_ARCHITECTURE_STANDARD_v1.md`. Status: Identity & Auth = FROZEN; VBIE = design-approved, build pending.

## 1. One-system topology
```
   WEBSITE (React)                 MOBILE APP (Expo)
        │  EXPO_PUBLIC/REACT_APP_BACKEND_URL + /api        │
        ├──────────────── content/Brain ──────────────────┤→ WEBSITE BACKEND (FastAPI, leadnation.app/api) + Brain
        └──────────────── identity ───────────────────────┤→ DIGITALOCEAN BACKEND (leadnation-lfrhs…/api)  ← OWNS identity
                                   │
        ┌──────────────────────────┴──────────────────────────┐
        ▼                          ▼                           ▼
  FIREBASE AUTH (trademate-new)   MONGODB ATLAS (leadnation)   BRAIN (5 modules)
        (shared)                     (shared, 58+ collections)   (shared intelligence)
                                   │
                             VBIE FOUNDATION (additive collections)
        entities(GEID) · relationships · sources · provenance · members_bridge · signals · score_history · brain_logs · geo · search_analytics
```
Rule: **web + app are thin clients.** No feature keeps its own DB/auth/company table.

## 2. Non-negotiable invariants (both teams obey)
1. **ONE Firebase** `trademate-new` (Google + Email + Phone). **ONE Atlas** `leadnation`.
2. **Identity owned by DO backend.** It is the **single** 5-digit `customer_id` allocator (`_counters`, at `/onboarding/register`). Neither website nor app mints IDs.
3. **`entities` (GEID) = the ONLY company-identity layer.** `company_profiles` = editable business data that *references* a GEID (never identity). `profiles` = personal only. `members_bridge{uid, customer_id, geid}` = the only user↔company join.
4. **Login by email / Google / mobile / Customer-ID** all resolve to the same `uid` → same `customer_id` → same data on both platforms.
5. **Mobile numbers stored E.164** with a country dial-code selector at every entry point.
6. **Networking = Mongo only** (retire Firestore `user_connections`); Networking is a view over the `entities` graph (Verified Companies + Verified Members).
7. **Admins (web + app) read all users via one endpoint** `GET /api/admin_v2/users`.
8. **New VBIE collections are additive** — never touch `users`/auth/`_counters`.

## 3. What the WEBSITE has already shipped (done + tested)
- Shared-Firebase client; calls DO `/onboarding/register`; **Customer-ID login**; self-heal for half-registered users.
- **Guarded Phone-OTP login** (flag `REACT_APP_ENABLE_PHONE_LOGIN`, OFF until Blaze).
- **Signup mobile**: optional, country flag + dial-code selector (India default), stored **E.164** as `mobile` + `mobile_number`; note about future phone login.
- **Admin "Users"** tab reading `GET /admin_v2/users` (read-only).

## 4. APP TEAM — required changes to reach parity (COPY-PASTE ORDER)
```
BACKEND (DigitalOcean — additive, do not break users/_counters):
1. users: add `mobile` (E.164, unique sparse index). Accept `mobile`/`mobile_number` in /onboarding/register.
2. Add POST /api/auth/resolve-mobile { mobile } -> { email, uid, customer_id }  (mirror of /auth/resolve-customer-id; rate-limited; no enumeration leak).
3. Keep 5-digit customer_id allocation as the SINGLE allocator. A phone/Google/email sign-in with no users doc -> allocate once (same self-heal contract the website uses).
4. Confirm GET /api/admin_v2/users returns profile+contact (customer_id, full_name, email, mobile, role, country, status) for admin consoles (web + app share it).
5. NETWORKING: migrate networkDB.ts OFF Firestore; all connections/requests/chats/messages -> Mongo (v1/v1b). Retire Firestore user_connections after backfill.
6. COMPANY IDENTITY: entities(GEID) is canonical. company_profiles = editable only + `geid` FK; never used to resolve/merge/identify. Add members_bridge { uid, customer_id, geid }.

MOBILE APP (Expo):
7. Signup/profile: country flag + dial-code selector, store mobile E.164 (same as website).
8. Add mobile-number (Phone OTP) sign-in via the SAME Firebase, linking to the same uid; keep Google + email + Customer-ID.
9. Login by email / Google / mobile / Customer-ID all resolve to the same customer_id + data.
10. Admin view consumes GET /api/admin_v2/users.
11. UI parity with website: same brand tokens, fonts (display + mono), tabs, and feature set; app-only extras = Marketplace, Networking, real-time chat.

DO NOT: create a second Firebase / second users store / second customer_id allocator; do not change existing customer_id values; do not tie company identity to company_profiles.
```

## 5. Feature parity map (web ⟷ app)
| Feature | Website | App | Shared source |
|---------|:--:|:--:|--------------|
| Auth (Google/Email/Mobile/Customer-ID) | ✅ | ✅ (add mobile) | Firebase + DO backend |
| Tools, Brain, Pricing, Academy, News, Expo, Command Center | ✅ | ✅ | website backend + Brain |
| Buyer Search / VBIE | ▶ build | ▶ build | entities(GEID) graph |
| Networking (Verified Companies + Members) | ▶ real page | ✅ (Mongo) | entities + members_bridge |
| Marketplace | ▶ | ✅ | shared backend |
| Real-time chat | — | ✅ (app-only) | Mongo v1b |
| Admin: all users | ✅ | ✅ | GET /admin_v2/users |

## 6. Sequencing (after this, we build VBIE)
1. App team applies §4 (identity parity + Networking→Mongo + company_profiles→GEID).
2. Enable Firebase **Blaze** + set `REACT_APP_ENABLE_PHONE_LOGIN=true` → mobile login live both sides.
3. Then VBIE Phase 6+ (shared `/api/entities`, `/api/networking`, Buyer Intelligence Card) + Importer/Exporter onboarding.

## 7. Definition of "connected & synchronized"
Both apps read/write the SAME Firebase + Atlas; identical login methods → identical `customer_id` + data; identical company identity via GEID; identical admin user visibility; UI/brand parity. When all §2 invariants hold and §4 is done, the systems are one.
