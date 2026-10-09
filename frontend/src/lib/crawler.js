/**
 * Crawler detection for render-budget control.
 *
 * Search engines and the edge pre-render worker run a headless browser and give up
 * once the page has not gone idle for too long. Third-party analytics keep the
 * network busy, so heavy data pages never settle and the crawler receives the empty
 * SPA shell instead of the content. For crawlers we therefore skip non-content
 * extras. The content itself is identical for everyone.
 */
const SEARCH_BOT_UA = /(googlebot|google-inspectiontool|storebot-google|google-read-aloud|bingbot|adidxbot|duckduckbot|slurp|baiduspider|yandex(bot|images)|applebot|petalbot|sogou|exabot|facebookexternalhit|facebot|twitterbot|linkedinbot|pinterest|slackbot|telegrambot|discordbot|redditbot|ia_archiver|semrushbot|ahrefsbot|mj12bot|dotbot|bytespider|gptbot|oai-searchbot|chatgpt-user|perplexitybot|claudebot|anthropic-ai|google-extended|ccbot|amazonbot|meta-externalagent|prerender)/i;

// Headless renderers (the pre-render worker, Lighthouse) — script-free, but they still
// get the full UI so automated UI testing keeps working.
const HEADLESS_UA = /(headlesschrome|phantomjs|lighthouse|chrome-lighthouse)/i;

const ua = () => (typeof navigator === "undefined" ? "" : navigator.userAgent || "");

/** Strict search/AI crawler — safe to drop floating widgets for. */
export function isSearchBot() {
  return SEARCH_BOT_UA.test(ua());
}

/** Crawler or headless render — never load third-party analytics scripts. */
export function isCrawler() {
  const u = ua();
  return SEARCH_BOT_UA.test(u) || HEADLESS_UA.test(u);
}

export default isCrawler;
