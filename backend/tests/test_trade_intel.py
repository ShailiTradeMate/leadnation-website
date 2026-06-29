"""Backend tests for Phase A — Live Global Trade Intelligence."""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://global-trade-hub-176.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# /api/trade-intel/status — first call may take long while it builds the HS map.
class TestTradeIntelStatus:
    def test_status(self, session):
        r = session.get(f"{API}/trade-intel/status", timeout=120)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["ok"] is True
        assert data["comtradeEnabled"] is False
        assert data["alwaysOn"] == "OEC World"
        assert isinstance(data["hsCodesIndexed"], int)
        assert data["hsCodesIndexed"] > 5000, f"hsCodesIndexed={data['hsCodesIndexed']}"


# /api/trade-intel/hs-search — text + numeric searches
class TestHsSearch:
    def test_text_search_coffee(self, session):
        r = session.get(f"{API}/trade-intel/hs-search", params={"q": "coffee"}, timeout=60)
        assert r.status_code == 200
        results = r.json().get("results", [])
        assert len(results) > 0
        # Look for 090111 (Unroasted coffee) in results
        hs_codes = [x["hs6"] for x in results]
        assert any(h.startswith("0901") for h in hs_codes), f"No coffee HS code in {hs_codes}"

    def test_numeric_search(self, session):
        r = session.get(f"{API}/trade-intel/hs-search", params={"q": "8517"}, timeout=60)
        assert r.status_code == 200
        results = r.json().get("results", [])
        assert len(results) > 0
        for x in results:
            assert x["hs6"].startswith("8517")


# /api/trade-intel/stats — real data from OEC
class TestTradeStats:
    @pytest.mark.parametrize("hs", ["090111", "270900", "851713"])
    def test_real_stats(self, session, hs):
        r = session.get(f"{API}/trade-intel/stats", params={"hs": hs}, timeout=90)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("ok") is True, d
        assert "OEC" in d["source"]
        assert 2020 <= d["year"] <= 2025, f"year={d['year']}"
        assert d["totalWorldTradeUSD"] > 0
        assert isinstance(d["topImporters"], list) and len(d["topImporters"]) > 0
        first = d["topImporters"][0]
        assert "country" in first and "value" in first and "share" in first
        assert isinstance(d["topExporters"], list) and len(d["topExporters"]) > 0
        assert isinstance(d["trend"], list) and len(d["trend"]) > 0

    def test_invalid_short_hs(self, session):
        r = session.get(f"{API}/trade-intel/stats", params={"hs": "99"}, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d.get("ok") is False
        assert "error" in d


# Brain integration
class TestBrainTradeStats:
    def test_brain_trade_stats(self, session):
        payload = {"question": "top importers and world trade value for HS 090111",
                   "session_id": "qa-trade"}
        r = session.post(f"{API}/brain/ask", json=payload, timeout=120)
        assert r.status_code == 200, r.text
        d = r.json()
        engines = d.get("enginesUsed", [])
        assert "trade_statistics" in engines, f"engines={engines}"
        outs = d.get("engineOutputs", {})
        assert "trade_statistics" in outs
        ts = outs["trade_statistics"]
        assert ts.get("data", {}).get("hsCode") == "090111"
        ans = (d.get("answer") or "").lower()
        # Real numbers/countries should be present in answer somewhere
        assert any(tok in ans for tok in ["coffee", "import", "$", "billion", "million", "world"]), ans[:200]
