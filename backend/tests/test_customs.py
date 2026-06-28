"""Backend tests for the rebuilt Customs & Compliance + CHA Hub endpoints.

Covers: /customs/profile, /customs/fx (live), /customs/cbm, /customs/cha-charges,
/customs/price, /customs/freight-routes, /customs/benefits, /customs/cha-directory.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://global-trade-hub-176.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def s():
    return requests.Session()


# ---- profile (compliance report) ----
class TestProfile:
    def test_export_to_uae_fta(self, s):
        r = s.post(f"{API}/customs/profile",
                   json={"product": "agarbatti", "country": "AE", "direction": "Export"})
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ("duty", "documents", "chaSteps", "benefits", "officialLinks", "brainPrompt"):
            assert k in d, f"missing {k}"
        # export should still be MFN BCD (FTA preferential is for import side per code)
        assert "basicCustomsDuty" in d["duty"]
        assert "igst" in d["duty"]
        assert "socialWelfareSurcharge" in d["duty"]
        assert isinstance(d["documents"], list) and len(d["documents"]) >= 5
        assert isinstance(d["chaSteps"], list) and len(d["chaSteps"]) >= 4
        assert isinstance(d["benefits"], list) and len(d["benefits"]) >= 1
        for b in d["benefits"]:
            assert b["link"].startswith("http")

    def test_import_from_uae_shows_fta_preferential(self, s):
        r = s.post(f"{API}/customs/profile",
                   json={"product": "basmati rice", "country": "AE", "direction": "Import"})
        assert r.status_code == 200
        d = r.json()
        assert d["duty"]["ftaApplicable"] is True
        assert d["duty"]["basicCustomsDuty"] == "0.0%"
        assert "FTA" in (d["duty"]["note"] or "")

    def test_import_non_fta_country(self, s):
        r = s.post(f"{API}/customs/profile",
                   json={"product": "agarbatti", "country": "US", "direction": "Import"})
        assert r.status_code == 200
        d = r.json()
        assert d["duty"]["ftaApplicable"] is False


# ---- FX live ----
class TestFx:
    def test_usd_to_inr(self, s):
        r = s.get(f"{API}/customs/fx", params={"base": "USD", "target": "INR", "amount": 100})
        assert r.status_code == 200
        d = r.json()
        assert d.get("ok") is True
        assert d["base"] == "USD" and d["target"] == "INR"
        assert isinstance(d["rate"], (int, float)) and d["rate"] > 50  # realistic floor
        assert d["converted"] > 0
        assert "source" in d

    def test_eur_to_inr(self, s):
        r = s.get(f"{API}/customs/fx", params={"base": "EUR", "target": "INR", "amount": 1})
        assert r.status_code == 200
        d = r.json()
        assert d["ok"] is True
        assert d["rate"] > 60


# ---- CBM ----
def test_cbm(s):
    r = s.post(f"{API}/customs/cbm",
               json={"length_cm": 100, "width_cm": 80, "height_cm": 60, "quantity": 10, "weight_kg": 25})
    assert r.status_code == 200
    d = r.json()
    assert d["totalCBM"] == pytest.approx(4.8, rel=1e-3)
    assert "airChargeableWeightKg" in d
    assert "seaChargeableTons" in d
    assert "container20ft" in d and "container40ft" in d
    assert d["recommendation"] in ("FCL 20ft", "LCL (consolidate)")


# ---- CHA charges ----
def test_cha_charges(s):
    r = s.post(f"{API}/customs/cha-charges",
               json={"shipmentValue": 500000, "mode": "sea", "direction": "Export", "containers": 1})
    assert r.status_code == 200
    d = r.json()
    assert d["currency"] == "INR"
    assert isinstance(d["items"], list) and len(d["items"]) >= 5
    assert d["total"] == sum(i["amount"] for i in d["items"])


# ---- Price ----
def test_price(s):
    r = s.post(f"{API}/customs/price",
               json={"productCost": 1000, "quantity": 100, "freight": 15000,
                     "insurance": 2000, "dutyPct": 5, "marginPct": 20})
    assert r.status_code == 200
    d = r.json()
    assert d["goodsValue"] == 100000
    assert d["cif"] == 117000
    assert d["duty"] == 5850.0
    assert d["landedCost"] == 122850.0
    assert d["sellingPrice"] == pytest.approx(147420.0, rel=1e-3)
    assert d["profit"] > 0


# ---- Freight routes ----
def test_freight_routes_known(s):
    r = s.get(f"{API}/customs/freight-routes", params={"to": "AE"})
    assert r.status_code == 200
    d = r.json()
    assert d["to"] == "AE"
    assert len(d["routes"]) >= 2
    modes = {x["mode"] for x in d["routes"]}
    assert "Sea" in modes and "Air" in modes


def test_freight_routes_default(s):
    r = s.get(f"{API}/customs/freight-routes", params={"to": "ZZ"})
    assert r.status_code == 200
    assert len(r.json()["routes"]) >= 2


# ---- Benefits ----
def test_benefits_export(s):
    r = s.get(f"{API}/customs/benefits", params={"direction": "Export"})
    assert r.status_code == 200
    d = r.json()
    schemes = [b["scheme"] for b in d["benefits"]]
    assert "RoDTEP" in schemes
    assert "Duty Drawback" in schemes
    assert "EPCG" in schemes
    for b in d["benefits"]:
        assert b["link"].startswith("http")


def test_benefits_import(s):
    r = s.get(f"{API}/customs/benefits", params={"direction": "Import"})
    assert r.status_code == 200
    d = r.json()
    schemes = [b["scheme"] for b in d["benefits"]]
    assert "EPCG" in schemes


# ---- CHA directory ----
def test_cha_directory_all(s):
    r = s.get(f"{API}/customs/cha-directory")
    assert r.status_code == 200
    d = r.json()
    assert d["total"] >= 5
    for c in d["chas"]:
        assert {"name", "port", "city", "services", "verified"}.issubset(c.keys())


def test_cha_directory_filter(s):
    r = s.get(f"{API}/customs/cha-directory", params={"port": "Mundra"})
    assert r.status_code == 200
    d = r.json()
    assert any("Mundra" in c["port"] for c in d["chas"])
