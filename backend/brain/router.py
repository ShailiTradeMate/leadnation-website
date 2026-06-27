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

    for slug, p in COUNTRY_PROFILES.items():
        if p["name"].lower() in ql or slug in ql or f" {p['code'].lower()} " in f" {ql} ":
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
    (("duty", "tariff", "tax", "landed cost", "import duty"), ["tariff"]),
    (("document", "certif", "compliance", "license", "licence", "iec", "gst", "rcmc", "required to export", "what do i need"), ["compliance"]),
    (("hsn", "hs code", "classif", "which code"), ["product_intelligence"]),
    (("buyer", "importer", "who imports", "which countries import", "demand", "market for"), ["product_intelligence", "market_intelligence"]),
    (("learn", "how do i start", "how to start", "beginner", "course", "guide", "teach"), ["learning"]),
    (("news", "update", "notification", "latest"), ["trade_news"]),
    (("ship", "freight", "logistic", "container", "port", "transit"), ["logistics"]),
    (("scheme", "incentive", "subsidy", "rodtep", "policy", "benefit"), ["policy"]),
    (("register", "registration", "service", "help me get", "apply for"), ["business_services", "compliance"]),
    (("supplier", "manufacturer", "network", "find seller"), ["network"]),
    (("rfq", "marketplace", "sell my", "listing"), ["marketplace"]),
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
    if entities["products"] and entities["countries"]:
        add(["compliance", "tariff", "trade_news", "logistics"])

    for kws, engs in KEYWORD_ENGINES:
        if any(k in ql for k in kws):
            add(engs)

    if not selected:
        add(["compliance", "learning", "business_services"])
    return selected[:6]


def _detect_intents(question, entities, engines):
    return {"primary": engines[0] if engines else "general", "engines": engines}


async def orchestrate(question: str, session_id: str = None, user_id: str = None):
    import hashlib
    from datetime import datetime as _dt

    entities = extract_entities(question)
    engine_keys = select_engines(question, entities)
    intent = _detect_intents(question, entities, engine_keys)

    engine_outputs = {}
    for key in engine_keys:
        out = await run_engine(key, entities)
        if out:
            engine_outputs[key] = out

    sources, suggestions = [], []
    for out in engine_outputs.values():
        for s in out.get("sources", []):
            if s not in sources:
                sources.append(s)
    for s in sources[:5]:
        suggestions.append({"label": s["title"], "to": s["to"]})

    provider = get_provider()
    cache_key = hashlib.sha256(f"{provider.name}:{getattr(provider,'model',None)}:{question.strip().lower()}".encode()).hexdigest()

    cached = await CACHE.find_one({"_id": cache_key})
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
            return _shape(question, result, intent, entities, engine_keys, engine_outputs, sources, suggestions, cached=True)

    context = await build_context(entities, session_id, user_id)
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
        "createdAt": _now(),
    })
    await USAGE.insert_one({"provider": result.get("provider"), "model": result.get("model"),
                            "live": result.get("live", False), "cached": False,
                            "tokens": result.get("tokens", {}), "cost": result.get("cost", 0.0),
                            "engines": len(engine_keys), "createdAt": _now()})

    if answered and not result.get("degraded"):
        await CACHE.replace_one({"_id": cache_key},
                                {"_id": cache_key, "result": result, "createdAt": _now()}, upsert=True)

    return _shape(question, result, intent, entities, engine_keys, engine_outputs, sources, suggestions, cached=False)


def _shape(question, result, intent, entities, engine_keys, engine_outputs, sources, suggestions, cached):
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
    }
