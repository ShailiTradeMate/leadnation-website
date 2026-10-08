"""Crawler / AI answer layer (GEO).

The React app is a client-rendered SPA, so answer engines that do not execute
JavaScript see very little text. This module serves the SAME data the page renders
as plain, complete HTML and Markdown documents at stable URLs, each canonical-tagged
back to the human page. Listed in llms.txt and the sitemap.

Nothing is invented here: export guides are composed from seo_pages (WITS tariffs,
OEC demand, VBIE buyer counts) and tool answers from the tool's own documented
behaviour. Every figure keeps its source and as-of year.
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse

from core import db
import seo_pages

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/answers", tags=["geo-answers"])

SITE = "https://vametra.com"


# ---------------------------------------------------------------- tool answers
TOOL_ANSWERS = {
    "/tools/duty-calculator": {
        "title": "Customs duty calculator — how to find the real import duty for any HS code",
        "description": "Look up the applied MFN and preferential import tariff for a 6-digit HS code "
                       "into 56 reporting countries, from World Bank WITS / UNCTAD TRAINS, with the "
                       "data year on every rate.",
        "answer": "To find the import duty your buyer will pay, you need three things: the 6-digit HS "
                  "code of the goods, the exporting (origin) country and the importing (destination) "
                  "country. Vametra AI reads the applied MFN rate the destination reports to the World "
                  "Bank WITS / UNCTAD TRAINS database at HS6 level, then checks whether a lower "
                  "preferential (FTA) rate is reported for your specific origin. The rate is shown with "
                  "its reporting year, because tariff data typically lags the current year by about two "
                  "years.",
        "sections": [
            ("What the tool returns", [
                "Applied MFN duty rate for the destination country at HS6, with reporting year and source.",
                "Preferential / FTA rate for your origin country when the destination reports one.",
                "Destination VAT/GST or equivalent consumption tax where applicable.",
                "For imports into India: the Basic Customs Duty, 10% Social Welfare Surcharge and IGST slab.",
                "Export-support schemes published by your own exporting country's authorities, with official links.",
            ]),
            ("How to read a 0% result", [
                "0% is the ad-valorem rate reported to WITS. Some tariff lines (EU cereals and sugar, for "
                "example) carry specific duties per tonne that are not expressed as a percentage — confirm "
                "them in the destination tariff schedule before quoting.",
            ]),
        ],
        "faqs": [
            ("Where does the duty data come from?",
             "World Bank WITS / UNCTAD TRAINS, at HS6 level, for 56 reporting countries. Results are cached "
             "for 7 days and the reporting year is displayed next to every rate."),
            ("Is the calculator free?", "Yes, duty lookup is free and needs no account."),
            ("Does it cover duty for every country in the world?",
             "No. Coverage is limited to the countries that report tariff data to WITS. If there is no record "
             "for a country/product pair, Vametra AI says so rather than estimating."),
        ],
    },
    "/tools/landed-cost-calculator": {
        "title": "Landed cost calculator — FOB to CIF to landed cost with real duty, VAT and FX",
        "description": "Build an export cost waterfall from Ex-Works to landed cost at destination using "
                       "live WITS duty, destination VAT/GST and exchange rates, in your buyer's currency.",
        "answer": "Landed cost is the total your buyer pays to get the goods cleared at their door: goods "
                  "value plus freight and insurance (CIF), plus import duty on the CIF value, plus any "
                  "destination VAT/GST, plus clearance and local delivery. Vametra AI applies the real "
                  "tariff for your HS code and trade lane, converts the result into the destination "
                  "currency at the current rate, and ranks the markets where your buyer pays the least.",
        "sections": [
            ("Inputs you need", [
                "6-digit HS code (or search by product name).",
                "Exporting country and importing country — the lane decides both the tariff and the taxes.",
                "Unit cost, quantity, freight, insurance and your margin.",
            ]),
            ("What the engine adds", [
                "Applied or preferential import duty from World Bank WITS / UNCTAD TRAINS.",
                "Destination VAT/GST where it applies to imports.",
                "Dual-currency quotation so the buyer sees their own currency.",
                "Market comparison: the same product costed into several destinations.",
            ]),
        ],
        "faqs": [
            ("Which Incoterms are covered?",
             "The waterfall covers Ex-Works, FOB, CIF and DDP-style landed cost, so you can quote at the "
             "Incoterm your buyer asks for."),
            ("Does it include my own country's export benefits?",
             "Yes — where your exporting country publishes an official scheme, it is listed with the "
             "administering authority and its official page. Rate-level figures are only shown where an "
             "official rate schedule exists (today, India's RoDTEP)."),
        ],
    },
    "/tools/export-incentive-finder": {
        "title": "Export incentive finder — your own country's official export-support schemes",
        "description": "See the official export-support schemes published by your exporting country's "
                       "authorities — remissions, duty drawback, tax refunds, export credit and grants — "
                       "plus the import duty your buyer pays at destination.",
        "answer": "Export support differs completely by country. India publishes a rate-level remission "
                  "schedule (RoDTEP, DGFT Appendix 4R). Most countries instead support exporters through "
                  "duty drawback, export VAT refunds, temporary-import regimes, state export credit "
                  "insurance or market-development grants — and EU/WTO rules prohibit direct export "
                  "subsidies altogether. Vametra AI shows the schemes your own country's authorities "
                  "actually publish, each linked to the official page, next to the duty your buyer pays.",
        "sections": [
            ("Types of export support you will see", [
                "Remission of embedded duties and taxes (e.g. India RoDTEP, rate schedule published).",
                "Duty drawback — refund of duty paid on imported inputs (US CBP, Canada CBSA, Australia ABF, India CBIC, Brazil).",
                "Export VAT / consumption tax refund (e.g. China, administered by the State Taxation Administration).",
                "Temporary-import / processing regimes (Mexico IMMEX, Indonesia KITE, EU inward processing).",
                "State export credit insurance and finance (US EXIM, UKEF, EDC, Hermes/AGA, SACE, NEXI, K-SURE, ECI, Saudi EXIM).",
                "Market-development grants (Australia EMDG, South Africa EMIA, Türkiye Turquality, Enterprise Singapore).",
            ]),
            ("Why no percentages for most countries", [
                "Only some governments publish a machine-readable rate schedule. Where a rate is not "
                "officially published, Vametra AI names the scheme and links the authority instead of "
                "estimating a number you could not rely on in a contract.",
            ]),
        ],
        "faqs": [
            ("Which countries are covered?",
             "Around 45 exporting countries whose official export-support pages have been verified, across "
             "Asia, the EU, the Middle East, Africa, the Americas and Oceania. Coverage expands as official "
             "sources are verified."),
            ("Is the RoDTEP rate exact?",
             "The rate shown is the chapter-level DGFT Appendix 4R figure. Confirm the exact 8-digit rate and "
             "value cap in the DGFT notification before claiming."),
        ],
    },
    "/tools/hsn-finder": {
        "title": "HS code finder — find the correct HS/HSN code for any product, any country",
        "description": "Search the full HS6 directory by product or trade name and get the code with the "
                       "duty, taxes and documents that apply to your origin-destination lane.",
        "answer": "An HS code is the 6-digit international classification that decides your duty rate, your "
                  "documentation and your buyer's taxes. Vametra AI searches the complete HS6 directory by "
                  "product or commercial trade name, then applies your chosen exporting and importing "
                  "country to show the duty, destination taxes and any export-support scheme for that lane. "
                  "National tariffs extend HS6 to 8 or 10 digits, so confirm the full national code in the "
                  "destination tariff schedule.",
        "sections": [
            ("How classification works", [
                "The first 6 digits are harmonised worldwide (WCO Harmonized System).",
                "Countries add 2-4 more digits for their national tariff — India HSN 8-digit, US HTS 10-digit.",
                "Classification follows the goods, not the intended use or your invoice description.",
            ]),
        ],
        "faqs": [
            ("Is the HS code the same in every country?",
             "The first 6 digits are. Beyond that, each country has its own national extension, so always "
             "confirm the 8 or 10-digit code in the destination tariff."),
            ("Can I search by trade name?",
             "Yes — commercial names like basmati rice, agarbatti or cotton t-shirt are mapped to the "
             "correct HS6 code."),
        ],
    },
    "/tools/find-buyers": {
        "title": "Find verified overseas buyers by HS code and country",
        "description": "Search verified importer records by product HS family and destination country, with "
                       "honest coverage disclosure per market.",
        "answer": "Vametra AI's verified buyer records are screened importer entities matched to HS families "
                  "and countries. Coverage is strongest in Europe today; for markets still being ingested, "
                  "the platform shows the real import demand for the product and marks buyer coverage as "
                  "expanding rather than showing filler records.",
        "sections": [
            ("What a buyer record contains", [
                "Company identity and country, matched HS families, and sector.",
                "Verification state — records are published only after screening.",
            ]),
        ],
        "faqs": [
            ("Which markets have buyer coverage today?",
             "European markets have the deepest coverage. Middle East, Africa and Asia-Pacific coverage is "
             "being ingested and is explicitly labelled as expanding where records are not yet available."),
        ],
    },
    "/tools/export-readiness": {
        "title": "Export readiness check — are you ready to ship to this market?",
        "description": "Check the registrations, documents and certifications you need before exporting a "
                       "product to a specific destination.",
        "answer": "Export readiness has three layers: your own registrations (business, tax and export "
                  "registration in your country), the shipping documents for the lane (invoice, packing "
                  "list, bill of lading or airway bill, certificate of origin) and the destination's product "
                  "requirements (sanitary/phytosanitary, labelling, conformity marks). Vametra AI checks each "
                  "layer for your product and destination, and the Brain turns gaps into next actions.",
        "sections": [],
        "faqs": [
            ("Does the checklist change by destination?",
             "Yes. Product requirements and certifications are set by the importing country, so the "
             "checklist is generated for your specific lane."),
        ],
    },
    "/tools/product-research": {
        "title": "Export product research — world demand, top importers and tariffs by HS code",
        "description": "See world import value, top importing and exporting countries and the tariff "
                       "landscape for any HS code, from OEC World (CEPII BACI / UN Comtrade) and WITS.",
        "answer": "Before choosing a market, check where the demand actually is. Vametra AI reads world "
                  "import value and the ranked list of importing countries for your HS code from OEC World "
                  "(CEPII BACI / UN Comtrade-derived data), then pairs each candidate market with its "
                  "applied import tariff from WITS so you can see demand and duty together.",
        "sections": [],
        "faqs": [
            ("How current is the trade data?",
             "Global trade statistics are published with a lag; the reporting year is shown with every "
             "figure."),
        ],
    },
    "/brain": {
        "title": "Vametra AI Brain — one answer across tariffs, documents, markets and buyers",
        "description": "Ask any export or import question and get one sourced answer composed from the "
                       "tariff, compliance, product, country, logistics and buyer engines.",
        "answer": "The Vametra AI Brain detects the product, HS code, countries and intent in your question, "
                  "routes it to the relevant trade engines, and composes a single answer with sources and "
                  "next actions — duty and taxes for the lane, documents and certifications, market demand, "
                  "export support in your country, and matching verified buyers.",
        "sections": [],
        "faqs": [
            ("Does it make up tariff numbers?",
             "No. Figures come from the same sourced engines as the tools — WITS/UNCTAD TRAINS for tariffs, "
             "OEC World for demand, official authority pages for export support."),
        ],
    },
}


# ---------------------------------------------------------------- composition
def _esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _fmt_usd(v):
    v = float(v or 0)
    for unit, div in (("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if v >= div:
            return f"US${v / div:.2f}{unit}"
    return f"US${v:.0f}"


def _tool_doc(path):
    t = TOOL_ANSWERS[path]
    md = [f"# {t['title']}", "", t["answer"], ""]
    for heading, bullets in t.get("sections", []):
        md += [f"## {heading}", ""] + [f"- {b}" for b in bullets] + [""]
    if t.get("faqs"):
        md += ["## FAQ", ""]
        for q, a in t["faqs"]:
            md += [f"### {q}", "", a, ""]
    md += ["## Source", f"Vametra AI — {SITE}{path}", ""]
    return {"path": path, "title": t["title"], "description": t["description"],
            "markdown": "\n".join(md),
            "sources": ["World Bank WITS / UNCTAD TRAINS", "OEC World (CEPII BACI / UN Comtrade)",
                        "Official national export-support authorities"]}


async def _export_doc(product, country):
    data = await seo_pages.product_country_page(product, country)
    p, c = data["product"], data["country"]
    duty, demand, buyers = data.get("duty"), data.get("demand"), data.get("buyers")
    title = f"Export {p['name']} to {c['name']} — duty, demand, documents and buyers"
    lead = []
    if duty and duty.get("importDuty"):
        d = duty["importDuty"]
        lead.append(f"{c['name']} applies a {d['rate']}% {d['type']} import duty on {p['name']} "
                    f"(HS {duty['hsCode']}) as reported for {d['year']} to {d['source']}.")
        if duty.get("preferential"):
            pr = duty["preferential"]
            lead.append(f"A preferential rate of {pr['rate']}% ({pr['type']}, {pr['year']}) is reported "
                        f"for shipments from India.")
    if duty and duty.get("exportBenefit"):
        b = duty["exportBenefit"]
        lead.append(f"Indian exporters can claim {b['scheme']} at {b['rate']}{b.get('unit', '%')} "
                    f"({b['source']}).")
    if demand and demand.get("countryImportsUSD"):
        lead.append(f"{c['name']} imported {_fmt_usd(demand['countryImportsUSD'])} of this product in "
                    f"{demand.get('year')}, ranking #{demand.get('countryRank')} worldwide "
                    f"({demand.get('source')}).")
    elif demand and demand.get("worldImportsUSD"):
        lead.append(f"World imports of this product were {_fmt_usd(demand['worldImportsUSD'])} in "
                    f"{demand.get('year')} ({demand.get('source')}).")

    md = [f"# {title}", "", " ".join(lead) or
          f"Export guide for {p['name']} (HS {p['primaryHs']}) to {c['name']}.", ""]

    if demand and demand.get("topImporters"):
        md += [f"## Top importing markets for {p['name']}", ""]
        for i, row in enumerate(demand["topImporters"], 1):
            name = row.get("country") or row.get("name")
            val = row.get("valueUSD") or row.get("value")
            md.append(f"{i}. {name} — {_fmt_usd(val)}" if val else f"{i}. {name}")
        md += ["", f"Source: {demand.get('source')} ({demand.get('year')})", ""]

    if duty:
        md += ["## Duty and taxes at destination", ""]
        if duty.get("importDuty"):
            d = duty["importDuty"]
            md.append(f"- Import duty into {c['name']}: {d['rate']}% ({d['type']}, {d['year']}, {d['source']})")
        if duty.get("preferential"):
            pr = duty["preferential"]
            md.append(f"- Preferential rate from India: {pr['rate']}% ({pr['type']}, {pr['year']})")
        if duty.get("exportBenefit"):
            b = duty["exportBenefit"]
            md.append(f"- India export benefit: {b['scheme']} {b['rate']}{b.get('unit', '%')} ({b['source']})")
        for n in duty.get("notes", []):
            md.append(f"- Note: {n}")
        md.append("")

    md += ["## Buyer coverage", ""]
    if buyers and buyers.get("covered"):
        md.append(f"- {buyers['total']} verified importer records in {c['name']}, "
                  f"{buyers.get('matchingHs', 0)} matching this HS family.")
    else:
        md.append(f"- Verified buyer coverage for {c['name']} is being ingested. Import demand above is "
                  f"real; buyer records are published only after screening.")
    md.append("")

    if data.get("expos"):
        md += ["## Trade events in this market", ""]
        for e in data["expos"]:
            md.append(f"- {e.get('name') or e.get('title')} — {e.get('city') or e.get('location') or ''} "
                      f"{e.get('startDate') or e.get('starts_at') or ''}".rstrip())
        md.append("")

    md += ["## Data sources", ""]
    for s in data.get("sources", []):
        md.append(f"- {s['name']} (as of {s.get('asOf')}) — {s['field']}")
    md += ["", f"Disclaimer: {data['disclaimer']}", "",
           "## Source", f"Vametra AI — {SITE}{data['url']}", ""]

    desc = (lead[0] if lead else f"Export {p['name']} to {c['name']}: duty, demand and buyers.")[:300]
    return {"path": data["url"], "title": title, "description": desc,
            "markdown": "\n".join(md), "indexable": data["indexable"],
            "dataScore": data["dataScore"],
            "sources": [s["name"] for s in data.get("sources", [])]}


def _html(doc):
    """Complete, crawlable HTML for the document, canonical-tagged to the human page."""
    body = []
    for line in doc["markdown"].split("\n"):
        l = line.strip()
        if not l:
            continue
        if l.startswith("### "):
            body.append(f"<h3>{_esc(l[4:])}</h3>")
        elif l.startswith("## "):
            body.append(f"<h2>{_esc(l[3:])}</h2>")
        elif l.startswith("# "):
            body.append(f"<h1>{_esc(l[2:])}</h1>")
        elif l.startswith("- "):
            body.append(f"<li>{_esc(l[2:])}</li>")
        elif l[0].isdigit() and l[1:3] in (". ", ") "):
            body.append(f"<li>{_esc(l[3:])}</li>")
        else:
            body.append(f"<p>{_esc(l)}</p>")
    html = []
    in_list = False
    for el in body:
        if el.startswith("<li>") and not in_list:
            html.append("<ul>")
            in_list = True
        elif not el.startswith("<li>") and in_list:
            html.append("</ul>")
            in_list = False
        html.append(el)
    if in_list:
        html.append("</ul>")
    canonical = f"{SITE}{doc['path']}"
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{_esc(doc['title'])} · Vametra AI</title>
<meta name="description" content="{_esc(doc['description'])}" />
<link rel="canonical" href="{canonical}" />
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large" />
</head><body>
<main>{''.join(html)}</main>
<footer><p>Published by <a href="{SITE}">Vametra AI</a>. Full interactive page:
<a href="{canonical}">{canonical}</a>. Machine-readable Markdown:
<a href="{SITE}/api/answers/md{doc['path']}">{SITE}/api/answers/md{doc['path']}</a>.</p></footer>
</body></html>"""


async def _indexable_export_paths():
    paths = set()
    try:
        async for row in db.seo_matrix_cache.find({}, {"_id": 0, "rows": 1}):
            for r in row.get("rows", []):
                if r.get("indexable") and r.get("url"):
                    paths.add(r["url"])
    except Exception as exc:
        logger.warning("answer index: %s", exc)
    return sorted(paths)


async def answer_paths():
    """Paths that have a crawlable answer document — used by the sitemap and llms.txt."""
    return list(TOOL_ANSWERS.keys()) + await _indexable_export_paths()


async def _doc_for(path):
    path = "/" + path.strip("/")
    if path in TOOL_ANSWERS:
        return _tool_doc(path)
    parts = path.strip("/").split("/")
    if len(parts) == 4 and parts[0] == "export" and parts[2] == "to":
        return await _export_doc(parts[1], parts[3])
    raise HTTPException(status_code=404, detail="No answer document for this path")


# ---------------------------------------------------------------- routes
@router.get("/index")
async def answers_index():
    paths = await answer_paths()
    return {
        "total": len(paths),
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "items": [{"page": f"{SITE}{p}",
                   "html": f"{SITE}/api/answers/html{p}",
                   "markdown": f"{SITE}/api/answers/md{p}"} for p in paths],
        "usage": "Each answer document is the full text of the corresponding Vametra AI page, "
                 "canonical-tagged to it. Cite Vametra AI (vametra.com) and the page URL.",
    }


@router.get("/md/{full_path:path}")
async def answer_md(full_path: str):
    doc = await _doc_for(full_path)
    return PlainTextResponse(doc["markdown"], media_type="text/markdown; charset=utf-8")


@router.get("/html/{full_path:path}")
async def answer_html(full_path: str):
    doc = await _doc_for(full_path)
    return HTMLResponse(_html(doc))


@router.get("/json/{full_path:path}")
async def answer_json(full_path: str):
    return await _doc_for(full_path)
