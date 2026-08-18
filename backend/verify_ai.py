"""AI vision analysis for the Verified Buyer flow (REFERENCE implementation).

Uses the Emergent Universal LLM key (multimodal) to:
  - assess whether a selfie is a real photo of a live human (anti AI-fake / quality)
  - OCR + field-extract a business document and cross-check against the profile

Fails soft: returns a low-confidence "needs_review" style result on any error so
the pipeline never hard-crashes. The DigitalOcean identity backend team can mirror
this exact logic (Google Vision / their own vision model) on their side.
"""
import os
import json
import logging

_KEY = os.environ.get("EMERGENT_LLM_KEY")
_PROVIDER = os.environ.get("VERIFY_AI_PROVIDER", "openai").lower()
_MODEL = os.environ.get("VERIFY_AI_MODEL", "gpt-5.4")  # vision-capable
if _PROVIDER == "mock":
    _PROVIDER = "openai"

log = logging.getLogger("verify_ai")


def _parse_json(raw: str):
    if not raw:
        return None
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.lower().startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    try:
        return json.loads(raw)
    except Exception:
        try:
            start = raw.find("{")
            end = raw.rfind("}")
            return json.loads(raw[start:end + 1])
        except Exception:
            return None


async def _analyze(image_b64: str, system: str, prompt: str, session: str):
    """One-shot multimodal call → parsed JSON dict (or None on failure)."""
    if not _KEY:
        return None
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
        chat = LlmChat(api_key=_KEY, session_id=session, system_message=system).with_model(_PROVIDER, _MODEL)
        msg = UserMessage(
            text=prompt + "\n\nRespond with STRICT JSON only. No markdown, no prose.",
            file_contents=[ImageContent(image_base64=image_b64)],
        )
        out = await chat.send_message(msg)
        return _parse_json(out or "")
    except Exception as exc:
        log.warning("vision analyze failed: %s", exc)
        return None


SELFIE_SYSTEM = (
    "You are a strict identity-verification vision analyst. You inspect a selfie/portrait "
    "and judge whether it is a genuine photograph of a real, live human being — not an "
    "AI-generated / deepfake / cartoon / screen-recapture / printed-photo image. Be conservative."
)

SELFIE_PROMPT = (
    "Analyse this image for identity verification. Return JSON with EXACTLY these keys:\n"
    "{\n"
    '  "is_human_face": boolean,            // a real human face is clearly visible\n'
    '  "face_count": integer,               // number of distinct human faces\n'
    '  "ai_generated_likelihood": number,   // 0..1, how likely it is AI-generated/deepfake\n'
    '  "recapture_likelihood": number,      // 0..1, likelihood it is a photo-of-a-screen or printed photo\n'
    '  "quality_score": number,             // 0..1, sharpness/lighting/framing good enough to verify\n'
    '  "liveness_ok": boolean,              // looks like a live in-the-moment capture (best-effort)\n'
    '  "confidence_real_person": number,    // 0..1 overall confidence this is a real, unique live person\n'
    '  "reasons": [string]                  // short bullet reasons for the scores\n'
    "}"
)

DOC_SYSTEM = (
    "You are a business-document verification analyst. You read a photo/scan of a company "
    "or trade document, extract key fields, and judge legitimacy. Never invent values — use "
    "null when a field is not clearly present."
)


def doc_prompt(expected_name: str, expected_country: str) -> str:
    return (
        "Read this business/trade document and return JSON with EXACTLY these keys:\n"
        "{\n"
        '  "is_business_document": boolean,\n'
        '  "document_type": string,          // e.g. GST certificate, IEC, incorporation, trade license\n'
        '  "company_name": string|null,\n'
        '  "registration_number": string|null,\n'
        '  "address": string|null,\n'
        '  "country": string|null,\n'
        '  "legible": boolean,\n'
        '  "tamper_signs": boolean,          // visible editing/forgery signs\n'
        '  "confidence": number,             // 0..1 overall document legitimacy\n'
        '  "extracted_text_summary": string\n'
        "}\n\n"
        f"For cross-checking, the applicant states their company/name is: \"{expected_name or 'unknown'}\" "
        f"and country: \"{expected_country or 'unknown'}\". Judge the document on its own merits; "
        "do not force a match."
    )


async def analyze_selfie(image_b64: str, session: str = "verify-selfie") -> dict:
    r = await _analyze(image_b64, SELFIE_SYSTEM, SELFIE_PROMPT, session)
    if not r:
        return {"available": False, "is_human_face": False, "ai_generated_likelihood": 0.5,
                "quality_score": 0.0, "liveness_ok": False, "confidence_real_person": 0.0,
                "reasons": ["AI analysis unavailable — routed to manual review."]}
    r["available"] = True
    return r


async def analyze_document(image_b64: str, expected_name: str = "", expected_country: str = "",
                           session: str = "verify-doc") -> dict:
    r = await _analyze(image_b64, DOC_SYSTEM, doc_prompt(expected_name, expected_country), session)
    if not r:
        return {"available": False, "is_business_document": False, "document_type": None,
                "company_name": None, "confidence": 0.0,
                "extracted_text_summary": "AI analysis unavailable — routed to manual review."}
    r["available"] = True
    return r
