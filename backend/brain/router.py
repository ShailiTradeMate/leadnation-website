"""Brain Router — intent detection, entity extraction, engine selection, orchestration.

This is the single coordination layer. Every platform (web, app, portals) calls
`orchestrate()`. It records analytics for the admin Brain dashboard.
"""
import re
from datetime import datetime, timezone

from core import db
from reference import COUNTRIES, PRODUCTS
from engines import COUNTRY_PROFILES
from content import PRODUCTS_DB
from trade_tools import HSN_DB
from services import SERVICES_DB

from brain.engines import run_engine
from brain.providers import get_provider
from brain.context import build_context
from brain import memory

QUERIES = db.brain_queries
USAGE = db.brain_usage
CACHE = db.brain_cache

CACHE_TTL_SECONDS = 24 * 3600


def _now():
    return datetime.now(timezone.utc).isoformat()


# ---------------- Entity extraction ----------------
def extract_entities(q: str) -> dict:
    ql = q.lower()
    countries, products, services, topics = [], [], [], []

    from duty_engine import COUNTRIES as DUTY_COUNTRIES
    for _code, name in DUTY_COUNTRIES:
        if name.lower() in ql and name not in countries:
            countries.append(name)

    for slug, p in COUNTRY_PROFILES.items():
        if p["name"].lower() in ql or slug in ql or f" {p['code'].lower()} " in f" {ql} ":
            if p["name"] not in countries:
                countries.append(p["name"])
    for c in COUNTRIES:
        if c["name"].lower() in ql and c["name"] not in countries:
            countries.append(c["name"])

    for slug, p in PRODUCTS_DB.items():
        if p["name"].lower() in ql or slug.replace("-", " ") in ql:
            products.append(p["name"])
    for p in PRODUCTS:
        if p.lower() in ql and p not in products:
            products.append(p)
    # common single-word product hints
    for word in ["agarbatti", "rice", "spice", "textile", "pharma", "tea", "coffee"]:
        if word in ql and not products:
            products.append(word)

    hsn = re.findall(r"\b\d{6,8}\b", ql)

    for kw in ["iec", "gst", "rcmc", "company registration", "import export code"]:
        if kw in ql:
            services.append(kw)
    for slug, s in SERVICES_DB.items():
        if s["name"].lower() in ql:
            services.append(s["name"])

    for kw in ["beginner", "intermediate", "advanced", "incoterm", "documentation", "fta"]:
        if kw in ql:
            topics.append(kw)

    return {"countries": countries, "products": products, "hsn": hsn,
            "services": services, "topics": topics}


# ---------------- Intent → engines ----------------
KEYWORD_ENGINES = [
    (("duty", "tariff", "tax", "landed cost", "import duty", "customs duty", "duty rate", "how much duty"), ["duty_benefits"]),
    (("rodtep", "export benefit", "export incentive", "drawback", "rebate", "scheme", "incentive", "subsidy", "policy"), ["duty_benefits", "policy"]),
    (("document", "certif", "compliance", "license", "licence", "iec", "gst", "rcmc", "required to export", "what do i need", "how to import", "how to export"), ["compliance"]),
    (("hsn", "hs code", "classif", "which code"), ["product_intelligence", "trade_statistics"]),
    (("buyer", "importer", "who imports", "which countries import", "demand", "market for"), ["trade_statistics", "product_intelligence"]),
    (("trade value", "trade data", "trade statistic", "trade flow", "world trade", "top importers", "top exporters", "how much is traded", "export value", "import value", "trade volume", "biggest exporters", "largest importers"), ["trade_statistics"]),
    (("learn", "how do i start", "how to start", "beginner", "course", "guide", "teach"), ["learning"]),
    (("news", "update", "notification", "latest"), ["trade_news"]),
    (("ship", "freight", "logistic", "container", "port", "transit"), ["logistics"]),
    (("register", "registration", "service", "help me get", "apply for"), ["business_services", "compliance"]),
    (("supplier", "manufacturer", "find seller"), ["business_services"]),
    (("gold", "silver", "oil", "currency", "commodity", "exchange rate", "price of"), ["market_intelligence"]),
]


def select_engines(question: str, entities: dict):
    ql = question.lower()
    selected = []

    def add(keys):
        for k in keys:
            if k not in selected:
                selected.append(k)

    if entities["products"]:
        add(["product_intelligence"])
    if entities["countries"]:
        add(["country_context"])
    if entities["hsn"]:
        add(["trade_statistics", "product_intelligence"])
    if entities["products"] and entities["countries"]:
        add(["duty_benefits", "compliance"])

    for kws, engs in KEYWORD_ENGINES:
        if any(k in ql for k in kws):
            add(engs)

    if not selected:
        add(["compliance", "business_services"])
    return selected[:5]


def _detect_intents(question, entities, engines):
    return {"primary": engines[0] if engines else "general", "engines": engines}


ROLE_BOOST = {
    "exporter": ["product_intelligence", "trade_news", "market_intelligence", "business_services"],
    "importer": ["product_intelligence", "logistics", "tariff", "compliance"],
    "cha": ["compliance", "logistics", "policy"],
    "buyer": ["marketplace", "product_intelligence", "network"],
    "supplier": ["marketplace", "network", "business_services"],
}

CTA_LIBRARY = {
    "create_account": {"label": "Create Free Account", "to": "/contact", "action": "create_account"},
    "download_app": {"label": "Download App", "to": "/#download", "action": "download_app"},
    "book_consultation": {"label": "Book a Consultation", "to": "/services", "action": "book_consultation"},
    "apply_iec": {"label": "Apply for IEC Registration", "to": "/services/iec-registration", "action": "apply_iec"},
    "contact": {"label": "Contact LeadNation Team", "to": "/contact", "action": "contact"},
}


# ---------------- Verified Buyers (subscription-gated) ----------------
BUYER_INTENT_KWS = ("buyer", "buyers", "importer", "importers", "who imports", "who is buying",
                    "who buys", "find buyers", "verified buyer", "leads for", "purchasers",
                    "customers abroad", "who will buy", "potential customers")


def _is_buyer_intent(question: str) -> bool:
    ql = question.lower()
    return any(k in ql for k in BUYER_INTENT_KWS)


async def _brain_subscribed(auth_uid):
    if not auth_uid:
        return False
    from core import db
    u = await db.users.find_one({"uid": auth_uid})
    if u and u.get("role") == "admin":
        return True
    s = await db.subscriptions.find_one({"owner": auth_uid, "status": "active"})
    if not s:
        return False
    try:
        return datetime.fromisoformat(s["until"]) > datetime.now(timezone.utc)
    except Exception:
        return False


async def _buyer_intel(entities, subscribed):
    from core import db
    base = {"entity_type": "buyer", "status": "active", "merged_into": None, "admin_deleted": {"$ne": True}}
    q = dict(base)
    ors = []
    if entities.get("countries"):
        ors.append({"country_name": {"$in": entities["countries"]}})
    if entities.get("hsn"):
        ors.append({"hs_families": {"$in": list({h[:4] for h in entities["hsn"]})}})
    if entities.get("products"):
        rx = "|".join(re.escape(p) for p in entities["products"][:5])
        ors += [{"products": {"$regex": rx, "$options": "i"}}, {"sector": {"$regex": rx, "$options": "i"}}]
    if ors:
        q["$or"] = ors
    total = await db.entities.count_documents(q)
    if total == 0:
        q = dict(base)
        total = await db.entities.count_documents(q)
    if total == 0:
        return None
    rows = await db.entities.find(q).sort("trust.score", -1).limit(6).to_list(6)
    markets, sectors = {}, {}
    async for e in db.entities.find(q, {"country_name": 1, "sector": 1}):
        markets[e.get("country_name", "—")] = markets.get(e.get("country_name", "—"), 0) + 1
        sectors[e.get("sector", "—")] = sectors.get(e.get("sector", "—"), 0) + 1
    top_markets = sorted(markets.items(), key=lambda x: -x[1])[:6]
    top_sectors = sorted(sectors.items(), key=lambda x: -x[1])[:6]
    if subscribed:
        listing = "\n".join(
            f"- {e.get('legal_name')} ({e.get('country_name')}) · {e.get('sector')} · "
            f"Trust {(e.get('trust') or {}).get('score')} ({(e.get('trust') or {}).get('band')}) · "
            f"source {((e.get('provenance') or [{}])[0]).get('source_name', '')}" for e in rows)
        summary = (f"LeadNation has {total} verified buyers matching this query. Top matches:\n{listing}\n\n"
                   f"All are aggregated from official government sources and sanctions-screened. Open the "
                   f"Verified Buyers page for full profiles, trust breakdowns and cited evidence. Note: we have "
                   f"no contact arrangement with these organisations — always verify directly before doing business.")
    else:
        summary = (f"LeadNation has {total} verified buyers matching this query, across markets like "
                   f"{', '.join(m for m, _ in top_markets)} and sectors like {', '.join(s for s, _ in top_sectors)}. "
                   f"Full buyer names, trust breakdowns and cited source evidence are available to subscribers. "
                   f"Subscribe and open the Verified Buyers page to unlock them.")
    engine = {"summary": summary, "sources": [{"title": "Verified Buyers", "to": "/buyers"}],
              "data": {"total": total, "markets": dict(top_markets), "sectors": dict(top_sectors),
                       "locked": not subscribed}}
    return {"engine": engine, "count": total, "locked": not subscribed}


async def _capture_buyer_signal(uid, question, entities):
    try:
        from core import db
        await db.user_intent_signals.update_one(
            {"uid": uid or "anon"},
            {"$set": {"uid": uid or "anon", "last_buyer_query": question, "is_searching_buyers": True,
                      "last_seen": datetime.now(timezone.utc).isoformat()},
             "$inc": {"buyer_query_count": 1},
             "$addToSet": {"markets_of_interest": {"$each": entities.get("countries", [])}}},
            upsert=True)
    except Exception:
        pass


async def _resolve_page_entity(page_context, entities):
    """On a country/product/hsn/service page, inject that entity even if not in the question."""
    if not page_context:
        return entities
    ptype, slug = page_context.get("type"), page_context.get("slug")
    if not ptype or not slug:
        return entities
    kind_map = {"country": "country", "product": "product", "hsn": "hsn",
                "service": "service", "corridor": "corridor", "industry": "industry"}
    kind = kind_map.get(ptype)
    if not kind:
        return entities
    from brain.knowledge import kb_get
    entry = await kb_get(kind, slug)
    if not entry:
        return entities
    title = (entry.get("data") or {}).get("name") or entry.get("title") or slug
    if ptype == "country" and title not in entities["countries"]:
        entities["countries"].insert(0, title)
    elif ptype == "product" and title not in entities["products"]:
        entities["products"].insert(0, (entry.get("data") or {}).get("name", title))
    elif ptype == "hsn" and slug not in entities["hsn"]:
        entities["hsn"].insert(0, slug)
    elif ptype == "service" and title not in entities["services"]:
        entities["services"].insert(0, title)
    return entities


def _ctas(question, entities, intent):
    ql = question.lower()
    out = []
    def add(key):
        if CTA_LIBRARY[key] not in out:
            out.append(CTA_LIBRARY[key])
    if any(k in ql for k in ["iec", "import export code"]):
        add("apply_iec")
    if any(k in ql for k in ["register", "registration", "gst", "rcmc", "compliance", "consult", "help me", "service"]):
        add("book_consultation")
    if any(k in ql for k in ["buyer", "sell", "export", "start", "how do i", "want to", "quote", "price", "get started"]):
        add("create_account")
    if "primary" in intent and intent.get("primary") in ("business_services", "compliance"):
        add("book_consultation")
    add("create_account")
    add("download_app")
    return out[:3]


async def _recommendations(entities):
    """Cross-domain related items from the Knowledge Base."""
    from brain.knowledge import kb_search
    terms = (entities.get("products") or []) + (entities.get("countries") or []) + (entities.get("hsn") or [])
    term = terms[0] if terms else ""
    rec = []
    seen = set()
    path = {"product": "/products/{s}", "country": "/countries/{s}", "hsn": "/hsn/{s}",
            "service": "/services/{s}", "blog": "/blog/{s}", "learning": "/academy",
            "corridor": "/corridors/{s}", "industry": "/industries/{s}"}
    for kind in ["product", "country", "hsn", "service", "blog", "learning", "corridor", "industry"]:
        hits = await kb_search(term, kinds=[kind], limit=2)
        for h in hits:
            key = (kind, h["slug"])
            if key in seen:
                continue
            seen.add(key)
            rec.append({"kind": kind, "label": h["title"],
                        "to": path[kind].format(s=h["slug"])})
    return rec[:8]


async def orchestrate(question: str, session_id: str = None, user_id: str = None,
                      page_context: dict = None, language: str = "en", auth_uid: str = None):
    import hashlib
    from datetime import datetime as _dt

    entities = extract_entities(question)
    entities = await _resolve_page_entity(page_context, entities)
    engine_keys = select_engines(question, entities)

    # personalization by role from user memory
    role = None
    if user_id:
        uc = await memory.get_user_context(user_id)
        role = (uc or {}).get("role")
        for e in ROLE_BOOST.get((role or "").lower(), []):
            if e not in engine_keys:
                engine_keys.append(e)
    engine_keys = engine_keys[:7]
    intent = _detect_intents(question, entities, engine_keys)

    engine_outputs = {}
    for key in engine_keys:
        out = await run_engine(key, entities)
        if out:
            engine_outputs[key] = out

    # Verified Buyers — subscription-gated intelligence injected into the answer grounding.
    buyer_intent = _is_buyer_intent(question)
    buyer_access = None
    if buyer_intent:
        subscribed = await _brain_subscribed(auth_uid)
        binfo = await _buyer_intel(entities, subscribed)
        if binfo:
            engine_outputs["buyer_intelligence"] = binfo["engine"]
            buyer_access = {"subscribed": subscribed, "locked": binfo["locked"], "count": binfo["count"]}
        await _capture_buyer_signal(auth_uid or user_id, question, entities)

    sources, suggestions = [], []
    for out in engine_outputs.values():
        for s in out.get("sources", []):
            if s not in sources:
                sources.append(s)
    for s in sources[:5]:
        suggestions.append({"label": s["title"], "to": s["to"]})

    recommendations = await _recommendations(entities)
    ctas = _ctas(question, entities, intent)
    if buyer_access and buyer_access.get("locked"):
        ctas.insert(0, {"label": "Unlock Verified Buyers", "to": "/pricing", "action": "subscribe"})
    elif buyer_intent:
        ctas.insert(0, {"label": "Open Verified Buyers", "to": "/buyers", "action": "buyers"})

    provider = get_provider()
    pc_sig = f"{(page_context or {}).get('type')}:{(page_context or {}).get('slug')}"
    cache_key = hashlib.sha256(
        f"{provider.name}:{getattr(provider,'model',None)}:{language}:{role}:{pc_sig}:{question.strip().lower()}".encode()
    ).hexdigest()

    cached = None if buyer_intent else await CACHE.find_one({"_id": cache_key})
    if cached:
        age = (_dt.now(timezone.utc) - _dt.fromisoformat(cached["createdAt"])).total_seconds()
        if age < CACHE_TTL_SECONDS:
            result = cached["result"]
            await USAGE.insert_one({"provider": result.get("provider"), "model": result.get("model"),
                                    "live": result.get("live", False), "cached": True,
                                    "tokens": result.get("tokens", {}), "cost": 0.0, "createdAt": _now()})
            if session_id:
                await memory.append_message(session_id, "user", question)
                await memory.append_message(session_id, "assistant", result["answer"])
            return _shape(question, result, intent, entities, engine_keys, engine_outputs,
                          sources, suggestions, recommendations, ctas, role, language, cached=True,
                          buyer_access=buyer_access)

    context = await build_context(entities, session_id, user_id)
    context["language"] = language
    context["role"] = role
    result = await provider.generate(question, intent, entities, engine_outputs, context)
    answered = bool(engine_outputs)

    if session_id:
        await memory.append_message(session_id, "user", question)
        await memory.append_message(session_id, "assistant", result["answer"])
    if user_id:
        await memory.add_recent_search(user_id, question)

    await QUERIES.insert_one({
        "question": question, "intents": intent, "engines": engine_keys,
        "entities": entities, "answered": answered, "session_id": session_id,
        "provider": result.get("provider"), "model": result.get("model"),
        "pageContext": page_context, "language": language, "role": role,
        "createdAt": _now(),
    })
    await USAGE.insert_one({"provider": result.get("provider"), "model": result.get("model"),
                            "live": result.get("live", False), "cached": False,
                            "tokens": result.get("tokens", {}), "cost": result.get("cost", 0.0),
                            "engines": len(engine_keys), "createdAt": _now()})

    if answered and not result.get("degraded") and not buyer_intent:
        await CACHE.replace_one({"_id": cache_key},
                                {"_id": cache_key, "result": result, "createdAt": _now()}, upsert=True)

    return _shape(question, result, intent, entities, engine_keys, engine_outputs,
                  sources, suggestions, recommendations, ctas, role, language, cached=False,
                  buyer_access=buyer_access)


def _shape(question, result, intent, entities, engine_keys, engine_outputs, sources,
           suggestions, recommendations, ctas, role, language, cached, buyer_access=None):
    return {
        "question": question,
        "answer": result["answer"],
        "provider": result.get("provider"),
        "model": result.get("model"),
        "live": result.get("live", False),
        "cached": cached,
        "note": result.get("note"),
        "isMock": not result.get("live", False),
        "intent": intent,
        "entities": entities,
        "enginesUsed": engine_keys,
        "engineOutputs": engine_outputs,
        "sources": sources,
        "suggestedTools": suggestions,
        "recommendations": recommendations,
        "ctas": ctas,
        "role": role,
        "language": language,
        "buyerAccess": buyer_access,
    }
