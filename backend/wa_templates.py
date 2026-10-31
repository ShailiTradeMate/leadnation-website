"""WhatsApp message templates — written in the customer's voice, auto-populated
with their Vametra identity. Editable by the main admin from the Dashboard."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core import db, require_admin

router = APIRouter()

PLACEHOLDERS = ["name", "customer_id", "phone", "email", "service", "request_id",
                "company", "product", "tool", "cha", "port", "page"]

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
}


class TemplatePatch(BaseModel):
    template: str


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
