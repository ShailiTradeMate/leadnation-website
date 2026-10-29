from fastapi import APIRouter, Query, Header, HTTPException, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Any
from datetime import datetime, timezone
import uuid, io, csv, logging
from core import db, require_admin, ADMIN_TOKEN
from firebase_auth import optional_user

router = APIRouter()


# ----- Business Services -----
SERVICES_DB = {
    "rcmc-registration": {
        "slug": "rcmc-registration", "category": "Govt Documentation", "name": "RCMC Registration",
        "tagline": "Registration-cum-Membership Certificate · Required for export incentives.",
        "image": "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?auto=format&fit=crop&w=1200&q=80",
        "overview": "An RCMC certifies an exporter as a registered member of an Export Promotion Council (EPC) or Commodity Board. It's mandatory to claim DGFT export benefits (RoDTEP, MAI, etc.).",
        "benefits": ["Unlock DGFT export incentives", "Claim RoDTEP, MAI, RoSCTL scrips", "Get EPC support for trade fairs", "Recognised as a serious exporter"],
        "documents": ["IEC certificate", "GST registration certificate", "PAN of the business", "Business constitution proof (MOA / LLP agreement / partnership deed / Shop Act licence)", "Cancelled cheque or bank certificate", "Export turnover declaration (CA-certified, if any past exports)", "Digital signature (DSC) of authorised signatory"],
        "process": ["Choose the relevant EPC / Board", "Submit application + documents", "EPC verifies & issues certificate", "Receive RCMC within 7–10 days"],
        "faqs": [
            {"q": "Is RCMC mandatory?", "a": "Yes, to claim any DGFT export incentive you need a valid RCMC."},
            {"q": "How long is it valid?", "a": "5 years from the date of issue."},
            {"q": "What does the Vametra AI fee include?", "a": "One all-inclusive fee — council selection, application filing, document follow-ups and certificate delivery, with government and professional charges covered. No hidden extras."},
            {"q": "Can Vametra AI help me apply?", "a": "Yes — we assign a dedicated CA from our compliance team to handle end-to-end."},
        ],
        "priceFrom": "INR 4,999",
    },
    "gst-registration": {
        "slug": "gst-registration", "category": "Govt Documentation", "name": "GST Registration",
        "tagline": "GSTIN number · Mandatory for any business above ₹20L turnover.",
        "image": "https://images.unsplash.com/photo-1554224155-6726b3ff858f?auto=format&fit=crop&w=1200&q=80",
        "overview": "Goods & Services Tax (GST) registration is mandatory for businesses in India with turnover above the threshold or for any exporter claiming refund of input GST.",
        "benefits": ["Legally collect GST", "Claim Input Tax Credit", "Export with zero-rated GST (refund eligible)", "Open Current Account in business name"],
        "documents": ["PAN of the business / proprietor", "Aadhaar of proprietor / partners / directors", "Business address proof (electricity bill or rent agreement + owner NOC)", "Bank account proof (cancelled cheque / statement)", "Passport-size photographs", "Business constitution proof (partnership deed / incorporation certificate, if not a proprietorship)", "DSC + authorisation letter (companies / LLPs)"],
        "process": ["Collect KYC documents", "Submit GST REG-01 online", "Verification by GST officer", "GSTIN issued within 7 days"],
        "faqs": [
            {"q": "Do I need GST for exports?", "a": "Yes — exports are zero-rated, and you'll claim refund of input GST. Registration is essential."},
            {"q": "Can it be done online?", "a": "Yes. Vametra AI's CA team files online and tracks until GSTIN is issued."},
            {"q": "What's the timeline?", "a": "Usually 5–7 working days. We expedite via professional follow-ups."},
            {"q": "What does the Vametra AI fee include?", "a": "One all-inclusive fee — document review, GST REG-01 filing, officer queries handled and GSTIN delivery, with government and professional charges covered."},
        ],
        "priceFrom": "INR 1,499",
    },
    "iec-registration": {
        "slug": "iec-registration", "category": "Govt Documentation", "name": "IEC Registration",
        "tagline": "Import Export Code · Foundational requirement for international trade.",
        "image": "https://images.unsplash.com/photo-1573164713988-8665fc963095?auto=format&fit=crop&w=1200&q=80",
        "overview": "The Import Export Code (IEC) issued by DGFT is the 10-digit identifier required for any cross-border trade transaction. It is a one-time, lifetime registration.",
        "benefits": ["Mandatory for any import/export", "Required to receive foreign currency", "Required for shipping bill / bill of entry", "Linked to RoDTEP & other incentives"],
        "documents": ["PAN of the business / proprietor", "Aadhaar of proprietor / authorised signatory (Aadhaar-linked mobile for OTP)", "Business address proof (utility bill / rent agreement + NOC)", "Cancelled cheque or bank certificate (ANF-2A(I))", "Business constitution proof (partnership deed / incorporation certificate, if applicable)", "DSC (optional — Aadhaar e-sign works for most applicants)"],
        "process": ["Collect KYC documents", "File ANF-2A online on DGFT portal", "Pay government fees", "Receive IEC certificate by email"],
        "faqs": [
            {"q": "How long does it take?", "a": "Typically 1–3 working days with our team. Some cases need Aadhaar OTP verification."},
            {"q": "Is annual renewal required?", "a": "No, lifetime validity. But you must update it annually on DGFT portal."},
            {"q": "What does the Vametra AI fee include?", "a": "One all-inclusive fee — ANF-2A filing, Aadhaar/DSC verification support and IEC certificate delivery, with government and professional charges covered. Lifetime validity, no renewal fee."},
        ],
        "priceFrom": "INR 1,999",
    },
    "company-registration": {
        "slug": "company-registration", "category": "Govt Documentation", "name": "Company Registration (Shop Act / LLP / Pvt Ltd)",
        "tagline": "Pick the right structure · We register your business end-to-end.",
        "image": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1200&q=80",
        "overview": "We help you choose and register the right business entity — sole proprietorship (Shop & Establishment), LLP, OPC or Private Limited — based on your scale, funding plans and compliance comfort.",
        "benefits": ["Limited liability protection", "Easier to raise funding", "Tax planning advantages", "Brand & contract credibility"],
        "documents": ["PAN + Aadhaar of proprietor / partners / directors", "Registered office address proof + owner NOC", "Passport-size photographs"],
        "documentGroups": [
            {"title": "Shop Act (Sole Proprietorship · Shop & Establishment)", "items": [
                "PAN + Aadhaar of proprietor", "Passport-size photograph", "Shop / office address proof (electricity bill or rent agreement + owner NOC)",
                "Business name & nature of business", "Number of employees (if any)"]},
            {"title": "LLP (Limited Liability Partnership)", "items": [
                "DSC of designated partners", "DIN / DPIN of designated partners", "PAN + Aadhaar of all partners",
                "Address proof of partners (bank statement / utility bill, < 2 months old)", "Registered office proof + owner NOC",
                "LLP Agreement (drafted and filed within 30 days of incorporation)"]},
            {"title": "Private Limited / OPC", "items": [
                "DSC of all directors", "DIN of directors", "PAN + Aadhaar of directors and shareholders",
                "Address proof of directors (bank statement / utility bill, < 2 months old)", "Registered office proof + owner NOC",
                "MOA & AOA (drafted by us)", "Nominee consent — Form INC-3 (OPC only)"]},
        ],
        "entityOptions": ["Shop Act (Sole Proprietorship)", "LLP", "Private Limited", "OPC (One Person Company)", "Not sure — help me choose"],
        "process": ["Free 30-min strategy call to choose entity", "Name reservation (RUN / SPICe+ Part A) with MCA — not needed for Shop Act", "Documents collection & e-signing", "Shop Act licence in 1–3 days · LLP / Pvt Ltd incorporation certificate within 7–10 days"],
        "faqs": [
            {"q": "Which entity is best for exporters?", "a": "For most SME exporters: LLP or Pvt Ltd. We'll guide you in the strategy call."},
            {"q": "What does the Vametra AI fee include?", "a": "One all-inclusive fee per entity — Shop Act from ₹2,499 · LLP from ₹6,999 · Pvt Ltd from ₹9,999 — covering name reservation, drafting, filing, government and professional charges. Your CA confirms the exact package on the strategy call."},
            {"q": "Do you also handle compliance?", "a": "Yes — annual ROC filing, ITR, GSTR — we offer a full retainer."},
        ],
        "priceFrom": "INR 2,499",
    },
    "udyam-registration": {
        "slug": "udyam-registration", "category": "Govt Documentation", "name": "Udyam (MSME) Registration",
        "tagline": "Udyam Registration Number · Unlock MSME benefits, tenders and collateral-free credit.",
        "image": "https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&w=1200&q=80",
        "overview": "Udyam Registration is the Government of India's free, paperless MSME registration on udyamregistration.gov.in. It classifies your business as Micro, Small or Medium based on investment and turnover and is the gateway to every MSME scheme — priority-sector lending, delayed-payment protection and tender exemptions.",
        "benefits": ["Collateral-free loans under CGTMSE & priority-sector lending", "Protection against delayed payments (MSMED Act, 45-day rule)", "EMD / tender-fee exemptions in government procurement", "Subsidies on patents, ISO certification & electricity (state-wise)", "Easier access to export promotion schemes & trade-fair support", "Lifetime validity — no renewal, only annual self-update"],
        "documents": ["Aadhaar of proprietor / managing partner / director (Aadhaar-linked mobile for OTP)", "PAN of the business (and of the signatory)", "GSTIN (mandatory if your business is required to register for GST)", "Bank account number + IFSC", "Business address & date of commencement", "Main activity (manufacturing / services) & NIC codes", "Investment in plant & machinery and previous-year turnover (self-declared, auto-checked with ITR / GST)"],
        "process": ["Collect Aadhaar, PAN, GST & bank details", "File on udyamregistration.gov.in with Aadhaar OTP", "PAN / GST / ITR auto-validation by the portal", "Udyam Registration Number (URN) & certificate issued — usually same day"],
        "faqs": [
            {"q": "What does the Vametra AI fee include?", "a": "One all-inclusive fee — correct Micro/Small/Medium classification, NIC code selection, Aadhaar-OTP filing, PAN/GST validation checks and your Udyam certificate delivered, usually the same day."},
            {"q": "Is it needed for exporters?", "a": "Not mandatory, but strongly recommended: many export promotion schemes, bank export-credit lines and MAI/trade-fair subsidies prioritise Udyam-registered MSMEs."},
            {"q": "Do I need GST first?", "a": "Only if your business is legally required to register for GST. Businesses exempt from GST can register with PAN alone."},
            {"q": "Already have Udyog Aadhaar (UAM)?", "a": "UAM has been replaced — we migrate it to Udyam so your benefits continue uninterrupted."},
        ],
        "priceFrom": "INR 999",
    },
    "business-website": {
        "slug": "business-website", "category": "Govt Documentation", "name": "Business Website (Import–Export)",
        "tagline": "Complete website for your import-export business · Built, hosted and supported for a year.",
        "image": "https://images.unsplash.com/photo-1467232004584-a241de8bcf5d?auto=format&fit=crop&w=1200&q=80",
        "overview": "A done-for-you website package built specifically for import-export businesses. We handle everything from the brand name and domain to hosting, coding, payment integration, quality testing and a full year of support — so buyers can find, trust and contact you online.",
        "benefits": [
            "Business name suggestions (brand + domain availability)",
            "Domain selection and purchase guidance",
            "Business email creation on your own domain",
            "Hosting service setup and management",
            "Website design and development (fully coded, no templates locked to us)",
            "Product / catalogue pages built for exporters and importers",
            "Payment gateway integration",
            "Quality testing across mobile, tablet and desktop",
            "Basic SEO setup so buyers can find you on Google",
            "Annual support included",
            "Up to 15 content/design changes every month after go-live",
        ],
        "documents": ["Business name / brand preferences", "Company details & address", "Product catalogue or price list",
                      "Logo and images (we can design if you don't have any)", "IEC / GST (optional, for trust badges)"],
        "process": [
            "Discovery call — goals, products, target markets",
            "Name suggestions, domain selection and business email setup",
            "Design approval, then development + payment integration",
            "Quality testing and go-live on your hosting",
            "Annual support + up to 15 changes per month",
        ],
        "faqs": [
            {"q": "What does the annual fee cover?", "a": "Design and development, hosting setup, business email, payment integration, quality testing, annual support and up to 15 change requests per month after the site is live."},
            {"q": "Who owns the website and domain?", "a": "You do. The domain, hosting account and code are yours."},
            {"q": "How long does it take?", "a": "Most import-export websites go live in 2–4 weeks, depending on how quickly content and approvals come through."},
            {"q": "Is the price different outside India?", "a": "Yes — ₹35,000 per year for Indian businesses and USD 2,500 per year for international businesses."},
        ],
        "priceFrom": "INR 35,000 / year",
        "priceFromIntl": "USD 2,500 / year",
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
             "image": s["image"], **_prices(s, overrides)}
            for s in SERVICES_DB.values()]


def _prices(s: dict, overrides: dict) -> dict:
    """Resolve the live IN + INTL display prices for a service (admin overrides win)."""
    o = overrides.get(s["slug"])
    price_in = s.get("priceFrom", "")
    price_intl = s.get("priceFromIntl", "")
    if isinstance(o, str) and o.strip():
        price_in = o.strip()
    elif isinstance(o, dict):
        if (o.get("IN") or "").strip():
            price_in = o["IN"].strip()
        if (o.get("INTL") or "").strip():
            price_intl = o["INTL"].strip()
    return {"priceFrom": price_in, "priceFromIntl": price_intl}


async def _rate_overrides():
    doc = await db.site_settings.find_one({"_id": "site"}, {"serviceRates": 1})
    return (doc or {}).get("serviceRates", {}) or {}


@router.get("/services/admin/rates")
async def service_rates_admin(_: dict = Depends(require_admin)):
    """Editable Business Services pricing for the Admin CMS (Pricing → Business Services)."""
    overrides = await _rate_overrides()
    items = []
    for s in SERVICES_DB.values():
        live = _prices(s, overrides)
        items.append({
            "slug": s["slug"], "name": s["name"], "category": s["category"],
            "defaultPriceFrom": s.get("priceFrom", ""),
            "defaultPriceFromIntl": s.get("priceFromIntl", ""),
            "priceFrom": live["priceFrom"], "priceFromIntl": live["priceFromIntl"],
            "overridden": s["slug"] in overrides,
        })
    return {"items": items, "count": len(items)}


class ServiceRatesIn(BaseModel):
    rates: dict   # { slug: {"IN": "INR 35,000 / year", "INTL": "USD 2,500 / year"} }


@router.put("/services/admin/rates")
async def service_rates_save(body: ServiceRatesIn, admin: dict = Depends(require_admin)):
    clean = {}
    for slug, val in (body.rates or {}).items():
        if slug not in SERVICES_DB:
            continue
        if isinstance(val, str):
            val = {"IN": val}
        row = {}
        for r in ("IN", "INTL"):
            v = str((val or {}).get(r, "") or "").strip()
            if v:
                row[r] = v
        if row:
            clean[slug] = row
    await db.site_settings.update_one(
        {"_id": "site"},
        {"$set": {"serviceRates": clean,
                  "serviceRatesUpdatedAt": datetime.now(timezone.utc).isoformat(),
                  "serviceRatesUpdatedBy": admin.get("email") or admin.get("sub") or "admin"}},
        upsert=True)
    return await service_rates_admin(_=admin)


@router.get("/service/{slug}")
async def service_detail(slug: str):
    s = SERVICES_DB.get(slug)
    if not s:
        return JSONResponse(status_code=404, content={"error": "Service not found"})
    overrides = await _rate_overrides()
    return {**s, **_prices(s, overrides)}


class ServiceRequest(BaseModel):
    service: str
    name: str
    email: EmailStr
    phone: Optional[str] = None
    country: Optional[str] = "India"
    company: Optional[str] = None
    entity: Optional[str] = None
    message: Optional[str] = None


@router.post("/service-request")
async def submit_service_request(payload: ServiceRequest, user: Optional[dict] = Depends(optional_user)):
    doc = payload.model_dump()
    doc["id"] = str(uuid.uuid4())
    doc["status"] = "new"
    doc["assignedCa"] = None
    doc["createdAt"] = datetime.now(timezone.utc).isoformat()
    # Link the request to the logged-in account (not the typed email) so admin sees the real customer.
    account = {}
    if user:
        account = await db.do_users_cache.find_one({"uid": user.get("uid")}, {"_id": 0}) \
            or await db.do_users_cache.find_one({"email": (user.get("email") or "").lower()}, {"_id": 0}) or {}
        doc["userUid"] = user.get("uid")
        doc["accountEmail"] = account.get("email") or user.get("email")
        doc["customerId"] = account.get("customer_id")
    await db.service_requests.insert_one(doc)
    # also save in leads
    lead = {"id": str(uuid.uuid4()), "name": payload.name, "email": payload.email, "phone": payload.phone, "country": payload.country,
            "source": f"service:{payload.service}", "message": payload.message,
            "createdAt": datetime.now(timezone.utc).isoformat()}
    await db.leads.insert_one(lead)
    svc = SERVICES_DB.get(payload.service) or {}
    service_label = svc.get("name") or payload.service.replace("-", " ").title()
    if user:
        kyc = str(account.get("kyc_status") or account.get("verification_status") or "pending")
        profile_rows = [
            ("Logged-in as", doc.get("accountEmail")),
            ("Customer ID", account.get("customer_id")),
            ("KYC status", kyc),
            ("Plan", account.get("subscription_status")),
        ]
        profile_rows = [(k, v) for k, v in profile_rows if v]
    else:
        profile_rows = [("Account", "Submitted as guest (not logged in)")]
    doc["profileRows"] = [list(r) for r in profile_rows]
    doc["serviceLabel"] = service_label
    await db.service_requests.update_one({"id": doc["id"]}, {"$set": {"profileRows": doc["profileRows"], "serviceLabel": service_label}})
    from emailer import send, ADMIN_EMAIL
    await send("service_request", ADMIN_EMAIL, {
        "service": service_label, "requestId": doc["id"], "submittedAt": doc["createdAt"][:19].replace("T", " ") + " UTC",
        "name": payload.name, "email": str(payload.email), "phone": payload.phone,
        "company": payload.company, "country": payload.country, "message": payload.message, "entity": payload.entity,
        "profileRows": profile_rows,
    }, reply_to=str(payload.email))
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


