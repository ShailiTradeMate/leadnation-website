# Service Request Allocation — Approved Plan (2026-06)

User decisions: statuses = +Partial payment received, +Full payment received (completed retained) · QA sub-admin left active ·
CA email subject "Vametra Service Request · <Service> · Allocated to Vametra CA" · filters never hide any status by default ·
all 6 enhancements accepted. Backlog (remind after marketing + service-request parts): Allocate button + CA/Associate categories.

## Phase 1 — Status + CA assignment (Main Admin)
Backend admin.py
- STATUSES = new, assigned, in-progress, Partial payment received, Full payment received, completed, cancelled (others → 400).
- PUT /admin/service-requests/{id}: status, assignedCaId, assignedCa, assignedCaEmail, internalNote → updatedAt/updatedBy + history[] entry.
- Guards: completed|cancelled ⇒ CA assignment rejected; assigning CA while new ⇒ assigned.
- GET /admin/service-requests/ca-options ⇒ active sub_admins (id,name,email).
- Assigned CA dropdown also offers "External CA…" ⇒ admin types CA name + email manually (assignedCaId = null, assignedCa/assignedCaEmail free text) — PatniCA is not permanent, so any CA can be used.
UI AdminDashboard ServiceRequests
- Row: Date | Service(+entity) | Name | Email/Phone | Status▾ | Assigned CA▾ | CA email (editable) | Email CA
- Completed/Cancelled ⇒ CA controls + Email CA disabled, row visible. Toasts.
- Filters bar: status, CA, service, search; "Unassigned" quick filter. Default shows ALL statuses.

## Phase 2 — Email CA (allocation email)
- POST /admin/service-requests/{id}/email-ca {to, note?} — valid email; blocked if completed/cancelled;
  CC forced = customer + admin@vametra.com; Reply-To = customer.
- Subject "Vametra Service Request · <Service> · Allocated to Vametra CA"; body = service_request template + Allocation block
  (CA name, allocated on/by, note, mailto:customer).
- Success ⇒ emailActivity[] + caNotifiedAt + history; failure ⇒ error for retry.
- UI: preview modal — To (editable, prefilled from CA email), CC = locked chips (customer + admin@vametra.com) PLUS admin can add extra CC addresses (comma separated, validated); subject; rendered preview; note ⇒ Send ▸; badge "CA notified ✓".
- Extra To/CC addresses are saved on the request (assignedCaEmail, extraCc[]) so they are reused next time.

## Phase 3 — Detail drawer (both CMSs)
- Row click ⇒ drawer: request, customer, Vametra account, status+CA, Internal notes, History, Email activity; same controls; copy buttons.

## Phase 4 — Sub-admin CMS "Service Requests" tab
- Permissions: sub_admin += service_requests.view_assigned/update_status/email_customer/notes; main += view_all/allocate.
- GET /staff/service-requests ⇒ main: all; sub-admin: assignedCaId == sid (server-enforced).
- PUT /staff/service-requests/{id} (sub-admin): status (completed is final), internalNote; cannot change CA. history "by: <CA>".
- POST /staff/service-requests/{id}/email-customer: To customer, CC admin + CA, Reply-To CA, same subject, template + CA message.
- UI: tab next to Users; same table minus CA controls ("Assigned to: you"); Email customer popup; "New" badge until opened; open-count badge in header.

## Enhancements (accepted)
1. "New" badge on freshly allocated requests in sub-admin CMS (opened_by tracking).
2. Status-change email to customer (CC admin) on Partial/Full payment received/Completed — per-save toggle "Notify customer".
3. Filters on both tables (status, CA, service, search) — never hide statuses by default.
4. Internal notes (admin + CA only, never emailed).
5. Audit history for every status/assignment/email action.
6. Main-admin "Unassigned" quick filter.

Build order: 1 → 2 → 4 → 3. Testing agent after Phase 2 and after Phase 4; then real email to patnica@vametra.com with user in CC.
