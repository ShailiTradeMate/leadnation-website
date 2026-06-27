"""Phase 7 — LeadNation Brain + refactor regression tests.

Covers:
  • Regression: all pre-existing endpoints still respond after router split.
  • Brain public API: /api/brain/ask, /search, /engines, /status,
    /context, /conversation, /save, /knowledge.
  • Brain admin API (X-Admin-Token): /api/admin/brain/overview, /knowledge/reseed.
"""
import os
import pytest
import requests
from pathlib import Path

def _load_backend_url():
    url = os.environ.get("REACT_APP_BACKEND_URL", "").strip()
    if not url:
        env_path = Path("/app/frontend/.env")
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("REACT_APP_BACKEND_URL="):
                    url = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    return url.rstrip("/")

BASE_URL = _load_backend_url()
assert BASE_URL, "REACT_APP_BACKEND_URL not set"
API = f"{BASE_URL}/api"
ADMIN_TOKEN = "leadnation-admin-2026"


@pytest.fixture(scope="session")
def s():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


@pytest.fixture(scope="session")
def admin(s):
    s2 = requests.Session()
    s2.headers.update({"Content-Type": "application/json",
                       "X-Admin-Token": ADMIN_TOKEN})
    return s2


# ---------------- Regression: pre-existing GET endpoints ----------------
@pytest.mark.parametrize("path", [
    "/countries", "/products", "/products-catalog", "/corridors", "/industries",
    "/blog", "/services", "/trade-news", "/expos", "/intelligence", "/academy",
    "/country-profiles", "/hsn", "/directory/exporters",
])
def test_get_endpoint_ok(s, path):
    r = s.get(f"{API}{path}", timeout=20)
    assert r.status_code == 200, f"{path} -> {r.status_code} {r.text[:200]}"
    data = r.json()
    assert data is not None
    # Must be either a list or a dict containing a list (e.g. {items:[...]})
    if isinstance(data, dict):
        # plausible — endpoint may wrap
        assert len(data) > 0
    else:
        assert isinstance(data, list)


def test_global_search_rice(s):
    r = s.get(f"{API}/global-search", params={"q": "rice"}, timeout=20)
    assert r.status_code == 200
    body = r.json()
    assert "results" in body or isinstance(body, list)


# ---------------- Regression: POST tools ----------------
def test_duty_calc(s):
    r = s.post(f"{API}/duty-calc", json={
        "exportCountry": "India",
        "importCountry": "UAE",
        "category": "spices",
        "value": 1000,
    }, timeout=20)
    assert r.status_code == 200, r.text[:300]
    body = r.json()
    assert isinstance(body, dict)


def test_hsn_finder(s):
    r = s.post(f"{API}/hsn-finder", json={"productName": "basmati rice"}, timeout=20)
    assert r.status_code == 200, r.text[:200]


def test_landed_cost(s):
    r = s.post(f"{API}/landed-cost", json={
        "productCost": 1000, "freight": 100, "insurance": 20,
        "duty": 50, "localCharges": 30,
    }, timeout=20)
    assert r.status_code == 200


def test_export_readiness(s):
    r = s.post(f"{API}/export-readiness", json={
        "hasIEC": True, "hasGST": True, "yearsInBusiness": 3,
        "hasProduct": True, "targetMarkets": ["UAE"],
    }, timeout=20)
    assert r.status_code == 200


def test_lead_create(s):
    r = s.post(f"{API}/leads", json={
        "name": "TEST_Phase7 Lead",
        "email": "TEST_phase7@example.com",
        "phone": "+910000000000",
        "interest": "phase7-test",
    }, timeout=20)
    assert r.status_code in (200, 201), r.text[:200]


def test_ai_ask_legacy(s):
    r = s.post(f"{API}/ai-ask", json={"question": "Hello"}, timeout=20)
    assert r.status_code == 200


# ---------------- Admin regression ----------------
def test_admin_login(s):
    r = s.post(f"{API}/admin/login", json={"token": ADMIN_TOKEN}, timeout=20)
    assert r.status_code == 200, r.text[:200]


def test_admin_leads_requires_token(s):
    r = s.get(f"{API}/admin/leads", timeout=20)
    assert r.status_code in (401, 403)


def test_admin_leads_with_token(admin):
    r = admin.get(f"{API}/admin/leads", timeout=20)
    assert r.status_code == 200


def test_admin_collections(admin):
    r = admin.get(f"{API}/admin/collections", timeout=20)
    assert r.status_code == 200


# ---------------- Brain: engines / status / search ----------------
def test_brain_engines(s):
    r = s.get(f"{API}/brain/engines", timeout=20)
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 12, body
    assert isinstance(body["engines"], list) and len(body["engines"]) == 12
    assert body["provider"]["active"] in ("mock", "openai")


def test_brain_status(s):
    r = s.get(f"{API}/brain/status", timeout=20)
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    kb = body["knowledgeBase"]
    assert kb.get("total", 0) >= 40, f"KB total low: {kb}"
    assert body["engines"] == 12


def test_brain_search(s):
    r = s.get(f"{API}/brain/search", params={"q": "basmati"}, timeout=25)
    assert r.status_code == 200
    body = r.json()
    assert "searchLayers" in body
    layers = body["searchLayers"]
    assert isinstance(layers, list) and len(layers) == 5
    names = [l.get("name", "") for l in layers]
    joined = " ".join(names).lower()
    assert "knowledge" in joined
    assert "database" in joined or "data" in joined
    assert "engines" in joined or "trade" in joined


# ---------------- Brain: ask ----------------
def test_brain_ask_agarbatti_uae(s):
    r = s.post(f"{API}/brain/ask", json={
        "question": "Can I export Agarbatti to UAE?",
        "session_id": "t1",
    }, timeout=30)
    assert r.status_code == 200, r.text[:400]
    body = r.json()
    eng = body.get("enginesUsed", [])
    assert "product_intelligence" in eng, eng
    assert "country_context" in eng, eng
    assert "compliance" in eng, eng
    assert "tariff" in eng, eng
    ents = body["entities"]
    assert any("uae" in c.lower() or "united arab" in c.lower() for c in ents["countries"]), ents
    assert any("agarbatti" in p.lower() for p in ents["products"]), ents
    assert isinstance(body["sources"], list) and len(body["sources"]) >= 1
    assert body.get("answer") and len(body["answer"]) > 20


@pytest.mark.parametrize("q", [
    "Which HSN code for Basmati rice?",
    "How do I get IEC registration?",
    "What is the duty on textiles to Australia?",
])
def test_brain_ask_other(s, q):
    r = s.post(f"{API}/brain/ask", json={"question": q, "session_id": "t1"}, timeout=30)
    assert r.status_code == 200
    body = r.json()
    assert body.get("answer")
    assert isinstance(body.get("enginesUsed"), list) and len(body["enginesUsed"]) >= 1


# ---------------- Brain: memory ----------------
def test_brain_context_set_get(s):
    r = s.post(f"{API}/brain/context", json={
        "user_id": "tu", "preferredCountry": "UAE", "role": "exporter",
    }, timeout=20)
    assert r.status_code == 200
    r2 = s.get(f"{API}/brain/context/tu", timeout=20)
    assert r2.status_code == 200
    ctx = r2.json()
    assert ctx.get("preferredCountry") == "UAE"
    assert ctx.get("role") == "exporter"


def test_brain_conversation_after_ask(s):
    r = s.get(f"{API}/brain/conversation/t1", timeout=20)
    assert r.status_code == 200
    body = r.json()
    # accept either {messages:[...]} or list
    msgs = body.get("messages") if isinstance(body, dict) else body
    assert msgs and len(msgs) >= 2


def test_brain_save(s):
    r = s.post(f"{API}/brain/save", json={
        "user_id": "tu", "field": "savedCountries", "item": "UAE",
    }, timeout=20)
    assert r.status_code == 200


# ---------------- Admin Brain ----------------
def test_admin_brain_requires_token(s):
    r = s.get(f"{API}/admin/brain/overview", timeout=20)
    assert r.status_code in (401, 403)


def test_admin_brain_overview(admin):
    r = admin.get(f"{API}/admin/brain/overview", timeout=30)
    assert r.status_code == 200, r.text[:400]
    body = r.json()
    for key in ["engineHealth", "knowledgeBase", "aiUsage",
                "mostAskedQuestions", "topCountries", "topProducts",
                "failedQueries", "knowledgeGaps"]:
        assert key in body, f"missing {key}"
    assert len(body["engineHealth"]) == 12


def test_admin_brain_reseed(admin):
    r = admin.post(f"{API}/admin/brain/knowledge/reseed", timeout=60)
    assert r.status_code == 200, r.text[:300]
    body = r.json()
    # reseed should return some stats / count
    assert body
