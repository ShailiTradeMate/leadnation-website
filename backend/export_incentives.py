"""Country export-support registry — every exporting country's own official schemes.

Why a curated registry and not a scrape: there is no single machine-readable global
source for export incentives. Each entry therefore carries the administering
authority and the OFFICIAL government/agency URL so the user can verify the current
rules themselves. Rate-level figures are only ever served where an official rate
schedule exists and we actually hold it (today: India RoDTEP, duty_engine).

Nothing here states a percentage. `gives` describes the benefit in words.
"""
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/incentives", tags=["export-incentives"])

VERIFIED_ON = "2026-06"

EU_NOTE = ("EU/WTO rules prohibit direct export subsidies. Support for EU exporters comes "
           "through state-backed export credit insurance and guarantees, plus duty relief "
           "under the Union Customs Code (inward/outward processing, customs warehousing).")

DISCLAIMER = ("Scheme names, eligibility and rates change with each budget or trade-policy "
              "notification. Vametra AI links the administering authority's official page for "
              "every scheme — confirm current eligibility and rates there (or with a licensed "
              "broker/consultant) before you price or contract an export.")


def _s(name, authority, url, gives, kind):
    return {"name": name, "authority": authority, "url": url, "gives": gives, "kind": kind}


# code (ISO numeric, as used by WITS/duty_engine) -> country export-support profile
REGISTRY = {
    "356": {"name": "India", "schemes": [
        _s("RoDTEP", "Directorate General of Foreign Trade (DGFT)", "https://www.dgft.gov.in/CP/?opt=RoDTEP",
           "Remission of embedded duties & taxes on exported goods, paid as a transferable e-scrip on FOB value. Rate schedule in Appendix 4R.", "remission"),
        _s("Duty Drawback", "Central Board of Indirect Taxes & Customs (CBIC)", "https://www.cbic.gov.in",
           "Refund of customs duty paid on imported inputs used in exported goods (All Industry Rates or brand rate).", "drawback"),
        _s("Advance Authorisation", "DGFT", "https://www.dgft.gov.in",
           "Duty-free import of inputs against an export obligation.", "temporary-import"),
        _s("EPCG Scheme", "DGFT", "https://www.dgft.gov.in",
           "Zero-duty import of capital goods against an export obligation.", "temporary-import"),
        _s("Export Credit Insurance", "ECGC Ltd", "https://www.ecgc.in",
           "Cover against buyer payment default and country risk; enables packing-credit terms from banks.", "insurance"),
        _s("Export Finance", "India Exim Bank", "https://www.eximbankindia.in",
           "Pre- and post-shipment credit, buyer's credit and project export finance.", "finance"),
    ], "hasRateSchedule": True},

    "842": {"name": "United States", "schemes": [
        _s("Duty Drawback (19 CFR 190)", "U.S. Customs and Border Protection", "https://www.cbp.gov/trade/programs-administration/entry-summary/drawback-overview",
           "Refund of duties, taxes and fees on imported goods that are later exported or destroyed.", "drawback"),
        _s("EXIM Working Capital & Credit Insurance", "Export-Import Bank of the United States", "https://www.exim.gov",
           "Working-capital loan guarantees, export credit insurance and buyer financing.", "finance"),
        _s("Export assistance & market entry", "International Trade Administration (trade.gov)", "https://www.trade.gov",
           "Market research, partner search and U.S. Commercial Service counselling.", "grant"),
    ]},

    "826": {"name": "United Kingdom", "schemes": [
        _s("UK Export Finance", "UK Export Finance (UKEF)", "https://www.gov.uk/government/organisations/uk-export-finance",
           "Government-backed export insurance, buyer credit and working-capital guarantees.", "finance"),
        _s("Export support service", "Department for Business and Trade", "https://www.great.gov.uk",
           "Market guidance, exporter checklists and trade advisers.", "grant"),
    ]},

    "124": {"name": "Canada", "schemes": [
        _s("Duty Drawback Program", "Canada Border Services Agency", "https://www.cbsa-asfc.gc.ca/import/ddr-red/drawback-eng.html",
           "Refund of duties paid on imported goods subsequently exported (Form K32, via CARM).", "drawback"),
        _s("EDC trade finance & insurance", "Export Development Canada", "https://www.edc.ca",
           "Credit insurance, buyer financing and working-capital guarantees.", "finance"),
        _s("CanExport / Trade Commissioner Service", "Global Affairs Canada", "https://www.tradecommissioner.gc.ca",
           "Market-development funding and in-market trade commissioner support.", "grant"),
    ]},

    "36": {"name": "Australia", "schemes": [
        _s("Duty Drawback Scheme", "Australian Border Force", "https://www.abf.gov.au/importing-exporting-and-manufacturing/exporting/duty-drawback-scheme",
           "Refund of customs duty paid on imported goods that are then exported.", "drawback"),
        _s("Export Market Development Grants (EMDG)", "Austrade", "https://www.austrade.gov.au",
           "Co-funding of eligible export promotion and market-entry costs for SMEs.", "grant"),
        _s("Export Finance Australia", "Export Finance Australia", "https://www.exportfinance.gov.au",
           "Loans, guarantees and bonds where commercial finance is unavailable.", "finance"),
    ]},

    "276": {"name": "Germany", "schemes": [
        _s("Hermes Cover (federal export credit guarantees)", "AGA Portal / Euler Hermes for the Federal Government", "https://www.agaportal.de/en/aga/index.html",
           "State guarantees against non-payment on export receivables.", "insurance"),
        _s("Inward/outward processing & customs warehousing", "EU Union Customs Code (DG TAXUD)", "https://taxation-customs.ec.europa.eu",
           "Duty relief on inputs processed for re-export.", "temporary-import"),
    ], "note": EU_NOTE},

    "250": {"name": "France", "schemes": [
        _s("Assurance-crédit export", "Bpifrance Assurance Export (for the French State)", "https://assurance-export.bpifrance.fr/en/",
           "Public export credit insurance, prospecting insurance and guarantees.", "insurance"),
        _s("Team France Export", "Business France", "https://www.businessfrance.fr",
           "Market-entry support, trade missions and exporter coaching.", "grant"),
    ], "note": EU_NOTE},

    "380": {"name": "Italy", "schemes": [
        _s("SACE export credit insurance & guarantees", "SACE S.p.A.", "https://www.sace.it/en",
           "Insurance and state guarantees on export receivables and buyer credit.", "insurance"),
        _s("SIMEST internationalisation finance", "SIMEST (CDP Group)", "https://www.simest.it",
           "Subsidised finance for export market development and foreign investment.", "finance"),
    ], "note": EU_NOTE},

    "528": {"name": "Netherlands", "schemes": [
        _s("Dutch State export credit insurance", "Atradius Dutch State Business", "https://atradiusdutchstatebusiness.nl/en/",
           "State-backed export credit insurance and guarantees.", "insurance"),
        _s("Internationalisation support", "Netherlands Enterprise Agency (RVO)", "https://www.rvo.nl",
           "Market information, missions and internationalisation subsidies.", "grant"),
    ], "note": EU_NOTE},

    "724": {"name": "Spain", "schemes": [
        _s("Export credit insurance on State account", "CESCE", "https://www.cesce.es/en/",
           "Public export credit insurance against commercial and political risk.", "insurance"),
        _s("ICEX internationalisation programmes", "ICEX España", "https://www.icex.es",
           "Market research, trade fairs and export-promotion funding.", "grant"),
    ], "note": EU_NOTE},

    "616": {"name": "Poland", "schemes": [
        _s("KUKE export credit insurance & guarantees", "KUKE S.A.", "https://www.kuke.com.pl",
           "State-supported insurance and guarantees on export contracts.", "insurance"),
        _s("PAIH export support", "Polish Investment & Trade Agency", "https://www.paih.gov.pl",
           "Market entry advice and foreign trade office network.", "grant"),
    ], "note": EU_NOTE},

    "752": {"name": "Sweden", "schemes": [
        _s("EKN export credit guarantees", "Exportkreditnämnden (EKN)", "https://www.ekn.se/en/",
           "Guarantees covering non-payment risk on export receivables.", "insurance"),
        _s("SEK export credits", "Svensk Exportkredit (SEK)", "https://www.sek.se/en/",
           "Buyer and supplier export credit financing.", "finance"),
    ], "note": EU_NOTE},

    "246": {"name": "Finland", "schemes": [
        _s("Finnvera export credit guarantees", "Finnvera plc", "https://www.finnvera.fi/eng/",
           "Export credit guarantees, financing and internationalisation loans.", "finance"),
    ], "note": EU_NOTE},

    "208": {"name": "Denmark", "schemes": [
        _s("EIFO export guarantees & finance", "Export and Investment Fund of Denmark (EIFO)", "https://eifo.dk/en",
           "Export credit guarantees, working capital and buyer finance.", "finance"),
    ], "note": EU_NOTE},

    "56": {"name": "Belgium", "schemes": [
        _s("Credendo export credit insurance", "Credendo – Export Credit Agency", "https://credendo.com/en/",
           "Public export credit insurance and guarantees.", "insurance"),
    ], "note": EU_NOTE},

    "40": {"name": "Austria", "schemes": [
        _s("Federal export guarantees", "Oesterreichische Kontrollbank (OeKB)", "https://www.oekb.at/en/",
           "Export guarantees and refinancing on behalf of the Republic of Austria.", "insurance"),
    ], "note": EU_NOTE},

    "756": {"name": "Switzerland", "schemes": [
        _s("SERV export risk insurance", "Swiss Export Risk Insurance (SERV)", "https://www.serv-ch.com/en/",
           "Insurance of export transactions against commercial and political risk.", "insurance"),
    ]},

    "578": {"name": "Norway", "schemes": [
        _s("Eksfin export loans & guarantees", "Export Finance Norway (Eksfin)", "https://www.eksfin.no/en/",
           "Government-backed export loans and guarantees.", "finance"),
    ]},

    "372": {"name": "Ireland", "schemes": [
        _s("Enterprise Ireland export supports", "Enterprise Ireland", "https://www.enterprise-ireland.com",
           "Market discovery funding, trade missions and exporter development.", "grant"),
    ], "note": EU_NOTE},

    "620": {"name": "Portugal", "schemes": [
        _s("COSEC export credit insurance (State account)", "COSEC", "https://www.cosec.pt",
           "Export credit insurance and guarantees on the Portuguese State account.", "insurance"),
        _s("AICEP internationalisation support", "AICEP Portugal Global", "https://www.aicep.pt",
           "Market intelligence, missions and internationalisation incentives.", "grant"),
    ], "note": EU_NOTE},

    "300": {"name": "Greece", "schemes": [
        _s("Enterprise Greece export promotion", "Enterprise Greece", "https://www.enterprisegreece.gov.gr",
           "Export promotion, trade fair participation and exporter services.", "grant"),
    ], "note": EU_NOTE},

    "203": {"name": "Czechia", "schemes": [
        _s("EGAP export credit insurance", "EGAP", "https://www.egap.cz/en",
           "State export credit insurance against commercial and political risk.", "insurance"),
        _s("CzechTrade export services", "CzechTrade", "https://www.czechtrade.cz",
           "Foreign office network, market research and export consulting.", "grant"),
    ], "note": EU_NOTE},

    "348": {"name": "Hungary", "schemes": [
        _s("EXIM Hungary export finance & insurance", "Hungarian Export-Import Bank / MEHIB", "https://exim.hu",
           "Export credit, guarantees and insurance for Hungarian exporters.", "finance"),
    ], "note": EU_NOTE},

    "156": {"name": "China", "schemes": [
        _s("Export VAT / consumption tax refund (exemption)", "State Taxation Administration", "https://www.chinatax.gov.cn",
           "Refund or exemption of VAT and consumption tax on exported goods; filed through the electronic tax bureau / single window.", "tax-refund"),
        _s("Sinosure export credit insurance", "China Export & Credit Insurance Corporation", "https://www.sinosure.com.cn",
           "Short- and medium-term export credit insurance.", "insurance"),
    ]},

    "392": {"name": "Japan", "schemes": [
        _s("NEXI trade insurance", "Nippon Export and Investment Insurance", "https://www.nexi.go.jp/en/",
           "Export credit and overseas investment insurance.", "insurance"),
        _s("JBIC export credit", "Japan Bank for International Cooperation", "https://www.jbic.go.jp/en/",
           "Buyer credit and project finance for Japanese exports.", "finance"),
        _s("JETRO export support", "JETRO", "https://www.jetro.go.jp/en/",
           "Market information, matchmaking and export advisers.", "grant"),
    ]},

    "410": {"name": "South Korea", "schemes": [
        _s("K-SURE trade insurance", "Korea Trade Insurance Corporation", "https://www.ksure.or.kr/english/index.jsp",
           "Export credit insurance and receivable protection.", "insurance"),
        _s("KEXIM export credit", "Export-Import Bank of Korea", "https://www.koreaexim.go.kr/en/",
           "Export loans, guarantees and overseas project finance.", "finance"),
        _s("KOTRA export marketing", "KOTRA", "https://www.kotra.or.kr",
           "Buyer matchmaking, trade fairs and overseas offices.", "grant"),
    ]},

    "792": {"name": "Türkiye", "schemes": [
        _s("Turquality & export support programmes", "Ministry of Trade", "https://www.ticaret.gov.tr",
           "State support for branding, market entry, trade fairs, certification and overseas store/office costs.", "grant"),
        _s("Türk Eximbank credit & insurance", "Türk Eximbank", "https://www.eximbank.gov.tr",
           "Pre-shipment credit, buyer credit and export receivable insurance.", "finance"),
    ]},

    "76": {"name": "Brazil", "schemes": [
        _s("Reintegra", "Receita Federal / Ministry of Finance", "https://www.gov.br/receitafederal",
           "Credit on export revenue to offset residual taxes in the production chain.", "tax-refund"),
        _s("Drawback", "SECEX / Receita Federal", "https://www.gov.br/mdic",
           "Suspension, exemption or refund of duties and taxes on inputs used in exported goods.", "drawback"),
        _s("Apex-Brasil export promotion", "Apex-Brasil", "https://apexbrasil.com.br",
           "Market intelligence, trade missions and buyer matchmaking.", "grant"),
    ]},

    "484": {"name": "Mexico", "schemes": [
        _s("IMMEX programme", "Secretaría de Economía", "https://www.snice.gob.mx/cs/avi/snice/programasdefom.immex.html",
           "Temporary import of inputs and machinery for export production with deferred duties, VAT and countervailing duties.", "temporary-import"),
        _s("Bancomext export finance", "Bancomext", "https://www.bancomext.com",
           "Working capital, guarantees and buyer financing for exporters.", "finance"),
    ]},

    "360": {"name": "Indonesia", "schemes": [
        _s("KITE (Kemudahan Impor Tujuan Ekspor)", "Directorate General of Customs and Excise", "https://www.beacukai.go.id",
           "Import duty exemption/refund and VAT non-collection on inputs for export production.", "temporary-import"),
        _s("LPEI export finance", "Indonesia Eximbank (LPEI)", "https://www.indonesiaeximbank.go.id",
           "Export working capital, guarantees and insurance.", "finance"),
    ]},

    "764": {"name": "Thailand", "schemes": [
        _s("BOI investment promotion", "Thailand Board of Investment", "https://www.boi.go.th",
           "Corporate income tax exemption and duty exemption on machinery/raw materials for promoted (largely export-oriented) activities.", "tax-refund"),
        _s("EXIM Thailand export credit", "Export-Import Bank of Thailand", "https://www.exim.go.th",
           "Pre/post-shipment credit and export credit insurance.", "finance"),
        _s("DITP export promotion", "Department of International Trade Promotion", "https://www.ditp.go.th",
           "Trade fairs, buyer matching and exporter training.", "grant"),
    ]},

    "458": {"name": "Malaysia", "schemes": [
        _s("New Incentive Framework (tax incentives)", "MIDA", "https://www.mida.gov.my",
           "Outcome-based tax incentives for manufacturing and services investments, including export-oriented activity.", "tax-refund"),
        _s("MATRADE export promotion", "MATRADE", "https://www.matrade.gov.my",
           "Market development grants, trade missions and exporter directories.", "grant"),
        _s("EXIM Bank Malaysia", "Export-Import Bank of Malaysia", "https://www.exim.com.my",
           "Export credit, guarantees and credit insurance.", "finance"),
    ]},

    "704": {"name": "Vietnam", "schemes": [
        _s("Export duty & tax policy and trade promotion", "Ministry of Industry and Trade (MOIT)", "https://moit.gov.vn",
           "Export-processing duty relief and national trade-promotion programme.", "grant"),
        _s("Vietrade trade promotion", "Vietnam Trade Promotion Agency", "https://vietrade.gov.vn",
           "Trade fairs, market information and buyer matchmaking.", "grant"),
    ]},

    "702": {"name": "Singapore", "schemes": [
        _s("Market Readiness Assistance & enterprise grants", "Enterprise Singapore", "https://www.enterprisesg.gov.sg",
           "Co-funding of overseas market set-up, promotion and business development.", "grant"),
    ]},

    "50": {"name": "Bangladesh", "schemes": [
        _s("Export cash incentives", "Bangladesh Bank", "https://www.bb.org.bd",
           "Sector-wise cash incentive on repatriated export proceeds, notified by F.E. circular (being phased down with LDC graduation).", "grant"),
        _s("EPB export facilitation", "Export Promotion Bureau", "https://epb.gov.bd",
           "Registration (ERC), market promotion and exporter services.", "grant"),
    ]},

    "586": {"name": "Pakistan", "schemes": [
        _s("Export Finance Scheme (EFS)", "State Bank of Pakistan", "https://www.sbp.org.pk",
           "Concessional pre/post-shipment export refinancing through banks.", "finance"),
        _s("TDAP export promotion", "Trade Development Authority of Pakistan", "https://www.tdap.gov.pk",
           "Trade fairs, delegations and market development support.", "grant"),
        _s("EXIM Bank of Pakistan", "EXIM Bank of Pakistan", "https://eximbank.gov.pk",
           "Export credit guarantees and insurance.", "finance"),
    ]},

    "144": {"name": "Sri Lanka", "schemes": [
        _s("EDB exporter development", "Sri Lanka Export Development Board", "https://www.srilankabusiness.com",
           "Market development assistance, exporter training and buyer matchmaking.", "grant"),
    ]},

    "608": {"name": "Philippines", "schemes": [
        _s("DTI export development", "Department of Trade and Industry", "https://www.dti.gov.ph",
           "Export marketing assistance under the Philippine Export Development Plan.", "grant"),
        _s("PHILGUARANTEE export guarantees", "Philippine Guarantee Corporation", "https://www.philguarantee.gov.ph",
           "Guarantees and insurance supporting export credit.", "finance"),
    ]},

    "818": {"name": "Egypt", "schemes": [
        _s("Export support programme (performance-based rebate)", "Export Development Fund / ITIDA (sector programmes)", "https://itida.gov.eg/English/Programs/electronics-embedded-systems-export-support/Pages/default.aspx",
           "Cash incentive linked to the year-on-year increase in export proceeds, by eligible sector.", "grant"),
    ]},

    "784": {"name": "United Arab Emirates", "schemes": [
        _s("ECI trade credit insurance & financing", "Etihad Credit Insurance (ECI)", "https://www.eci.gov.ae/en",
           "Federal export credit insurance, guarantees and working-capital solutions for non-oil exporters.", "insurance"),
        _s("Xport Xponential", "Etihad Credit Insurance (ECI)", "https://www.eci.gov.ae/en/xponential-program",
           "Trade finance access, market guidance and federal trade missions to CEPA markets.", "grant"),
    ]},

    "682": {"name": "Saudi Arabia", "schemes": [
        _s("Saudi EXIM financing & insurance", "Saudi Export-Import Bank", "https://saudiexim.gov.sa/en/Pages/default.aspx",
           "Export credit, buyer finance, guarantees and credit insurance for non-oil exports.", "finance"),
    ]},

    "634": {"name": "Qatar", "schemes": [
        _s("Tasdeer export development", "Qatar Development Bank", "https://www.qdb.qa",
           "Export capacity building, trade missions, market studies and exporter directory.", "grant"),
    ]},

    "48": {"name": "Bahrain", "schemes": [
        _s("Tamkeen enterprise & export support", "Tamkeen", "https://www.tamkeen.bh",
           "Co-funding of business growth, certification and market expansion costs.", "grant"),
    ]},

    "376": {"name": "Israel", "schemes": [
        _s("ASHRA foreign trade risks insurance", "ASHRA – Israel Foreign Trade Risks Insurance Corporation", "https://www.ashra.gov.il/eng/",
           "Medium and long-term export credit insurance backed by the State.", "insurance"),
        _s("Israel Export Institute", "Israel Export and International Cooperation Institute", "https://www.export.gov.il",
           "Market entry, delegations and buyer matchmaking.", "grant"),
    ]},

    "710": {"name": "South Africa", "schemes": [
        _s("Export Marketing & Investment Assistance (EMIA)", "Department of Trade, Industry and Competition", "https://www.thedtic.gov.za/financial-and-non-financial-support/incentives/export-marketing-and-investment-assistance/",
           "Compensation of market-development costs: primary market research, national pavilions, inward buying missions.", "grant"),
        _s("ECIC export credit insurance", "Export Credit Insurance Corporation of South Africa", "https://www.ecic.co.za",
           "Political and commercial risk insurance for capital goods and services exports.", "insurance"),
    ]},

    "404": {"name": "Kenya", "schemes": [
        _s("KEPROBA export promotion", "Kenya Export Promotion and Branding Agency", "https://makeitkenya.go.ke",
           "Market information, exporter capacity building and country branding support.", "grant"),
    ]},

    "566": {"name": "Nigeria", "schemes": [
        _s("NEXIM export credit", "Nigerian Export-Import Bank", "https://neximbank.gov.ng",
           "Export credit facilities, guarantees and trade advisory.", "finance"),
        _s("NEPC export development", "Nigerian Export Promotion Council", "https://nepc.gov.ng",
           "Exporter registration, market development and export expansion support.", "grant"),
    ]},

    "643": {"name": "Russia", "schemes": [
        _s("Russian Export Center support", "Russian Export Center (REC)", "https://www.exportcenter.ru/en/",
           "One-stop export finance, insurance (EXIAR), certification and trade-event support.", "finance"),
    ]},

    "152": {"name": "Chile", "schemes": [
        _s("ProChile export promotion", "ProChile (Ministry of Foreign Affairs)", "https://www.prochile.gob.cl/en",
           "Market intelligence, promotion funds and 50+ commercial offices abroad.", "grant"),
    ]},

    "170": {"name": "Colombia", "schemes": [
        _s("ProColombia export promotion", "ProColombia", "https://procolombia.co/en",
           "Buyer matchmaking, market studies and export promotion programmes.", "grant"),
        _s("Bancóldex export finance", "Bancóldex", "https://www.bancoldex.com",
           "Working capital and investment credit lines for exporters.", "finance"),
    ]},

    "604": {"name": "Peru", "schemes": [
        _s("PromPerú export services", "PromPerú", "https://exportemos.pe",
           "Commercial intelligence, exporter training and market-entry services.", "grant"),
    ]},

    "554": {"name": "New Zealand", "schemes": [
        _s("NZTE export services", "New Zealand Trade & Enterprise", "https://www.nzte.govt.nz",
           "Export advisers, market intelligence and growth funding.", "grant"),
        _s("NZECO export credit", "New Zealand Export Credit", "https://www.nzeco.govt.nz",
           "Government guarantees and insurance for export contracts.", "insurance"),
    ]},
}


def for_country(code: str):
    """Export-support profile for an exporting country, or a transparent 'not covered' answer."""
    key = (code or "").lstrip("0") or code
    entry = REGISTRY.get(key) or REGISTRY.get(code or "")
    if not entry:
        return {"covered": False, "schemes": [],
                "note": "Vametra AI has not yet verified an official export-support source for this "
                        "country. Check the national trade ministry or export promotion agency — we "
                        "only publish schemes we can link to an official page.",
                "verifiedOn": VERIFIED_ON, "disclaimer": DISCLAIMER}
    return {"covered": True, "country": entry["name"], "schemes": entry["schemes"],
            "hasRateSchedule": bool(entry.get("hasRateSchedule")),
            "note": entry.get("note"), "verifiedOn": VERIFIED_ON, "disclaimer": DISCLAIMER}


@router.get("/countries")
async def covered_countries():
    """Every exporting country whose own official export-support schemes we publish."""
    rows = [{"code": code, "name": e["name"], "schemes": len(e["schemes"]),
             "hasRateSchedule": bool(e.get("hasRateSchedule")),
             "kinds": sorted({s["kind"] for s in e["schemes"]})}
            for code, e in REGISTRY.items()]
    rows.sort(key=lambda r: r["name"])
    return {"total": len(rows), "countries": rows, "verifiedOn": VERIFIED_ON,
            "disclaimer": DISCLAIMER}


@router.get("/{code}")
async def country_incentives(code: str):
    data = for_country(code)
    if not data["covered"] and code not in REGISTRY:
        # Still a 200 with an honest answer for known-but-uncovered codes; 404 only for junk input.
        if not code.replace("0", "").isdigit():
            raise HTTPException(status_code=404, detail="Unknown country code")
    return {"ok": True, "code": code, **data}
