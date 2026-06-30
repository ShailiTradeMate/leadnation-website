"""Trade Projects — the stateful spine of the LeadNation Trade Command Center.

Every calculation, quote, report, document and Brain conversation belongs to ONE
persistent Trade Project. Projects are owned by a Firebase UID (signed-in) OR an
anonymous Trade Session UUID (guest). On login the guest projects merge into the
account (POST /projects/merge), exactly like Notion/Figma/Canva.

Stored in the LOCAL content DB (collection `trade_projects`) — this is website
content keyed by owner, NOT identity (identity stays on the shared DO backend).
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from core import db
import duty_engine
from firebase_auth import _bearer, verify_token

router = APIRouter(prefix="/projects")
COL = db.trade_projects

WORKFLOW = ["Created", "Research", "Costing", "Compliance", "Documentation",
            "Quotation", "Negotiation", "Shipment", "Completed"]

NEXT_ACTION = {
    "Created": "Add product, route and quantity, then build your costing.",
    "Research": "Review market & buyer comparison, then move to costing.",
    "Costing": "Complete the FOB → CIF cost waterfall and set your margin.",
    "Compliance": "Confirm duties, FTA eligibility and required documents.",
    "Documentation": "Prepare and attach the shipment documents.",
    "Quotation": "Generate and export the buyer quote (PDF).",
    "Negotiation": "Share the quote and align on Incoterm & payment terms.",
    "Shipment": "Book freight, insurance and track the shipment.",
    "Completed": "Archive the project or duplicate it as a template.",
}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _owner(authorization: Optional[str], session: Optional[str]):
    """Return (owner_id, owner_type). Signed-in UID wins; else guest session UUID."""
    token = _bearer(authorization)
    claims = verify_token(token) if token else None
    if claims and claims.get("uid"):
        return claims["uid"], "uid"
    if session:
        return session, "guest"
    raise HTTPException(status_code=400, detail="Missing X-Trade-Session for guest, or sign in.")


# ---------------- Health scores (deterministic, explainable) ----------------
def compute_health(p: dict) -> dict:
    q = p.get("lastQuote") or {}
    margin = float(p.get("marginPct") or 0)
    pay = (p.get("paymentMethod") or "").lower()
    incoterm = (p.get("incoterm") or "").upper()
    docs = p.get("documents") or []
    stage_idx = WORKFLOW.index(p["stage"]) if p.get("stage") in WORKFLOW else 0

    dest = (q.get("destination") or {})
    duty_known = dest.get("dutyRate") is not None
    fta = bool(dest.get("fta"))

    def band(v):
        v = max(0, min(100, round(v)))
        color = "emerald" if v >= 70 else ("amber" if v >= 40 else "rose")
        return {"value": v, "color": color}

    profitability = band(min(100, margin * 4))
    # payment-risk: advance safest, LC good, DA/DP moderate, open account riskiest
    pay_risk = {"advance": 90, "lc": 78, "letter of credit": 78, "cad": 60, "da": 50, "dp": 55, "open account": 30}
    base_risk = next((v for k, v in pay_risk.items() if k in pay), 55)
    risk = band(base_risk - (0 if margin >= 12 else 10) + (5 if incoterm in ("CIF", "CFR", "DAP", "DDP") else 0))
    compliance = band((70 if duty_known else 40) + (15 if fta else 0) + (10 if incoterm else 0))
    documentation = band(min(100, 30 + len(docs) * 12))
    timeline = band((stage_idx / (len(WORKFLOW) - 1)) * 100)
    cash_flow = band(base_risk * 0.6 + min(40, margin * 1.6))

    parts = [profitability, risk, compliance, documentation, timeline, cash_flow]
    overall = band(sum(x["value"] for x in parts) / len(parts))
    return {
        "profitability": profitability, "risk": risk, "compliance": compliance,
        "documentation": documentation, "timeline": timeline, "cashFlow": cash_flow,
        "overall": overall,
    }


def _summary(p: dict) -> dict:
    q = p.get("lastQuote") or {}
    tc = (q.get("currency") or {}).get("transaction") or p.get("transactionCurrency") or "USD"
    return {
        "revenue": (q.get("pricing") or {}).get("selling"),
        "profit": (q.get("pricing") or {}).get("profit"),
        "currency": tc,
        "buyer": p.get("buyer"), "supplier": p.get("supplier"),
        "destination": duty_engine.NAME_BY_CODE.get(p.get("importer"), p.get("importer")),
        "origin": duty_engine.NAME_BY_CODE.get(p.get("exporter"), p.get("exporter")),
        "status": p.get("status") or "active", "stage": p.get("stage"),
        "nextAction": NEXT_ACTION.get(p.get("stage"), ""),
    }


def _public(p: dict) -> dict:
    p = {k: v for k, v in p.items() if k != "_id"}
    p["health"] = compute_health(p)
    p["summary"] = _summary(p)
    return p


def _card(p: dict) -> dict:
    return {
        "id": p["id"], "title": p.get("title"), "stage": p.get("stage"),
        "product": p.get("product"), "hs": p.get("hs"),
        "origin": duty_engine.NAME_BY_CODE.get(p.get("exporter"), p.get("exporter")),
        "destination": duty_engine.NAME_BY_CODE.get(p.get("importer"), p.get("importer")),
        "pinned": bool(p.get("pinned")), "isTemplate": bool(p.get("isTemplate")),
        "status": p.get("status") or "active",
        "updatedAt": p.get("updatedAt"), "health": compute_health(p)["overall"],
        "summary": _summary(p),
    }


class ProjectIn(BaseModel):
    title: str = "Untitled Trade Project"
    product: str = ""
    hs: str = ""
    exporter: str = "356"
    importer: str = "842"
    incoterm: str = "FOB"
    quantity: float = 1
    unit: str = "unit"
    transactionCurrency: str = "USD"
    globalCurrency: str = "EUR"
    marginPct: float = 0
    buyer: str = ""
    supplier: str = ""
    paymentMethod: str = ""
    shipmentMode: str = "Sea FCL"
    containerType: str = ""
    costs: dict = Field(default_factory=dict)
    assumptions: dict = Field(default_factory=dict)
    notes: str = ""
    stage: str = "Created"
    isTemplate: bool = False


DEFAULT_ASSUMPTIONS = {"exchangeRate": "live", "freight": 0, "insurancePct": 0.2,
                       "marginPct": 0, "commissionPct": 0, "interestPct": 0, "containerCost": 0}


@router.get("")
async def list_projects(authorization: Optional[str] = Header(default=None),
                        x_trade_session: Optional[str] = Header(default=None)):
    owner, _t = _owner(authorization, x_trade_session)
    docs = await COL.find({"owner": owner}).sort("updatedAt", -1).to_list(200)
    return {"projects": [_card(d) for d in docs]}


@router.post("")
async def create_project(body: ProjectIn, authorization: Optional[str] = Header(default=None),
                         x_trade_session: Optional[str] = Header(default=None)):
    owner, otype = _owner(authorization, x_trade_session)
    pid = uuid.uuid4().hex
    doc = body.model_dump()
    doc.update({
        "_id": pid, "id": pid, "owner": owner, "ownerType": otype,
        "assumptions": {**DEFAULT_ASSUMPTIONS, **(doc.get("assumptions") or {})},
        "status": "active", "pinned": False, "lastQuote": None,
        "timeline": [{"at": _now(), "type": "created", "text": f"Project '{doc['title']}' created"}],
        "versions": [], "documents": [],
        "createdAt": _now(), "updatedAt": _now(),
    })
    await COL.insert_one(doc)
    return _public(doc)


@router.get("/templates")
async def templates():
    docs = await COL.find({"isTemplate": True}).limit(50).to_list(50)
    return {"templates": [_card(d) for d in docs]}


@router.get("/{pid}")
async def get_project(pid: str, authorization: Optional[str] = Header(default=None),
                      x_trade_session: Optional[str] = Header(default=None)):
    owner, _t = _owner(authorization, x_trade_session)
    doc = await COL.find_one({"_id": pid, "owner": owner})
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")
    return _public(doc)


class ProjectUpdate(BaseModel):
    patch: dict
    activity: Optional[str] = None


ALLOWED = {"title", "product", "hs", "exporter", "importer", "incoterm", "quantity", "unit",
           "transactionCurrency", "globalCurrency", "marginPct", "buyer", "supplier",
           "paymentMethod", "shipmentMode", "containerType", "costs", "assumptions",
           "notes", "stage", "lastQuote", "documents", "status", "isTemplate"}


@router.put("/{pid}")
async def update_project(pid: str, body: ProjectUpdate, authorization: Optional[str] = Header(default=None),
                         x_trade_session: Optional[str] = Header(default=None)):
    owner, _t = _owner(authorization, x_trade_session)
    doc = await COL.find_one({"_id": pid, "owner": owner})
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")
    patch = {k: v for k, v in (body.patch or {}).items() if k in ALLOWED}
    patch["updatedAt"] = _now()
    push = {}
    if body.activity:
        push["timeline"] = {"$each": [{"at": _now(), "type": "update", "text": body.activity}], "$slice": -100}
    update = {"$set": patch}
    if push:
        update["$push"] = push
    await COL.update_one({"_id": pid}, update)
    return _public(await COL.find_one({"_id": pid}))


@router.delete("/{pid}")
async def delete_project(pid: str, authorization: Optional[str] = Header(default=None),
                         x_trade_session: Optional[str] = Header(default=None)):
    owner, _t = _owner(authorization, x_trade_session)
    res = await COL.delete_one({"_id": pid, "owner": owner})
    return {"ok": res.deleted_count > 0}


@router.post("/{pid}/pin")
async def pin_project(pid: str, authorization: Optional[str] = Header(default=None),
                      x_trade_session: Optional[str] = Header(default=None)):
    owner, _t = _owner(authorization, x_trade_session)
    doc = await COL.find_one({"_id": pid, "owner": owner})
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")
    pinned = not bool(doc.get("pinned"))
    await COL.update_one({"_id": pid}, {"$set": {"pinned": pinned, "updatedAt": _now()}})
    return {"ok": True, "pinned": pinned}


@router.post("/{pid}/duplicate")
async def duplicate_project(pid: str, authorization: Optional[str] = Header(default=None),
                            x_trade_session: Optional[str] = Header(default=None)):
    owner, otype = _owner(authorization, x_trade_session)
    doc = await COL.find_one({"_id": pid, "owner": owner})
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")
    nid = uuid.uuid4().hex
    doc = {k: v for k, v in doc.items() if k != "_id"}
    doc.update({"_id": nid, "id": nid, "title": f"{doc.get('title','Project')} (copy)",
                "isTemplate": False, "pinned": False, "createdAt": _now(), "updatedAt": _now(),
                "timeline": [{"at": _now(), "type": "created", "text": "Duplicated from another project"}],
                "versions": []})
    await COL.insert_one(doc)
    return _public(doc)


class VersionIn(BaseModel):
    kind: str  # quote | report | calculation
    label: str = ""
    snapshot: dict = Field(default_factory=dict)


@router.post("/{pid}/version")
async def add_version(pid: str, body: VersionIn, authorization: Optional[str] = Header(default=None),
                      x_trade_session: Optional[str] = Header(default=None)):
    owner, _t = _owner(authorization, x_trade_session)
    doc = await COL.find_one({"_id": pid, "owner": owner})
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")
    v = {"id": uuid.uuid4().hex, "at": _now(), "kind": body.kind,
         "label": body.label or body.kind, "snapshot": body.snapshot}
    await COL.update_one({"_id": pid}, {
        "$push": {"versions": {"$each": [v], "$slice": -50},
                  "timeline": {"$each": [{"at": _now(), "type": body.kind, "text": f"{body.kind.title()} saved: {v['label']}"}], "$slice": -100}},
        "$set": {"updatedAt": _now()}})
    return {"ok": True, "version": v}


@router.post("/merge")
async def merge_guest(x_trade_session: Optional[str] = Header(default=None),
                      authorization: Optional[str] = Header(default=None)):
    """On login, move guest-session projects into the signed-in account."""
    token = _bearer(authorization)
    claims = verify_token(token) if token else None
    if not claims or not claims.get("uid"):
        raise HTTPException(status_code=401, detail="Sign in required to merge")
    if not x_trade_session:
        return {"ok": True, "merged": 0}
    uid = claims["uid"]
    res = await COL.update_many({"owner": x_trade_session, "ownerType": "guest"},
                                {"$set": {"owner": uid, "ownerType": "uid", "updatedAt": _now()}})
    logging.info("Merged %d guest projects into uid %s", res.modified_count, uid)
    return {"ok": True, "merged": res.modified_count}
