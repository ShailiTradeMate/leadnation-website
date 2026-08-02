"""VBIE admin console + QA audit + notifications.

Admin sovereignty over the buyer graph: list/search, edit, delete (one / by-source /
all), export to Excel + PDF. Admin edits/deletes are marked so the daily connector
ingestion never overwrites them. Also: data-quality QA report, and user + admin
notifications when new buyers are ingested.
"""
import io
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from core import db, require_admin
from firebase_auth import _bearer, verify_token
from vbie import SOURCES_SEED, _SOURCE_BY_ID, _card

logger = logging.getLogger(__name__)

admin_router = APIRouter(prefix="/buyers/admin")
notif_router = APIRouter(prefix="/notifications")

BUYER_Q = {"entity_type": "buyer"}
VALID_SECTORS = None  # computed lazily from live data


def _now():
    return datetime.now(timezone.utc)


def _iso(dt):
    return dt.isoformat() if isinstance(dt, datetime) else dt


# ─────────────────────────────── QA audit ───────────────────────────────────
async def run_qa(write_report: bool = True) -> dict:
    """Full data-quality + compliance audit over the buyer graph."""
    allowed_sources = set(_SOURCE_BY_ID.keys())
    total = geid_missing = geid_dupes = name_dupes = 0
    no_provenance = bad_source = no_trust = no_country = no_sector = 0
    seen_geid, seen_nk = set(), {}
    countries, sectors, by_source = {}, {}, {}
    samples = 0

    async for e in db.entities.find(BUYER_Q):
        total += 1
        geid = e.get("geid") or e.get("_id")
        if not geid:
            geid_missing += 1
        elif geid in seen_geid:
            geid_dupes += 1
        else:
            seen_geid.add(geid)
        # duplicate identity check (country + normalized legal name)
        import re
        nk = re.sub(r"[^a-z0-9]+", " ", (e.get("legal_name") or "").lower()).strip() + "|" + (e.get("country") or "")
        if nk in seen_nk:
            name_dupes += 1
        else:
            seen_nk[nk] = geid
        prov = e.get("provenance") or []
        if not prov:
            no_provenance += 1
        for p in prov:
            if p.get("source_id") not in allowed_sources:
                bad_source += 1
                break
        if not (e.get("trust") or {}).get("factors"):
            no_trust += 1
        if not e.get("country_name"):
            no_country += 1
        if not e.get("sector"):
            no_sector += 1
        if e.get("sample"):
            samples += 1
        cn = e.get("country_name") or "—"
        countries[cn] = countries.get(cn, 0) + 1
        sec = e.get("sector") or "—"
        sectors[sec] = sectors.get(sec, 0) + 1
        for p in prov:
            sid = p.get("source_id") or "?"
            by_source[sid] = by_source.get(sid, 0) + 1

    passed = (geid_missing == 0 and geid_dupes == 0 and name_dupes == 0 and
              no_provenance == 0 and bad_source == 0 and no_trust == 0 and
              no_country == 0 and no_sector == 0 and samples == 0)
    report = {
        "generated_at": _iso(_now()),
        "total_buyers": total,
        "checks": {
            "unique_geid": {"missing": geid_missing, "duplicates": geid_dupes, "pass": geid_missing == 0 and geid_dupes == 0},
            "no_duplicate_entities": {"duplicate_name_country": name_dupes, "pass": name_dupes == 0},
            "provenance_present": {"missing": no_provenance, "pass": no_provenance == 0},
            "source_registry_compliance": {"non_registry_sources": bad_source, "pass": bad_source == 0},
            "trust_explainable": {"missing_factors": no_trust, "pass": no_trust == 0},
            "country_classified": {"missing": no_country, "pass": no_country == 0},
            "sector_classified": {"missing": no_sector, "pass": no_sector == 0},
            "no_demo_data": {"sample_records": samples, "pass": samples == 0},
        },
        "distribution": {"countries": dict(sorted(countries.items(), key=lambda x: -x[1])),
                          "sectors": dict(sorted(sectors.items(), key=lambda x: -x[1])),
                          "by_source": by_source},
        "overall_pass": passed,
    }
    if write_report:
        try:
            _write_report_md(report)
        except Exception as exc:
            logger.warning("QA report write failed: %s", exc)
    return report


def _write_report_md(r: dict):
    lines = [f"# VBIE Data Quality & Compliance Report", "",
             f"Generated: {r['generated_at']}", f"Total buyers: **{r['total_buyers']}**",
             f"Overall: **{'✅ PASS' if r['overall_pass'] else '❌ ISSUES FOUND'}**", "", "## Checks", ""]
    for name, c in r["checks"].items():
        status = "✅" if c.get("pass") else "❌"
        detail = ", ".join(f"{k}={v}" for k, v in c.items() if k != "pass")
        lines.append(f"- {status} **{name}** — {detail}")
    lines += ["", "## Distribution by country", ""]
    for k, v in list(r["distribution"]["countries"].items())[:40]:
        lines.append(f"- {k}: {v}")
    lines += ["", "## Distribution by sector", ""]
    for k, v in r["distribution"]["sectors"].items():
        lines.append(f"- {k}: {v}")
    lines += ["", "## Evidence by source", ""]
    for k, v in r["distribution"]["by_source"].items():
        src = _SOURCE_BY_ID.get(k, {})
        lines.append(f"- {src.get('name', k)} ({src.get('tier', '?')}): {v} evidence citations")
    with open("/app/memory/VBIE_QA_REPORT.md", "w") as f:
        f.write("\n".join(lines))


@admin_router.get("/qa")
async def buyers_qa(_: dict = Depends(require_admin)):
    return await run_qa(write_report=True)


# ─────────────────────────── admin buyer CRUD ───────────────────────────────
@admin_router.get("/list")
async def admin_list(q: Optional[str] = None, country: Optional[str] = None,
                     sector: Optional[str] = None, page: int = 1, limit: int = 50,
                     _: dict = Depends(require_admin)):
    query = dict(BUYER_Q)
    if country:
        query["country_name"] = country
    if sector:
        query["sector"] = sector
    if q:
        import re
        rx = {"$regex": re.escape(q.strip()), "$options": "i"}
        query["$or"] = [{"legal_name": rx}, {"products": rx}, {"city": rx}]
    page = max(1, page); limit = max(1, min(limit, 200))
    total = await db.entities.count_documents(query)
    rows = await db.entities.find(query).sort("updated_at", -1).skip((page - 1) * limit).limit(limit).to_list(limit)
    out = []
    for e in rows:
        out.append({**_card(e), "website": e.get("website", ""),
                    "created_by": e.get("created_by"), "admin_edited": bool(e.get("admin_edited")),
                    "admin_deleted": bool(e.get("admin_deleted")), "status": e.get("status"),
                    "provenance_count": len(e.get("provenance", []))})
    return {"buyers": out, "total": total, "page": page, "limit": limit}


class BuyerPatch(BaseModel):
    legal_name: Optional[str] = None
    display_name: Optional[str] = None
    country_name: Optional[str] = None
    city: Optional[str] = None
    sector: Optional[str] = None
    products: Optional[list] = None
    hs_families: Optional[list] = None
    website: Optional[str] = None
    status: Optional[str] = None


@admin_router.patch("/{geid}")
async def admin_edit(geid: str, body: BuyerPatch, _: dict = Depends(require_admin)):
    patch = {k: v for k, v in body.model_dump().items() if v is not None}
    if not patch:
        raise HTTPException(400, "No fields to update")
    patch["admin_edited"] = True
    patch["updated_at"] = _now()
    res = await db.entities.update_one({"_id": geid, "entity_type": "buyer"}, {"$set": patch})
    if not res.matched_count:
        raise HTTPException(404, "Buyer not found")
    return {"ok": True, "geid": geid, "updated": list(patch.keys())}


@admin_router.delete("/{geid}")
async def admin_delete(geid: str, hard: bool = False, _: dict = Depends(require_admin)):
    if hard:
        res = await db.entities.delete_one({"_id": geid, "entity_type": "buyer"})
        return {"ok": res.deleted_count > 0, "hard": True}
    # soft delete: mark admin_deleted so ingestion never resurrects it
    res = await db.entities.update_one({"_id": geid, "entity_type": "buyer"},
                                       {"$set": {"admin_deleted": True, "status": "deleted", "updated_at": _now()}})
    if not res.matched_count:
        raise HTTPException(404, "Buyer not found")
    return {"ok": True, "soft": True}


class BulkDelete(BaseModel):
    scope: str = "all"          # all | source
    source_id: Optional[str] = None
    hard: bool = False


@admin_router.post("/delete-bulk")
async def admin_bulk_delete(body: BulkDelete, _: dict = Depends(require_admin)):
    q = dict(BUYER_Q)
    if body.scope == "source" and body.source_id:
        q["created_by"] = f"vbie-connector:{body.source_id}"
    if body.hard:
        res = await db.entities.delete_many(q)
        return {"ok": True, "deleted": res.deleted_count, "hard": True}
    res = await db.entities.update_many(q, {"$set": {"admin_deleted": True, "status": "deleted", "updated_at": _now()}})
    return {"ok": True, "deleted": res.modified_count, "soft": True}


# ───────────────────────────── exports ──────────────────────────────────────
async def _export_rows(limit=5000):
    rows = await db.entities.find(BUYER_Q).sort("trust.score", -1).limit(limit).to_list(limit)
    data = []
    for e in rows:
        t = e.get("trust") or {}
        prov = e.get("provenance") or []
        data.append([
            e.get("geid", ""), e.get("legal_name", ""), e.get("country_name", ""),
            e.get("city", ""), e.get("sector", ""), ", ".join(e.get("products", [])),
            ", ".join(e.get("hs_families", [])), ", ".join(e.get("corridors", [])),
            t.get("score", ""), t.get("band", ""),
            "; ".join(sorted({p.get("source_name", "") for p in prov})),
            "yes" if e.get("admin_edited") else "", e.get("status", ""),
        ])
    return data


_HEADERS = ["GEID", "Legal name", "Country", "City", "Sector", "Products", "HS families",
            "Corridors", "Trust score", "Trust band", "Sources", "Admin edited", "Status"]


@admin_router.get("/export.xlsx")
async def export_xlsx(_: dict = Depends(require_admin)):
    from openpyxl import Workbook
    wb = Workbook(); ws = wb.active; ws.title = "Verified Buyers"
    ws.append(_HEADERS)
    for row in await _export_rows():
        ws.append(row)
    buf = io.BytesIO(); wb.save(buf); buf.seek(0)
    fn = f"leadnation-buyers-{_now().strftime('%Y%m%d')}.xlsx"
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": f"attachment; filename={fn}"})


@admin_router.get("/export.pdf")
async def export_pdf(_: dict = Depends(require_admin)):
    from fpdf import FPDF
    def _s(v):
        return str(v).encode("latin-1", "replace").decode("latin-1")
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page(); pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, _s("LeadNation - Verified Buyers Export"), ln=1)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(0, 5, _s(f"Generated {_now().strftime('%Y-%m-%d %H:%M UTC')}"), ln=1)
    pdf.ln(2)
    cols = [("Legal name", 70), ("Country", 30), ("Sector", 40), ("Trust", 20), ("Sources", 100)]
    pdf.set_font("Helvetica", "B", 8)
    for name, w in cols:
        pdf.cell(w, 6, _s(name), border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 7)
    for r in await _export_rows(limit=2000):
        vals = [str(r[1])[:45], str(r[2])[:20], str(r[4])[:25], f"{r[8]} {r[9]}", str(r[10])[:70]]
        for (name, w), v in zip(cols, vals):
            pdf.cell(w, 5, _s(v), border=1)
        pdf.ln()
    out = pdf.output()
    buf = io.BytesIO(bytes(out)); buf.seek(0)
    fn = f"leadnation-buyers-{_now().strftime('%Y%m%d')}.pdf"
    return StreamingResponse(buf, media_type="application/pdf",
                             headers={"Content-Disposition": f"attachment; filename={fn}"})


# ─────────────────────────── notifications ──────────────────────────────────
async def notify_ingestion(run: dict):
    """Create user + admin notifications and email subscribers when new buyers land."""
    new_n = int(run.get("new_buyers", 0) or 0)
    if new_n <= 0:
        return
    src_names = "EU TED, Canadian Importers Database, UN Comtrade (sanctions-screened via trade.gov CSL)"
    markets = len((await db.entities.distinct("country_name", {"entity_type": "buyer", "sample": {"$ne": True}})) or [])
    body = (f"{new_n} newly verified buyers were added across {markets} markets. "
            f"Sources: {src_names}. Check the Verified Buyers section for details.")
    now = _now()
    await db.notifications.insert_one({
        "audience": "users", "scope": "broadcast", "kind": "buyers_added",
        "title": "New verified buyers added", "body": body, "source": src_names,
        "meta": {"new_buyers": new_n, "markets": markets}, "created_at": _iso(now)})
    await db.notifications.insert_one({
        "audience": "admin", "scope": "admin", "kind": "buyers_added",
        "title": "Buyer ingestion complete", "source": src_names,
        "body": (f"Ingestion added {new_n} new buyers (upserted {run.get('upserted')}, "
                 f"screened out {run.get('screened_out')}, skipped admin-locked {run.get('skipped_admin', 0)}). "
                 f"Download & verify from the admin console."),
        "meta": run.get("sources", {}), "created_at": _iso(now)})
    # Best-effort email to subscribers (emails from paid transactions + captures).
    try:
        emails = set()
        async for t in db.payment_transactions.find({"email": {"$nin": ["", None]}}, {"email": 1}):
            emails.add(t["email"])
        async for c in db.email_captures.find({}, {"email": 1}):
            if c.get("email"):
                emails.add(c["email"])
        if emails:
            from emailer import send
            import asyncio
            for em in list(emails)[:200]:
                await send("buyers_added", em, {"count": new_n, "markets": markets, "sources": src_names})
                await asyncio.sleep(0.05)
    except Exception as exc:
        logger.warning("Subscriber email digest failed: %s", exc)


@notif_router.get("")
async def user_notifications(authorization: Optional[str] = Header(default=None)):
    """User-facing notifications (broadcast). Unread computed vs the user's last-read marker."""
    token = _bearer(authorization)
    claims = verify_token(token) if token else None
    uid = claims.get("uid") if claims else None
    rows = await db.notifications.find({"audience": "users"}).sort("created_at", -1).limit(30).to_list(30)
    last_read = None
    if uid:
        mk = await db.notification_reads.find_one({"uid": uid})
        last_read = (mk or {}).get("last_read")
    unread = sum(1 for r in rows if not last_read or r.get("created_at", "") > last_read)
    return {"notifications": [{k: v for k, v in r.items() if k != "_id"} for r in rows],
            "unread": unread, "authed": bool(uid)}


@notif_router.post("/read")
async def mark_read(authorization: Optional[str] = Header(default=None)):
    token = _bearer(authorization)
    claims = verify_token(token) if token else None
    if not claims:
        raise HTTPException(401, "Authentication required")
    await db.notification_reads.update_one({"uid": claims["uid"]},
                                           {"$set": {"uid": claims["uid"], "last_read": _iso(_now())}}, upsert=True)
    return {"ok": True}


@admin_router.get("/notifications")
async def admin_notifications(_: dict = Depends(require_admin)):
    rows = await db.notifications.find({"audience": "admin"}).sort("created_at", -1).limit(30).to_list(30)
    mk = await db.notification_reads.find_one({"uid": "__admin__"})
    last_read = (mk or {}).get("last_read")
    unread = sum(1 for r in rows if not last_read or r.get("created_at", "") > last_read)
    return {"notifications": [{k: v for k, v in r.items() if k != "_id"} for r in rows], "unread": unread}


@admin_router.post("/notifications/read")
async def admin_mark_read(_: dict = Depends(require_admin)):
    await db.notification_reads.update_one({"uid": "__admin__"},
                                           {"$set": {"uid": "__admin__", "last_read": _iso(_now())}}, upsert=True)
    return {"ok": True}
