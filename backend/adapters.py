"""Live Data Adapter Framework.

One standard interface for ALL external/derived data. The Trade Command Center never
knows where a value came from — it only sees an AdapterResult with a source tier and a
confidence. Facts (government/official) are NEVER mixed with AI estimates: every result
carries `aiEstimated`, `confidence`, `reason` and `assumptions`.

Priority order (highest trust first):
  government > official > live_commercial > knowledge_base > historical > ai_estimate

Current adapters wrap already-wired free sources (WITS duty, FX, OEC trade stats, gov
incentives). Future commercial feeds (freight, weather, ports, insurance, banking,
commodity, carbon…) simply `register()` an adapter implementing `fetch(ctx)` — nothing
else in the platform changes.
"""
import asyncio
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

import duty_engine
import trade_intel
from customs import _fx_rates

router = APIRouter(prefix="/adapters")

SOURCE_TIERS = ["government", "official", "live_commercial", "knowledge_base", "historical", "ai_estimate"]
_TIER_RANK = {t: i for i, t in enumerate(SOURCE_TIERS)}


def _now():
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AdapterResult:
    key: str
    value: Any = None
    source: str = ""
    sourceTier: str = "ai_estimate"
    confidence: float = 0.5          # 0..1
    aiEstimated: bool = False
    reason: str = ""
    assumptions: List[str] = field(default_factory=list)
    ok: bool = True
    asOf: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["tierRank"] = _TIER_RANK.get(self.sourceTier, 99)
        return d


class Adapter:
    key: str = ""
    label: str = ""
    domain: str = ""
    live: bool = False               # True once a real feed is connected
    tier: str = "ai_estimate"

    async def fetch(self, ctx: Dict[str, Any]) -> AdapterResult:  # pragma: no cover
        raise NotImplementedError

    def info(self) -> dict:
        return {"key": self.key, "label": self.label, "domain": self.domain,
                "live": self.live, "tier": self.tier}


REGISTRY: Dict[str, Adapter] = {}


def register(adapter: Adapter):
    REGISTRY[adapter.key] = adapter
    return adapter


def get_adapter(key: str) -> Optional[Adapter]:
    return REGISTRY.get(key)


async def run_adapters(keys: List[str], ctx: Dict[str, Any]) -> Dict[str, dict]:
    keys = [k for k in keys if k in REGISTRY]
    results = await asyncio.gather(*[REGISTRY[k].fetch(ctx) for k in keys], return_exceptions=True)
    out: Dict[str, dict] = {}
    for k, r in zip(keys, results):
        if isinstance(r, Exception):
            logging.warning("Adapter %s failed: %s", k, r)
            out[k] = AdapterResult(key=k, ok=False, reason=str(r)).to_dict()
        else:
            out[k] = r.to_dict()
    return out


# ---------------- Concrete adapters (existing free/gov sources) ----------------
class DutyAdapter(Adapter):
    key = "duty"; label = "Import Duty (WITS/TRAINS)"; domain = "customs"; live = True; tier = "government"

    async def fetch(self, ctx):
        hs6 = ctx.get("hs6") or trade_intel._norm_hs(ctx.get("hs", ""))
        origin = ctx.get("exporter", "356"); dest = ctx.get("importer", "842")
        mfn = await duty_engine.wits_tariff(dest, "000", hs6) if hs6 else None
        rate = mfn["rate"] if mfn else None; rtype = "MFN" if mfn else None; fta = False
        if hs6 and origin and origin != dest:
            pref = await duty_engine.wits_tariff(dest, origin, hs6)
            if pref and (rate is None or pref["rate"] < rate):
                rate, rtype, fta = pref["rate"], pref["type"], True
        return AdapterResult(key=self.key, value={"rate": rate, "type": rtype, "fta": fta},
                             source="World Bank WITS / UNCTAD TRAINS", sourceTier="government",
                             confidence=0.95 if rate is not None else 0.4,
                             aiEstimated=False, ok=rate is not None,
                             reason="Official applied/MFN tariff" if rate is not None else "No tariff record found")


class FXAdapter(Adapter):
    key = "fx"; label = "Foreign Exchange (live)"; domain = "banking"; live = True; tier = "official"

    async def fetch(self, ctx):
        base = (ctx.get("transactionCurrency") or "USD").upper()
        rates, cached = await _fx_rates(base)
        return AdapterResult(key=self.key, value={"base": base, "rates": rates or {}},
                             source="open.er-api.com", sourceTier="official",
                             confidence=0.9, aiEstimated=False, ok=bool(rates),
                             reason="Live daily reference rates" + (" (cached)" if cached else ""))


class TradeStatsAdapter(Adapter):
    key = "trade_stats"; label = "Trade Statistics (OEC)"; domain = "market"; live = True; tier = "official"

    async def fetch(self, ctx):
        hs6 = ctx.get("hs6") or trade_intel._norm_hs(ctx.get("hs", ""))
        stats = await trade_intel.trade_stats(hs6) if hs6 else {"ok": False}
        return AdapterResult(key=self.key, value=stats, source="OEC World",
                             sourceTier="official", confidence=0.85 if stats.get("ok") else 0.3,
                             aiEstimated=False, ok=bool(stats.get("ok")),
                             reason="Historical bilateral trade flows")


class IncentiveAdapter(Adapter):
    key = "incentives"; label = "Export Incentives (DGFT/CBIC)"; domain = "government"; live = True; tier = "government"

    async def fetch(self, ctx):
        exporter = ctx.get("exporter", "356")
        hs6 = ctx.get("hs6") or trade_intel._norm_hs(ctx.get("hs", ""))
        out = []
        if exporter == "356" and hs6:
            rb = await duty_engine.rodtep_rate(hs6)
            if rb:
                out.append({"scheme": "RoDTEP", "value": f"{rb['rate']}% of FOB", "source": rb["source"]})
        return AdapterResult(key=self.key, value=out, source="DGFT / CBIC",
                             sourceTier="government", confidence=0.9, aiEstimated=False,
                             ok=True, reason="Notified export incentive schemes")


class FreightAdapter(Adapter):
    """No live freight feed connected yet — estimates from lane + mode heuristics."""
    key = "freight"; label = "Ocean/Air Freight"; domain = "logistics"; live = False; tier = "ai_estimate"

    async def fetch(self, ctx):
        dest = ctx.get("importer", "842")
        band = None
        try:
            from costing_engine import TRANSIT_DAYS
            band = TRANSIT_DAYS.get(dest)
        except Exception:
            pass
        return AdapterResult(key=self.key, value={"transitDays": band},
                             source="LeadNation heuristics", sourceTier="ai_estimate",
                             confidence=0.5, aiEstimated=True,
                             reason="No live freight-rate feed connected; transit estimated from lane heuristics.",
                             assumptions=["Sea FCL baseline", "Excludes seasonal surcharges & BAF/CAF"])


for _a in (DutyAdapter(), FXAdapter(), TradeStatsAdapter(), IncentiveAdapter(), FreightAdapter()):
    register(_a)


# ---------------- API ----------------
@router.get("")
async def list_adapters():
    return {"adapters": [a.info() for a in REGISTRY.values()], "tiers": SOURCE_TIERS}


class RunIn(BaseModel):
    keys: List[str]
    context: Dict[str, Any] = {}


@router.post("/run")
async def run(body: RunIn):
    return {"results": await run_adapters(body.keys, body.context)}
