"""Iteration 15 — Brain global/non-repetitive + Compile Data + CBIC FX tests."""
import os
import re
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://trade-brain-ai.preview.emergentagent.com").rstrip("/")
TIMEOUT_LLM = 60
TIMEOUT_COMPILE = 90


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ---------- BRAIN: 3 distinct global questions ----------
QUESTIONS = [
    {
        "q": "What documents do I need to export olive oil from Spain to Brazil?",
        "expect_kw": ["spain", "brazil", "olive"],
        "engine_hint": "compliance",
    },
    {
        "q": "Who are the top importers of cocoa beans worldwide?",
        "expect_kw": ["cocoa"],
        "engine_hint": "trade_statistics",
    },
    {
        "q": "How do I ship electronics from China to Nigeria and what duty applies?",
        "expect_kw": ["china", "nigeria"],
        "engine_hint": "duty_benefits",
    },
]

INDIA_REPETITIVE_PATTERNS = [
    "india exports crossed $450",
    "mundra port",
    "indian export sector",
]


@pytest.fixture(scope="module")
def brain_answers(session):
    answers = []
    for item in QUESTIONS:
        payload = {"question": item["q"], "session_id": f"test-{uuid.uuid4()}"}
        r = session.post(f"{BASE_URL}/api/brain/ask", json=payload, timeout=TIMEOUT_LLM)
        assert r.status_code == 200, f"Brain ask failed for '{item['q']}': {r.status_code} {r.text[:200]}"
        data = r.json()
        answers.append({"req": item, "resp": data})
    return answers


def test_brain_three_questions_returned(brain_answers):
    assert len(brain_answers) == 3
    for a in brain_answers:
        assert a["resp"].get("answer"), f"Empty answer for {a['req']['q']}"
        assert len(a["resp"]["answer"]) > 100, f"Suspiciously short answer for {a['req']['q']}"


def test_brain_answers_are_distinct(brain_answers):
    """Core bug fix: answers must differ across the 3 distinct queries."""
    answers = [a["resp"]["answer"].strip() for a in brain_answers]
    # No two answers should be identical
    assert answers[0] != answers[1], "Q1 and Q2 returned IDENTICAL answers (repetitive bug)"
    assert answers[1] != answers[2], "Q2 and Q3 returned IDENTICAL answers (repetitive bug)"
    assert answers[0] != answers[2], "Q1 and Q3 returned IDENTICAL answers (repetitive bug)"

    # Strong overlap check: tokens overlap must not be >85%
    def tokset(t):
        return set(re.findall(r"[a-zA-Z]{4,}", t.lower()))
    a0, a1, a2 = map(tokset, answers)
    for i, (x, y) in enumerate([(a0, a1), (a1, a2), (a0, a2)]):
        if not x or not y:
            continue
        overlap = len(x & y) / max(len(x | y), 1)
        assert overlap < 0.9, f"Answers {i} too similar (overlap={overlap:.2f}) — likely repetitive"


def test_brain_answers_are_tailored_to_question(brain_answers):
    for a in brain_answers:
        ans = a["resp"]["answer"].lower()
        kws = a["req"]["expect_kw"]
        # At least one of the expected country/product keywords must appear
        hits = sum(1 for k in kws if k in ans)
        assert hits >= 1, f"Answer for '{a['req']['q']}' does not reference any of {kws}: {ans[:300]}"


def test_brain_not_india_centric_boilerplate(brain_answers):
    """The Spain→Brazil and China→Nigeria queries must not mention India-centric template lines."""
    for a in brain_answers:
        if "india" in a["req"]["q"].lower():
            continue
        ans = a["resp"]["answer"].lower()
        for pat in INDIA_REPETITIVE_PATTERNS:
            assert pat not in ans, f"India-centric boilerplate '{pat}' found in answer to '{a['req']['q']}'"


def test_brain_engine_selection_varies(brain_answers):
    """enginesUsed should be tailored to the question type, not the same list every time."""
    engines_per_q = []
    for a in brain_answers:
        eu = a["resp"].get("enginesUsed") or a["resp"].get("engines_used") or []
        if not eu:
            # try alternate shape
            eo = a["resp"].get("engineOutputs") or a["resp"].get("engine_outputs") or {}
            eu = list(eo.keys()) if isinstance(eo, dict) else []
        engines_per_q.append(set(eu))
        print(f"Q='{a['req']['q'][:40]}' enginesUsed={eu}")
    # At least 2 distinct engine sets across the 3 queries
    uniq = {frozenset(s) for s in engines_per_q}
    assert len(uniq) >= 2, f"All 3 questions used the SAME engines: {engines_per_q}"


# ---------- Compile Data ----------
def test_compile_report_coffee_india_to_germany_eur(session):
    r = session.get(
        f"{BASE_URL}/api/compile/report",
        params={"product": "coffee", "exporter": "356", "importer": "276", "currency": "EUR"},
        timeout=TIMEOUT_COMPILE,
    )
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    assert data.get("ok") is True, f"compile ok=false: {data}"
    assert data.get("hsCode") and len(data["hsCode"]) == 6, f"missing hsCode: {data.get('hsCode')}"
    assert data.get("narrative"), "narrative (Brain executive brief) is empty"
    assert len(data["narrative"]) > 80, f"narrative too short: {data['narrative'][:120]}"
    assert data.get("tradeStats"), "tradeStats missing"
    assert data.get("duty"), "duty missing"
    assert isinstance(data.get("tariffComparison"), list) and len(data["tariffComparison"]) >= 1
    for row in data["tariffComparison"]:
        assert "country" in row and "rate" in row
    assert data.get("fx") and isinstance(data["fx"].get("rate"), (int, float))
    assert data.get("price") and data["price"].get("landedUSD")


def test_compile_report_rice_india_to_uae(session):
    r = session.get(
        f"{BASE_URL}/api/compile/report",
        params={"product": "rice", "exporter": "356", "importer": "784", "currency": "AED"},
        timeout=TIMEOUT_COMPILE,
    )
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    assert data.get("ok") is True
    assert data.get("hsCode")
    assert data.get("importer", {}).get("code") == "784"


def test_compile_report_invalid(session):
    r = session.get(f"{BASE_URL}/api/compile/report", params={}, timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is False
    assert "error" in data


# ---------- CBIC FX (Phase C) ----------
def test_cbic_fx(session):
    r = session.get(f"{BASE_URL}/api/customs/cbic-fx", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    assert data.get("notifiedDate")
    rates = data.get("rates") or {}
    assert "USD" in rates, f"USD missing from CBIC rates: {list(rates.keys())}"
    usd = rates["USD"]
    assert isinstance(usd.get("import"), (int, float))
    assert isinstance(usd.get("export"), (int, float))


# ---------- Regression smoke ----------
def test_trade_intel_smoke(session):
    r = session.get(f"{BASE_URL}/api/trade-intel/hs-search", params={"q": "coffee"}, timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") in (True, None)


def test_duty_lookup_smoke(session):
    r = session.get(
        f"{BASE_URL}/api/duty/lookup",
        params={"hs": "090111", "origin": "842", "dest": "356"},
        timeout=45,
    )
    assert r.status_code == 200
    assert r.json().get("ok") is True
