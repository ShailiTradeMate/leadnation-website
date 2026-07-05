import { api } from "@/lib/api";

const GA4_ID = process.env.REACT_APP_GA4_ID;
const GTM_ID = process.env.REACT_APP_GTM_ID;
const CLARITY_ID = process.env.REACT_APP_CLARITY_ID;
const META_PIXEL_ID = process.env.REACT_APP_META_PIXEL_ID;

let loaded = false;

function injectScript(src, attrs = {}) {
  const s = document.createElement("script");
  s.async = true;
  s.src = src;
  Object.entries(attrs).forEach(([k, v]) => s.setAttribute(k, v));
  document.head.appendChild(s);
  return s;
}

export function initAnalytics() {
  if (loaded || typeof window === "undefined") return;
  loaded = true;

  // Google Tag Manager
  if (GTM_ID) {
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push({ "gtm.start": Date.now(), event: "gtm.js" });
    injectScript(`https://www.googletagmanager.com/gtm.js?id=${GTM_ID}`);
  }

  // GA4
  if (GA4_ID) {
    injectScript(`https://www.googletagmanager.com/gtag/js?id=${GA4_ID}`);
    window.dataLayer = window.dataLayer || [];
    window.gtag = function gtag() { window.dataLayer.push(arguments); };
    window.gtag("js", new Date());
    window.gtag("config", GA4_ID, { send_page_view: true });
  }

  // Microsoft Clarity
  if (CLARITY_ID) {
    (function (c, l, a, r, i, t, y) {
      c[a] = c[a] || function () { (c[a].q = c[a].q || []).push(arguments); };
      t = l.createElement(r); t.async = 1; t.src = "https://www.clarity.ms/tag/" + i;
      y = l.getElementsByTagName(r)[0]; y.parentNode.insertBefore(t, y);
    })(window, document, "clarity", "script", CLARITY_ID);
  }

  // Meta Pixel
  if (META_PIXEL_ID) {
    /* eslint-disable */
    !function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?
      n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;
      n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;
      t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,
      document,'script','https://connect.facebook.net/en_US/fbevents.js');
    /* eslint-enable */
    window.fbq("init", META_PIXEL_ID);
    window.fbq("track", "PageView");
  }
}

export const EVENTS = {
  USER_REGISTERED: "user_registered",
  USER_LOGIN: "user_login",
  COMMAND_CENTER_OPENED: "command_center_opened",
  TRADE_PROJECT_CREATED: "trade_project_created",
  TRADE_PROJECT_UPDATED: "trade_project_updated",
  QUOTE_GENERATED: "quote_generated",
  SCENARIO_CREATED: "scenario_created",
  BRAIN_QUERY: "brain_query",
  PDF_REPORT_CREATED: "pdf_report_created",
  PDF_REPORT_DOWNLOADED: "pdf_report_downloaded",
  SUBSCRIPTION_STARTED: "subscription_started",
  PAYMENT_ATTEMPT: "payment_attempt",
  PAYMENT_SUCCESS: "payment_success",
  PAYMENT_FAILURE: "payment_failure",
};

// Map our events to Meta Pixel standard events (falls back to trackCustom).
const META_STANDARD = {
  user_registered: "CompleteRegistration",
  user_login: "Lead",
  trade_project_created: "Lead",
  command_center_opened: "ViewContent",
  subscription_started: "Subscribe",
  payment_success: "Purchase",
};

// Privacy: never send PII / confidential data to analytics. Only safe, non-identifying
// primitives are forwarded (see Cookie & Privacy Policy). Everything else is dropped.
const BLOCKED_KEYS = ["email", "phone", "mobile", "name", "customerid", "customer_id",
  "uid", "token", "password", "address", "buyer", "supplier", "notes", "document",
  "documents", "company", "product", "title"];

function scrub(meta = {}) {
  const out = {};
  for (const [k, v] of Object.entries(meta || {})) {
    const key = String(k).toLowerCase();
    if (BLOCKED_KEYS.some((b) => key.includes(b))) continue;
    if (v == null) continue;
    if (typeof v === "object") continue; // no nested/PII-bearing objects
    out[k] = v;
  }
  return out;
}

export function trackEvent(name, meta = {}) {
  const safe = scrub(meta);
  // GA4
  try { window.gtag && window.gtag("event", name, safe); } catch (_) {}
  // GTM dataLayer (central tag manager)
  try { window.dataLayer && window.dataLayer.push({ event: name, ...safe }); } catch (_) {}
  // Meta Pixel — use standard event when mapped, else custom
  try {
    if (window.fbq) {
      const std = META_STANDARD[name];
      if (std) window.fbq("track", std, safe); else window.fbq("trackCustom", name, safe);
    }
  } catch (_) {}
  // Clarity — tag the session with the event name
  try { window.clarity && window.clarity("event", name); } catch (_) {}
  // First-party (always works, regardless of keys) — powers the future admin dashboard
  try {
    api.post("/track", { name, path: typeof window !== "undefined" ? window.location.pathname : "", meta: safe });
  } catch (_) {}
}

export function trackPageView(path) {
  try { window.gtag && window.gtag("event", "page_view", { page_path: path }); } catch (_) {}
  try { window.fbq && window.fbq("track", "PageView"); } catch (_) {}
  try {
    api.post("/track", { name: "page_view", path });
  } catch (_) {}
}
