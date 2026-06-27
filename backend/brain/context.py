"""Context Builder — assembles retrieval + memory context for the AI provider.

This is the retrieval/context seam. When live AI is activated, the same context
is what gets injected into the prompt.
"""
from brain import memory
from brain.knowledge import kb_search


async def build_context(entities: dict, session_id: str = None, user_id: str = None):
    ctx = {"retrieved": [], "memory": {}, "user": {}}

    # Retrieval from Knowledge Base (SSOT) — priority source
    seeds = (entities.get("products") or []) + (entities.get("countries") or [])
    for term in seeds[:3]:
        hits = await kb_search(term, limit=3)
        ctx["retrieved"].extend({"id": h["id"], "title": h["title"]} for h in hits)

    if session_id:
        conv = await memory.get_conversation(session_id, limit=6)
        ctx["memory"] = {"recentMessages": conv.get("messages", [])}
    if user_id:
        ctx["user"] = await memory.get_user_context(user_id)
    return ctx
