from fastapi import APIRouter, Query, Header, HTTPException, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Any
from datetime import datetime, timezone
import uuid, io, csv, logging
from core import db, require_admin, ADMIN_TOKEN

router = APIRouter()


# ----- AI Assistant (mock) -----
class AiAskRequest(BaseModel):
    question: str


AI_RESPONSES = {
    "export": "Yes — most products can be exported with an IEC code, GST registration and applicable RCMC. The most efficient routes from India are via Mundra (West) and Chennai (South).",
    "document": "Standard export documents: Commercial Invoice, Packing List, Bill of Lading / AWB, Certificate of Origin, FTA Certificate (if applicable), Phytosanitary / Health Certificate, Letter of Credit and Insurance.",
    "country": "Best initial targets for Indian exporters: UAE (zero-duty CEPA), Saudi Arabia, USA (high volumes), Singapore (re-export gateway), UK (post-FTA), Australia (ECTA zero-duty on 96% goods).",
    "certification": "It depends on your product category — Food (FSSAI, APEDA, HACCP), Pharma (CDSCO, GMP), Textiles (Oeko-Tex), Engineering (CE / BIS), Cosmetics (GMP, ISO 22716).",
    "hsn": "Open our HSN Finder tool, paste your product name and description — we'll return the most likely codes with GST and RoDTEP info instantly.",
}


@router.post("/ai-ask")
async def ai_ask(payload: AiAskRequest):
    q = payload.question.lower()
    answer = None
    for k, v in AI_RESPONSES.items():
        if k in q:
            answer = v
            break
    if not answer:
        answer = (
            "Great question — based on LeadNation's compliance and trade data, the safest path is to start with an IEC code, "
            "identify your HS code, check applicable FTA benefits and validate your buyer market with our Buyer Discovery tool. "
            "Try one of the suggested prompts on the left for a more specific answer."
        )
    return {
        "question": payload.question,
        "answer": answer,
        "suggestedTools": [
            {"label": "HSN Finder", "to": "/tools/hsn-finder"},
            {"label": "Duty Calculator", "to": "/tools/duty-calculator"},
            {"label": "Find Buyers", "to": "/tools/find-buyers"},
        ],
        "isMock": True,
    }


