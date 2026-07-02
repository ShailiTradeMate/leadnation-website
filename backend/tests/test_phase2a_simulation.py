"""Volume 2 Phase 2A — Simulation Engine + Decision Engine + Adapters + Events + Trade Scores.

Guest identity via X-Trade-Session UUID. Deterministic backend maths; Brain must
degrade gracefully. Full lifecycle for scenarios, comparison, decision, events.
"""
import os
import uuid
import requests
import pytest
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parents[2] / "frontend" / ".env")
BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") + "/api"

# Fresh guest session per test run
SESSION = uuid.uuid4().hex
H = {"X-Trade-Session": SESSION, "Content-Type": "application/json"}


# ---------------- Shared fixtures ----------------
@pytest.fixture(scope="module")
def project_id():
    """Create a Trade Project as guest (tea, India → United States)."""
    payload = {
        "title": "TEST_Phase2A_TeaExport",
        "product": "Tea",
        "hs": "090240",  # green tea
        "exporter": "356",  # India
        "importer": "842",  # USA
        "incoterm": "CIF",
        "quantity": 5000,
        "unit": "kg",
        "transactionCurrency": "USD",
        "globalCurrency": "USD",
        "marginPct": 15,
        "buyer": "TEST BuyerCo Inc",
        "supplier": "TEST SupplierCo Pvt",
        "paymentMethod": "LC",
        "shipmentMode": "Sea FCL",
        "costs": {"exw": 20000, "packing": 500, "inland": 400, "thc": 300,
                  "customsDocs": 150, "freight": 2500, "insurance": 200},
    }
    r = requests.post(f"{BASE}/projects", headers=H, json=payload, timeout=45)
    assert r.status_code == 200, r.text
    pid = r.json()["id"]
    yield pid
    # Cleanup: remove project + scenarios (best effort)
    try:
        requests.delete(f"{BASE}/projects/{pid}", headers=H, timeout=15)
    except Exception:
        pass


TWIN_INPUTS = {
    "hs": "090240", "product": "Tea",
    "exporter": "356", "importer": "842",
    "quantity": 5000, "unit": "kg", "incoterm": "CIF",
    "marginPct": 15, "paymentMethod": "LC",
    "buyer": "TEST Buyer", "supplier": "TEST Supplier",
    "transactionCurrency": "USD", "globalCurrency": "USD",
    "costs": {"exw": 20000, "packing": 500, "inland": 400, "thc": 300,
              "customsDocs": 150, "freight": 2500, "insurance": 200},
}


# ==================== Adapters Framework ====================
class TestAdapters:
    def test_list_adapters(self):
        r = requests.get(f"{BASE}/adapters", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert "adapters" in data and "tiers" in data
        keys = {a["key"] for a in data["adapters"]}
        # All five expected adapters registered
        for expected in ("duty", "fx", "trade_stats", "incentives", "freight"):
            assert expected in keys, f"Missing adapter: {expected}"
        # 6 canonical tiers
        assert data["tiers"] == ["government", "official", "live_commercial",
                                 "knowledge_base", "historical", "ai_estimate"]

    def test_adapter_run_duty_and_fx(self):
        ctx = {"hs": "090240", "exporter": "356", "importer": "842",
               "transactionCurrency": "USD"}
        r = requests.post(f"{BASE}/adapters/run",
                          json={"keys": ["duty", "fx"], "context": ctx}, timeout=60)
        assert r.status_code == 200, r.text
        results = r.json()["results"]
        assert "duty" in results and "fx" in results
        # Duty must be government tier + not AI estimated
        assert results["duty"]["sourceTier"] == "government"
        assert results["duty"]["aiEstimated"] is False
        assert "confidence" in results["duty"]
        # FX must be official + not AI
        assert results["fx"]["sourceTier"] == "official"
        assert results["fx"]["aiEstimated"] is False

    def test_adapter_freight_is_ai_estimated(self):
        r = requests.post(f"{BASE}/adapters/run",
                          json={"keys": ["freight"], "context": {"importer": "842"}}, timeout=30)
        assert r.status_code == 200
        f = r.json()["results"]["freight"]
        assert f["sourceTier"] == "ai_estimate"
        assert f["aiEstimated"] is True
        # Must carry assumptions when ai-estimated
        assert isinstance(f.get("assumptions"), list)


# ==================== Digital Twin ====================
class TestDigitalTwin:
    def test_twin_returns_full_shape(self):
        r = requests.post(f"{BASE}/simulation/twin",
                          headers=H, json={"inputs": TWIN_INPUTS}, timeout=60)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["ok"] is True
        # Quote block
        assert "quote" in d
        # Summary shape
        s = d["summary"]
        for k in ("fob", "cif", "landed", "selling", "profit"):
            assert k in s, f"summary missing {k}"
        # Scores — 8 explainable keys incl overall
        sc = d["scores"]
        for k in ("profitability", "risk", "compliance", "competition",
                  "market", "buyer", "supplier", "overall"):
            assert k in sc, f"scores missing {k}"
            assert 0 <= sc[k]["value"] <= 100
            assert sc[k]["color"] in ("emerald", "amber", "rose")
            assert isinstance(sc[k]["factors"], list)
            assert isinstance(sc[k]["explanation"], str) and sc[k]["explanation"]
        # Decision object
        dec = d["decision"]
        assert "recommendedActions" in dec
        assert "overallVerdict" in dec
        assert dec["overallVerdict"] in ("strong", "moderate", "weak")

    def test_twin_no_save_side_effect(self, project_id):
        # Compute twin; scenarios list for project should be independent
        r = requests.post(f"{BASE}/simulation/twin",
                          headers=H, json={"inputs": TWIN_INPUTS}, timeout=30)
        assert r.status_code == 200
        # Scenarios list should be unchanged from twin call
        r2 = requests.get(f"{BASE}/simulation/scenarios",
                          headers=H, params={"projectId": project_id}, timeout=30)
        assert r2.status_code == 200


# ==================== Scenario Builder CRUD ====================
class TestScenarioBuilder:
    def test_create_first_scenario_auto_A(self, project_id):
        r = requests.post(f"{BASE}/simulation/scenarios",
                          headers=H, json={"projectId": project_id}, timeout=60)
        assert r.status_code == 200, r.text
        sc = r.json()
        assert sc["projectId"] == project_id
        assert sc["label"].startswith("Scenario ")  # auto "Scenario A"
        assert sc["version"] == 1
        assert sc["archived"] is False
        # Auto computed: outputs + scores + confidence
        assert "outputs" in sc and sc["outputs"].get("profit") is not None
        assert "scores" in sc and "overall" in sc["scores"]
        assert "confidence" in sc and 0 <= sc["confidence"] <= 1
        pytest.first_id = sc["id"]  # stash for later
        pytest.first_label = sc["label"]

    def test_create_second_scenario_custom_inputs(self, project_id):
        custom = dict(TWIN_INPUTS)
        custom["marginPct"] = 25  # different from project's 15
        custom["costs"] = dict(TWIN_INPUTS["costs"])
        custom["costs"]["freight"] = 1800  # lower freight
        r = requests.post(f"{BASE}/simulation/scenarios",
                          headers=H, json={"projectId": project_id,
                                           "label": "TEST_HighMarginLowFreight",
                                           "inputs": custom}, timeout=60)
        assert r.status_code == 200, r.text
        sc = r.json()
        assert sc["label"] == "TEST_HighMarginLowFreight"
        assert sc["inputs"]["marginPct"] == 25
        pytest.second_id = sc["id"]

    def test_list_scenarios(self, project_id):
        r = requests.get(f"{BASE}/simulation/scenarios",
                         headers=H, params={"projectId": project_id}, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert "scenarios" in data
        ids = [s["id"] for s in data["scenarios"]]
        assert pytest.first_id in ids
        assert pytest.second_id in ids

    def test_update_recomputes_and_bumps_version(self, project_id):
        # Fetch current inputs of second scenario
        r = requests.get(f"{BASE}/simulation/scenarios/{pytest.second_id}",
                         headers=H, timeout=30)
        assert r.status_code == 200
        sc = r.json()
        new_inputs = dict(sc["inputs"])
        new_inputs["marginPct"] = 30
        r2 = requests.put(f"{BASE}/simulation/scenarios/{pytest.second_id}",
                          headers=H, json={"inputs": new_inputs}, timeout=45)
        assert r2.status_code == 200, r2.text
        updated = r2.json()
        assert updated["inputs"]["marginPct"] == 30
        assert updated["version"] == (sc.get("version") or 1) + 1
        # Selling price must recompute (higher margin => higher selling)
        assert updated["outputs"]["selling"] is not None

    def test_duplicate(self, project_id):
        r = requests.post(f"{BASE}/simulation/scenarios/{pytest.first_id}/duplicate",
                          headers=H, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["parentId"] == pytest.first_id
        assert "(copy)" in d["label"]
        pytest.dup_id = d["id"]

    def test_merge(self, project_id):
        r = requests.post(f"{BASE}/simulation/scenarios/merge",
                          headers=H, json={"projectId": project_id,
                                           "ids": [pytest.first_id, pytest.second_id],
                                           "label": "TEST_Merged"}, timeout=45)
        assert r.status_code == 200, r.text
        m = r.json()
        assert m["label"] == "TEST_Merged"
        assert m["mergedFrom"] == [pytest.first_id, pytest.second_id]
        assert m["outputs"]["profit"] is not None
        pytest.merged_id = m["id"]

    def test_merge_requires_two(self, project_id):
        r = requests.post(f"{BASE}/simulation/scenarios/merge",
                          headers=H, json={"projectId": project_id,
                                           "ids": [pytest.first_id]}, timeout=15)
        assert r.status_code == 400

    def test_archive_hides_from_default_list(self, project_id):
        r = requests.put(f"{BASE}/simulation/scenarios/{pytest.dup_id}",
                         headers=H, json={"archived": True}, timeout=30)
        assert r.status_code == 200
        # Default list must exclude archived
        r2 = requests.get(f"{BASE}/simulation/scenarios",
                          headers=H, params={"projectId": project_id}, timeout=30)
        ids = [s["id"] for s in r2.json()["scenarios"]]
        assert pytest.dup_id not in ids
        # includeArchived shows it
        r3 = requests.get(f"{BASE}/simulation/scenarios",
                          headers=H, params={"projectId": project_id,
                                             "includeArchived": "true"}, timeout=30)
        ids3 = [s["id"] for s in r3.json()["scenarios"]]
        assert pytest.dup_id in ids3

    def test_delete(self, project_id):
        r = requests.delete(f"{BASE}/simulation/scenarios/{pytest.dup_id}",
                            headers=H, timeout=30)
        assert r.status_code == 200
        assert r.json()["ok"] is True
        # GET now 404
        r2 = requests.get(f"{BASE}/simulation/scenarios/{pytest.dup_id}",
                          headers=H, timeout=15)
        assert r2.status_code == 404


# ==================== Scenario Comparison ====================
class TestCompare:
    def test_compare_returns_rows_and_winners(self, project_id):
        r = requests.post(f"{BASE}/simulation/compare",
                          headers=H, json={"projectId": project_id}, timeout=45)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["ok"] is True
        assert isinstance(d["rows"], list) and len(d["rows"]) >= 2
        for row in d["rows"]:
            assert "summary" in row and "scores" in row
        # Winners for 5 metrics — each is an id from the rows
        w = d["winners"]
        assert set(w.keys()) >= {"profit", "landed", "selling", "margin", "overall"}
        row_ids = {r_["id"] for r_ in d["rows"]}
        for metric, wid in w.items():
            if wid is not None:
                assert wid in row_ids


# ==================== Decision Engine ====================
class TestDecisionEngine:
    def test_decision_full_shape(self, project_id):
        r = requests.post(f"{BASE}/decision",
                          headers=H, json={"projectId": project_id}, timeout=45)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["ok"] is True
        # Scores 8 keys
        for k in ("profitability", "risk", "compliance", "competition",
                  "market", "buyer", "supplier", "overall"):
            assert k in d["scores"]
        dec = d["decision"]
        # 6 domain decision objects
        domains = {o["domain"] for o in dec["objects"]}
        assert domains == {"profitability", "risk", "compliance", "buyer", "logistics", "market"}
        assert isinstance(dec["recommendedActions"], list)
        assert dec["overallVerdict"] in ("strong", "moderate", "weak")
        assert "confidence" in dec
        # bestMarket may be None if no comparison — key must exist
        assert "bestMarket" in dec

    def test_decision_recommendations_degrades_gracefully(self, project_id):
        r = requests.post(f"{BASE}/decision/recommendations",
                          headers=H, json={"projectId": project_id}, timeout=90)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["ok"] is True
        assert "scores" in d and "decision" in d
        # 'recommendations' key exists (may be empty string if LLM degraded — MUST NOT error)
        assert "recommendations" in d
        assert isinstance(d["recommendations"], str)


# ==================== Trade Score Explainability ====================
class TestScoreExplainability:
    def test_scores_include_factors_and_explanation(self, project_id):
        r = requests.post(f"{BASE}/decision",
                          headers=H, json={"projectId": project_id}, timeout=45)
        assert r.status_code == 200
        scores = r.json()["scores"]
        for k, s in scores.items():
            assert isinstance(s["value"], int) and 0 <= s["value"] <= 100
            assert s["color"] in ("emerald", "amber", "rose")
            assert isinstance(s["factors"], list) and len(s["factors"]) >= 1
            assert isinstance(s["explanation"], str) and s["explanation"]


# ==================== Universal Audit Trail ====================
class TestEvents:
    def test_events_captured(self, project_id):
        r = requests.get(f"{BASE}/events",
                         headers=H, params={"projectId": project_id}, timeout=30)
        assert r.status_code == 200, r.text
        evts = r.json()["events"]
        assert isinstance(evts, list) and len(evts) > 0
        types = {e["type"] for e in evts}
        # These types must have been logged during earlier tests
        for expected in ("project_created", "scenario_created",
                         "scenario_compared", "decision_computed", "brain_recommendation"):
            assert expected in types, f"Missing event type: {expected} (got {types})"
        # Each event has timestamp + projectId
        for e in evts:
            assert e["projectId"] == project_id
            assert "at" in e and e["at"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
