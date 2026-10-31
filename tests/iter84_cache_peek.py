# Iter84: inspect cached stats/imptable for an HS code (read-only)
import asyncio, sys
sys.path.insert(0, "/app/backend")
import trade_intel as T


async def main():
    for c in sys.argv[1:]:
        s = await T.CACHE.find_one({"_id": f"stats:{c}"})
        t = await T.CACHE.find_one({"_id": f"imptable:{c}"})
        r = (s or {}).get("result", {})
        names = [x["country"] for x in r.get("topImporters", [])]
        print(c, r.get("sourceKey"), r.get("year"), r.get("totalWorldTradeUSD"),
              [(x["country"], x["value"], x["share"]) for x in r.get("topImporters", [])[:4]],
              "dupes", len(names) != len(set(names)),
              "| table", t and t["result"]["source"], t and t["result"]["count"],
              t and round(sum(x["share"] for x in t["result"]["rows"]), 1))


asyncio.run(main())
