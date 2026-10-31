# Iteration 82: Comtrade fallback + sitemap/SEO regression (HTTP only; no admin, no force rebuilds)
import os
import re
import pytest
import requests


def _base():
    url = os.environ.get("REACT_APP_BACKEND_URL")
    if not url:
        for line in open("/app/frontend/.env"):
            if line.startswith("REACT_APP_BACKEND_URL="):
                url = line.split("=", 1)[1].strip()
    return url.rstrip("/")


BASE_URL = _base()
S = requests.Session()


# trade-intel status / stats
def test_status_comtrade_enabled():
    d = S.get(f"{BASE_URL}/api/trade-intel/status", timeout=30).json()
    assert d["ok"] is True and d["comtradeEnabled"] is True


@pytest.mark.parametrize("hs", ["330741", "300490", "090111"])
def test_stats_oec_primary(hs):
    d = S.get(f"{BASE_URL}/api/trade-intel/stats", params={"hs": hs}, timeout=90).json()
    assert d["ok"] is True
    assert d["sourceKey"] == "oec"
    assert d["totalWorldTradeUSD"] > 0
    assert len(d["topImporters"]) == 12
    assert d["trend"]
    names = [i["country"] for i in d["topImporters"]]
    assert len(names) == len(set(names))


# sitemap regression
def test_sitemap_counts():
    r = S.get(f"{BASE_URL}/api/sitemap.xml", timeout=120)
    assert r.status_code == 200
    locs = re.findall(r"<loc>([^<]+)</loc>", r.text)
    assert len(locs) >= 950, len(locs)
    assert any("/export/" in l and "/to/" in l and "/api/answers/html/" not in l for l in locs)
    assert any("/api/answers/html/export/" in l for l in locs)
    for slug in ["europe", "middle-east", "asia-pacific", "americas", "africa"]:
        assert any(l.endswith(f"/regions/{slug}") for l in locs), slug


def test_matrix_limit5():
    d = S.get(f"{BASE_URL}/api/seo/matrix", params={"limit": 5}, timeout=90).json()
    assert d["indexable"] == 5
    assert not d.get("stale")


# guide pages
@pytest.mark.parametrize("prod,country", [("agarbatti", "germany"), ("pharmaceuticals", "portugal"),
                                          ("indian-spices", "italy"), ("basmati-rice", "israel")])
def test_page_data_demand(prod, country):
    r = S.get(f"{BASE_URL}/api/seo/page-data/{prod}/{country}", timeout=120)
    assert r.status_code == 200
    d = r.json()
    dem = d["demand"]
    assert d["indexable"] is True
    assert dem["worldImportsUSD"] and dem["countryImportsUSD"] and dem["trend"]
    if prod == "agarbatti":
        assert d["dataScore"] == 100
