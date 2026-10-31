# Iter84 regression: OEC breaker status field, page-data source, stats trend, sitemap hubs
import os
import re
import time
import requests


def _env(path, key):
    for line in open(path):
        if line.startswith(key + "="):
            return line.split("=", 1)[1].strip().strip('"')


BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or _env("/app/frontend/.env", "REACT_APP_BACKEND_URL")).rstrip("/")


# Breaker status exposed and closed in the live server
def test_status_oec_skipped_null():
    d = requests.get(f"{BASE_URL}/api/trade-intel/status", timeout=30).json()
    assert "oecSkippedUntil" in d
    assert d["oecSkippedUntil"] is None
    assert d["comtradeEnabled"] is True


# OEC remains preferred in the healthy path
def test_stats_oec_trend():
    d = requests.get(f"{BASE_URL}/api/trade-intel/stats", params={"hs": "330741"}, timeout=60).json()
    assert d["ok"] and d["sourceKey"] == "oec"
    assert len(d["trend"]) == 3
    assert len(d["topExporters"]) > 0


# Page-data for agarbatti/germany indexable from OEC
def test_page_data_agarbatti_germany():
    d = requests.get(f"{BASE_URL}/api/seo/page-data/agarbatti/germany", timeout=60).json()
    blob = str(d)
    assert d.get("indexable") is True
    assert d.get("dataScore") == 100
    assert d.get("demand")
    assert "OEC World" in blob


# Sitemap: ~975 locs, regions hubs, under 30s
def test_sitemap():
    t0 = time.time()
    r = requests.get(f"{BASE_URL}/api/sitemap.xml", timeout=90)
    el = time.time() - t0
    assert r.status_code == 200 and el < 30, el
    locs = re.findall(r"<loc>(.*?)</loc>", r.text)
    assert 950 <= len(locs) <= 1000, len(locs)
    assert any("/export/" in l for l in locs)
    assert any("/api/answers/html/" in l for l in locs)
    hubs = {l for l in locs if re.search(r"/regions/[^/]+/?$", l)}
    assert len(hubs) >= 5, hubs


# Matrix limit=5 indexable and not stale
def test_matrix_limit5():
    d = requests.get(f"{BASE_URL}/api/seo/matrix", params={"limit": 5}, timeout=60).json()
    assert d.get("indexable") == 5, {k: v for k, v in d.items() if k != "pages"}
    assert not d.get("stale")
