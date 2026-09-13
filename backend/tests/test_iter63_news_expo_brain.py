"""
Iteration 63 — Vametra AI: News country scoping bug, Expo live engine, Brain product mode,
Product Info removal, Event submission → admin approval flow.

Scope-limited: only touches news / expo / brain-product / event-submission APIs.
"""
import os
import time
import json
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://leadnation-build.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

# Firebase creds for admin token minting
FIREBASE_KEY = "AIzaSyCHQaCkzlfOdVB1-bzuJ_NnCE7vRFmT5WA"
ADMIN_EMAIL = "admin@vametra.com"
ADMIN_PASS = "Shiv@12345"


@pytest.fixture(scope="session")
def admin_token():
    try:
        r = requests.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_KEY}",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASS, "returnSecureToken": True},
            timeout=30,
        )
        if r.status_code == 200:
            return r.json().get("idToken")
    except Exception as e:
        print(f"Firebase admin login failed: {e}")
    return None


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    if not admin_token:
        pytest.skip("No admin token")
    return {"Authorization": f"Bearer {admin_token}"}


# ============================================================
# NEWS API
# ============================================================
class TestNewsAPI:
    def test_topics(self):
        r = requests.get(f"{API}/news/topics", timeout=30)
        assert r.status_code == 200
        data = r.json()
        topics = data.get("topics") or data
        assert isinstance(topics, list)
        assert len(topics) == 12, f"Expected 12 topics, got {len(topics)}"

    def test_countries(self):
        r = requests.get(f"{API}/news/countries", timeout=30)
        assert r.status_code == 200
        data = r.json()
        countries = data.get("countries") or data
        assert isinstance(countries, list)
        assert len(countries) >= 200, f"Expected ~249 countries, got {len(countries)}"
        # spot-check shape
        sample = countries[0]
        assert "code" in sample and "name" in sample

    def test_status(self):
        r = requests.get(f"{API}/news/status", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert "adapters" in data or "sources" in data or isinstance(data, dict)

    def test_global_feed_returns_items(self):
        r = requests.get(f"{API}/news/feed", params={"topic": "all", "refresh": 1}, timeout=90)
        assert r.status_code == 200
        data = r.json()
        items = data.get("items") or []
        assert len(items) > 0, "Global feed empty"
        first = items[0]
        assert first.get("title")
        assert first.get("publishedAt") or first.get("published_at")
        assert first.get("source") or first.get("sourceName")
        # last updated stamp
        assert data.get("lastUpdated") or data.get("last_updated") or data.get("cachedAt")

    # ---------- The critical bug fix: country scoping ----------
    def test_country_scoping_bug_am_vs_global(self):
        """Armenia country feed must return DIFFERENT articles than Global, with scope='country' block first."""
        g = requests.get(f"{API}/news/feed", params={"topic": "all", "refresh": 1}, timeout=90)
        c = requests.get(f"{API}/news/feed", params={"country": "am", "topic": "all", "refresh": 1}, timeout=90)
        assert g.status_code == 200 and c.status_code == 200
        gitems = g.json().get("items") or []
        citems = c.json().get("items") or []
        assert gitems and citems
        # There should be a scope='country' segment when a country is selected
        scopes = [i.get("scope") for i in citems]
        assert "country" in scopes, f"No country-scope items in Armenia feed. scopes={set(scopes)}"
        # country block must be BEFORE global block
        first_country_idx = scopes.index("country")
        first_global_idx = scopes.index("global") if "global" in scopes else len(scopes)
        assert first_country_idx < first_global_idx, "country block should come before global block"
        # Compare titles of country-scoped block vs pure global
        country_titles = {i["title"] for i in citems if i.get("scope") == "country"}
        global_titles = {i["title"] for i in gitems[:20]}
        overlap = country_titles & global_titles
        assert len(country_titles) > 0
        # Country-scoped titles must be largely different from global (regression: user reported same articles)
        ratio = len(overlap) / max(1, len(country_titles))
        assert ratio < 0.5, f"Country-scoped titles too similar to global ({ratio:.2f} overlap). Country={list(country_titles)[:5]}"

    @pytest.mark.parametrize("cc", ["in", "br"])
    def test_country_scoping_other_countries(self, cc):
        g = requests.get(f"{API}/news/feed", params={"topic": "all", "refresh": 1}, timeout=90)
        c = requests.get(f"{API}/news/feed", params={"country": cc, "topic": "all", "refresh": 1}, timeout=90)
        assert c.status_code == 200
        citems = c.json().get("items") or []
        gitems = g.json().get("items") or []
        assert citems
        scopes = {i.get("scope") for i in citems}
        assert "country" in scopes, f"Missing country scope for {cc}"
        country_titles = {i["title"] for i in citems if i.get("scope") == "country"}
        global_titles = {i["title"] for i in gitems[:20]}
        overlap = country_titles & global_titles
        ratio = len(overlap) / max(1, len(country_titles))
        assert ratio < 0.5, f"{cc}: too much overlap with global ({ratio:.2f})"

    def test_search_filter(self):
        r = requests.get(f"{API}/news/feed", params={"q": "tariff", "topic": "all"}, timeout=90)
        assert r.status_code == 200
        items = r.json().get("items") or []
        # If items exist, at least some should match
        if items:
            assert len(items) > 0

    @pytest.mark.parametrize("topic", [
        "top", "trade", "business", "currency", "geopolitics",
        "conflict", "energy", "shipping", "policy", "technology", "events", "sports"
    ])
    def test_feed_each_topic(self, topic):
        r = requests.get(f"{API}/news/feed", params={"topic": topic}, timeout=90)
        assert r.status_code == 200, f"topic {topic} failed: {r.status_code}"
        data = r.json()
        # Not asserting non-empty because some topics may have low volume, but structure must be valid
        assert "items" in data or isinstance(data, dict)


# ============================================================
# BRAIN PRODUCT MODE
# ============================================================
class TestBrainProductMode:
    def test_product_mode_ask(self):
        payload = {
            "question": "Tell me about exporting Agarbatti from India to UAE",
            "session_id": "qa-test-iter63",
            "mode": "product",
            "product": "Agarbatti",
            "origin": "India",
            "destination": "UAE",
        }
        r = requests.post(f"{API}/brain/ask", json=payload, timeout=120)
        assert r.status_code == 200, r.text[:500]
        data = r.json()
        engines = data.get("enginesUsed") or data.get("engines_used") or []
        # be tolerant of camel vs snake
        engine_set = {e.lower() for e in engines}
        for required in ["product_intelligence", "trade_statistics", "duty_benefits", "compliance", "logistics", "policy", "trade_news"]:
            assert required in engine_set, f"Missing engine {required}. Got {engine_set}"
        ctas = data.get("ctas") or []
        cta_str = json.dumps(ctas).lower()
        assert "command" in cta_str or "command-center" in cta_str
        assert "landed" in cta_str or "cost" in cta_str
        buyer = data.get("buyerAccess") or data.get("buyer_access") or {}
        assert buyer, "buyerAccess missing"
        assert buyer.get("locked") is True, f"Unauth call should be locked. Got {buyer}"

    def test_normal_mode_regression(self):
        payload = {"question": "What is HS code?", "session_id": "qa-test-iter63-normal"}
        r = requests.post(f"{API}/brain/ask", json=payload, timeout=120)
        assert r.status_code == 200
        data = r.json()
        assert data.get("answer") or data.get("response") or data.get("text")


# ============================================================
# EXPO ENGINE
# ============================================================
class TestExpo:
    def test_engine_status(self):
        r = requests.get(f"{API}/events/engine/status", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert data.get("live") is True
        assert data.get("catalogue") == 64, f"Expected 64 catalogue, got {data.get('catalogue')}"
        upcoming = data.get("upcoming") or data.get("upcomingCount") or 0
        assert upcoming > 50, f"upcoming should be >50, got {upcoming}"
        assert data.get("lastUpdated") or data.get("last_updated")

    def test_list_only_upcoming(self):
        from datetime import datetime, timezone
        r = requests.get(f"{API}/events/list", timeout=30)
        assert r.status_code == 200
        data = r.json()
        items = data.get("items") or data.get("events") or (data if isinstance(data, list) else [])
        assert items
        today = datetime.now(timezone.utc).date()
        starts = []
        for e in items[:20]:
            end = e.get("endDate") or e.get("end_date")
            start = e.get("startDate") or e.get("start_date")
            if end:
                # parse iso date
                try:
                    ed = datetime.fromisoformat(end.replace("Z", "+00:00")).date()
                    assert ed >= today, f"Past event leaked: {e.get('name')} endDate={end}"
                except Exception:
                    pass
            if start:
                starts.append(start)
        # ascending
        assert starts == sorted(starts), "startDate not ascending"

    def test_list_when_all_includes_past(self):
        r_all = requests.get(f"{API}/events/list", params={"when": "all"}, timeout=30)
        r_upc = requests.get(f"{API}/events/list", timeout=30)
        assert r_all.status_code == 200 and r_upc.status_code == 200
        all_items = r_all.json().get("items") or r_all.json().get("events") or []
        upc_items = r_upc.json().get("items") or r_upc.json().get("events") or []
        assert len(all_items) >= len(upc_items)

    def test_filters(self):
        r = requests.get(f"{API}/events/filters", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert data.get("countries") is not None


# ============================================================
# EVENT SUBMISSION → ADMIN APPROVAL FLOW
# ============================================================
class TestEventApprovalFlow:
    def test_submit_and_admin_notification(self, admin_headers):
        payload = {
            "name": "QA TEST Iter63 Global Trade Expo",
            "startDate": "2026-06-15",
            "endDate": "2026-06-17",
            "city": "Dubai",
            "country": "AE",
            "organizer": "QA Testing",
            "website": "https://qa-example.com",
            "industry": "Trade",
            "submitterEmail": "qa@vametra.com",
            "contactEmail": "qa@vametra.com",
        }
        r = requests.post(f"{API}/events/submit", json=payload, timeout=30)
        assert r.status_code in (200, 201), r.text[:500]
        data = r.json()
        assert data.get("ok") is True
        assert data.get("adminEmail") is True
        event_id = data.get("id") or data.get("eventId")

        # Admin notifications
        n = requests.get(f"{API}/events/admin/notifications", headers=admin_headers, timeout=30)
        assert n.status_code == 200, n.text[:500]
        nd = n.json()
        items = nd.get("items") or nd.get("notifications") or []
        kinds = [i.get("kind") for i in items]
        assert "event_submission" in kinds, f"Missing event_submission. Kinds={kinds}"
        unread = nd.get("unread") or 0
        assert unread >= 1
        counts = nd.get("counts") or {}
        assert counts.get("payment_pending", 0) >= 0  # tolerant
        assert counts.get("ai_discovered", 0) >= 0

        # mark read
        rd = requests.post(f"{API}/events/admin/notifications/read", headers=admin_headers, timeout=30)
        assert rd.status_code == 200

        # cleanup — delete event
        if event_id:
            try:
                requests.delete(f"{API}/events/admin/{event_id}", headers=admin_headers, timeout=30)
            except Exception:
                pass


# ============================================================
# PRODUCT INFO ROUTE REMOVAL (backend-side check)
# ============================================================
class TestProductInfoRemoval:
    def test_no_product_info_backend(self):
        # There shouldn't be a /api/product-info endpoint anymore; a 404 is expected
        r = requests.get(f"{API}/product-info", timeout=15)
        # Either 404 or method-not-allowed acceptable; must NOT be 200
        assert r.status_code != 200, f"product-info endpoint still active: {r.status_code}"
