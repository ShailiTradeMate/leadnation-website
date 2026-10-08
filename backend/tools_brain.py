"""Brain Next Steps — one endpoint that turns any tool result into (a) a short AI read of
the user's own numbers and (b) deterministic, pre-filled links to the logical next tool.
Links are always returned even when the LLM is slow or unavailable."""
import asyncio
import json
import logging
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter
from pydantic import BaseModel

import duty_engine
import llm_util

router = APIRouter(prefix="/tools", tags=["tools-brain"])

CODE_BY_NAME = {n.lower(): c for c, n in duty_engine.COUNTRIES}


def _name(code: str) -> str:
    return duty_engine.NAME_BY_CODE.get(str(code or ""), "")


def _code_from_name(name: str) -> str:
    return CODE_BY_NAME.get((name or "").lower(), "")


def _export_page(hs6: str, dest_code: str) -> Optional[str]:
    try:
        import seo_pages
    except Exception:
        return None
    pslug = next((s for s, p in seo_pages.PRODUCTS.items() if hs6 in p["hs"]), None)
    c = seo_pages.COUNTRY_BY_CODE.get(str(dest_code or "").lstrip("0"))
    if pslug and c and dest_code != seo_pages.INDIA:
        return f"/export/{pslug}/to/{c['slug']}"
    return None


def _step(label, to, why, kind="tool"):
    return {"label": label, "to": to, "why": why, "kind": kind}


def _common(hs6, origin, dest, product=""):
    dn, on = _name(dest), _name(origin)
    q = f"hs={hs6}" if hs6 else ""
    lane = f"&from={origin}&to={dest}" if (origin or dest) else ""
    steps = []
    if hs6:
        steps.append(_step(f"Build landed cost in {dn or 'destination'} (Command Center)",
                           f"/tools/landed-cost-calculator?{q}{lane}",
                           "Turn the duty rate into a full FOB → CIF → landed quote with FX."))
    if dn:
        steps.append(_step(f"Find verified buyers in {dn}", f"/buyers?hs={hs6}&country={quote(dn)}",
                           "Real importer records with trust scores for this market.", "buyers"))
    if hs6:
        steps.append(_step(f"World demand for HS {hs6}", f"/tools/product-research?hs={hs6}",
                           "Top importing countries, world trade value and multi-year trend."))
    ep = _export_page(hs6, dest)
    if ep:
        steps.append(_step(f"{on or 'India'} → {dn} export guide", ep,
                           "Documents, certifications, FTA status and buyer coverage for this exact lane.", "guide"))
    return steps


def _brain(q):
    return _step("Ask the Brain for a full plan", f"/brain?q={quote(q)}",
                 "A written export plan: duty, documents, pricing, buyers, risks.", "brain")


def deterministic_steps(tool: str, inputs: dict, result: dict):
    hs6 = str(inputs.get("hs") or result.get("hsCode") or "")[:6]
    origin = str(inputs.get("origin") or inputs.get("exporter") or "")
    dest = str(inputs.get("destination") or inputs.get("importer") or "")
    product = inputs.get("product") or result.get("description") or ""
    steps = []

    if tool == "duty":
        steps = _common(hs6, origin, dest, product)
        steps.append(_brain(f"Duty, documents and savings plan for HS {hs6} from {_name(origin) or 'India'} to {_name(dest)}"))

    elif tool == "trade-stats":
        top = (result.get("topImporters") or [{}])[0]
        top_code = _code_from_name(top.get("country", ""))
        if top_code:
            steps.append(_step(f"Check import duty into {top.get('country')} (#1 importer)",
                               f"/tools/duty-calculator?hs={hs6}&from=356&to={top_code}",
                               "The biggest market first — see MFN and preferential rates."))
            steps.append(_step(f"Find buyers in {top.get('country')}",
                               f"/buyers?hs={hs6}&country={quote(top.get('country'))}",
                               "Importer records for the market with the highest demand.", "buyers"))
        steps.append(_step("Cost a shipment to the best market",
                           f"/tools/landed-cost-calculator?hs={hs6}&from=356&to={top_code or '784'}",
                           "Compare buyer landed cost across markets in one run."))
        ep = _export_page(hs6, top_code)
        if ep:
            steps.append(_step(f"India → {top.get('country')} export guide", ep, "Lane-specific documents and compliance.", "guide"))
        steps.append(_brain(f"Full trade analysis for HS {hs6} ({product}) — demand, top markets and opportunities"))

    elif tool == "command-center":
        dn = _name(dest)
        comp = result.get("comparison") or []
        best = comp[0] if comp else None
        if dn:
            steps.append(_step(f"Find buyers in {dn}", f"/buyers?hs={hs6}&country={quote(dn)}",
                               "You know your landed price — now find who imports it.", "buyers"))
        if best and best.get("code") and str(best.get("code")) != dest:
            steps.append(_step(f"Cheapest market for your buyer: {best.get('country')}",
                               f"/tools/landed-cost-calculator?hs={hs6}&from={origin}&to={best.get('code')}",
                               "Re-run the quote where your buyer pays the least."))
        steps.append(_step("Save this as a Trade Project", "/command-center",
                           "Compliance checklist, documents and PDF report in the full workspace.", "workspace"))
        ep = _export_page(hs6, dest)
        if ep:
            steps.append(_step(f"{_name(origin) or 'India'} → {dn} export guide", ep, "Documents, FTA and certifications for this lane.", "guide"))
        steps.append(_brain(f"Full export plan for HS {hs6} ({product}) from {_name(origin)} to {dn}"))

    elif tool == "hsn":
        o, dd = origin or "356", dest or "784"
        on, dn = _name(o), _name(dd)
        steps.append(_step(f"Full duty & FTA check: {on} → {dn}", f"/tools/duty-calculator?hs={hs6}&from={o}&to={dd}",
                           f"MFN and preferential rates into {dn}" + (" + RoDTEP export benefit." if o == "356" else ".")))
        steps.append(_step(f"World demand for HS {hs6}", f"/tools/product-research?hs={hs6}",
                           "Who imports it, how much and the 5-year trend."))
        steps.append(_step(f"Cost a shipment to {dn} (Command Center)", f"/tools/landed-cost-calculator?hs={hs6}&from={o}&to={dd}",
                           "FOB → CIF → landed with duty, VAT and FX."))
        steps.append(_step(f"Find buyers in {dn}" if dn else "Find buyers for this HS code",
                           f"/buyers?hs={hs6}&country={quote(dn)}" if dn else f"/buyers?hs={hs6}", "Importer records matched to the HS family.", "buyers"))
        ep = _export_page(hs6, dd) if o == "356" else None
        if ep:
            steps.append(_step(f"India → {dn} export guide", ep, "Documents, certifications and FTA status for this lane.", "guide"))
        steps.append(_brain(f"Export documents, certifications, duty and best buyers for HS {hs6} ({product}) from {on} to {dn}"))

    elif tool == "readiness":
        score = int(result.get("score") or 0)
        if score < 40:
            steps.append(_step("Start with Export Academy basics", "/academy", "IEC, GST, first shipment — step by step.", "learn"))
            steps.append(_step("Classify your product (HSN Finder)", "/tools/hsn-finder", "Every duty, benefit and document starts with the right HS code."))
        elif score < 75:
            steps.append(_step("Check duty & RoDTEP for your product", "/tools/duty-calculator", "See what your buyer pays and what DGFT refunds you."))
            steps.append(_step("Get export-ready with Vametra services", "/services", "Certifications, documentation and compliance support.", "service"))
        else:
            steps.append(_step("Find verified buyers now", "/buyers", "You're export-ready — go straight to real importers.", "buyers"))
            steps.append(_step("Cost your first quote (Command Center)", "/tools/landed-cost-calculator", "FOB → CIF → landed, in your currency and the buyer's."))
        steps.append(_step("Upcoming trade expos", "/expo", "Meet buyers in person at the right fairs.", "expo"))
        steps.append(_brain(f"I scored {score}/100 on export readiness. Give me a 90-day plan to my first shipment."))

    elif tool == "buyers":
        dn = _name(dest)
        if hs6 and dest:
            steps.append(_step(f"Import duty into {dn}", f"/tools/duty-calculator?hs={hs6}&from=356&to={dest}",
                               "Know the tariff before you quote these buyers."))
            steps.append(_step(f"Quote for {dn} (Command Center)", f"/tools/landed-cost-calculator?hs={hs6}&from=356&to={dest}",
                               "Landed price your buyer will actually pay."))
        ep = _export_page(hs6, dest)
        if ep:
            steps.append(_step(f"India → {dn} export guide", ep, "Documents and compliance for this lane.", "guide"))
        steps.append(_step("Open full Buyer Intelligence", f"/buyers?hs={hs6}&country={quote(dn)}" if dn else "/buyers",
                           "Trust scores, evidence, watchlists and contact unlock.", "buyers"))
        steps.append(_brain(f"How do I approach importers of HS {hs6} in {dn or 'this market'}? Give me an outreach plan."))

    elif tool == "incentives":
        steps = _common(hs6, origin or "356", dest, product)
        steps.append(_brain(f"All export incentives and schemes for HS {hs6} shipped from India to {_name(dest)}"))

    if not steps:
        steps = [_step("Open the Customs & Compliance Engine", "/customs-compliance", "Duty, trade stats, FX, CBM and routes in one place."), _brain("Help me plan my next export shipment")]
    return steps[:5]


SYSTEM = ("You are the Vametra AI Brain, a senior export-import advisor. Write 2–3 crisp sentences that read the "
          "user's OWN numbers back to them (quote the actual figures given), say what they mean for the deal, and "
          "name the single most valuable next action. Never invent figures that are not in the data. Write numbers plainly "
          "(5%, $1.2B) without quotation marks. No greetings, no markdown headings, no bullet points.")


async def ai_insight(tool: str, inputs: dict, result: dict, steps: list) -> Optional[str]:
    readable = dict(inputs)
    for k in ("origin", "exporter"):
        if readable.get(k):
            readable[k] = _name(readable[k]) or readable[k]
    for k in ("destination", "importer"):
        if readable.get(k):
            readable[k] = _name(readable[k]) or readable[k]
    slim = json.dumps({"tool": tool, "inputs": readable, "result": result}, default=str)[:6000]
    prompt = (f"Tool data (duty/benefit 'rate' values are percentages; money values are in the stated currency or USD; "
              f"country names are already resolved — never mention numeric country codes):\n{slim}\n\n"
              f"Suggested next action: {steps[0]['label'] if steps else 'n/a'}.\n"
              "Return JSON: {\"insight\": \"...\"}")
    try:
        out = await asyncio.wait_for(llm_util.generate_json(SYSTEM, prompt, session=f"tools-{tool}"), timeout=18)
    except Exception as exc:
        logging.warning("tools next-steps insight failed: %s", exc)
        return None
    if isinstance(out, dict) and out.get("insight"):
        return str(out["insight"]).strip()
    return None


def fallback_insight(tool: str, inputs: dict, result: dict) -> str:
    hs6 = str(inputs.get("hs") or result.get("hsCode") or "")[:6]
    dn = _name(inputs.get("destination") or inputs.get("importer") or "")
    if tool == "duty" and result.get("importDuty"):
        d = result["importDuty"]
        pref = result.get("preferential")
        s = f"Import duty into {dn} for HS {hs6} is {d.get('rate')}% ({d.get('type')}, {d.get('year')} data)."
        if pref:
            s += f" A preferential {pref.get('rate')}% rate exists for your origin — a certificate of origin unlocks it."
        if result.get("exportBenefit"):
            s += f" RoDTEP refunds {result['exportBenefit'].get('rate')}% of FOB on the Indian side."
        return s + " Next: turn this into a landed-cost quote."
    if tool == "trade-stats" and result.get("topImporters"):
        t = result["topImporters"][0]
        return (f"World imports of HS {hs6} were about ${float(result.get('totalWorldTradeUSD') or 0)/1e9:.1f}B in "
                f"{result.get('year')}; {t.get('country')} is the largest buyer. Check its duty next.")
    if tool == "readiness":
        return f"You scored {result.get('score')}/100 — {result.get('band')}. Follow the roadmap below in order."
    return "Here are the most valuable next actions for this result."


class NextStepsReq(BaseModel):
    tool: str
    inputs: dict = {}
    result: dict = {}
    ai: bool = True


@router.post("/next-steps")
async def next_steps(req: NextStepsReq):
    steps = deterministic_steps(req.tool, req.inputs or {}, req.result or {})
    insight = await ai_insight(req.tool, req.inputs or {}, req.result or {}, steps) if req.ai else None
    return {
        "ok": True, "tool": req.tool, "aiGenerated": bool(insight),
        "insight": insight or fallback_insight(req.tool, req.inputs or {}, req.result or {}),
        "nextSteps": steps,
        "upgrade": {"label": "Unlock unlimited Brain plans, buyer contacts & PDF reports", "to": "/pricing"},
    }
