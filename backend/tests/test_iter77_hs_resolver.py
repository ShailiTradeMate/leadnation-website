"""Iter77 — HS smart resolver (local names, misspellings) across Brain/Trade-intel/Compile."""
import os
import time
import pytest
import requests

BASE = os.environ.get("REACT_APP_BACKEND_URL", "https://leadnation-build.preview.emergentagent.com").rstrip("/")

SHORT = 30
LONG = 180


def _post(path, payload, timeout=LONG):
    return requests.post(f"{BASE}{path}", json=payload, timeout=timeout)


def _get(path, timeout=SHORT):
    return requests.get(f"{BASE}{path}", timeout=timeout)


# ---------- /api/trade-intel/hs-search (AI fallback) ----------
class TestHsSearchFallback:
    def test_rice_directory_fast(self):
        t0 = time.time()
        r = _get("/api/trade-intel/hs-search?q=rice")
        elapsed = time.time() - t0
        assert r.status_code == 200
        data = r.json()
        rows = data if isinstance(data, list) else data.get("results") or data.get("rows") or []
        assert rows, f"expected rows for rice, got {data}"
        assert elapsed < 10, f"directory query should be fast, took {elapsed:.1f}s"

    @pytest.mark.parametrize("q,expect_hs", [("brinjal", "070930"), ("okra", "070999")])
    def test_local_name_ai_fallback(self, q, expect_hs):
        r = requests.get(f"{BASE}/api/trade-intel/hs-search?q={q}", timeout=LONG)
        assert r.status_code == 200, r.text
        data = r.json()
        rows = data if isinstance(data, list) else data.get("results") or data.get("rows") or []
        assert rows, f"expected AI-fallback result for {q}, got empty"
        top = rows[0]
        assert top.get("hs6") == expect_hs, f"{q} resolved to {top.get('hs6')}, expected {expect_hs}"


# ---------- /api/brain/explore (country+product local name) ----------
class TestBrainExploreResolution:
    def test_bringle_country_argentina(self):
        r = _post("/api/brain/explore",
                  {"kind": "country", "destination": "Argentina", "product": "bringle"})
        assert r.status_code == 200, r.text
        data = r.json()
        hs = data.get("hs6") or (data.get("hsResolution") or {}).get("hs6")
        assert hs == "070930", f"bringle→Argentina hs6={hs}"
        res = data.get("hsResolution") or {}
        assert "eggplant" in (res.get("canonical") or res.get("description") or "").lower() \
            or "aubergin" in (res.get("canonical") or res.get("description") or "").lower()

    def test_okra_product_uae(self):
        r = _post("/api/brain/explore",
                  {"kind": "product", "product": "okra", "destination": "United Arab Emirates", "origin": "India"})
        assert r.status_code == 200, r.text
        data = r.json()
        hs = data.get("hs6") or (data.get("hsResolution") or {}).get("hs6")
        assert hs == "070999", f"okra hs6={hs}"

    def test_basmati_regression(self):
        r = _post("/api/brain/explore",
                  {"kind": "corridor", "origin": "India", "destination": "Germany", "product": "Basmati rice"})
        assert r.status_code == 200, r.text
        data = r.json()
        hs = data.get("hs6") or (data.get("hsResolution") or {}).get("hs6")
        assert hs == "100630", f"basmati regression hs6={hs}"

    def test_nonsense_stays_honest(self):
        r = _post("/api/brain/explore",
                  {"kind": "country", "destination": "Germany", "product": "zzzqqxnotaproduct"})
        assert r.status_code == 200, r.text
        data = r.json()
        hs = data.get("hs6") or (data.get("hsResolution") or {}).get("hs6")
        assert not hs, f"expected no hs6 for nonsense, got {hs}"
        # Should contain a note explaining no HS code was resolved
        note_text = (data.get("hsResolution") or {}).get("note", "") + " " + (data.get("note") or "")
        notes_blob = (str(data) or "").lower()
        assert "no hs" in notes_blob or "could not" in notes_blob or "unresolved" in notes_blob, \
            f"expected a 'no HS code' note, got: {note_text}"


# ---------- /api/compile/report ----------
class TestCompileReport:
    def test_bhindi_compile(self):
        r = _get("/api/compile/report?product=bhindi&importer=784&exporter=356", timeout=LONG)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("ok") is True, f"compile not ok: {data}"
        hs = data.get("hsCode") or data.get("hs6") or (data.get("resolution") or {}).get("hs6")
        assert hs == "070999", f"compile bhindi hs={hs}, body={data}"
