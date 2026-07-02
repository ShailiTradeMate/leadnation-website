"""Decision Engine — the layer BETWEEN the Simulation Engine and the Brain.

It consolidates deterministic outputs (costing, scores, market comparison, risk) into
structured "decision objects" with a verdict, signal and evidence per domain. The Brain
reasons over these structured objects — never over raw numbers — so the Brain stays an
interpreter/advisor and the platform stays testable and extensible.

Flow:  Trade Project → Reactive Graph → Simulation Engine → Decision Engine → Brain → Report
"""
import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Header
from pydantic import BaseModel

from core import db
from projects import _owner, COL
from costing_engine import compute_quote, QuoteRequest, CostInputs
from scores import compute_scores
from brain.providers import get_provider
import events

router = APIRouter(prefix="/decision")


def _verdict(v: float) -> str:
    return "strong" if v >= 70 else ("moderate" if v >= 45 else "weak")


def build_decision(project: Dict[str, Any], quote: Dict[str, Any], scores: Dict[str, Any]) -> Dict[str, Any]:
    q = quote or {}
    comp = q.get("comparison") or []
    dest = q.get("destination") or {}
    pricing = q.get("pricing") or {}
    txn = (q.get("currency") or {}).get("transaction", "")
    best = comp[0] if comp else None

    def obj(domain, score_key, signal, evidence):
        s = scores.get(score_key, {})
        return {"domain": domain, "score": s.get("value"), "color": s.get("color"),
                "verdict": _verdict(s.get("value", 0)), "signal": signal, "evidence": evidence}

    objects = [
        obj("profitability", "profitability",
            f"Margin {pricing.get('marginPct', 0)}% → profit {pricing.get('profit')} {txn}",
            {"selling": pricing.get("selling"), "profit": pricing.get("profit"), "marginPct": pricing.get("marginPct")}),
        obj("risk", "risk", f"Payment: {project.get('paymentMethod') or 'not set'}; Incoterm {project.get('incoterm')}",
            {"paymentMethod": project.get("paymentMethod"), "incoterm": project.get("incoterm")}),
        obj("compliance", "compliance",
            f"Duty {dest.get('dutyRate')}% {dest.get('dutyType') or ''}{' · FTA' if dest.get('fta') else ''}",
            {"dutyRate": dest.get("dutyRate"), "fta": dest.get("fta"), "documents": len(project.get("documents") or [])}),
        obj("buyer", "buyer", project.get("buyer") or "No buyer linked", {"buyer": project.get("buyer")}),
        obj("logistics", "market", f"Best market: {best['country'] if best else '—'}",
            {"bestMarket": best, "routes": q.get("routes")}),
        obj("market", "competition",
            f"{len(comp)} markets compared" if comp else "No comparison yet", {"comparison": comp[:5]}),
    ]

    # Deterministic candidate actions (the Brain will prioritise & explain these).
    actions: List[dict] = []
    imp_code = (q.get("importer") or {}).get("code")
    if best and imp_code and best.get("code") != imp_code:
        actions.append({"type": "market", "priority": "high",
                        "title": f"Consider {best['country']} — lowest buyer landed cost",
                        "detail": f"Buyer total {best.get('buyerTotal')} {txn}" + (" (FTA)" if best.get("fta") else "")})
    if (pricing.get("marginPct") or 0) < 12:
        actions.append({"type": "pricing", "priority": "medium",
                        "title": "Margin below 12% — review pricing",
                        "detail": "Raise selling price or reduce landed cost to reach a healthier margin."})
    if not dest.get("fta") and dest.get("dutyRate"):
        actions.append({"type": "compliance", "priority": "medium",
                        "title": "Check FTA / preferential origin eligibility",
                        "detail": f"MFN duty is {dest.get('dutyRate')}%. A qualifying origin could cut this."})
    if (project.get("paymentMethod") or "").lower() in ("", "open account", "da"):
        actions.append({"type": "risk", "priority": "high",
                        "title": "De-risk payment terms",
                        "detail": "Move toward advance payment or an LC to lower buyer-default risk."})

    overall = scores.get("overall", {})
    confidence = round(min(0.95, 0.5 + (0.4 if q.get("ok") else 0) + (0.05 if comp else 0)), 2)
    return {"objects": objects, "bestMarket": best, "recommendedActions": actions,
            "overallVerdict": _verdict(overall.get("value", 0)),
            "overallScore": overall.get("value"), "confidence": confidence,
            "dataSources": q.get("sources", [])}


async def _project_and_quote(pid: str, owner: str):
    doc = await COL.find_one({"_id": pid, "owner": owner})
    if not doc:
        return None, None
    q = doc.get("lastQuote")
    if not q or not q.get("ok"):
        req = QuoteRequest(hs=doc.get("hs", ""), product=doc.get("product", ""),
                           exporter=doc.get("exporter", "356"), importer=doc.get("importer", "842"),
                           quantity=doc.get("quantity", 1), unit=doc.get("unit", "unit"),
                           costs=CostInputs(**{k: (doc.get("costs") or {}).get(k, 0) for k in ["exw", "packing", "inland", "thc", "customsDocs", "freight", "insurance"]}),
                           marginPct=doc.get("marginPct", 0),
                           transactionCurrency=doc.get("transactionCurrency", "USD"),
                           globalCurrency=doc.get("globalCurrency", "USD"))
        q = await compute_quote(req)
    return doc, q


class DecisionIn(BaseModel):
    projectId: str


@router.post("")
async def decision(body: DecisionIn, authorization: Optional[str] = Header(default=None),
                   x_trade_session: Optional[str] = Header(default=None)):
    owner, _t = _owner(authorization, x_trade_session)
    doc, q = await _project_and_quote(body.projectId, owner)
    if not doc:
        return {"ok": False, "error": "Project not found"}
    scores = compute_scores(doc, q)
    dec = build_decision(doc, q, scores)
    await events.log_event(body.projectId, owner, "decision_computed",
                           f"Decision engine evaluated ({dec['overallVerdict']})", {"score": dec.get("overallScore")})
    return {"ok": True, "scores": scores, "decision": dec}


@router.post("/recommendations")
async def recommendations(body: DecisionIn, authorization: Optional[str] = Header(default=None),
                          x_trade_session: Optional[str] = Header(default=None)):
    owner, _t = _owner(authorization, x_trade_session)
    doc, q = await _project_and_quote(body.projectId, owner)
    if not doc:
        return {"ok": False, "error": "Project not found"}
    scores = compute_scores(doc, q)
    dec = build_decision(doc, q, scores)

    # Brain reasons over STRUCTURED decision objects — it must not fabricate numbers.
    exp = (q.get("exporter") or {}).get("name", "")
    imp = (q.get("importer") or {}).get("name", "")
    desc = q.get("description", "")
    eo = {
        "decision_objects": {"summary": "; ".join(f"{o['domain']}: {o['verdict']} ({o['score']}/100) — {o['signal']}" for o in dec["objects"]), "data": dec["objects"]},
        "candidate_actions": {"summary": "; ".join(f"[{a['priority']}] {a['title']}" for a in dec["recommendedActions"]) or "none", "data": dec["recommendedActions"]},
        "scores": {"summary": f"Overall trade health {scores['overall']['value']}/100 ({dec['overallVerdict']}).", "data": {}},
    }
    question = (
        f"You are the LeadNation Brain — the orchestration & advisory layer of a Trade Command Center. "
        f"You are given STRUCTURED decision objects and candidate actions for exporting {desc} from {exp} to {imp}. "
        f"Do NOT invent or recompute any numbers — only use the figures provided. Produce concise markdown with: "
        f"(1) a 2-line Executive Summary of this trade's health, (2) the top 3 prioritised Recommendations "
        f"(reference the candidate actions, explain WHY using the evidence), (3) a short Action Plan (numbered next steps). "
        f"Be specific and decisive."
    )
    advisor = ""
    try:
        provider = get_provider()
        res = await provider.generate(question, {"primary": "decision"},
                                      {"products": [desc], "countries": [exp, imp], "hsn": [q.get("hsCode", "")]},
                                      eo, {"retrieved": [], "memory": {}, "user": {}, "language": "en"})
        advisor = res.get("answer", "")
    except Exception as exc:
        logging.warning("Decision recommendations failed: %s", exc)

    await events.log_event(body.projectId, owner, "brain_recommendation",
                           "Brain generated recommendations & action plan", {})
    try:
        await db.trade_project_brain_history.insert_one({
            "projectId": body.projectId, "owner": owner, "kind": "recommendations",
            "advisor": advisor, "at": events._now()})
    except Exception:
        pass
    return {"ok": True, "scores": scores, "decision": dec, "recommendations": advisor}
