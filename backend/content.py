from fastapi import APIRouter, Query, Header, HTTPException, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Any
from datetime import datetime, timezone
import uuid, io, csv, logging
from core import db, require_admin, ADMIN_TOKEN

router = APIRouter()


# ----- Products (rich) -----
PRODUCTS_DB = {
    "basmati-rice": {
        "slug": "basmati-rice", "name": "Basmati Rice", "hsn": "10063020", "image": "https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=1200&q=80",
        "overview": "India is the world's #1 exporter of Basmati rice — controlling ~75% of global supply. The aromatic long-grain variety is GI-protected and commands a premium of 14% over regular long-grain.",
        "topExporters": ["India", "Pakistan"],
        "topImporters": ["Saudi Arabia", "Iran", "Iraq", "UAE", "USA"],
        "demand": "$5.4B annual global demand, growing 6% YoY.",
        "opportunities": ["GI-tagged origin variants", "Private-label for GCC retail", "Premium organic in EU / USA"],
        "compliance": ["APEDA RCMC", "Phytosanitary", "ISO 22000", "Halal"],
        "certifications": ["APEDA", "Organic NPOP", "Halal", "Kosher"],
        "logistics": "Mundra port preferred. 21-day transit to GCC; 35-day to USA East coast.",
        "category": "Agriculture & Food",
        "relatedCorridors": ["india-to-uae", "india-to-usa"],
    },
    "agarbatti": {
        "slug": "agarbatti", "name": "Agarbatti (Incense Sticks)", "hsn": "33074100", "image": "https://images.unsplash.com/photo-1602874801007-bd45867d505b?auto=format&fit=crop&w=1200&q=80",
        "overview": "Indian agarbatti dominates 90% of global market share. Cities like Bengaluru, Ahmedabad and Mysore are global production hubs.",
        "topExporters": ["India", "Vietnam", "China"],
        "topImporters": ["USA", "UAE", "Malaysia", "UK", "Nigeria"],
        "demand": "$850M global, growing 9% YoY.",
        "opportunities": ["Premium fragrance variants for Western markets", "Halal-certified for GCC", "Private-label drop-shipping"],
        "compliance": ["EPCH RCMC", "MSDS for ingredients", "Halal certificate"],
        "certifications": ["EPCH", "Halal", "FSC paper rolls"],
        "logistics": "Air freight common for smaller orders; FCL for large retailers.",
        "category": "FMCG",
        "relatedCorridors": ["india-to-uae", "india-to-usa"],
    },
    "spices": {
        "slug": "spices", "name": "Indian Spices", "hsn": "09042190", "image": "https://images.unsplash.com/photo-1596797038530-2c107229654b?auto=format&fit=crop&w=1200&q=80",
        "overview": "India is the largest producer, consumer and exporter of spices. Turmeric, cumin, coriander, cardamom and chilli dominate the basket.",
        "topExporters": ["India", "China", "Vietnam"],
        "topImporters": ["USA", "China", "UAE", "Thailand", "UK"],
        "demand": "$4.1B Indian export turnover.",
        "opportunities": ["Organic + ESG-certified spices", "Private-label blends", "Single-origin GI variants"],
        "compliance": ["Spices Board mandatory registration", "FSSAI", "EU pesticide MRL compliance"],
        "certifications": ["Spices Board", "Organic NPOP", "USDA Organic", "Fairtrade"],
        "logistics": "Cochin, Tuticorin and Mundra dominate spice exports.",
        "category": "Agriculture & Food",
        "relatedCorridors": ["india-to-uae", "india-to-usa"],
    },
    "textiles": {
        "slug": "textiles", "name": "Cotton Textiles & Apparel", "hsn": "62034299", "image": "https://images.unsplash.com/photo-1558769132-cb1aea458c5e?auto=format&fit=crop&w=1200&q=80",
        "overview": "India is the world's 2nd largest textile producer with a $44B export economy. Tirupur, Surat and Ludhiana power the value chain.",
        "topExporters": ["China", "India", "Bangladesh", "Vietnam"],
        "topImporters": ["USA", "EU", "UAE", "UK", "Japan"],
        "demand": "$44B Indian export; global apparel market $1.7T.",
        "opportunities": ["Sustainable cotton + GOTS premium", "Private-label for fast fashion", "Athleisure + recycled fibre"],
        "compliance": ["AEPC RCMC", "RoSCTL", "Oeko-Tex", "GOTS for organic"],
        "certifications": ["AEPC", "Oeko-Tex", "GOTS", "BCI"],
        "logistics": "Chennai and Mundra are primary apparel ports.",
        "category": "Textiles & Apparel",
        "relatedCorridors": ["india-to-usa", "india-to-uae"],
    },
    "pharmaceuticals": {
        "slug": "pharmaceuticals", "name": "Pharmaceuticals", "hsn": "30049099", "image": "https://images.unsplash.com/photo-1631549916768-4119b2e5f926?auto=format&fit=crop&w=1200&q=80",
        "overview": "India is the world's 3rd largest pharma exporter ($28B). 60% of global vaccines and 40% of US generics come from Indian factories.",
        "topExporters": ["USA", "Germany", "Switzerland", "India"],
        "topImporters": ["USA", "EU", "Africa", "ASEAN"],
        "demand": "$28B Indian pharma exports; $1.5T global market.",
        "opportunities": ["Biosimilars to USA + EU", "CDMO contracts", "Generic export to Africa"],
        "compliance": ["CDSCO", "USFDA approval for USA", "EMA for EU", "WHO GMP"],
        "certifications": ["WHO GMP", "USFDA", "EU GMP", "Pharmexcil"],
        "logistics": "Cold chain critical — Hyderabad and Mumbai are pharma hubs.",
        "category": "Pharmaceuticals",
        "relatedCorridors": ["india-to-usa"],
    },
}


@router.get("/products-catalog")
async def products_catalog():
    return [{"slug": p["slug"], "name": p["name"], "hsn": p["hsn"], "image": p["image"], "category": p["category"]} for p in PRODUCTS_DB.values()]


@router.get("/product/{slug}")
async def product_detail(slug: str):
    p = PRODUCTS_DB.get(slug.lower())
    if not p:
        return JSONResponse(status_code=404, content={"error": "Product not found"})
    return p


# ----- Trade Corridors -----
CORRIDOR_DB = {
    "india-to-uae": {
        "slug": "india-to-uae", "from": "India", "fromCode": "IN", "to": "UAE", "toCode": "AE",
        "fromFlag": "🇮🇳", "toFlag": "🇦🇪",
        "tagline": "India ↔ UAE · $85B+ bilateral trade · CEPA preferential",
        "exportProcess": "IEC → buyer KYC → invoice → packing → shipping bill via ICEGATE → customs clearance → FCL/LCL booking.",
        "importProcess": "UAE buyer obtains import code → opens LC → Indian customs export → sea/air freight to Jebel Ali → DP World clearance.",
        "customsInfo": "0% duty on 90% of HS lines under India–UAE CEPA. AEO-certified shippers clear in 4–6 hours.",
        "documents": ["Invoice", "Packing List", "Bill of Lading", "Certificate of Origin (CEPA)", "Phytosanitary / Halal / FSSAI as applicable"],
        "dutiesTaxes": "Duty: 0–5% (most goods free under CEPA) · UAE VAT 5%.",
        "opportunities": ["Food & Agri", "Pharma", "Textiles", "Jewellery", "IT services"],
        "popularProducts": ["basmati-rice", "spices", "agarbatti", "textiles"],
        "logistics": "Mundra → Jebel Ali in 4 days (sea) · DEL → DXB 3.5 hrs (air).",
        "image": "https://images.unsplash.com/photo-1518684079-3c830dcef090?auto=format&fit=crop&w=1200&q=80",
    },
    "india-to-usa": {
        "slug": "india-to-usa", "from": "India", "fromCode": "IN", "to": "USA", "toCode": "US",
        "fromFlag": "🇮🇳", "toFlag": "🇺🇸",
        "tagline": "India ↔ USA · $190B+ bilateral · Largest export destination",
        "exportProcess": "IEC → US importer EIN → ISF 10+2 filing → ocean booking → customs entry → FDA / FCC as applicable.",
        "importProcess": "US buyer files entry via CBP → FDA / EPA / DOT inspection as required → DDP or DAP delivery.",
        "customsInfo": "MFN avg 3.4%. GSP benefits paused; check current tariff schedule. Section 301 surcharges may apply to China-origin re-exports.",
        "documents": ["Invoice", "Packing List", "BOL", "Certificate of Origin", "FDA Prior Notice (food/pharma)", "FCC declaration (electronics)"],
        "dutiesTaxes": "Duty 0–20% by HS · State sales tax 4–9% · No federal VAT.",
        "opportunities": ["Pharma", "Engineering goods", "Textiles", "Jewellery", "Software services"],
        "popularProducts": ["pharmaceuticals", "textiles", "spices", "basmati-rice"],
        "logistics": "Mundra → NY/NJ in 28 days · Chennai → LA via Panama 32 days · Air to JFK 18 hrs.",
        "image": "https://images.unsplash.com/photo-1485871981521-5b1fd3805eee?auto=format&fit=crop&w=1200&q=80",
    },
    "india-to-australia": {
        "slug": "india-to-australia", "from": "India", "fromCode": "IN", "to": "Australia", "toCode": "AU",
        "fromFlag": "🇮🇳", "toFlag": "🇦🇺",
        "tagline": "India ↔ Australia · ECTA delivers 0% duty on 96% of Indian exports",
        "exportProcess": "IEC → ECTA Certificate of Origin → shipping bill → ABF clearance → biosecurity (DAFF) inspection.",
        "importProcess": "Australian importer ABN → ABF import declaration → biosecurity → GST 10%.",
        "customsInfo": "0% duty under ECTA on 96% Indian goods. Strict biosecurity for any plant/animal-based products.",
        "documents": ["Invoice", "Packing List", "BOL", "ECTA Certificate of Origin", "Biosecurity Treatment Certificate"],
        "dutiesTaxes": "Duty 0% (ECTA) · GST 10% on import.",
        "opportunities": ["Textiles", "Engineering", "Food & Agri", "Pharma", "Education services"],
        "popularProducts": ["textiles", "spices", "basmati-rice", "pharmaceuticals"],
        "logistics": "Mundra → Sydney 23 days · Chennai → Melbourne 21 days.",
        "image": "https://images.unsplash.com/photo-1523482580672-f109ba8cb9be?auto=format&fit=crop&w=1200&q=80",
    },
    "india-to-armenia": {
        "slug": "india-to-armenia", "from": "India", "fromCode": "IN", "to": "Armenia", "toCode": "AM",
        "fromFlag": "🇮🇳", "toFlag": "🇦🇲",
        "tagline": "India ↔ Armenia · Caucasus gateway · EAEU re-export potential",
        "exportProcess": "IEC → invoice → shipping bill → multimodal via Bandar Abbas or Black Sea ports → customs clearance in Yerevan.",
        "importProcess": "Armenian importer registers with Armenian Customs Service → EAEU tariff → onward re-export to Russia / Belarus / Kazakhstan.",
        "customsInfo": "EAEU Common External Tariff applies (avg 5%). Re-export to EAEU members is duty-free for Armenian-origin.",
        "documents": ["Invoice", "Packing List", "BOL", "Certificate of Origin", "Quality / Halal as required"],
        "dutiesTaxes": "Duty avg 5% EAEU CET · VAT 20%.",
        "opportunities": ["Pharma", "Textiles", "IT services", "Diamonds (Armenia is global polishing hub)"],
        "popularProducts": ["pharmaceuticals", "textiles", "spices"],
        "logistics": "Sea via Bandar Abbas + rail/road; INSTC corridor cuts time by 40%.",
        "image": "https://images.unsplash.com/photo-1564507004663-b6dfb3c824d5?auto=format&fit=crop&w=1200&q=80",
    },
}


@router.get("/corridors")
async def list_corridors():
    return [{"slug": c["slug"], "from": c["from"], "to": c["to"], "fromFlag": c["fromFlag"], "toFlag": c["toFlag"], "tagline": c["tagline"], "image": c["image"]} for c in CORRIDOR_DB.values()]


@router.get("/corridor/{slug}")
async def corridor_detail(slug: str):
    c = CORRIDOR_DB.get(slug.lower())
    if not c:
        return JSONResponse(status_code=404, content={"error": "Corridor not found"})
    return c


# ----- Industries -----
INDUSTRY_DB = {
    "agriculture": {"slug": "agriculture", "name": "Agriculture", "icon": "plant", "overview": "$4.1T global agri trade · India is #1 exporter of rice, spices, milk and pulses.", "exports": ["Rice", "Spices", "Tea", "Marine products"], "topMarkets": ["UAE", "USA", "Bangladesh", "Iran", "Saudi Arabia"], "compliance": ["APEDA", "FSSAI", "Spices Board"], "image": "https://images.unsplash.com/photo-1500937386664-56d1dfef3854?auto=format&fit=crop&w=1200&q=80"},
    "food-processing": {"slug": "food-processing", "name": "Food Processing", "icon": "cooking-pot", "overview": "India's processed food exports cross $50B with high-growth in GCC and Africa.", "exports": ["Snacks", "Ready meals", "Dairy", "Beverages"], "topMarkets": ["UAE", "USA", "Saudi Arabia", "UK", "Malaysia"], "compliance": ["FSSAI", "APEDA", "Halal", "Kosher"], "image": "https://images.unsplash.com/photo-1606787366850-de6330128bfc?auto=format&fit=crop&w=1200&q=80"},
    "textiles": {"slug": "textiles", "name": "Textiles & Apparel", "icon": "scissors", "overview": "$44B Indian textile + apparel exports across 100+ countries.", "exports": ["Cotton textiles", "Apparel", "Home furnishings", "Yarn"], "topMarkets": ["USA", "UAE", "UK", "EU", "Australia"], "compliance": ["AEPC", "Oeko-Tex", "GOTS"], "image": "https://images.unsplash.com/photo-1558769132-cb1aea458c5e?auto=format&fit=crop&w=1200&q=80"},
    "chemicals": {"slug": "chemicals", "name": "Chemicals", "icon": "flask", "overview": "India is the 6th largest chemical producer globally — $220B industry with $30B+ exports.", "exports": ["Dyes & pigments", "Agrochemicals", "Specialty chemicals", "Polymers"], "topMarkets": ["USA", "China", "Brazil", "UAE", "Germany"], "compliance": ["REACH (EU)", "TSCA (USA)", "GHS"], "image": "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?auto=format&fit=crop&w=1200&q=80"},
    "pharmaceuticals": {"slug": "pharmaceuticals", "name": "Pharmaceuticals", "icon": "pill", "overview": "World's 3rd largest pharma exporter — $28B annual · 60% of global vaccines.", "exports": ["Generics", "Vaccines", "APIs", "Biosimilars"], "topMarkets": ["USA", "EU", "Africa", "ASEAN", "LatAm"], "compliance": ["USFDA", "EMA", "WHO GMP", "CDSCO"], "image": "https://images.unsplash.com/photo-1631549916768-4119b2e5f926?auto=format&fit=crop&w=1200&q=80"},
    "engineering": {"slug": "engineering", "name": "Engineering Goods", "icon": "gear", "overview": "India's largest export category — $112B in 2024, growing 14% YoY.", "exports": ["Auto components", "Industrial machinery", "Electrical equipment", "Iron & steel"], "topMarkets": ["USA", "UAE", "China", "Singapore", "Germany"], "compliance": ["BIS", "CE marking", "ISO 9001"], "image": "https://images.unsplash.com/photo-1581094288338-2314dddb7ece?auto=format&fit=crop&w=1200&q=80"},
    "handicrafts": {"slug": "handicrafts", "name": "Handicrafts", "icon": "paint-brush", "overview": "India's handicrafts exports cross $4B with high-value buyers in USA, UK, GCC and EU.", "exports": ["Wood crafts", "Brass items", "Embroidered textiles", "Pottery"], "topMarkets": ["USA", "UK", "UAE", "Germany", "France"], "compliance": ["EPCH RCMC", "CITES (for ivory/wood)"], "image": "https://images.unsplash.com/photo-1528465424850-54d22f092f9d?auto=format&fit=crop&w=1200&q=80"},
    "fmcg": {"slug": "fmcg", "name": "FMCG", "icon": "shopping-bag", "overview": "$110B Indian FMCG sector — agarbatti, packaged foods and personal care lead exports.", "exports": ["Agarbatti", "Packaged foods", "Personal care", "Household products"], "topMarkets": ["UAE", "USA", "Saudi Arabia", "UK", "Nepal"], "compliance": ["FSSAI", "BIS", "Halal", "Kosher"], "image": "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?auto=format&fit=crop&w=1200&q=80"},
}


@router.get("/industries")
async def list_industries():
    return [{"slug": i["slug"], "name": i["name"], "icon": i["icon"], "overview": i["overview"], "image": i["image"]} for i in INDUSTRY_DB.values()]


@router.get("/industry/{slug}")
async def industry_detail(slug: str):
    i = INDUSTRY_DB.get(slug.lower())
    if not i:
        return JSONResponse(status_code=404, content={"error": "Industry not found"})
    return i


# ----- Blog -----
BLOG_DB = [
    {"slug": "complete-guide-to-iec-code-india", "title": "The complete guide to getting your IEC code in India (2026)", "category": "Export Guides", "date": "Jan 12, 2026", "image": "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?auto=format&fit=crop&w=1200&q=80", "excerpt": "An IEC code is the foundation of every Indian exporter's journey. Here's the simplest, free, online process — start to finish.", "readMins": 7},
    {"slug": "rodtep-explained-2026", "title": "RoDTEP, RoSCTL & Duty Drawback explained for 2026", "category": "Compliance", "date": "Jan 10, 2026", "image": "https://images.unsplash.com/photo-1554224155-6726b3ff858f?auto=format&fit=crop&w=1200&q=80", "excerpt": "Three powerful export incentives, three different rates. Here's exactly which one applies to you — and how to claim it.", "readMins": 9},
    {"slug": "incoterms-2020-cheatsheet", "title": "Incoterms 2020 cheatsheet for exporters", "category": "Trade Intelligence", "date": "Jan 8, 2026", "image": "https://images.unsplash.com/photo-1577017040065-650ee4d43339?auto=format&fit=crop&w=1200&q=80", "excerpt": "FOB or CIF? DDP or DAP? A quick chart that will save you 30% on disputes and 10% on freight.", "readMins": 5},
    {"slug": "india-uae-cepa-product-list", "title": "India–UAE CEPA: full list of products with 0% duty", "category": "Trade News", "date": "Jan 6, 2026", "image": "https://images.unsplash.com/photo-1518684079-3c830dcef090?auto=format&fit=crop&w=1200&q=80", "excerpt": "11,908 products at zero duty. Find yours in 30 seconds — and start saving 5–18% per shipment.", "readMins": 8},
    {"slug": "lcs-vs-da-vs-tt-payment-terms", "title": "LC vs DA vs TT — which payment term protects your margin?", "category": "Logistics", "date": "Jan 4, 2026", "image": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80", "excerpt": "A practical guide for first-time exporters — when to insist on an LC, when DA is fine, and when never to take TT.", "readMins": 6},
    {"slug": "how-to-find-buyers-in-gcc", "title": "How to find your first buyer in the GCC", "category": "International Marketing", "date": "Jan 2, 2026", "image": "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?auto=format&fit=crop&w=1200&q=80", "excerpt": "From Gulfood to LinkedIn to LeadNation — the 9 channels that work for new GCC exporters.", "readMins": 10},
]


@router.get("/blog")
async def blog_list():
    return BLOG_DB


@router.get("/blog/{slug}")
async def blog_detail(slug: str):
    post = next((b for b in BLOG_DB if b["slug"] == slug), None)
    if not post:
        return JSONResponse(status_code=404, content={"error": "Blog post not found"})
    # add body
    full = {**post, "body": [
        "International trade can feel overwhelming when you're just starting. But the principles never change: the right paperwork, the right partner and the right pricing.",
        "In this guide we walk through every step — from registration to shipping bill — with a checklist you can use today.",
        "The most important thing is to start with a small, friendly market and grow incrementally. Most successful Indian exporters did their first shipment to UAE or Singapore.",
        "Want help moving faster? LeadNation's app gives you HSN codes, duty rates, buyers and compliance in one screen.",
    ]}
    return full


# ----- Marketplace & Network (mock previews) -----
@router.get("/marketplace")
async def marketplace():
    return {
        "listings": [
            {"id": 1, "title": "Premium Basmati Rice — 1121", "supplier": "KRBL Ltd", "price": "USD 1,180 / MT", "moq": "26 MT", "image": "https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=900&q=80"},
            {"id": 2, "title": "Agarbatti Bulk — Sandalwood", "supplier": "Mysore Sandal", "price": "USD 2.4 / kg", "moq": "500 kg", "image": "https://images.unsplash.com/photo-1602874801007-bd45867d505b?auto=format&fit=crop&w=900&q=80"},
            {"id": 3, "title": "Cotton Bed Linen Sets", "supplier": "Welspun", "price": "USD 18 / set", "moq": "500 sets", "image": "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=900&q=80"},
            {"id": 4, "title": "Turmeric Powder — Lakadong", "supplier": "ITC Spices", "price": "USD 4.2 / kg", "moq": "2 MT", "image": "https://images.unsplash.com/photo-1596797038530-2c107229654b?auto=format&fit=crop&w=900&q=80"},
            {"id": 5, "title": "Paracetamol Tablets 500mg", "supplier": "Cipla Exports", "price": "USD 0.012 / tab", "moq": "1M tabs", "image": "https://images.unsplash.com/photo-1631549916768-4119b2e5f926?auto=format&fit=crop&w=900&q=80"},
            {"id": 6, "title": "Auto Parts — Bearings", "supplier": "Mahindra Auto", "price": "USD 6.4 / pc", "moq": "10K pcs", "image": "https://images.unsplash.com/photo-1581094288338-2314dddb7ece?auto=format&fit=crop&w=900&q=80"},
        ],
        "reels": [
            {"id": 1, "title": "Inside Mundra Port — 9M containers/yr", "thumb": "https://images.unsplash.com/photo-1494412519320-aa613dfb7738?auto=format&fit=crop&w=600&q=80"},
            {"id": 2, "title": "How Basmati gets to Saudi", "thumb": "https://images.unsplash.com/photo-1605902711622-cfb43c4437b5?auto=format&fit=crop&w=600&q=80"},
            {"id": 3, "title": "First export at 22 — Tirupur founder", "thumb": "https://images.unsplash.com/photo-1573164713988-8665fc963095?auto=format&fit=crop&w=600&q=80"},
            {"id": 4, "title": "Inside Jebel Ali Free Zone", "thumb": "https://images.unsplash.com/photo-1518684079-3c830dcef090?auto=format&fit=crop&w=600&q=80"},
        ],
        "buyerRequests": [
            {"id": 1, "title": "RFQ · 50 MT Basmati to Riyadh · Halal certified", "country": "🇸🇦"},
            {"id": 2, "title": "RFQ · 1,000 cartons Agarbatti to Dubai · monthly", "country": "🇦🇪"},
            {"id": 3, "title": "RFQ · 200 MT Turmeric to Houston · USDA Organic", "country": "🇺🇸"},
        ],
    }


@router.get("/network")
async def network():
    return {
        "members": [
            {"name": "Rohan Mehta", "role": "Exporter · Basmati Rice", "city": "Karnal, IN", "avatar": "https://i.pravatar.cc/120?img=11"},
            {"name": "Aisha Al-Rashid", "role": "Importer · GCC Wholesale", "city": "Dubai, AE", "avatar": "https://i.pravatar.cc/120?img=25"},
            {"name": "Sundar Iyer", "role": "CHA · Customs House Agent", "city": "Chennai, IN", "avatar": "https://i.pravatar.cc/120?img=33"},
            {"name": "Ana García", "role": "Buyer · Latin America", "city": "São Paulo, BR", "avatar": "https://i.pravatar.cc/120?img=49"},
            {"name": "James O'Connor", "role": "Logistics · NVOCC", "city": "London, GB", "avatar": "https://i.pravatar.cc/120?img=57"},
            {"name": "Priya Sharma", "role": "Export Agent · Pharma", "city": "Hyderabad, IN", "avatar": "https://i.pravatar.cc/120?img=44"},
        ],
        "stats": [
            {"label": "Verified members", "value": "48,200+"},
            {"label": "Countries covered", "value": "92"},
            {"label": "Categories", "value": "112"},
            {"label": "Avg response time", "value": "< 6 hrs"},
        ],
    }


