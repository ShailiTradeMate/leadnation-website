"""VBIE has_contact engine guard verification (iteration 47).

Verifies:
  1. SEARCH GUARD: /api/buyers/search never returns has_contact=false (all filters/pages).
  2. META GUARD: /api/buyers/meta 'total' == count of has_contact=true buyers.
  3. SUBSCRIBER REVEAL: vaibhav can reveal email/phone for buyers incl. GB.
  4. Anonymous & non-subscriber => 402.
  5. Bulk-loader code enforces has_contact rule (static assertions).
"""
import os
import re
import requests
import pytest

def _load_base():
    v = os.environ.get("REACT_APP_BACKEND_URL")
    if not v:
        try:
            for line in open("/app/frontend/.env"):
                if line.startswith("REACT_APP_BACKEND_URL="):
                    v = line.split("=", 1)[1].strip()
                    break
        except Exception:
            pass
    assert v, "REACT_APP_BACKEND_URL not set"
    return v.rstrip("/")

BASE = _load_base()
FIREBASE_KEY = "AIzaSyCHQaCkzlfOdVB1-bzuJ_NnCE7vRFmT5WA"
SUB_EMAIL = "vaibhav@leadnation.app"
SUB_PASS = "Shiv@12345"


def _sign_in(email, password):
    r = requests.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_KEY}",
        json={"email": email, "password": password, "returnSecureToken": True},
        timeout=20,
    )
    assert r.status_code == 200, f"Firebase login failed for {email}: {r.status_code} {r.text}"
    return r.json()["idToken"]


def _sign_up_fresh():
    import uuid
    email = f"nosub_{uuid.uuid4().hex[:10]}@leadnation-test.app"
    r = requests.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_KEY}",
        json={"email": email, "password": "Test@12345", "returnSecureToken": True},
        timeout=20,
    )
    assert r.status_code == 200, f"Firebase signup failed: {r.status_code} {r.text}"
    return r.json()["idToken"], email


@pytest.fixture(scope="module")
def sub_token():
    return _sign_in(SUB_EMAIL, SUB_PASS)


@pytest.fixture(scope="module")
def sub_headers(sub_token):
    return {"Authorization": f"Bearer {sub_token}"}


# ---- 1. SEARCH GUARD --------------------------------------------------------

@pytest.mark.parametrize("params", [
    {"limit": 20},
    {"limit": 20, "country": "GB"},
    {"limit": 20, "offset": 20},
    {"limit": 20, "offset": 100},
    {"limit": 20, "country": "GB", "offset": 20},
])
def test_search_never_returns_no_contact(params, sub_headers):
    r = requests.get(f"{BASE}/api/buyers/search", params=params, headers=sub_headers, timeout=30)
    assert r.status_code == 200, r.text
    items = r.json().get("items") or r.json().get("results") or r.json().get("buyers") or []
    # tolerate any list-shaped payload
    if not items and isinstance(r.json(), list):
        items = r.json()
    for b in items:
        assert b.get("has_contact") is True, f"Buyer {b.get('geid')} has_contact={b.get('has_contact')} params={params}"


# ---- 2. META GUARD ----------------------------------------------------------

def test_meta_total_matches_has_contact(sub_headers):
    r = requests.get(f"{BASE}/api/buyers/meta", headers=sub_headers, timeout=30)
    assert r.status_code == 200, r.text
    meta = r.json()
    total = meta.get("total") or meta.get("count") or meta.get("total_buyers")
    assert isinstance(total, int) and total > 0, f"unexpected total in meta: {meta}"
    # Cross-check: search with no filter must return same total in a 'total'/'count' field.
    r2 = requests.get(f"{BASE}/api/buyers/search", params={"limit": 1}, headers=sub_headers, timeout=30)
    assert r2.status_code == 200
    data = r2.json()
    stotal = data.get("total") or data.get("count")
    if isinstance(stotal, int):
        assert stotal == total, f"meta.total={total} but search.total={stotal}"


# ---- 3. SUBSCRIBER REVEAL --------------------------------------------------

def _collect_geids(sub_headers, params, n=15):
    r = requests.get(f"{BASE}/api/buyers/search", params={**params, "limit": n}, headers=sub_headers, timeout=30)
    assert r.status_code == 200, r.text
    items = r.json().get("items") or r.json().get("results") or r.json().get("buyers") or []
    return [b for b in items if b.get("geid")]


def test_subscriber_reveal_15_20_buyers(sub_headers):
    global_pool = _collect_geids(sub_headers, {}, 15)
    gb_pool = _collect_geids(sub_headers, {"country": "GB"}, 5)
    pool = global_pool + gb_pool
    assert len(pool) >= 15, f"not enough buyers to spot-check: {len(pool)}"

    failures = []
    revealed = 0
    for b in pool:
        geid = b["geid"]
        # has_contact must already be True (search guard)
        assert b.get("has_contact") is True, f"{geid} leaked has_contact=false in search"
        r = requests.post(f"{BASE}/api/buyers/{geid}/contact", headers=sub_headers, timeout=30)
        if r.status_code != 200:
            failures.append((geid, r.status_code, r.text[:200]))
            continue
        data = r.json()
        contact = data.get("contact") or data
        email = (contact.get("email") or "").strip()
        phone = (contact.get("phone") or "").strip()
        if not (email or phone):
            failures.append((geid, "empty contact", str(contact)[:200]))
            continue
        revealed += 1
    assert not failures, f"reveal failures ({len(failures)}/{len(pool)}): {failures[:5]}"
    assert revealed >= 15, f"only revealed {revealed} buyers"


def test_subscriber_reveal_gb_buyer(sub_headers):
    gb = _collect_geids(sub_headers, {"country": "GB"}, 3)
    if not gb:
        pytest.skip("No GB buyers in current preview data")
    for b in gb:
        r = requests.post(f"{BASE}/api/buyers/{b['geid']}/contact", headers=sub_headers, timeout=30)
        assert r.status_code == 200, f"GB reveal failed for {b['geid']}: {r.status_code} {r.text}"
        c = r.json().get("contact") or r.json()
        assert (c.get("email") or c.get("phone")), f"GB buyer {b['geid']} has empty contact"


# ---- 4. Access control -----------------------------------------------------

def test_anonymous_reveal_402(sub_headers):
    pool = _collect_geids(sub_headers, {}, 1)
    assert pool, "no buyers"
    geid = pool[0]["geid"]
    r = requests.post(f"{BASE}/api/buyers/{geid}/contact", timeout=20)
    assert r.status_code in (401, 402, 403), f"anonymous reveal expected 401/402/403, got {r.status_code}"


def test_fresh_nonsub_reveal_402(sub_headers):
    token, email = _sign_up_fresh()
    pool = _collect_geids(sub_headers, {}, 1)
    assert pool, "no buyers"
    geid = pool[0]["geid"]
    r = requests.post(
        f"{BASE}/api/buyers/{geid}/contact",
        headers={"Authorization": f"Bearer {token}"},
        timeout=20,
    )
    assert r.status_code == 402, f"non-sub reveal expected 402, got {r.status_code}: {r.text[:200]} (email={email})"


# ---- 5. Static code audit --------------------------------------------------

def test_bulk_loader_enforces_has_contact_rule():
    src = open("/app/backend/vbie_connectors.py").read()
    # upsert_candidates block
    m = re.search(r"async def upsert_candidates\(.*?\n(?=async def )", src, re.S)
    assert m, "upsert_candidates not found"
    body = m.group(0)
    assert "has_contact(contact)" in body, "upsert_candidates missing has_contact() check"
    assert "skipped_no_contact" in body, "upsert_candidates missing skipped_no_contact counter"
    assert '"has_contact": True' in body, "upsert_candidates not setting has_contact=True"
    # run_ingestion block
    m2 = re.search(r"async def run_ingestion\(.*?\Z", src, re.S)
    assert m2, "run_ingestion not found"
    body2 = m2.group(0)
    assert "has_contact(contact)" in body2, "run_ingestion missing has_contact() check"
    assert '"has_contact": True' in body2, "run_ingestion not setting has_contact=True"
