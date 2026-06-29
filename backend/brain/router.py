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
                      page_context: dict = None, language: str = "en"):
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

    sources, suggestions = [], []
    for out in engine_outputs.values():
        for s in out.get("sources", []):
            if s not in sources:
                sources.append(s)
    for s in sources[:5]:
        suggestions.append({"label": s["title"], "to": s["to"]})

    recommendations = await _recommendations(entities)
    ctas = _ctas(question, entities, intent)

    provider = get_provider()
    pc_sig = f"{(page_context or {}).get('type')}:{(page_context or {}).get('slug')}"
    cache_key = hashlib.sha256(
        f"{provider.name}:{getattr(provider,'model',None)}:{language}:{role}:{pc_sig}:{question.strip().lower()}".encode()
    ).hexdigest()

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
            return _shape(question, result, intent, entities, engine_keys, engine_outputs,
                          sources, suggestions, recommendations, ctas, role, language, cached=True)

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

    if answered and not result.get("degraded"):
        await CACHE.replace_one({"_id": cache_key},
                                {"_id": cache_key, "result": result, "createdAt": _now()}, upsert=True)

    return _shape(question, result, intent, entities, engine_keys, engine_outputs,
                  sources, suggestions, recommendations, ctas, role, language, cached=False)


def _shape(question, result, intent, entities, engine_keys, engine_outputs, sources,
           suggestions, recommendations, ctas, role, language, cached):
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
    }
