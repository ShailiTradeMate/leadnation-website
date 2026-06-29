"""Phase B Duty & Benefits engine tests."""
import os
import time
import pytest
import requests

BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") if os.environ.get("REACT_APP_BACKEND_URL") else "https://global-trade-hub-176.preview.emergentagent.com"


@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(f"{BASE}/api/auth/admin/login", json={"username": "00001", "password": "Shiv@12345"}, timeout=20)
    assert r.status_code == 200, r.text
    return r.json().get("token")


# --- countries ---
def test_countries_50_plus():
    r = requests.get(f"{BASE}/api/duty/countries", timeout=20)
    assert r.status_code == 200
    cs = r.json()["countries"]
    assert len(cs) >= 50
    codes = {c["code"]: c["name"] for c in cs}
    assert codes.get("356") == "India"
    assert codes.get("842") == "United States"
    assert codes.get("276") == "Germany"


# --- meta ---
def test_meta_has_timestamps():
    r = requests.get(f"{BASE}/api/duty/meta", timeout=20)
    assert r.status_code == 200
    d = r.json()
    assert "lastRefresh" in d and "nextRefresh" in d
    assert isinstance(d.get("sources"), list) and len(d["sources"]) >= 1


# --- lookup: USA -> India coffee (HS 090111) ---
def test_lookup_coffee_usa_to_india():
    r = requests.get(f"{BASE}/api/duty/lookup", params={"hs": "090111", "origin": "842", "destination": "356"}, timeout=60)
    assert r.status_code == 200
    d = r.json()
    assert d["ok"] is True
    assert d["hsCode"] == "090111"
    imp = d.get("importDuty")
    assert imp is not None, f"expected importDuty, got {d}"
    assert imp["source"].startswith("World Bank WITS")
    assert imp.get("rate") is not None
    ib = d.get("indiaBreakdown")
    assert ib is not None
    # SWS must be 10% of BCD
    assert ib["swsRate"] == 10.0
    assert round(ib["socialWelfareSurcharge"], 2) == round(ib["basicCustomsDuty"] * 0.10, 2)
    assert "igst" in ib


# --- lookup: USA -> Germany (HS 870323) ---
def test_lookup_germany_car():
    r = requests.get(f"{BASE}/api/duty/lookup", params={"hs": "870323", "origin": "842", "destination": "276"}, timeout=60)
    assert r.status_code == 200
    d = r.json()
    assert d["ok"] is True
    imp = d.get("importDuty")
    assert imp is not None, f"expected MFN for DE 870323, got {d}"
    assert imp["rate"] is not None
    # India breakdown should be None since destination is Germany
    assert d.get("indiaBreakdown") is None


# --- RoDTEP: India -> Germany coffee ---
def test_lookup_rodtep_india_to_germany():
    r = requests.get(f"{BASE}/api/duty/lookup", params={"hs": "090111", "origin": "356", "destination": "276"}, timeout=60)
    assert r.status_code == 200
    d = r.json()
    assert d["ok"] is True
    eb = d.get("exportBenefit")
    assert eb is not None, f"expected RoDTEP exportBenefit, got {d}"
    assert eb["scheme"] == "RoDTEP"
    assert eb.get("rate") is not None
    assert "DGFT" in eb["source"]


# --- Graceful no-data ---
def test_lookup_no_data_graceful():
    # Obscure HS likely missing for an exotic destination pair
    r = requests.get(f"{BASE}/api/duty/lookup", params={"hs": "999999", "origin": "032", "destination": "204"}, timeout=60)
    assert r.status_code == 200
    d = r.json()
    assert d["ok"] is True
    # Either importDuty null and a note, or notes list populated
    if d.get("importDuty") is None:
        assert isinstance(d.get("notes"), list)


# --- Admin refresh requires auth ---
def test_refresh_no_auth_401():
    r = requests.post(f"{BASE}/api/duty/refresh", timeout=20)
    assert r.status_code == 401


def test_refresh_with_admin_jwt(admin_token):
    before = requests.get(f"{BASE}/api/duty/meta", timeout=20).json()["lastRefresh"]
    time.sleep(1.1)
    r = requests.post(f"{BASE}/api/duty/refresh", headers={"Authorization": f"Bearer {admin_token}"}, timeout=60)
    assert r.status_code == 200, r.text
    after = r.json()["lastRefresh"]
    assert after >= before


# --- Brain integration ---
def test_brain_duty_benefits_engine():
    payload = {"question": "What is the import duty on coffee HS 090111 into India and the RoDTEP benefit for exporting from India?", "session_id": "qa-duty2"}
    r = requests.post(f"{BASE}/api/brain/ask", json=payload, timeout=90)
    assert r.status_code == 200, r.text
    d = r.json()
    engines = d.get("enginesUsed") or d.get("engines_used") or []
    assert "duty_benefits" in engines, f"engines: {engines}"
    eo = d.get("engineOutputs") or d.get("engine_outputs") or {}
    assert "duty_benefits" in eo
