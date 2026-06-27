"""Phase 8 — LeadNation Brain LIVE AI activation tests.

Covers:
  * Live AI RAG via Emergent Universal LLM (openai gpt-5.4-mini)
  * 24h response caching (cached:true on 2nd identical call)
  * Insufficient info / no fabrication (unrelated question doesn't crash)
  * Rate limiting (20 req / 60s / session)
  * Brain Universal Search (5 layers, new types)
  * Conversation memory + user context
  * Admin Brain overview new fields: aiHealth, costMonitoring, tokenUsage, mostViewed*
  * Regression: pre-existing endpoints still ok.
"""
import os
import time
import uuid
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
def admin():
    s2 = requests.Session()
    s2.headers.update({"Content-Type": "application/json",
                       "X-Admin-Token": ADMIN_TOKEN})
    return s2


# ----------------- Provider status / engines -----------------
def test_brain_status_live(s):
    r = s.get(f"{API}/brain/status", timeout=20)
    assert r.status_code == 200
    body = r.json()
    prov = body["provider"]
    assert prov["live"] is True, f"expected live AI, got {prov}"
    assert prov["active"] == "openai", prov
    assert prov["model"] == "gpt-5.4-mini", prov
    assert prov["ragEnabled"] is True


def test_brain_engines_provider(s):
    r = s.get(f"{API}/brain/engines", timeout=20)
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 12
    assert body["provider"]["active"] == "openai"
    assert body["provider"]["model"] == "gpt-5.4-mini"
    assert body["provider"]["live"] is True


# ----------------- Live AI RAG -----------------
def test_brain_ask_live_uae_export(s):
    session_id = f"qa-{uuid.uuid4().hex[:8]}"
    r = s.post(f"{API}/brain/ask", json={
        "question": "Can I export agarbatti to UAE and which documents are required?",
        "session_id": session_id,
    }, timeout=90)
    assert r.status_code == 200, r.text[:400]
    body = r.json()
    assert body.get("live") is True, f"not live: {body}"
    assert body.get("provider") == "openai", body
    assert body.get("model") == "gpt-5.4-mini", body
    # cached True is acceptable (proves cache works for previously-asked Q)
    assert body.get("cached") in (True, False)
    ans = body.get("answer", "")
    assert ans and len(ans) > 40, ans
    eng = body.get("enginesUsed", [])
    for needed in ("product_intelligence", "country_context", "compliance", "tariff"):
        assert needed in eng, f"missing engine {needed}: {eng}"
    assert isinstance(body.get("sources"), list) and len(body["sources"]) >= 1


@pytest.mark.parametrize("q", [
    "Which HSN code should I use for Basmati rice?",
    "How do I get IEC registration?",
    "What certifications are required for pharmaceuticals?",
])
def test_brain_ask_live_others(s, q):
    r = s.post(f"{API}/brain/ask", json={
        "question": q, "session_id": f"qa-other-{uuid.uuid4().hex[:6]}"
    }, timeout=90)
    assert r.status_code == 200, r.text[:400]
    body = r.json()
    # may be live or degraded — but live=true should be the case in healthy state
    assert body.get("answer")
    assert isinstance(body.get("enginesUsed"), list) and len(body["enginesUsed"]) >= 1
    # If live, model/provider must match
    if body.get("live"):
        assert body.get("provider") == "openai"
        assert body.get("model") == "gpt-5.4-mini"


# ----------------- Caching -----------------
def test_brain_ask_cached_on_repeat(s):
    q = f"Test cache query about IEC registration {uuid.uuid4().hex[:6]}"
    sid = f"cache-{uuid.uuid4().hex[:8]}"
    # First call — should be fresh
    t0 = time.time()
    r1 = s.post(f"{API}/brain/ask",
                json={"question": q, "session_id": sid}, timeout=90)
    dt1 = time.time() - t0
    assert r1.status_code == 200
    b1 = r1.json()
    assert b1.get("cached") is False

    # Second call — same q, same provider+model -> cache hit (only if first wasn't degraded)
    t0 = time.time()
    r2 = s.post(f"{API}/brain/ask",
                json={"question": q, "session_id": sid}, timeout=90)
    dt2 = time.time() - t0
    assert r2.status_code == 200
    b2 = r2.json()
    if not b1.get("note"):  # not degraded
        assert b2.get("cached") is True, f"expected cache hit; got {b2.get('cached')}"
        # cached call should be noticeably faster
        assert dt2 < max(dt1, 2.0), f"cached call not faster: dt1={dt1:.2f} dt2={dt2:.2f}"


# ----------------- Insufficient info / no fabrication -----------------
def test_brain_ask_unrelated_no_crash(s):
    r = s.post(f"{API}/brain/ask", json={
        "question": "What is the weather today?",
        "session_id": f"weather-{uuid.uuid4().hex[:6]}",
    }, timeout=90)
    assert r.status_code == 200, r.text[:400]
    body = r.json()
    assert "answer" in body and isinstance(body["answer"], str) and body["answer"]


# ----------------- Rate limit -----------------
def test_brain_ask_rate_limit():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    sid = f"rl-{uuid.uuid4().hex[:8]}"
    codes = []
    for i in range(25):
        try:
            r = sess.post(f"{API}/brain/ask",
                          json={"question": f"ping {i}", "session_id": sid}, timeout=20)
            codes.append(r.status_code)
        except requests.RequestException:
            codes.append(0)
        if codes.count(429) >= 1 and i >= 20:
            break
    assert 429 in codes, f"expected 429 in {codes}"


# ----------------- Brain Universal Search -----------------
def test_brain_search_iec(s):
    r = s.get(f"{API}/brain/search", params={"q": "iec"}, timeout=25)
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body.get("searchLayers"), list)
    assert len(body["searchLayers"]) == 5, body["searchLayers"]
    results = body.get("results") or []
    assert isinstance(results, list) and len(results) > 0
    types = {r.get("type") or r.get("kind") for r in results}
    # Should contain at least one of the new types
    assert types & {"service", "compliance", "blog", "learning", "faq"}, types


def test_brain_search_basmati(s):
    r = s.get(f"{API}/brain/search", params={"q": "basmati"}, timeout=25)
    assert r.status_code == 200
    body = r.json()
    assert len(body["searchLayers"]) == 5
    results = body.get("results") or []
    types = {r.get("type") or r.get("kind") for r in results}
    assert types & {"product", "hsn", "corridor"}, f"expected product/hsn/corridor in {types}"


# ----------------- Memory -----------------
def test_brain_context_set_get(s):
    uid = "qa"
    r = s.post(f"{API}/brain/context",
               json={"user_id": uid, "preferredCountry": "UAE", "role": "exporter"},
               timeout=20)
    assert r.status_code == 200
    r2 = s.get(f"{API}/brain/context/{uid}", timeout=20)
    assert r2.status_code == 200
    ctx = r2.json()
    assert ctx.get("preferredCountry") == "UAE"
    assert ctx.get("role") == "exporter"


def test_brain_save(s):
    r = s.post(f"{API}/brain/save",
               json={"user_id": "qa", "field": "savedCountries", "item": "UAE"},
               timeout=20)
    assert r.status_code == 200


def test_brain_conversation_after_ask(s):
    sid = f"conv-{uuid.uuid4().hex[:8]}"
    s.post(f"{API}/brain/ask",
           json={"question": "How do I get IEC?", "session_id": sid}, timeout=90)
    r = s.get(f"{API}/brain/conversation/{sid}", timeout=20)
    assert r.status_code == 200
    body = r.json()
    msgs = body.get("messages") if isinstance(body, dict) else body
    assert msgs and len(msgs) >= 2


# ----------------- Admin Brain overview -----------------
def test_admin_brain_overview_requires_token(s):
    r = s.get(f"{API}/admin/brain/overview", timeout=20)
    assert r.status_code in (401, 403)


def test_admin_brain_overview_full(admin):
    r = admin.get(f"{API}/admin/brain/overview", timeout=30)
    assert r.status_code == 200, r.text[:400]
    body = r.json()
    # New Phase 8 sections
    for key in ("aiHealth", "costMonitoring", "tokenUsage",
                "engineHealth", "knowledgeBase",
                "mostAskedQuestions", "topCountries", "topProducts",
                "mostViewedCountries", "mostViewedProducts", "mostUsedServices",
                "failedQueries", "knowledgeGaps"):
        assert key in body, f"missing {key}"
    assert len(body["engineHealth"]) == 12
    ai = body["aiHealth"]
    assert ai["status"] == "live"
    assert ai["provider"] == "openai"
    assert ai["model"] == "gpt-5.4-mini"
    assert "cacheHitRate" in ai
    assert "degradedCalls" in ai
    cm = body["costMonitoring"]
    assert "totalCostUsd" in cm and isinstance(cm["totalCostUsd"], (int, float))
    assert isinstance(cm.get("byModel"), list)
    assert "totalTokens" in body["tokenUsage"]


# ----------------- Regression -----------------
@pytest.mark.parametrize("path", [
    "/countries", "/products-catalog", "/services",
])
def test_get_endpoint_ok(s, path):
    r = s.get(f"{API}{path}", timeout=20)
    assert r.status_code == 200


def test_global_search_rice(s):
    r = s.get(f"{API}/global-search", params={"q": "rice"}, timeout=20)
    assert r.status_code == 200


def test_duty_calc(s):
    r = s.post(f"{API}/duty-calc", json={
        "exportCountry": "India", "importCountry": "UAE",
        "category": "spices", "value": 1000,
    }, timeout=20)
    assert r.status_code == 200


def test_lead_create(s):
    r = s.post(f"{API}/leads", json={
        "name": "TEST_Phase8 Lead",
        "email": "TEST_phase8@example.com",
        "phone": "+910000000000",
        "interest": "phase8-test",
    }, timeout=20)
    assert r.status_code in (200, 201)


def test_admin_login(s):
    r = s.post(f"{API}/admin/login", json={"token": ADMIN_TOKEN}, timeout=20)
    assert r.status_code == 200


def test_admin_leads_with_token(admin):
    r = admin.get(f"{API}/admin/leads", timeout=20)
    assert r.status_code == 200
