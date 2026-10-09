# Prerender escalation — export guide SPA shell issue

Status: OPEN. Blocked on Emergent platform (Cloudflare prerender worker). Not an app bug.

## Symptom (production, vametra.com)
Googlebot UA on `/export/<product>/to/<country>`:
- 335 guides audited -> HTTP 200 on all 335
- 69 rendered full content (h1 + ~870-1250 words)
- 266 returned ~205-307 word SPA shell, no h1, no canonical, in ~300ms

Hubs are unaffected: `/export`, 8 product hubs, `/regions` + 5 region hubs = 15/15 rendered.
Answer docs unaffected: 413/413 `/api/answers/html/*` return 200 text/html with single canonical.

## Proof it is not the app
- Real browser on `/export/agarbatti/to/belgium` reaches network idle in ~1.65s, renders h1 + 873 words.
- Deployed JS bundle contains the crawler-lean code (`frontend/src/lib/crawler.js`).
- Analytics (GTM/GA4/Clarity/Meta Pixel) and Brain/WhatsApp widgets are suppressed for crawler UA.
- Shell responses come back in ~300ms = cache hit, no render attempted.
- Cold requests, repeat requests, 30s spacing and an ~8min idle wait never converted a shell URL to rendered.
- Backend render fetcher (35.227.215.211) gets HTTP 200 from `/api/seo/page-data/*`.

## Deployer agent verdict (run b5226749-5cd0-4528-bb88-f0c3d816607d)
Decision lives inside Emergent's managed Cloudflare prerender worker: render cache,
per-app render budget/quota, route-depth rules, cache-purge-on-deploy, worker logs.
Deployer surface has no Cloudflare access. Must be answered by Emergent platform eng.

## Questions for Emergent support
Deployment `trade-brain-ai`, id `d75488b7-8c6f-4ff6-9317-11a4cc0d4e41`,
run `b5226749-5cd0-4528-bb88-f0c3d816607d`. Crawl optimisation toggle is ON.
1. Is there a per-app prerender render cap or distinct-URL cache quota? Current usage?
2. Worker render / timeout / quota-rejection logs for `/export/*/to/*`.
3. Any route allow/deny or max-path-depth rule for 4-segment paths? (69 of them DO render,
   so not a hard block.)
4. Did the last deploy purge the prerender cache, and how does a URL enter it?
5. Supported way to warm or prioritise ~400 URLs, or raise the cap.

## Do not repeat
- Do not mass-crawl the site while investigating; it may consume the render budget that
  Googlebot needs.
- Do not tell the user guide rendering is fixed until a Googlebot-UA audit confirms it.
- Do not resubmit sitemaps as a remedy; the sitemap is dynamic and already healthy
  (975 `<loc>`, HTTP 200).

## Audit scripts
- `/app/memory/reaudit.py` — Googlebot-UA rendered/shell audit over guide URLs
- `/app/memory/warmtest.py` — cold/warm cache behaviour probe
