"""Playwright snippet used with mcp_browser_automation for iteration 44 UI retest.

It assumes an async Playwright `page` object is provided by the browser tool.
"""

await page.set_viewport_size({"width": 1920, "height": 1080})

FORBIDDEN_UI = [
    "GLEIF",
    "GLEI LEI",
    "EU Tenders Electronic Daily",
    "TED",
    "trade.gov",
    "Companies House",
    "Brønnøysund",
    "ARES",
    "SIRENE",
]
SOURCE_LINK_SELECTORS = (
    'a[href*="ted.europa.eu"], a[href*="gleif.org"], a[href*="trade.gov"], '
    'a[href*="company-information.service.gov.uk"], a[href*="brreg.no"], '
    'a[href*="ares.gov.cz"], a[href*="insee.fr"]'
)

try:
    print("Opening anonymous buyer profile")
    await page.goto("https://vbie-verify.preview.emergentagent.com/buyers/LN-buyer-C3FYC9ZJHCKS7VCGKBENZNSDHZ", wait_until="domcontentloaded")
    profile_loaded = False
    for attempt in range(8):
        try:
            await page.get_by_test_id("buyer-profile-header").wait_for(timeout=5000)
            await page.get_by_test_id("buyer-paywall").wait_for(timeout=5000)
            profile_loaded = True
            print(f"Profile loaded on attempt {attempt + 1}")
            break
        except Exception:
            print(f"Profile not ready on attempt {attempt + 1}; reloading")
            await page.reload(wait_until="domcontentloaded")
    if not profile_loaded:
        raise Exception("Anonymous buyer profile/paywall did not load within retry window")

    paywall_text = await page.get_by_test_id("buyer-paywall").inner_text()
    if "verified contact details locked" in paywall_text.lower():
        print("PASS: Paywall shows Verified contact details locked")
    else:
        raise Exception(f"Paywall missing lock copy. Text: {paywall_text[:500]}")

    body_text = await page.locator("body").inner_text()
    forbidden_hits = [term for term in FORBIDDEN_UI if term in body_text]
    if forbidden_hits:
        raise Exception(f"Profile text contains forbidden source/LEI terms: {forbidden_hits}")
    print("PASS: Profile text has no forbidden source/LEI terms")

    website_text_count = await page.get_by_text("Website", exact=True).count()
    if website_text_count == 0:
        print("PASS: Anonymous profile has no Website button/text")
    else:
        raise Exception(f"Anonymous profile unexpectedly contains Website text count={website_text_count}")

    source_hrefs = await page.evaluate(f"""() => Array.from(document.querySelectorAll('{SOURCE_LINK_SELECTORS}')).map(a => a.href)""")
    if source_hrefs:
        raise Exception(f"Profile contains clickable source links: {source_hrefs}")
    print("PASS: Profile contains no clickable source links")

    lei_count = await page.get_by_test_id("intel-lei").count()
    if lei_count:
        lei_text = await page.get_by_test_id("intel-lei").inner_text()
        if "Globally verified company identity" in lei_text and "LEI" not in lei_text and "GLEIF" not in lei_text:
            print("PASS: LEI indicator is relabelled generically")
        else:
            raise Exception(f"LEI indicator is not generic: {lei_text}")
    else:
        print("INFO: LEI indicator not visible on this profile")

    print("Opening buyers list / source transparency")
    await page.goto("https://vbie-verify.preview.emergentagent.com/buyers", wait_until="domcontentloaded")
    list_loaded = False
    for attempt in range(8):
        try:
            await page.get_by_test_id("buyer-result-count").wait_for(timeout=5000)
            await page.get_by_test_id("buyer-sources-section").wait_for(timeout=5000)
            list_loaded = True
            print(f"Buyers list/source section loaded on attempt {attempt + 1}")
            break
        except Exception:
            print(f"Buyers list/source section not ready on attempt {attempt + 1}; reloading")
            await page.reload(wait_until="domcontentloaded")
    if not list_loaded:
        raise Exception("Buyers list or Source Transparency section did not load within retry window")

    list_text = await page.locator("body").inner_text()
    list_hits = [term for term in ["GLEIF", "EU Tenders Electronic Daily", "TED", "Companies House", "Brønnøysund", "ARES", "SIRENE", "trade.gov"] if term in list_text]
    if list_hits:
        raise Exception(f"Buyers list/source transparency text contains forbidden terms: {list_hits}")
    print("PASS: Buyers list/source transparency has no forbidden source names")

    list_source_hrefs = await page.evaluate(f"""() => Array.from(document.querySelectorAll('{SOURCE_LINK_SELECTORS}')).map(a => a.href)""")
    if list_source_hrefs:
        raise Exception(f"Buyers list contains clickable source links: {list_source_hrefs}")
    print("PASS: Buyers list/source transparency contains no clickable source links")

    # Get error messages using specific selectors
    error_text = await page.evaluate("""() => {
    const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
    return errorElements.map(el => el.textContent).join(", ");
    }""")
    if error_text:
        print(f"Found error message: {error_text}")
    else:
        print("No error messages found on the page")

    print("UI_PRIVACY_RETEST_PASS")
except Exception as exc:
    print(f"UI_PRIVACY_RETEST_FAIL: {exc}")
    raise