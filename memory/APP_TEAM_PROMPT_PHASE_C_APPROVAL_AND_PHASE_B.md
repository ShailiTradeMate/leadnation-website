# LeadNation — App Team Directive (2026-06) — Phase C APPROVED · Minimal Phase B · Guarded Phase D · STOP boundary

> Source of truth: `/app/memory/LEADNATION_UNIFIED_IDENTITY_ARCHITECTURE_STANDARD_v1.md`.
> This directive was issued after an independent line-by-line review of `shaili-trademate-app-main (2).zip` (`backend/server.py`).
> All decisions below are PERMANENT for the current structure and future-ready. Do not re-litigate.

---

## ✅ DECISION 1 — Phase C (GEID Entity Model): APPROVED

Reviewed and confirmed correct against the frozen standard:
- `entities` is the sole identity layer; `_id == geid`, immutable; GEID `LN-<type>-<ULID>` (Crockford base32). ✔
- `company_profiles` upsert writes **editable fields only** with a `geid` FK; never touches `legal_name`/identity. ✔
- `members_bridge` unique on `uid` and `customer_id`, non-unique on `geid`. ✔
- `/entities/{geid}` + `/members/company` follow merge pointers (hop-capped); merge moves bridges + profiles to survivor. ✔
- Startup indexes exactly as specified; `users`/`_counters`/auth untouched. ✔
- Phase A polish confirmed: canonical `mobile` in admin search `$or`; `uniq_mobile` sparse-unique index at startup. ✔

### Required BEFORE starting Phase B — 2 small permanent hardenings (NOT a rework, ~30 min)

**1C. Control who can mint canonical GEIDs.**
Free minting of canonical entities by any authenticated user defeats the purpose of GEID (it causes duplicate-identity pollution — the exact thing GEID prevents). Permanent rule:
- `POST /entities` for `entity_type in {buyer, supplier, manufacturer, agency}` (the canonical trade graph) → **admin/service-role only** (`require_admin`).
- `POST /entities` for `entity_type in {member_company, prospect}` (a user registering their OWN company during onboarding) → authenticated user allowed, but **one self-minted `member_company` per user** (guard: if the caller already has a `members_bridge`, reject with 409 and return the existing GEID instead of minting a duplicate).
- Keep `POST /entities/{geid}/merge` admin-only (already correct).
- Future (VBIE, not now): add `POST /entities/claim` (claim-this-company) that binds a user to an EXISTING GEID rather than minting.

**2C. Merge idempotency + cycle guard.** In `POST /entities/{geid}/merge`:
- Reject if `src.merged_into` is already set (already merged) → 409.
- If `into` is itself merged, follow to its survivor first and merge into the survivor.
- Reject if the resolved survivor `== geid` (would create a cycle) → 400.

No other Phase C changes. Ship these two, then proceed.

---

## ✅ DECISION 2 — Phase B (Networking → Mongo canonical): MINIMAL, future-ready

**Key finding: the Mongo networking/chat BACKEND ALREADY EXISTS. Do NOT build a new one.**
`backend/server.py` already serves (via `v1b_router`, prefix `/api/v1b` or as mounted):
`/connections/request`, `/connections/requests`, `/connections/{id}/respond`, `/connections/{user_id}`,
`/chats`, `/chats/{user_id}`, `/chats/{chat_id}/participants`, `/chats/{chat_id}/messages` (POST+GET),
`/match/network` — backed by Mongo `v1_connections` / `user_connections`.

The ONLY divergence is the **mobile frontend** `frontend/services/networkDB.ts`, which still uses Firestore
(`onSnapshot` real-time listeners on `PROFILES`, `REQUESTS`, `CONNECTIONS = user_connections`).

### Scope (do exactly this, nothing more)
1. **Repoint `networkDB.ts` from Firestore → the existing Mongo `v1b` endpoints.** Keep the same exported
   function signatures so screens don't change.
2. **Replace `onSnapshot` real-time listeners with polling** behind the same `subscribe*`-shaped wrappers
   (React Query `refetchInterval`): ~15–20s for connection/request lists, ~3–5s while a chat screen is
   focused (stop polling on blur). Call sites stay identical.
3. **Networking is a VIEW over identity, not a separate directory.** Personal data → `profiles` (uid-keyed).
   Company/business data → `company_profiles` (geid FK). Connections/requests reference `uid`/`customer_id`
   (and `geid` where a company is involved). No parallel user store.
4. **Firestore cutover:** count docs in `PROFILES` / `REQUESTS` / `user_connections`. If >0 → one-time
   backfill into Mongo, verify counts match, then remove all Firestore reads/writes and delete the listener
   code. If 0 → clean cut immediately. Firestore must NOT remain canonical for networking.

### DEFER (do NOT build now) — but keep it future-ready
- **Do NOT build WebSocket or Atlas change-streams.** Polling is sufficient for launch.
- Keep messages realtime-ready so it's additive later (no migration): ensure the `messages` doc has
  `{ _id, chat_id, sender_uid, body, created_at, seq }` with an index on `(chat_id, created_at)` and a
  monotonic `seq`, and keep send/fetch centralized in ONE service module. Change-streams/WebSocket can then
  be added later as a drop-in transport with zero call-site changes.

---

## ✅ DECISION 3 — Phase D (mobile phone login): GUARDED UI ONLY (mirror the website)

- Signup: add an OPTIONAL country-code selector + phone field; **normalize to E.164 before** calling
  `/onboarding/register` (backend also normalizes — belt & suspenders). Show the note:
  "Your mobile number will be used for faster login and account recovery when Phone Login becomes available."
- Login: add a "Mobile number" tab **gated behind `EXPO_PUBLIC_ENABLE_PHONE_LOGIN` (default false)**. With the
  flag OFF it shows "launching soon" and never calls any SMS/OTP SDK.
- **No live SMS/OTP wiring** until Firebase Blaze is enabled by the owner. Do not test with personal numbers.

---

## 🛑 DECISION 4 — STOP boundary (explicit)

After: **A (done) + C (approved + the 2 hardenings) + minimal B + guarded D** → the app team **STOPS all
auth/identity/architecture/networking work.** Do not start new features, new realtime infra, or speculative
migrations. Report completion with your own testing-agent run (runtime, not just code review) in the app env.

The next joint effort is **VBIE implementation**, which begins only after our shared Research → Design →
Review → Approval gate. First VBIE slice (to be planned jointly, not started now): shared `/api/entities`
consumption, the approved source registry, the Buyer Intelligence Card (with source evidence), and the
claim-this-company flow.

---

## Guardrails (unchanged, restate for the record)
- One Firebase (`trademate-new`), one Atlas DB (`leadnation`). DO backend is the ONLY identity owner and the
  ONLY 5-digit `customer_id` allocator (`_counters`, `00001` reserved). Never mint IDs elsewhere.
- New collections must be ADDITIVE. Never modify/delete `users`, `_counters`, or auth records.
- `entities`(GEID) = identity ONLY. `company_profiles` = editable business data ONLY. `profiles` = personal
  ONLY. `members_bridge{uid,customer_id,geid}` = the only user↔company join.
- All mobile numbers stored E.164.
- Both web + app admins must see every user's profile/contact via `GET /api/admin_v2/users` (admin-gated; never public).
