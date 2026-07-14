"""Iteration 20 — Test /ports, /autofill and destinationPort persistence."""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/") or "https://trade-beyond-2.preview.emergentagent.com"
SESSION_ID = str(uuid.uuid4())
HEADERS = {"Content-Type": "application/json", "X-Trade-Session": SESSION_ID}


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update(HEADERS)
    return s


# ---------- /command-center/ports ----------
class TestPorts:
    def test_ports_us(self, api):
        r = api.get(f"{BASE_URL}/api/command-center/ports?country=842", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert data["country"] == "842"
        ports = data["ports"]
        assert isinstance(ports, list) and len(ports) > 0
        joined = " ".join(ports)
        assert "Los Angeles" in joined
        assert "Long Beach" in joined
        assert "New York" in joined

    def test_ports_india(self, api):
        r = api.get(f"{BASE_URL}/api/command-center/ports?country=356", timeout=30)
        assert r.status_code == 200
        ports = r.json()["ports"]
        assert any("Nhava Sheva" in p for p in ports)
        assert any("Mundra" in p for p in ports)

    def test_ports_generic_fallback(self, api):
        r = api.get(f"{BASE_URL}/api/command-center/ports?country=999", timeout=30)
        assert r.status_code == 200
        ports = r.json()["ports"]
        assert isinstance(ports, list) and len(ports) >= 1
        assert any("Sea Port" in p or "Airport" in p for p in ports)


# ---------- /command-center/autofill (LLM) ----------
class TestAutofill:
    def test_autofill_wheat_ind_to_usa(self, api):
        payload = {
            "hs": "100630", "exporter": "356", "importer": "842",
            "quantity": 1000, "unit": "mt", "incoterm": "CIF",
            "transactionCurrency": "USD",
        }
        r = api.post(f"{BASE_URL}/api/command-center/autofill", json=payload, timeout=120)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("ok") is True, data
        costs = data.get("costs", {})
        for k in ["exw", "packing", "inland", "thc", "customsDocs", "freight", "insurance"]:
            assert k in costs, f"missing key {k}"
            assert isinstance(costs[k], (int, float)), f"{k} not numeric: {costs[k]}"
        assert costs["exw"] > 0, f"exw must be > 0 (Brain price estimate): {costs}"
        assert data.get("source") == "brain"
        assert data.get("note")


# ---------- /projects destinationPort persistence ----------
class TestProjectDestinationPort:
    def test_create_and_patch_destination_port(self, api):
        # Create
        create = api.post(f"{BASE_URL}/api/projects",
                          json={"title": "TEST_iter20_destport", "hs": "100630",
                                "exporter": "356", "importer": "842"}, timeout=30)
        assert create.status_code == 200, create.text
        pid = create.json()["id"]

        # PUT patch destinationPort
        r = api.put(f"{BASE_URL}/api/projects/{pid}",
                    json={"patch": {"destinationPort": "Los Angeles"}}, timeout=30)
        assert r.status_code == 200, r.text
        proj = r.json()
        assert proj.get("destinationPort") == "Los Angeles"

        # GET to verify persistence
        g = api.get(f"{BASE_URL}/api/projects/{pid}", timeout=30)
        assert g.status_code == 200
        assert g.json().get("destinationPort") == "Los Angeles"

        # Update destinationPort
        r2 = api.put(f"{BASE_URL}/api/projects/{pid}",
                     json={"patch": {"destinationPort": "Long Beach"}}, timeout=30)
        assert r2.status_code == 200
        assert r2.json().get("destinationPort") == "Long Beach"

        # Cleanup
        api.delete(f"{BASE_URL}/api/projects/{pid}", timeout=30)
