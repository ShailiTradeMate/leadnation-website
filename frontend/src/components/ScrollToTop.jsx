import { useEffect, useLayoutEffect } from "react";
import { useLocation, useNavigationType } from "react-router-dom";

// P0 GLOBAL SCROLL FIX
// Every internal navigation opens from the top of the page (header),
// never from the previous scroll position. Handles navbar, cards, CTAs,
// footer links, search results, and browser Back/Forward — mobile + desktop.
// Anchor links (e.g. /#download) still scroll to their target element.
export default function ScrollToTop() {
  const { pathname, hash } = useLocation();
  const navType = useNavigationType(); // PUSH | REPLACE | POP

  // Take manual control of the browser's default scroll restoration so that
  // Back/Forward (POP) also lands at the top instead of the remembered spot.
  useEffect(() => {
    if ("scrollRestoration" in window.history) {
      window.history.scrollRestoration = "manual";
    }
  }, []);

  useLayoutEffect(() => {
    if (hash) {
      const el = document.getElementById(hash.slice(1));
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "start" });
        return;
      }
    }
    // Instant top for route changes (incl. POP) — no janky animation on nav.
    window.scrollTo({ top: 0, left: 0, behavior: "instant" in document.documentElement.style ? "instant" : "auto" });
  }, [pathname, hash, navType]);

  return null;
}
