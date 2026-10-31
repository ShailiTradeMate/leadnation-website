"""WhatsApp message templates — written in the customer's voice, auto-populated
with their Vametra identity. Editable by the main admin from the Dashboard."""
from datetime import datetime, timezone
from typing import Optional
import re
import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core import db, require_admin
from firebase_auth import optional_user

router = APIRouter()

PLACEHOLDERS = ["name", "customer_id", "phone", "email", "service", "request_id",
                "company", "product", "tool", "cha", "port", "page", "ca_name", "message", "documents"]

DEFAULTS = {
    "general": {
        "label": "Floating chat button",
        "where": "Green WhatsApp bubble on every page",
        "template": (
            "Hi Vametra AI, I'm reaching out to understand how Vametra AI can help my trade business.\n\n"
            "My details\n"
            "• Name: {{name}}\n"
            "• Vametra ID: {{customer_id}}\n"
            "• Mobile: {{phone}}\n"
            "• Email: {{email}}\n\n"
            "Page I'm on: {{page}}"
        ),
    },
    "service_request": {
        "label": "After a service request is submitted",
        "where": "Chat on WhatsApp button on the service success card",
        "template": (
            "Hi Vametra AI, I have just submitted a service request for {{service}} on your website "
            "and I'd like to take it forward here on WhatsApp.\n\n"
            "My details\n"
            "• Name: {{name}}\n"
            "• Vametra ID: {{customer_id}}\n"
            "• Mobile: {{phone}}\n"
            "• Email: {{email}}\n"
            "• Request ID: {{request_id}}\n\n"
            "Please confirm the next steps and the documents you need from me."
        ),
    },
    "service_enquiry": {
        "label": "Service page enquiry",
        "where": "WhatsApp links on service pages before submitting",
        "template": (
            "Hi Vametra AI, I'm interested in your {{service}} service and I want to know the charges, "
            "documents required and how long it takes.\n\n"
            "My details\n"
            "• Name: {{name}}\n"
            "• Vametra ID: {{customer_id}}\n"
            "• Mobile: {{phone}}\n"
            "• Email: {{email}}"
        ),
    },
    "contact": {
        "label": "Contact page",
        "where": "WhatsApp card / button on /contact",
        "template": (
            "Hi Vametra AI, I'm reaching out through your Contact page because I need help with my "
            "import-export requirement.\n\n"
            "My details\n"
            "• Name: {{name}}\n"
            "• Vametra ID: {{customer_id}}\n"
            "• Mobile: {{phone}}\n"
            "• Email: {{email}}\n\n"
            "What I need help with: "
        ),
    },
    "supplier_connect": {
        "label": "Supplier connect",
        "where": "Connect buttons in the supplier directory",
        "template": (
            "Hi Vametra AI, please connect me with the supplier {{company}} ({{product}}) listed on "
            "your website.\n\n"
            "My details\n"
            "• Name: {{name}}\n"
            "• Vametra ID: {{customer_id}}\n"
            "• Mobile: {{phone}}\n"
            "• Email: {{email}}\n\n"
            "Quantity / requirement: "
        ),
    },
    "cha_connect": {
        "label": "CHA / customs partner connect",
        "where": "Connect via WhatsApp in the Customs engine",
        "template": (
            "Hi Vametra AI, please connect me with the CHA {{cha}} at {{port}} port.\n\n"
            "My details\n"
            "• Name: {{name}}\n"
            "• Vametra ID: {{customer_id}}\n"
            "• Mobile: {{phone}}\n"
            "• Email: {{email}}\n\n"
            "Shipment details: "
        ),
    },
    "tool_help": {
        "label": "Trade tools help",
        "where": "Chat on WhatsApp inside the trade tools",
        "template": (
            "Hi Vametra AI, I'm using the {{tool}} on your website and I need help understanding the "
            "result for my shipment.\n\n"
            "My details\n"
            "• Name: {{name}}\n"
            "• Vametra ID: {{customer_id}}\n"
            "• Mobile: {{phone}}\n"
            "• Email: {{email}}\n\n"
            "Page I'm on: {{page}}"
        ),
    },
    "ca_message": {
        "label": "CA → customer (documents & updates)",
        "where": "Sent to the customer's WhatsApp from the request chatbox in the Admin / CA dashboard",
        "template": (
            "Hi {{name}}, this is {{ca_name}} from Vametra AI regarding your {{service}} request "
            "(ID {{request_id}}).\n\n"
            "{{message}}\n\n"
            "{{documents}}\n\n"
            "The same has been emailed to {{email}}. Reply here if you need anything else."
        ),
    },
}


class TemplatePatch(BaseModel):
    template: str


# ---------------- Click logging (every customer tap on a WhatsApp button) ----------------
def phone_key(p) -> str:
    """Last 10 digits — lets +91 98xx and 098xx match the same customer."""
    d = re.sub(r"\D", "", str(p or ""))
    return d[-10:] if len(d) >= 10 else d


class WaClick(BaseModel):
    key: str = "direct"
    page: str = ""
    message: str = ""
    requestId: Optional[str] = None
    service: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    customerId: Optional[str] = None


def _s(v, n):
    return (str(v).strip()[:n] or None) if v is not None else None


@router.post("/whatsapp/clicks")
async def log_click(payload: WaClick, user: Optional[dict] = Depends(optional_user)):
    account = {}
    if user:
        account = await db.do_users_cache.find_one({"uid": user.get("uid")}, {"_id": 0}) \
            or await db.do_users_cache.find_one({"email": (user.get("email") or "").lower()}, {"_id": 0}) or {}
    email = (_s(account.get("email") or (user or {}).get("email") or payload.email, 200) or "").lower() or None
    phone = _s(account.get("mobile") or account.get("phone") or payload.phone, 40)
    doc = {
        "id": uuid.uuid4().hex, "at": datetime.now(timezone.utc).isoformat(),
        "key": payload.key if payload.key in DEFAULTS else "direct",
        "label": (DEFAULTS.get(payload.key) or {}).get("label") or "WhatsApp link",
        "page": _s(payload.page, 500), "message": _s(payload.message, 2000),
        "requestId": _s(payload.requestId, 80), "service": _s(payload.service, 120),
        "name": _s(account.get("full_name") or account.get("name") or payload.name, 120),
        "phone": phone, "phoneKey": phone_key(phone), "email": email,
        "customerId": _s(account.get("customer_id") or payload.customerId, 20),
        "userUid": (user or {}).get("uid"), "signedIn": bool(user),
    }
    await db.wa_clicks.insert_one(doc)
    doc.pop("_id", None)
    ors = [{"id": doc["requestId"]}] if doc["requestId"] else []
    if doc["customerId"]:
        ors.append({"customerId": doc["customerId"]})
    if email:
        ors += [{"email": email}, {"accountEmail": email}]
    if ors:
        await db.service_requests.update_many({"$or": ors}, {"$set": {"lastWhatsAppAt": doc["at"]}})
    return {"ok": True, "id": doc["id"]}


def click_filter(item: dict) -> dict:
    ors = [{"requestId": item["id"]}]
    if item.get("customerId"):
        ors.append({"customerId": item["customerId"]})
    for e in {(item.get("email") or "").lower(), (item.get("accountEmail") or "").lower()} - {""}:
        ors.append({"email": e})
    pk = phone_key(item.get("phone"))
    if len(pk) == 10:
        ors.append({"phoneKey": pk})
    return {"$or": ors}


@router.get("/admin/whatsapp-clicks")
async def admin_clicks(limit: int = 100, _: bool = Depends(require_admin)):
    rows = await db.wa_clicks.find({}, {"_id": 0}).sort("at", -1).to_list(min(max(limit, 1), 500))
    return {"items": rows}


async def _overrides() -> dict:
    rows = await db.wa_templates.find({}, {"_id": 0}).to_list(100)
    return {r["key"]: r for r in rows}


@router.get("/whatsapp/templates")
async def public_templates():
    """Public — the website renders these with the signed-in user's details."""
    ov = await _overrides()
    return {
        "templates": {k: (ov.get(k, {}).get("template") or v["template"]) for k, v in DEFAULTS.items()},
        "placeholders": PLACEHOLDERS,
    }


@router.get("/admin/whatsapp-templates")
async def admin_list(_: bool = Depends(require_admin)):
    ov = await _overrides()
    return {
        "placeholders": PLACEHOLDERS,
        "items": [
            {
                "key": k,
                "label": v["label"],
                "where": v["where"],
                "default": v["template"],
                "template": ov.get(k, {}).get("template") or v["template"],
                "customized": bool(ov.get(k, {}).get("template")),
                "updatedAt": ov.get(k, {}).get("updatedAt"),
            }
            for k, v in DEFAULTS.items()
        ],
    }


@router.put("/admin/whatsapp-templates/{key}")
async def admin_update(key: str, patch: TemplatePatch, _: bool = Depends(require_admin)):
    if key not in DEFAULTS:
        raise HTTPException(status_code=404, detail="Unknown template")
    text = patch.template.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Template cannot be empty")
    await db.wa_templates.update_one(
        {"key": key},
        {"$set": {"key": key, "template": text, "updatedAt": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    return {"key": key, "template": text, "customized": True}


@router.post("/admin/whatsapp-templates/{key}/reset")
async def admin_reset(key: str, _: bool = Depends(require_admin)):
    if key not in DEFAULTS:
        raise HTTPException(status_code=404, detail="Unknown template")
    await db.wa_templates.delete_one({"key": key})
    return {"key": key, "template": DEFAULTS[key]["template"], "customized": False}
