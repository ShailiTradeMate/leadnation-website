"""LeadNation transactional email service (Resend) — production infrastructure.

Env-driven and NON-BLOCKING: if RESEND_API_KEY is missing the service logs and
no-ops so signup / payments / event submission / reports never break. Branded HTML
templates (Vametra AI Technologies Pvt Ltd · LeadNation) covering the full
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
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "LeadNation <onboarding@resend.dev>").strip()
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "").strip()
EMAIL_LOGO_URL = os.environ.get("EMAIL_LOGO_URL", "").strip()
SITE = os.environ.get("PUBLIC_SITE_URL", "https://leadnation.app").rstrip("/")

BRAND = "LeadNation"
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
  <div style="font-family:Georgia,'Times New Roman',serif;font-size:22px;font-weight:700;letter-spacing:-0.3px;color:#ffffff;">Lead<span style="color:#00C2FF;">Nation</span></div>
  <div style="font-family:Arial,Helvetica,sans-serif;font-size:10px;letter-spacing:2px;color:#6b7c99;text-transform:uppercase;margin-top:5px;">by Vametra AI Technologies Pvt Ltd</div>
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
  &copy; {year} {COMPANY}. All rights reserved. LeadNation is a product of {COMPANY}.<br/>
  <a href="{SITE}" style="color:#00C2FF;text-decoration:none;">{SITE.replace('https://', '')}</a>
</td></tr>
</table></td></tr></table></body></html>"""


def _amount_label(amount, currency):
    try:
        amount = float(amount)
    except Exception:
        return ""
    return f"\u20b9{amount:,.0f}" if str(currency).lower() == "inr" else f"${amount:,.2f}"


# ---------------- Templates (kind -> builder(ctx) -> (subject, html)) ----------------
def _b(name):
    return lambda c: BUILDERS[name](c)


BUILDERS = {
    # ---- User ----
    "account_created": lambda c: ("Welcome to LeadNation", _shell(
        "Your LeadNation account is ready 🎉",
        f"<p>Hi {c.get('name','there')},</p><p>Welcome aboard! Your Customer ID is "
        f"<b>{c.get('customerId','—')}</b>. Use it to sign in on the website and the LeadNation app "
        f"— one identity across both.</p><p>Start by building a Trade Command Center report or "
        f"exploring live trade intelligence.</p>",
        "Open LeadNation", SITE)),
    "welcome": lambda c: BUILDERS["account_created"](c),
    "security_alert": lambda c: ("Security notification · LeadNation", _shell(
        "A security event on your account",
        f"<p>Hi {c.get('name','there')},</p><p>{c.get('message','We detected a security-related change on your account.')} "
        f"If this wasn't you, secure your account immediately.</p>",
        "Review account", f"{SITE}/account")),

    # ---- Events ----
    "submitted": lambda c: ("Your event submission was received", _shell(
        "We've received your event 🎉",
        f"<p>Hi {c.get('name','there')},</p><p>Thanks for submitting "
        f"<b>{c.get('eventName','your event')}</b> to the LeadNation Expo &amp; Events Engine. "
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
        f"now be published on the LeadNation website and mobile app.</p>",
        "See it live", f"{SITE}/expo")),
    "published": lambda c: ("Your event is now live", _shell(
        "You're live 🌍",
        f"<p>Hi {c.get('name','there')},</p><p><b>{c.get('eventName','')}</b> is now published and visible "
        f"across the LeadNation network until <b>{str(c.get('expiresAt',''))[:10]}</b>.</p>",
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
        f"<b>{c.get('reportTitle','')}</b>. Thank you for using LeadNation.</p>",
        "View report", c.get("reportUrl", f"{SITE}/account?tab=downloads"))),
    "shared_report": lambda c: (f"{c.get('sharedBy','A LeadNation user')} shared a trade report with you", _shell(
        "A trade report was shared with you",
        f"<p>{c.get('sharedBy','A LeadNation user')} shared the report <b>{c.get('reportTitle','')}</b> with you.</p>",
        "View report", c.get("reportUrl", SITE))),

    # ---- Payments / Subscriptions ----
    "subscription_success": lambda c: ("Your LeadNation subscription is active", _shell(
        "Subscription active 🎉",
        f"<p>Hi {c.get('name','there')},</p><p>Your <b>{c.get('plan','')}</b> subscription is now active"
        f"{(' until <b>' + str(c.get('until',''))[:10] + '</b>') if c.get('until') else ''}. "
        f"Payment: <b>{c.get('amountLabel','')}</b>. Invoice: <b>{c.get('invoice','')}</b>.</p>"
        f"<p>You now have unlimited report downloads. Thank you for upgrading!</p>",
        "Manage billing", f"{SITE}/account?tab=billing")),
    "payment_failed": lambda c: ("Your LeadNation payment could not be completed", _shell(
        "Payment not completed",
        f"<p>Hi {c.get('name','there')},</p><p>We couldn't complete your recent payment for "
        f"<b>{c.get('item','your purchase')}</b>. No amount has been charged. Please try again.</p>",
        "Retry payment", f"{SITE}/account?tab=billing")),
    "renewal_reminder": lambda c: ("Your LeadNation subscription renews soon", _shell(
        "Renewal reminder ⏳",
        f"<p>Hi {c.get('name','there')},</p><p>Your <b>{c.get('plan','')}</b> subscription expires on "
        f"<b>{str(c.get('until',''))[:10]}</b>. Renew to keep unlimited downloads.</p>",
        "Renew now", f"{SITE}/account?tab=billing")),

    # ---- Admin alerts ----
    "admin_new_submission": lambda c: ("[LeadNation] New event submission", _shell(
        "New event submitted for review",
        f"<p>A new event listing needs review:</p><p><b>{c.get('eventName','')}</b><br/>"
        f"Country: {c.get('country','')} · Category: {c.get('category','')}<br/>"
        f"Contact: {c.get('contactName','')} ({c.get('contactEmail','')})</p>",
        "Open admin", f"{SITE}/admin-cms")),
    "admin_new_lead": lambda c: ("[LeadNation] New lead captured", _shell(
        "New lead",
        f"<p>A new lead just came in:</p><p><b>{c.get('name','')}</b><br/>"
        f"{c.get('email','')} · {c.get('phone','')}<br/>Country: {c.get('country','')} · Source: {c.get('source','')}</p>",
        "View leads", f"{SITE}/admin-cms")),
    "admin_service_request": lambda c: ("[LeadNation] New service request", _shell(
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
