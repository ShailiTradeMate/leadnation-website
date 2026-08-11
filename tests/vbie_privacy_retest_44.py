#!/usr/bin/env python3
"""Focused VBIE privacy/reveal retest for iteration 44.

This script intentionally tests only the owner-reported bug:
- exact source names / links must not appear in buyer payloads or UI-fed APIs
- raw LEI must not appear in buyer profile payloads
- contact reveal must be subscriber/admin gated and return in-app contact only
- active buyers should be contactable
"""
import json
import os
import random
import re
import string
import time
from pathlib import Path

import requests


APP = Path("/app")
RESULTS_PATH = APP / "test_reports" / "vbie_privacy_retest_44_results.json"
FIREBASE_KEY = "AIzaSyCHQaCkzlfOdVB1-bzuJ_NnCE7vRFmT5WA"
PASSWORD = "Shiv@12345"

FORBIDDEN_SUBSTRINGS = [
    "EU Tenders Electronic Daily",
    "GLEIF",
    "trade.gov",
    "Companies House",
    "Brønnøysund",
    "ARES",
    "SIRENE",
]
FORBIDDEN_REGEXES = [re.compile(r"\bTED\b")]
FORBIDDEN_SOURCE_DOMAINS = [
    "ted.europa.eu",
    "www.gleif.org",
    "gleif.org",
    "trade.gov/consolidated-screening-list",
    "find-and-update.company-information.service.gov.uk",
    "data.brreg.no",
    "ares.gov.cz",
    "insee.fr/fr/information/3591226",
]


def read_backend_base() -> str:
    env = (APP / "frontend" / ".env").read_text()
    for line in env.splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            return line.split("=", 1)[1].strip().rstrip("/") + "/api"
    raise RuntimeError("REACT_APP_BACKEND_URL not found")


BASE = read_backend_base()


def dump_results(results):
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False))


def token_for(email: str, password: str = PASSWORD) -> str:
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_KEY}"
    r = requests.post(url, json={"email": email, "password": password, "returnSecureToken": True}, timeout=30)
    r.raise_for_status()
    return r.json()["idToken"]


def create_fresh_user_token() -> tuple[str, str]:
    suffix = "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10))
    email = f"vbie-nosub-{int(time.time())}-{suffix}@leadtest.dev"
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_KEY}"
    r = requests.post(url, json={"email": email, "password": PASSWORD, "returnSecureToken": True}, timeout=30)
    r.raise_for_status()
    return email, r.json()["idToken"]


def h(token: str | None = None) -> dict:
    return {"Authorization": f"Bearer {token}"} if token else {}


def get_json(method: str, path: str, token: str | None = None, expected: int = 200):
    r = requests.request(method, f"{BASE}{path}", headers=h(token), timeout=45)
    ok = r.status_code == expected
    body = None
    try:
        body = r.json()
    except Exception:
        body = r.text[:500]
    return ok, r.status_code, body


def as_text(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)


def find_forbidden(obj) -> list[str]:
    text = as_text(obj)
    hits = [s for s in FORBIDDEN_SUBSTRINGS if s in text]
    hits += [rgx.pattern for rgx in FORBIDDEN_REGEXES if rgx.search(text)]
    hits += [d for d in FORBIDDEN_SOURCE_DOMAINS if d in text]
    return sorted(set(hits))


def raw_lei_key_paths(obj, path="$") -> list[str]:
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            new = f"{path}.{k}"
            if k == "lei":
                hits.append(new)
            hits.extend(raw_lei_key_paths(v, new))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(raw_lei_key_paths(v, f"{path}[{i}]"))
    return hits


def source_url_key_paths(obj, path="$") -> list[str]:
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            new = f"{path}.{k}"
            if k in {"source_url", "source_link", "url", "href"}:
                hits.append(new)
            hits.extend(source_url_key_paths(v, new))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(source_url_key_paths(v, f"{path}[{i}]"))
    return hits


def mongo_probe():
    """Read-only DB probe to choose a GLEIF/LEI buyer and verify contact-only invariant."""
    try:
        from pymongo import MongoClient
    except Exception as exc:
        return {"available": False, "error": f"pymongo import failed: {exc}"}
    env = (APP / "backend" / ".env").read_text()
    mongo_url = re.search(r'MONGO_URL="?([^"\n]+)"?', env).group(1)
    db_name = re.search(r'DB_NAME="?([^"\n]+)"?', env).group(1)
    client = MongoClient(mongo_url, serverSelectionTimeoutMS=15000)
    db = client[db_name]
    no_contact_q = {
        "entity_type": "buyer",
        "status": "active",
        "merged_into": None,
        "$nor": [
            {"contact.email": {"$exists": True, "$nin": ["", None]}},
            {"contact.phone": {"$exists": True, "$nin": ["", None]}},
        ],
    }
    no_contact_count = db.entities.count_documents(no_contact_q)
    trust_factor_leak_q = {
        "entity_type": "buyer",
        "status": "active",
        "merged_into": None,
        "trust.factors.detail": {
            "$regex": "EU Tenders Electronic Daily|\\bTED\\b|GLEIF|trade\\.gov|Companies House|Brønnøysund|ARES|SIRENE"
        },
    }
    trust_factor_leak_count = db.entities.count_documents(trust_factor_leak_q)
    geid_doc = db.entities.find_one(
        {
            "entity_type": "buyer",
            "status": "active",
            "merged_into": None,
            "has_contact": True,
            "$or": [{"provenance.source_id": "gleif"}, {"lei": {"$exists": True, "$nin": ["", None]}}],
        },
        {"_id": 1, "display_name": 1, "contact.email": 1, "contact.phone": 1, "provenance.source_id": 1, "lei": 1},
        sort=[("trust.score", -1)],
    )
    return {
        "available": True,
        "no_contact_active_buyers": no_contact_count,
        "trust_factor_leak_count": trust_factor_leak_count,
        "selected_geid": geid_doc.get("_id") if geid_doc else None,
        "selected_name": geid_doc.get("display_name") if geid_doc else None,
        "selected_has_lei": bool(geid_doc and geid_doc.get("lei")),
    }


def main():
    results = {
        "base": BASE,
        "checks": [],
        "failures": [],
        "tokens": {},
        "mongo_probe": None,
    }

    def record(name, passed, details=None):
        row = {"name": name, "passed": bool(passed), "details": details or {}}
        results["checks"].append(row)
        if not passed:
            results["failures"].append(row)

    # Choose a buyer that exercises the old GLEIF/LEI leak where possible.
    mp = mongo_probe()
    results["mongo_probe"] = mp
    geid = mp.get("selected_geid") if mp.get("available") else None

    ok, status, search = get_json("GET", "/buyers/search?limit=5")
    record("GET /buyers/search returns buyers", ok and bool(search.get("buyers")), {"status": status, "count": len(search.get("buyers", [])) if isinstance(search, dict) else None})
    if not geid and ok and search.get("buyers"):
        geid = search["buyers"][0]["geid"]
    record("selected test GEID", bool(geid), {"geid": geid})
    if not geid:
        dump_results(results)
        raise SystemExit(2)

    if mp.get("available"):
        record("DB active buyers are contactable", mp.get("no_contact_active_buyers") == 0, {"no_contact_active_buyers": mp.get("no_contact_active_buyers")})
        record("DB active buyer trust factors have no forbidden registry names", mp.get("trust_factor_leak_count") == 0, {"trust_factor_leak_count": mp.get("trust_factor_leak_count")})

    # Auth tokens.
    subscriber_token = token_for("vaibhav@leadnation.app")
    admin_token = token_for("admin@leadnation.app")
    non_sub_email, non_sub_token = create_fresh_user_token()
    results["tokens"] = {"subscriber": "vaibhav@leadnation.app", "admin": "admin@leadnation.app", "non_subscriber": non_sub_email}

    # Buyer profile payloads: anonymous + entitled subscriber/admin must be source-sanitized and LEI-free.
    for label, token in [("anonymous", None), ("subscriber", subscriber_token), ("admin", admin_token)]:
        ok, status, body = get_json("GET", f"/buyers/{geid}", token=token)
        forbidden = find_forbidden(body)
        lei_paths = raw_lei_key_paths(body)
        record(f"GET /buyers/{{geid}} {label} status", ok, {"status": status, "locked": body.get("locked") if isinstance(body, dict) else None})
        record(f"GET /buyers/{{geid}} {label} has no exact source brands/domains", ok and not forbidden, {"hits": forbidden})
        record(f"GET /buyers/{{geid}} {label} has no raw lei key", ok and not lei_paths, {"lei_paths": lei_paths})
        if label == "anonymous":
            record("anonymous profile is locked", ok and body.get("locked") is True, {"lock_reason": body.get("lock_reason") if isinstance(body, dict) else None})
        else:
            record(f"{label} profile is unlocked", ok and body.get("locked") is False, {"locked": body.get("locked") if isinstance(body, dict) else None})

    # Evidence and sources endpoints must not expose GLEIF or exact sources.
    ok, status, evidence = get_json("GET", f"/buyers/{geid}/evidence", token=subscriber_token)
    record("GET /buyers/{geid}/evidence subscriber status", ok, {"status": status})
    record("GET /buyers/{geid}/evidence has no exact source brands/domains", ok and not find_forbidden(evidence), {"hits": find_forbidden(evidence)})
    record("GET /buyers/{geid}/evidence has no source URL keys", ok and not source_url_key_paths(evidence), {"source_url_key_paths": source_url_key_paths(evidence)})

    ok, status, sources = get_json("GET", "/buyers/sources")
    record("GET /buyers/sources status", ok, {"status": status})
    record("GET /buyers/sources has no exact source brands/domains", ok and not find_forbidden(sources), {"hits": find_forbidden(sources)})
    record("GET /buyers/sources has no URL keys", ok and not source_url_key_paths(sources), {"source_url_key_paths": source_url_key_paths(sources)})

    # Reveal gating.
    for label, token, expected in [
        ("anonymous", None, 402),
        ("non_subscriber", non_sub_token, 402),
        ("subscriber", subscriber_token, 200),
        ("admin", admin_token, 200),
    ]:
        ok, status, body = get_json("POST", f"/buyers/{geid}/contact", token=token, expected=expected)
        details = {"status": status, "body": body if status != 200 else {"keys": list(body.keys()), "contact": body.get("contact", {})}}
        record(f"POST /buyers/{{geid}}/contact {label} expected {expected}", ok, details)
        if expected == 200:
            contact = body.get("contact", {}) if isinstance(body, dict) else {}
            contactable = bool(contact.get("email") or contact.get("phone"))
            forbidden = find_forbidden(body)
            url_keys = [p for p in source_url_key_paths(body) if not p.endswith(".contact.website")]
            record(f"POST /buyers/{{geid}}/contact {label} returns email/phone", ok and contactable, {"contact": contact})
            record(f"POST /buyers/{{geid}}/contact {label} has no exact source brands/domains", ok and not forbidden, {"hits": forbidden})
            record(f"POST /buyers/{{geid}}/contact {label} has no source URL/link keys", ok and not url_keys, {"source_url_key_paths": url_keys})

    # Search-card sample should expose only contactable cards and no source brands.
    if isinstance(search, dict):
        record("search cards have no exact source brands/domains", not find_forbidden(search), {"hits": find_forbidden(search)})
        cards = search.get("buyers", [])
        record("search cards mark buyers contactable", bool(cards) and all(c.get("has_contact") is True for c in cards), {"has_contact_values": [c.get("has_contact") for c in cards]})

    dump_results(results)
    if results["failures"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()