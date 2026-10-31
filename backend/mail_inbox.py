"""Polls the admin mailbox over IMAP and threads replies into service-request conversations."""
import asyncio
import email
import imaplib
import logging
import os
import re
from datetime import datetime, timezone
from email.header import decode_header, make_header
from email.utils import parseaddr, getaddresses, parsedate_to_datetime
from html import unescape
from typing import Optional

from core import db

log = logging.getLogger("mail_inbox")
IMAP_HOST = "imap.gmail.com"
REF_RE = re.compile(r"SR-([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", re.I)
QUOTE_CUTS = [
    re.compile(r"^On .{5,200} wrote:\s*$", re.M | re.S),
    re.compile(r"^-{2,}\s*Original Message\s*-{2,}", re.M | re.I),
    re.compile(r"^-{2,}\s*Forwarded message\s*-{2,}", re.M | re.I),
    re.compile(r"^From:\s.+\nSent:\s.+", re.M),
    re.compile(r"^_{10,}\s*$", re.M),
    re.compile(r"^Ref:\s*SR-", re.M),
]
POLL_SECONDS = 120


def _creds():
    return os.environ.get("GMAIL_IMAP_USER"), os.environ.get("GMAIL_APP_PASSWORD")


def configured() -> bool:
    u, p = _creds()
    return bool(u and p)


def _hdr(msg, name) -> str:
    raw = msg.get(name, "") or ""
    try:
        return str(make_header(decode_header(raw)))
    except Exception:
        return raw


def _addrs(msg, *names):
    out = []
    for n in names:
        out += [a.lower() for _, a in getaddresses(msg.get_all(n, []) or []) if a]
    return out


def _html_to_text(html: str) -> str:
    html = re.sub(r"(?is)<(script|style).*?</\1>", "", html)
    html = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>", "\n", html)
    return unescape(re.sub(r"<[^>]+>", "", html))


def _body_text(msg) -> str:
    plain, html = None, None
    parts = msg.walk() if msg.is_multipart() else [msg]
    for part in parts:
        ct = part.get_content_type()
        if part.get_content_disposition() == "attachment":
            continue
        try:
            payload = part.get_payload(decode=True)
        except Exception:
            payload = None
        if payload is None:
            continue
        text = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        if ct == "text/plain" and plain is None:
            plain = text
        elif ct == "text/html" and html is None:
            html = text
    return plain if plain is not None else (_html_to_text(html) if html else "")


def strip_quoted(text: str) -> str:
    text = text.replace("\r\n", "\n")
    cut = len(text)
    for rx in QUOTE_CUTS:
        m = rx.search(text)
        if m and m.start() < cut:
            cut = m.start()
    text = text[:cut]
    lines = [ln for ln in text.split("\n") if not ln.lstrip().startswith(">")]
    text = "\n".join(lines).strip()
    # drop trailing signature separator
    text = re.split(r"\n--\s*\n", text)[0].strip()
    return text[:4000]


async def _match_request(msg, body: str) -> Optional[dict]:
    subject = _hdr(msg, "Subject")
    m = REF_RE.search(body) or REF_RE.search(subject)
    if m:
        item = await db.service_requests.find_one({"id": m.group(1).lower()}, {"_id": 0})
        if item:
            return item
    if "vametra service request" not in subject.lower():
        return None
    sender = parseaddr(_hdr(msg, "From"))[1].lower()
    participants = set(_addrs(msg, "To", "Cc") + [sender])
    cands = await db.service_requests.find(
        {"$or": [{"email": {"$in": list(participants)}}, {"assignedCaEmail": {"$in": list(participants)}}]},
        {"_id": 0}).sort("createdAt", -1).to_list(50)
    for c in cands:
        if (c.get("serviceLabel") or "") and (c["serviceLabel"].lower() in subject.lower()):
            return c
    return cands[0] if cands else None


def _role_for(item: dict, sender: str) -> str:
    if sender == (item.get("email") or "").lower():
        return "customer"
    if sender and sender == (item.get("assignedCaEmail") or "").lower():
        return "CA"
    from emailer import ADMIN_EMAIL
    if sender == (ADMIN_EMAIL or "").lower():
        return "admin"
    return "other"


async def _forward_missed(item: dict, role: str, text: str, recipients: set, sender: str, when: str):
    """Customer replied without CA/admin on the thread → send them a copy."""
    if role != "customer":
        return []
    from emailer import ADMIN_EMAIL, send
    missing = [e for e in {(item.get("assignedCaEmail") or "").lower(), (ADMIN_EMAIL or "").lower()} if e and e not in recipients]
    if not missing:
        return []
    from service_desk import request_email_ctx
    ctx = request_email_ctx(item)
    ctx.update({"senderName": item.get("name") or "Customer", "senderRole": "customer", "messageText": text, "sentAt": when, "caName": item.get("assignedCa")})
    res = await send("service_reply_forward", missing[0], ctx, cc=missing[1:], reply_to=sender)
    return missing if res.get("sent") else []


async def ingest_message(raw: bytes) -> Optional[str]:
    msg = email.message_from_bytes(raw)
    message_id = (msg.get("Message-ID") or "").strip()
    if message_id and await db.service_requests.count_documents({"emailActivity.messageId": message_id}, limit=1):
        return None
    sender = parseaddr(_hdr(msg, "From"))[1].lower()
    from emailer import SENDER_EMAIL
    own_sender = parseaddr(SENDER_EMAIL or "")[1].lower()
    is_reply = bool(msg.get("In-Reply-To") or msg.get("References"))
    if sender and sender == own_sender and not is_reply:
        return None  # our own outbound copies (CC to admin) — only real replies count
    body = _body_text(msg)
    item = await _match_request(msg, body)
    if not item:
        return None
    text = strip_quoted(body) or "(empty reply)"
    role = _role_for(item, sender)
    try:
        when_dt = parsedate_to_datetime(msg.get("Date")) if msg.get("Date") else datetime.now(timezone.utc)
        when = when_dt.astimezone(timezone.utc).isoformat()
    except Exception:
        when = datetime.now(timezone.utc).isoformat()
    recipients = set(_addrs(msg, "To", "Cc"))
    forwarded = await _forward_missed(item, role, text, recipients, sender, when[:16].replace("T", " ") + " UTC")
    name = parseaddr(_hdr(msg, "From"))[0] or (item.get("name") if role == "customer" else item.get("assignedCa") if role == "CA" else sender)
    unread = ["admin"]
    if item.get("assignedCaId") and role != "CA":
        unread.append(item["assignedCaId"])
    if role == "admin":
        unread = [item["assignedCaId"]] if item.get("assignedCaId") else []
    activity = {"at": when, "by": sender, "byName": name, "role": role, "kind": "inbound", "to": _addrs(msg, "To"), "cc": _addrs(msg, "Cc"),
                "subject": _hdr(msg, "Subject"), "text": text, "messageId": message_id, "forwardedTo": forwarded, "receivedAt": datetime.now(timezone.utc).isoformat()}
    await db.service_requests.update_one({"id": item["id"]}, {
        "$push": {"emailActivity": activity, "history": {"at": when, "by": sender, "changes": [f"{role} replied by email" + (f" (forwarded to {', '.join(forwarded)})" if forwarded else "")]}},
        "$set": {"lastReplyAt": when, "lastReplyRole": role, "updatedAt": when},
        "$addToSet": {"unreadFor": {"$each": unread}},
    })
    return item["id"]


def _fetch_new(last_uid: int):
    user, pwd = _creds()
    conn = imaplib.IMAP4_SSL(IMAP_HOST)
    try:
        conn.login(user, pwd)
        conn.select("INBOX", readonly=True)
        typ, data = conn.uid("search", None, f"UID {last_uid + 1}:*")
        uids = [int(u) for u in (data[0].split() if typ == "OK" and data and data[0] else []) if int(u) > last_uid]
        out = []
        for uid in uids[-50:]:
            typ, parts = conn.uid("fetch", str(uid), "(BODY.PEEK[])")
            if typ == "OK" and parts and isinstance(parts[0], tuple):
                out.append((uid, parts[0][1]))
        return out
    finally:
        try:
            conn.logout()
        except Exception:
            pass


async def poll_once() -> dict:
    if not configured():
        return {"ok": False, "reason": "Mailbox not configured"}
    state = await db.settings.find_one({"key": "imap_inbox"}, {"_id": 0}) or {}
    last_uid = int(state.get("last_uid") or 0)
    try:
        batch = await asyncio.to_thread(_fetch_new, last_uid)
    except imaplib.IMAP4.error as e:
        log.warning("IMAP login/fetch failed: %s", e)
        await db.settings.update_one({"key": "imap_inbox"}, {"$set": {"last_error": str(e), "last_error_at": datetime.now(timezone.utc).isoformat()}}, upsert=True)
        return {"ok": False, "reason": f"IMAP error: {e}"}
    matched = []
    max_uid = last_uid
    for uid, raw in batch:
        max_uid = max(max_uid, uid)
        try:
            rid = await ingest_message(raw)
            if rid:
                matched.append(rid)
        except Exception as e:  # keep polling even if one message is malformed
            log.exception("ingest failed for uid %s: %s", uid, e)
    await db.settings.update_one({"key": "imap_inbox"}, {"$set": {
        "last_uid": max_uid, "last_poll_at": datetime.now(timezone.utc).isoformat(), "last_error": None,
        "last_scanned": len(batch), "last_matched": len(matched)}}, upsert=True)
    return {"ok": True, "scanned": len(batch), "matched": len(matched), "requestIds": matched}


async def status() -> dict:
    state = await db.settings.find_one({"key": "imap_inbox"}, {"_id": 0}) or {}
    return {"configured": configured(), "mailbox": _creds()[0] if configured() else None, "pollSeconds": POLL_SECONDS, **{k: state.get(k) for k in ("last_poll_at", "last_error", "last_scanned", "last_matched")}}


async def run_forever():
    if not configured():
        log.info("IMAP inbox polling disabled (GMAIL_IMAP_USER / GMAIL_APP_PASSWORD not set)")
        return
    # first run only tracks the current mailbox position so old mail is not re-threaded
    state = await db.settings.find_one({"key": "imap_inbox"}, {"_id": 0})
    if not state:
        try:
            batch = await asyncio.to_thread(_fetch_new, 0)
            await db.settings.update_one({"key": "imap_inbox"}, {"$set": {"last_uid": max([u for u, _ in batch], default=0), "last_poll_at": datetime.now(timezone.utc).isoformat()}}, upsert=True)
        except Exception as e:
            log.warning("IMAP baseline failed: %s", e)
    while True:
        try:
            await poll_once()
        except Exception as e:
            log.exception("inbox poll crashed: %s", e)
        await asyncio.sleep(POLL_SECONDS)
