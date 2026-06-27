"""Brain public API — /api/brain/*"""
import time
from collections import defaultdict
from typing import Optional

from fastapi import APIRouter, Query, Request, HTTPException
from pydantic import BaseModel

from brain.router import orchestrate
from brain.search_layer import universal_search
from brain.providers import provider_status
from brain import memory, knowledge
from brain.engines import ENGINES

router = APIRouter(prefix="/brain")

# Lightweight in-memory rate limiter (single-process): 20 requests / 60s per key.
_HITS = defaultdict(list)
_RL_WINDOW = 60
_RL_MAX = 20


def _rate_limit(key: str):
    now = time.time()
    _HITS[key] = [t for t in _HITS[key] if now - t < _RL_WINDOW]
    if len(_HITS[key]) >= _RL_MAX:
        raise HTTPException(status_code=429, detail="Too many requests — please slow down.")
    _HITS[key].append(now)


class AskRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    page_context: Optional[dict] = None
    language: Optional[str] = "en"


@router.post("/ask")
async def brain_ask(payload: AskRequest, request: Request):
    key = payload.session_id or payload.user_id or (request.client.host if request.client else "anon")
    _rate_limit(key)
    return await orchestrate(payload.question, payload.session_id, payload.user_id,
                             page_context=payload.page_context, language=payload.language or "en")


@router.get("/search")
async def brain_search(q: str = Query("", min_length=0)):
    return await universal_search(q)


@router.get("/engines")
async def brain_engines():
    return {"engines": list(ENGINES.keys()), "count": len(ENGINES),
            "provider": provider_status()}


@router.get("/status")
async def brain_status():
    return {"ok": True, "provider": provider_status(), "knowledgeBase": await knowledge.kb_stats(),
            "engines": len(ENGINES)}


@router.get("/conversation/{session_id}")
async def brain_conversation(session_id: str):
    return await memory.get_conversation(session_id)


class ContextPatch(BaseModel):
    user_id: str
    preferredCountry: Optional[str] = None
    preferredProducts: Optional[list] = None
    preferredIndustries: Optional[list] = None
    role: Optional[str] = None


@router.get("/context/{user_id}")
async def get_context(user_id: str):
    return await memory.get_user_context(user_id)


@router.post("/context")
async def set_context(payload: ContextPatch):
    patch = payload.model_dump(exclude={"user_id"})
    return await memory.update_user_context(payload.user_id, patch)


class SaveRequest(BaseModel):
    user_id: str
    field: str  # savedProducts | savedCountries | savedConversations
    item: dict | str


@router.post("/save")
async def save_item(payload: SaveRequest):
    return await memory.add_saved_item(payload.user_id, payload.field, payload.item)


@router.get("/knowledge")
async def kb_lookup(kind: Optional[str] = None, q: str = ""):
    kinds = [kind] if kind else None
    return {"results": await knowledge.kb_search(q, kinds=kinds, limit=50)}
