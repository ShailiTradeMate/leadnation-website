from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timezone
import re
from core import db, require_admin

router = APIRouter()

STATUSES = ["new", "assigned", "in-progress", "Partial payment received", "Full payment received", "completed", "cancelled"]
CLOSED = {"completed", "cancelled"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _label(slug):
    from services import SERVICES_DB
    return (SERVICES_DB.get(slug or "") or {}).get("name") or (slug or "").replace("-", " ").title()


def request_email_ctx(item: dict) -> dict:
    """Same context the submission email uses — keeps every service-request mail identical."""
    return {
        "service": item.get("serviceLabel") or _label(item.get("service")), "requestId": item["id"],
        "submittedAt": (item.get("createdAt") or "")[:19].replace("T", " ") + " UTC",
        "name": item.get("name"), "email": item.get("email"), "phone": item.get("phone"),
        "company": item.get("company"), "country": item.get("country"), "message": item.get("message"),
        "entity": item.get("entity"), "profileRows": item.get("profileRows") or [("Account", "Submitted as guest (not logged in)")],
    }


def _now():
    return datetime.now(timezone.utc).isoformat()


def _who(ident: dict) -> str:
    return ident.get("email") or ident.get("name") or "admin"


@router.get("/admin/service-requests")
async def admin_service_requests(_: dict = Depends(require_admin)):
    return await db.service_requests.find({}, {"_id": 0}).sort("createdAt", -1).to_list(2000)


@router.get("/admin/service-requests/ca-options")
async def ca_options(_: dict = Depends(require_admin)):
    out = []
    async for sa in db.sub_admins.find({"active": {"$ne": False}}, {"_id": 0, "id": 1, "name": 1, "email": 1}):
        out.append({"id": sa["id"], "name": sa.get("name"), "email": sa.get("email")})
    out.sort(key=lambda x: (x.get("name") or "").lower())
    return {"statuses": STATUSES, "cas": out}


class ServiceUpdate(BaseModel):
    status: Optional[str] = None
    assignedCaId: Optional[str] = None
    assignedCa: Optional[str] = None
    assignedCaEmail: Optional[str] = None
    internalNote: Optional[str] = None
    clearCa: bool = False


@router.put("/admin/service-requests/{req_id}")
async def admin_update_service_request(req_id: str, payload: ServiceUpdate, ident: dict = Depends(require_admin)):
    item = await db.service_requests.find_one({"id": req_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Request not found")
    update, changes = {}, []
    if payload.status is not None:
        if payload.status not in STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status. Allowed: {', '.join(STATUSES)}")
        if payload.status != item.get("status"):
            update["status"] = payload.status
            changes.append(f"status: {item.get('status') or 'new'} → {payload.status}")
    touching_ca = payload.clearCa or any(v is not None for v in (payload.assignedCaId, payload.assignedCa, payload.assignedCaEmail))
    if touching_ca:
        if (update.get("status") or item.get("status")) in CLOSED:
            raise HTTPException(status_code=400, detail="Completed or cancelled requests cannot be allocated to a CA")
        if payload.clearCa:
            update.update({"assignedCaId": None, "assignedCa": None, "assignedCaEmail": None})
            changes.append("CA unassigned")
        else:
            if payload.assignedCaId:
                sa = await db.sub_admins.find_one({"id": payload.assignedCaId}, {"_id": 0})
                if not sa:
                    raise HTTPException(status_code=404, detail="Sub-admin not found")
                update["assignedCaId"] = sa["id"]
                update["assignedCa"] = payload.assignedCa or sa.get("name")
                update["assignedCaEmail"] = (payload.assignedCaEmail or sa.get("email") or "").strip().lower()
            else:
                if payload.assignedCa is not None:
                    update["assignedCaId"] = None
                    update["assignedCa"] = payload.assignedCa.strip() or None
                if payload.assignedCaEmail is not None:
                    update["assignedCaEmail"] = payload.assignedCaEmail.strip().lower() or None
            if update.get("assignedCa") and update.get("assignedCa") != item.get("assignedCa"):
                changes.append(f"CA: {item.get('assignedCa') or '—'} → {update['assignedCa']}")
            if "assignedCaEmail" in update and update["assignedCaEmail"] != item.get("assignedCaEmail"):
                changes.append(f"CA email: {update['assignedCaEmail'] or '—'}")
            if update.get("assignedCa") and (update.get("status") or item.get("status") or "new") == "new":
                update["status"] = "assigned"
                changes.append("status: new → assigned (auto)")
    if payload.internalNote is not None and payload.internalNote.strip():
        changes.append("internal note added")
    if not changes:
        return item
    now, who = _now(), _who(ident)
    update["updatedAt"], update["updatedBy"] = now, who
    push = {"history": {"at": now, "by": who, "changes": changes}}
    if payload.internalNote and payload.internalNote.strip():
        push["notes"] = {"at": now, "by": who, "text": payload.internalNote.strip()}
    await db.service_requests.update_one({"id": req_id}, {"$set": update, "$push": push})
    return await db.service_requests.find_one({"id": req_id}, {"_id": 0})


class EmailCa(BaseModel):
    to: str
    extraCc: List[str] = []
    note: Optional[str] = None
    dryRun: bool = False


def _clean_emails(xs) -> List[str]:
    out = []
    for x in xs or []:
        e = (x or "").strip().lower()
        if e and EMAIL_RE.match(e) and e not in out:
            out.append(e)
    return out


@router.post("/admin/service-requests/{req_id}/email-ca")
async def email_ca(req_id: str, payload: EmailCa, ident: dict = Depends(require_admin)):
    from emailer import send, BUILDERS, ADMIN_EMAIL
    item = await db.service_requests.find_one({"id": req_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Request not found")
    if item.get("status") in CLOSED:
        raise HTTPException(status_code=400, detail="Completed or cancelled requests cannot be allocated to a CA")
    to = (payload.to or "").strip().lower()
    if not EMAIL_RE.match(to):
        raise HTTPException(status_code=400, detail="Enter a valid CA email address")
    bad = [x for x in payload.extraCc if x.strip() and not EMAIL_RE.match(x.strip().lower())]
    if bad:
        raise HTTPException(status_code=400, detail=f"Invalid CC address: {', '.join(bad)}")
    locked = _clean_emails([item.get("email"), ADMIN_EMAIL])
    cc = _clean_emails(locked + payload.extraCc)
    cc = [e for e in cc if e != to]
    now, who = _now(), _who(ident)
    ctx = request_email_ctx(item)
    ctx.update({"caName": item.get("assignedCa") or "Vametra CA", "caEmail": to, "allocatedAt": now[:16].replace("T", " ") + " UTC",
                "allocatedBy": who, "note": (payload.note or "").strip()})
    subject, html = BUILDERS["service_allocation"](ctx)
    if payload.dryRun:
        return {"subject": subject, "html": html, "to": to, "cc": cc, "lockedCc": locked}
    res = await send("service_allocation", to, ctx, cc=cc, reply_to=item.get("email"))
    if not res.get("sent"):
        raise HTTPException(status_code=400, detail=f"Email could not be sent: {res.get('error') or res.get('reason') or 'unknown error'}")
    activity = {"at": now, "by": who, "kind": "allocation", "to": to, "cc": cc, "subject": subject, "providerId": res.get("id")}
    upd = {"caNotifiedAt": now, "updatedAt": now, "updatedBy": who, "assignedCaEmail": to}
    if not item.get("assignedCa"):
        upd["assignedCa"] = "Vametra CA"
    if (item.get("status") or "new") == "new":
        upd["status"] = "assigned"
    await db.service_requests.update_one({"id": req_id}, {"$set": upd, "$push": {
        "emailActivity": activity, "history": {"at": now, "by": who, "changes": [f"allocation email sent to {to} (cc {', '.join(cc)})"]}}})
    return {"ok": True, "to": to, "cc": cc, "item": await db.service_requests.find_one({"id": req_id}, {"_id": 0})}
