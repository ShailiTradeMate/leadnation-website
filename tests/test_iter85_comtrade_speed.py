"""Iter85: Comtrade fallback speed fix - year choice, single fetch per cold HS, 85% completeness rule.
Run: cd /app/backend && python3 /app/tests/test_iter85_comtrade_speed.py"""
import asyncio, sys, time
sys.path.insert(0, "/app/backend")
import trade_intel as T

HS = "330741"
calls = []
_orig_call = T._comtrade_call


async def counting_call(cx, flow, hs6, year):
    rows = await _orig_call(cx, flow, hs6, year)
    calls.append((flow, hs6, year, None if rows is None else len(rows)))
    return rows


async def boom(*a, **k):
    raise RuntimeError("simulated blocked egress")


async def test_single_fetch_and_year():
    T._oec_query = boom
    T._OEC_DOWN_UNTIL = None
    T._comtrade_call = counting_call
    await T.CACHE.delete_many({"_id": {"$in": [f"stats:{HS}", f"imptable:{HS}"]}})
    t0 = time.time()
    s = await T.trade_stats(HS)
    d = await T.importer_detail(HS, "Germany")
    el = round(time.time() - t0, 1)
    print(f"[single-fetch] calls={calls} elapsed={el}s year={s.get('year')} source={s.get('sourceKey')} "
          f"germany={d.get('countryImportsUSD')} reporters={d.get('countriesReporting')}")
    assert len(calls) == 1, f"expected exactly 1 Comtrade fetch, got {len(calls)}"
    assert s["sourceKey"] == "comtrade" and s["year"] == 2024 and d["year"] == 2024
    assert abs(d["countryImportsUSD"] - 7.79e6) < 0.05e6, d["countryImportsUSD"]
    print("PASS single fetch + correct year (2024, Germany ~7.79M)")


async def test_85_rule():
    # Synthetic: year-2 thin (100), year-1 (120), year-3 (150) -> best=150, 85% = 127.5 -> 2023 chosen
    fake = {2024: 100, 2025: 120, 2023: 150}
    seq = []

    async def fake_call(cx, flow, hs6, year):
        seq.append(year)
        return [{"i": i} for i in range(fake[year])]
    T._comtrade_call = fake_call
    rows, y = await T._comtrade_imports(None, HS)
    print(f"[85%] order={seq} chosen={y} rows={len(rows)}")
    assert seq == [2024, 2025, 2023] and y == 2023

    # year-2 thin (130), year-1 near (125), year-3 (145): best 145, 85%=123.25 -> newest qualifying = 2025
    fake.update({2024: 130, 2025: 125, 2023: 145}); seq.clear()
    rows, y = await T._comtrade_imports(None, HS)
    print(f"[85%] order={seq} chosen={y}")
    assert y == 2025

    # complete first year -> early stop
    fake.update({2024: 145}); seq.clear()
    rows, y = await T._comtrade_imports(None, HS)
    print(f"[early-stop] order={seq} chosen={y}")
    assert seq == [2024] and y == 2024

    # first year None (e.g. 429) -> continues
    async def none_first(cx, flow, hs6, year):
        seq.append(year)
        return None if year == 2024 else [{"i": i} for i in range(fake[year])]
    T._comtrade_call = none_first; seq.clear()
    rows, y = await T._comtrade_imports(None, HS)
    print(f"[first-None] order={seq} chosen={y}")
    assert y in (2025, 2023)
    T._comtrade_call = _orig_call
    print("PASS 85% rule / early stop")


async def main():
    await test_single_fetch_and_year()
    await test_85_rule()
    print("ALL PASS")

asyncio.run(main())
