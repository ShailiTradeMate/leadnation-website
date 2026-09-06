"""Admin Phase C — per-user workflow actions (two-tier sign-off).

Main admin has final authority: a sub-admin's approve/reject is stored as a
RECOMMENDATION and only becomes real after main-admin sign-off (the DO identity
write / GEID issuance needs the main admin's Firebase session anyway).

Every mutation is audited in `admin_audit` and handed to the Profile Brain
(brain/profile_brain.py), which owns user communication — the buyer always gets
an email + in-app notification for approve, reject, correction, profile edits,
document changes, subscription grants and record removal.
"""
import uuid
import asyncio
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Optional

import requests
from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from core import db
from subadmin import require_staff, require_perm, has_perm
from brain import profile_brain
import emailer
import storage

router = APIRouter(prefix="/admin")
log = logging.getLogger("admin_ops")

SUBS = db.verification_submissions
OVERLAY = db.profile_overlay
AUDIT = db.admin_audit
NOTES = db.admin_contact_notes
SUBSCRIPTIONS = db.subscriptions
TX = db.payment_transactions
DL = db.downloads

PLAN_DAYS = {"monthly": 30, "quarterly": 90, "annual": 365}
DO_BASE = os.environ.get("AUTH_API_BASE", "").rstrip("/")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean(doc: dict) -> dict:
    return {k: v for k, v in (doc or {}).items() if k != "_id"}


def _pick(*vals):
    for v in vals:
        if v not in (None, "", []):
            return v
    return None


async def _audit(actor: dict, action: str, uid: str, detail: dict = None):
    await AUDIT.insert_one({
        "_id": uuid.uuid4().hex, "action": action, "uid": uid,
        "actor": {"role": actor.get("role"), "name": actor.get("name"),
                  "email": actor.get("email"), "sid": actor.get("sid")},
        "detail": detail or {}, "at": _now()})


def _sub_rank(s: dict):
    st = s.get("status")
    return (1 if st == "needs_review" else 0,
            1 if s.get("assigned_to") else 0,
            str(s.get("created_at") or ""))


async def _user_doc(uid: str) -> dict:
    """User record: website-local row if present, else the cached DO identity registry row."""
    u = await db.users.find_one({"uid": uid})
    if u:
        return u
    c = await db.do_users_cache.find_one({"uid": uid})
    return {k: v for k, v in (c or {}).items() if k not in ("_id", "synced_at")}


async def _resolve(uid: str, actor: dict):
    """Load the user + their most relevant submission, enforcing sub-admin scope."""
    user = await _user_doc(uid)
    subs = await SUBS.find({"uid": uid}).to_list(50)
    if not user and not subs:
        raise HTTPException(404, "User not found.")
    sub = max(subs, key=_sub_rank) if subs else {}
    if not actor.get("is_main"):
        if not sub or sub.get("assigned_to") != actor.get("sid"):
            raise HTTPException(403, "This user is not allocated to you.")
    ov = await OVERLAY.find_one({"uid": uid}) or {}
    return user, sub, ov


def _contact(user: dict, sub: dict, ov: dict) -> dict:
    return {
        "email": _pick(user.get("email"), sub.get("email")),
        "name": _pick(user.get("full_name"), user.get("name"), sub.get("name"), "there"),
    }


# ================= C1 — Review actions (two-tier) =================
class ReviewIn(BaseModel):
    decision: str            # approve | reject | correction
    note: Optional[str] = None
    fields: Optional[list[str]] = None   # for correction requests


@router.post("/users/{uid}/review")
async def review_user(uid: str, body: ReviewIn,
                      actor: dict = Depends(require_staff),
                      authorization: Optional[str] = Header(default=None)):
    decision = (body.decision or "").lower()
    if decision not in ("approve", "reject", "correction"):
        raise HTTPException(400, "decision must be approve, reject or correction.")
    if not has_perm(actor, "users.review_recommend"):
        raise HTTPException(403, "Your role does not allow reviewing users.")
    user, sub, ov = await _resolve(uid, actor)
    if not sub:
        raise HTTPException(400, "This user has not submitted a verification application.")
    c = _contact(user, sub, ov)
    sid = sub["_id"]

    # --- Correction request: not a final decision, either role may send it ---
    if decision == "correction":
        if not (body.note or body.fields):
            raise HTTPException(400, "Add the fields or a note describing the correction needed.")
        await SUBS.update_one({"_id": sid}, {"$set": {
            "review_stage": "correction_requested",
            "correction_requested": {"fields": body.fields or [], "note": body.note,
                                     "by": actor.get("name"), "role": actor.get("role"),
                                     "at": _now()},
            "updated_at": _now()}})
        await _audit(actor, "review.correction", uid, {"fields": body.fields, "note": body.note})
        res = await profile_brain.announce(
            uid, "verify_correction", email=c["email"], name=c["name"], actor=actor,
            summary="Correction requested on your verification application",
            ctx={"fields": body.fields or [], "note": body.note})
        return {"ok": True, "stage": "correction_requested", "email": res["email"]}

    # --- Sub-admin: store a recommendation and ask the main admin to sign off ---
    if not actor.get("is_main"):
        await SUBS.update_one({"_id": sid}, {"$set": {
            "review_stage": "awaiting_signoff",
            "recommendation": {"decision": decision, "note": body.note,
                               "by": actor.get("name"), "sid": actor.get("sid"),
                               "email": actor.get("email"), "at": _now()},
            "updated_at": _now()}})
        await _audit(actor, f"review.recommend.{decision}", uid, {"note": body.note})
        try:
            await emailer.notify_admin("admin_signoff_request", {
                "subadmin": actor.get("name"), "decision": decision, "note": body.note,
                "userName": c["name"], "userEmail": c["email"],
                "company": sub.get("company_name") or "—",
                "customerId": _pick(sub.get("customer_id"), user.get("customer_id")) or "—"})
        except Exception as exc:
            log.warning("sign-off request email failed: %s", exc)
        return {"ok": True, "stage": "awaiting_signoff",
                "message": "Sent to the main admin for final sign-off. The buyer has not been notified yet."}

    # --- Main admin: final decision ---
    return await _finalise(uid, sid, decision, body.note, actor, authorization)


async def _finalise(uid: str, sid: str, decision: str, note: Optional[str],
                    actor: dict, authorization: Optional[str]):
    """Execute the final approve/reject — DO identity write + Brain notification."""
    import verify
    sub = await SUBS.find_one({"_id": sid})
    if not sub:
        raise HTTPException(404, "Submission not found.")
    user = await _user_doc(uid)
    ov = await OVERLAY.find_one({"uid": uid}) or {}
    c = _contact(user, sub, ov)
    profile = await verify._profile(uid, authorization)
    reviewer = actor.get("name") or actor.get("email") or "Main admin"

    if decision == "approve":
        link = verify._do_link_buyer(uid, profile.get("customer_id"), profile,
                                     sub.get("entity_type") or "prospect", authorization)
        verify._do_put_profile(uid, {"verification_status": "verified"}, authorization)
        await SUBS.update_one({"_id": sid}, {"$set": {
            "status": "verified", "geid": link.get("geid"), "linked": link.get("linked"),
            "reviewer": reviewer, "review_note": note, "review_stage": "completed",
            "decided_at": _now(), "updated_at": _now()},
            "$unset": {"recommendation": ""}})
        await _audit(actor, "review.approve", uid, {"note": note, "geid": link.get("geid")})
        res = await profile_brain.announce(
            uid, "verify_approved", email=c["email"], name=c["name"], actor=actor,
            summary="Your Verified Buyer application was approved",
            ctx={"customerId": _pick(sub.get("customer_id"), user.get("customer_id")) or "—",
                 "geid": link.get("geid") or sub.get("geid") or "—",
                 "reviewer": reviewer, "note": note})
        await profile_brain.sync_profile_memory(uid, {**profile, "verification_status": "verified",
                                                     "geid": link.get("geid")})
        return {"ok": True, "status": "verified", "geid": link.get("geid"), "email": res["email"]}

    verify._do_put_profile(uid, {"verification_status": "rejected"}, authorization)
    await SUBS.update_one({"_id": sid}, {"$set": {
        "status": "rejected", "reviewer": reviewer, "review_note": note,
        "review_stage": "completed", "decided_at": _now(), "updated_at": _now()},
        "$unset": {"recommendation": ""}})
    await _audit(actor, "review.reject", uid, {"note": note})
    res = await profile_brain.announce(
        uid, "verify_rejected", email=c["email"], name=c["name"], actor=actor,
        summary="Your Verified Buyer application could not be approved",
        ctx={"note": note, "reviewer": reviewer})
    return {"ok": True, "status": "rejected", "email": res["email"]}


# ---- Sign-off queue (main admin) ----
@router.get("/signoff")
async def signoff_queue(actor: dict = Depends(require_perm("signoff.view"))):
    rows = []
    async for s in SUBS.find({"review_stage": "awaiting_signoff"}):
        u = await _user_doc(s.get("uid"))
        rec = s.get("recommendation") or {}
        rows.append({
            "submission_id": s["_id"], "uid": s.get("uid"),
            "customer_id": _pick(s.get("customer_id"), u.get("customer_id")),
            "name": _pick(s.get("name"), u.get("full_name"), u.get("name")),
            "email": _pick(s.get("email"), u.get("email")),
            "company_name": s.get("company_name"),
            "status": s.get("status"),
            "recommended": rec.get("decision"), "reviewer_note": rec.get("note"),
            "recommended_by": rec.get("by"), "recommended_at": rec.get("at"),
        })
    rows.sort(key=lambda r: str(r.get("recommended_at") or ""))
    return {"queue": rows, "count": len(rows)}


class SignoffIn(BaseModel):
    submission_id: str
    action: str                    # confirm | decline | override
    decision: Optional[str] = None  # required for override
    note: Optional[str] = None


@router.post("/users/{uid}/signoff")
async def signoff(uid: str, body: SignoffIn,
                  actor: dict = Depends(require_perm("signoff.view")),
                  authorization: Optional[str] = Header(default=None)):
    sub = await SUBS.find_one({"_id": body.submission_id, "uid": uid})
    if not sub:
        raise HTTPException(404, "Submission not found.")
    rec = sub.get("recommendation") or {}
    action = (body.action or "").lower()

    if action == "decline":
        await SUBS.update_one({"_id": sub["_id"]}, {"$set": {
            "review_stage": "returned", "signoff_note": body.note, "updated_at": _now()},
            "$unset": {"recommendation": ""}})
        await _audit(actor, "signoff.decline", uid, {"note": body.note, "was": rec.get("decision")})
        if rec.get("email"):
            try:
                await emailer.send("signoff_declined", rec["email"], {
                    "name": rec.get("by") or "there", "decision": rec.get("decision"),
                    "userName": sub.get("name") or sub.get("email") or "the buyer",
                    "note": body.note})
            except Exception as exc:
                log.warning("signoff decline email failed: %s", exc)
        return {"ok": True, "stage": "returned",
                "message": "Recommendation returned to the sub-admin. The buyer was not notified."}

    decision = (body.decision or rec.get("decision") or "").lower()
    if action == "override" and decision not in ("approve", "reject"):
        raise HTTPException(400, "Provide the final decision to override with.")
    if decision not in ("approve", "reject"):
        raise HTTPException(400, "Nothing to sign off on.")
    out = await _finalise(uid, sub["_id"], decision, body.note or rec.get("note"), actor, authorization)
    out["signed_off"] = decision
    return out


# ================= C2 — Edit profile / documents / contact =================
class ProfileEdit(BaseModel):
    patch: dict


@router.patch("/users/{uid}/profile")
async def edit_profile(uid: str, body: ProfileEdit,
                       actor: dict = Depends(require_perm("users.edit")),
                       authorization: Optional[str] = Header(default=None)):
    """Admin/sub-admin correction of a buyer profile — same write path the user's own
    form uses (DO canonical + website overlay), then Brain informs the buyer."""
    import verify
    patch = {k: v for k, v in (body.patch or {}).items() if v is not None}
    if not patch:
        raise HTTPException(400, "Nothing to update.")
    user, sub, ov = await _resolve(uid, actor)
    c = _contact(user, sub, ov)
    before = await verify._profile(uid, authorization)

    verify._do_put_profile(uid, patch, authorization)
    await verify._save_overlay(uid, patch)

    # keep the admin table + the review record consistent with the correction
    flat = {k: patch[k] for k in ("name", "mobile", "country", "state", "city", "role")
            if patch.get(k) is not None}
    if flat:
        u_set = dict(flat)
        if flat.get("mobile"):
            u_set["mobile_number"] = flat["mobile"]
        await db.users.update_one({"uid": uid}, {"$set": u_set})
    cd = patch.get("company_details") or {}
    sub_set = {k: v for k, v in {**flat,
                                 "company_name": cd.get("company_name"),
                                 "company_email": cd.get("company_email"),
                                 "company_phone": cd.get("company_phone")}.items() if v}
    if sub and sub_set:
        await SUBS.update_one({"_id": sub["_id"]}, {"$set": {**sub_set, "updated_at": _now()}})

    after = await verify._profile(uid, authorization)
    await _audit(actor, "profile.edit", uid, {"patch": patch})
    res = await profile_brain.observe(uid, before, after, actor=actor, source="admin_edit",
                                      email=c["email"], name=c["name"])
    return {"ok": True, "changes": res["changes"], "email": res["email"], "profile": after}


@router.post("/users/{uid}/documents")
async def upload_document(uid: str, file: UploadFile = File(...), kind: str = Form("document"),
                          label: str = Form(""), note: str = Form(""),
                          actor: dict = Depends(require_perm("users.documents"))):
    """Upload/replace a verification document on the buyer's behalf."""
    user, sub, ov = await _resolve(uid, actor)
    if not sub:
        raise HTTPException(400, "This user has no verification application to attach a document to.")
    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(413, "File too large (max 10 MB).")
    ext = (file.filename.rsplit(".", 1)[-1].lower() if "." in (file.filename or "") else "jpg")
    ctype = file.content_type or storage.MIME_TYPES.get(ext, "application/octet-stream")
    path = f"{storage.APP_NAME}/verify/{uid}/admin/{uuid.uuid4().hex}.{ext}"
    try:
        result = storage.get_provider().put(path, data, ctype)
    except Exception as exc:
        log.error("admin document upload failed: %s", exc)
        raise HTTPException(502, "Upload failed. Please retry.")
    fid = uuid.uuid4().hex
    await db.uploaded_files.insert_one({
        "_id": fid, "id": fid, "storage_path": result.get("path", path),
        "original_filename": file.filename, "content_type": ctype,
        "size": result.get("size", len(data)), "owner": uid, "kind": f"verify:{kind}",
        "uploaded_by_admin": actor.get("email") or actor.get("name"),
        "provider": storage.get_provider().name, "is_deleted": False, "created_at": _now()})

    field = "selfie_file_id" if kind == "selfie" else "document_file_id"
    await SUBS.update_one({"_id": sub["_id"]}, {
        "$set": {field: fid, "updated_at": _now()},
        "$push": {"admin_documents": {"file_id": fid, "kind": kind,
                                      "label": label or file.filename,
                                      "by": actor.get("name"), "at": _now()}}})
    c = _contact(user, sub, ov)
    await _audit(actor, "document.upload", uid, {"file_id": fid, "kind": kind, "note": note})
    res = await profile_brain.announce(
        uid, "document_updated", email=c["email"], name=c["name"], actor=actor,
        summary=f"{label or kind.title()} document updated on your account",
        ctx={"docLabel": label or kind.title(), "filename": file.filename, "note": note})
    return {"ok": True, "file_id": fid, "url": f"/api/storage/file/{fid}", "email": res["email"]}


class NoteIn(BaseModel):
    channel: str = "call"       # call | email | whatsapp | note
    note: str


@router.get("/users/{uid}/notes")
async def list_notes(uid: str, actor: dict = Depends(require_perm("users.contact"))):
    await _resolve(uid, actor)
    rows = await NOTES.find({"uid": uid}).sort("at", -1).to_list(100)
    return {"notes": [_clean(r) for r in rows]}


@router.post("/users/{uid}/notes")
async def add_note(uid: str, body: NoteIn, actor: dict = Depends(require_perm("users.contact"))):
    await _resolve(uid, actor)
    doc = {"_id": uuid.uuid4().hex, "uid": uid, "channel": body.channel, "note": body.note,
           "by": actor.get("name"), "role": actor.get("role"), "at": _now()}
    await NOTES.insert_one(dict(doc))
    await _audit(actor, "contact.note", uid, {"channel": body.channel})
    return {"ok": True, "note": _clean(doc)}


# ================= C3 — Payments & subscriptions =================
@router.get("/users/{uid}/payments")
async def user_payments(uid: str, actor: dict = Depends(require_perm("payments.view"))):
    user, sub, ov = await _resolve(uid, actor)
    keys = [k for k in {uid, user.get("customer_id"), sub.get("customer_id")} if k]
    subscription = await SUBSCRIPTIONS.find_one({"owner": {"$in": keys}}) or {}
    txs = await TX.find({"$or": [{"owner": {"$in": keys}}, {"uid": uid}]}) \
                  .sort("createdAt", -1).to_list(100)
    dls = await DL.find({"owner": {"$in": keys}}).sort("at", -1).to_list(100)
    return {
        "subscription": {
            "status": subscription.get("status"), "plan": subscription.get("plan"),
            "until": subscription.get("until"), "source": subscription.get("source"),
            "granted_by": subscription.get("granted_by"), "reason": subscription.get("reason"),
        },
        "transactions": [{
            "id": t.get("_id"), "txnId": t.get("txnId") or t.get("_id"),
            "gateway": t.get("gateway"), "status": t.get("status"), "kind": t.get("kind"),
            "plan": t.get("planLabel") or t.get("kind"), "amount": t.get("amount"),
            "currency": t.get("currency"), "invoice": t.get("invoice"),
            "createdAt": t.get("createdAt"), "paidAt": t.get("paidAt"),
        } for t in txs],
        "invoices": [{"number": d.get("invoiceId"), "date": d.get("at"),
                      "amount": d.get("amount"), "currency": d.get("currency"),
                      "item": d.get("projectTitle") or d.get("projectId")}
                     for d in dls if d.get("paid")],
        "totals": {"downloads": len(dls),
                   "spend": round(sum(d.get("amount") or 0 for d in dls if d.get("paid")), 2)},
        "can_grant": has_perm(actor, "payments.grant"),
    }


class GrantIn(BaseModel):
    action: str = "grant"           # grant | revoke
    plan: str = "monthly"           # monthly | quarterly | annual
    days: Optional[int] = None
    note: Optional[str] = None


@router.post("/users/{uid}/subscription")
async def manage_subscription(uid: str, body: GrantIn,
                              actor: dict = Depends(require_perm("payments.grant"))):
    user, sub, ov = await _resolve(uid, actor)
    c = _contact(user, sub, ov)
    if (body.action or "").lower() == "revoke":
        await SUBSCRIPTIONS.update_one({"owner": uid}, {"$set": {
            "status": "cancelled", "revoked_by": actor.get("name"),
            "reason": body.note, "updatedAt": _now()}})
        await _audit(actor, "subscription.revoke", uid, {"note": body.note})
        res = await profile_brain.announce(
            uid, "subscription_revoked", email=c["email"], name=c["name"], actor=actor,
            summary="A subscription on your account was removed",
            ctx={"plan": body.plan, "note": body.note})
        return {"ok": True, "status": "cancelled", "email": res["email"]}

    days = int(body.days or PLAN_DAYS.get(body.plan, 30))
    until = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
    await SUBSCRIPTIONS.update_one({"owner": uid}, {"$set": {
        "owner": uid, "status": "active", "plan": body.plan, "until": until,
        "source": "admin_grant", "granted_by": actor.get("name"),
        "reason": body.note, "gateway": "admin", "updatedAt": _now()}}, upsert=True)
    await _audit(actor, "subscription.grant", uid,
                 {"plan": body.plan, "days": days, "note": body.note})
    res = await profile_brain.announce(
        uid, "subscription_granted", email=c["email"], name=c["name"], actor=actor,
        summary=f"{body.plan.title()} subscription activated on your account",
        ctx={"plan": body.plan, "until": until, "note": body.note})
    return {"ok": True, "status": "active", "plan": body.plan, "until": until,
            "email": res["email"]}


# ================= C1 — Hard delete (two-tier) =================
DELETE_REQUESTS = db.delete_requests

# Every website-local store that holds anything about a user.
WEBSITE_STORES = [
    ("verification_submissions", "uid"), ("profile_overlay", "uid"),
    ("admin_contact_notes", "uid"), ("profile_changes", "uid"),
    ("notifications", "uid"), ("user_context", "user_id"),
    ("do_users_cache", "uid"), ("delete_requests", "uid"),
    ("test_accounts", "uid"),
]


class DeleteRequestIn(BaseModel):
    business_case: str


@router.post("/users/{uid}/delete-request")
async def request_hard_delete(uid: str, body: DeleteRequestIn,
                              actor: dict = Depends(require_perm("users.review_recommend"))):
    """A sub-admin cannot delete — they raise a hard-delete request with a business
    case for the main admin to approve."""
    if len((body.business_case or "").strip()) < 10:
        raise HTTPException(400, "Describe the business case for deleting this user (min 10 characters).")
    user, sub, ov = await _resolve(uid, actor)
    c = _contact(user, sub, ov)
    doc = {"_id": uuid.uuid4().hex, "uid": uid, "status": "pending",
           "business_case": body.business_case,
           "user_name": c["name"], "user_email": c["email"],
           "customer_id": _pick(user.get("customer_id"), sub.get("customer_id")),
           "requested_by": actor.get("name"), "requested_by_email": actor.get("email"),
           "requested_at": _now()}
    await DELETE_REQUESTS.insert_one(dict(doc))
    await _audit(actor, "delete.request", uid, {"business_case": body.business_case})
    try:
        await emailer.notify_admin("admin_delete_request", {
            "subadmin": actor.get("name"), "userName": c["name"], "userEmail": c["email"],
            "customerId": doc["customer_id"] or "—", "note": body.business_case})
    except Exception as exc:
        log.warning("delete request email failed: %s", exc)
    return {"ok": True, "stage": "awaiting_admin_approval", "request_id": doc["_id"],
            "message": "Hard-delete request sent to the main admin for approval."}


@router.get("/delete-requests")
async def delete_requests(actor: dict = Depends(require_perm("users.delete"))):
    rows = await DELETE_REQUESTS.find({"status": "pending"}).sort("requested_at", 1).to_list(200)
    return {"queue": [{**_clean(r), "id": r["_id"]} for r in rows], "count": len(rows)}


@router.post("/delete-requests/{request_id}/decline")
async def decline_delete_request(request_id: str, note: Optional[str] = None,
                                 actor: dict = Depends(require_perm("users.delete"))):
    res = await DELETE_REQUESTS.update_one({"_id": request_id, "status": "pending"}, {"$set": {
        "status": "declined", "declined_by": actor.get("name"),
        "decline_note": note, "declined_at": _now()}})
    if res.matched_count == 0:
        raise HTTPException(404, "Request not found.")
    return {"ok": True, "status": "declined"}


class DeleteIn(BaseModel):
    confirm: str
    note: Optional[str] = None
    request_id: Optional[str] = None
    force: bool = False


@router.post("/users/{uid}/hard-delete")
async def hard_delete(uid: str, body: DeleteIn,
                      actor: dict = Depends(require_perm("users.delete")),
                      authorization: Optional[str] = Header(default=None)):
    """MAIN ADMIN ONLY — erase a user from EVERY system in one action: identity
    registry (DO), sign-in account (Firebase), shared profile, verification records,
    documents, notes, activity and subscriptions. A full copy is archived first so
    the deletion itself stays auditable.

    Identity is removed BEFORE the local purge: if the identity backend cannot be
    reached we abort with nothing deleted, so a user can never end up able to sign
    in with an emptied account. `force: true` overrides that guard."""
    if (body.confirm or "").strip().upper() != "DELETE":
        raise HTTPException(400, "Type DELETE to confirm this permanent action.")
    user = await _user_doc(uid)
    subs = await SUBS.find({"uid": uid}).to_list(50)
    ov = await OVERLAY.find_one({"uid": uid}) or {}
    shared = await db.profiles.find_one({"uid": uid}) or {}
    if not user and not subs and not shared:
        raise HTTPException(404, "User not found.")
    c = _contact(user, subs[0] if subs else {}, ov)
    cid = _pick(user.get("customer_id"), shared.get("customer_id"),
                (subs[0] if subs else {}).get("customer_id"))
    files = await db.uploaded_files.find({"owner": uid}).to_list(200)

    # 1. archive everything first
    await db.admin_deleted_archive.insert_one({
        "_id": uuid.uuid4().hex, "uid": uid, "customer_id": cid,
        "user": _clean(user), "shared_profile": _clean(shared),
        "submissions": [_clean(s) for s in subs], "overlay": _clean(ov),
        "files": [_clean(f) for f in files],
        "notes": [_clean(n) for n in await NOTES.find({"uid": uid}).to_list(200)],
        "brain_events": await profile_brain.feed(uid, 200),
        "audit": [_clean(a) for a in await AUDIT.find({"uid": uid}).to_list(200)],
        "deleted_by": actor.get("name"), "role": actor.get("role"),
        "note": body.note, "request_id": body.request_id, "at": _now()})

    # 2. identity FIRST — abort the whole delete if the registry cannot be erased
    identity = {"do_registry": "skipped", "firebase": "skipped"}
    if cid and DO_BASE and authorization:
        try:
            r = await asyncio.to_thread(requests.delete, f"{DO_BASE}/admin_v2/users/{cid}",
                                        headers={"Authorization": authorization}, timeout=30)
            identity["do_registry"] = "deleted" if r.ok else f"failed ({r.status_code})"
        except Exception as exc:
            identity["do_registry"] = f"failed ({type(exc).__name__})"
    if identity["do_registry"].startswith("failed") and not body.force:
        raise HTTPException(502, "The identity backend could not delete this user "
                                 f"({identity['do_registry']}). Nothing was deleted — retry, or "
                                 "use force to remove our records only.")
    try:
        import firebase_auth
        firebase_auth.init_firebase()
        from firebase_admin import auth as fb_auth
        await asyncio.to_thread(fb_auth.delete_user, uid)
        identity["firebase"] = "deleted"
    except Exception as exc:
        identity["firebase"] = f"failed ({type(exc).__name__})"

    # 3. purge every store
    purged = {}
    for coll, key in WEBSITE_STORES:
        try:
            purged[coll] = (await db[coll].delete_many({key: uid})).deleted_count
        except Exception as exc:
            log.warning("purge %s failed: %s", coll, exc)
    purged["uploaded_files"] = (await db.uploaded_files.delete_many({"owner": uid})).deleted_count
    purged["profiles"] = (await db.profiles.delete_many({"uid": uid})).deleted_count
    purged["users"] = (await db.users.delete_many({"uid": uid})).deleted_count
    subs_purged = 0
    for q in [{"owner": uid}, {"uid": uid}] + ([{"owner": cid}] if cid else []):
        try:
            subs_purged += (await SUBSCRIPTIONS.delete_many(q)).deleted_count
        except Exception:
            pass
    purged["subscriptions"] = subs_purged

    # 4. tell the user (we kept their address in memory for exactly this)
    email_res = await profile_brain.announce(
        uid, "account_removed", email=c["email"], name=c["name"], actor=actor,
        summary="Your Vametra AI account and records were permanently removed",
        ctx={"note": body.note})
    await db.profile_changes.delete_many({"uid": uid})
    await db.notifications.delete_many({"uid": uid})

    if body.request_id:
        await DELETE_REQUESTS.update_one({"_id": body.request_id}, {"$set": {
            "status": "approved", "approved_by": actor.get("name"), "approved_at": _now()}})
    await _audit(actor, "user.hard_delete", uid,
                 {"note": body.note, "customer_id": cid, "purged": purged, "identity": identity})
    warnings = [f"{k.replace('_', ' ')}: {v}" for k, v in identity.items() if v != "deleted"]
    return {"ok": True, "archived": True, "purged": purged, "identity": identity,
            "warnings": warnings, "email": email_res["email"]}


# ================= Test-account flagging + one-click export =================
TEST_ACCOUNTS = db.test_accounts


class TestFlagIn(BaseModel):
    is_test: bool = True
    reason: Optional[str] = None


@router.post("/users/{uid}/test-flag")
async def flag_test_account(uid: str, body: TestFlagIn,
                            actor: dict = Depends(require_perm("users.edit"))):
    """Mark/unmark a user as a TEST account so it is obvious in the User Section and
    can be cleaned up. Any account created for testing MUST carry this flag."""
    await _resolve(uid, actor)
    if body.is_test:
        await TEST_ACCOUNTS.update_one({"uid": uid}, {"$set": {
            "uid": uid, "reason": body.reason or "Created for testing",
            "flagged_by": actor.get("name"), "at": _now()}}, upsert=True)
    else:
        await TEST_ACCOUNTS.delete_many({"uid": uid})
    await _audit(actor, "user.test_flag", uid, {"is_test": body.is_test, "reason": body.reason})
    return {"ok": True, "is_test_account": body.is_test}


@router.get("/users/{uid}/export")
async def export_user(uid: str, actor: dict = Depends(require_staff),
                      authorization: Optional[str] = Header(default=None)):
    """One-click complete record for a single user — every detail we hold, in one file."""
    import verify
    user, sub, ov = await _resolve(uid, actor)
    shared = await db.profiles.find_one({"uid": uid}) or {}
    do_profile = {}
    try:
        do_profile = await asyncio.to_thread(verify._do_get_profile, uid, authorization) or {}
    except Exception:
        pass
    files = await db.uploaded_files.find({"owner": uid}).to_list(200)
    subscription = await SUBSCRIPTIONS.find_one({"$or": [{"owner": uid}, {"uid": uid}]}) or {}
    return {
        "exported_at": _now(), "exported_by": actor.get("name"),
        "customer_id": _pick(user.get("customer_id"), shared.get("customer_id")),
        "uid": uid,
        "identity_registry": _clean(user),
        "shared_profile": _clean(verify._merge_supplement(
            {k: v for k, v in shared.items() if k != "_id"}, do_profile)),
        "website_overlay": _clean(ov),
        "verification_submissions": [_clean(s) for s in
                                     await SUBS.find({"uid": uid}).to_list(50)],
        "documents": [{"file_id": f.get("_id"), "filename": f.get("original_filename"),
                       "kind": f.get("kind"), "size": f.get("size"),
                       "uploaded_at": f.get("created_at"),
                       "url": f"/api/storage/file/{f.get('_id')}"} for f in files],
        "subscription": _clean(subscription),
        "payments": [_clean(t) for t in
                     await TX.find({"$or": [{"owner": uid}, {"uid": uid}]}).to_list(200)],
        "contact_notes": [_clean(n) for n in await NOTES.find({"uid": uid}).to_list(200)],
        "brain_events": await profile_brain.feed(uid, 200),
        "admin_audit": [_clean(a) for a in await AUDIT.find({"uid": uid}).to_list(200)],
        "is_test_account": bool(await TEST_ACCOUNTS.find_one({"uid": uid})),
    }


# ================= Activity trail =================
@router.get("/users/{uid}/profile")
async def user_profile(uid: str, actor: dict = Depends(require_staff),
                       authorization: Optional[str] = Header(default=None)):
    """Everything we know about one user: canonical DO shared profile + website overlay
    + identity-registry row (fetched on demand when a row is expanded)."""
    import verify
    user, sub, ov = await _resolve(uid, actor)
    profile = {}
    try:
        profile = await asyncio.to_thread(verify._do_get_profile, uid, authorization) or {}
    except Exception as exc:
        log.warning("DO profile fetch failed for %s: %s", uid, exc)
    shared = await db.profiles.find_one({"uid": uid}) or {}
    base = verify._merge_supplement({k: v for k, v in ov.items() if k not in ("_id", "uid")},
                                    {k: v for k, v in shared.items() if k != "_id"})
    merged = verify._merge_supplement(base, profile)
    return {"profile": _clean(merged), "identity": _clean(user),
            "submission": _clean(sub), "do_reachable": bool(profile)}


@router.get("/users/{uid}/activity")
async def user_activity(uid: str, actor: dict = Depends(require_staff)):
    await _resolve(uid, actor)
    audit = await AUDIT.find({"uid": uid}).sort("at", -1).limit(50).to_list(50)
    return {"brain_events": await profile_brain.feed(uid, 30),
            "audit": [_clean(a) for a in audit]}
