# Iter84: healthy-path check in a fresh process + restore caches to OEC (no patching)
import asyncio, sys, time
sys.path.insert(0, "/app/backend")
import trade_intel as T


async def main():
    codes = sys.argv[1:] or ["330741"]
    for c in codes:
        t0 = time.time()
        s = await T.trade_stats(c, force=True)
        tbl = await T.importer_table(c, force=True)
        print(f"{c}: {time.time()-t0:.1f}s src={s.get('sourceKey')} year={s.get('year')} trend={len(s.get('trend') or [])} "
              f"exporters={len(s.get('topExporters') or [])} table_src={tbl and tbl['source']} table_count={tbl and tbl['count']} "
              f"top={[(r['country'], r['value']) for r in s['topImporters'][:3]]} breaker={T._oec_down()}")


asyncio.run(main())
