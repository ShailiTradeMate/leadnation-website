"""Durable two-tier approval inbox. Each item is independently claimed and applied."""
import uuid
import logging
from datetime import datetime, timezone
from typing import Literal, Optional
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from core import db
from subadmin import require_staff, require_main_admin

router = APIRouter(prefix="/admin/approvals")
REQUESTS = db.admin_approval_requests
log = logging.getLogger(__name__)


def now():
    return datetime.now(timezone.utc).isoformat()


async def enqueue(uid, kind, payload, actor, note, *, key=None):
    from admin_ops import _resolve, _contact, _audit
    u, s, ov = await _resolve(uid, actor)
    c = _contact(u, s, ov)
    # One live request of each kind per user; never silently replace reviewed data.
    key = key or f"{uid}:{kind}"
    existing = await REQUESTS.find_one({"pending_key": key}, {"_id": 0})
    if existing:
        raise HTTPException(409, "A request of this type is already pending for this user.")
    await REQUESTS.create_index("pending_key", unique=True, sparse=True)
    rid = uuid.uuid4().hex
    doc = {"id": rid, "uid": uid, "kind": kind, "payload": payload,
           "note": (note or "").strip(), "status": "pending", "pending_key": key,
           "name": c["name"], "email": c["email"],
           "customer_id": u.get("customer_id") or s.get("customer_id"),
           "requested_by": actor.get("name"), "requested_by_sid": actor.get("sid"),
           "requested_by_email": actor.get("email"), "requested_at": now()}
    from pymongo.errors import DuplicateKeyError
    try:
        await REQUESTS.insert_one({"_id": rid, **doc})
    except DuplicateKeyError:
        raise HTTPException(409, "A request of this type is already pending.")
    await _audit(actor, "approval.request", uid, {"request_id": rid, "kind": kind})
    await db.notifications.insert_one({"audience": "admin", "title": "New approval request",
        "message": f"{actor.get('name')} · {kind.replace('_', ' ')} · {c['name']}", "created_at": now()})
    return {"ok": True, "stage": "awaiting_signoff", "request_id": rid,
            "message": "Request sent to the main admin. No user changes have been applied."}


async def import_legacy():
    """Existing outstanding review/delete requests remain actionable in the same inbox."""
    async for s in db.verification_submissions.find({"review_stage": "awaiting_signoff"}, {"_id": 0}):
        rec = s.get("recommendation") or {}
        if not s.get("id") or rec.get("decision") not in ("approve", "reject"):
            continue
        rid = f"review:{s['id']}:{rec.get('at', '')}"
        await REQUESTS.update_one({"_id": rid}, {"$setOnInsert": {
            "id": rid, "uid": s["uid"], "kind": "review", "status": "pending",
            "payload": {"submission_id": s["id"], "decision": rec["decision"]},
            "note": rec.get("note"), "name": s.get("name"), "email": s.get("email"),
            "requested_by": rec.get("by"), "requested_by_sid": rec.get("sid"),
            "requested_at": rec.get("at"), "customer_id": s.get("customer_id")}}, upsert=True)
    async for d in db.delete_requests.find({"status": "pending"}):
        rid = f"delete:{d['_id']}"
        await REQUESTS.update_one({"_id": rid}, {"$setOnInsert": {
            "id": rid, "uid": d["uid"], "kind": "hard_delete", "status": "pending",
            "payload": {"request_id": str(d['_id'])}, "note": d.get("business_case"),
            "name": d.get("user_name"), "email": d.get("user_email"),
            "requested_by": d.get("requested_by"), "requested_at": d.get("requested_at"),
            "customer_id": d.get("customer_id")}}, upsert=True)


@router.get("")
async def inbox(actor: dict = Depends(require_staff)):
    await import_legacy()
    query = {} if actor.get("is_main") else {"requested_by_sid": actor.get("sid")}
    rows = await REQUESTS.find(query, {"_id": 0, "pending_key": 0}).sort("requested_at", -1).to_list(5000)
    for r in rows:
        r.setdefault("payload", {})
        if r.get("kind") in ("review", "registry_claim") and r.get("status") in ("pending", "failed"):
            if not r["payload"].get("submission_id"):
                r.update(status="cancelled", error="The underlying application was removed. Submit a new request if needed.")
                await REQUESTS.update_one({"id": r["id"]}, {"$set": {"status": r["status"], "error": r["error"]}, "$unset": {"pending_key": ""}})
                continue
            r["verification"] = await db.verification_submissions.find_one(
                {"_id": r["payload"]["submission_id"], "uid": r["uid"]},
                {"_id": 0, "checks": 1, "selfie_file_id": 1, "document_file_id": 1, "reasons": 1})
    return {"requests": rows, "pending": sum(r["status"] in ("pending", "failed") for r in rows),
            "is_main": bool(actor.get("is_main"))}


class Decision(BaseModel):
    request_ids: list[str] = Field(min_length=1, max_length=500)
    action: Literal["approve", "decline"] = "approve"
    confirm_delete: str = ""
    note: Optional[str] = None


async def execute_request(r, actor, authorization):
    import admin_ops as ops
    p, uid = r.get("payload") or {}, r["uid"]
    if r["kind"] in ("review", "registry_claim"):
        if not p.get("submission_id"):
            raise HTTPException(409, "The application was removed; this request cannot be applied.")
        s = await db.verification_submissions.find_one({"_id": p["submission_id"], "uid": uid}, {"_id": 0})
        if not s or s.get("status") not in ("needs_review", "verified", "rejected"):
            raise HTTPException(409, "Submission changed; review the latest application.")
        if r["kind"] == "review" and s.get("review_stage") != "awaiting_signoff":
            raise HTTPException(409, "This recommendation is no longer awaiting sign-off.")
        return await ops._finalise(uid, p["submission_id"], p.get("decision", "approve"), r.get("note"), actor, authorization)
    if r["kind"] == "profile_edit":
        import verify
        current = await verify._profile(uid, authorization)
        for path, old in p.get("before", {}).items():
            value = verify._get_nested(current, path)
            proposed = verify._get_nested(p["patch"], path)
            if value != old and value != proposed:
                raise HTTPException(409, f"Profile changed since request: {path}. Decline and request again.")
        return await ops.edit_profile(uid, ops.ProfileEdit(patch=p["patch"]), actor, authorization)
    if r["kind"] == "subscription":
        return await ops.manage_subscription(uid, ops.GrantIn(**p), actor, request_id=r["id"])
    if r["kind"] == "document":
        return await ops.apply_document(uid, p, actor)
    if r["kind"] == "hard_delete":
        return await ops.hard_delete(uid, ops.DeleteIn(confirm="DELETE", note=r.get("note"),
                                     request_id=p.get("request_id")), actor, authorization)
    raise HTTPException(400, "Unsupported request type.")


@router.post("/decide")
async def decide(body: Decision, actor: dict = Depends(require_main_admin),
                 authorization: Optional[str] = Header(default=None)):
    await import_legacy()
    ids = list(dict.fromkeys(body.request_ids))
    rows = await REQUESTS.find({"id": {"$in": ids}}, {"_id": 0}).to_list(len(ids))
    if body.action == "approve" and any(r["kind"] == "hard_delete" for r in rows) and body.confirm_delete != "DELETE":
        raise HTTPException(400, "Type DELETE to approve the selected permanent deletions.")
    # Deletions always run last, after other explicitly selected changes.
    kinds = {r["id"]: r["kind"] for r in rows}
    ids.sort(key=lambda rid: kinds.get(rid) == "hard_delete")
    results = []
    from admin_ops import _audit
    for rid in ids:
        r = await REQUESTS.find_one_and_update({"id": rid, "status": {"$in": ["pending", "failed"]}},
            {"$set": {"status": "processing", "started_at": now()}}, projection={"_id": 0})
        if not r:
            results.append({"id": rid, "status": "skipped", "error": "Already decided, processing, or not found."})
            continue
        try:
            result = {} if body.action == "decline" else await execute_request(r, actor, authorization)
            status = "declined" if body.action == "decline" else "approved"
            if status == "declined" and r["kind"] in ("review", "registry_claim"):
                await db.verification_submissions.update_one({"_id": r["payload"]["submission_id"]},
                    {"$set": {"review_stage": "returned"}, "$unset": {"recommendation": ""}})
                if r["kind"] == "registry_claim":
                    await db.registry_matches.update_one({"uid": r["uid"]}, {"$set": {"status": "declined"}})
            if status == "declined" and r["kind"] == "hard_delete":
                await db.delete_requests.update_one({"_id": r["payload"].get("request_id")}, {"$set": {"status": "declined"}})
            if status == "declined" and r["kind"] == "document":
                await db.uploaded_files.update_one({"_id": r["payload"].get("file_id")}, {"$set": {"is_deleted": True}})
            await REQUESTS.update_one({"id": rid}, {"$set": {"status": status, "result": result,
                "decided_by": actor.get("name"), "decided_at": now(), "decision_note": body.note},
                "$unset": {"pending_key": "", "error": ""}})
            await _audit(actor, f"approval.{status}", r["uid"], {"request_id": rid, "kind": r["kind"]})
            results.append({"id": rid, "status": status, "result": result})
        except Exception as exc:
            error = exc.detail if isinstance(exc, HTTPException) else "Unable to complete request; retry or contact support."
            log.warning("Approval %s failed: %s", rid, type(exc).__name__)
            await REQUESTS.update_one({"id": rid}, {"$set": {"status": "failed", "error": error}})
            results.append({"id": rid, "status": "failed", "error": error})
    return {"results": results, "approved": sum(r["status"] == "approved" for r in results),
            "failed": sum(r["status"] == "failed" for r in results)}