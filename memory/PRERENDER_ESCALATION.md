# Prerender escalation — export guide SPA shell issue

Status: **RESOLVED IN CODE 10 Oct 2026 — it was ours, not the platform.** Awaiting prod deploy.

## Actual root cause
`GET /api/seo/page-data/{product}/{country}` had no response cache and built its sections
sequentially. `_duty_section` (WITS tariff) costs ~14.6s cold vs 0.9s warm, and `duty_cache` is
both 7-day TTL and CLEARED by the weekly refresh job. So any product x country nobody had touched
recently took 9-15s, which is longer than the edge pre-render worker waits — it gave up and served
the bare SPA shell. Products that happened to be warm (basmati-rice 0.35s) rendered fine. That is
why the failures were product-shaped (pharmaceuticals 0/6, basmati-rice 6/6) rather than random.

Fix: 24h `db.seo_page_cache` + concurrent sections + `POST /api/seo/warm-pages` + boot/daily warm
job + a `Semaphore(4)` gate on outbound WITS calls. See CHANGELOG 2026-10-10.

## Lesson — do not repeat
- Profile the API **per product** before blaming the platform. A whole-site average hid a 40x
  spread between warm and cold products.
- A fast page-data reading for ONE product proves nothing about the others.
- Any background warmer must be bounded, or it starves the event loop and times out live traffic
  (27/29 tests failed at 30s until the WITS gate was added).
- Do not resubmit sitemaps as a remedy. GSC showed Success / 975 discovered throughout; discovery
  was never the problem.

## Original symptom (for reference)
Googlebot UA on `/export/<product>/to/<country>`: 335 audited, all HTTP 200, 69 rendered,
266 returned a ~205-word shell with no h1 and no canonical in ~300ms (cache hit, no render).
Hubs were always fine (15/15). Answer docs were always fine (413/413).

## Deployer agent verdict (run b5226749-5cd0-4528-bb88-f0c3d816607d) — SUPERSEDED
Attributed it to the managed Cloudflare pre-render worker (render cache, per-app quota,
route-depth rules) because the deployer surface has no Cloudflare visibility. It did correctly
surface the real `matrix()` Query-object bug. No platform ticket is needed unless the post-deploy
re-audit still shows shells on warm, sub-second URLs.

## Audit scripts
- `/app/memory/sample_audit.py` — fast random-sample Googlebot-UA audit (`python3 sample_audit.py 30`)
- `/app/memory/reaudit.py` — full Googlebot-UA audit over every guide URL
- `/app/memory/warmtest.py` — cold/warm cache behaviour probe
