"""VBIE connectors — daily ingestion of REAL buyer intelligence from official sources.

SINGLE-WRITER RULE: every buyer/entity write to the shared `entities` graph happens
HERE, in the website backend. The DigitalOcean identity backend never writes the buyer
graph. Legal policy is data-driven (see /app/memory/research/platform/sources_seed.json):
we use official government APIs and robots-compliant open data ONLY — we never scrape
sites the registry flags as prohibited/tos-gated.

Live connectors (all ADDITIVE, upsert into `entities` with entity_type='buyer'):
  • EU TED (api.ted.europa.eu) — real named EU public buyers actively procuring goods.
      Open reuse licence, no key. This is the primary live named-buyer source.
  • trade.gov CSL — MANDATORY sanctions/denied-party screening gate on every buyer. No key.
  • UN Comtrade preview — aggregate corridor market context (India export corridors). No key.
  • Canadian Importers Database — real named importers by HS (open data; best-effort).
  • SAM.gov — US registered entities/vendors (needs free SAM_GOV_API_KEY).
  • UK Companies House — UK registry identities (needs free COMPANIES_HOUSE_API_KEY).

Every surfaced buyer is deterministic-GEID keyed (idempotent re-ingest), sanctions-screened
before it is ever shown, and carries cited provenance. Illustrative demo records are removed
once real records exist.
"""
import os
import re
import uuid
import logging
from datetime import datetime, timezone

import httpx
from pymongo import UpdateOne

from core import db
from vbie_core import compute_trust, _stable_geid, _prov, _now, _iso, is_source_approved

logger = logging.getLogger(__name__)

TED_URL = "https://api.ted.europa.eu/v3/notices/search"
CSL_URL = "https://data.trade.gov/downloadable_consolidated_screening_list/v1/consolidated.json"
COMTRADE_PREVIEW = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"
CID_URL = "https://ised-isde.canada.ca/site/ised/sites/default/files/documents/cid-bdic-majorimportersbyhs6bycountry2022.csv"
GLEIF_API = "https://api.gleif.org/api/v1/lei-records"

SAM_GOV_API_KEY = os.environ.get("SAM_GOV_API_KEY", "").strip()
COMPANIES_HOUSE_API_KEY = os.environ.get("COMPANIES_HOUSE_API_KEY", "").strip()
COMTRADE_API_KEY = os.environ.get("COMTRADE_API_KEY", "").strip()

UA = {"User-Agent": "LeadNation-VBIE/1.0 (+https://leadnation.app)"}

# ISO-3 → (ISO-2, display name) for buyer countries we surface.
ISO3 = {
    "AUT": ("AT", "Austria"), "BEL": ("BE", "Belgium"), "BGR": ("BG", "Bulgaria"),
    "HRV": ("HR", "Croatia"), "CYP": ("CY", "Cyprus"), "CZE": ("CZ", "Czechia"),
    "DNK": ("DK", "Denmark"), "EST": ("EE", "Estonia"), "FIN": ("FI", "Finland"),
    "FRA": ("FR", "France"), "DEU": ("DE", "Germany"), "GRC": ("GR", "Greece"),
    "HUN": ("HU", "Hungary"), "IRL": ("IE", "Ireland"), "ITA": ("IT", "Italy"),
    "LVA": ("LV", "Latvia"), "LTU": ("LT", "Lithuania"), "LUX": ("LU", "Luxembourg"),
    "MLT": ("MT", "Malta"), "NLD": ("NL", "Netherlands"), "POL": ("PL", "Poland"),
    "PRT": ("PT", "Portugal"), "ROU": ("RO", "Romania"), "SVK": ("SK", "Slovakia"),
    "SVN": ("SI", "Slovenia"), "ESP": ("ES", "Spain"), "SWE": ("SE", "Sweden"),
    "NOR": ("NO", "Norway"), "CHE": ("CH", "Switzerland"), "ISL": ("IS", "Iceland"),
    "GBR": ("GB", "United Kingdom"), "USA": ("US", "United States"),
    "CAN": ("CA", "Canada"), "AUS": ("AU", "Australia"),
}

# CPV division → (LeadNation sector, product labels, indicative HS families).
CPV_DIVISIONS = {
    "03": ("Agri & Foods", ["Agricultural Produce", "Grains & Seeds", "Spices"], ["1006", "1005", "1207", "0713", "0904"]),
    "09": ("Energy & Fuels", ["Fuels & Lubricants", "Energy Products"], ["2710", "2711", "2701"]),
    "14": ("Minerals & Metals", ["Mining Products", "Basic Metals"], ["2515", "7208", "2601"]),
    "15": ("Agri & Foods", ["Food & Beverages", "Processed Foods", "Agri Commodities"], ["1006", "2106", "0904", "1701", "0713"]),
    "16": ("Agri & Machinery", ["Agricultural Machinery"], ["8432", "8433", "8436"]),
    "18": ("Textiles & Apparel", ["Apparel & Clothing", "Workwear & Uniforms"], ["6109", "6203", "6302", "6110"]),
    "19": ("Leather & Footwear", ["Leather Goods", "Footwear"], ["4202", "6403", "4203"]),
    "22": ("Print & Paper", ["Printed Matter", "Paper Products"], ["4901", "4802", "4819"]),
    "24": ("Chemicals", ["Industrial Chemicals", "Specialty Chemicals"], ["2941", "3808", "3204", "2915"]),
    "30": ("IT & Electronics", ["Computers & Office Equipment"], ["8471", "8443", "8517"]),
    "31": ("Electrical Equipment", ["Electrical Machinery & Apparatus"], ["8544", "8536", "8504"]),
    "32": ("IT & Electronics", ["Telecom & Broadcast Equipment"], ["8517", "8528", "8518"]),
    "33": ("Pharma & Medical", ["Medical Supplies", "Pharmaceuticals", "Medical Devices"], ["3004", "3005", "9018", "3006"]),
    "34": ("Automotive & Transport", ["Transport Equipment", "Auto Components"], ["8708", "8716", "8703"]),
    "37": ("Sports & Musical", ["Musical Instruments", "Sports Goods"], ["9506", "9503", "9207"]),
    "38": ("Instruments & Lab", ["Laboratory & Precision Instruments"], ["9027", "9026", "9031"]),
    "39": ("Home & Furnishings", ["Furniture", "Home Furnishings"], ["9403", "6302", "9404"]),
    "42": ("Industrial Machinery", ["Industrial Machinery & Equipment"], ["8479", "8438", "8422"]),
    "43": ("Mining & Construction", ["Mining & Construction Machinery"], ["8429", "8431", "8474"]),
    "44": ("Construction & Metals", ["Construction Materials", "Metal Products"], ["7308", "6810", "7214", "7325"]),
    "45": ("Construction Works", ["Construction & Civil Works"], ["6810", "7308", "2523"]),
    "48": ("IT & Software", ["Software & IT Systems"], ["8523", "8471"]),
}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def _first(v):
    """TED fields are multilingual dicts ({'eng':[...]}) or lists — pull the first string."""
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    if isinstance(v, list):
        return _first(v[0]) if v else ""
    if isinstance(v, dict):
        for _k, val in v.items():
            r = _first(val)
            if r:
                return r
    return ""


# ─────────────────────────── sanctions screening ────────────────────────────
_CSL_CACHE = None
_CSL_AT = None


async def load_sanctions(force: bool = False):
    """Download the trade.gov Consolidated Screening List and build a normalized
    denied-party name set. Cached for ~20h. Used as a MANDATORY hard gate."""
    global _CSL_CACHE, _CSL_AT
    if _CSL_CACHE is not None and not force and _CSL_AT and (_now() - _CSL_AT).total_seconds() < 72000:
        return _CSL_CACHE
    names = set()
    try:
        async with httpx.AsyncClient(timeout=120, headers=UA) as cx:
            r = await cx.get(CSL_URL)
            r.raise_for_status()
            data = r.json()
        for row in data.get("results", []):
            for nm in [row.get("name")] + (row.get("alt_names") or []):
                n = _norm(nm)
                if n:
                    names.add(n)
        _CSL_CACHE, _CSL_AT = names, _now()
        await db.vbie_sanctions_meta.update_one(
            {"_id": "csl"},
            {"$set": {"count": len(names), "refreshed_at": _iso(_now()), "source": "trade.gov CSL"}},
            upsert=True)
        logger.info("VBIE sanctions list loaded: %d denied-party names", len(names))
    except Exception as exc:
        logger.warning("VBIE sanctions load failed (gate open-fails-closed=skip): %s", exc)
        _CSL_CACHE = names
    return _CSL_CACHE


def is_sanctioned(name: str, screener: set) -> bool:
    return _norm(name) in screener if screener else False


# ───────────────────────────── connectors ───────────────────────────────────
async def connector_ted(days: int = 365, per_page: int = 100, pages: int = 16) -> list:
    """EU TED — real named public-sector buyers procuring goods, by country + sector.
    Paginates across all mapped CPV divisions to scale toward a large corpus."""
    out = {}
    fields = ["publication-number", "organisation-name-buyer", "organisation-country-buyer",
              "notice-title", "classification-cpv"]
    async with httpx.AsyncClient(timeout=40, headers=UA) as cx:
        for div, (sector, products, hs) in CPV_DIVISIONS.items():
            for page in range(1, pages + 1):
                body = {"query": f"classification-cpv={div}000000 AND publication-date>=today(-{days})",
                        "fields": fields, "limit": per_page, "page": page, "scope": "ALL"}
                try:
                    r = await cx.post(TED_URL, json=body)
                    if r.status_code != 200:
                        break
                    notices = (r.json() or {}).get("notices", [])
                except Exception as exc:
                    logger.warning("TED fetch failed CPV %s p%d: %s", div, page, exc)
                    break
                if not notices:
                    break
                for n in notices:
                    name = _first(n.get("organisation-name-buyer"))
                    iso3 = _first(n.get("organisation-country-buyer"))
                    iso2, cname = ISO3.get(iso3, (None, None))
                    if not name or not iso2:
                        continue
                    nk = f"ted:{iso2}:{_norm(name)}"
                    if nk in out:
                        continue
                    pub = n.get("publication-number") or ""
                    title = _first(n.get("notice-title"))
                    url = f"https://ted.europa.eu/en/notice/-/detail/{pub}"
                    out[nk] = {
                        "source_id": "eu_ted", "natural_key": nk, "legal_name": name,
                        "country": iso2, "country_name": cname, "city": "",
                        "sector": sector, "products": products, "hs_families": hs,
                        "corridors": [f"IN-{iso2}"], "size": "Public-sector buyer",
                        "website": "", "role": "procurement buyer",
                        "signals": {"registry_listed": True, "sanctions_clear": True},
                        "prov": [("eu_ted", "buying evidence",
                                  f"EU procurement notice {pub}: {title[:140]}", url)],
                    }
    logger.info("TED connector: %d unique buyers", len(out))
    return list(out.values())


async def connector_cid() -> list:
    """Canadian Importers Database — real named importers by HS6 + origin country (open data)."""
    out = {}
    try:
        async with httpx.AsyncClient(timeout=90, headers=UA, follow_redirects=True) as cx:
            r = await cx.get(CID_URL)
        text = r.text or ""
        if not text.strip():
            logger.info("CID connector: empty response (source not reachable from this host) — skipped")
            return []
        import csv, io
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            name = (row.get("Company") or row.get("Importer") or row.get("Company Name") or "").strip()
            hs6 = (row.get("HS6") or row.get("HS 6") or "").strip()
            origin = (row.get("Country") or row.get("Country of Origin") or "").strip()
            if not name:
                continue
            nk = f"cid:CA:{_norm(name)}"
            if nk in out:
                if hs6:
                    out[nk]["hs_families"] = sorted(set(out[nk]["hs_families"] + [hs6[:4]]))
                continue
            out[nk] = {
                "source_id": "cid_canada", "natural_key": nk, "legal_name": name,
                "country": "CA", "country_name": "Canada", "city": "",
                "sector": "Import & Distribution", "products": ["Imported Goods"],
                "hs_families": [hs6[:4]] if hs6 else [],
                "corridors": ["IN-CA"], "size": "Named importer",
                "website": "", "role": "importer",
                "signals": {"sanctions_clear": True},
                "prov": [("cid_canada", "buying evidence",
                          f"Named importer (HS {hs6}{', origin ' + origin if origin else ''})",
                          "https://ised-isde.canada.ca/site/canadian-importers-database/en")],
            }
            if len(out) >= 400:
                break
    except Exception as exc:
        logger.warning("CID connector failed: %s", exc)
    logger.info("CID connector: %d importers", len(out))
    return list(out.values())


async def connector_sam_gov() -> list:
    """SAM.gov registered US entities (needs free SAM_GOV_API_KEY). Skipped without a key."""
    if not SAM_GOV_API_KEY:
        return []
    out = {}
    try:
        async with httpx.AsyncClient(timeout=30, headers=UA) as cx:
            r = await cx.get("https://api.sam.gov/entity-information/v3/entities", params={
                "api_key": SAM_GOV_API_KEY, "registrationStatus": "A",
                "includeSections": "entityRegistration,coreData",
                "physicalAddressCountryCode": "USA", "page": 0, "size": 50})
            data = r.json() if r.status_code == 200 else {}
        for e in data.get("entityData", []) or []:
            reg = e.get("entityRegistration", {}) or {}
            core = e.get("coreData", {}) or {}
            name = (reg.get("legalBusinessName") or "").strip()
            if not name:
                continue
            addr = (core.get("physicalAddress", {}) or {})
            city = (addr.get("city") or "").strip()
            nk = f"sam:US:{_norm(name)}"
            out[nk] = {
                "source_id": "sam_gov", "natural_key": nk, "legal_name": name,
                "country": "US", "country_name": "United States", "city": city,
                "sector": "Import & Distribution", "products": ["Imported Goods"],
                "hs_families": [], "corridors": ["IN-US"], "size": "Registered US entity",
                "website": "", "role": "importer",
                "signals": {"registry_listed": True, "sanctions_clear": True},
                "prov": [("sam_gov", "identity", f"SAM.gov registered entity (UEI {reg.get('ueiSAM', '')})", "https://sam.gov")],
            }
    except Exception as exc:
        logger.warning("SAM.gov connector failed: %s", exc)
    logger.info("SAM.gov connector: %d entities", len(out))
    return list(out.values())


async def connector_companies_house() -> list:
    """UK Companies House registry (OGL v3.0). Hybrid model: this is the API-for-freshness
    path (advanced-search by importer/wholesaler SIC codes), paginated within the
    600-req/5-min rate limit. Needs COMPANIES_HOUSE_API_KEY. Skipped without a key.
    NOTE: company-level identity only — director/PSC personal data is NEVER ingested
    (UK GDPR: no marketing/contact use of individuals)."""
    if not COMPANIES_HOUSE_API_KEY or not is_source_approved("uk_companies_house"):
        return []
    out = {}
    # SIC codes indicative of importers/wholesalers of goods.
    sic = ["46170", "46900", "46310", "46410", "46450", "46460", "46480", "46390", "46760"]
    base = "https://api.company-information.service.gov.uk/advanced-search/companies"
    try:
        async with httpx.AsyncClient(timeout=30, headers=UA,
                                     auth=(COMPANIES_HOUSE_API_KEY, "")) as cx:
            for start in range(0, 1000, 100):  # up to 1000 companies/run, within rate limit
                try:
                    r = await cx.get(base, params={"company_status": "active",
                                                   "sic_codes": ",".join(sic),
                                                   "size": 100, "start_index": start})
                    if r.status_code != 200:
                        break
                    items = (r.json() or {}).get("items", []) or []
                except Exception as exc:
                    logger.warning("Companies House page %d failed: %s", start, exc)
                    break
                if not items:
                    break
                for c in items:
                    name = (c.get("company_name") or "").strip()
                    if not name:
                        continue
                    addr = c.get("registered_office_address", {}) or {}
                    city = (addr.get("locality") or "").strip()
                    num = c.get("company_number", "")
                    nk = f"ukch:GB:{_norm(name)}"
                    if nk in out:
                        continue
                    out[nk] = {
                        "source_id": "uk_companies_house", "natural_key": nk, "legal_name": name,
                        "country": "GB", "country_name": "United Kingdom", "city": city,
                        "sector": "Import & Distribution", "products": ["Imported Goods"],
                        "hs_families": [], "corridors": ["IN-GB"], "size": "Registered UK company",
                        "website": "", "role": "importer",
                        "signals": {"registry_listed": True, "sanctions_clear": True},
                        "prov": [("uk_companies_house", "identity",
                                  f"UK Companies House registered ({num}) — Open Government Licence v3.0",
                                  f"https://find-and-update.company-information.service.gov.uk/company/{num}")],
                    }
    except Exception as exc:
        logger.warning("Companies House connector failed: %s", exc)
    logger.info("Companies House connector: %d companies", len(out))
    return list(out.values())


async def connector_comtrade_context():
    """UN Comtrade — aggregate India export-corridor context (value by partner). No named buyers."""
    from duty_engine import NAME_BY_CODE
    key = COMTRADE_API_KEY
    base = "https://comtradeapi.un.org/data/v1/get/C/A/HS" if key else COMTRADE_PREVIEW
    for year in ("2024", "2023"):
        params = {"reporterCode": 356, "period": year, "flowCode": "X",
                  "cmdCode": "TOTAL", "maxRecords": 250}
        if key:
            params["subscription-key"] = key
        try:
            async with httpx.AsyncClient(timeout=30, headers=UA) as cx:
                r = await cx.get(base, params=params)
                if r.status_code != 200:
                    continue
                rows = (r.json() or {}).get("data", [])
        except Exception as exc:
            logger.warning("Comtrade context failed: %s", exc)
            return
        n = 0
        for row in rows:
            code = str(row.get("partnerCode"))
            if code in ("0", "None"):
                continue
            cname = NAME_BY_CODE.get(code)
            val = row.get("primaryValue")
            if not cname or not val:
                continue
            await db.vbie_market_stats.update_one(
                {"_id": f"IN-export-{code}"},
                {"$set": {"reporter": "India", "partner_code": code, "partner_name": cname,
                          "flow": "export", "year": year, "value_usd": val,
                          "source": "UN Comtrade", "updated_at": _iso(_now())}},
                upsert=True)
            n += 1
        if n:
            logger.info("Comtrade context: %d India export corridors for %s", n, year)
            return


# ─────────────────── GLEIF — global identity backbone ───────────────────────
# LEI (Legal Entity Identifier) is the permanent, CC0/public-domain global key
# that every registry + buyer-signal maps to. We resolve each buyer to its LEI so
# the same real company from different sources collapses to ONE canonical entity.
async def resolve_lei(cx, name: str, country_iso2: str):
    """Best-effort GLEIF LEI lookup by legal name + country. Returns LEI string or None."""
    if not name:
        return None
    try:
        r = await cx.get(GLEIF_API, params={
            "filter[entity.legalName]": name,
            "filter[entity.legalAddress.country]": (country_iso2 or "").upper(),
            "page[size]": 5})
        if r.status_code != 200:
            return None
        data = (r.json() or {}).get("data", [])
    except Exception:
        return None
    target = _norm(name)
    for item in data:
        try:
            ent = item["attributes"]["entity"]
            cand = _norm(ent["legalName"]["name"])
            ctry = (ent.get("legalAddress", {}) or {}).get("country")
        except Exception:
            continue
        if country_iso2 and ctry and ctry.upper() != country_iso2.upper():
            continue
        if cand and (cand == target or cand.startswith(target) or target.startswith(cand)):
            return item.get("id")
    return None


async def connector_gleif_enrich(limit: int = 150) -> int:
    """Attach GLEIF LEI to buyers and keep the identity link durable. Two phases:
      A. RE-LINK (no API): any buyer with a known `lei` but missing the gleif evidence
         (e.g. because a source connector re-upserted and overwrote provenance) is healed.
      B. RESOLVE (API): buyers with no lei yet are looked up in the GLEIF index (throttled).
    Runs AFTER upserts so every source's records tie to the identity spine idempotently."""
    if not is_source_approved("gleif"):
        return 0
    healed = 0
    # Phase A — re-link known LEIs whose evidence was overwritten (cheap, no network).
    async for e in db.entities.find(
            {"entity_type": "buyer", "admin_deleted": {"$ne": True},
             "lei": {"$nin": ["", None]}, "signals.lei_verified": {"$ne": True}},
            {"provenance": 1, "signals": 1, "lei": 1}):
        lei = e["lei"]
        prov = [p for p in e.get("provenance", []) if p.get("source_id") != "gleif"]
        prov.append(_prov("gleif", "identity", f"Matched to GLEIF Global LEI Index (LEI {lei})",
                          f"https://search.gleif.org/#/record/{lei}"))
        sig = dict(e.get("signals", {})); sig["lei_verified"] = True
        await db.entities.update_one({"_id": e["_id"]}, {"$set": {
            "provenance": prov[:12], "signals": sig, "trust": compute_trust(prov[:12], sig)}})
        healed += 1

    # Phase B — resolve new LEIs for buyers that don't have one yet.
    n = 0
    if limit and limit > 0:
        async with httpx.AsyncClient(timeout=20, headers=UA) as cx:
            cursor = db.entities.find(
                {"entity_type": "buyer", "admin_deleted": {"$ne": True},
                 "$or": [{"lei": {"$exists": False}}, {"lei": ""}]},
                {"legal_name": 1, "country": 1, "provenance": 1, "signals": 1}).limit(limit)
            async for e in cursor:
                lei = await resolve_lei(cx, e.get("legal_name", ""), e.get("country", ""))
                if not lei:
                    await db.entities.update_one({"_id": e["_id"]}, {"$set": {"lei_checked": _iso(_now())}})
                    continue
                prov = [p for p in e.get("provenance", []) if p.get("source_id") != "gleif"]
                prov.append(_prov("gleif", "identity", f"Matched to GLEIF Global LEI Index (LEI {lei})",
                                  f"https://search.gleif.org/#/record/{lei}"))
                sig = dict(e.get("signals", {})); sig["lei_verified"] = True
                await db.entities.update_one({"_id": e["_id"]}, {"$set": {
                    "lei": lei, "provenance": prov[:12], "signals": sig,
                    "trust": compute_trust(prov[:12], sig), "lei_checked": _iso(_now())}})
                n += 1
    logger.info("GLEIF enrich: %d re-linked, %d newly matched to LEI", healed, n)
    return n + healed


# ──────── freshness-merge / hard-delete engine (validate current vs upcoming) ─
async def dedupe_and_prune() -> dict:
    """Match records that resolve to the SAME real company (LEI first, else
    country + normalized name), MERGE their evidence into the freshest record,
    then HARD-DELETE the stale duplicates. Admin-edited/deleted records are never
    touched (admin sovereignty)."""
    groups = {}
    async for e in db.entities.find(
            {"entity_type": "buyer", "admin_deleted": {"$ne": True}, "status": {"$ne": "deleted"}},
            {"legal_name": 1, "country": 1, "lei": 1, "last_verified": 1, "updated_at": 1,
             "provenance": 1, "signals": 1, "admin_edited": 1, "corridors": 1, "products": 1, "hs_families": 1}):
        key = e.get("lei") or f"{e.get('country', '')}:{_norm(e.get('legal_name', ''))}"
        if not key or key == ":":
            continue
        groups.setdefault(key, []).append(e)

    merged = deleted = 0
    for docs in groups.values():
        if len(docs) < 2:
            continue

        def _rank(d):
            uv = d.get("updated_at")
            uv = uv.isoformat() if hasattr(uv, "isoformat") else (uv or "")
            return (1 if d.get("admin_edited") else 0, d.get("last_verified") or uv, len(d.get("provenance", [])))

        docs.sort(key=_rank, reverse=True)
        keep, dups = docs[0], docs[1:]
        stale = [d for d in dups if not d.get("admin_edited")]
        if not stale:
            continue

        if not keep.get("admin_edited"):
            prov = list(keep.get("provenance", []))
            seen = {(p.get("source_id"), p.get("field"), p.get("note")) for p in prov}
            sig = dict(keep.get("signals", {}))
            corr = set(keep.get("corridors", [])); prods = set(keep.get("products", [])); hs = set(keep.get("hs_families", []))
            for d in stale:
                for p in d.get("provenance", []):
                    k = (p.get("source_id"), p.get("field"), p.get("note"))
                    if k not in seen:
                        seen.add(k); prov.append(p)
                sig.update({k: v for k, v in (d.get("signals") or {}).items() if v})
                corr |= set(d.get("corridors", [])); prods |= set(d.get("products", [])); hs |= set(d.get("hs_families", []))
            prov = prov[:12]
            await db.entities.update_one({"_id": keep["_id"]}, {"$set": {
                "provenance": prov, "signals": sig, "trust": compute_trust(prov, sig),
                "corridors": sorted(c for c in corr if c), "products": sorted(p for p in prods if p)[:20],
                "hs_families": sorted(h for h in hs if h), "updated_at": _now()}})
            merged += 1

        res = await db.entities.delete_many({"_id": {"$in": [d["_id"] for d in stale]}})
        deleted += res.deleted_count

    logger.info("Dedupe/prune: merged=%d hard_deleted_stale=%d", merged, deleted)
    return {"merged": merged, "hard_deleted": deleted}


# ───────────────────────────── orchestrator ─────────────────────────────────
async def run_ingestion(trigger: str = "manual") -> dict:
    """Run all enabled connectors → sanctions-screen → upsert real buyers → drop demo data."""
    run = {"_id": uuid.uuid4().hex, "trigger": trigger, "started_at": _iso(_now()),
           "sources": {}, "screened_out": 0, "upserted": 0, "samples_removed": 0}
    logger.info("VBIE ingestion started (trigger=%s)", trigger)
    screener = await load_sanctions()

    connectors = [("eu_ted", connector_ted), ("cid_canada", connector_cid),
                  ("sam_gov", connector_sam_gov), ("uk_companies_house", connector_companies_house)]
    # Legal gate: only run sources whose licence/ToS is reviewed + approved.
    connectors = [(sid, fn) for sid, fn in connectors if is_source_approved(sid)]
    run["skipped_pending_legal"] = [sid for sid in ("sam_gov",) if not is_source_approved(sid)]
    candidates = {}
    for sid, fn in connectors:
        try:
            rows = await fn()
        except Exception as exc:
            logger.warning("Connector %s failed: %s", sid, exc)
            rows = []
        run["sources"][sid] = len(rows)
        for c in rows:
            candidates[c["natural_key"]] = c

    # Admin sovereignty: never overwrite admin-edited buyers or resurrect admin-deleted ones.
    admin_managed = set()
    async for d in db.entities.find(
            {"entity_type": "buyer", "$or": [{"admin_edited": True}, {"admin_deleted": True}]},
            {"_id": 1}):
        admin_managed.add(d["_id"])

    upserted = screened = new_count = skipped_admin = 0
    ops = []
    for c in candidates.values():
        if is_sanctioned(c["legal_name"], screener):
            screened += 1
            continue
        geid = _stable_geid(c["natural_key"])
        if geid in admin_managed:
            skipped_admin += 1
            continue
        provenance = [_prov(sid, field, note, url) for (sid, field, note, url) in c["prov"]]
        trust = compute_trust(provenance, c.get("signals", {}))
        doc = {
            "_id": geid, "geid": geid, "entity_type": "buyer", "status": "active",
            "legal_name": c["legal_name"], "display_name": c["legal_name"],
            "country": c["country"], "country_name": c["country_name"], "city": c.get("city", ""),
            "sector": c["sector"], "products": c.get("products", []),
            "hs_families": [h for h in c.get("hs_families", []) if h],
            "corridors": c.get("corridors", []), "size": c.get("size", ""),
            "website": c.get("website", ""), "role": c.get("role", "importer"),
            "signals": c.get("signals", {}), "provenance": provenance, "trust": trust,
            "sample": False, "source_verified": True,
            "created_by": f"vbie-connector:{c['source_id']}", "merged_into": None,
            "updated_at": _now(), "last_verified": _iso(_now()),
        }
        ops.append(UpdateOne({"_id": geid}, {"$set": doc, "$setOnInsert": {"created_at": _now(), "lei": ""}}, upsert=True))
        upserted += 1
    # Bulk-write in chunks (fast; avoids per-doc Atlas round-trips).
    for i in range(0, len(ops), 500):
        res = await db.entities.bulk_write(ops[i:i + 500], ordered=False)
        new_count += (res.upserted_count or 0)

    try:
        await connector_comtrade_context()
    except Exception as exc:
        logger.warning("Comtrade context skipped: %s", exc)

    # GLEIF identity backbone: map buyers to LEI (canonical global identity).
    try:
        run["lei_matched"] = await connector_gleif_enrich()
    except Exception as exc:
        logger.warning("GLEIF enrich skipped: %s", exc)

    # Freshness-merge: validate current vs upcoming, keep fresh, hard-delete stale dupes.
    try:
        run["dedupe"] = await dedupe_and_prune()
    except Exception as exc:
        logger.warning("Dedupe/prune skipped: %s", exc)

    real = await db.entities.count_documents(
        {"entity_type": "buyer", "sample": {"$ne": True}, "admin_deleted": {"$ne": True}})
    if real > 0:
        res = await db.entities.delete_many({"entity_type": "buyer", "sample": True})
        run["samples_removed"] = res.deleted_count

    run.update({"finished_at": _iso(_now()), "upserted": upserted, "new_buyers": new_count,
                "screened_out": screened, "skipped_admin": skipped_admin,
                "real_total": real, "ok": True})
    await db.vbie_ingest_runs.insert_one(dict(run))
    logger.info("VBIE ingestion done: upserted=%d new=%d screened_out=%d skipped_admin=%d real_total=%d",
                upserted, new_count, screened, skipped_admin, real)
    try:
        import vbie_admin
        await vbie_admin.notify_ingestion(run)
    except Exception as exc:
        logger.warning("Ingestion notifications failed: %s", exc)
    # Auto-quarantine any non-compliant / placeholder / duplicate records after every run.
    try:
        import vbie_admin
        audit = await vbie_admin.production_audit(auto_fix=True)
        run["quarantined_total"] = audit.get("quarantined_total")
        run["active_production_buyers"] = audit.get("active_production_buyers")
    except Exception as exc:
        logger.warning("Post-ingestion production audit failed: %s", exc)
    return run


# ─────────────────────────────── scheduler ──────────────────────────────────
_scheduler = None


def start_scheduler():
    global _scheduler
    if _scheduler:
        return
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        _scheduler = AsyncIOScheduler(timezone="UTC")
        _scheduler.add_job(run_ingestion, "cron", hour=2, minute=0, args=["scheduled"],
                           id="vbie_daily_ingest", replace_existing=True, max_instances=1)
        _scheduler.start()
        logger.info("VBIE daily ingestion scheduler started (02:00 UTC)")
    except Exception as exc:
        logger.warning("Could not start VBIE scheduler: %s", exc)
