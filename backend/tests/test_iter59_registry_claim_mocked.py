"""Iter 59 (MOCKED) — registry-claim submit + Add User linkage unit checks.

MOCKED ONLY: validates decision wiring and payloads without live government/DO writes.
"""

import types
import sys
import anyio

sys.path.insert(0, "/app/backend")

import verify
import verify_ai
import admin_approvals
import buyer_admin_actions as baa


class _EmptyAsyncCursor:
    def __aiter__(self):
        return self

    async def __anext__(self):
        raise StopAsyncIteration


class _SubmissionStore:
    def __init__(self):
        self.rows = []

    async def insert_one(self, doc):
        self.rows.append(dict(doc))
        return types.SimpleNamespace(inserted_id=doc.get("_id"))

    async def update_one(self, *_args, **_kwargs):
        return types.SimpleNamespace(modified_count=1)


class _SimpleStore:
    def __init__(self, row=None):
        self.row = row
        self.updated = []

    async def find_one(self, *_args, **_kwargs):
        return self.row

    async def update_one(self, *args, **kwargs):
        self.updated.append((args, kwargs))
        return types.SimpleNamespace(modified_count=1)


def test_mocked_registry_accepted_submit_forces_needs_review_and_enqueues(monkeypatch):
    subs = _SubmissionStore()
    reg = _SimpleStore({"uid": "U1", "status": "accepted", "geid": "LN-prospect-MOCK"})
    pending = _SimpleStore(None)

    fake_db = types.SimpleNamespace(
        registry_matches=reg,
        admin_approval_requests=pending,
    )
    monkeypatch.setattr(verify, "db", fake_db)
    monkeypatch.setattr(verify, "SUBS", subs)
    monkeypatch.setattr(verify, "FACE_INDEX", types.SimpleNamespace(find=lambda *_a, **_k: _EmptyAsyncCursor(), update_one=lambda *_a, **_k: None))

    async def _save_overlay(_uid, _patch):
        return None

    async def _profile(_uid, _auth):
        return {
            "customer_id": "00099",
            "name": "Mock User",
            "country": "India",
            "mobile": "9876543210",
            "company_details": {
                "company_name": "Mock Co",
                "company_email": "mock@example.com",
                "company_phone": "+919876543210",
            },
        }

    async def _load_image(_fid, _uid):
        return ("ZmFrZQ==", b"fake", "image/jpeg")

    async def _selfie(*_a, **_k):
        return {"is_human_face": True, "quality_score": 0.9, "ai_generated_likelihood": 0.01, "confidence_real_person": 0.95}

    async def _doc(*_a, **_k):
        return {"available": True, "is_business_document": True, "confidence": 0.9}

    enqueue_calls = []

    async def _enqueue(uid, kind, payload, actor, note, key=None):
        enqueue_calls.append({"uid": uid, "kind": kind, "payload": payload, "actor": actor, "note": note, "key": key})
        return {"ok": True, "request_id": "MOCK_REQ"}

    monkeypatch.setattr(verify, "_save_overlay", _save_overlay)
    monkeypatch.setattr(verify, "_profile", _profile)
    monkeypatch.setattr(verify, "_do_put_profile", lambda *_a, **_k: {"ok": True})
    monkeypatch.setattr(verify, "_load_image_b64", _load_image)
    monkeypatch.setattr(verify_ai, "analyze_selfie", _selfie)
    monkeypatch.setattr(verify_ai, "analyze_document", _doc)
    monkeypatch.setattr(verify, "_decide", lambda *_a, **_k: ("verified", 0.91, ["auto-pass"]))
    monkeypatch.setattr(admin_approvals, "enqueue", _enqueue)

    body = verify.SubmitReq(
        role="importer",
        selfie_file_id="SELFIE1",
        document_file_id="DOC1",
        doc_type="gst",
        consent=True,
        notify_opt_in=True,
        profile_patch={"city": "Pune"},
    )
    out = anyio.run(verify.submit_verification, body, {"uid": "U1", "email": "mock@example.com"}, None)

    assert out["status"] == "needs_review"
    assert out["submission"]["status"] == "needs_review"
    assert enqueue_calls, "registry_claim enqueue was not called"
    assert enqueue_calls[0]["kind"] == "registry_claim"
    assert enqueue_calls[0]["payload"]["decision"] == "approve"
    assert enqueue_calls[0]["payload"]["geid"] == "LN-prospect-MOCK"


def test_mocked_add_user_links_via_decide(monkeypatch):
    request_row = {"id": "REQ1", "kind": "registry_claim", "payload": {"geid": "LN-prospect-MOCK"}, "uid": "U1"}

    class _ReqStore:
        async def find_one(self, query, *_args, **_kwargs):
            if query.get("id") == "REQ1" and query.get("kind") == "registry_claim" and query.get("payload.geid") == "LN-prospect-MOCK":
                return request_row
            return None

    async def _decide(body, actor, authorization):
        assert body.request_ids == ["REQ1"]
        assert actor.get("is_main") is True
        assert authorization == "Bearer MOCK_MAIN"
        return {"results": [{"id": "REQ1", "status": "approved"}], "approved": 1, "failed": 0}

    monkeypatch.setattr(baa, "db", types.SimpleNamespace(admin_approval_requests=_ReqStore()))
    monkeypatch.setattr(admin_approvals, "decide", _decide)

    out = anyio.run(
        baa.add_buyer_user,
        "LN-prospect-MOCK",
        baa.AddUser(request_id="REQ1"),
        {"is_main": True, "name": "Main Admin"},
        "Bearer MOCK_MAIN",
    )
    assert out["results"][0]["status"] == "approved"
