"""Compile Data — one-click master trade report.

Aggregates, for a product + export country + import country (+ optional HS, currency):
  * Trade statistics (global, both countries' role)
  * Duty & benefits for the exact lane (+ India breakdown / RoDTEP when relevant)
  * Tariff comparison across top destination markets
  * Live currency exchange + a sample landed-cost / price calculation
  * Freight modes & government-benefit pointers
  * A Brain-written executive narrative (LLM) tying it all together
Everything the engines return is REAL/live; the Brain composes the human report.
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Query

from core import db
import trade_intel
import duty_engine
from customs import _fx_rates
from brain.providers import get_provider

router = APIRouter(prefix="/compile")
CACHE = db.compile_cache

COMPARE_MARKETS = ["842", "276", "826", "784", "392", "156"]  # US, DE, UK, AE, JP, CN


def _now():
    return datetime.now(timezone.utc)


async def _tariff_comparison(hs6, exporter):
    out = []
    for dest in COMPARE_MARKETS:
        t = await duty_engine.wits_tariff(dest, "000", hs6)
        if t:
            out.append({"country": duty_engine.NAME_BY_CODE.get(dest, dest),
                        "rate": t["rate"], "type": t["type"], "year": t["year"]})
    out.sort(key=lambda x: x["rate"])
    return out


async def _sample_price(duty_rate, txn_cur, txn_rate, exp_cur, exp_rate):
    """Illustrative landed cost for a US$10,000 FOB shipment, shown in 3 currencies."""
    fob = 10000.0
    freight, insurance = 1200.0, 150.0
    cif = fob + freight + insurance
    duty = round(cif * (duty_rate or 0) / 100, 2)
    landed = round(cif + duty, 2)
    conv = lambda rate: round(landed * rate, 2) if rate else None
    return {
        "assumptionsUSD": {"fob": fob, "freight": freight, "insurance": insurance},
        "cifUSD": cif, "dutyRatePct": duty_rate or 0, "dutyUSD": duty, "landedUSD": landed,
        "transactionCurrency": txn_cur, "landedTransaction": conv(txn_rate),
        "exporterCurrency": exp_cur, "landedExporter": conv(exp_rate),
    }


async def compile_report(hs="", product="", exporter="", importer="356", currency="USD", force=False):
    hs6 = trade_intel._norm_hs(hs)
    if len(hs6) < 6 and product:
        hits = await trade_intel.hs_search(product, limit=1)
        if hits:
            hs6 = hits[0]["hs6"]
    if len(hs6) < 6:
        return {"ok": False, "error": "Provide a product name or a 6-digit HS code."}

    cache_id = f"v2:{hs6}:{exporter}:{importer}:{currency}"
    if not force:
        c = await CACHE.find_one({"_id": cache_id})
        if c and (_now() - datetime.fromisoformat(c["at"])).days < 7:
            return c["result"]

    stats = await trade_intel.trade_stats(hs6)
    duty = await duty_engine.duty_and_benefits(hs6, origin=exporter, destination=importer)
    comparison = await _tariff_comparison(hs6, exporter)

    cur = (currency or "USD").upper()                                   # user transaction currency
    exporter_currency = duty_engine.CURRENCY_BY_CODE.get(exporter, "USD")  # auto-detected
    rates, _cached = await _fx_rates("USD")
    txn_rate = (rates or {}).get(cur)
    exp_rate = (rates or {}).get(exporter_currency)
    fx_block = None
    if rates:
        fx_block = {"base": "USD",
                    "transactionCurrency": cur, "transactionRate": txn_rate,
                    "exporterCurrency": exporter_currency, "exporterRate": exp_rate,
                    "popular": {c: rates.get(c) for c in ["INR", "USD", "EUR", "GBP", "AED", "CNY", "JPY"] if rates.get(c)},
                    "source": "open.er-api.com (live)"}

    duty_rate = None
    if duty.get("ok"):
        duty_rate = (duty.get("preferential") or duty.get("importDuty") or {}).get("rate")
    price = await _sample_price(duty_rate, cur, txn_rate, exporter_currency, exp_rate)

    exporter_name = duty_engine.NAME_BY_CODE.get(exporter, exporter or "any country")
    importer_name = duty_engine.NAME_BY_CODE.get(importer, importer)
    desc = (stats.get("description") if stats.get("ok") else "") or f"HS {hs6}"

    # ---- Brain narrative (LLM composes a real report from the live data) ----
    narrative = ""
    try:
        engine_outputs = {}
        if stats.get("ok"):
            imp = ", ".join(f"{i['country']} ({i['share']}%)" for i in stats["topImporters"][:5])
            engine_outputs["trade_statistics"] = {"summary": f"World trade in {desc} ({stats['year']}): ${stats['totalWorldTradeUSD']:,.0f}. Top importers: {imp}. Leading exporters: {', '.join(e['country'] for e in stats['topExporters'][:5])}.", "data": {}}
        if duty.get("ok"):
            di = duty.get("importDuty")
            line = f"Import duty into {importer_name}: {di['rate']}% {di['type']} ({di['year']})." if di else f"No tariff record found for {importer_name} on this product."
            if duty.get("exportBenefit"):
                line += f" Export benefit ({exporter_name}): {duty['exportBenefit']['scheme']} {duty['exportBenefit']['rate']}% of FOB."
            engine_outputs["duty_benefits"] = {"summary": line, "data": {}}
        if comparison:
            engine_outputs["tariff_comparison"] = {"summary": "Import duty by market: " + "; ".join(f"{c['country']} {c['rate']}%" for c in comparison), "data": {}}
        q = f"Create a concise export action plan for shipping {desc} (HS {hs6}) from {exporter_name} to {importer_name}: market opportunity, duty & benefits, compliance & documents needed for this exact lane, logistics, and 3 next steps."
        provider = get_provider()
        res = await provider.generate(q, {"primary": "compile"}, {"products": [product or desc], "countries": [exporter_name, importer_name], "hsn": [hs6]}, engine_outputs, {"retrieved": [], "memory": {}, "user": {}, "language": "en"})
        narrative = res.get("answer", "")
    except Exception as exc:
        logging.warning("Compile narrative failed: %s", exc)

    result = {
        "ok": True, "hsCode": hs6, "description": desc,
        "exporter": {"code": exporter, "name": exporter_name},
        "importer": {"code": importer, "name": importer_name},
        "currency": cur,
        "exporterCurrency": exporter_currency,
        "tradeStats": stats if stats.get("ok") else None,
        "duty": duty if duty.get("ok") else None,
        "tariffComparison": comparison,
        "fx": fx_block,
        "price": price,
        "freightModes": ["Sea FCL", "Sea LCL", "Air"],
        "narrative": narrative,
        "generatedAt": _now().isoformat(),
    }
    await CACHE.replace_one({"_id": cache_id}, {"_id": cache_id, "result": result, "at": _now().isoformat()}, upsert=True)
    return result


@router.get("/report")
async def report(hs: str = Query(""), product: str = Query(""), exporter: str = Query(""),
                 importer: str = Query("356"), currency: str = Query("USD"), force: bool = False):
    return await compile_report(hs=hs, product=product, exporter=exporter,
                                importer=importer, currency=currency, force=force)
