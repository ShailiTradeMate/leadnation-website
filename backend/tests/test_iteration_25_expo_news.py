"""Iteration 25 — Expo Events Engine + Trade News Engine + Storage regression.

Uses backend admin fallback: header X-Admin-Token: leadnation-admin-2026.
Covers:
  * /api/events/filters, /list, /pricing (INR/USD)
  * POST /events/submit, /pay/stripe, /pay/razorpay/order (503)
  * Admin approve/reject/feature/extend/delete + pricing GET/PUT
  * /api/news/feed (guest), /news/{id} impact, admin CRUD, feature-first
  * /api/storage/upload + file serve
"""
import io
import os
import time
import uuid

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://trade-brain-ai.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"
ADMIN_HDR = {"X-Admin-Token": "leadnation-admin-2026"}


@pytest.fixture(scope="session")
def s():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


# ---------------- EVENTS ----------------
class TestEventsPublic:
    def test_filters(self, s):
        r = s.get(f"{API}/events/filters", timeout=20)
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ("categories", "industries", "audiences", "countries"):
            assert k in d and isinstance(d[k], list) and len(d[k]) > 0

    def test_list_only_published(self, s):
        r = s.get(f"{API}/events/list", timeout=20)
        assert r.status_code == 200
        items = r.json().get("items", [])
        assert isinstance(items, list) and len(items) >= 1
        for it in items:
            assert it.get("status") in ("published", "approved"), it.get("status")
        # Gulfood (seeded featured) should be present
        names = [i.get("name", "") for i in items]
        assert any("Gulfood" in n for n in names), f"No Gulfood in list: {names[:5]}"

    def test_pricing_india_inr(self, s):
        r = s.get(f"{API}/events/pricing", params={"country": "India"}, timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert d["region"] == "IN"
        assert float(d["amount"]) == 10000.0
        assert d["currency"] == "inr"
        assert d["durationDays"] == 30

    def test_pricing_intl_usd(self, s):
        r = s.get(f"{API}/events/pricing", params={"region": "INTL"}, timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert d["region"] == "INTL"
        assert float(d["amount"]) == 105.0
        assert d["currency"] == "usd"


# ---------------- EVENT SUBMISSION + PAYMENT ----------------
@pytest.fixture(scope="session")
def submitted_event(s):
    body = {
        "name": f"TEST_Regression_Expo_{uuid.uuid4().hex[:6]}",
        "category": "Trade Fair",
        "country": "USA",
        "city": "New York",
        "startDate": "2026-06-10",
        "endDate": "2026-06-12",
        "industry": "Multi-sector",
        "audience": "Buyers",
        "description": "Automated regression test event.",
        "venueName": "Test Center",
        "organizer": "TestOrg",
        "contactEmail": "test-regression@leadnation.app",
        "contactName": "Test User",
    }
    r = s.post(f"{API}/events/submit", json=body, timeout=20)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["ok"] and d.get("eventId")
    assert d["status"] == "payment_pending"
    assert d["region"] == "INTL"
    return d["eventId"]


class TestEventSubmit:
    def test_submit_contact_email_required(self, s):
        # Missing contactEmail -> 422
        r = s.post(f"{API}/events/submit",
                   json={"name": "X", "country": "India"}, timeout=20)
        assert r.status_code == 422, r.text

    def test_submit_created(self, submitted_event):
        assert isinstance(submitted_event, str) and len(submitted_event) > 8

    def test_stripe_checkout_intl(self, s, submitted_event):
        r = s.post(f"{API}/events/{submitted_event}/pay/stripe",
                   json={"origin": BASE_URL}, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("url", "").startswith("https://checkout.stripe.com"), d
        assert float(d["amount"]) == 105.0
        assert d["currency"] == "usd"

    def test_razorpay_503_graceful(self, s, submitted_event):
        r = s.post(f"{API}/events/{submitted_event}/pay/razorpay/order", timeout=20)
        assert r.status_code == 503, r.text


# ---------------- ADMIN EVENTS ----------------
class TestEventsAdmin:
    def test_admin_all(self, s):
        r = requests.get(f"{API}/events/admin/all", headers=ADMIN_HDR, timeout=20)
        assert r.status_code == 200, r.text
        assert isinstance(r.json().get("items"), list)

    def test_admin_all_requires_auth(self, s):
        r = requests.get(f"{API}/events/admin/all", timeout=20)
        assert r.status_code in (401, 403), r.status_code

    def test_admin_pricing_get_and_update(self, s):
        r = requests.get(f"{API}/events/admin/pricing", headers=ADMIN_HDR, timeout=20)
        assert r.status_code == 200
        original = r.json()
        # Increment INR then restore
        upd = {"inAmount": float(original["IN"]["amount"]) + 1.0,
               "intlAmount": float(original["INTL"]["amount"]),
               "durationDays": int(original["durationDays"]),
               "discountPct": original.get("discountPct", 0)}
        r2 = requests.put(f"{API}/events/admin/pricing", json=upd, headers=ADMIN_HDR, timeout=20)
        assert r2.status_code == 200, r2.text
        r3 = requests.get(f"{API}/events/admin/pricing", headers=ADMIN_HDR, timeout=20)
        assert float(r3.json()["IN"]["amount"]) == upd["inAmount"]
        # restore
        restore = {"inAmount": float(original["IN"]["amount"]),
                   "intlAmount": float(original["INTL"]["amount"]),
                   "durationDays": int(original["durationDays"])}
        requests.put(f"{API}/events/admin/pricing", json=restore, headers=ADMIN_HDR, timeout=20)

    def test_admin_full_lifecycle(self, s):
        body = {
            "name": f"TEST_Admin_Lifecycle_{uuid.uuid4().hex[:6]}",
            "category": "Trade Fair", "country": "India", "city": "Mumbai",
            "startDate": "2026-09-01", "endDate": "2026-09-03",
            "industry": "Multi-sector", "audience": "All",
            "contactEmail": "cycle@leadnation.app", "organizer": "T",
            "description": "lifecycle",
        }
        r = s.post(f"{API}/events/submit", json=body, timeout=20)
        eid = r.json()["eventId"]

        # Approve -> publishes
        r = requests.post(f"{API}/events/admin/{eid}/approve", headers=ADMIN_HDR, timeout=20)
        assert r.status_code == 200 and r.json().get("expiresAt")

        # Appears in public list
        r = s.get(f"{API}/events/list", params={"country": "India"}, timeout=20)
        ids = [i["id"] for i in r.json()["items"]]
        assert eid in ids, "Approved event not published in /list"

        # Feature toggle
        r = requests.post(f"{API}/events/admin/{eid}/feature", headers=ADMIN_HDR, timeout=20)
        assert r.status_code == 200

        # Extend +7 days
        r = requests.post(f"{API}/events/admin/{eid}/extend",
                          json={"days": 7}, headers=ADMIN_HDR, timeout=20)
        assert r.status_code == 200 and r.json().get("expiresAt")

        # Reject (state change works even after publish)
        r = requests.post(f"{API}/events/admin/{eid}/reject",
                          json={"reason": "test"}, headers=ADMIN_HDR, timeout=20)
        assert r.status_code == 200

        # Delete
        r = requests.delete(f"{API}/events/admin/{eid}", headers=ADMIN_HDR, timeout=20)
        assert r.status_code == 200

        # 404 after delete
        r = s.get(f"{API}/events/{eid}", timeout=20)
        assert r.status_code == 404


# ---------------- NEWS ----------------
class TestNews:
    def test_feed_guest(self, s):
        r = s.get(f"{API}/news/feed", timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("personalized") is False
        items = d.get("items", [])
        assert len(items) >= 3
        # badges
        badges = {i.get("badge") for i in items}
        assert badges & {"live", "ai", "admin"}, f"Unexpected badges: {badges}"

    def test_news_detail_impact(self, s):
        r = s.get(f"{API}/news/feed", timeout=30)
        items = r.json()["items"]
        # Pick an item that persists (avoid live news that isn't cached)
        target = next((i for i in items if i.get("badge") in ("ai", "admin")), items[0])
        nid = target["id"]
        r2 = s.get(f"{API}/news/{nid}", timeout=45)
        assert r2.status_code == 200, r2.text
        d = r2.json()
        assert "impact" in d and isinstance(d["impact"], str) and len(d["impact"]) > 10

    def test_admin_news_crud_and_featured_first(self, s):
        title = f"TEST_Regression_Featured_{uuid.uuid4().hex[:6]}"
        body = {"title": title, "excerpt": "Featured test",
                "body": "Body text", "category": "Business",
                "country": "Global", "featured": True, "active": True}
        r = requests.post(f"{API}/news/admin", json=body, headers=ADMIN_HDR, timeout=20)
        assert r.status_code == 200, r.text
        nid = r.json()["id"]

        # Appears in feed
        r = s.get(f"{API}/news/feed", timeout=30)
        items = r.json()["items"]
        titles = [i["title"] for i in items]
        assert title in titles, f"Admin featured not in feed: {titles[:5]}"
        # Featured admin should appear first among admin items
        first_admin_idx = next((idx for idx, i in enumerate(items) if i.get("badge") == "admin"), None)
        assert first_admin_idx is not None
        assert items[first_admin_idx]["title"] == title, "Featured admin news should appear first"

        # Update
        r = requests.put(f"{API}/news/admin/{nid}",
                         json={**body, "title": title + "_upd"},
                         headers=ADMIN_HDR, timeout=20)
        assert r.status_code == 200

        # Delete
        r = requests.delete(f"{API}/news/admin/{nid}", headers=ADMIN_HDR, timeout=20)
        assert r.status_code == 200

    def test_admin_news_requires_auth(self):
        r = requests.get(f"{API}/news/admin/all", timeout=20)
        assert r.status_code in (401, 403)


# ---------------- STORAGE ----------------
class TestStorage:
    def test_upload_and_serve(self):
        # 1x1 png
        png_bytes = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
                     b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0"
                     b"\x00\x00\x00\x03\x00\x01\x5b\xa7\xa3\x8c\x00\x00\x00\x00IEND\xaeB`\x82")
        files = {"file": ("test.png", io.BytesIO(png_bytes), "image/png")}
        r = requests.post(f"{API}/storage/upload", files=files, timeout=60)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "id" in d and d["url"].startswith("/api/storage/file/")
        fid = d["id"]

        r2 = requests.get(f"{API}/storage/file/{fid}", timeout=60)
        assert r2.status_code == 200
        assert r2.headers.get("content-type", "").startswith("image/")
        assert len(r2.content) > 0
