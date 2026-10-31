# Iter84: OEC breaker + shared Comtrade fetch probe (run from /app/backend in a fresh process)
import asyncio, sys, time
sys.path.insert(0, "/app/backend")
import trade_intel as T

CALLS = []
_orig = T._comtrade_call


async def counted(cx, flow, hs6, year):
    t0 = time.time()
    rows = await _orig(cx, flow, hs6, year)
    CALLS.append((flow, hs6, year, len(rows or []), round(time.time() - t0, 2)))
    return rows


async def boom(*a, **k):
    await asyncio.sleep(8)
    raise RuntimeError("simulated blocked egress")


async def main():
    codes = sys.argv[1:] or ["300490"]
    T._oec_query = boom
    T._comtrade_call = counted
    T._OEC_DOWN_UNTIL = None
    await T.CACHE.delete_many({"_id": {"$in": [f"stats:{c}" for c in codes] + [f"imptable:{c}" for c in codes]}})
    for c in codes:
        before = len(CALLS)
        t0 = time.time(); s = await T.trade_stats(c); t1 = time.time() - t0
        t0 = time.time(); s2 = await T.trade_stats(c); t2 = time.time() - t0
        t0 = time.time(); d = await T.importer_detail(c, "Germany"); t3 = time.time() - t0
        tbl = await T.importer_table(c)
        print(f"{c}: first={t1:.2f}s second={t2:.3f}s detail={t3:.3f}s src={s.get('sourceKey')} year={s.get('year')} calls={CALLS[before:]}")
        imps = s["topImporters"]
        names = [r["country"] for r in imps]
        print("  top:", [(r["country"], r["value"], r["share"]) for r in imps[:5]])
        print("  dupes:", len(names) != len(set(names)), "US-canonical:", "United States" in names or "USA" not in names,
              "full share sum:", round(sum(r["share"] for r in tbl["rows"]), 2), "count:", tbl["count"],
              "topExporters:", s["topExporters"], "trend:", s["trend"], "germany:", d)
        assert s2 == s, "second call not identical (not cached?)"


asyncio.run(main())
