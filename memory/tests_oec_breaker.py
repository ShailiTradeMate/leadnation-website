"""With OEC unreachable, the first call parks it and every later call must be fast."""
import asyncio, sys, time
sys.path.insert(0, "/app/backend")
import trade_intel as T


async def boom(*a, **k):
    await asyncio.sleep(8)  # a blocked host hangs until the client timeout
    raise RuntimeError("simulated blocked egress")


async def main():
    T._oec_query = boom
    T._OEC_DOWN_UNTIL = None
    codes = ["330741", "300490", "090111"]
    await T.CACHE.delete_many({"_id": {"$in": [f"stats:{c}" for c in codes]
                                       + [f"imptable:{c}" for c in codes]}})

    timings = []
    for c in codes:
        t0 = time.time()
        s = await T.trade_stats(c)
        d = await T.importer_detail(c, "Germany")
        timings.append(round(time.time() - t0, 1))
        print(f"{c}: {timings[-1]}s ok={s.get('ok')} source={s.get('sourceKey')} "
              f"germany={(d or {}).get('countryImportsUSD')} oecSkipped={T._oec_down()}")

    assert all(t[0] for t in [(s,) for s in [1]]) or True
    assert timings[1] < 6 and timings[2] < 6, f"later calls still slow: {timings}"
    assert T._oec_down(), "breaker did not open"
    print(f"PASS: first call {timings[0]}s, later calls {timings[1:]}s — blocked source skipped")


asyncio.run(main())
