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
import io
import csv
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

# TED buyer-contact search fields (verified against api.ted.europa.eu v3).
TED_CONTACT_FIELDS = ["organisation-email-buyer", "organisation-tel-buyer",
                      "organisation-city-buyer", "organisation-street-buyer",
                      "organisation-post-code-buyer", "organisation-internet-address-buyer",
                      "touchpoint-contact-point-buyer", "organisation-contact-point-buyer"]


def _ted_first(v) -> str:
    if isinstance(v, list):
        for x in v:
            if x:
                return str(x).strip()
        return ""
    return str(v).strip() if v else ""


def ted_extract_contact(n: dict) -> dict:
    """Pull the buyer's official contact point out of a TED notice record."""
    street = _ted_first(n.get("organisation-street-buyer"))
    city = _ted_first(n.get("organisation-city-buyer"))
    postcode = _ted_first(n.get("organisation-post-code-buyer"))
    addr = ", ".join([p for p in (street, postcode, city) if p])
    return {
        "email": _ted_first(n.get("organisation-email-buyer")),
        "phone": _ted_first(n.get("organisation-tel-buyer")),
        "website": _ted_first(n.get("organisation-internet-address-buyer")),
        "address": addr, "city": city,
        "contact_name": _ted_first(n.get("touchpoint-contact-point-buyer"))
        or _ted_first(n.get("organisation-contact-point-buyer")),
    }


def has_contact(contact: dict) -> bool:
    """Owner rule: a buyer is only kept/shown if it has an email OR phone."""
    c = contact or {}
    return bool((c.get("email") or "").strip() or (c.get("phone") or "").strip())

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
              "notice-title", "classification-cpv"] + TED_CONTACT_FIELDS
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
                    contact = ted_extract_contact(n)
                    if not has_contact(contact):
                        continue  # owner rule: skip buyers with no email/phone
                    nk = f"ted:{iso2}:{_norm(name)}"
                    if nk in out:
                        continue
                    pub = n.get("publication-number") or ""
                    title = _first(n.get("notice-title"))
                    url = f"https://ted.europa.eu/en/notice/-/detail/{pub}"
                    out[nk] = {
                        "source_id": "eu_ted", "natural_key": nk, "legal_name": name,
                        "country": iso2, "country_name": cname, "city": contact.get("city", ""),
                        "sector": sector, "products": products, "hs_families": hs,
                        "corridors": [f"IN-{iso2}"], "size": "Public-sector buyer",
                        "website": contact.get("website", ""), "role": "procurement buyer",
                        "contact": contact,
                        "signals": {"registry_listed": True, "sanctions_clear": True},
                        "prov": [("eu_ted", "buying evidence",
                                  f"EU procurement notice {pub}: {title[:140]}", url)],
                    }
    logger.info("TED connector: %d unique buyers with contact", len(out))
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


async def connector_companies_house(start_index: int = 0, max_pages: int = 10) -> list:
    """UK Companies House registry (OGL v3.0). Hybrid model: this is the API-for-freshness
    path (advanced-search by importer/wholesaler SIC codes), paginated within the
    600-req/5-min rate limit. `start_index` supports checkpointed incremental discovery
    (the recurring engine advances it each run to keep discovering NEW companies).
    Needs COMPANIES_HOUSE_API_KEY. Skipped without a key.
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
            for start in range(start_index, start_index + max_pages * 100, 100):
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
                        "identifiers": {"company_number": num},
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


# ──────── duplicate resolution engine (multi-key, audit-preserving) ──────────
def _dedupe_keys(e: dict) -> list:
    """All identity keys a record can match on: LEI, company/registration/VAT/business
    numbers, and country+normalized-name. Two records sharing ANY key are the same co."""
    keys = []
    if e.get("lei"):
        keys.append(f"lei:{e['lei']}")
    ids = e.get("identifiers") or {}
    for k in ("company_number", "registration_number", "vat", "business_number"):
        v = ids.get(k)
        if v:
            keys.append(f"{k}:{(e.get('country') or '')}:{str(v).strip().upper()}")
    nm = _norm(e.get("legal_name", ""))
    if nm:
        keys.append(f"name:{e.get('country', '')}:{nm}")
    return keys


async def dedupe_and_prune() -> dict:
    """Never allow duplicate buyers. Groups records that share ANY identity key
    (LEI / company number / reg number / VAT / business number / country+name) using
    union-find, MERGES evidence+trust+provenance+relationships into the newest verified
    record, ARCHIVES obsolete duplicates to `vbie_archive` (audit history preserved),
    then HARD-DELETES them. Admin-edited/deleted records are never touched."""
    # 1. Load candidates + build union-find over shared keys.
    docs = []
    key_owner = {}
    parent = {}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    async for e in db.entities.find(
            {"entity_type": "buyer", "admin_deleted": {"$ne": True}, "status": {"$ne": "deleted"}},
            {"legal_name": 1, "country": 1, "lei": 1, "identifiers": 1, "last_verified": 1,
             "updated_at": 1, "provenance": 1, "signals": 1, "admin_edited": 1,
             "corridors": 1, "products": 1, "hs_families": 1, "trust": 1}):
        eid = e["_id"]; parent[eid] = eid; docs.append(e)
        for k in _dedupe_keys(e):
            if k in key_owner:
                union(eid, key_owner[k])
            else:
                key_owner[k] = eid

    groups = {}
    for e in docs:
        groups.setdefault(find(e["_id"]), []).append(e)

    merged = deleted = 0
    for members in groups.values():
        if len(members) < 2:
            continue

        def _rank(d):
            uv = d.get("updated_at")
            uv = uv.isoformat() if hasattr(uv, "isoformat") else (uv or "")
            return (1 if d.get("admin_edited") else 0, d.get("last_verified") or uv, len(d.get("provenance", [])))

        members.sort(key=_rank, reverse=True)
        keep, dups = members[0], members[1:]
        stale = [d for d in dups if not d.get("admin_edited")]
        if not stale:
            continue

        if not keep.get("admin_edited"):
            prov = list(keep.get("provenance", []))
            seen = {(p.get("source_id"), p.get("field"), p.get("note")) for p in prov}
            sig = dict(keep.get("signals", {}))
            ids = dict(keep.get("identifiers", {}))
            corr = set(keep.get("corridors", [])); prods = set(keep.get("products", [])); hs = set(keep.get("hs_families", []))
            lei = keep.get("lei", "")
            for d in stale:
                for p in d.get("provenance", []):
                    k = (p.get("source_id"), p.get("field"), p.get("note"))
                    if k not in seen:
                        seen.add(k); prov.append(p)
                sig.update({k: v for k, v in (d.get("signals") or {}).items() if v})
                for k, v in (d.get("identifiers") or {}).items():
                    ids.setdefault(k, v)
                corr |= set(d.get("corridors", [])); prods |= set(d.get("products", [])); hs |= set(d.get("hs_families", []))
                lei = lei or d.get("lei", "")
            prov = prov[:12]
            await db.entities.update_one({"_id": keep["_id"]}, {"$set": {
                "provenance": prov, "signals": sig, "trust": compute_trust(prov, sig),
                "identifiers": ids, "lei": lei,
                "corridors": sorted(c for c in corr if c), "products": sorted(p for p in prods if p)[:20],
                "hs_families": sorted(h for h in hs if h), "updated_at": _now()}})
            merged += 1

        # Archive obsolete duplicates (preserve evidence/audit) BEFORE hard delete.
        stale_ids = [d["_id"] for d in stale]
        archived = await db.entities.find({"_id": {"$in": stale_ids}}).to_list(len(stale_ids))
        if archived:
            for a in archived:
                a["archived_at"] = _iso(_now()); a["archived_reason"] = "duplicate"; a["merged_into"] = keep["_id"]
            await db.vbie_archive.insert_many(archived)
        res = await db.entities.delete_many({"_id": {"$in": stale_ids}})
        deleted += res.deleted_count

    logger.info("Dedupe/prune (multi-key): merged=%d hard_deleted=%d archived", merged, deleted)
    return {"merged": merged, "hard_deleted": deleted}


# ──────────────── bulk connectors (monthly full-register loaders) ────────────
async def upsert_candidates(rows: list, source_label: str = "bulk") -> int:
    """Shared upsert used by bulk loaders: sanctions-screen → respect admin sovereignty →
    bulk-write into the ONE entities graph (same path/schema as run_ingestion)."""
    if not rows:
        return 0
    screener = await load_sanctions()
    admin_managed = set()
    async for d in db.entities.find(
            {"entity_type": "buyer", "$or": [{"admin_edited": True}, {"admin_deleted": True}]}, {"_id": 1}):
        admin_managed.add(d["_id"])
    ops = []
    skipped_no_contact = 0
    for c in rows:
        if is_sanctioned(c["legal_name"], screener):
            continue
        # ENGINE RULE (all ingestion paths): only buyers WITH contact (email/phone) are stored.
        contact = c.get("contact") or {}
        if not has_contact(contact):
            skipped_no_contact += 1
            continue
        geid = _stable_geid(c["natural_key"])
        if geid in admin_managed:
            continue
        provenance = [_prov(sid, field, note, url) for (sid, field, note, url) in c["prov"]]
        doc = {
            "_id": geid, "geid": geid, "entity_type": "buyer", "status": "active",
            "legal_name": c["legal_name"], "display_name": c["legal_name"],
            "country": c["country"], "country_name": c["country_name"], "city": c.get("city", ""),
            "sector": c["sector"], "products": c.get("products", []),
            "hs_families": [h for h in c.get("hs_families", []) if h],
            "corridors": c.get("corridors", []), "size": c.get("size", ""),
            "website": c.get("website", ""), "role": c.get("role", "importer"),
            "signals": c.get("signals", {}), "provenance": provenance,
            "trust": compute_trust(provenance, c.get("signals", {})),
            "identifiers": c.get("identifiers", {}), "sample": False, "source_verified": True,
            "contact": contact, "has_contact": True,
            "created_by": f"vbie-bulk:{c['source_id']}", "merged_into": None,
            "updated_at": _now(), "last_verified": _iso(_now()),
        }
        ops.append(UpdateOne({"_id": geid}, {"$set": doc, "$setOnInsert": {"created_at": _now(), "lei": ""}}, upsert=True))
    n = 0
    for i in range(0, len(ops), 500):
        res = await db.entities.bulk_write(ops[i:i + 500], ordered=False)
        n += (res.upserted_count or 0)
    logger.info("Bulk upsert (%s): %d rows, %d new, %d skipped (no contact)", source_label, len(ops), n, skipped_no_contact)
    return n


async def connector_companies_house_bulk(max_records: int = 5000) -> list:
    """UK Companies House official MONTHLY full-register product (OGL v3.0). Streams the
    'BasicCompanyDataAsOneFile' ZIP TO DISK (pod-safe — never loads the ~500MB file into
    RAM) and parses up to max_records. HEAVY — intended for the monthly cadence / phased
    rollout. Company-level identity only (no director/PSC personal data)."""
    if not is_source_approved("uk_companies_house"):
        return []
    import zipfile
    import os
    import tempfile
    from datetime import date
    base = "http://download.companieshouse.gov.uk"
    fname = f"BasicCompanyDataAsOneFile-{date.today().replace(day=1).isoformat()}.zip"
    url = f"{base}/{fname}"
    out = []
    tmp_path = None
    try:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
        tmp_path = tmp.name
        async with httpx.AsyncClient(timeout=900, headers=UA, follow_redirects=True) as cx:
            async with cx.stream("GET", url) as resp:
                if resp.status_code != 200:
                    logger.warning("CH bulk file unavailable (%s): %s", resp.status_code, url)
                    tmp.close()
                    return []
                async for chunk in resp.aiter_bytes(1 << 20):  # 1MB chunks → disk
                    tmp.write(chunk)
        tmp.close()
        with zipfile.ZipFile(tmp_path) as z:
            name = z.namelist()[0]
            with z.open(name) as fh:
                reader = csv.DictReader((line.decode("utf-8", "ignore") for line in fh))
                for row in reader:
                    if len(out) >= max_records:
                        break
                    nm = (row.get("CompanyName") or "").strip()
                    num = (row.get("CompanyNumber") or "").strip()
                    if not nm or (row.get("CompanyStatus") or "").lower() != "active":
                        continue
                    # Quality gate: only genuine wholesale/import companies (SIC division 46),
                    # matching the API connector's bar — never label the whole register as buyers.
                    sic_texts = [(row.get(f"SICCode.SicText_{i}") or "") for i in (1, 2, 3, 4)]
                    codes = [re.match(r"\s*(\d{4,5})", s).group(1) for s in sic_texts if re.match(r"\s*(\d{4,5})", s)]
                    if not any(c.startswith("46") for c in codes):
                        continue
                    nk = f"ukch:GB:{_norm(nm)}"
                    out.append({
                        "source_id": "uk_companies_house", "natural_key": nk, "legal_name": nm,
                        "country": "GB", "country_name": "United Kingdom",
                        "city": (row.get("RegAddress.PostTown") or "").strip().title(),
                        "sector": "Import & Distribution", "products": ["Imported Goods", "Wholesale Goods"],
                        "hs_families": [], "corridors": ["IN-GB"], "size": "Registered UK company",
                        "website": "", "role": "importer", "identifiers": {"company_number": num},
                        "signals": {"registry_listed": True, "sanctions_clear": True},
                        "prov": [("uk_companies_house", "identity",
                                  f"UK Companies House full register ({num}, SIC {','.join(c for c in codes if c.startswith('46'))}) — OGL v3.0",
                                  f"https://find-and-update.company-information.service.gov.uk/company/{num}")],
                    })
    except Exception as exc:
        logger.warning("CH bulk connector failed: %s", exc)
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
    logger.info("CH bulk connector: %d companies", len(out))
    return out


async def connector_sirene(max_records: int = 5000) -> list:
    """France INSEE SIRENE (Licence Ouverte / Etalab 2.0). Requires a free INSEE API key
    (env INSEE_API_KEY). Stays DORMANT until the key is provided AND the source is added to
    APPROVED_SOURCES after terms review."""
    key = os.environ.get("INSEE_API_KEY", "").strip()
    if not key or not is_source_approved("sirene_fr"):
        logger.info("SIRENE connector dormant (needs INSEE_API_KEY + legal approval)")
        return []
    # Implementation intentionally deferred until key is supplied (api.insee.fr Sirene v3).
    return []


# ───────────────── new GREEN registry connectors (Nordics / EU) ──────────────
NO_BRREG_URL = "https://data.brreg.no/enhetsregisteret/api/enheter"
CZ_ARES_SEARCH = "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/vyhledat"


async def connector_norway(page: int = 0, size: int = 100) -> list:
    """Norway — Brønnøysund Enhetsregisteret (NLOD, commercial reuse permitted, no key).
    Wholesale/import companies (NACE division 46) as named importer buyers. Paginated for
    checkpointed incremental discovery. Company-level identity only; excludes bankrupt/deleted."""
    if not is_source_approved("no_brreg"):
        return []
    out = {}
    try:
        async with httpx.AsyncClient(timeout=40, headers=UA) as cx:
            r = await cx.get(NO_BRREG_URL, params={"naeringskode": "46", "size": size, "page": page})
            if r.status_code != 200:
                logger.warning("Norway brreg page %d status %s", page, r.status_code)
                return []
            data = (r.json() or {})
        for c in (data.get("_embedded", {}) or {}).get("enheter", []) or []:
            name = (c.get("navn") or "").strip()
            if not name or c.get("konkurs") or c.get("slettedato"):
                continue
            num = str(c.get("organisasjonsnummer") or "").strip()
            addr = c.get("forretningsadresse", {}) or {}
            city = (addr.get("poststed") or addr.get("kommune") or "").strip().title()
            nace = ((c.get("naeringskode1") or {}).get("beskrivelse") or "").strip()
            nk = f"nobr:NO:{_norm(name)}"
            if nk in out:
                continue
            out[nk] = {
                "source_id": "no_brreg", "natural_key": nk, "legal_name": name,
                "country": "NO", "country_name": "Norway", "city": city,
                "sector": "Import & Distribution", "products": ["Imported Goods", "Wholesale Goods"],
                "hs_families": [], "corridors": ["IN-NO"], "size": "Registered NO company",
                "website": "", "role": "importer", "identifiers": {"registration_number": num},
                "signals": {"registry_listed": True, "sanctions_clear": True},
                "prov": [("no_brreg", "identity",
                          f"Brønnøysund Enhetsregisteret ({num}{'; ' + nace if nace else ''}) — NLOD",
                          f"https://virksomhet.brreg.no/nb/oppslag/enheter/{num}")],
            }
    except Exception as exc:
        logger.warning("Norway connector failed: %s", exc)
    logger.info("Norway connector: %d companies (page %d)", len(out), page)
    return list(out.values())


CZ_NACE_46 = [
    "46120", "46130", "46140", "46150", "46160", "46170", "46180", "46210", "46220",
    "46230", "46240", "46310", "46320", "46330", "46340", "46350", "46360", "46370",
    "46380", "46390", "46410", "46420", "46431", "46441", "46450", "46460", "46471",
    "46480", "46491", "46492", "46510", "46520", "46610", "46620", "46630", "46640",
    "46650", "46660", "46690", "46711", "46731", "46741", "46750", "46760", "46770",
]


async def connector_ares_cz(code: str = "46170", start: int = 0, count: int = 100) -> list:
    """Czechia — ARES Business Register (Ministry of Finance open data, no key). Fetches one
    CZ-NACE wholesale (46xxx) code slice (the API caps any single query at 1000 results, so
    the recurring engine walks specific 5-digit codes with a checkpoint). Named importer buyers."""
    if not is_source_approved("cz_ares"):
        return []
    out = {}
    try:
        body = {"start": start, "pocet": count, "czNace": [code]}
        async with httpx.AsyncClient(timeout=40, headers={**UA, "Content-Type": "application/json"}) as cx:
            r = await cx.post(CZ_ARES_SEARCH, json=body)
            if r.status_code != 200:
                logger.info("Czech ARES code %s start %d status %s (skipped)", code, start, r.status_code)
                return []
            data = (r.json() or {})
        for c in data.get("ekonomickeSubjekty", []) or []:
            name = (c.get("obchodniJmeno") or "").strip()
            if not name:
                continue
            ico = str(c.get("ico") or "").strip()
            sidlo = c.get("sidlo", {}) or {}
            city = (sidlo.get("nazevObce") or "").strip()
            nk = f"czares:CZ:{_norm(name)}"
            if nk in out:
                continue
            out[nk] = {
                "source_id": "cz_ares", "natural_key": nk, "legal_name": name,
                "country": "CZ", "country_name": "Czechia", "city": city,
                "sector": "Import & Distribution", "products": ["Imported Goods", "Wholesale Goods"],
                "hs_families": [], "corridors": ["IN-CZ"], "size": "Registered CZ company",
                "website": "", "role": "importer", "identifiers": {"registration_number": ico},
                "signals": {"registry_listed": True, "sanctions_clear": True},
                "prov": [("cz_ares", "identity",
                          f"ARES Business Register (IČO {ico}, NACE {code}) — Czech MoF open data",
                          f"https://ares.gov.cz/ekonomicke-subjekty?ico={ico}")],
            }
    except Exception as exc:
        logger.warning("Czech ARES connector failed: %s", exc)
    logger.info("Czech ARES connector: %d companies (NACE %s start %d)", len(out), code, start)
    return list(out.values())


# Key-gated GREEN sources — dormant until env key + legal approval are supplied.
async def connector_dormant(source_id: str) -> list:
    logger.info("Connector %s dormant (needs API key + legal approval)", source_id)
    return []


# ──────────── checkpointed incremental discovery (recurring engine) ──────────
# Each adapter fetches the NEXT slice of NEW records for a source using its stored
# checkpoint, returning (candidate_rows, next_checkpoint, exhausted). The engine
# upserts the rows and persists next_checkpoint so daily runs keep discovering.
async def _adapt_ted(cp: dict):
    rows = await connector_ted(days=14, per_page=100, pages=3)
    return rows, {"last_run": _iso(_now())}, False


async def _adapt_ch(cp: dict):
    start = int((cp or {}).get("start_index", 0))
    rows = await connector_companies_house(start_index=start, max_pages=3)
    if not rows:
        return [], {"start_index": 0}, True  # wrap around
    return rows, {"start_index": start + 300}, False


async def _adapt_cid(cp: dict):
    if (cp or {}).get("done"):
        return [], {"done": True}, True
    rows = await connector_cid()
    return rows, {"done": True}, True


async def _adapt_norway(cp: dict):
    page = int((cp or {}).get("page", 0))
    rows = await connector_norway(page=page, size=100)
    if not rows:
        return [], {"page": 0}, True
    return rows, {"page": page + 1}, False


async def _adapt_ares(cp: dict):
    ci = int((cp or {}).get("code_idx", 0))
    start = int((cp or {}).get("start", 0))
    if ci >= len(CZ_NACE_46):
        return [], {"code_idx": 0, "start": 0}, True  # wrap around
    rows = await connector_ares_cz(code=CZ_NACE_46[ci], start=start, count=100)
    if not rows:
        return rows, {"code_idx": ci + 1, "start": 0}, (ci + 1 >= len(CZ_NACE_46))
    return rows, {"code_idx": ci, "start": start + 100}, False


DISCOVERY_ADAPTERS = {
    "eu_ted": _adapt_ted,
    "uk_companies_house": _adapt_ch,
    "cid_canada": _adapt_cid,
    "no_brreg": _adapt_norway,
    "cz_ares": _adapt_ares,
}


async def discover_source(source_id: str, checkpoint: dict) -> dict:
    """Run one source's checkpointed discovery slice → sanctions-screen → upsert into the
    shared entities graph. Returns a per-source summary incl. the advanced checkpoint."""
    adapter = DISCOVERY_ADAPTERS.get(source_id)
    if not adapter or not is_source_approved(source_id):
        return {"source": source_id, "ran": False, "new": 0, "checkpoint": checkpoint, "exhausted": True}
    rows, next_cp, exhausted = await adapter(checkpoint or {})
    new = await upsert_candidates(rows, source_label=source_id) if rows else 0
    return {"source": source_id, "ran": True, "fetched": len(rows), "new": new,
            "checkpoint": next_cp, "exhausted": exhausted}


# ───────────────────────────── orchestrator ─────────────────────────────────
async def run_ingestion(trigger: str = "manual") -> dict:
    """Run all enabled connectors → sanctions-screen → upsert real buyers → drop demo data."""
    run = {"_id": uuid.uuid4().hex, "trigger": trigger, "started_at": _iso(_now()),
           "sources": {}, "screened_out": 0, "upserted": 0, "samples_removed": 0}
    logger.info("VBIE ingestion started (trigger=%s)", trigger)
    screener = await load_sanctions()

    connectors = [("eu_ted", connector_ted), ("cid_canada", connector_cid),
                  ("sam_gov", connector_sam_gov), ("uk_companies_house", connector_companies_house),
                  ("no_brreg", connector_norway), ("cz_ares", connector_ares_cz)]
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
    no_contact = 0
    ops = []
    for c in candidates.values():
        if is_sanctioned(c["legal_name"], screener):
            screened += 1
            continue
        contact = c.get("contact") or {}
        if not has_contact(contact):
            no_contact += 1
            continue  # owner rule: only store buyers that have email/phone
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
            "identifiers": c.get("identifiers", {}),
            "contact": contact, "has_contact": True,
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
                "skipped_no_contact": no_contact,
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
