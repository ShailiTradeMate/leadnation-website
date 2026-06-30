"""LeadNation Trade Command Center — world-class costing & quotation engine.

Two endpoints, by design:
  * POST /command-center/quote    → 100% deterministic FOB→CIF→Landed→Selling waterfall,
    buyer-landed-cost comparison across markets, dual + global currency conversion,
    export incentives and indicative routes. Returns INSTANTLY (no LLM) so the UI never
    blocks on a model.
  * POST /command-center/insights → the LeadNation Brain reasons over the quote and returns
    recommendations, risks, savings and alternatives. Called separately by the UI so the
    numbers render first and the AI advisor fills in progressively.

All math is transparent and explainable (every output traces to its inputs + source).
Currency the user types in = `transactionCurrency`; a second globally-traded currency
(`globalCurrency`, user-picked) is shown alongside, plus the exporter's local currency.
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel, Field

from core import db
import trade_intel
import duty_engine
from customs import _fx_rates
from brain.providers import get_provider

router = APIRouter(prefix="/command-center")
CACHE = db.cc_cache

DEFAULT_MARKETS = ["842", "784", "826", "276", "682", "702", "124", "36"]  # US,UAE,UK,DE,SA,SG,CA,AU

# Indicative standard VAT / GST rate (%) levied by the destination on imports.
VAT_BY_CODE = {
    "356": 18, "842": 0, "156": 13, "784": 5, "826": 20, "276": 19, "392": 10, "36": 10,
    "682": 15, "702": 9, "250": 20, "380": 22, "124": 5, "76": 17, "410": 10, "484": 16,
    "528": 21, "724": 21, "643": 20, "792": 20, "360": 11, "764": 7, "458": 10, "704": 10,
    "710": 15, "818": 14, "566": 7.5, "404": 16, "586": 18, "050": 15, "144": 18, "608": 12,
    "756": 8.1, "056": 21, "616": 23, "752": 25, "204": 18, "634": 0, "512": 5, "414": 0,
    "48": 10, "32": 21, "152": 19, "170": 19, "604": 18, "376": 17, "348": 27, "203": 21,
    "620": 23, "300": 24, "372": 23, "578": 25, "208": 25, "246": 25.5, "40": 20, "554": 15,
}

# Indicative ocean-freight transit (days) from any Indian gateway, by destination region.
TRANSIT_DAYS = {
    "784": "8-12", "682": "10-14", "634": "10-14", "512": "8-12", "414": "12-16", "48": "12-16",
    "842": "22-30", "124": "26-34", "484": "30-38", "826": "18-24", "276": "20-26", "250": "20-26",
    "380": "18-24", "528": "20-26", "724": "22-28", "752": "24-30", "208": "24-30", "578": "26-32",
    "392": "18-24", "410": "16-22", "156": "12-18", "702": "6-10", "458": "8-12", "764": "10-14",
    "704": "10-14", "360": "10-14", "608": "12-16", "36": "16-22", "554": "22-28", "710": "20-26",
}


def _now():
    return datetime.now(timezone.utc)


def _r(v):
    try:
        return round(float(v or 0), 2)
    except Exception:
        return 0.0


class CostInputs(BaseModel):
    exw: float = 0          # Ex-Works (factory gate) price / unit
    packing: float = 0      # export packing & labelling / unit
    inland: float = 0       # inland / local transport to port / unit
    thc: float = 0          # port handling & terminal charges / unit
    customsDocs: float = 0  # CHA, shipping bill, certs, fumigation / unit
    freight: float = 0      # main-leg ocean/air freight / unit
    insurance: float = 0    # marine / cargo insurance / unit


class QuoteRequest(BaseModel):
    hs: str = ""
    product: str = ""
    exporter: str = "356"           # ISO numeric origin
    importer: str = "842"           # ISO numeric destination
    quantity: float = 1
    unit: str = "unit"
    costs: CostInputs = Field(default_factory=CostInputs)
    marginPct: float = 0
    transactionCurrency: str = "USD"
    globalCurrency: str = "USD"     # user-picked second / globally-traded currency
    compareMarkets: list[str] | None = None


async def _resolve_hs(hs, product):
    hs6 = trade_intel._norm_hs(hs)
    if len(hs6) < 6 and product:
        hits = await trade_intel.hs_search(product, limit=1)
        if hits:
            hs6 = hits[0]["hs6"]
    return hs6


async def _duty_rate(destination, origin, hs6):
    """Best (lowest applicable) import duty rate into destination for goods of `origin`."""
    mfn = await duty_engine.wits_tariff(destination, "000", hs6)
    rate = mfn["rate"] if mfn else None
    rtype = "MFN" if mfn else None
    fta = False
    if origin and origin != destination:
        pref = await duty_engine.wits_tariff(destination, origin, hs6)
        if pref and (rate is None or pref["rate"] < rate):
            rate, rtype, fta = pref["rate"], pref["type"], True
    return rate, rtype, fta


async def _incentives(exporter, hs6):
    out = []
    if exporter == "356":  # India
        rb = await duty_engine.rodtep_rate(hs6)
        if rb:
            out.append({"scheme": "RoDTEP", "value": f"{rb['rate']}% of FOB",
                        "detail": "Remission of Duties & Taxes on Exported Products — tradable e-scrip.", "source": rb["source"]})
        out += [
            {"scheme": "GST Refund / LUT", "value": "Zero-rated", "detail": "Exports are zero-rated under GST; claim ITC refund or export under LUT without paying IGST.", "source": "CBIC"},
            {"scheme": "Duty Drawback", "value": "Schedule rate", "detail": "Rebate of customs duty paid on imported inputs used in the exported product.", "source": "CBIC Drawback Schedule"},
            {"scheme": "Advance Authorisation", "value": "Duty-free inputs", "detail": "Duty-free import of raw materials physically incorporated into export goods.", "source": "DGFT FTP"},
        ]
    return out


async def compute_quote(req: QuoteRequest):
    hs6 = await _resolve_hs(req.hs, req.product)
    if len(hs6) < 6:
        return {"ok": False, "error": "Provide a product name or a 6-digit HS code."}

    c = req.costs
    qty = max(req.quantity or 1, 0) or 1
    fob_u = _r(c.exw + c.packing + c.inland + c.thc + c.customsDocs)
    cif_u = _r(fob_u + c.freight + c.insurance)
    fob_t = _r(fob_u * qty)
    cif_t = _r(cif_u * qty)

    exporter_name = duty_engine.NAME_BY_CODE.get(req.exporter, req.exporter or "any country")
    importer_name = duty_engine.NAME_BY_CODE.get(req.importer, req.importer)

    # Duty & tax into the primary destination
    rate, rtype, fta = await _duty_rate(req.importer, req.exporter, hs6)
    duty_amt = _r(cif_t * (rate or 0) / 100)
    vat_rate = VAT_BY_CODE.get(req.importer, 0)
    vat_amt = _r((cif_t + duty_amt) * vat_rate / 100)
    landed_t = _r(cif_t + duty_amt + vat_amt)

    margin = req.marginPct or 0
    selling_t = _r(cif_t * (1 + margin / 100))
    profit_t = _r(selling_t - cif_t)

    # Currency context: user types in transactionCurrency. Convert to global + exporter-local.
    txn = (req.transactionCurrency or "USD").upper()
    glob = (req.globalCurrency or "USD").upper()
    exp_cur = duty_engine.CURRENCY_BY_CODE.get(req.exporter, "USD")
    rates, _cached = await _fx_rates(txn)
    def conv(v, cur):
        r = (rates or {}).get(cur)
        return _r(v * r) if r else None
    currency = {
        "transaction": txn,
        "global": glob,
        "exporterLocal": exp_cur,
        "fxBase": txn,
        "rates": {glob: (rates or {}).get(glob), exp_cur: (rates or {}).get(exp_cur)} if rates else {},
        "source": "open.er-api.com (live)",
        "converted": {
            "fob": {"global": conv(fob_t, glob), "exporterLocal": conv(fob_t, exp_cur)},
            "cif": {"global": conv(cif_t, glob), "exporterLocal": conv(cif_t, exp_cur)},
            "landed": {"global": conv(landed_t, glob), "exporterLocal": conv(landed_t, exp_cur)},
            "selling": {"global": conv(selling_t, glob), "exporterLocal": conv(selling_t, exp_cur)},
        },
    }

    # Buyer-landed-cost comparison across markets (buyer pays CIF + their duty + their VAT).
    markets = req.compareMarkets or DEFAULT_MARKETS
    markets = [m for m in markets if m != req.exporter][:8]
    comparison = []
    for m in markets:
        mrate, mtype, mfta = await _duty_rate(m, req.exporter, hs6)
        mvat = VAT_BY_CODE.get(m, 0)
        bduty = _r(cif_t * (mrate or 0) / 100)
        bvat = _r((cif_t + bduty) * mvat / 100)
        btotal = _r(cif_t + bduty + bvat)
        comparison.append({
            "code": m, "country": duty_engine.NAME_BY_CODE.get(m, m),
            "cif": cif_t, "dutyRate": mrate, "dutyType": mtype, "duty": bduty,
            "vatRate": mvat, "vat": bvat, "buyerTotal": btotal, "fta": mfta,
            "note": "Preferential / FTA rate applies" if mfta else ("Duty-free" if (mrate == 0) else None),
        })
    comparison.sort(key=lambda x: x["buyerTotal"])

    incentives = await _incentives(req.exporter, hs6)
    transit = TRANSIT_DAYS.get(req.importer)
    routes = [
        {"mode": "Sea FCL", "detail": "Full container — lowest unit cost for volume cargo", "transit": f"{transit} days" if transit else "varies"},
        {"mode": "Sea LCL", "detail": "Shared container — best for part loads", "transit": f"{transit} days" if transit else "varies"},
        {"mode": "Air", "detail": "Fastest, premium freight — high-value / urgent goods", "transit": "2-6 days"},
    ]

    stats = await trade_intel.trade_stats(hs6)
    desc = (stats.get("description") if stats.get("ok") else "") or f"HS {hs6}"

    return {
        "ok": True, "hsCode": hs6, "description": desc, "quantity": qty, "unit": req.unit,
        "exporter": {"code": req.exporter, "name": exporter_name},
        "importer": {"code": req.importer, "name": importer_name},
        "waterfall": [
            {"stage": "Ex-Works (EXW)", "perUnit": _r(c.exw), "total": _r(c.exw * qty), "note": "Factory gate price"},
            {"stage": "Export Packing & Labelling", "perUnit": _r(c.packing), "total": _r(c.packing * qty), "note": "Cartons, marks, palletising"},
            {"stage": "Inland / Local Transport", "perUnit": _r(c.inland), "total": _r(c.inland * qty), "note": "Factory to origin port/airport"},
            {"stage": "Port Handling & Terminal (THC)", "perUnit": _r(c.thc), "total": _r(c.thc * qty), "note": "Stuffing, loading, port charges"},
            {"stage": "Customs & Documentation", "perUnit": _r(c.customsDocs), "total": _r(c.customsDocs * qty), "note": "CHA fees, shipping bill, certs, fumigation"},
            {"stage": "FOB Value", "perUnit": fob_u, "total": fob_t, "note": "Items 1-5: price at origin port", "milestone": True},
            {"stage": "Ocean / Air Freight", "perUnit": _r(c.freight), "total": _r(c.freight * qty), "note": "Main-leg freight to destination"},
            {"stage": "Marine / Cargo Insurance", "perUnit": _r(c.insurance), "total": _r(c.insurance * qty), "note": "Transit cover, typically 0.1%-0.5% of CIF"},
            {"stage": "CIF Value", "perUnit": cif_u, "total": cif_t, "note": "FOB + Freight + Insurance — import duties assess on this", "milestone": True},
        ],
        "fob": {"perUnit": fob_u, "total": fob_t},
        "cif": {"perUnit": cif_u, "total": cif_t},
        "destination": {
            "dutyRate": rate, "dutyType": rtype, "duty": duty_amt, "fta": fta,
            "vatRate": vat_rate, "vat": vat_amt, "landed": landed_t,
        },
        "pricing": {"marginPct": margin, "selling": selling_t, "profit": profit_t, "basis": "CIF"},
        "currency": currency,
        "comparison": comparison,
        "incentives": incentives,
        "routes": routes,
        "sources": ["World Bank WITS / UNCTAD TRAINS", "open.er-api.com (FX)", "OEC World", "DGFT / CBIC (incentives)"],
        "generatedAt": _now().isoformat(),
    }


@router.post("/quote")
async def quote(req: QuoteRequest):
    return await compute_quote(req)


@router.get("/markets")
async def markets():
    return {"countries": [{"code": c, "name": n} for c, n in sorted(duty_engine.COUNTRIES, key=lambda x: x[1])]}


class InsightRequest(BaseModel):
    quote: dict


@router.post("/insights")
async def insights(req: InsightRequest):
    q = req.quote or {}
    if not q.get("ok"):
        return {"ok": False, "error": "Run a quote first."}
    exp = q.get("exporter", {}).get("name", "")
    imp = q.get("importer", {}).get("name", "")
    desc = q.get("description", "")
    hs6 = q.get("hsCode", "")
    dest = q.get("destination", {})
    comp = q.get("comparison", [])
    cif = q.get("cif", {}).get("total")
    txn = q.get("currency", {}).get("transaction", "USD")

    cheapest = comp[0] if comp else None
    engine_outputs = {
        "costing": {"summary": f"CIF to {imp}: {cif} {txn} for {q.get('quantity')} {q.get('unit')}. Import duty {dest.get('dutyRate')}% ({dest.get('dutyType')}), destination VAT {dest.get('vatRate')}%, landed {dest.get('landed')} {txn}.", "data": {}},
    }
    if cheapest:
        engine_outputs["market_comparison"] = {"summary": "Buyer total cost by market (ascending): " + "; ".join(f"{c['country']} {c['buyerTotal']} {txn} (duty {c['dutyRate']}%{', FTA' if c['fta'] else ''})" for c in comp[:6]), "data": {}}
    if q.get("incentives"):
        engine_outputs["incentives"] = {"summary": "Export incentives available: " + "; ".join(f"{i['scheme']} ({i['value']})" for i in q["incentives"]), "data": {}}

    question = (f"Act as a senior global-trade advisor for an exporter shipping {desc} (HS {hs6}) from {exp} to {imp}. "
                f"Using ONLY the figures provided, give: (1) 2-3 sharp insights on this costing, "
                f"(2) the single best destination market and why (cite the buyer landed cost), "
                f"(3) concrete duty/cost SAVINGS opportunities (FTAs, incentives, Incoterm or routing changes) with the approximate amount saved, "
                f"(4) the top 2 risks (currency, payment, compliance) and how to mitigate them. "
                f"Be specific and quantitative. Use short markdown headings and bullets. Do not invent numbers not given.")
    try:
        provider = get_provider()
        res = await provider.generate(
            question, {"primary": "command_center"},
            {"products": [desc], "countries": [exp, imp], "hsn": [hs6]},
            engine_outputs, {"retrieved": [], "memory": {}, "user": {}, "language": "en"})
        return {"ok": True, "advisor": res.get("answer", ""), "live": res.get("live", False),
                "degraded": res.get("degraded", False)}
    except Exception as exc:
        logging.warning("Command Center insights failed: %s", exc)
        return {"ok": False, "error": "Advisor temporarily unavailable."}
