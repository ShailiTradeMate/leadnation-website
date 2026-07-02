"""Trade Score Engine — deterministic, fully explainable scores.

The Brain NEVER computes these numbers; it only explains them. Each score returns a
0-100 value, a colour band and a list of factors (what pushed it up/down) plus a plain
explanation, so the UI and PDF can show *why* every score is what it is.
"""
from typing import Dict, Any, List


def _band(v: float):
    v = max(0, min(100, round(v)))
    color = "emerald" if v >= 70 else ("amber" if v >= 40 else "rose")
    return v, color


def _score(label: str, value: float, factors: List[dict], explanation: str) -> dict:
    v, color = _band(value)
    return {"label": label, "value": v, "color": color, "factors": factors, "explanation": explanation}


PAY_RISK = {"advance": 90, "lc": 78, "letter of credit": 78, "cad": 60, "dp": 55, "da": 50, "open account": 30}


def compute_scores(project: Dict[str, Any], quote: Dict[str, Any]) -> Dict[str, Any]:
    q = quote or {}
    pricing = q.get("pricing") or {}
    dest = q.get("destination") or {}
    comp = q.get("comparison") or []
    margin = float(project.get("marginPct") or pricing.get("marginPct") or 0)
    pay = (project.get("paymentMethod") or "").lower()
    incoterm = (project.get("incoterm") or "").upper()
    docs = project.get("documents") or []
    duty_known = dest.get("dutyRate") is not None
    fta = bool(dest.get("fta"))
    importer_code = (q.get("importer") or {}).get("code")

    # Profitability
    prof_f = [{"label": f"Margin {margin:.1f}%", "impact": "+" if margin >= 12 else "-",
               "detail": "Healthy" if margin >= 12 else "Below a typical 12% export margin"}]
    if pricing.get("profit") is not None:
        prof_f.append({"label": f"Profit {pricing.get('profit')} {q.get('currency', {}).get('transaction', '')}", "impact": "+", "detail": "Absolute profit on CIF basis"})
    profitability = _score("Profitability", min(100, margin * 4),
                           prof_f, f"Driven by your {margin:.1f}% margin on the CIF basis. Every point of margin lifts this score by 4.")

    # Compliance
    comp_val = (70 if duty_known else 40) + (15 if fta else 0) + (10 if incoterm else 0) + min(15, len(docs) * 3)
    comp_f = [
        {"label": "Duty rate", "impact": "+" if duty_known else "-", "detail": "Known from WITS" if duty_known else "No tariff record — verify manually"},
        {"label": "FTA", "impact": "+" if fta else "0", "detail": "Preferential origin qualifies" if fta else "MFN rate assumed"},
        {"label": f"{len(docs)} documents", "impact": "+" if docs else "-", "detail": "Prepared" if docs else "No documents attached yet"},
    ]
    compliance = _score("Compliance", comp_val, comp_f,
                        "Rises with a known duty rate, FTA eligibility, a set Incoterm and prepared documents.")

    # Competition (how price-competitive the chosen destination is vs peers)
    if comp:
        codes = [c.get("code") for c in comp]
        rank = codes.index(importer_code) if importer_code in codes else len(codes) - 1
        comp_score = 90 - (rank * (55 / max(1, len(codes) - 1))) if len(codes) > 1 else 75
        comp_c_f = [{"label": f"Rank {rank + 1} of {len(codes)}", "impact": "+" if rank == 0 else ("0" if rank < len(codes) / 2 else "-"),
                     "detail": f"Buyer landed cost in {(q.get('importer') or {}).get('name', 'destination')} vs {len(codes)} markets"}]
        expl = "Where your chosen destination ranks on buyer landed cost against comparable markets — rank 1 is the most competitive."
    else:
        comp_score, comp_c_f, expl = 50, [{"label": "No market comparison", "impact": "-", "detail": "Run a quote to compare markets"}], "Run a costing to compare markets."
    competition = _score("Competition", comp_score, comp_c_f, expl)

    # Market attractiveness
    stats_ok = bool((q.get("sources")))
    mkt_val = 45 + (20 if fta else 0) + (20 if (dest.get("dutyRate") == 0) else 0) + (10 if stats_ok else 0)
    market = _score("Market", mkt_val,
                    [{"label": "Duty-free access", "impact": "+" if dest.get("dutyRate") == 0 else "0", "detail": "Zero import duty" if dest.get("dutyRate") == 0 else f"{dest.get('dutyRate')}% duty"},
                     {"label": "FTA", "impact": "+" if fta else "0", "detail": "Trade agreement in force" if fta else "No preferential access"}],
                    "Reflects tariff access and trade-agreement coverage into the destination market.")

    # Risk (payment + incoterm + margin buffer)
    base_risk = next((v for k, v in PAY_RISK.items() if k in pay), 55)
    risk_val = base_risk - (0 if margin >= 12 else 10) + (5 if incoterm in ("CIF", "CFR", "DAP", "DDP") else 0)
    risk = _score("Risk (safety)", risk_val,
                  [{"label": f"Payment: {pay or 'not set'}", "impact": "+" if base_risk >= 70 else "-", "detail": "Advance/LC is safest" if base_risk >= 70 else "Open-account/DA carries buyer default risk"},
                   {"label": f"Incoterm {incoterm or '—'}", "impact": "+" if incoterm in ("CIF", "CFR", "DAP", "DDP") else "0", "detail": "Seller controls main carriage"}],
                  "Higher = safer. Advance payment and Letters of Credit raise safety; open-account terms lower it.")

    # Buyer readiness
    buyer_val = 40 + (30 if project.get("buyer") else 0) + (30 if base_risk >= 70 else 0)
    buyer = _score("Buyer", buyer_val,
                   [{"label": "Buyer identified", "impact": "+" if project.get("buyer") else "-", "detail": project.get("buyer") or "No buyer linked"},
                    {"label": "Payment security", "impact": "+" if base_risk >= 70 else "-", "detail": "Secure terms" if base_risk >= 70 else "Terms increase exposure"}],
                   "Rises when a buyer is identified and payment terms are secure.")

    # Supplier readiness
    supplier_val = 40 + (35 if project.get("supplier") else 0) + (25 if (q.get("fob") or {}).get("total") else 0)
    supplier = _score("Supplier", supplier_val,
                      [{"label": "Supplier identified", "impact": "+" if project.get("supplier") else "-", "detail": project.get("supplier") or "No supplier linked"},
                       {"label": "Costed FOB", "impact": "+" if (q.get("fob") or {}).get("total") else "-", "detail": "Ex-works costing complete" if (q.get("fob") or {}).get("total") else "Complete the costing"}],
                      "Rises when a supplier is identified and the ex-works/FOB costing is complete.")

    weights = {"profitability": 0.25, "risk": 0.2, "compliance": 0.15, "competition": 0.15,
               "market": 0.1, "buyer": 0.075, "supplier": 0.075}
    parts = {"profitability": profitability, "risk": risk, "compliance": compliance,
             "competition": competition, "market": market, "buyer": buyer, "supplier": supplier}
    overall_val = sum(parts[k]["value"] * w for k, w in weights.items())
    overall = _score("Overall Trade Health", overall_val,
                     [{"label": k.title(), "impact": "+" if parts[k]["value"] >= 60 else "-", "detail": f"{parts[k]['value']}/100 (weight {int(w * 100)}%)"} for k, w in weights.items()],
                     "Weighted blend of all trade scores — the single headline health of this trade.")

    return {**parts, "overall": overall}
