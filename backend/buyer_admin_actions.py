"""CMS actions reuse user approval/deletion services; no second buyer-user store."""
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from core import db
from subadmin import require_main_admin
from buyer_membership import entity_query, now

router = APIRouter(prefix="/admin/buyer-records")


@router.get("/{geid}")
async def buyer_record(geid: str, actor: dict = Depends(require_main_admin)):
    e = await db.entities.find_one(entity_query(geid), {"_id": 0})
    if not e:
        raise HTTPException(404, "Buyer not found.")
    uids = set(e.get("verified_member_uids", []))
    async for b in db.members_bridge.find({"geid": geid}, {"_id": 0}):
        if b.get("uid"):
            uids.add(b["uid"])
    async for b in db.verification_submissions.find({"geid": geid}, {"_id": 0, "uid": 1}):
        uids.add(b["uid"])
    async for b in db.registry_matches.find({"geid": geid}, {"_id": 0, "uid": 1}):
        uids.add(b["uid"])
    from admin_ops import _user_doc
    people = []
    for uid in sorted(uids):
        u = await _user_doc(uid)
        s = await db.verification_submissions.find_one({"uid": uid}, {"_id": 0}, sort=[("created_at", -1)]) or {}
        requests = await db.admin_approval_requests.find({"uid": uid, "kind": "registry_claim", "status": {"$in": ["pending", "failed"]}}, {"_id": 0}).to_list(50)
        people.append({"uid": uid, "name": u.get("name") or u.get("full_name") or s.get("name"),
            "email": u.get("email") or s.get("email"), "submission": s, "requests": requests})
    return {"buyer": e, "users": people, "linked_uids": sorted(uids)}


class AddUser(BaseModel):
    request_id: str


@router.post("/{geid}/add-user")
async def add_buyer_user(geid: str, body: AddUser, actor: dict = Depends(require_main_admin),
                         authorization: Optional[str] = Header(default=None)):
    r = await db.admin_approval_requests.find_one({"id": body.request_id, "kind": "registry_claim", "payload.geid": geid}, {"_id": 0})
    if not r:
        raise HTTPException(404, "No KYC approval request for this buyer.")
    from admin_approvals import decide, Decision
    return await decide(Decision(request_ids=[body.request_id]), actor, authorization)


class BuyerDelete(BaseModel):
    confirm: str
    linked_uids: list[str]
    note: Optional[str] = None


@router.post("/{geid}/hard-delete")
async def delete_buyer_record(geid: str, body: BuyerDelete, actor: dict = Depends(require_main_admin),
                              authorization: Optional[str] = Header(default=None)):
    if body.confirm != "DELETE":
        raise HTTPException(400, "Type DELETE to confirm permanent deletion.")
    detail = await buyer_record(geid, actor)
    if sorted(set(body.linked_uids)) != detail["linked_uids"]:
        raise HTTPException(409, "Linked users changed. Reopen this record and confirm again.")
    from admin_ops import hard_delete, DeleteIn
    results = []
    for uid in detail["linked_uids"]:
        results.append(await hard_delete(uid, DeleteIn(confirm="DELETE", note=body.note), actor, authorization))
    await purge_buyer(geid)
    return {"ok": True, "deleted_users": len(results), "results": results}


async def purge_buyer(geid):
    # Content-free suppression tombstone is not a buyer record; ingestion cannot recreate it.
    await db.buyer_deletion_tombstones.update_one({"geid": geid}, {"$set": {"geid": geid, "at": now()}}, upsert=True)
    for name in ("buyer_watchlist", "buyer_claims", "buyer_contact_reveals", "company_profiles", "members_bridge", "registry_matches"):
        await db[name].delete_many({"geid": geid})
    await db.entities.delete_one({"geid": geid})