"""Memory system — conversation memory, user context, saved preferences.

Improves future recommendations. Keyed by session_id (anonymous) and/or user_id.
"""
from datetime import datetime, timezone

from core import db

CONV = db.conversation_memory
CTX = db.user_context


def _now():
    return datetime.now(timezone.utc).isoformat()


async def append_message(session_id: str, role: str, text: str):
    if not session_id:
        return
    await CONV.update_one(
        {"session_id": session_id},
        {"$push": {"messages": {"role": role, "text": text, "at": _now()}},
         "$setOnInsert": {"session_id": session_id, "createdAt": _now()},
         "$set": {"updatedAt": _now()}},
        upsert=True,
    )


async def get_conversation(session_id: str, limit: int = 20):
    doc = await CONV.find_one({"session_id": session_id}, {"_id": 0})
    if not doc:
        return {"session_id": session_id, "messages": []}
    doc["messages"] = doc.get("messages", [])[-limit:]
    return doc


async def get_user_context(user_id: str):
    if not user_id:
        return {}
    doc = await CTX.find_one({"user_id": user_id}, {"_id": 0})
    return doc or {
        "user_id": user_id, "preferredCountry": None, "preferredProducts": [],
        "preferredIndustries": [], "role": None, "recentSearches": [],
        "savedProducts": [], "savedCountries": [], "savedConversations": [],
    }


async def update_user_context(user_id: str, patch: dict):
    if not user_id:
        return {}
    patch = {k: v for k, v in patch.items() if v is not None}
    patch["updatedAt"] = _now()
    await CTX.update_one(
        {"user_id": user_id},
        {"$set": patch, "$setOnInsert": {"user_id": user_id, "createdAt": _now()}},
        upsert=True,
    )
    return await get_user_context(user_id)


async def add_recent_search(user_id: str, query: str):
    if not user_id or not query:
        return
    await CTX.update_one(
        {"user_id": user_id},
        {"$push": {"recentSearches": {"$each": [{"q": query, "at": _now()}], "$slice": -25}},
         "$setOnInsert": {"user_id": user_id, "createdAt": _now()}},
        upsert=True,
    )


async def add_saved_item(user_id: str, field: str, item):
    if not user_id or field not in ("savedProducts", "savedCountries", "savedConversations"):
        return {}
    await CTX.update_one(
        {"user_id": user_id},
        {"$addToSet": {field: item},
         "$setOnInsert": {"user_id": user_id, "createdAt": _now()}},
        upsert=True,
    )
    return await get_user_context(user_id)
