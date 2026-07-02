"""Simulation Engine + Scenario Builder — deterministic maths on the backend.

Scenarios live in their OWN collection (`trade_project_scenarios`), linked to a Trade
Project — never embedded in the project document. Each scenario is a versioned what-if
with inputs, deterministic outputs (costing), scores and a consolidated decision object.
The Digital Twin (`/twin`) recomputes everything instantly for any variable change
without saving. Monte-Carlo / sensitivity land in Phase 2B on this same spine.

The Brain only explains/interprets these results — it never computes them here.
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from core import db
from projects import _owner, COL
from costing_engine import compute_quote, QuoteRequest, CostInputs
from scores import compute_scores
from decision_engine import build_decision
import events

router = APIRouter(prefix="/simulation")
SCN = db.trade_project_scenarios

COST_KEYS = ["exw", "packing", "inland", "thc", "customsDocs", "freight", "insurance"]


def _now():
    return datetime.now(timezone.utc).isoformat()


def _quote_req(inputs: Dict[str, Any]) -> QuoteRequest:
    costs = inputs.get("costs") or {}
    return QuoteRequest(
        hs=inputs.get("hs", ""), product=inputs.get("product", ""),
        exporter=inputs.get("exporter", "356"), importer=inputs.get("importer", "842"),
        quantity=inputs.get("quantity", 1) or 1, unit=inputs.get("unit", "unit"),
        costs=CostInputs(**{k: costs.get(k, 0) for k in COST_KEYS}),
        marginPct=inputs.get("marginPct", 0),
        transactionCurrency=inputs.get("transactionCurrency", "USD"),
        globalCurrency=inputs.get("globalCurrency", "USD"))


def _summary(q: Dict[str, Any]) -> Dict[str, Any]:
    dest = q.get("destination") or {}
    pricing = q.get("pricing") or {}
    comp = q.get("comparison") or []
    return {
        "fob": (q.get("fob") or {}).get("total"),
        "cif": (q.get("cif") or {}).get("total"),
        "landed": dest.get("landed"),
        "selling": pricing.get("selling"),
        "profit": pricing.get("profit"),
        "marginPct": pricing.get("marginPct"),
        "dutyRate": dest.get("dutyRate"),
        "vatRate": dest.get("vatRate"),
        "currency": (q.get("currency") or {}).get("transaction"),
        "bestMarket": (comp[0] if comp else None),
    }


def _confidence(inputs: Dict[str, Any], q: Dict[str, Any]) -> float:
    costs = inputs.get("costs") or {}
    costed = sum(float(costs.get(k, 0) or 0) for k in COST_KEYS) > 0
    duty_known = (q.get("destination") or {}).get("dutyRate") is not None
    return round(min(0.95, 0.4 + (0.3 if costed else 0) + (0.25 if duty_known else 0)), 2)


async def _compute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Digital Twin core: instant deterministic recompute for a set of inputs."""
    q = await compute_quote(_quote_req(inputs))
    scores = compute_scores(inputs, q)
    decision = build_decision(inputs, q, scores)
    return {"quote": q, "summary": _summary(q), "scores": scores, "decision": decision,
            "confidence": _confidence(inputs, q)}


def _pub(s: dict) -> dict:
    return {k: v for k, v in s.items() if k != "_id"}


# ---------------- Digital Twin (what-if, no save) ----------------
class TwinIn(BaseModel):
    inputs: Dict[str, Any] = Field(default_factory=dict)


@router.post("/twin")
async def twin(body: TwinIn):
    out = await _compute(body.inputs)
    return {"ok": bool(out["quote"].get("ok")), **out}


# ---------------- Scenario Builder ----------------
class ScenarioIn(BaseModel):
    projectId: str
    label: str = ""
    inputs: Dict[str, Any] = Field(default_factory=dict)
    assumptions: Dict[str, Any] = Field(default_factory=dict)
    parentId: Optional[str] = None


async def _owned_project(pid: str, owner: str):
    doc = await COL.find_one({"_id": pid, "owner": owner})
    if not doc:
        raise HTTPException(404, "Project not found")
    return doc


def _inputs_from_project(p: dict) -> Dict[str, Any]:
    return {k: p.get(k) for k in ("hs", "product", "exporter", "importer", "incoterm", "quantity",
                                  "unit", "marginPct", "transactionCurrency", "globalCurrency",
                                  "paymentMethod", "buyer", "supplier", "shipmentMode", "containerType",
                                  "documents")} | {"costs": p.get("costs") or {}}


@router.post("/scenarios")
async def create_scenario(body: ScenarioIn, authorization: Optional[str] = Header(default=None),
                          x_trade_session: Optional[str] = Header(default=None)):
    owner, otype = _owner(authorization, x_trade_session)
    proj = await _owned_project(body.projectId, owner)
    inputs = body.inputs or _inputs_from_project(proj)
    n = await SCN.count_documents({"projectId": body.projectId, "owner": owner})
    label = body.label or f"Scenario {chr(65 + min(n, 25))}"
    out = await _compute(inputs)
    sid = uuid.uuid4().hex
    doc = {
        "_id": sid, "id": sid, "projectId": body.projectId, "owner": owner, "createdBy": otype,
        "parentId": body.parentId, "version": 1, "label": label, "archived": False,
        "assumptions": body.assumptions or (proj.get("assumptions") or {}),
        "inputs": inputs, "outputs": out["summary"], "quote": out["quote"],
        "simulation": {}, "scores": out["scores"], "decision": out["decision"],
        "risk": out["scores"].get("risk", {}).get("value"),
        "profit": out["summary"].get("profit"), "market": out["summary"].get("bestMarket"),
        "compliance": out["scores"].get("compliance", {}).get("value"),
        "executiveSummary": "", "brainAnalysis": "", "confidence": out["confidence"],
        "createdAt": _now(), "updatedAt": _now(),
    }
    await SCN.insert_one(doc)
    await events.log_event(body.projectId, owner, "scenario_created", f"Scenario '{label}' created", {"scenarioId": sid})
    return _pub(doc)


@router.get("/scenarios")
async def list_scenarios(projectId: str, includeArchived: bool = False,
                         authorization: Optional[str] = Header(default=None),
                         x_trade_session: Optional[str] = Header(default=None)):
    owner, _t = _owner(authorization, x_trade_session)
    query = {"projectId": projectId, "owner": owner}
    if not includeArchived:
        query["archived"] = {"$ne": True}
    docs = await SCN.find(query).sort("createdAt", 1).to_list(100)
    return {"scenarios": [_pub(d) for d in docs]}


@router.get("/scenarios/{sid}")
async def get_scenario(sid: str, authorization: Optional[str] = Header(default=None),
                       x_trade_session: Optional[str] = Header(default=None)):
    owner, _t = _owner(authorization, x_trade_session)
    doc = await SCN.find_one({"_id": sid, "owner": owner})
    if not doc:
        raise HTTPException(404, "Scenario not found")
    return _pub(doc)


class ScenarioPatch(BaseModel):
    label: Optional[str] = None
    inputs: Optional[Dict[str, Any]] = None
    assumptions: Optional[Dict[str, Any]] = None
    archived: Optional[bool] = None


@router.put("/scenarios/{sid}")
async def update_scenario(sid: str, body: ScenarioPatch, authorization: Optional[str] = Header(default=None),
                          x_trade_session: Optional[str] = Header(default=None)):
    owner, _t = _owner(authorization, x_trade_session)
    doc = await SCN.find_one({"_id": sid, "owner": owner})
    if not doc:
        raise HTTPException(404, "Scenario not found")
    patch: Dict[str, Any] = {"updatedAt": _now()}
    if body.label is not None:
        patch["label"] = body.label
    if body.assumptions is not None:
        patch["assumptions"] = body.assumptions
    if body.archived is not None:
        patch["archived"] = body.archived
        if body.archived:
            await events.log_event(doc["projectId"], owner, "scenario_archived", f"Scenario '{doc.get('label')}' archived", {"scenarioId": sid})
    if body.inputs is not None:
        out = await _compute(body.inputs)
        patch.update({"inputs": body.inputs, "outputs": out["summary"], "quote": out["quote"],
                      "scores": out["scores"], "decision": out["decision"], "confidence": out["confidence"],
                      "risk": out["scores"].get("risk", {}).get("value"), "profit": out["summary"].get("profit"),
                      "market": out["summary"].get("bestMarket"), "compliance": out["scores"].get("compliance", {}).get("value"),
                      "version": (doc.get("version") or 1) + 1})
        await events.log_event(doc["projectId"], owner, "scenario_updated", f"Scenario '{doc.get('label')}' recomputed (v{patch['version']})", {"scenarioId": sid})
    await SCN.update_one({"_id": sid}, {"$set": patch})
    return _pub(await SCN.find_one({"_id": sid}))


@router.post("/scenarios/{sid}/duplicate")
async def duplicate_scenario(sid: str, authorization: Optional[str] = Header(default=None),
                             x_trade_session: Optional[str] = Header(default=None)):
    owner, _t = _owner(authorization, x_trade_session)
    doc = await SCN.find_one({"_id": sid, "owner": owner})
    if not doc:
        raise HTTPException(404, "Scenario not found")
    nid = uuid.uuid4().hex
    nd = {k: v for k, v in doc.items() if k != "_id"}
    nd.update({"_id": nid, "id": nid, "parentId": sid, "version": 1,
               "label": f"{doc.get('label', 'Scenario')} (copy)", "archived": False,
               "createdAt": _now(), "updatedAt": _now()})
    await SCN.insert_one(nd)
    await events.log_event(doc["projectId"], owner, "scenario_created", f"Duplicated '{doc.get('label')}'", {"scenarioId": nid, "parentId": sid})
    return _pub(nd)


class MergeIn(BaseModel):
    projectId: str
    ids: List[str]
    label: str = "Merged Scenario"


@router.post("/scenarios/merge")
async def merge_scenarios(body: MergeIn, authorization: Optional[str] = Header(default=None),
                          x_trade_session: Optional[str] = Header(default=None)):
    owner, otype = _owner(authorization, x_trade_session)
    docs = await SCN.find({"_id": {"$in": body.ids}, "owner": owner}).to_list(50)
    if len(docs) < 2:
        raise HTTPException(400, "Select at least two scenarios to merge")
    # Merge = best-of: pick the winning scenario per objective, blend its inputs as the base.
    best = max(docs, key=lambda d: (d.get("scores", {}).get("overall", {}).get("value") or 0))
    inputs = dict(best.get("inputs") or {})
    # Take the lowest freight+insurance across scenarios (best logistics), highest margin.
    best_costs = dict(inputs.get("costs") or {})
    for d in docs:
        c = (d.get("inputs") or {}).get("costs") or {}
        for k in ("freight", "insurance"):
            if c.get(k) is not None and (best_costs.get(k) is None or c[k] < best_costs.get(k, 1e18)):
                best_costs[k] = c[k]
    inputs["costs"] = best_costs
    inputs["marginPct"] = max((float((d.get("inputs") or {}).get("marginPct") or 0)) for d in docs)
    out = await _compute(inputs)
    nid = uuid.uuid4().hex
    doc = {"_id": nid, "id": nid, "projectId": body.projectId, "owner": owner, "createdBy": otype,
           "parentId": None, "mergedFrom": body.ids, "version": 1, "label": body.label, "archived": False,
           "assumptions": best.get("assumptions") or {}, "inputs": inputs, "outputs": out["summary"],
           "quote": out["quote"], "simulation": {}, "scores": out["scores"], "decision": out["decision"],
           "risk": out["scores"].get("risk", {}).get("value"), "profit": out["summary"].get("profit"),
           "market": out["summary"].get("bestMarket"), "compliance": out["scores"].get("compliance", {}).get("value"),
           "executiveSummary": "", "brainAnalysis": "", "confidence": out["confidence"],
           "createdAt": _now(), "updatedAt": _now()}
    await SCN.insert_one(doc)
    await events.log_event(body.projectId, owner, "scenario_merged", f"Merged {len(body.ids)} scenarios → '{body.label}'", {"scenarioId": nid, "from": body.ids})
    return _pub(doc)


@router.delete("/scenarios/{sid}")
async def delete_scenario(sid: str, authorization: Optional[str] = Header(default=None),
                          x_trade_session: Optional[str] = Header(default=None)):
    owner, _t = _owner(authorization, x_trade_session)
    doc = await SCN.find_one({"_id": sid, "owner": owner})
    res = await SCN.delete_one({"_id": sid, "owner": owner})
    if doc:
        await events.log_event(doc["projectId"], owner, "scenario_archived", f"Scenario '{doc.get('label')}' deleted", {"scenarioId": sid})
    return {"ok": res.deleted_count > 0}


class CompareIn(BaseModel):
    projectId: str
    ids: Optional[List[str]] = None


@router.post("/compare")
async def compare(body: CompareIn, authorization: Optional[str] = Header(default=None),
                  x_trade_session: Optional[str] = Header(default=None)):
    owner, _t = _owner(authorization, x_trade_session)
    query = {"projectId": body.projectId, "owner": owner, "archived": {"$ne": True}}
    if body.ids:
        query = {"_id": {"$in": body.ids}, "owner": owner}
    docs = await SCN.find(query).sort("createdAt", 1).to_list(50)
    rows = []
    for d in docs:
        rows.append({"id": d["id"], "label": d.get("label"), "version": d.get("version"),
                     "summary": d.get("outputs"), "scores": {k: (v or {}).get("value") if isinstance(v, dict) else v for k, v in (d.get("scores") or {}).items()},
                     "confidence": d.get("confidence"), "overall": (d.get("scores", {}).get("overall", {}) or {}).get("value")})
    # Winner per metric
    def _best(metric, hi=True, path=("summary",)):
        vals = [(r["id"], (r["summary"] or {}).get(metric)) for r in rows]
        vals = [(i, v) for i, v in vals if v is not None]
        if not vals:
            return None
        return (max if hi else min)(vals, key=lambda x: x[1])[0]
    winners = {"profit": _best("profit", True), "landed": _best("landed", False),
               "selling": _best("selling", False), "margin": _best("marginPct", True),
               "overall": (max(rows, key=lambda r: r.get("overall") or 0)["id"] if rows else None)}
    await events.log_event(body.projectId, owner, "scenario_compared", f"Compared {len(rows)} scenarios", {})
    return {"ok": True, "rows": rows, "winners": winners}
