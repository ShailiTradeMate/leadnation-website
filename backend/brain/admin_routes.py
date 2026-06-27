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

    # engine usage counts
    eng_rows = await QUERIES.aggregate([
        {"$unwind": "$engines"},
        {"$group": {"_id": "$engines", "count": {"$sum": 1}}},
    ]).to_list(50)
    eng_counts = {r["_id"]: r["count"] for r in eng_rows}
    engine_health = [{"engine": k, "status": "operational", "calls": eng_counts.get(k, 0)}
                     for k in ENGINES.keys()]

    # most asked questions
    top_q = await QUERIES.aggregate([
        {"$group": {"_id": "$question", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}, {"$limit": 10},
    ]).to_list(10)

    failed_q = await QUERIES.find({"answered": False}, {"_id": 0, "question": 1, "createdAt": 1}) \
        .sort("createdAt", -1).limit(10).to_list(10)

    return {
        "provider": provider_status(),
        "knowledgeBase": await knowledge.kb_stats(),
        "engineHealth": engine_health,
        "aiUsage": {"totalCalls": ai_calls, "totalQueries": total_q,
                    "answered": answered, "failed": failed,
                    "answerRate": round((answered / total_q * 100) if total_q else 0, 1)},
        "searchAnalytics": {"totalQueries": total_q},
        "mostAskedQuestions": [{"question": r["_id"], "count": r["count"]} for r in top_q],
        "topCountries": await _top("entities.countries"),
        "topProducts": await _top("entities.products"),
        "topHsn": await _top("entities.hsn"),
        "topServices": await _top("entities.services"),
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
