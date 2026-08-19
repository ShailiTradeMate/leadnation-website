"""Vametra AI transactional email service (Resend) — production infrastructure.

Env-driven and NON-BLOCKING: if RESEND_API_KEY is missing the service logs and
no-ops so signup / payments / event submission / reports never break. Branded HTML
templates (Vametra AI Technologies Pvt Ltd · Vametra AI) covering the full
lifecycle: user, events, reports, payments and admin alerts. Shared by website AND
mobile app (same backend, same flow — an action from the app triggers the same email).
"""
import os
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

import resend
from dotenv import load_dotenv

load_dotenv()

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "").strip()
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "Vametra AI <onboarding@resend.dev>").strip()
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "").strip()
EMAIL_LOGO_URL = os.environ.get("EMAIL_LOGO_URL", "").strip()
SITE = os.environ.get("PUBLIC_SITE_URL", "https://vametra.com").rstrip("/")

BRAND = "Vametra AI"
COMPANY = "Vametra AI Technologies Pvt Ltd"

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY


# ---------------- Branded shell ----------------
def _shell(title: str, body_html: str, cta_label: str = "", cta_url: str = "") -> str:
    year = datetime.now(timezone.utc).year
    cta = ""
    if cta_label and cta_url:
        cta = (f'<tr><td style="padding:10px 0 4px 0;"><a href="{cta_url}" '
               f'style="display:inline-block;background:#00C2FF;color:#04121f;font-weight:700;'
               f'text-decoration:none;padding:12px 26px;border-radius:10px;font-size:14px;">'
               f'{cta_label}</a></td></tr>')
    return f"""<!doctype html><html><body style="margin:0;background:#05070f;font-family:Georgia,'Times New Roman',serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#05070f;padding:28px 0;">
<tr><td align="center">
<table role="presentation" width="560" cellpadding="0" cellspacing="0" style="background:#0b1120;border:1px solid #1c2740;border-radius:16px;overflow:hidden;">
<tr><td style="padding:24px 32px;border-bottom:1px solid #1c2740;">
  <div style="font-family:Georgia,'Times New Roman',serif;font-size:22px;font-weight:700;letter-spacing:-0.3px;color:#ffffff;">Vametra<span style="color:#00C2FF;"> AI</span></div>
  <div style="font-family:Arial,Helvetica,sans-serif;font-size:10px;letter-spacing:3px;color:#00C2FF;text-transform:uppercase;margin-top:5px;">Intelligence Beyond Borders</div>
  <div style="font-family:Arial,Helvetica,sans-serif;font-size:10px;letter-spacing:2px;color:#6b7c99;text-transform:uppercase;margin-top:3px;">by Vametra AI Technologies Pvt Ltd</div>
</td></tr>
<tr><td style="padding:30px 32px;font-family:Arial,Helvetica,sans-serif;">
  <h1 style="color:#ffffff;font-size:20px;margin:0 0 14px 0;">{title}</h1>
  <div style="color:#c3ccdd;font-size:14px;line-height:1.6;">{body_html}</div>
  <table role="presentation" cellpadding="0" cellspacing="0">{cta}</table>
</td></tr>
<tr><td style="padding:18px 32px;border-top:1px solid #1c2740;font-family:Arial,Helvetica,sans-serif;color:#5b6b86;font-size:11px;line-height:1.7;">
  <a href="{SITE}/legal/privacy" style="color:#8aa0c0;text-decoration:none;">Privacy Policy</a> &nbsp;·&nbsp;
  <a href="{SITE}/legal/terms" style="color:#8aa0c0;text-decoration:none;">Terms</a> &nbsp;·&nbsp;
  <a href="{SITE}/contact" style="color:#8aa0c0;text-decoration:none;">Contact</a><br/>
  &copy; {year} {COMPANY}. All rights reserved. Vametra AI is a product of {COMPANY}.<br/>
  <a href="{SITE}" style="color:#00C2FF;text-decoration:none;">{SITE.replace('https://', '')}</a>
</td></tr>
</table></td></tr></table></body></html>"""


def _amount_label(amount, currency):
    try:
        amount = float(amount)
    except Exception:
        return ""
    return f"\u20b9{amount:,.0f}" if str(currency).lower() == "inr" else f"${amount:,.2f}"


def _kv_row(label, val):
    if val in (None, "", "—"):
        return ""
    return (f'<tr><td style="padding:7px 12px;color:#8aa0c0;font-size:13px;border-bottom:1px solid #1c2740;">{label}</td>'
            f'<td style="padding:7px 12px;color:#eef3fb;font-size:13px;font-weight:600;text-align:right;border-bottom:1px solid #1c2740;">{val}</td></tr>')


def _detail_table(rows):
    body = "".join(_kv_row(l, v) for l, v in rows)
    return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            f'style="margin:14px 0;border:1px solid #1c2740;border-radius:10px;overflow:hidden;">{body}</table>')


def _benefits_ul(items):
    if not items:
        return ""
    lis = "".join(f'<li style="margin:4px 0;">{i}</li>' for i in items)
    return (f'<p style="margin:16px 0 6px;color:#ffffff;font-weight:700;">What your subscription unlocks</p>'
            f'<ul style="color:#c3ccdd;font-size:13px;line-height:1.6;padding-left:18px;margin:0;">{lis}</ul>')


def _tpl_subscription_success(c):
    rows = [
        ("Subscription", c.get("plan", "")),
        ("Amount paid", c.get("amountLabel", "")),
        ("Billing period", c.get("period", "")),
        ("Active until", str(c.get("until", ""))[:10]),
        ("Payment mode", (c.get("method", "") or "").upper()),
        ("Transaction ID", c.get("txnId", "")),
        ("Invoice", c.get("invoice", "")),
        ("User ID", c.get("userId", "")),
        ("Customer ID", c.get("customerId", "")),
        ("Registered email", c.get("email", "")),
    ]
    body = (f"<p>Hi {c.get('name', 'there')},</p>"
            f"<p>Thank you for subscribing — your <b>{c.get('plan', '')}</b> plan on {BRAND} is now "
            f"<b>active</b>. Here is your confirmation:</p>"
            + _detail_table(rows)
            + _benefits_ul(c.get("benefits", []))
            + f"<p style='margin-top:16px;'>You can manage or renew your plan anytime from your account. "
            f"{BRAND} is a product of {COMPANY}.</p>")
    return ("Your Vametra AI subscription is active ✅",
            _shell("Subscription active 🎉", body, "Manage my subscription", f"{SITE}/account?tab=billing"))


def _tpl_admin_payment_alert(c):
    rows = [
        ("Plan / item", c.get("plan", "")),
        ("Amount", c.get("amountLabel", "")),
        ("Gateway", (c.get("gateway", "") or "").title()),
        ("Payment mode", (c.get("method", "") or "").upper()),
        ("Transaction ID", c.get("txnId", "")),
        ("Invoice", c.get("invoice", "")),
        ("User ID", c.get("userId", "")),
        ("Customer ID", c.get("customerId", "")),
        ("Name", c.get("name", "")),
        ("Email", c.get("email", "")),
        ("Mobile", c.get("mobile", "")),
        ("Country", c.get("country", "")),
        ("Region", c.get("region", "")),
        ("Active until", str(c.get("until", ""))[:10]),
    ]
    body = f"<p>A new payment was captured on {BRAND}:</p>" + _detail_table(rows)
    return (f"[Vametra AI] Payment received · {c.get('amountLabel', '')} · {c.get('plan', '')}",
            _shell("New payment received 💳", body, "Open admin CMS", f"{SITE}/admin-cms"))


# ---------------- Templates (kind -> builder(ctx) -> (subject, html)) ----------------
def _b(name):
    return lambda c: BUILDERS[name](c)


BUILDERS = {
    # ---- User ----
    "account_created": lambda c: ("Welcome to Vametra AI", _shell(
        "Your Vametra AI account is ready 🎉",
        f"<p>Hi {c.get('name','there')},</p><p>Welcome aboard! Your Customer ID is "
        f"<b>{c.get('customerId','—')}</b>. Use it to sign in on the website and the Vametra AI app "
        f"— one identity across both.</p><p>Start by building a Trade Command Center report or "
        f"exploring live trade intelligence.</p>",
        "Open Vametra AI", SITE)),
    "welcome": lambda c: BUILDERS["account_created"](c),
    "security_alert": lambda c: ("Security notification · Vametra AI", _shell(
        "A security event on your account",
        f"<p>Hi {c.get('name','there')},</p><p>{c.get('message','We detected a security-related change on your account.')} "
        f"If this wasn't you, secure your account immediately.</p>",
        "Review account", f"{SITE}/account")),

    # ---- Events ----
    "submitted": lambda c: ("Your event submission was received", _shell(
        "We've received your event 🎉",
        f"<p>Hi {c.get('name','there')},</p><p>Thanks for submitting "
        f"<b>{c.get('eventName','your event')}</b> to the Vametra AI Expo &amp; Events Engine. "
        f"Reference: <b>{str(c.get('eventId',''))[:8].upper()}</b>.</p>"
        f"<p>Next: complete the listing payment to send it for admin review.</p>",
        "View my submission", f"{SITE}/expo/submit")),
    "payment_success": lambda c: ("Payment received — event under review", _shell(
        "Payment successful ✅",
        f"<p>Hi {c.get('name','there')},</p><p>We received your payment of "
        f"<b>{c.get('amountLabel','')}</b> for listing <b>{c.get('eventName','')}</b> "
        f"({c.get('durationDays',30)} days). Invoice: <b>{c.get('invoice','')}</b>.</p>"
        f"<p>Your event is queued for admin review. We'll email you once it's approved.</p>",
        "Track status", f"{SITE}/expo")),
    "under_review": lambda c: ("Your event is under review", _shell(
        "Under admin review 🔍",
        f"<p>Hi {c.get('name','there')},</p><p><b>{c.get('eventName','')}</b> is being reviewed for "
        f"quality and compliance. This usually takes less than 24 hours.</p>")),
    "approved": lambda c: ("Your event has been approved", _shell(
        "Approved! 🚀",
        f"<p>Hi {c.get('name','there')},</p><p><b>{c.get('eventName','')}</b> has been approved and will "
        f"now be published on the Vametra AI website and mobile app.</p>",
        "See it live", f"{SITE}/expo")),
    "published": lambda c: ("Your event is now live", _shell(
        "You're live 🌍",
        f"<p>Hi {c.get('name','there')},</p><p><b>{c.get('eventName','')}</b> is now published and visible "
        f"across the Vametra AI network until <b>{str(c.get('expiresAt',''))[:10]}</b>.</p>",
        "View listing", f"{SITE}/expo")),
    "rejected": lambda c: ("Update on your event submission", _shell(
        "Submission needs changes",
        f"<p>Hi {c.get('name','there')},</p><p>After review, <b>{c.get('eventName','')}</b> could not be "
        f"approved.</p><p><b>Reason:</b> {c.get('reason','Does not meet listing guidelines.')}</p>"
        f"<p>You're welcome to revise and resubmit; any payment is handled per our refund policy.</p>",
        "Resubmit", f"{SITE}/expo/submit")),
    "expiring": lambda c: ("Your event listing expires soon", _shell(
        "Expiring soon ⏳",
        f"<p>Hi {c.get('name','there')},</p><p>Your listing <b>{c.get('eventName','')}</b> expires on "
        f"<b>{str(c.get('expiresAt',''))[:10]}</b>. Renew to keep it visible.</p>",
        "Renew listing", f"{SITE}/expo/submit")),
    "expired": lambda c: ("Your event listing has expired", _shell(
        "Listing expired",
        f"<p>Hi {c.get('name','there')},</p><p>Your listing <b>{c.get('eventName','')}</b> has expired and "
        f"is no longer shown. You can relist anytime.</p>",
        "Relist", f"{SITE}/expo/submit")),

    # ---- Trade Command Center / Reports ----
    "report_generated": lambda c: ("Your trade report is ready", _shell(
        "Report generated ✅",
        f"<p>Hi {c.get('name','there')},</p><p>Your Trade Command Center report "
        f"<b>{c.get('reportTitle','')}</b> has been generated{(' · Invoice ' + c['invoice']) if c.get('invoice') else ''}. "
        f"You can view and download it anytime from your account.</p>",
        "Open my reports", f"{SITE}/account?tab=downloads")),
    "report_pdf": lambda c: ("Your trade report PDF", _shell(
        "Here's your report",
        f"<p>Hi {c.get('name','there')},</p><p>Attached / linked is your report "
        f"<b>{c.get('reportTitle','')}</b>. Thank you for using Vametra AI.</p>",
        "View report", c.get("reportUrl", f"{SITE}/account?tab=downloads"))),
    "shared_report": lambda c: (f"{c.get('sharedBy','A Vametra AI user')} shared a trade report with you", _shell(
        "A trade report was shared with you",
        f"<p>{c.get('sharedBy','A Vametra AI user')} shared the report <b>{c.get('reportTitle','')}</b> with you.</p>",
        "View report", c.get("reportUrl", SITE))),

    # ---- Payments / Subscriptions ----
    "subscription_success": _tpl_subscription_success,
    "admin_payment_alert": _tpl_admin_payment_alert,
    "payment_failed": lambda c: ("Your Vametra AI payment could not be completed", _shell(
        "Payment not completed",
        f"<p>Hi {c.get('name','there')},</p><p>We couldn't complete your recent payment for "
        f"<b>{c.get('item','your purchase')}</b>. No amount has been charged. Please try again.</p>",
        "Retry payment", f"{SITE}/account?tab=billing")),
    "renewal_reminder": lambda c: ("Your Vametra AI subscription renews soon", _shell(
        "Renewal reminder ⏳",
        f"<p>Hi {c.get('name','there')},</p><p>Your <b>{c.get('plan','')}</b> subscription expires on "
        f"<b>{str(c.get('until',''))[:10]}</b>. Renew to keep unlimited downloads.</p>",
        "Renew now", f"{SITE}/account?tab=billing")),

    # ---- Verified Buyers (VBIE) ----
    "buyers_added": lambda c: ("New verified buyers added to Vametra AI", _shell(
        "Fresh verified buyers are in 🌍",
        f"<p>Hi {c.get('name','there')},</p><p>We've just added <b>{c.get('count','new')}</b> newly "
        f"verified buyers to the Vametra AI Verified Buyer Intelligence Engine"
        f"{(' across ' + str(c.get('markets')) + ' markets') if c.get('markets') else ''}. "
        f"Sourced from {c.get('sources','official government trade sources')} and sanctions-screened.</p>"
        f"<p>Check the website or app for the latest buyer intelligence. Please note buyer records are "
        f"aggregated from public official sources — always verify details directly with the buyer before "
        f"doing business.</p>",
        "See new buyers", f"{SITE}/buyers")),
    "buyer_changed": lambda c: (f"Update on a buyer you're watching · {c.get('buyer','')}", _shell(
        "A buyer you watch just changed 🔔",
        f"<p>Hi there,</p><p>There's a new update on <b>{c.get('buyer','a buyer')}</b> that you're "
        f"watching in Vametra AI: <b>{c.get('summary','details changed')}</b>.</p>"
        f"<p>Open Vametra AI to review the latest verified intelligence.</p>",
        "View buyer", f"{SITE}/buyers/{c.get('geid','')}")),
    "weekly_report": lambda c: ("[Vametra AI] Weekly Intelligence Report", _shell(
        "Weekly VBIE Intelligence Summary 📊",
        f"<p>Here's this week's Verified Buyer Intelligence summary:</p>"
        f"<ul>"
        f"<li><b>{c.get('new_buyers',0)}</b> new buyers added</li>"
        f"<li><b>{c.get('updated',0)}</b> buyers updated</li>"
        f"<li><b>{c.get('merged',0)}</b> duplicates merged · <b>{c.get('removed',0)}</b> obsolete records removed</li>"
        f"<li><b>{c.get('dissolved',0)}</b> companies dissolved/inactive</li>"
        f"<li><b>{c.get('total',0)}</b> total verified buyers · LEI coverage <b>{c.get('lei_pct',0)}%</b></li>"
        f"</ul><p>Download the full report from the admin console.</p>",
        "Open admin", f"{SITE}/admin-cms")),

    # ---- Admin alerts ----
    "admin_new_submission": lambda c: ("[Vametra AI] New event submission", _shell(
        "New event submitted for review",
        f"<p>A new event listing needs review:</p><p><b>{c.get('eventName','')}</b><br/>"
        f"Country: {c.get('country','')} · Category: {c.get('category','')}<br/>"
        f"Contact: {c.get('contactName','')} ({c.get('contactEmail','')})</p>",
        "Open admin", f"{SITE}/admin-cms")),
    "admin_new_lead": lambda c: ("[Vametra AI] New lead captured", _shell(
        "New lead",
        f"<p>A new lead just came in:</p><p><b>{c.get('name','')}</b><br/>"
        f"{c.get('email','')} · {c.get('phone','')}<br/>Country: {c.get('country','')} · Source: {c.get('source','')}</p>",
        "View leads", f"{SITE}/admin-cms")),
    "admin_service_request": lambda c: ("[Vametra AI] New service request", _shell(
        "New service request",
        f"<p>A new service request was submitted:</p><p><b>{c.get('service','')}</b><br/>"
        f"{c.get('name','')} · {c.get('email','')} · {c.get('phone','')}<br/>Country: {c.get('country','')}</p>",
        "View requests", f"{SITE}/admin-cms")),
}


# ---------------- Core send ----------------
async def send(kind: str, to_email: Optional[str], ctx: dict = None):
    """Fire-and-forget branded email. Fails soft (never raises)."""
    ctx = ctx or {}
    if not to_email:
        return {"sent": False, "reason": "no recipient"}
    if kind not in BUILDERS:
        return {"sent": False, "reason": f"unknown template {kind}"}
    try:
        subject, html = BUILDERS[kind](ctx)
    except Exception as exc:
        logging.warning("Email template %s failed: %s", kind, exc)
        return {"sent": False, "error": str(exc)}
    if not RESEND_API_KEY:
        logging.info("[email:mock] %s -> %s (%s)", kind, to_email, subject)
        return {"sent": False, "mocked": True, "reason": "RESEND_API_KEY not set"}
    try:
        params = {"from": SENDER_EMAIL, "to": [to_email], "subject": subject, "html": html}
        res = await asyncio.to_thread(resend.Emails.send, params)
        return {"sent": True, "id": (res or {}).get("id")}
    except Exception as exc:
        # Retry once on Resend free-tier rate limit (2 req/s) so lifecycle emails don't drop.
        if "Too many requests" in str(exc) or "429" in str(exc):
            try:
                await asyncio.sleep(1.2)
                res = await asyncio.to_thread(resend.Emails.send, params)
                return {"sent": True, "id": (res or {}).get("id"), "retried": True}
            except Exception as exc2:
                exc = exc2
        logging.warning("Email send failed (%s -> %s): %s", kind, to_email, exc)
        return {"sent": False, "error": str(exc)}


async def notify_admin(kind: str, ctx: dict = None):
    """Send an admin alert to ADMIN_EMAIL (no-op if unset)."""
    if not ADMIN_EMAIL:
        logging.info("[email:admin skipped] %s (ADMIN_EMAIL unset)", kind)
        return {"sent": False, "reason": "ADMIN_EMAIL unset"}
    return await send(kind, ADMIN_EMAIL, ctx)


# Backwards-compatible alias used by the events module.
send_event_email = send
