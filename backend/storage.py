"""Pluggable object-storage abstraction for LeadNation.

A single `storage_provider` interface so we can migrate between Emergent Object
Storage (now), Firebase Storage, AWS S3 or DigitalOcean Spaces later WITHOUT
rewriting callers. Files are stored via the active provider; the canonical record
lives in Mongo (`uploaded_files`) with a soft-delete flag. Shared by website AND
the mobile app (same upload + serve endpoints).
"""
import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Tuple

import requests
from fastapi import APIRouter, UploadFile, File, Header, Query, HTTPException, Response

from core import db
from firebase_auth import optional_user

router = APIRouter(prefix="/storage")
FILES = db.uploaded_files

APP_NAME = "leadnation"
STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY")
STORAGE_PROVIDER = os.environ.get("STORAGE_PROVIDER", "emergent")

MIME_TYPES = {
    "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
    "gif": "image/gif", "webp": "image/webp", "pdf": "application/pdf",
    "svg": "image/svg+xml", "csv": "text/csv", "txt": "text/plain",
}
MAX_BYTES = 12 * 1024 * 1024  # 12 MB per file


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------- Provider interface ----------------
class StorageProvider:
    name = "base"

    def put(self, path: str, data: bytes, content_type: str) -> dict:
        raise NotImplementedError

    def get(self, path: str) -> Tuple[bytes, str]:
        raise NotImplementedError


class EmergentStorage(StorageProvider):
    name = "emergent"
    _key = None

    def _init(self) -> Optional[str]:
        if self._key:
            return self._key
        if not EMERGENT_KEY:
            return None
        resp = requests.post(f"{STORAGE_URL}/init", json={"emergent_key": EMERGENT_KEY}, timeout=30)
        resp.raise_for_status()
        EmergentStorage._key = resp.json()["storage_key"]
        return self._key

    def put(self, path: str, data: bytes, content_type: str) -> dict:
        key = self._init()
        if not key:
            raise RuntimeError("Storage not configured (EMERGENT_LLM_KEY missing)")
        resp = requests.put(f"{STORAGE_URL}/objects/{path}",
                            headers={"X-Storage-Key": key, "Content-Type": content_type},
                            data=data, timeout=120)
        resp.raise_for_status()
        return resp.json()

    def get(self, path: str) -> Tuple[bytes, str]:
        key = self._init()
        if not key:
            raise RuntimeError("Storage not configured")
        resp = requests.get(f"{STORAGE_URL}/objects/{path}",
                            headers={"X-Storage-Key": key}, timeout=60)
        resp.raise_for_status()
        return resp.content, resp.headers.get("Content-Type", "application/octet-stream")


_PROVIDERS = {"emergent": EmergentStorage()}


def get_provider() -> StorageProvider:
    return _PROVIDERS.get(STORAGE_PROVIDER, _PROVIDERS["emergent"])


def init_storage():
    prov = get_provider()
    if isinstance(prov, EmergentStorage):
        prov._init()


# ---------------- Public API ----------------
@router.post("/upload")
async def upload_file(file: UploadFile = File(...),
                      authorization: Optional[str] = Header(default=None)):
    claims = await optional_user(authorization)
    owner = (claims or {}).get("uid", "guest")
    ext = (file.filename.rsplit(".", 1)[-1].lower() if "." in (file.filename or "") else "bin")
    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "File too large (max 12 MB).")
    content_type = file.content_type or MIME_TYPES.get(ext, "application/octet-stream")
    path = f"{APP_NAME}/uploads/{owner}/{uuid.uuid4().hex}.{ext}"
    try:
        result = get_provider().put(path, data, content_type)
    except Exception as exc:
        logging.error("Upload failed: %s", exc)
        raise HTTPException(502, "Upload failed. Please retry.")
    stored_path = result.get("path", path)
    fid = uuid.uuid4().hex
    await FILES.insert_one({
        "_id": fid, "id": fid, "storage_path": stored_path,
        "original_filename": file.filename, "content_type": content_type,
        "size": result.get("size", len(data)), "owner": owner,
        "provider": get_provider().name, "is_deleted": False, "created_at": _now()})
    return {"id": fid, "url": f"/api/storage/file/{fid}", "path": stored_path,
            "filename": file.filename, "size": result.get("size", len(data)),
            "contentType": content_type}


@router.get("/file/{fid}")
async def serve_file(fid: str):
    rec = await FILES.find_one({"_id": fid, "is_deleted": False})
    if not rec:
        raise HTTPException(404, "File not found")
    try:
        data, ctype = get_provider().get(rec["storage_path"])
    except Exception as exc:
        logging.error("File fetch failed: %s", exc)
        raise HTTPException(502, "File unavailable")
    return Response(content=data, media_type=rec.get("content_type", ctype),
                    headers={"Cache-Control": "public, max-age=86400"})
