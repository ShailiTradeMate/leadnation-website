"""LeadNation Brain — the central intelligence layer.

Reusable across Website, Mobile App, Admin / Partner / Customer portals.
Architecture-first: AI responses are MOCK/rule-based today; provider layer is
configurable so live OpenAI / Anthropic / Gemini / local models can be activated
later with minimal code changes.
"""

ENGINE_REGISTRY = [
    "country_context", "trade_news", "market_intelligence", "learning",
    "compliance", "tariff", "logistics", "policy", "product_intelligence",
    "business_services", "marketplace", "network",
]
