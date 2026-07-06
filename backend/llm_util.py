"""Thin LLM helper for one-shot text generation (news synthesis + impact notes).

Uses the Emergent Universal key via emergentintegrations. Fails soft: returns
None on any error so callers can fall back to deterministic content.
"""
import os
import json
import logging

_KEY = os.environ.get("EMERGENT_LLM_KEY")
_PROVIDER = os.environ.get("BRAIN_AI_PROVIDER", "openai").lower()
_MODEL = os.environ.get("BRAIN_AI_MODEL", "gpt-5.4-mini")
if _PROVIDER == "mock":
    _PROVIDER = "openai"


async def generate(system: str, prompt: str, session: str = "llm") -> str | None:
    if not _KEY:
        return None
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        chat = LlmChat(api_key=_KEY, session_id=session, system_message=system).with_model(_PROVIDER, _MODEL)
        out = await chat.send_message(UserMessage(text=prompt))
        return (out or "").strip() or None
    except Exception as exc:
        logging.warning("llm_util.generate failed: %s", exc)
        return None


async def generate_json(system: str, prompt: str, session: str = "llm-json"):
    raw = await generate(system, prompt + "\n\nRespond with STRICT JSON only, no markdown.", session)
    if not raw:
        return None
    try:
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1].lstrip("json").strip() if "```" in raw else raw
        return json.loads(raw)
    except Exception:
        # best-effort: extract first {...} or [...]
        try:
            start = min([i for i in (raw.find("{"), raw.find("[")) if i >= 0])
            end = max(raw.rfind("}"), raw.rfind("]"))
            return json.loads(raw[start:end + 1])
        except Exception:
            return None
