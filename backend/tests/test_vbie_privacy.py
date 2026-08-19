"""VBIE privacy / reveal tests (iteration 43)."""
import os, json, time, requests, pytest

BASE = os.environ.get("REACT_APP_BACKEND_URL", "https://vbie-verify.preview.emergentagent.com").rstrip("/")
FB_KEY = "AIzaSyCHQaCkzlfOdVB1-bzuJ_NnCE7vRFmT5WA"
ADMIN_HDR = {"X-Admin-Token": "leadnation-admin-2026"}

FORBIDDEN_SOURCES = ["EU Tenders Electronic Daily", "Companies House", "ted.europa.eu"]
FORBIDDEN_META = ["EU TED", "Companies House", "GLEIF", "EU Tenders Electronic Daily"]


def _mint(email, password, signup=False):
    ep = "signUp" if signup else "signInWithPassword"
    r = requests.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts:{ep}?key={FB_KEY}",
        json={"email": email, "password": password, "returnSecureToken": True}, timeout=20)
    if r.status_code != 200:
        return None
    return r.json().get("idToken")


@pytest.fixture(scope="session")
def vaibhav_token():
    tok = _mint("vaibhav@leadnation.app", "Shiv@12345")
    if not tok: pytest.skip("Cannot mint vaibhav token")
    return tok


@pytest.fixture(scope="session")
def admin_token():
    tok = _mint("admin@leadnation.app", "Shiv@12345")
    if not tok: pytest.skip("Cannot mint admin token")
    return tok


@pytest.fixture(scope="session")
def nosub_token():
    email = f"testnosub_{int(time.time())}@leadtest.dev"
    tok = _mint(email, "Shiv@12345", signup=True)
    if not tok: pytest.skip("Cannot mint fresh non-sub token")
    return tok


@pytest.fixture(scope="session")
def sample_geid():
    r = requests.get(f"{BASE}/api/buyers/search?limit=5", timeout=20)
    assert r.status_code == 200
    b = r.json().get("buyers", [])
    assert b, "no buyers returned from search"
    return b[0]["geid"]


# --- /buyers/{geid} entitled user (vaibhav) ---
class TestBuyerProfilePayload:
    def test_entitled_has_no_provenance_website_source_url(self, vaibhav_token, sample_geid):
        r = requests.get(f"{BASE}/api/buyers/{sample_geid}",
                         headers={"Authorization": f"Bearer {vaibhav_token}"}, timeout=20)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "provenance" not in d
        assert "website" not in d
        assert "source_url" not in d
        assert d.get("has_contact") is True
        assert isinstance(d.get("evidence"), list) and d["evidence"], "evidence must be present"
        for row in d["evidence"]:
            assert "source_label" in row and "tier_label" in row
            assert "source_url" not in row and "source_name" not in row and "note" not in row
        assert isinstance(d.get("evidence_sources"), list) and d["evidence_sources"]
        assert isinstance(d.get("primary_source"), str) and d["primary_source"]

    def test_entitled_no_registry_leak_in_full_payload(self, vaibhav_token, sample_geid):
        r = requests.get(f"{BASE}/api/buyers/{sample_geid}",
                         headers={"Authorization": f"Bearer {vaibhav_token}"}, timeout=20)
        raw = json.dumps(r.json())
        leaked = [s for s in FORBIDDEN_META if s in raw]
        assert not leaked, f"registry leak in /buyers/{{geid}}: {leaked}"

    def test_anonymous_returns_locked_login_no_leaks(self, sample_geid):
        r = requests.get(f"{BASE}/api/buyers/{sample_geid}", timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert d.get("locked") is True
        assert d.get("lock_reason") == "login"
        assert "provenance" not in d
        assert "source_url" not in d
        assert isinstance(d.get("evidence_sources"), list)
        raw = json.dumps(d)
        leaked = [s for s in FORBIDDEN_META if s in raw]
        assert not leaked, f"registry leak (anonymous): {leaked}"


# --- POST /buyers/{geid}/contact reveal ---
class TestReveal:
    def test_reveal_anonymous_402(self, sample_geid):
        r = requests.post(f"{BASE}/api/buyers/{sample_geid}/contact", timeout=20)
        assert r.status_code == 402, r.text

    def test_reveal_nonsub_402(self, nosub_token, sample_geid):
        r = requests.post(f"{BASE}/api/buyers/{sample_geid}/contact",
                          headers={"Authorization": f"Bearer {nosub_token}"}, timeout=20)
        assert r.status_code == 402, r.text

    def test_reveal_subscriber_200(self, vaibhav_token, sample_geid):
        r = requests.post(f"{BASE}/api/buyers/{sample_geid}/contact",
                          headers={"Authorization": f"Bearer {vaibhav_token}"}, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        c = d.get("contact") or {}
        assert (c.get("email") or c.get("phone")), "email or phone required"
        for k in ("email","phone","address","city","website","contact_name"):
            assert k in c, f"missing contact field: {k}"
        raw = json.dumps(d)
        assert "http://" not in raw and "https://" not in raw, "no URL in reveal response"

    def test_reveal_admin_firebase_200(self, admin_token, sample_geid):
        r = requests.post(f"{BASE}/api/buyers/{sample_geid}/contact",
                          headers={"Authorization": f"Bearer {admin_token}"}, timeout=30)
        assert r.status_code == 200, r.text


# --- /evidence, /sources, /meta ---
class TestEvidenceSourcesMeta:
    def test_evidence_generic(self, vaibhav_token, sample_geid):
        r = requests.get(f"{BASE}/api/buyers/{sample_geid}/evidence",
                         headers={"Authorization": f"Bearer {vaibhav_token}"}, timeout=20)
        assert r.status_code == 200
        d = r.json()
        for row in d.get("evidence", []):
            assert "source_url" not in row and "source_name" not in row and "note" not in row
            assert "source_label" in row and "tier_label" in row

    def test_sources_no_forbidden(self):
        r = requests.get(f"{BASE}/api/buyers/sources", timeout=20)
        assert r.status_code == 200
        d = r.json()
        srcs = d.get("sources", [])
        for row in srcs:
            assert "url" not in row, f"url field leaked: {row}"
            assert "attribution" not in row, f"attribution field leaked: {row}"
        raw = json.dumps(d)
        for s in FORBIDDEN_SOURCES:
            assert s not in raw, f"forbidden {s!r} in /sources"

    def test_meta_disclaimer_no_registry(self):
        r = requests.get(f"{BASE}/api/buyers/meta", timeout=20)
        assert r.status_code == 200
        d = r.json()
        raw = json.dumps(d)
        for s in FORBIDDEN_META:
            assert s not in raw, f"forbidden {s!r} in /meta"


class TestContactCoverage:
    def test_active_buyers_all_have_contact(self, vaibhav_token):
        r = requests.get(f"{BASE}/api/buyers/search?limit=10", timeout=20)
        assert r.status_code == 200
        buyers = r.json().get("buyers", [])
        assert buyers
        for b in buyers:
            assert b.get("has_contact") is True, f"{b['geid']} lacks contact"
        # spot check reveal on 3
        for b in buyers[:3]:
            rr = requests.post(f"{BASE}/api/buyers/{b['geid']}/contact",
                               headers={"Authorization": f"Bearer {vaibhav_token}"}, timeout=30)
            assert rr.status_code == 200
            c = rr.json().get("contact", {})
            assert c.get("email") or c.get("phone")
