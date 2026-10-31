# Iteration 83: sitemap timeout guard, egress-check endpoint, trade-intel/SEO regression (preview only)
import os
import re
import time
import xml.etree.ElementTree as ET
from collections import Counter

import pytest
import requests


def _env(path, key):
    for line in open(path):
        if line.startswith(key + "="):
            return line.split("=", 1)[1].strip().strip('"')


BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or _env("/app/frontend/.env", "REACT_APP_BACKEND_URL")).rstrip("/")
ADMIN = _env("/app/backend/.env", "ADMIN_TOKEN")
KEY = _env("/app/backend/.env", "COMTRADE_API_KEY") or ""
NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


@pytest.fixture(scope="module")
def sitemap():
    t = time.time()
    r = requests.get(f"{BASE_URL}/api/sitemap.xml", timeout=60)
    return r, time.time() - t


# --- Sitemap ---
class TestSitemap:
    def test_status_and_time(self, sitemap):
        r, dt = sitemap
        print(f"sitemap status={r.status_code} seconds={dt:.2f} bytes={len(r.content)}")
        assert r.status_code == 200
        assert "xml" in r.headers.get("content-type", "")
        assert dt < 30

    def test_contents(self, sitemap):
        r, _ = sitemap
        root = ET.fromstring(r.content)
        urls = root.findall(f"{NS}url")
        locs = [u.find(f"{NS}loc").text for u in urls]
        print(f"loc count={len(locs)}")
        dups = [k for k, v in Counter(locs).items() if v > 1]
        print(f"duplicates={len(dups)} sample={dups[:5]}")
        for u in urls:
            assert u.find(f"{NS}lastmod") is not None and u.find(f"{NS}changefreq") is not None \
                and u.find(f"{NS}priority") is not None
        exp = [l for l in locs if re.search(r"/export/[^/]+/to/[^/]+$", l)]
        ans = [l for l in locs if "/api/answers/html/" in l]
        reg = [l for l in locs if "/regions/" in l]
        print(f"export={len(exp)} answers={len(ans)} regions={len(reg)} {reg}")
        assert len(locs) >= 900
        assert exp and ans
        assert len(reg) >= 5
        assert not dups


# --- Egress check ---
class TestEgress:
    def test_no_token(self):
        r = requests.get(f"{BASE_URL}/api/trade-intel/egress-check", timeout=30)
        assert r.status_code == 403

    def test_wrong_token(self):
        r = requests.get(f"{BASE_URL}/api/trade-intel/egress-check", headers={"X-Admin-Token": "nope"}, timeout=30)
        assert r.status_code == 403

    def test_admin(self):
        r = requests.get(f"{BASE_URL}/api/trade-intel/egress-check", headers={"X-Admin-Token": ADMIN}, timeout=90)
        assert r.status_code == 200
        d = r.json()
        print({k: {kk: vv for kk, vv in v.items() if kk != "body"} for k, v in d["targets"].items()})
        assert d["comtradeKeySet"] is True
        for name in ("oec", "comtrade", "control_wits"):
            assert d["targets"][name]["status"] == 200, (name, d["targets"][name])
        assert KEY and KEY not in r.text


# --- Regression ---
class TestRegression:
    def test_status(self):
        d = requests.get(f"{BASE_URL}/api/trade-intel/status", timeout=30).json()
        assert d.get("ok") is True and d.get("comtradeEnabled") is True

    def test_stats(self):
        d = requests.get(f"{BASE_URL}/api/trade-intel/stats", params={"hs": "330741"}, timeout=60).json()
        print({k: d.get(k) for k in ("ok", "sourceKey")}, len(d.get("topImporters") or []), len(d.get("trend") or []))
        assert d["ok"] is True and d.get("sourceKey") == "oec"
        assert len(d["topImporters"]) == 12 and d["trend"]

    def test_matrix(self):
        d = requests.get(f"{BASE_URL}/api/seo/matrix", params={"limit": 5}, timeout=60).json()
        print({k: v for k, v in d.items() if k not in ("rows", "items")})
        assert d.get("indexable") == 5 and not d.get("stale")

    def test_page_data(self):
        d = requests.get(f"{BASE_URL}/api/seo/page-data/agarbatti/germany", timeout=60).json()
        print(d.get("indexable"), d.get("dataScore"), list((d.get("demand") or {}).keys())[:8])
        assert d["indexable"] is True and d["dataScore"] == 100 and d.get("demand")
