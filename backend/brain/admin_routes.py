"""Brain Admin API — /api/admin/brain/*  (token-gated)"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from core import db, require_admin, ADMIN_TOKEN
from brain.providers import provider_status
from brain import knowledge
from brain.engines import ENGINES

router = APIRouter(prefix="/admin/brain")

QUERIES = db.brain_queries
USAGE = db.brain_usage
KB = db.knowledge_base


def _now():
    return datetime.now(timezone.utc).isoformat()


async def _top(field: str, limit: int = 8):
    pipeline = [
        {"$unwind": f"${field}"},
        {"$group": {"_id": f"${field}", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit},
    ]
    rows = await QUERIES.aggregate(pipeline).to_list(limit)
    return [{"value": r["_id"], "count": r["count"]} for r in rows if r["_id"]]


@router.get("/overview")
async def overview(_: bool = Depends(require_admin)):
    total_q = await QUERIES.count_documents({})
    answered = await QUERIES.count_documents({"answered": True})
    failed = await QUERIES.count_documents({"answered": False})
    ai_calls = await USAGE.count_documents({})
    cached_calls = await USAGE.count_documents({"cached": True})

    # cost + token monitoring
    agg = await USAGE.aggregate([{"$group": {
        "_id": None, "cost": {"$sum": "$cost"}, "tokens": {"$sum": "$tokens.total"}}}]).to_list(1)
    total_cost = round(agg[0]["cost"], 6) if agg else 0.0
    total_tokens = int(agg[0]["tokens"]) if agg and agg[0].get("tokens") else 0
    cost_by_model = await USAGE.aggregate([
        {"$match": {"model": {"$ne": None}}},
        {"$group": {"_id": "$model", "cost": {"$sum": "$cost"}, "calls": {"$sum": 1},
                    "tokens": {"$sum": "$tokens.total"}}},
        {"$sort": {"cost": -1}},
    ]).to_list(10)

    # engine usage
    eng_rows = await QUERIES.aggregate([
        {"$unwind": "$engines"},
        {"$group": {"_id": "$engines", "count": {"$sum": 1}}},
    ]).to_list(50)
    eng_counts = {r["_id"]: r["count"] for r in eng_rows}
    engine_health = [{"engine": k, "status": "operational", "calls": eng_counts.get(k, 0)}
                     for k in ENGINES.keys()]

    top_q = await QUERIES.aggregate([
        {"$group": {"_id": "$question", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}, {"$limit": 10},
    ]).to_list(10)

    failed_q = await QUERIES.find({"answered": False}, {"_id": 0, "question": 1, "createdAt": 1}) \
        .sort("createdAt", -1).limit(10).to_list(10)

    # most-viewed from first-party events
    async def _top_paths(prefix, limit=6):
        rows = await db.events.aggregate([
            {"$match": {"path": {"$regex": f"^{prefix}"}}},
            {"$group": {"_id": "$path", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}, {"$limit": limit},
        ]).to_list(limit)
        return [{"value": r["_id"], "count": r["count"]} for r in rows]

    most_used_services = await db.service_requests.aggregate([
        {"$group": {"_id": "$service", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}, {"$limit": 8},
    ]).to_list(8)

    prov = provider_status()
    return {
        "provider": prov,
        "aiHealth": {"status": "live" if prov["live"] else "mock", "provider": prov["active"],
                     "model": prov.get("model"), "ragEnabled": prov["ragEnabled"],
                     "cacheHitRate": round((cached_calls / ai_calls * 100) if ai_calls else 0, 1),
                     "degradedCalls": await USAGE.count_documents({"live": False, "cached": False})},
        "knowledgeBase": await knowledge.kb_stats(),
        "engineHealth": engine_health,
        "aiUsage": {"totalCalls": ai_calls, "cachedCalls": cached_calls, "totalQueries": total_q,
                    "answered": answered, "failed": failed,
                    "answerRate": round((answered / total_q * 100) if total_q else 0, 1)},
        "costMonitoring": {"totalCostUsd": total_cost, "byModel": [
            {"model": r["_id"], "cost": round(r["cost"], 6), "calls": r["calls"],
             "tokens": int(r.get("tokens") or 0)} for r in cost_by_model]},
        "tokenUsage": {"totalTokens": total_tokens},
        "searchAnalytics": {"totalQueries": total_q},
        "mostAskedQuestions": [{"question": r["_id"], "count": r["count"]} for r in top_q],
        "topCountries": await _top("entities.countries"),
        "topProducts": await _top("entities.products"),
        "topHsn": await _top("entities.hsn"),
        "topServices": await _top("entities.services"),
        "mostViewedCountries": await _top_paths("/countries/"),
        "mostViewedProducts": await _top_paths("/products/"),
        "mostUsedServices": [{"value": r["_id"], "count": r["count"]} for r in most_used_services if r["_id"]],
        "trendingSearches": [{"question": r["_id"], "count": r["count"]} for r in top_q[:6]],
        "failedQueries": failed_q,
        "knowledgeGaps": [q["question"] for q in failed_q],
    }


@router.get("/knowledge")
async def list_kb(kind: str = "", q: str = "", _: bool = Depends(require_admin)):
    kinds = [kind] if kind else None
    items = await knowledge.kb_search(q, kinds=kinds, limit=200)
    return {"total": len(items), "items": items, "stats": await knowledge.kb_stats()}


class KbItem(BaseModel):
    kind: str
    slug: str
    title: str
    content: str = ""
    tags: list = []
    data: dict = {}


@router.post("/knowledge")
async def create_kb(item: KbItem, _: bool = Depends(require_admin)):
    doc = item.model_dump()
    doc["id"] = f"{doc['kind']}:{doc['slug']}"
    doc["_text"] = (doc["title"] + " " + doc["content"] + " " + " ".join(doc["tags"])).lower()
    doc["source"] = "admin"
    doc["updatedAt"] = _now()
    await KB.replace_one({"id": doc["id"]}, doc, upsert=True)
    doc.pop("_text", None)
    return doc


@router.delete("/knowledge/{kind}/{slug}")
async def delete_kb(kind: str, slug: str, _: bool = Depends(require_admin)):
    res = await KB.delete_one({"id": f"{kind}:{slug}"})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Not found")
    return {"ok": True}


@router.post("/knowledge/reseed")
async def reseed(_: bool = Depends(require_admin)):
    return await knowledge.seed_knowledge_base(force=True)
