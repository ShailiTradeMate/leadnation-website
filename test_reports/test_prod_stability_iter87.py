# Iteration 87: production-stability fixes (sitemap cache, health, deferred startup, OEC/WITS)
import os, re, time
import pytest, requests
from dotenv import dotenv_values

BASE_URL = dotenv_values('/app/frontend/.env')['REACT_APP_BACKEND_URL'].strip('"').rstrip('/')
ADMIN = dotenv_values('/app/backend/.env')['ADMIN_TOKEN'].strip('"')
S = requests.Session()
STATE = {}


def _get_sitemap():
    t = time.time()
    r = S.get(f"{BASE_URL}/api/sitemap.xml", timeout=60)
    return r, time.time() - t


# --- Sitemap served from cache ---
class TestSitemap:
    def test_sitemap_three_calls_fast_identical(self):
        counts = []
        for i in range(3):
            r, dt = _get_sitemap()
            assert r.status_code == 200
            print(f"call {i}: {dt:.2f}s urls={r.headers.get('X-Sitemap-Urls')} built={r.headers.get('X-Sitemap-Built')}")
            assert dt < 3, f"slow sitemap {dt:.2f}s"
            assert r.headers.get("X-Sitemap-Built"), "missing X-Sitemap-Built"
            locs = re.findall(r"<loc>(.*?)</loc>", r.text)
            assert len(locs) == int(r.headers["X-Sitemap-Urls"])
            assert len(locs) == len(set(locs)), f"duplicates: {len(locs) - len(set(locs))}"
            assert 900 <= len(locs) <= 1100
            counts.append(len(locs))
            STATE["built"] = r.headers["X-Sitemap-Built"]
            STATE["locs"] = locs
        assert len(set(counts)) == 1

    def test_sitemap_contains_url_families(self):
        locs = STATE.get("locs") or re.findall(r"<loc>(.*?)</loc>", _get_sitemap()[0].text)
        assert any(re.search(r"/export/[^/]+/to/[^/]+", l) for l in locs)
        assert any("/regions/" in l for l in locs)
        assert any("/api/answers/html/" in l for l in locs)
        print("export:", sum(1 for l in locs if "/to/" in l), "regions:", sum(1 for l in locs if "/regions/" in l),
              "answers:", sum(1 for l in locs if "/api/answers/html/" in l))

    def test_refresh_requires_token(self):
        r = S.post(f"{BASE_URL}/api/sitemap/refresh", timeout=30)
        assert r.status_code == 403
        r = S.post(f"{BASE_URL}/api/sitemap/refresh", headers={"X-Admin-Token": "wrong"}, timeout=30)
        assert r.status_code == 403

    def test_refresh_with_token_and_built_newer(self):
        before = STATE.get("built") or _get_sitemap()[0].headers["X-Sitemap-Built"]
        t = time.time()
        r = S.post(f"{BASE_URL}/api/sitemap/refresh", headers={"X-Admin-Token": ADMIN}, timeout=90)
        print(f"refresh {time.time() - t:.1f}s -> {r.status_code} {r.text[:200]}")
        assert r.status_code == 200
        d = r.json()
        assert d["ok"] is True
        assert 900 <= d.get("count", d.get("kept", 0)) <= 1100
        r2, dt = _get_sitemap()
        assert dt < 3
        after = r2.headers["X-Sitemap-Built"]
        print("built before/after:", before, after)
        assert after > before


# --- Health probes ---
class TestHealth:
    def test_api_health_external(self):
        t = time.time()
        r = S.get(f"{BASE_URL}/api/health", timeout=10)
        assert r.status_code == 200 and r.json() == {"ok": True}
        assert time.time() - t < 1.5

    def test_localhost_health(self):
        t = time.time()
        r = requests.get("http://localhost:8001/health", timeout=5)
        assert r.status_code == 200 and r.json() == {"ok": True}
        assert time.time() - t < 1


# --- Deferred-startup regression: seeded data still served ---
class TestDeferredStartup:
    def test_blog(self):
        r = S.get(f"{BASE_URL}/api/blog", timeout=20)
        assert r.status_code == 200
        d = r.json()
        items = d if isinstance(d, list) else d.get("items", d.get("posts", []))
        assert isinstance(items, list) and len(items) > 0

    def test_trade_intel_status(self):
        r = S.get(f"{BASE_URL}/api/trade-intel/status", timeout=20)
        assert r.status_code == 200
        d = r.json()
        print(d)
        assert d.get("ok") is True and d.get("hsCodesIndexed", 0) > 5000

    def test_seo_matrix(self):
        t = time.time()
        r = S.get(f"{BASE_URL}/api/seo/matrix", params={"limit": 3}, timeout=20)
        dt = time.time() - t
        assert r.status_code == 200
        d = r.json()
        rows = d if isinstance(d, list) else d.get("rows", [])
        print(f"matrix {dt:.2f}s rows={len(rows)}")
        assert len(rows) > 0 and dt < 3

    def test_page_data(self):
        r = S.get(f"{BASE_URL}/api/seo/page-data/agarbatti/bangladesh", timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), dict)

    def test_duty_meta(self):
        r = S.get(f"{BASE_URL}/api/duty/meta", timeout=20)
        assert r.status_code == 200
        print(r.json())
        assert r.json().get("lastRefresh")


# --- OEC status check + fallback ---
class TestTradeIntel:
    def test_stats_330741(self):
        t = time.time()
        r = S.get(f"{BASE_URL}/api/trade-intel/stats", params={"hs": "330741"}, timeout=30)
        dt = time.time() - t
        d = r.json()
        print(f"stats {dt:.2f}s sourceKey={d.get('sourceKey')}")
        assert r.status_code == 200 and d.get("ok") is True
        assert d.get("sourceKey") in ("oec", "comtrade")
        assert dt < 5


# --- iteration_86 regression ---
class TestMatrixRegression:
    def test_warm_status(self):
        r = S.get(f"{BASE_URL}/api/seo/warm-status", headers={"X-Admin-Token": ADMIN}, timeout=20)
        assert r.status_code == 200
        m = r.json().get("matrix")
        print(m)
        assert m and m.get("rows") == 440 and m.get("partial") is False
        assert 350 <= m.get("indexable", 0) <= 440

    def test_rebuild_no_token(self):
        r = S.post(f"{BASE_URL}/api/seo/matrix/rebuild", timeout=20)
        assert r.status_code == 403
