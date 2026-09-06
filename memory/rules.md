# Project rules — Vametra AI (must be followed by every agent)

## 1. One user = one record
- A user is identified by **one uid → one Customer ID → one GEID**. All of their data must be
  reachable from that single record in the admin **Users** tab: personal details, company details,
  documents, verification history, admin actions, payment status.
- Never create a parallel/website-local user identity, Customer ID or company identity. The
  DigitalOcean backend owns identity; `profiles` is the shared profile store; the website may only
  keep supplemental overlays and workflow metadata (allocation, notes, audit) keyed by the same uid.
- Any new store keyed by a user MUST be added to `WEBSITE_STORES` in `backend/admin_ops.py` so a
  hard delete purges it. If you add a collection and forget this, the user's data survives deletion.

## 2. Test accounts must be visible and deletable
- NEVER seed hidden or shadow user records. Create test users through the **normal signup flow**
  so they appear in the Users tab like any real user.
- Immediately flag them: `POST /api/admin/users/{uid}/test-flag {"is_test": true, "reason": "..."}`
  (or the "Mark as test account" button). They then show a **TEST** badge in the Users tab.
- Record every test account in `/app/memory/test_credentials.md`.
- Delete test accounts when the testing is finished. Emails like `*@example.com`, `dsa-probe*`,
  `dsa-loop*`, `dsa-login*`, `dsa-diagnostic*` are auto-flagged as TEST (see
  `subadmin._looks_like_test`), but that is a safety net, not a substitute for flagging.
- The owner has explicitly complained about invisible test data once (June 2026). Do not repeat it.

## 3. Hard delete is two-tier and total
- Sub-admin: may only **request** a hard delete with a business case (`/users/{uid}/delete-request`).
- Main admin: approves in the Users tab → `/users/{uid}/hard-delete` erases the user from every
  system in one action (identity registry via DO `DELETE /admin_v2/users/{customer_id}`, shared
  `profiles`, Firebase sign-in account, verification submissions, overlay, documents, notes,
  Brain events, subscriptions, caches) after archiving a full copy to `admin_deleted_archive`.

## 4. The Brain owns user communication
- Admin code must never email a user directly. Route it through `brain/profile_brain.py`
  (`observe()` for profile diffs, `announce()` for events) so every change is logged, pushed
  in-app and emailed with the right template.
