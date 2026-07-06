from fastapi import APIRouter, Query, Header, HTTPException, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Any
from datetime import datetime, timezone
import uuid, io, csv, logging
from core import db, require_admin, ADMIN_TOKEN

router = APIRouter()


# ----- Business Services -----
SERVICES_DB = {
    "rcmc-registration": {
        "slug": "rcmc-registration", "category": "Govt Documentation", "name": "RCMC Registration",
        "tagline": "Registration-cum-Membership Certificate · Required for export incentives.",
        "image": "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?auto=format&fit=crop&w=1200&q=80",
        "overview": "An RCMC certifies an exporter as a registered member of an Export Promotion Council (EPC) or Commodity Board. It's mandatory to claim DGFT export benefits (RoDTEP, MAI, etc.).",
        "benefits": ["Unlock DGFT export incentives", "Claim RoDTEP, MAI, RoSCTL scrips", "Get EPC support for trade fairs", "Recognised as a serious exporter"],
        "documents": ["IEC certificate", "GST registration", "PAN card", "Cancelled cheque", "MOA / Partnership deed", "Bank certificate"],
        "process": ["Choose the relevant EPC / Board", "Submit application + documents", "EPC verifies & issues certificate", "Receive RCMC within 7–10 days"],
        "faqs": [
            {"q": "Is RCMC mandatory?", "a": "Yes, to claim any DGFT export incentive you need a valid RCMC."},
            {"q": "How long is it valid?", "a": "5 years from the date of issue."},
            {"q": "Can LeadNation help me apply?", "a": "Yes — we assign a dedicated CA from our compliance team to handle end-to-end."},
        ],
        "priceFrom": "INR 4,999",
    },
    "gst-registration": {
        "slug": "gst-registration", "category": "Govt Documentation", "name": "GST Registration",
        "tagline": "GSTIN number · Mandatory for any business above ₹20L turnover.",
        "image": "https://images.unsplash.com/photo-1554224155-6726b3ff858f?auto=format&fit=crop&w=1200&q=80",
        "overview": "Goods & Services Tax (GST) registration is mandatory for businesses in India with turnover above the threshold or for any exporter claiming refund of input GST.",
        "benefits": ["Legally collect GST", "Claim Input Tax Credit", "Export with zero-rated GST (refund eligible)", "Open Current Account in business name"],
        "documents": ["PAN card", "Aadhaar of proprietor / partners", "Business address proof", "Bank account proof", "Photographs"],
        "process": ["Collect KYC documents", "Submit GST REG-01 online", "Verification by GST officer", "GSTIN issued within 7 days"],
        "faqs": [
            {"q": "Do I need GST for exports?", "a": "Yes — exports are zero-rated, and you'll claim refund of input GST. Registration is essential."},
            {"q": "Can it be done online?", "a": "Yes. LeadNation's CA team files online and tracks until GSTIN is issued."},
            {"q": "What's the timeline?", "a": "Usually 5–7 working days. We expedite via professional follow-ups."},
        ],
        "priceFrom": "INR 1,499",
    },
    "iec-registration": {
        "slug": "iec-registration", "category": "Govt Documentation", "name": "IEC Registration",
        "tagline": "Import Export Code · Foundational requirement for international trade.",
        "image": "https://images.unsplash.com/photo-1573164713988-8665fc963095?auto=format&fit=crop&w=1200&q=80",
        "overview": "The Import Export Code (IEC) issued by DGFT is the 10-digit identifier required for any cross-border trade transaction. It is a one-time, lifetime registration.",
        "benefits": ["Mandatory for any import/export", "Required to receive foreign currency", "Required for shipping bill / bill of entry", "Linked to RoDTEP & other incentives"],
        "documents": ["PAN card", "Aadhaar of proprietor", "Address proof (utility bill)", "Bank certificate / cancelled cheque", "Digital signature (if applicable)"],
        "process": ["Collect KYC documents", "File ANF-2A online on DGFT portal", "Pay government fees", "Receive IEC certificate by email"],
        "faqs": [
            {"q": "How long does it take?", "a": "Typically 1–3 working days with our team. Some cases need Aadhaar OTP verification."},
            {"q": "Is annual renewal required?", "a": "No, lifetime validity. But you must update it annually on DGFT portal."},
            {"q": "What's the cost?", "a": "Government fee INR 500 + LeadNation professional fee."},
        ],
        "priceFrom": "INR 1,999",
    },
    "company-registration": {
        "slug": "company-registration", "category": "Govt Documentation", "name": "Company Registration (Shop Act / LLP / Pvt Ltd)",
        "tagline": "Pick the right structure · We register your business end-to-end.",
        "image": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1200&q=80",
        "overview": "We help you choose and register the right business entity — sole proprietorship (Shop & Establishment), LLP, OPC or Private Limited — based on your scale, funding plans and compliance comfort.",
        "benefits": ["Limited liability protection", "Easier to raise funding", "Tax planning advantages", "Brand & contract credibility"],
        "documents": ["DIN / DSC for directors", "PAN + Aadhaar of directors", "Registered office address proof", "MOA / AOA drafting (Pvt Ltd)", "Partnership deed (LLP)"],
        "process": ["Free 30-min strategy call to choose entity", "Name reservation with MCA", "Documents collection & e-signing", "Incorporation certificate within 7–10 days"],
        "faqs": [
            {"q": "Which entity is best for exporters?", "a": "For most SME exporters: LLP or Pvt Ltd. We'll guide you in the strategy call."},
            {"q": "What is the cost?", "a": "Depends on entity — Shop Act from ₹2,499 · LLP from ₹6,999 · Pvt Ltd from ₹9,999. Includes government + professional fees."},
            {"q": "Do you also handle compliance?", "a": "Yes — annual ROC filing, ITR, GSTR — we offer a full retainer."},
        ],
        "priceFrom": "INR 2,499",
    },
    "export-consulting": {
        "slug": "export-consulting", "category": "Consulting", "name": "Export Consulting",
        "tagline": "Strategy + execution for first-time exporters.",
        "image": "https://images.unsplash.com/photo-1605902711622-cfb43c4437b5?auto=format&fit=crop&w=1200&q=80",
        "overview": "Our certified export consultants help you go from idea to first shipment — market selection, buyer outreach, pricing, documentation, logistics and incentive claims.",
        "benefits": ["1:1 consultant assigned", "Market entry roadmap", "Pricing & costing template", "Buyer outreach playbook"],
        "documents": ["Product spec sheet", "Business profile", "Target markets / countries (if any)"],
        "process": ["Discovery call (30 min)", "Market & opportunity report (5 days)", "Setup IEC/RCMC/GST as needed", "Buyer outreach + first shipment support"],
        "faqs": [{"q": "Is this a one-time service?", "a": "We offer one-time and retainer packages. Most exporters start with a one-time onboarding."}],
        "priceFrom": "INR 14,999",
    },
    "import-consulting": {
        "slug": "import-consulting", "category": "Consulting", "name": "Import Consulting",
        "tagline": "Source globally · Land profitably.",
        "image": "https://images.unsplash.com/photo-1494412519320-aa613dfb7738?auto=format&fit=crop&w=1200&q=80",
        "overview": "Sourcing, supplier vetting, contract negotiation, customs clearance and landed-cost optimisation for Indian importers.",
        "benefits": ["Verified supplier shortlist", "Negotiation support", "Customs clearance handled", "Landed cost optimisation"],
        "documents": ["Product spec", "Budget & MOQ", "Target ports"],
        "process": ["Discovery call", "Supplier shortlist (within 5 days)", "Negotiation & sample order", "Bulk PO + clearance"],
        "faqs": [{"q": "Do you handle customs?", "a": "Yes — our partner CHA network clears at all major Indian ports."}],
        "priceFrom": "INR 14,999",
    },
    "compliance-consulting": {
        "slug": "compliance-consulting", "category": "Consulting", "name": "Compliance Consulting",
        "tagline": "Audit-proof your trade operations.",
        "image": "https://images.unsplash.com/photo-1497436072909-60f360e1d4b1?auto=format&fit=crop&w=1200&q=80",
        "overview": "End-to-end compliance support — DGFT, customs, GST, CBAM (EU), FDA (USA), ESG. Pass any audit, win any tender.",
        "benefits": ["Audit-ready records", "CBAM / FDA / REACH dossiers", "Quarterly compliance health-check"],
        "documents": ["Last 12 months' shipping bills", "GST returns", "Quality certifications"],
        "process": ["Compliance audit (1 week)", "Gap closure plan", "Documentation upgrade", "Quarterly reviews"],
        "faqs": [{"q": "Do you cover EU CBAM?", "a": "Yes — we prepare embedded-carbon reports and CBAM declarations."}],
        "priceFrom": "INR 24,999",
    },
    "market-entry": {
        "slug": "market-entry", "category": "Consulting", "name": "Market Entry",
        "tagline": "Validated market entry plans for any country.",
        "image": "https://images.unsplash.com/photo-1488229297570-58520851e868?auto=format&fit=crop&w=1200&q=80",
        "overview": "Country-specific market entry — demand validation, competitor mapping, distributor shortlist, regulatory clearance and a 90-day go-to-market plan.",
        "benefits": ["Local distributor shortlist", "Regulatory clearance plan", "Pricing benchmarks", "90-day GTM roadmap"],
        "documents": ["Product profile", "Target country", "Budget"],
        "process": ["Country selection workshop", "Field research (2 weeks)", "GTM report", "Distributor introductions"],
        "faqs": [{"q": "Which countries do you cover?", "a": "All GCC, USA, UK, EU, ASEAN, Australia, LATAM. New geographies on request."}],
        "priceFrom": "INR 49,999",
    },
    "product-sourcing": {
        "slug": "product-sourcing", "category": "Consulting", "name": "Product Sourcing",
        "tagline": "Find the right product, supplier and price.",
        "image": "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?auto=format&fit=crop&w=1200&q=80",
        "overview": "Sourcing service for importers and private-label brands — supplier vetting, sample management, quality inspection and shipping coordination.",
        "benefits": ["Vetted supplier shortlist", "Sample management", "Third-party inspection", "Best-in-class pricing"],
        "documents": ["Product spec", "MOQ", "Target landed cost"],
        "process": ["Brief", "Supplier shortlist", "Sample order", "Bulk order + QC"],
        "faqs": [{"q": "How do you ensure quality?", "a": "Third-party inspections at factory before dispatch + photo + video evidence."}],
        "priceFrom": "INR 19,999",
    },
    "buyer-discovery-service": {
        "slug": "buyer-discovery-service", "category": "Consulting", "name": "Buyer Discovery Service",
        "tagline": "Done-for-you buyer outreach in 6 weeks.",
        "image": "https://images.unsplash.com/photo-1521737711867-e3b97375f902?auto=format&fit=crop&w=1200&q=80",
        "overview": "Our team handles target list research, multi-channel outreach (email + WhatsApp + LinkedIn) and meeting scheduling so you can focus on closing.",
        "benefits": ["100+ qualified buyer leads", "Outreach across 3 channels", "Meeting scheduling", "Performance dashboard"],
        "documents": ["Product profile", "Target markets", "Ideal buyer persona"],
        "process": ["Onboarding call", "Target list & sequences (week 1)", "Outreach (weeks 2–5)", "Meetings + reporting (week 6)"],
        "faqs": [{"q": "Guaranteed meetings?", "a": "We guarantee a minimum of 10 qualified meetings per 6-week cycle."}],
        "priceFrom": "INR 39,999 / month",
    },
}


@router.get("/services")
async def services_list():
    overrides = await _rate_overrides()
    return [{"slug": s["slug"], "name": s["name"], "category": s["category"], "tagline": s["tagline"],
             "image": s["image"], "priceFrom": overrides.get(s["slug"], s["priceFrom"])}
            for s in SERVICES_DB.values()]


async def _rate_overrides():
    doc = await db.site_settings.find_one({"_id": "site"}, {"serviceRates": 1})
    return (doc or {}).get("serviceRates", {}) or {}


@router.get("/service/{slug}")
async def service_detail(slug: str):
    s = SERVICES_DB.get(slug)
    if not s:
        return JSONResponse(status_code=404, content={"error": "Service not found"})
    overrides = await _rate_overrides()
    if slug in overrides:
        s = {**s, "priceFrom": overrides[slug]}
    return s


class ServiceRequest(BaseModel):
    service: str
    name: str
    email: EmailStr
    phone: Optional[str] = None
    country: Optional[str] = "India"
    company: Optional[str] = None
    message: Optional[str] = None


@router.post("/service-request")
async def submit_service_request(payload: ServiceRequest):
    doc = payload.model_dump()
    doc["id"] = str(uuid.uuid4())
    doc["status"] = "new"
    doc["assignedCa"] = None
    doc["createdAt"] = datetime.now(timezone.utc).isoformat()
    await db.service_requests.insert_one(doc)
    # also save in leads
    lead = {"id": str(uuid.uuid4()), "name": payload.name, "email": payload.email, "phone": payload.phone, "country": payload.country,
            "source": f"service:{payload.service}", "message": payload.message,
            "createdAt": datetime.now(timezone.utc).isoformat()}
    await db.leads.insert_one(lead)
    from emailer import notify_admin
    await notify_admin("admin_service_request", {
        "service": payload.service, "name": payload.name, "email": payload.email,
        "phone": payload.phone, "country": payload.country})
    return {"ok": True, "id": doc["id"]}


# ----- Directories -----
DIRECTORY_DB = {
    "exporters": [
        {"name": "KRBL Limited", "city": "New Delhi", "country": "IN", "category": "Basmati Rice", "verified": True, "since": 1889},
        {"name": "Cipla Exports", "city": "Mumbai", "country": "IN", "category": "Pharmaceuticals", "verified": True, "since": 1935},
        {"name": "Welspun Cotton", "city": "Anjar", "country": "IN", "category": "Home Textiles", "verified": True, "since": 1985},
        {"name": "Mysore Sandal Soaps", "city": "Bengaluru", "country": "IN", "category": "FMCG", "verified": True, "since": 1916},
        {"name": "ITC Spices", "city": "Cochin", "country": "IN", "category": "Spices", "verified": True, "since": 1910},
        {"name": "Mahindra Auto Components", "city": "Pune", "country": "IN", "category": "Auto Parts", "verified": True, "since": 1945},
    ],
    "importers": [
        {"name": "Gulf Imports LLC", "city": "Dubai", "country": "AE", "category": "Food & FMCG", "verified": True, "since": 2002},
        {"name": "Riyadh Trading Co.", "city": "Riyadh", "country": "SA", "category": "Food & Beverage", "verified": True, "since": 1988},
        {"name": "Sunrise Distributors", "city": "Houston", "country": "US", "category": "Multi-sector", "verified": True, "since": 1995},
        {"name": "British Foods PLC", "city": "London", "country": "GB", "category": "Food & Spices", "verified": True, "since": 1965},
        {"name": "Sydney Imports Pty", "city": "Sydney", "country": "AU", "category": "Multi-sector", "verified": True, "since": 2010},
        {"name": "Singapore Trade Hub", "city": "Singapore", "country": "SG", "category": "Re-export", "verified": True, "since": 1998},
    ],
    "suppliers": [
        {"name": "Tirupur Knit Mills", "city": "Tirupur", "country": "IN", "category": "Garments", "verified": True, "since": 1992},
        {"name": "Surat Diamond Polishing", "city": "Surat", "country": "IN", "category": "Gems & Jewellery", "verified": True, "since": 1978},
        {"name": "Coimbatore Engineering Works", "city": "Coimbatore", "country": "IN", "category": "Engineering", "verified": True, "since": 1965},
        {"name": "Moradabad Brassware", "city": "Moradabad", "country": "IN", "category": "Handicrafts", "verified": True, "since": 1880},
        {"name": "Ludhiana Cycle Parts", "city": "Ludhiana", "country": "IN", "category": "Auto Parts", "verified": True, "since": 1947},
    ],
    "cha": [
        {"name": "Mundra Customs Brokers", "city": "Mundra", "country": "IN", "category": "Sea + Air", "verified": True, "since": 2002, "licence": "11/CHA/2002"},
        {"name": "Chennai Cargo Clearance", "city": "Chennai", "country": "IN", "category": "Sea + Air", "verified": True, "since": 1995, "licence": "07/CHA/1995"},
        {"name": "Delhi Logistics Hub", "city": "New Delhi", "country": "IN", "category": "Air + ICD", "verified": True, "since": 2008, "licence": "21/CHA/2008"},
        {"name": "Nhava Sheva Brokers Co.", "city": "Mumbai", "country": "IN", "category": "Sea", "verified": True, "since": 1988, "licence": "02/CHA/1988"},
    ],
    "export-agents": [
        {"name": "Asia Bridge Exports", "city": "Singapore", "country": "SG", "category": "FMCG · Pharma", "verified": True, "since": 2015},
        {"name": "Middle East Trade Partners", "city": "Dubai", "country": "AE", "category": "GCC · Food", "verified": True, "since": 2010},
        {"name": "Atlantic Sourcing", "city": "London", "country": "GB", "category": "UK · EU", "verified": True, "since": 2005},
        {"name": "Pacific Reach", "city": "Sydney", "country": "AU", "category": "Australia · NZ", "verified": True, "since": 2018},
    ],
}


@router.get("/directory/{kind}")
async def directory(kind: str, q: str = "", country: str = ""):
    items = DIRECTORY_DB.get(kind)
    if items is None:
        raise HTTPException(status_code=404, detail="Unknown directory")
    res = items
    if q:
        ql = q.lower()
        res = [i for i in res if ql in i["name"].lower() or ql in i["category"].lower() or ql in i["city"].lower()]
    if country:
        res = [i for i in res if i["country"].upper() == country.upper()]
    return {"kind": kind, "total": len(res), "items": res, "lockedExtras": True}


