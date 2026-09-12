"""Expo & Events Engine — LIVE layer.

Three sources feed the same `expo_listings` collection:
  1. CATALOGUE  — a curated register of the world's major recurring trade fairs.
                  A daily job rolls every entry forward to its NEXT edition, so the
                  calendar is always "live" (never shows a finished expo).
  2. USER/ADMIN — paid listings + admin-created events (event_listings.py).
  3. DISCOVERY  — a daily Vametra AI Brain pass that proposes NEW events; these land in
                  the admin approval queue (`status="pending"`, `source="ai-discovery"`)
                  and are never auto-published, so nothing unverified reaches users.

Public pages only ever show ongoing + upcoming events.
"""
import json
import logging
from datetime import datetime, timezone, timedelta, date
from typing import Any, Dict, List

from core import db

EVENTS = db.expo_listings
META = db.expo_engine_meta

# month, day = the edition's typical opening date; recurrence: annual | biennial-odd | biennial-even
CATALOGUE: List[Dict[str, Any]] = [
    # ---- India ----
    {"slug": "iitf-new-delhi", "name": "India International Trade Fair (IITF)", "category": "Trade Fair",
     "country": "India", "city": "New Delhi", "venueName": "Bharat Mandapam, Pragati Maidan",
     "industry": "Multi-sector", "audience": "All", "organizer": "India Trade Promotion Organisation (ITPO)",
     "website": "https://indiatradefair.com", "month": 11, "day": 14, "days": 14, "recurrence": "annual"},
    {"slug": "aahar-new-delhi", "name": "AAHAR — International Food & Hospitality Fair", "category": "Trade Fair",
     "country": "India", "city": "New Delhi", "venueName": "Bharat Mandapam, Pragati Maidan",
     "industry": "Agriculture & Food", "audience": "Importers", "organizer": "ITPO / APEDA",
     "website": "https://aaharinternationalfair.com", "month": 3, "day": 4, "days": 5, "recurrence": "annual"},
    {"slug": "india-intl-garment-fair", "name": "India International Garment Fair", "category": "Trade Fair",
     "country": "India", "city": "New Delhi", "venueName": "Yashobhoomi, Dwarka",
     "industry": "Textiles & Apparel", "audience": "Buyers", "organizer": "Apparel Export Promotion Council",
     "website": "https://indiaapparelfair.com", "month": 7, "day": 15, "days": 3, "recurrence": "annual"},
    {"slug": "auto-expo-india", "name": "Bharat Mobility Global Expo", "category": "Manufacturing",
     "country": "India", "city": "New Delhi", "venueName": "Bharat Mandapam & Yashobhoomi",
     "industry": "Automotive", "audience": "Manufacturers", "organizer": "CII / ACMA / SIAM",
     "website": "https://bharat-mobility.com", "month": 1, "day": 17, "days": 6, "recurrence": "annual"},
    {"slug": "india-pharma-expo", "name": "iPHEX — India Pharma & Healthcare Expo", "category": "Trade Fair",
     "country": "India", "city": "Mumbai", "venueName": "Jio World Convention Centre",
     "industry": "Pharmaceuticals", "audience": "Importers", "organizer": "Pharmexcil",
     "website": "https://iphex-india.com", "month": 9, "day": 10, "days": 3, "recurrence": "annual"},
    {"slug": "iimtf-kolkata", "name": "India International Mega Trade Fair", "category": "Trade Fair",
     "country": "India", "city": "Kolkata", "venueName": "Science City Ground",
     "industry": "Multi-sector", "audience": "All", "organizer": "ITPO East",
     "website": "https://iimtf.com", "month": 12, "day": 12, "days": 12, "recurrence": "annual"},
    {"slug": "vibrant-gujarat", "name": "Vibrant Gujarat Global Summit", "category": "Government",
     "country": "India", "city": "Gandhinagar", "venueName": "Mahatma Mandir",
     "industry": "Multi-sector", "audience": "Investors", "organizer": "Government of Gujarat",
     "website": "https://vibrantgujarat.com", "month": 1, "day": 10, "days": 3, "recurrence": "biennial-odd"},
    {"slug": "acetech-mumbai", "name": "ACETECH — Architecture & Building Materials", "category": "Manufacturing",
     "country": "India", "city": "Mumbai", "venueName": "Bombay Exhibition Centre",
     "industry": "Engineering Goods", "audience": "Distributors", "organizer": "ABEC Exhibitions",
     "website": "https://etacetech.com", "month": 10, "day": 30, "days": 4, "recurrence": "annual"},
    {"slug": "india-intl-jewellery-show", "name": "India International Jewellery Show (IIJS)", "category": "Trade Fair",
     "country": "India", "city": "Mumbai", "venueName": "Jio World Convention Centre",
     "industry": "Gems & Jewellery", "audience": "Buyers", "organizer": "GJEPC",
     "website": "https://iijs.org", "month": 8, "day": 5, "days": 5, "recurrence": "annual"},
    {"slug": "india-chem", "name": "India Chem", "category": "Manufacturing",
     "country": "India", "city": "Mumbai", "venueName": "Bombay Exhibition Centre",
     "industry": "Chemicals", "audience": "Manufacturers", "organizer": "FICCI",
     "website": "https://indiachem.in", "month": 10, "day": 15, "days": 3, "recurrence": "biennial-even"},

    # ---- Middle East ----
    {"slug": "gulfood-dubai", "name": "Gulfood Dubai", "category": "Trade Fair",
     "country": "UAE", "city": "Dubai", "venueName": "Dubai World Trade Centre",
     "industry": "Agriculture & Food", "audience": "Importers", "organizer": "DWTC",
     "website": "https://gulfood.com", "month": 2, "day": 16, "days": 5, "recurrence": "annual"},
    {"slug": "gitex-global", "name": "GITEX Global", "category": "Technology",
     "country": "UAE", "city": "Dubai", "venueName": "Dubai World Trade Centre",
     "industry": "Electronics", "audience": "All", "organizer": "DWTC",
     "website": "https://gitex.com", "month": 10, "day": 13, "days": 5, "recurrence": "annual"},
    {"slug": "big5-global", "name": "The Big 5 Global", "category": "Manufacturing",
     "country": "UAE", "city": "Dubai", "venueName": "Dubai World Trade Centre",
     "industry": "Engineering Goods", "audience": "Distributors", "organizer": "dmg events",
     "website": "https://thebig5global.com", "month": 11, "day": 24, "days": 4, "recurrence": "annual"},
    {"slug": "arab-health", "name": "Arab Health", "category": "Trade Fair",
     "country": "UAE", "city": "Dubai", "venueName": "Dubai World Trade Centre",
     "industry": "Pharmaceuticals", "audience": "Importers", "organizer": "Informa Markets",
     "website": "https://arabhealthonline.com", "month": 1, "day": 27, "days": 4, "recurrence": "annual"},
    {"slug": "beautyworld-me", "name": "Beautyworld Middle East", "category": "Trade Fair",
     "country": "UAE", "city": "Dubai", "venueName": "Dubai World Trade Centre",
     "industry": "FMCG", "audience": "Buyers", "organizer": "Messe Frankfurt Middle East",
     "website": "https://beautyworld-middle-east.ae.messefrankfurt.com", "month": 10, "day": 27, "days": 3, "recurrence": "annual"},
    {"slug": "saudi-food-show", "name": "Saudi Food Show", "category": "Trade Fair",
     "country": "Saudi Arabia", "city": "Riyadh", "venueName": "Riyadh Front Exhibition Centre",
     "industry": "Agriculture & Food", "audience": "Importers", "organizer": "dmg events",
     "website": "https://saudifoodshow.com", "month": 6, "day": 22, "days": 3, "recurrence": "annual"},
    {"slug": "big5-construct-saudi", "name": "Big 5 Construct Saudi", "category": "Manufacturing",
     "country": "Saudi Arabia", "city": "Riyadh", "venueName": "Riyadh International Convention Centre",
     "industry": "Engineering Goods", "audience": "Distributors", "organizer": "dmg events",
     "website": "https://big5constructsaudi.com", "month": 2, "day": 23, "days": 4, "recurrence": "annual"},
    {"slug": "qatar-agriteq", "name": "AgriteQ — Qatar International Agricultural Exhibition", "category": "Agriculture",
     "country": "Qatar", "city": "Doha", "venueName": "Doha Exhibition & Convention Center",
     "industry": "Agriculture & Food", "audience": "Importers", "organizer": "Ministry of Municipality",
     "website": "https://agriteq.com", "month": 3, "day": 18, "days": 5, "recurrence": "annual"},

    # ---- China / Asia ----
    {"slug": "canton-fair", "name": "Canton Fair (China Import & Export Fair)", "category": "Import/Export",
     "country": "China", "city": "Guangzhou", "venueName": "Canton Fair Complex",
     "industry": "Multi-sector", "audience": "Importers", "organizer": "China Foreign Trade Centre",
     "website": "https://cantonfair.org.cn", "month": 4, "day": 15, "days": 21, "recurrence": "annual"},
    {"slug": "china-intl-import-expo", "name": "China International Import Expo (CIIE)", "category": "Import/Export",
     "country": "China", "city": "Shanghai", "venueName": "National Exhibition & Convention Center",
     "industry": "Multi-sector", "audience": "Exporters", "organizer": "Ministry of Commerce, PRC",
     "website": "https://ciie.org", "month": 11, "day": 5, "days": 6, "recurrence": "annual"},
    {"slug": "hktdc-gift-fair", "name": "HKTDC Hong Kong Gifts & Premium Fair", "category": "Trade Fair",
     "country": "Hong Kong", "city": "Hong Kong", "venueName": "HK Convention & Exhibition Centre",
     "industry": "Handicrafts", "audience": "Buyers", "organizer": "HKTDC",
     "website": "https://hktdc.com", "month": 4, "day": 27, "days": 4, "recurrence": "annual"},
    {"slug": "foodex-japan", "name": "FOODEX JAPAN", "category": "Trade Fair",
     "country": "Japan", "city": "Chiba", "venueName": "Makuhari Messe",
     "industry": "Agriculture & Food", "audience": "Importers", "organizer": "JMA",
     "website": "https://jma-foodex.jp", "month": 3, "day": 10, "days": 4, "recurrence": "annual"},
    {"slug": "seoul-food-hotel", "name": "Seoul Food & Hotel", "category": "Trade Fair",
     "country": "South Korea", "city": "Goyang", "venueName": "KINTEX",
     "industry": "Agriculture & Food", "audience": "Importers", "organizer": "KOTRA / Informa",
     "website": "https://seoulfoodnhotel.co.kr", "month": 6, "day": 10, "days": 4, "recurrence": "annual"},
    {"slug": "thaifex-anuga-asia", "name": "THAIFEX – Anuga Asia", "category": "Trade Fair",
     "country": "Thailand", "city": "Bangkok", "venueName": "IMPACT Muang Thong Thani",
     "industry": "Agriculture & Food", "audience": "Importers", "organizer": "Koelnmesse / DITP",
     "website": "https://thaifex-anuga.com", "month": 5, "day": 27, "days": 5, "recurrence": "annual"},
    {"slug": "vietnam-expo", "name": "Vietnam International Trade Fair (VIETNAM EXPO)", "category": "Import/Export",
     "country": "Vietnam", "city": "Hanoi", "venueName": "Hanoi ICE",
     "industry": "Multi-sector", "audience": "All", "organizer": "VINEXAD / MOIT",
     "website": "https://vietnamexpo.com.vn", "month": 4, "day": 15, "days": 4, "recurrence": "annual"},
    {"slug": "singapore-fintech-festival", "name": "Singapore FinTech Festival", "category": "Finance",
     "country": "Singapore", "city": "Singapore", "venueName": "Singapore EXPO",
     "industry": "Logistics", "audience": "Startups", "organizer": "Monetary Authority of Singapore",
     "website": "https://fintechfestival.sg", "month": 11, "day": 11, "days": 3, "recurrence": "annual"},
    {"slug": "food-hotel-asia", "name": "Food & Hotel Asia (FHA)", "category": "Trade Fair",
     "country": "Singapore", "city": "Singapore", "venueName": "Singapore EXPO",
     "industry": "Agriculture & Food", "audience": "Importers", "organizer": "Informa Markets",
     "website": "https://fhafnb.com", "month": 4, "day": 8, "days": 4, "recurrence": "annual"},
    {"slug": "indonesia-trade-expo", "name": "Trade Expo Indonesia", "category": "Import/Export",
     "country": "Indonesia", "city": "Tangerang", "venueName": "ICE BSD City",
     "industry": "Multi-sector", "audience": "Importers", "organizer": "Ministry of Trade, Indonesia",
     "website": "https://tradeexpoindonesia.com", "month": 10, "day": 9, "days": 5, "recurrence": "annual"},
    {"slug": "dhaka-intl-trade-fair", "name": "Dhaka International Trade Fair", "category": "Trade Fair",
     "country": "Bangladesh", "city": "Dhaka", "venueName": "Bangabandhu Bangladesh–China Exhibition Centre",
     "industry": "Multi-sector", "audience": "All", "organizer": "Export Promotion Bureau",
     "website": "https://epb.gov.bd", "month": 1, "day": 1, "days": 30, "recurrence": "annual"},

    # ---- Europe ----
    {"slug": "hannover-messe", "name": "Hannover Messe", "category": "Manufacturing",
     "country": "Germany", "city": "Hannover", "venueName": "Deutsche Messe",
     "industry": "Engineering Goods", "audience": "Manufacturers", "organizer": "Deutsche Messe AG",
     "website": "https://hannovermesse.de", "month": 4, "day": 20, "days": 5, "recurrence": "annual"},
    {"slug": "anuga-cologne", "name": "Anuga", "category": "Trade Fair",
     "country": "Germany", "city": "Cologne", "venueName": "Koelnmesse",
     "industry": "Agriculture & Food", "audience": "Importers", "organizer": "Koelnmesse",
     "website": "https://anuga.com", "month": 10, "day": 4, "days": 5, "recurrence": "biennial-odd"},
    {"slug": "biofach-nuremberg", "name": "BIOFACH — World Organic Trade Fair", "category": "Trade Fair",
     "country": "Germany", "city": "Nuremberg", "venueName": "NürnbergMesse",
     "industry": "Agriculture & Food", "audience": "Importers", "organizer": "NürnbergMesse",
     "website": "https://biofach.de", "month": 2, "day": 11, "days": 4, "recurrence": "annual"},
    {"slug": "transport-logistic-munich", "name": "transport logistic", "category": "Logistics",
     "country": "Germany", "city": "Munich", "venueName": "Messe München",
     "industry": "Logistics", "audience": "All", "organizer": "Messe München",
     "website": "https://transportlogistic.de", "month": 6, "day": 2, "days": 4, "recurrence": "biennial-odd"},
    {"slug": "heimtextil-frankfurt", "name": "Heimtextil", "category": "Trade Fair",
     "country": "Germany", "city": "Frankfurt", "venueName": "Messe Frankfurt",
     "industry": "Textiles & Apparel", "audience": "Buyers", "organizer": "Messe Frankfurt",
     "website": "https://heimtextil.messefrankfurt.com", "month": 1, "day": 13, "days": 4, "recurrence": "annual"},
    {"slug": "ambiente-frankfurt", "name": "Ambiente", "category": "Trade Fair",
     "country": "Germany", "city": "Frankfurt", "venueName": "Messe Frankfurt",
     "industry": "Handicrafts", "audience": "Buyers", "organizer": "Messe Frankfurt",
     "website": "https://ambiente.messefrankfurt.com", "month": 2, "day": 6, "days": 4, "recurrence": "annual"},
    {"slug": "sial-paris", "name": "SIAL Paris", "category": "Trade Fair",
     "country": "France", "city": "Paris", "venueName": "Paris Nord Villepinte",
     "industry": "Agriculture & Food", "audience": "Importers", "organizer": "Comexposium",
     "website": "https://sialparis.com", "month": 10, "day": 17, "days": 5, "recurrence": "biennial-even"},
    {"slug": "vinexpo-paris", "name": "Wine Paris & Vinexpo", "category": "Trade Fair",
     "country": "France", "city": "Paris", "venueName": "Paris Expo Porte de Versailles",
     "industry": "Agriculture & Food", "audience": "Importers", "organizer": "Vinexposium",
     "website": "https://wineparis-vinexpo.com", "month": 2, "day": 10, "days": 3, "recurrence": "annual"},
    {"slug": "cphi-worldwide", "name": "CPHI Worldwide", "category": "Trade Fair",
     "country": "Spain", "city": "Barcelona", "venueName": "Fira de Barcelona Gran Via",
     "industry": "Pharmaceuticals", "audience": "Importers", "organizer": "Informa Markets",
     "website": "https://cphi.com", "month": 10, "day": 8, "days": 3, "recurrence": "annual"},
    {"slug": "mwc-barcelona", "name": "Mobile World Congress", "category": "Technology",
     "country": "Spain", "city": "Barcelona", "venueName": "Fira Gran Via",
     "industry": "Electronics", "audience": "All", "organizer": "GSMA",
     "website": "https://mwcbarcelona.com", "month": 3, "day": 2, "days": 4, "recurrence": "annual"},
    {"slug": "fruit-attraction-madrid", "name": "Fruit Attraction", "category": "Agriculture",
     "country": "Spain", "city": "Madrid", "venueName": "IFEMA Madrid",
     "industry": "Agriculture & Food", "audience": "Importers", "organizer": "IFEMA / FEPEX",
     "website": "https://ifema.es/fruit-attraction", "month": 9, "day": 30, "days": 3, "recurrence": "annual"},
    {"slug": "cibus-parma", "name": "CIBUS — International Food Exhibition", "category": "Trade Fair",
     "country": "Italy", "city": "Parma", "venueName": "Fiere di Parma",
     "industry": "Agriculture & Food", "audience": "Importers", "organizer": "Fiere di Parma",
     "website": "https://cibus.it", "month": 5, "day": 5, "days": 4, "recurrence": "biennial-even"},
    {"slug": "micam-milano", "name": "MICAM Milano — Footwear", "category": "Trade Fair",
     "country": "Italy", "city": "Milan", "venueName": "Fiera Milano Rho",
     "industry": "Textiles & Apparel", "audience": "Buyers", "organizer": "Assocalzaturifici",
     "website": "https://themicam.com", "month": 2, "day": 16, "days": 3, "recurrence": "annual"},
    {"slug": "itb-berlin", "name": "ITB Berlin", "category": "Business",
     "country": "Germany", "city": "Berlin", "venueName": "Messe Berlin",
     "industry": "Multi-sector", "audience": "All", "organizer": "Messe Berlin",
     "website": "https://itb.com", "month": 3, "day": 3, "days": 3, "recurrence": "annual"},
    {"slug": "world-economic-forum-davos", "name": "World Economic Forum Annual Meeting", "category": "Business",
     "country": "Switzerland", "city": "Davos", "venueName": "Davos Congress Centre",
     "industry": "Multi-sector", "audience": "Investors", "organizer": "World Economic Forum",
     "website": "https://weforum.org", "month": 1, "day": 19, "days": 5, "recurrence": "annual"},
    {"slug": "plma-amsterdam", "name": "PLMA World of Private Label", "category": "Trade Fair",
     "country": "Netherlands", "city": "Amsterdam", "venueName": "RAI Amsterdam",
     "industry": "FMCG", "audience": "Buyers", "organizer": "PLMA",
     "website": "https://plmainternational.com", "month": 5, "day": 20, "days": 2, "recurrence": "annual"},
    {"slug": "intertraffic-amsterdam", "name": "Intertraffic Amsterdam", "category": "Logistics",
     "country": "Netherlands", "city": "Amsterdam", "venueName": "RAI Amsterdam",
     "industry": "Logistics", "audience": "All", "organizer": "RAI Amsterdam",
     "website": "https://intertraffic.com", "month": 4, "day": 7, "days": 4, "recurrence": "biennial-even"},
    {"slug": "itma-textile", "name": "ITMA — Textile & Garment Technology", "category": "Manufacturing",
     "country": "Italy", "city": "Milan", "venueName": "Fiera Milano Rho",
     "industry": "Textiles & Apparel", "audience": "Manufacturers", "organizer": "CEMATEX",
     "website": "https://itma.com", "month": 6, "day": 15, "days": 7, "recurrence": "biennial-odd"},

    # ---- UK / Americas ----
    {"slug": "ife-london", "name": "IFE — International Food & Drink Event", "category": "Trade Fair",
     "country": "United Kingdom", "city": "London", "venueName": "ExCeL London",
     "industry": "Agriculture & Food", "audience": "Importers", "organizer": "Montgomery Group",
     "website": "https://ife.co.uk", "month": 3, "day": 17, "days": 3, "recurrence": "annual"},
    {"slug": "spring-fair-birmingham", "name": "Spring Fair", "category": "Trade Fair",
     "country": "United Kingdom", "city": "Birmingham", "venueName": "NEC Birmingham",
     "industry": "Handicrafts", "audience": "Buyers", "organizer": "Hyve Group",
     "website": "https://springfair.com", "month": 2, "day": 2, "days": 4, "recurrence": "annual"},
    {"slug": "multimodal-uk", "name": "Multimodal", "category": "Logistics",
     "country": "United Kingdom", "city": "Birmingham", "venueName": "NEC Birmingham",
     "industry": "Logistics", "audience": "All", "organizer": "Clarion Events",
     "website": "https://multimodal.org.uk", "month": 6, "day": 10, "days": 3, "recurrence": "annual"},
    {"slug": "ces-las-vegas", "name": "CES", "category": "Technology",
     "country": "USA", "city": "Las Vegas", "venueName": "Las Vegas Convention Center",
     "industry": "Electronics", "audience": "All", "organizer": "Consumer Technology Association",
     "website": "https://ces.tech", "month": 1, "day": 6, "days": 4, "recurrence": "annual"},
    {"slug": "natural-products-expo-west", "name": "Natural Products Expo West", "category": "Trade Fair",
     "country": "USA", "city": "Anaheim", "venueName": "Anaheim Convention Center",
     "industry": "Agriculture & Food", "audience": "Buyers", "organizer": "New Hope Network",
     "website": "https://expowest.com", "month": 3, "day": 4, "days": 4, "recurrence": "annual"},
    {"slug": "magic-las-vegas", "name": "MAGIC Las Vegas — Apparel", "category": "Trade Fair",
     "country": "USA", "city": "Las Vegas", "venueName": "Las Vegas Convention Center",
     "industry": "Textiles & Apparel", "audience": "Buyers", "organizer": "Informa Markets Fashion",
     "website": "https://magicfashionevents.com", "month": 8, "day": 11, "days": 3, "recurrence": "annual"},
    {"slug": "pack-expo-intl", "name": "PACK EXPO International", "category": "Manufacturing",
     "country": "USA", "city": "Chicago", "venueName": "McCormick Place",
     "industry": "Engineering Goods", "audience": "Manufacturers", "organizer": "PMMI",
     "website": "https://packexpointernational.com", "month": 11, "day": 2, "days": 4, "recurrence": "biennial-even"},
    {"slug": "fancy-food-show", "name": "Summer Fancy Food Show", "category": "Trade Fair",
     "country": "USA", "city": "New York", "venueName": "Javits Center",
     "industry": "Agriculture & Food", "audience": "Buyers", "organizer": "Specialty Food Association",
     "website": "https://specialtyfood.com", "month": 6, "day": 29, "days": 3, "recurrence": "annual"},
    {"slug": "expo-antad-mexico", "name": "Expo ANTAD & Alimentaria", "category": "Trade Fair",
     "country": "Mexico", "city": "Guadalajara", "venueName": "Expo Guadalajara",
     "industry": "FMCG", "audience": "Buyers", "organizer": "ANTAD",
     "website": "https://expoantad.net", "month": 3, "day": 11, "days": 3, "recurrence": "annual"},
    {"slug": "fispal-sao-paulo", "name": "Fispal Food Service", "category": "Trade Fair",
     "country": "Brazil", "city": "São Paulo", "venueName": "Expo Center Norte",
     "industry": "Agriculture & Food", "audience": "Distributors", "organizer": "Informa Markets Brazil",
     "website": "https://fispalfoodservice.com.br", "month": 6, "day": 10, "days": 4, "recurrence": "annual"},
    {"slug": "sial-canada", "name": "SIAL Canada", "category": "Trade Fair",
     "country": "Canada", "city": "Toronto", "venueName": "Enercare Centre",
     "industry": "Agriculture & Food", "audience": "Importers", "organizer": "SIAL Network",
     "website": "https://sialcanada.com", "month": 5, "day": 6, "days": 3, "recurrence": "annual"},

    # ---- Africa / Oceania / Eurasia ----
    {"slug": "intra-african-trade-fair", "name": "Intra-African Trade Fair (IATF)", "category": "Import/Export",
     "country": "Nigeria", "city": "Lagos", "venueName": "Landmark Centre",
     "industry": "Multi-sector", "audience": "All", "organizer": "Afreximbank / AfCFTA",
     "website": "https://iatf.africa", "month": 11, "day": 21, "days": 7, "recurrence": "biennial-even"},
    {"slug": "africa-big7", "name": "Africa's Big 7 (Food & Beverage)", "category": "Trade Fair",
     "country": "South Africa", "city": "Johannesburg", "venueName": "Gallagher Convention Centre",
     "industry": "Agriculture & Food", "audience": "Importers", "organizer": "dmg events",
     "website": "https://africabig7.com", "month": 6, "day": 24, "days": 3, "recurrence": "annual"},
    {"slug": "cairo-intl-fair", "name": "Cairo International Fair", "category": "Trade Fair",
     "country": "Egypt", "city": "Cairo", "venueName": "Egypt International Exhibition Center",
     "industry": "Multi-sector", "audience": "All", "organizer": "GOIEF",
     "website": "https://egyexpo.com", "month": 3, "day": 8, "days": 7, "recurrence": "annual"},
    {"slug": "fine-food-australia", "name": "Fine Food Australia", "category": "Trade Fair",
     "country": "Australia", "city": "Sydney", "venueName": "ICC Sydney",
     "industry": "Agriculture & Food", "audience": "Importers", "organizer": "Diversified Communications",
     "website": "https://finefoodaustralia.com.au", "month": 9, "day": 8, "days": 4, "recurrence": "annual"},
    {"slug": "worldfood-istanbul", "name": "WorldFood Istanbul", "category": "Trade Fair",
     "country": "Turkey", "city": "Istanbul", "venueName": "Tüyap Fair Centre",
     "industry": "Agriculture & Food", "audience": "Importers", "organizer": "Hyve Group",
     "website": "https://worldfood-istanbul.com", "month": 9, "day": 3, "days": 4, "recurrence": "annual"},
    {"slug": "worldfood-moscow", "name": "WorldFood Moscow", "category": "Trade Fair",
     "country": "Russia", "city": "Moscow", "venueName": "Crocus Expo",
     "industry": "Agriculture & Food", "audience": "Importers", "organizer": "ITE Group",
     "website": "https://world-food.ru", "month": 9, "day": 16, "days": 4, "recurrence": "annual"},
]

IMAGE_BY_INDUSTRY = {
    "Agriculture & Food": "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?auto=format&fit=crop&w=1200&q=80",
    "Textiles & Apparel": "https://images.unsplash.com/photo-1489987707025-afc232f7ea0f?auto=format&fit=crop&w=1200&q=80",
    "Pharmaceuticals": "https://images.unsplash.com/photo-1587854692152-cbe660dbde88?auto=format&fit=crop&w=1200&q=80",
    "Engineering Goods": "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&w=1200&q=80",
    "Chemicals": "https://images.unsplash.com/photo-1532634922-8fe0b757fb13?auto=format&fit=crop&w=1200&q=80",
    "FMCG": "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?auto=format&fit=crop&w=1200&q=80",
    "Handicrafts": "https://images.unsplash.com/photo-1513519245088-0e12902e5a38?auto=format&fit=crop&w=1200&q=80",
    "Electronics": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80",
    "Automotive": "https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1200&q=80",
    "Gems & Jewellery": "https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?auto=format&fit=crop&w=1200&q=80",
    "Logistics": "https://images.unsplash.com/photo-1494412519320-aa613dfb7738?auto=format&fit=crop&w=1200&q=80",
    "Multi-sector": "https://images.unsplash.com/photo-1505373877841-8d25f7d46678?auto=format&fit=crop&w=1200&q=80",
}


def _now():
    return datetime.now(timezone.utc)


def _iso(dt=None):
    return (dt or _now()).isoformat()


def _next_edition(entry: Dict[str, Any], today: date) -> date:
    """Next start date for a recurring event, always today or later."""
    month, day, rec = entry["month"], entry["day"], entry.get("recurrence", "annual")
    year = today.year
    for _ in range(6):
        if rec == "biennial-odd" and year % 2 == 0:
            year += 1
            continue
        if rec == "biennial-even" and year % 2 == 1:
            year += 1
            continue
        try:
            start = date(year, month, day)
        except ValueError:
            start = date(year, month, 28)
        if start >= today:
            return start
        year += 1 if rec == "annual" else 2
    return date(today.year + 1, month, min(day, 28))


async def refresh_catalogue() -> Dict[str, Any]:
    """Roll every catalogued expo forward to its next edition (idempotent upsert)."""
    today = _now().date()
    created = updated = 0
    for e in CATALOGUE:
        start = _next_edition(e, today)
        end = start + timedelta(days=max(1, e.get("days", 3)) - 1)
        eid = f"cat-{e['slug']}"
        doc = {
            "id": eid, "name": e["name"], "category": e["category"], "country": e["country"],
            "city": e["city"], "venueName": e["venueName"], "industry": e["industry"],
            "audience": e["audience"], "organizer": e["organizer"], "website": e.get("website", ""),
            "startDate": start.isoformat(), "endDate": end.isoformat(),
            "description": (f"{e['name']} — {e['industry']} trade event in {e['city']}, {e['country']}, "
                            f"organised by {e['organizer']}. Dates are indicative for the next edition; "
                            f"confirm exact dates and registration on the organiser's website."),
            "image": IMAGE_BY_INDUSTRY.get(e["industry"], IMAGE_BY_INDUSTRY["Multi-sector"]),
            "status": "published", "paid": True, "featured": False,
            "owner": "engine", "ownerType": "engine", "source": "catalogue",
            "recurrence": e.get("recurrence", "annual"), "datesIndicative": True,
            "products": "", "contactEmail": "", "contactName": e["organizer"],
            "region": "IN" if e["country"] == "India" else "INTL",
            "expiresAt": _iso(datetime.combine(end, datetime.min.time(), timezone.utc) + timedelta(days=1)),
            "updatedAt": _iso(),
        }
        res = await EVENTS.update_one({"_id": eid}, {"$set": doc, "$setOnInsert": {"createdAt": _iso()}},
                                      upsert=True)
        if res.upserted_id:
            created += 1
        elif res.modified_count:
            updated += 1
    return {"catalogue": len(CATALOGUE), "created": created, "updated": updated}


DISCOVERY_SYSTEM = (
    "You are the Vametra AI Expo Discovery engine. You list REAL, well-known international "
    "trade fairs, expos and business events that are scheduled to take place in the given window. "
    "Only include events you are confident actually exist, with their official organiser. "
    "Never invent an event. Respond with STRICT JSON only."
)


async def discover_events(limit: int = 12) -> Dict[str, Any]:
    """Daily AI pass — proposes NEW events into the admin approval queue (never auto-published)."""
    import llm_util
    today = _now().date()
    window_end = today + timedelta(days=240)
    known = ", ".join(e["name"] for e in CATALOGUE[:40])
    prompt = (
        f"List up to {limit} major international trade fairs / expos / trade summits starting between "
        f"{today.isoformat()} and {window_end.isoformat()} that are NOT in this list: {known}.\n"
        'Return JSON: {"events":[{"name":"","category":"Trade Fair","country":"","city":"",'
        '"venueName":"","industry":"","audience":"","organizer":"","website":"",'
        '"startDate":"YYYY-MM-DD","endDate":"YYYY-MM-DD","description":""}]}'
    )
    raw = await llm_util.generate(DISCOVERY_SYSTEM, prompt, session="expo-discovery")
    if not raw:
        return {"proposed": 0, "reason": "no llm response"}
    txt = raw.strip()
    if "```" in txt:
        txt = txt.split("```")[1].replace("json", "", 1).strip()
    try:
        data = json.loads(txt[txt.find("{"): txt.rfind("}") + 1])
    except Exception as exc:
        logging.warning("Expo discovery parse failed: %s", exc)
        return {"proposed": 0, "reason": "unparseable"}

    proposed = 0
    for ev in (data.get("events") or [])[:limit]:
        name = (ev.get("name") or "").strip()
        start = (ev.get("startDate") or "").strip()
        if not name or len(start) != 10:
            continue
        if await EVENTS.find_one({"name": {"$regex": f"^{name[:40]}", "$options": "i"}}):
            continue
        eid = f"disc-{abs(hash(name + start)) % (10 ** 12)}"
        end = ev.get("endDate") or start
        await EVENTS.update_one({"_id": eid}, {"$set": {
            "id": eid, "name": name, "category": ev.get("category") or "Trade Fair",
            "country": ev.get("country") or "", "city": ev.get("city") or "",
            "venueName": ev.get("venueName") or "", "industry": ev.get("industry") or "Multi-sector",
            "audience": ev.get("audience") or "All", "organizer": ev.get("organizer") or "",
            "website": ev.get("website") or "", "startDate": start, "endDate": end,
            "description": ev.get("description") or "",
            "image": IMAGE_BY_INDUSTRY.get(ev.get("industry"), IMAGE_BY_INDUSTRY["Multi-sector"]),
            "status": "pending", "source": "ai-discovery", "owner": "engine", "ownerType": "engine",
            "paid": True, "featured": False, "datesIndicative": True,
            "region": "IN" if ev.get("country") == "India" else "INTL",
            "contactEmail": "", "contactName": ev.get("organizer") or "",
            "updatedAt": _iso()}, "$setOnInsert": {"createdAt": _iso()}}, upsert=True)
        proposed += 1
    return {"proposed": proposed}


async def run_engine(trigger: str = "scheduler") -> Dict[str, Any]:
    """Daily: roll the catalogue forward, expire finished events, discover new candidates."""
    started = _iso()
    result: Dict[str, Any] = {"trigger": trigger, "startedAt": started}
    try:
        result.update(await refresh_catalogue())
    except Exception as exc:
        logging.warning("Catalogue refresh failed: %s", exc)
        result["catalogueError"] = str(exc)
    try:
        import event_listings
        await event_listings.event_expiry_sweep()
    except Exception as exc:
        logging.warning("Expiry sweep failed: %s", exc)
    try:
        result.update(await discover_events())
    except Exception as exc:
        logging.warning("Expo discovery failed: %s", exc)
        result["discoveryError"] = str(exc)

    today = _now().date().isoformat()
    published = await EVENTS.count_documents({"status": {"$in": ["published", "approved"]}})
    upcoming = await EVENTS.count_documents({"status": {"$in": ["published", "approved"]},
                                             "endDate": {"$gte": today}})
    pending_ai = await EVENTS.count_documents({"status": "pending", "source": "ai-discovery"})
    result.update({"finishedAt": _iso(), "published": published, "upcoming": upcoming,
                   "pendingDiscovery": pending_ai})
    await META.replace_one({"_id": "heartbeat"}, {"_id": "heartbeat", **result}, upsert=True)
    logging.info("Expo engine run: %s", result)
    return result


async def engine_status() -> Dict[str, Any]:
    meta = await META.find_one({"_id": "heartbeat"}) or {}
    today = _now().date().isoformat()
    upcoming = await EVENTS.count_documents({"status": {"$in": ["published", "approved"]},
                                             "endDate": {"$gte": today}})
    return {"lastUpdated": meta.get("finishedAt"), "upcoming": upcoming,
            "catalogue": len(CATALOGUE), "pendingDiscovery": meta.get("pendingDiscovery", 0),
            "live": True}


_sched = None


def start_expo_engine():
    """Daily at 01:30 UTC + a warm-up shortly after boot."""
    global _sched
    if _sched:
        return
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.date import DateTrigger
    _sched = AsyncIOScheduler(timezone="UTC")
    _sched.add_job(run_engine, CronTrigger(hour=1, minute=30), id="expo-daily",
                   replace_existing=True, misfire_grace_time=3600)
    _sched.add_job(refresh_catalogue, DateTrigger(run_date=_now() + timedelta(seconds=20)),
                   id="expo-warmup", replace_existing=True)
    _sched.start()
    logging.info("Expo & Events engine scheduled (daily 01:30 UTC).")
