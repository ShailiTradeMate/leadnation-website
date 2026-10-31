# Iteration 86: SEO matrix cache-only endpoint, cross-replica lock, sitemap completeness,
# cache import/export, health routes, egress-check, trade-intel regressions.
import os
import re
import time
from collections import Counter

import pytest
import requests
from dotenv import dotenv_values

BASE_URL = dotenv_values("/app/frontend/.env")["REACT_APP_BACKEND_URL"].rstrip("/")
ADMIN = dotenv_values("/app/backend/.env")["ADMIN_TOKEN"]
H = {"X-Admin-Token": ADMIN}
BAD = {"X-Admin-Token": "wrong-token"}

_state = {}


def _locs():
    t = time.time()
    r = requests.get(f"{BASE_URL}/api/sitemap.xml", timeout=40)
    el = time.time() - t
    return r, el, re.findall(r"<loc>(.*?)</loc>", r.text)


# --- health
class TestHealth:
    @pytest.mark.parametrize("path", ["/api/health", "/health"])
    def test_health(self, path):
        r = requests.get(f"{BASE_URL}{path}", timeout=15)
        print(path, r.status_code, r.text[:200])
        assert r.status_code == 200
        assert r.json().get("ok") is True


# --- sitemap (before rebuild)
class TestSitemap:
    def test_sitemap_complete(self):
        r, el, locs = _locs()
        print("sitemap", r.status_code, round(el, 1), "s", len(locs), "locs")
        dups = [k for k, v in Counter(locs).items() if v > 1]
        print("dups", dups[:10])
        assert r.status_code == 200
        assert el < 20
        assert len(locs) >= 900
        assert any("/export/" in l and "/to/" in l for l in locs)
        assert any("/regions/" in l for l in locs)
        assert any("/api/answers/html/" in l for l in locs)
        assert not dups, f"duplicate locs: {dups[:10]}"


# --- matrix (cache-only)
class TestMatrix:
    def test_matrix_limit5(self):
        t = time.time()
        r = requests.get(f"{BASE_URL}/api/seo/matrix", params={"limit": 5}, timeout=30)
        el = time.time() - t
        d = r.json()
        print("matrix", r.status_code, round(el, 2), {k: v for k, v in d.items() if k != "rows"})
        assert r.status_code == 200 and el < 10
        assert d["count"] == 5 and len(d["rows"]) == 5
        assert d["partial"] is False and d.get("cachedAt")
        assert "indexable" in d
        _state["row0"] = d["rows"][0]

    def test_matrix_min70(self):
        r = requests.get(f"{BASE_URL}/api/seo/matrix", params={"min_score": 70, "limit": 1000}, timeout=30)
        d = r.json()
        print("min70", d["count"], d["indexable"])
        assert r.status_code == 200
        assert 350 <= d["indexable"] <= 440


# --- warm-status
class TestWarmStatus:
    def test_no_token(self):
        assert requests.get(f"{BASE_URL}/api/seo/warm-status", timeout=30).status_code == 403

    def test_with_token(self):
        r = requests.get(f"{BASE_URL}/api/seo/warm-status", headers=H, timeout=60)
        assert r.status_code == 200
        m = r.json()["matrix"]
        print("matrix status", m)
        assert m["rows"] == 440 and 350 <= m["indexable"] <= 440
        assert m["partial"] is False and m["buildingHere"] is False and m["lockUntil"] is None
        assert m["cachedAt"]


# --- cache export / import
class TestCacheIO:
    def test_export_no_token(self):
        r = requests.get(f"{BASE_URL}/api/seo/cache-export", params={"collection": "duty_cache", "limit": 2}, timeout=30)
        assert r.status_code == 403

    def test_export_users_400(self):
        r = requests.get(f"{BASE_URL}/api/seo/cache-export", params={"collection": "users"}, headers=H, timeout=30)
        assert r.status_code == 400

    def test_export_ok(self):
        r = requests.get(f"{BASE_URL}/api/seo/cache-export", params={"collection": "duty_cache", "limit": 2}, headers=H, timeout=30)
        d = r.json()
        print({k: v for k, v in d.items() if k != "docs"}, d["docs"][:1])
        assert r.status_code == 200
        assert d["collection"] == "duty_cache" and d["skip"] == 0 and d["total"] >= 2
        assert len(d["docs"]) == 2 and all(isinstance(x["_id"], str) for x in d["docs"])
        _state["docs"] = d["docs"]

    def test_import_ok(self):
        docs = _state.get("docs") or pytest.skip("no export")
        r = requests.post(f"{BASE_URL}/api/seo/cache-import", json={"collection": "duty_cache", "docs": docs}, headers=H, timeout=30)
        print(r.status_code, r.text)
        assert r.status_code == 200 and r.json()["ok"] is True and r.json()["written"] == 2
        # idempotent: total unchanged
        r2 = requests.get(f"{BASE_URL}/api/seo/cache-export", params={"collection": "duty_cache", "limit": 2}, headers=H, timeout=30)
        assert r2.json()["docs"] == docs

    def test_import_users_400(self):
        r = requests.post(f"{BASE_URL}/api/seo/cache-import", json={"collection": "users", "docs": []}, headers=H, timeout=30)
        assert r.status_code == 400

    def test_import_wrong_token(self):
        r = requests.post(f"{BASE_URL}/api/seo/cache-import", json={"collection": "duty_cache", "docs": []}, headers=BAD, timeout=30)
        assert r.status_code == 403


# --- trade-intel
class TestTradeIntel:
    def test_egress_no_token(self):
        assert requests.get(f"{BASE_URL}/api/trade-intel/egress-check", timeout=60).status_code == 403

    def test_egress_ok(self):
        r = requests.get(f"{BASE_URL}/api/trade-intel/egress-check", headers=H, timeout=90)
        d = r.json()
        print(d)
        assert r.status_code == 200
        t = d.get("targets", d)
        for k in ("oec", "comtrade", "control_wits"):
            assert t[k]["status"] == 200, (k, t.get(k))

    def test_status(self):
        r = requests.get(f"{BASE_URL}/api/trade-intel/status", timeout=30)
        d = r.json()
        print(d)
        assert d["ok"] is True and d["comtradeEnabled"] is True and "oecSkippedUntil" in d

    def test_stats(self):
        t = time.time()
        r = requests.get(f"{BASE_URL}/api/trade-intel/stats", params={"hs": "330741"}, timeout=60)
        el = time.time() - t
        d = r.json()
        print(round(el, 2), {k: d.get(k) for k in ("ok", "sourceKey")})
        assert r.status_code == 200 and d["ok"] is True and d.get("sourceKey") in ("oec", "comtrade")
        assert el < 20

    def test_page_data(self):
        row = _state.get("row0") or {"product": "agarbatti", "country": "bangladesh"}
        t = time.time()
        r = requests.get(f"{BASE_URL}/api/seo/page-data/{row['product']}/{row['country']}", timeout=60)
        print(row["url"] if "url" in row else row, r.status_code, round(time.time() - t, 2))
        assert r.status_code == 200 and isinstance(r.json(), dict)


# --- rebuild + lock (runs last; starts a ~25 min background job)
class TestZRebuild:
    def test_rebuild_no_token(self):
        assert requests.post(f"{BASE_URL}/api/seo/matrix/rebuild", timeout=30).status_code == 403

    def test_rebuild_wrong_token(self):
        assert requests.post(f"{BASE_URL}/api/seo/matrix/rebuild", headers=BAD, timeout=30).status_code == 403

    def test_rebuild_start(self):
        t = time.time()
        r = requests.post(f"{BASE_URL}/api/seo/matrix/rebuild", headers=H, timeout=30)
        el = time.time() - t
        print(r.status_code, r.text, round(el, 2))
        assert r.status_code == 200 and r.json() == {"ok": True, "started": True} and el < 5
        time.sleep(1.5)
        m = requests.get(f"{BASE_URL}/api/seo/warm-status", headers=H, timeout=60).json()["matrix"]
        print("after start", m)
        assert m["buildingHere"] is True and m["lockUntil"]

    def test_rebuild_wait_skipped(self):
        t = time.time()
        r = requests.post(f"{BASE_URL}/api/seo/matrix/rebuild", params={"wait": "true"}, headers=H, timeout=30)
        el = time.time() - t
        print(r.status_code, r.text, round(el, 2))
        assert r.status_code == 200 and el < 10
        assert r.json() == {"ok": False, "skipped": "already building on this replica"}

    def test_sitemap_during_build(self):
        r, el, locs = _locs()
        print("during build sitemap", r.status_code, round(el, 1), len(locs))
        assert r.status_code == 200 and len(locs) >= 900 and el < 20

    def test_matrix_during_build(self):
        t = time.time()
        r = requests.get(f"{BASE_URL}/api/seo/matrix", params={"limit": 5}, timeout=30)
        el = time.time() - t
        d = r.json()
        print("during build matrix", round(el, 2), {k: v for k, v in d.items() if k != "rows"})
        assert r.status_code == 200 and el < 10 and d["count"] == 5
