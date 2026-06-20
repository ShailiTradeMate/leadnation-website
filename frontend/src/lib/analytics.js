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

export function trackEvent(name, meta = {}) {
  // GA4
  try { window.gtag && window.gtag("event", name, meta); } catch (_) {}
  // GTM dataLayer
  try { window.dataLayer && window.dataLayer.push({ event: name, ...meta }); } catch (_) {}
  // Meta Pixel
  try { window.fbq && window.fbq("trackCustom", name, meta); } catch (_) {}
  // Clarity
  try { window.clarity && window.clarity("event", name); } catch (_) {}
  // First-party (always works, regardless of keys)
  try {
    api.post("/track", { name, path: typeof window !== "undefined" ? window.location.pathname : "", meta });
  } catch (_) {}
}

export function trackPageView(path) {
  try { window.gtag && window.gtag("event", "page_view", { page_path: path }); } catch (_) {}
  try { window.fbq && window.fbq("track", "PageView"); } catch (_) {}
  try {
    api.post("/track", { name: "page_view", path });
  } catch (_) {}
}
