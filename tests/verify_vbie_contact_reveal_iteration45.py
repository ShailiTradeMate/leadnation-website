#!/usr/bin/env python3
"""Focused bug verification for VBIE buyer contact reveal.

Checks the exact reported flow:
- active subscriber can reveal non-empty email/phone for many searched buyers
- anonymous and fresh non-subscriber users are gated with HTTP 402
- active buyer corpus returned by /buyers/meta has actual email/phone in Mongo
- AK EXPORTS LTD (reported no-contact Companies House buyer) is not active/searchable
"""

from __future__ import annotations

import json
import os
import random
import string
import sys
import time
from pathlib import Path

import certifi
import requests
from pymongo import MongoClient


ROOT = Path("/app")
OUT = ROOT / "test_reports" / "vbie_contact_reveal_iteration45_results.json"
FIREBASE_KEY = "AIzaSyCHQaCkzlfOdVB1-bzuJ_NnCE7vRFmT5WA"
ACTIVE_EMAIL = "vaibhav@leadnation.app"
ACTIVE_PASSWORD = "Shiv@12345"


def read_env(path: Path) -> dict:
    out = {}
    for raw in path.read_text().splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        k, v = raw.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def fb(endpoint: str, payload: dict) -> dict:
    url = f"https://identitytoolkit.googleapis.com/v1/{endpoint}?key={FIREBASE_KEY}"
    r = requests.post(url, json=payload, timeout=30)
    try:
        data = r.json()
    except Exception:
        data = {"text": r.text[:300]}
    if r.status_code >= 400:
        raise RuntimeError(f"Firebase {endpoint} failed {r.status_code}: {data}")
    return data


def sign_in(email: str, password: str) -> dict:
    return fb("accounts:signInWithPassword", {"email": email, "password": password, "returnSecureToken": True})


def sign_up_fresh_user() -> dict:
    suffix = "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8))
    email = f"vbie-nosub-{int(time.time())}-{suffix}@leadnation.app"
    password = "Shiv@12345T!"
    data = fb("accounts:signUp", {"email": email, "password": password, "returnSecureToken": True})
    data["email"] = email
    return data


def delete_firebase_user(id_token: str) -> None:
    try:
        fb("accounts:delete", {"idToken": id_token})
    except Exception as exc:  # cleanup best-effort only
        print(f"WARN: failed to cleanup fresh Firebase user: {exc}")


def nonempty_contact(contact: dict) -> bool:
    return bool(((contact or {}).get("email") or "").strip() or ((contact or {}).get("phone") or "").strip())


def main() -> int:
    frontend_env = read_env(ROOT / "frontend" / ".env")
    backend_env = read_env(ROOT / "backend" / ".env")
    api_base = frontend_env["REACT_APP_BACKEND_URL"].rstrip("/") + "/api"

    session = requests.Session()
    results = {
        "api_base": api_base,
        "checks": {},
        "sample_reveals": [],
        "failures": [],
    }

    def fail(msg: str) -> None:
        print(f"FAIL: {msg}")
        results["failures"].append(msg)

    # Public corpus checks
    meta_r = session.get(f"{api_base}/buyers/meta", timeout=30)
    results["checks"]["meta_status"] = meta_r.status_code
    if meta_r.status_code != 200:
        fail(f"GET /buyers/meta returned {meta_r.status_code}: {meta_r.text[:300]}")
        OUT.write_text(json.dumps(results, indent=2))
        return 1
    meta = meta_r.json()
    results["checks"]["meta_total"] = meta.get("total")

    search_r = session.get(f"{api_base}/buyers/search", params={"limit": 20}, timeout=30)
    results["checks"]["search_status"] = search_r.status_code
    if search_r.status_code != 200:
        fail(f"GET /buyers/search returned {search_r.status_code}: {search_r.text[:300]}")
        OUT.write_text(json.dumps(results, indent=2))
        return 1
    buyers = search_r.json().get("buyers") or []
    results["checks"]["search_count"] = len(buyers)
    if len(buyers) < 15:
        fail(f"Expected at least 15 buyers for spot-check, got {len(buyers)}")
    cards_without_has_contact = [b.get("geid") for b in buyers if not b.get("has_contact")]
    results["checks"]["cards_without_has_contact"] = cards_without_has_contact
    if cards_without_has_contact:
        fail(f"Search returned buyers with has_contact false: {cards_without_has_contact[:5]}")
    geids = [b["geid"] for b in buyers if b.get("geid")]
    if not geids:
        fail("Search returned no geids")
        OUT.write_text(json.dumps(results, indent=2))
        return 1

    # Reported no-contact buyer should not be active/searchable.
    ak_r = session.get(f"{api_base}/buyers/search", params={"q": "AK EXPORTS LTD", "limit": 10}, timeout=30)
    ak_exact = []
    if ak_r.status_code == 200:
        ak_exact = [b for b in ak_r.json().get("buyers") or [] if (b.get("display_name") or b.get("legal_name") or "").strip().upper() == "AK EXPORTS LTD"]
    results["checks"]["ak_exports_exact_active_matches"] = len(ak_exact)
    if ak_exact:
        fail("AK EXPORTS LTD still appears in active buyer search")

    # Mongo corpus truth: active total must equal actual contact-bearing active buyers.
    mongo = MongoClient(backend_env["MONGO_URL"], tlsCAFile=certifi.where(), serverSelectionTimeoutMS=30000)
    db = mongo[backend_env.get("DB_NAME", "leadnation")]
    active_q = {"entity_type": "buyer", "status": "active", "merged_into": None}
    active_total = db.entities.count_documents(active_q)
    contact_count = 0
    no_contact_examples = []
    cursor = db.entities.find(active_q, {"_id": 1, "display_name": 1, "legal_name": 1, "contact": 1, "has_contact": 1}).batch_size(500)
    for doc in cursor:
        if nonempty_contact(doc.get("contact") or {}):
            contact_count += 1
        elif len(no_contact_examples) < 10:
            no_contact_examples.append({
                "geid": str(doc.get("_id")),
                "name": doc.get("display_name") or doc.get("legal_name"),
                "has_contact_flag": bool(doc.get("has_contact")),
            })
    results["checks"]["mongo_active_total"] = active_total
    results["checks"]["mongo_active_with_actual_email_or_phone"] = contact_count
    results["checks"]["mongo_no_contact_examples"] = no_contact_examples
    if meta.get("total") != active_total:
        fail(f"/buyers/meta total {meta.get('total')} != Mongo active buyer count {active_total}")
    if active_total != contact_count:
        fail(f"Active buyer count {active_total} != buyers with actual email/phone {contact_count}; examples={no_contact_examples[:3]}")

    # Auth tokens and gating.
    active = sign_in(ACTIVE_EMAIL, ACTIVE_PASSWORD)
    active_token = active["idToken"]
    results["checks"]["active_uid"] = active.get("localId")

    first_geid = geids[0]
    anon_r = session.post(f"{api_base}/buyers/{first_geid}/contact", timeout=30)
    results["checks"]["anonymous_reveal_status"] = anon_r.status_code
    if anon_r.status_code != 402:
        fail(f"Anonymous reveal returned {anon_r.status_code}, expected 402")

    fresh = sign_up_fresh_user()
    results["checks"]["fresh_non_subscriber_uid"] = fresh.get("localId")
    try:
        ns_r = session.post(
            f"{api_base}/buyers/{first_geid}/contact",
            headers={"Authorization": f"Bearer {fresh['idToken']}"},
            timeout=30,
        )
        results["checks"]["non_subscriber_reveal_status"] = ns_r.status_code
        results["checks"]["non_subscriber_reveal_body"] = ns_r.json() if ns_r.text else {}
        if ns_r.status_code != 402:
            fail(f"Fresh non-subscriber reveal returned {ns_r.status_code}, expected 402")
    finally:
        delete_firebase_user(fresh["idToken"])

    # Active subscriber reveal for every searched buyer.
    bad_reveals = []
    for b in buyers:
        geid = b.get("geid")
        rr = session.post(f"{api_base}/buyers/{geid}/contact", headers={"Authorization": f"Bearer {active_token}"}, timeout=45)
        if rr.status_code != 200:
            bad_reveals.append({"geid": geid, "name": b.get("display_name"), "status": rr.status_code, "body": rr.text[:200]})
            continue
        data = rr.json()
        contact = data.get("contact") or {}
        if not nonempty_contact(contact):
            bad_reveals.append({"geid": geid, "name": b.get("display_name"), "status": 200, "body": data})
        if len(results["sample_reveals"]) < 8:
            results["sample_reveals"].append({
                "geid": geid,
                "name": b.get("display_name"),
                "has_email": bool((contact.get("email") or "").strip()),
                "has_phone": bool((contact.get("phone") or "").strip()),
            })
    results["checks"]["active_reveal_attempts"] = len(buyers)
    results["checks"]["bad_active_reveals"] = bad_reveals
    if bad_reveals:
        fail(f"Active subscriber reveal failed/empty for {len(bad_reveals)} buyers; first={bad_reveals[0]}")

    passed = not results["failures"]
    results["passed"] = passed
    OUT.write_text(json.dumps(results, indent=2, default=str))
    print(json.dumps(results, indent=2, default=str))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())