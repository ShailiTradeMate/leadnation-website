"""With OEC unreachable, the first call parks it and later calls must not pay the dead wait.
Target: a cold fallback page build stays in single digits (Comtrade download is ~4MB/year,
fetched concurrently), and a repeat call is served from cache in well under a second."""
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
        assert s.get("ok") and s["sourceKey"] == "comtrade", "fallback source not used"
        assert (d or {}).get("countryImportsUSD"), "no per-country figure from the fallback"

    t0 = time.time()
    await T.trade_stats(codes[0])
    cached = round(time.time() - t0, 2)
    print(f"repeat call (cached): {cached}s")

    assert T._oec_down(), "breaker did not open"
    assert timings[1] < 10 and timings[2] < 10, f"later calls still slow: {timings}"
    assert cached < 1, f"cached call took {cached}s"
    print(f"PASS: first {timings[0]}s (incl. the 8s that trips the breaker), "
          f"later {timings[1:]}s, cached {cached}s")


asyncio.run(main())
