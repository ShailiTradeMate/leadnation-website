"""AI Provider abstraction + Prompt management + RAG composition.

CTO design notes
----------------
* Live AI is ON via the Emergent Universal LLM key, default model = cheapest
  reliable (gpt-5.4-mini). Provider/model are env-configurable — switch between
  OpenAI / Anthropic / Gemini with ZERO app code changes.
* Cost control: the Brain Router caches answers (24h) and selects minimal context,
  so repeat / similar questions cost nothing. If the LLM call fails (or balance is
  exhausted), we transparently fall back to deterministic engine composition so the
  product NEVER breaks and stays usable at zero budget.
* RAG: the LLM only reasons over LeadNation engine + Knowledge Base context. It is
  instructed to say so when information is insufficient (no fabrication).
"""
import os
import logging
from typing import Dict, List

from dotenv import load_dotenv

load_dotenv()

# Rough public per-1M-token prices (USD) for cost MONITORING only (input, output).
MODEL_PRICING = {
    "gpt-5.4-mini": (0.15, 0.60),
    "gpt-5.4": (2.50, 10.0),
    "gpt-4o-mini": (0.15, 0.60),
    "claude-haiku-4-5-20251001": (0.80, 4.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "gemini-3-flash-preview": (0.10, 0.40),
    "gemini-2.5-flash": (0.10, 0.40),
}


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    pin, pout = MODEL_PRICING.get(model, (0.15, 0.60))
    return round((prompt_tokens / 1_000_000) * pin + (completion_tokens / 1_000_000) * pout, 6)


def approx_tokens(text: str) -> int:
    return max(1, len(text or "") // 4)


# ---------------- Prompt management ----------------
class PromptManager:
    SYSTEM = (
        "You are LeadNation Brain — a global trade-intelligence assistant for importers and "
        "exporters in ANY country. Your job is to answer the user's SPECIFIC question directly "
        "and usefully.\n\n"
        "RULES:\n"
        "1. Answer THIS question. Never output generic boilerplate or repeat the same sections "
        "across different answers. Include ONLY what is relevant to what was asked.\n"
        "2. Use the LIVE ENGINE CONTEXT (real tariffs, trade values, duty, benefits, FX, news) "
        "for every figure or number. Never invent specific rates or values — if a number is not "
        "in the context, say it is indicative and point to the relevant LeadNation tool.\n"
        "3. For country-specific compliance, customs procedure, required documents, certifications "
        "and logistics for ANY of the world's countries, use your own up-to-date international-trade "
        "expertise, tailored precisely to the ORIGIN and DESTINATION in the question. Be specific to "
        "those countries. NEVER default to India unless India is actually part of the question.\n"
        "4. Adapt structure and length to the question: a short direct answer first, then only the "
        "relevant headings/bullets. Be concrete, practical and globally relevant.\n"
        "5. If origin/destination are given, frame everything around that exact trade lane."
    )

    @classmethod
    def build_context_block(cls, question, intent, entities, engine_outputs, context) -> str:
        lines: List[str] = [f"USER QUESTION: {question}", ""]
        ents = {k: v for k, v in entities.items() if v}
        if ents:
            lines.append(f"DETECTED ENTITIES: {ents}")
        lines.append("\nENGINE CONTEXT (each item = an engine that LeadNation routed):")
        for key, out in engine_outputs.items():
            summ = out.get("summary", "")
            lines.append(f"- [{key}] {summ}")
            data = out.get("data") or {}
            if isinstance(data, dict):
                small = {k: v for k, v in list(data.items())[:6] if v}
                if small:
                    lines.append(f"    data: {small}")
            elif isinstance(data, list) and data:
                lines.append(f"    data: {data[:6]}")
        retrieved = context.get("retrieved") or []
        if retrieved:
            lines.append("\nKNOWLEDGE BASE MATCHES: " + ", ".join(r["title"] for r in retrieved[:6]))
        user_ctx = context.get("user") or {}
        if user_ctx.get("preferredCountry") or user_ctx.get("preferredProducts"):
            lines.append(f"\nUSER MEMORY: country={user_ctx.get('preferredCountry')}, "
                         f"products={user_ctx.get('preferredProducts')}, role={user_ctx.get('role')}")
        mem = (context.get("memory") or {}).get("recentMessages") or []
        if mem:
            recent = " | ".join(f"{m['role']}: {m['text'][:80]}" for m in mem[-4:])
            lines.append(f"\nRECENT CONVERSATION: {recent}")
        role = context.get("role")
        if role:
            lines.append(f"\nUSER ROLE: {role} — tailor priorities accordingly.")
        lang = context.get("language", "en")
        if lang and lang != "en":
            lang_names = {"hi": "Hindi", "ar": "Arabic", "fr": "French", "es": "Spanish"}
            lines.append(f"\nIMPORTANT: Respond entirely in {lang_names.get(lang, lang)}.")
        lines.append("\nWrite the answer now.")
        return "\n".join(lines)


# ---------------- Provider interface ----------------
class BaseProvider:
    name = "base"
    live = False

    async def generate(self, question, intent, entities, engine_outputs, context) -> Dict:
        raise NotImplementedError


class MockProvider(BaseProvider):
    """Deterministic engine composition — fallback + zero-budget mode."""
    name = "mock"
    live = False

    async def generate(self, question, intent, entities, engine_outputs, context):
        sections: List[str] = []
        order = [
            ("product_intelligence", "Product Intelligence"),
            ("compliance", "Compliance & Documentation"),
            ("tariff", "Duties & Landed Cost"),
            ("country_context", "Country Context"),
            ("logistics", "Logistics"),
            ("policy", "Policy & Incentives"),
            ("trade_news", "Relevant Trade News"),
            ("market_intelligence", "Market Intelligence"),
            ("business_services", "How LeadNation Can Help"),
            ("learning", "Learn More"),
            ("marketplace", "Marketplace"),
            ("network", "Trade Network"),
        ]
        for key, label in order:
            out = engine_outputs.get(key)
            if out and out.get("summary"):
                sections.append(f"**{label}** — {out['summary']}")

        prod = (entities.get("products") or [None])[0]
        country = (entities.get("countries") or [None])[0]
        if prod and country:
            headline = f"Here's what you need to trade {prod} with {country}:"
        elif prod:
            headline = f"Here's the LeadNation Brain briefing on {prod}:"
        elif country:
            headline = f"Here's the LeadNation Brain briefing on {country}:"
        else:
            headline = "Here's what the LeadNation Brain found:"

        if not sections:
            sections.append("I don't have enough LeadNation data to answer that precisely yet. "
                            "Try asking about a product, country, HSN code, duty, compliance step or service.")
        answer = headline + "\n\n" + "\n\n".join(sections)
        return {"answer": answer, "provider": self.name, "live": False, "model": None,
                "tokens": {"prompt": 0, "completion": 0, "total": 0}, "cost": 0.0}


class EmergentLLMProvider(BaseProvider):
    """Live AI via the Emergent Universal key (configurable provider/model)."""

    def __init__(self, provider: str, model: str):
        self.name = provider
        self.model = model
        self.live = True
        self._mock = MockProvider()
        self._key = os.environ.get("EMERGENT_LLM_KEY")

    async def generate(self, question, intent, entities, engine_outputs, context):
        if not self._key:
            return await self._mock.generate(question, intent, entities, engine_outputs, context)

        from emergentintegrations.llm.chat import LlmChat, UserMessage
        prompt = PromptManager.build_context_block(question, intent, entities, engine_outputs, context)

        last_err = None
        for attempt in range(2):  # retry once
            try:
                chat = LlmChat(api_key=self._key, session_id=f"brain-{abs(hash(question)) % 10**9}",
                               system_message=PromptManager.SYSTEM).with_model(self.name, self.model)
                answer = await chat.send_message(UserMessage(text=prompt))
                answer = (answer or "").strip()
                if not answer:
                    raise ValueError("empty answer")
                p_tok = approx_tokens(PromptManager.SYSTEM + prompt)
                c_tok = approx_tokens(answer)
                return {"answer": answer, "provider": self.name, "live": True, "model": self.model,
                        "tokens": {"prompt": p_tok, "completion": c_tok, "total": p_tok + c_tok},
                        "cost": estimate_cost(self.model, p_tok, c_tok)}
            except Exception as exc:  # noqa
                last_err = exc
                logging.warning("Brain LLM attempt %d failed: %s", attempt + 1, exc)

        # graceful fallback
        res = await self._mock.generate(question, intent, entities, engine_outputs, context)
        res["note"] = f"Live AI unavailable ({last_err}); used deterministic engine composition."
        res["degraded"] = True
        return res


_INSTANCE = None


def get_provider() -> BaseProvider:
    global _INSTANCE
    provider = os.environ.get("BRAIN_AI_PROVIDER", "mock").lower()
    enabled = os.environ.get("BRAIN_AI_ENABLED", "false").lower() == "true"
    model = os.environ.get("BRAIN_AI_MODEL", "gpt-5.4-mini")
    key = f"{provider}:{model}:{enabled}"
    if _INSTANCE is None or getattr(_INSTANCE, "_key_sig", None) != key:
        if provider == "mock" or not enabled:
            inst = MockProvider()
        else:
            inst = EmergentLLMProvider(provider, model)
        inst._key_sig = key
        _INSTANCE = inst
    return _INSTANCE


def provider_status() -> dict:
    provider = os.environ.get("BRAIN_AI_PROVIDER", "mock").lower()
    enabled = os.environ.get("BRAIN_AI_ENABLED", "false").lower() == "true"
    model = os.environ.get("BRAIN_AI_MODEL", "gpt-5.4-mini")
    live = enabled and provider != "mock" and bool(os.environ.get("EMERGENT_LLM_KEY"))
    return {
        "active": provider if live else "mock",
        "model": model if live else None,
        "live": live,
        "ragEnabled": True,
        "supported": ["mock", "openai", "anthropic", "gemini", "local"],
        "note": "Live RAG AI active." if live else "Mock mode — set BRAIN_AI_ENABLED=true.",
    }
