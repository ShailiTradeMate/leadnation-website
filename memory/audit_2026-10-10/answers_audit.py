"""Production audit of /api/answers/index + every answer document (HTML + Markdown)."""
import csv, json, re, hashlib, collections, time
from concurrent.futures import ThreadPoolExecutor
import requests

OUT = "/app/memory/audit_2026-10-10/"
S = requests.Session()
S.headers["User-Agent"] = "Mozilla/5.0 (compatible; GPTBot/1.0; +https://openai.com/gptbot)"
idx = S.get("https://vametra.com/api/answers/index", timeout=60)
print("index", idx.status_code, idx.headers.get("content-type"), len(idx.content), flush=True)
items = idx.json()["items"]
xml = requests.get("https://vametra.com/api/sitemap.xml", timeout=120).text
sitemap = set(re.findall(r"<loc>(.*?)</loc>", xml))
print("docs", len(items), flush=True)

YEAR = re.compile(r"\b(20[12]\d)\b")


def strip(html):
    t = re.sub(r"(?s)<script.*?</script>|<style.*?</style>", " ", html)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)).strip()


def audit(it):
    page, html_u, md_u = it["page"], it["html"], it["markdown"]
    row = {"page": page, "html_url": html_u, "in_sitemap_html": html_u in sitemap, "in_sitemap_page": page in sitemap}
    try:
        t = time.time()
        r = S.get(html_u, timeout=60)
        row["html_status"], row["html_ms"] = r.status_code, int((time.time() - t) * 1000)
        row["content_type"] = r.headers.get("content-type", "")
        h = r.text
        canon = re.findall(r'rel="canonical" href="([^"]+)"', h)
        row["canonical"] = canon[0] if canon else ""
        row["canonical_count"] = len(canon)
        row["canonical_matches_page"] = bool(canon) and canon[0] == page
        row["robots"] = (re.findall(r'name="robots" content="([^"]+)"', h) or [""])[0]
        row["title"] = (re.findall(r"<title>(.*?)</title>", h) or [""])[0]
        h1 = re.findall(r"(?s)<h1[^>]*>(.*?)</h1>", h)
        row["h1"] = re.sub(r"<[^>]+>", "", h1[0]).strip() if h1 else ""
        row["h1_count"] = len(h1)
        body = strip(re.findall(r"(?s)<main>(.*?)</main>", h)[0]) if "<main>" in h else strip(h)
        row["words"] = len(body.split())
        years = [int(y) for y in YEAR.findall(body)]
        row["years"] = ",".join(sorted({str(y) for y in years}))
        row["newest_year"] = max(years) if years else ""
        row["oldest_year"] = min(years) if years else ""
        row["has_source_wits"] = "WITS" in body or "TRAINS" in body
        row["has_source_oec"] = "OEC" in body or "Comtrade" in body or "BACI" in body
        row["has_source_dgft"] = "DGFT" in body or "RoDTEP" in body
        row["mentions_verify"] = bool(re.search(r"verif|confirm", body, re.I))
        row["has_percent"] = bool(re.search(r"\d+(\.\d+)?%", body))
        row["has_usd"] = bool(re.search(r"\$\d", body))
        row["has_hs"] = bool(re.search(r"HS \d{6}", body))
        row["placeholder_flags"] = ";".join(w for w in ("undefined", "NaN", "None", "null", "[object", "TODO", "lorem") if w in body)
        row["links_to_page"] = page in h
        row["links_to_md"] = md_u in h
        # near-duplicate fingerprint: body with product/country-specific tokens removed
        m = re.match(r"https://vametra\.com/export/([a-z-]+)/to/([a-z-]+)", page)
        gen = body
        if m:
            for tok in (row["h1"].split(" to ")[-1], m.group(1), m.group(2)):
                gen = gen.replace(tok, " ")
        gen = re.sub(r"[\d$.,%#]+", "#", gen)
        gen = re.sub(r"\b[A-Z][a-z]+\b", "X", gen)
        row["template_fp"] = hashlib.md5(gen.encode()).hexdigest()[:10]
        row["exact_fp"] = hashlib.md5(body.encode()).hexdigest()[:10]
        # markdown twin
        t = time.time()
        md = S.get(md_u, timeout=60)
        row["md_status"], row["md_ms"] = md.status_code, int((time.time() - t) * 1000)
        row["md_words"] = len(md.text.split())
        row["md_h1_matches"] = md.text.splitlines()[0].lstrip("# ").strip()[:60] == row["h1"][:60] if md.text else False
    except Exception as e:
        row["error"] = f"{type(e).__name__}: {e}"[:120]
    return row


with ThreadPoolExecutor(max_workers=6) as ex:
    rows = list(ex.map(audit, items))

fields = ["page", "html_url", "html_status", "html_ms", "content_type", "canonical_matches_page", "canonical_count",
          "robots", "in_sitemap_html", "in_sitemap_page", "title", "h1", "h1_count", "words", "md_status", "md_words",
          "md_h1_matches", "years", "oldest_year", "newest_year", "has_source_wits", "has_source_oec", "has_source_dgft",
          "has_percent", "has_usd", "has_hs", "mentions_verify", "placeholder_flags", "links_to_page", "links_to_md",
          "template_fp", "exact_fp", "error"]
with open(OUT + "answers_per_doc.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)

ok = [r for r in rows if r.get("html_status") == 200]
summary = {
    "total": len(rows), "html_200": len(ok), "md_200": sum(r.get("md_status") == 200 for r in rows),
    "errors": sum("error" in r for r in rows),
    "canonical_matches_page": sum(r.get("canonical_matches_page") for r in ok),
    "single_canonical": sum(r.get("canonical_count") == 1 for r in ok),
    "robots_index": sum("index" in r.get("robots", "") and "noindex" not in r.get("robots", "") for r in ok),
    "single_h1": sum(r.get("h1_count") == 1 for r in ok),
    "in_sitemap_html": sum(r["in_sitemap_html"] for r in rows), "in_sitemap_page": sum(r["in_sitemap_page"] for r in rows),
    "words_min": min(r["words"] for r in ok), "words_median": sorted(r["words"] for r in ok)[len(ok) // 2],
    "words_max": max(r["words"] for r in ok), "under_300_words": sum(r["words"] < 300 for r in ok),
    "exact_duplicates": sum(c - 1 for c in collections.Counter(r["exact_fp"] for r in ok).values() if c > 1),
    "template_groups": len(set(r["template_fp"] for r in ok)),
    "largest_template_group": max(collections.Counter(r["template_fp"] for r in ok).values()),
    "has_wits_or_trains": sum(r["has_source_wits"] for r in ok), "has_oec": sum(r["has_source_oec"] for r in ok),
    "has_dgft_rodtep": sum(r["has_source_dgft"] for r in ok), "has_percent": sum(r["has_percent"] for r in ok),
    "has_usd": sum(r["has_usd"] for r in ok), "has_hs": sum(r["has_hs"] for r in ok),
    "mentions_verify": sum(r["mentions_verify"] for r in ok),
    "placeholder_flagged": sum(bool(r["placeholder_flags"]) for r in ok),
    "links_to_page": sum(r["links_to_page"] for r in ok), "md_h1_matches": sum(r.get("md_h1_matches") for r in ok),
    "newest_year_dist": dict(collections.Counter(str(r["newest_year"]) for r in ok)),
    "oldest_year_dist": dict(collections.Counter(str(r["oldest_year"]) for r in ok)),
    "html_ms_median": sorted(r["html_ms"] for r in ok)[len(ok) // 2], "html_ms_max": max(r["html_ms"] for r in ok),
    "kinds": dict(collections.Counter(
        "export-guide" if "/to/" in r["page"] else "product-hub" if r["page"].startswith("https://vametra.com/export/")
        else "region-hub" if "/regions/" in r["page"] else "tool" for r in rows)),
}
json.dump(summary, open(OUT + "answers_summary.json", "w"), indent=1)
print(json.dumps(summary, indent=1))
print("DONE", flush=True)
