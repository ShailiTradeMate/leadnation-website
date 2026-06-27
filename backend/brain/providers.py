"""AI Provider abstraction + Prompt management.

Configurable via env BRAIN_AI_PROVIDER (mock | openai | anthropic | gemini | local).
Default = mock. NO paid AI calls are made until a provider is explicitly enabled
and wired through the integration layer. The interfaces below are the seams that
let us flip to live AI with minimal change.
"""
import os
from typing import Dict, List


# ---------------- Prompt management ----------------
class PromptManager:
    SYSTEM = (
        "You are LeadNation Brain — the trade intelligence operating system for "
        "global importers and exporters, India-first. Answer precisely using the "
        "provided engine context. Cite which engines/sources informed the answer."
    )

    TEMPLATES = {
        "trade_answer": (
            "Question: {question}\n"
            "Detected entities: {entities}\n"
            "Engine context:\n{context}\n\n"
            "Write a clear, structured answer for a trader."
        ),
    }

    @classmethod
    def build(cls, key: str, **kwargs) -> str:
        return cls.TEMPLATES.get(key, "{question}").format(**kwargs)


# ---------------- Provider interface ----------------
class BaseProvider:
    name = "base"
    live = False

    def generate(self, question: str, intent: dict, entities: dict,
                 engine_outputs: dict, context: dict) -> Dict:
        raise NotImplementedError


class MockProvider(BaseProvider):
    """Rule-based composer that synthesises engine outputs into one answer.

    This mirrors exactly what a live LLM would receive (engine_outputs + context),
    so swapping in a real provider requires no orchestration changes.
    """
    name = "mock"
    live = False

    def generate(self, question, intent, entities, engine_outputs, context):
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
            if not out:
                continue
            summary = out.get("summary")
            if summary:
                sections.append(f"**{label}** — {summary}")

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
            sections.append(
                "I couldn't match this to a specific engine yet. Try asking about a "
                "product, country, HSN code, duty, compliance step, or business service."
            )

        answer = headline + "\n\n" + "\n\n".join(sections)
        return {"answer": answer, "provider": self.name, "live": False}


class _DeferredLiveProvider(BaseProvider):
    """Placeholder for OpenAI / Anthropic / Gemini / local.

    Live calls are intentionally NOT implemented yet. When enabled, this is where
    the integration playbook code (emergentintegrations / SDK) plugs in. Until then
    it gracefully degrades to the mock composer so the product never breaks.
    """
    def __init__(self, name):
        self.name = name
        self.live = False
        self._mock = MockProvider()

    def generate(self, question, intent, entities, engine_outputs, context):
        res = self._mock.generate(question, intent, entities, engine_outputs, context)
        res["provider"] = self.name
        res["note"] = "Live AI provider configured but not yet activated — using deterministic engine composition."
        return res


_PROVIDERS = {}


def get_provider() -> BaseProvider:
    name = os.environ.get("BRAIN_AI_PROVIDER", "mock").lower()
    if name not in _PROVIDERS:
        if name == "mock":
            _PROVIDERS[name] = MockProvider()
        else:
            _PROVIDERS[name] = _DeferredLiveProvider(name)
    return _PROVIDERS[name]


def provider_status() -> dict:
    name = os.environ.get("BRAIN_AI_PROVIDER", "mock").lower()
    return {
        "active": name,
        "live": name != "mock",
        "supported": ["mock", "openai", "anthropic", "gemini", "local"],
        "note": "Set BRAIN_AI_PROVIDER + provider key to activate live AI.",
    }
