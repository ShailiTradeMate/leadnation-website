"""LeadNation transactional email service (Resend).

Env-driven and NON-BLOCKING: if RESEND_API_KEY is missing the service logs and
no-ops so nothing breaks in preview/before keys arrive. Branded HTML templates
for the full event-listing lifecycle; reusable for future reports / subscriptions
/ account alerts. Shared by website + mobile app backends (same backend).
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
BRAND = "LeadNation"
SITE = os.environ.get("PUBLIC_SITE_URL", "https://leadnation.app")

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY


def _shell(title: str, body_html: str, cta_label: str = "", cta_url: str = "") -> str:
    year = datetime.now(timezone.utc).year
    cta = ""
    if cta_label and cta_url:
        cta = (f'<tr><td style="padding:8px 0 4px 0;"><a href="{cta_url}" '
               f'style="display:inline-block;background:#00C2FF;color:#04121f;font-weight:700;'
               f'text-decoration:none;padding:12px 24px;border-radius:10px;font-size:14px;">'
               f'{cta_label}</a></td></tr>')
    return f"""<!doctype html><html><body style="margin:0;background:#05070f;font-family:Arial,Helvetica,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#05070f;padding:28px 0;">
<tr><td align="center">
<table role="presentation" width="560" cellpadding="0" cellspacing="0" style="background:#0b1120;border:1px solid #1c2740;border-radius:16px;overflow:hidden;">
<tr><td style="padding:22px 32px;border-bottom:1px solid #1c2740;">
  <span style="font-size:18px;font-weight:800;color:#ffffff;">Lead<span style="color:#00C2FF;">Nation</span></span>
  <span style="font-size:10px;letter-spacing:3px;color:#5b6b86;text-transform:uppercase;display:block;margin-top:2px;">Global Trade Intelligence</span>
</td></tr>
<tr><td style="padding:30px 32px;">
  <h1 style="color:#ffffff;font-size:20px;margin:0 0 14px 0;">{title}</h1>
  <div style="color:#c3ccdd;font-size:14px;line-height:1.6;">{body_html}</div>
  <table role="presentation" cellpadding="0" cellspacing="0">{cta}</table>
</td></tr>
<tr><td style="padding:18px 32px;border-top:1px solid #1c2740;color:#5b6b86;font-size:11px;">
  &copy; {year} {BRAND}. You are receiving this because you interacted with LeadNation.<br/>
  <a href="{SITE}" style="color:#00C2FF;text-decoration:none;">{SITE.replace('https://','')}</a>
</td></tr>
</table></td></tr></table></body></html>"""


# ---- Event lifecycle templates ----
def _t_submitted(ctx):
    return ("Your event submission was received", _shell(
        "We've received your event 🎉",
        f"<p>Hi {ctx.get('name','there')},</p><p>Thanks for submitting "
        f"<b>{ctx.get('eventName','your event')}</b> to the LeadNation Expo &amp; Events Engine. "
        f"Your submission reference is <b>{ctx.get('eventId','')[:8].upper()}</b>.</p>"
        f"<p>Next step: complete the listing payment to send it for admin review.</p>",
        "View my submission", f"{SITE}/expo/submit"))


def _t_payment_success(ctx):
    return ("Payment received — event under review", _shell(
        "Payment successful ✅",
        f"<p>Hi {ctx.get('name','there')},</p><p>We received your payment of "
        f"<b>{ctx.get('amountLabel','')}</b> for listing <b>{ctx.get('eventName','')}</b> "
        f"({ctx.get('durationDays',30)} days). Invoice: <b>{ctx.get('invoice','')}</b>.</p>"
        f"<p>Your event is now queued for admin review. We'll email you once it's approved.</p>",
        "Track status", f"{SITE}/expo"))


def _t_under_review(ctx):
    return ("Your event is under review", _shell(
        "Under admin review 🔍",
        f"<p>Hi {ctx.get('name','there')},</p><p><b>{ctx.get('eventName','')}</b> is being "
        f"reviewed by our team for quality and compliance. This usually takes less than 24 hours.</p>"))


def _t_approved(ctx):
    return ("Your event has been approved", _shell(
        "Approved! 🚀",
        f"<p>Hi {ctx.get('name','there')},</p><p>Great news — <b>{ctx.get('eventName','')}</b> "
        f"has been approved and will now be published on the LeadNation website and mobile app.</p>",
        "See it live", f"{SITE}/expo"))


def _t_published(ctx):
    return ("Your event is now live", _shell(
        "You're live 🌍",
        f"<p>Hi {ctx.get('name','there')},</p><p><b>{ctx.get('eventName','')}</b> is now published "
        f"and visible to exporters, importers and buyers across the LeadNation network until "
        f"<b>{ctx.get('expiresAt','')[:10]}</b>.</p>",
        "View listing", f"{SITE}/expo"))


def _t_rejected(ctx):
    return ("Update on your event submission", _shell(
        "Submission needs changes",
        f"<p>Hi {ctx.get('name','there')},</p><p>After review, <b>{ctx.get('eventName','')}</b> "
        f"could not be approved.</p><p><b>Reason:</b> {ctx.get('reason','Does not meet listing guidelines.')}</p>"
        f"<p>You're welcome to revise and resubmit. Any listing payment will be handled per our refund policy.</p>",
        "Resubmit", f"{SITE}/expo/submit"))


def _t_expiring(ctx):
    return ("Your event listing expires soon", _shell(
        "Expiring soon ⏳",
        f"<p>Hi {ctx.get('name','there')},</p><p>Your listing <b>{ctx.get('eventName','')}</b> "
        f"expires on <b>{ctx.get('expiresAt','')[:10]}</b>. Renew to keep it visible.</p>",
        "Renew listing", f"{SITE}/expo/submit"))


def _t_expired(ctx):
    return ("Your event listing has expired", _shell(
        "Listing expired",
        f"<p>Hi {ctx.get('name','there')},</p><p>Your listing <b>{ctx.get('eventName','')}</b> "
        f"has expired and is no longer shown. You can relist anytime.</p>",
        "Relist", f"{SITE}/expo/submit"))


TEMPLATES = {
    "submitted": _t_submitted, "payment_success": _t_payment_success,
    "under_review": _t_under_review, "approved": _t_approved,
    "published": _t_published, "rejected": _t_rejected,
    "expiring": _t_expiring, "expired": _t_expired,
}


async def send_event_email(kind: str, to_email: Optional[str], ctx: dict):
    """Fire-and-forget branded email. No-ops gracefully if unconfigured."""
    if not to_email:
        return {"sent": False, "reason": "no recipient"}
    if kind not in TEMPLATES:
        return {"sent": False, "reason": "unknown template"}
    subject, html = TEMPLATES[kind](ctx or {})
    if not RESEND_API_KEY:
        logging.info("[email:mock] %s -> %s (%s)", kind, to_email, subject)
        return {"sent": False, "mocked": True, "reason": "RESEND_API_KEY not set"}
    try:
        params = {"from": SENDER_EMAIL, "to": [to_email], "subject": subject, "html": html}
        res = await asyncio.to_thread(resend.Emails.send, params)
        return {"sent": True, "id": (res or {}).get("id")}
    except Exception as exc:
        logging.warning("Email send failed (%s -> %s): %s", kind, to_email, exc)
        return {"sent": False, "error": str(exc)}
