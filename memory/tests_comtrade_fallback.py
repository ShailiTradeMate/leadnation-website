"""Simulates the production failure: OEC unreachable -> the keyed Comtrade source must keep
the demand pillar (and therefore sitemap indexability) alive."""
import asyncio, sys
sys.path.insert(0, "/app/backend")
import trade_intel as T
import seo_pages


async def boom(*a, **k):
    raise RuntimeError("simulated OEC egress failure")


async def main():
    T._oec_query = boom  # _oec_stats and importer_table both catch this, as in production
    await T.CACHE.delete_many({"_id": {"$in": ["stats:330741", "imptable:330741"]}})

    s = await T.trade_stats("330741")
    print("stats ok:", s.get("ok"), "| source:", s.get("source"), "| year:", s.get("year"),
          "| world:", s.get("totalWorldTradeUSD"), "| importers:", len(s.get("topImporters") or []))
    assert s.get("ok") and s["sourceKey"] == "comtrade"
    assert (s.get("totalWorldTradeUSD") or 0) > 0 and s["topImporters"]

    d = await T.importer_detail("330741", "Germany")
    print("Germany detail:", d)
    assert d and d["countryImportsUSD"] and d["countryRank"]

    demand = await seo_pages._demand_section("330741", "Germany")
    print("demand pillar:", bool(demand), "| worldImportsUSD:", (demand or {}).get("worldImportsUSD"),
          "| countryImportsUSD:", (demand or {}).get("countryImportsUSD"))
    assert demand and demand["worldImportsUSD"] and demand["countryImportsUSD"]
    print("PASS: Comtrade keeps the demand pillar alive while OEC is down")


asyncio.run(main())
