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
    items = await db.service_requests.find({}, {"_id": 0}).sort("createdAt", -1).to_list(2000)
    for it in items:
        it["hasUnreadReply"] = "admin" in (it.get("unreadFor") or [])
    return items


@router.get("/admin/service-requests/ca-options")
async def ca_options(_: dict = Depends(require_admin)):
    out = []
    async for sa in db.sub_admins.find({"active": {"$ne": False}}, {"_id": 0, "id": 1, "name": 1, "email": 1, "category": 1}):
        out.append({"id": sa["id"], "name": sa.get("name"), "email": sa.get("email"), "category": sa.get("category") or "Uncategorised"})
    out.sort(key=lambda x: (x["category"] != "CA", x["category"] != "Associate", (x.get("name") or "").lower()))
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
    from emailer import ADMIN_EMAIL
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
    return await _send_allocation(item, to, cc, locked, payload.note, who, now, payload.dryRun)


async def _send_allocation(item, to, cc, locked, note, who, now, dry_run):
    from emailer import send, BUILDERS
    req_id = item["id"]
    ctx = request_email_ctx(item)
    ctx.update({"caName": item.get("assignedCa") or "Vametra CA", "caEmail": to, "allocatedAt": now[:16].replace("T", " ") + " UTC",
                "allocatedBy": who, "note": (note or "").strip()})
    subject, html = BUILDERS["service_allocation"](ctx)
    if dry_run:
        return {"subject": subject, "html": html, "to": to, "cc": cc, "lockedCc": locked}
    res = await send("service_allocation", to, ctx, cc=cc, reply_to=item.get("email"))
    if not res.get("sent"):
        raise HTTPException(status_code=400, detail=f"Email could not be sent: {res.get('error') or res.get('reason') or 'unknown error'}")
    activity = {"at": now, "by": who, "byName": "Vametra AI team", "role": "admin", "kind": "allocation", "to": to, "cc": cc, "subject": subject,
                "note": (note or "").strip() or None, "providerId": res.get("id")}
    upd = {"caNotifiedAt": now, "updatedAt": now, "updatedBy": who, "assignedCaEmail": to}
    if not item.get("assignedCa"):
        upd["assignedCa"] = "Vametra CA"
    if (item.get("status") or "new") == "new":
        upd["status"] = "assigned"
    await db.service_requests.update_one({"id": req_id}, {"$set": upd, "$push": {
        "emailActivity": activity, "history": {"at": now, "by": who, "changes": [f"allocation email sent to {to} (cc {', '.join(cc)})"]}}})
    return {"ok": True, "to": to, "cc": cc, "item": await db.service_requests.find_one({"id": req_id}, {"_id": 0})}


class EmailCustomer(BaseModel):
    message: str
    extraCc: List[str] = []
    dryRun: bool = False


async def send_customer_message(item: dict, message: str, extra_cc: List[str], sender_name: str, sender_email: Optional[str],
                                sender_role: str, dry_run: bool = False):
    """Shared by main admin and (Phase 4) sub-admins: emails the customer using the service-request template."""
    from emailer import send, BUILDERS, ADMIN_EMAIL
    message = (message or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="Write a message first")
    bad = [x for x in extra_cc if x.strip() and not EMAIL_RE.match(x.strip().lower())]
    if bad:
        raise HTTPException(status_code=400, detail=f"Invalid CC address: {', '.join(bad)}")
    to = (item.get("email") or "").strip().lower()
    if not EMAIL_RE.match(to):
        raise HTTPException(status_code=400, detail="This request has no valid customer email")
    locked = _clean_emails([ADMIN_EMAIL, item.get("assignedCaEmail")])
    cc = [e for e in _clean_emails(locked + extra_cc) if e != to]
    now = _now()
    ctx = request_email_ctx(item)
    ctx.update({"senderName": sender_name, "senderRole": sender_role, "senderEmail": sender_email, "messageText": message,
                "sentAt": now[:16].replace("T", " ") + " UTC", "caName": item.get("assignedCa")})
    subject, html = BUILDERS["service_message"](ctx)
    if dry_run:
        return {"subject": subject, "html": html, "to": to, "cc": cc, "lockedCc": locked}
    res = await send("service_message", to, ctx, cc=cc, reply_to=sender_email or ADMIN_EMAIL)
    if not res.get("sent"):
        raise HTTPException(status_code=400, detail=f"Email could not be sent: {res.get('error') or res.get('reason') or 'unknown error'}")
    who = sender_email or sender_name
    activity = {"at": now, "by": who, "byName": sender_name, "role": sender_role, "kind": "message", "to": to, "cc": cc,
                "subject": subject, "text": message, "providerId": res.get("id")}
    await db.service_requests.update_one({"id": item["id"]}, {"$set": {"updatedAt": now, "updatedBy": who, "lastMessageAt": now}, "$push": {
        "emailActivity": activity, "history": {"at": now, "by": who, "changes": [f"message emailed to customer (cc {', '.join(cc) or '—'})"]}}})
    return {"ok": True, "to": to, "cc": cc, "item": await db.service_requests.find_one({"id": item["id"]}, {"_id": 0})}


@router.post("/admin/service-requests/{req_id}/email-customer")
async def admin_email_customer(req_id: str, payload: EmailCustomer, ident: dict = Depends(require_admin)):
    item = await db.service_requests.find_one({"id": req_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Request not found")
    return await send_customer_message(item, payload.message, payload.extraCc, "Vametra AI team", ident.get("email"), "admin", payload.dryRun)


# ---------------- Allocate (one step: assign + optional allocation email) ----------------
class AllocateIn(BaseModel):
    assignedCaId: Optional[str] = None
    assignedCa: Optional[str] = None
    assignedCaEmail: Optional[str] = None
    note: Optional[str] = None
    sendEmail: bool = True
    extraCc: List[str] = []


@router.post("/admin/service-requests/{req_id}/allocate")
async def allocate(req_id: str, payload: AllocateIn, ident: dict = Depends(require_admin)):
    from emailer import ADMIN_EMAIL
    item = await db.service_requests.find_one({"id": req_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Request not found")
    if item.get("status") in CLOSED:
        raise HTTPException(status_code=400, detail="Completed or cancelled requests cannot be allocated to a CA")
    if payload.assignedCaId:
        sa = await db.sub_admins.find_one({"id": payload.assignedCaId}, {"_id": 0})
        if not sa:
            raise HTTPException(status_code=404, detail="Sub-admin not found")
        ca_id, ca_name, ca_email = sa["id"], sa.get("name"), (payload.assignedCaEmail or sa.get("email") or "").strip().lower()
    else:
        ca_id, ca_name, ca_email = None, (payload.assignedCa or "").strip(), (payload.assignedCaEmail or "").strip().lower()
        if not ca_name:
            raise HTTPException(status_code=400, detail="Enter the CA / employee name")
    if payload.sendEmail and not EMAIL_RE.match(ca_email):
        raise HTTPException(status_code=400, detail="Enter a valid CA email address to send the allocation email")
    now, who = _now(), _who(ident)
    changes = [f"allocated to {ca_name}" + (f" <{ca_email}>" if ca_email else "")]
    upd = {"assignedCaId": ca_id, "assignedCa": ca_name, "assignedCaEmail": ca_email or None, "allocatedAt": now, "allocatedBy": who,
           "updatedAt": now, "updatedBy": who, "openedBy": []}
    if (item.get("status") or "new") == "new":
        upd["status"] = "assigned"
        changes.append("status: new → assigned (auto)")
    push = {"history": {"at": now, "by": who, "changes": changes}}
    if payload.note and payload.note.strip():
        push["notes"] = {"at": now, "by": who, "text": f"[allocation] {payload.note.strip()}"}
    await db.service_requests.update_one({"id": req_id}, {"$set": upd, "$push": push})
    item = await db.service_requests.find_one({"id": req_id}, {"_id": 0})
    if payload.sendEmail:
        bad = [x for x in payload.extraCc if x.strip() and not EMAIL_RE.match(x.strip().lower())]
        if bad:
            raise HTTPException(status_code=400, detail=f"Allocated, but invalid CC address: {', '.join(bad)}")
        locked = _clean_emails([item.get("email"), ADMIN_EMAIL])
        cc = [e for e in _clean_emails(locked + payload.extraCc) if e != ca_email]
        return await _send_allocation(item, ca_email, cc, locked, payload.note, who, now, False)
    return {"ok": True, "item": item}


# ---------------- Staff (main admin + sub-admins) ----------------
from subadmin import require_staff, has_perm  # noqa: E402


async def _staff_item(req_id: str, ident: dict) -> dict:
    item = await db.service_requests.find_one({"id": req_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Request not found")
    if not ident.get("is_main") and item.get("assignedCaId") != ident.get("sid"):
        raise HTTPException(status_code=403, detail="This request is not allocated to you")
    return item


def _staff_name(ident: dict) -> str:
    return "Vametra AI team" if ident.get("is_main") else (ident.get("name") or "Vametra CA")


@router.get("/staff/service-requests")
async def staff_service_requests(ident: dict = Depends(require_staff)):
    q = {} if ident.get("is_main") else {"assignedCaId": ident.get("sid")}
    items = await db.service_requests.find(q, {"_id": 0}).sort("createdAt", -1).to_list(2000)
    sid = ident.get("sid")
    viewer = sid or "admin"
    for it in items:
        it["isNew"] = bool(sid) and sid not in (it.get("openedBy") or [])
        it["hasUnreadReply"] = viewer in (it.get("unreadFor") or [])
    return {"items": items, "statuses": STATUSES, "me": {"sid": sid, "name": ident.get("name"), "email": ident.get("email"), "isMain": bool(ident.get("is_main"))}}


@router.get("/staff/service-requests/summary")
async def staff_service_requests_summary(ident: dict = Depends(require_staff)):
    q = {} if ident.get("is_main") else {"assignedCaId": ident.get("sid")}
    items = await db.service_requests.find(q, {"_id": 0, "status": 1, "openedBy": 1, "assignedCaId": 1, "assignedCa": 1, "unreadFor": 1}).to_list(5000)
    sid = ident.get("sid")
    viewer = sid or "admin"
    open_ = [i for i in items if (i.get("status") or "new") not in CLOSED]
    users_q = {"status": "needs_review"} if ident.get("is_main") else {"status": "needs_review", "assigned_to": sid}
    users_pending = await db.verification_submissions.count_documents(users_q)
    return {"open": len(open_), "new": len([i for i in open_ if sid and sid not in (i.get("openedBy") or [])]),
            "unassigned": len([i for i in open_ if not i.get("assignedCaId") and not i.get("assignedCa")]),
            "unreadReplies": len([i for i in items if viewer in (i.get("unreadFor") or [])]),
            "usersPending": users_pending}


@router.post("/staff/service-requests/{req_id}/open")
async def staff_open(req_id: str, ident: dict = Depends(require_staff)):
    await _staff_item(req_id, ident)
    if ident.get("sid"):
        await db.service_requests.update_one({"id": req_id}, {"$addToSet": {"openedBy": ident["sid"]}, "$pull": {"unreadFor": ident["sid"]}})
    else:
        await db.service_requests.update_one({"id": req_id}, {"$pull": {"unreadFor": "admin"}})
    return {"ok": True}


class StaffUpdate(BaseModel):
    status: Optional[str] = None
    internalNote: Optional[str] = None


@router.put("/staff/service-requests/{req_id}")
async def staff_update(req_id: str, payload: StaffUpdate, ident: dict = Depends(require_staff)):
    if not has_perm(ident, "service_requests.update_status"):
        raise HTTPException(status_code=403, detail="Not allowed")
    item = await _staff_item(req_id, ident)
    update, changes = {}, []
    if payload.status is not None and payload.status != item.get("status"):
        if payload.status not in STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status. Allowed: {', '.join(STATUSES)}")
        if not ident.get("is_main") and item.get("status") == "completed":
            raise HTTPException(status_code=400, detail="Completed requests are final — ask the main admin to reopen")
        update["status"] = payload.status
        changes.append(f"status: {item.get('status') or 'new'} → {payload.status}")
    if payload.internalNote and payload.internalNote.strip():
        changes.append("internal note added")
    if not changes:
        return item
    now, who = _now(), (ident.get("email") or _staff_name(ident))
    update.update({"updatedAt": now, "updatedBy": who})
    push = {"history": {"at": now, "by": who, "changes": changes}}
    if payload.internalNote and payload.internalNote.strip():
        push["notes"] = {"at": now, "by": who, "text": payload.internalNote.strip()}
    await db.service_requests.update_one({"id": req_id}, {"$set": update, "$push": push})
    return await db.service_requests.find_one({"id": req_id}, {"_id": 0})


@router.post("/staff/service-requests/{req_id}/email-customer")
async def staff_email_customer(req_id: str, payload: EmailCustomer, ident: dict = Depends(require_staff)):
    if not has_perm(ident, "service_requests.email_customer"):
        raise HTTPException(status_code=403, detail="Not allowed")
    item = await _staff_item(req_id, ident)
    role = "admin" if ident.get("is_main") else "CA"
    return await send_customer_message(item, payload.message, payload.extraCc, _staff_name(ident), ident.get("email"), role, payload.dryRun)


# ---------------- Inbound replies (IMAP poller) ----------------
@router.post("/admin/service-requests/{req_id}/seen")
async def admin_seen(req_id: str, _: dict = Depends(require_admin)):
    await db.service_requests.update_one({"id": req_id}, {"$pull": {"unreadFor": "admin"}})
    return {"ok": True}


@router.get("/admin/service-requests/inbox/status")
async def inbox_status(_: dict = Depends(require_admin)):
    import mail_inbox
    return await mail_inbox.status()


@router.post("/staff/service-requests/inbox/poll")
async def inbox_poll(ident: dict = Depends(require_staff)):
    import mail_inbox
    return await mail_inbox.poll_once()


# ---------------- Attachments in the conversation ----------------
from fastapi import UploadFile, File, Form  # noqa: E402
from fastapi.responses import Response  # noqa: E402
import base64  # noqa: E402
import uuid as _uuid  # noqa: E402

MAX_ATTACH_BYTES = 8 * 1024 * 1024
ALLOWED_EXT = {".pdf", ".png", ".jpg", ".jpeg", ".doc", ".docx", ".xls", ".xlsx", ".zip", ".txt", ".csv"}


async def _send_with_files(item: dict, message: str, extra_cc: List[str], files: List[UploadFile], sender_name: str,
                           sender_email: Optional[str], sender_role: str):
    from emailer import send, BUILDERS, ADMIN_EMAIL
    stored, payload = [], []
    total = 0
    for f in files:
        data = await f.read()
        ext = ("." + f.filename.rsplit(".", 1)[-1].lower()) if "." in (f.filename or "") else ""
        if ext not in ALLOWED_EXT:
            raise HTTPException(status_code=400, detail=f"File type not allowed: {f.filename}")
        total += len(data)
        if total > MAX_ATTACH_BYTES:
            raise HTTPException(status_code=400, detail="Attachments exceed 8 MB in total")
        fid = _uuid.uuid4().hex
        await db.service_files.insert_one({"id": fid, "requestId": item["id"], "filename": f.filename, "contentType": f.content_type or "application/octet-stream",
                                           "size": len(data), "data": base64.b64encode(data).decode(), "uploadedAt": _now(), "by": sender_email or sender_name})
        stored.append({"id": fid, "filename": f.filename, "size": len(data)})
        payload.append({"filename": f.filename, "content": data})
    message = (message or "").strip() or ("Please find the attached document(s)." if payload else "")
    if not message:
        raise HTTPException(status_code=400, detail="Write a message or attach a file")
    bad = [x for x in extra_cc if x.strip() and not EMAIL_RE.match(x.strip().lower())]
    if bad:
        raise HTTPException(status_code=400, detail=f"Invalid CC address: {', '.join(bad)}")
    to = (item.get("email") or "").strip().lower()
    if not EMAIL_RE.match(to):
        raise HTTPException(status_code=400, detail="This request has no valid customer email")
    locked = _clean_emails([ADMIN_EMAIL, item.get("assignedCaEmail")])
    cc = [e for e in _clean_emails(locked + extra_cc) if e != to]
    now = _now()
    ctx = request_email_ctx(item)
    ctx.update({"senderName": sender_name, "senderRole": sender_role, "senderEmail": sender_email, "messageText": message,
                "sentAt": now[:16].replace("T", " ") + " UTC", "caName": item.get("assignedCa"), "attachmentNames": [s["filename"] for s in stored]})
    subject, _ = BUILDERS["service_message"](ctx)
    res = await send("service_message", to, ctx, cc=cc, reply_to=sender_email or ADMIN_EMAIL, attachments=payload or None)
    if not res.get("sent"):
        await db.service_files.delete_many({"id": {"$in": [s["id"] for s in stored]}})
        raise HTTPException(status_code=400, detail=f"Email could not be sent: {res.get('error') or res.get('reason') or 'unknown error'}")
    who = sender_email or sender_name
    activity = {"at": now, "by": who, "byName": sender_name, "role": sender_role, "kind": "message", "to": to, "cc": cc,
                "subject": subject, "text": message, "attachments": stored, "providerId": res.get("id")}
    await db.service_requests.update_one({"id": item["id"]}, {"$set": {"updatedAt": now, "updatedBy": who, "lastMessageAt": now}, "$push": {
        "emailActivity": activity, "history": {"at": now, "by": who, "changes": [f"message emailed to customer with {len(stored)} attachment(s)" if stored else "message emailed to customer"]}}})
    return {"ok": True, "to": to, "cc": cc, "item": await db.service_requests.find_one({"id": item["id"]}, {"_id": 0})}


@router.post("/staff/service-requests/{req_id}/email-customer-files")
async def staff_email_customer_files(req_id: str, message: str = Form(""), extraCc: str = Form(""),
                                     files: List[UploadFile] = File(default=[]), ident: dict = Depends(require_staff)):
    if not has_perm(ident, "service_requests.email_customer"):
        raise HTTPException(status_code=403, detail="Not allowed")
    item = await _staff_item(req_id, ident)
    role = "admin" if ident.get("is_main") else "CA"
    cc = [x for x in re.split(r"[,;\s]+", extraCc or "") if x]
    return await _send_with_files(item, message, cc, files, _staff_name(ident), ident.get("email"), role)


@router.get("/staff/service-requests/{req_id}/files/{file_id}")
async def staff_download_file(req_id: str, file_id: str, ident: dict = Depends(require_staff)):
    await _staff_item(req_id, ident)
    doc = await db.service_files.find_one({"id": file_id, "requestId": req_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="File not found")
    return Response(content=base64.b64decode(doc["data"]), media_type=doc.get("contentType") or "application/octet-stream",
                    headers={"Content-Disposition": f'attachment; filename="{doc["filename"]}"'})
