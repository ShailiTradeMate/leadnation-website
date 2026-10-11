import { api } from "@/lib/api";

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/**
 * Resolves { ok, data } | { notFound: true } | { stalled: true }.
 *
 * A transient failure (network drop, timeout, 5xx during a deploy) must never be
 * reported as "not found": those branches render a noindex soft-404, and the
 * crawler cache can hold that snapshot for weeks against a perfectly good URL.
 * Only a real 404/410 from the API counts as not published.
 */
export async function fetchPageData(path, { attempts = 4, timeout = 120000 } = {}) {
  for (let i = 0; i < attempts; i++) {
    try {
      const { data } = await api.get(path, { timeout });
      return { ok: true, data };
    } catch (e) {
      const status = e?.response?.status ?? null;
      if (status === 404 || status === 410) return { notFound: true };
      if (i < attempts - 1) await sleep(800 * (i + 1));
    }
  }
  return { stalled: true };
}
