// Slug → display title. Used to emit a correct <title>/canonical on first render,
// before async page data arrives — the crawler renderer can snapshot that early.
const LOWER = new Set(["to", "and", "of", "the", "for", "in"]);
const UPPER = new Set(["usa", "uae", "uk", "eu", "us", "hs", "hsn", "gst", "fta", "ftas", "vat", "ksa", "drc", "cis"]);

export const titleize = (slug) =>
  String(slug || "")
    .split("-")
    .filter(Boolean)
    .map((w) => {
      const l = w.toLowerCase();
      if (LOWER.has(l)) return l;
      if (UPPER.has(l)) return l.toUpperCase();
      return w.charAt(0).toUpperCase() + w.slice(1);
    })
    .join(" ");
