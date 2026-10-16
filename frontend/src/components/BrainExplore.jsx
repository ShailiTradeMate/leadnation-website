import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Brain, ArrowRight } from "@phosphor-icons/react";
import { fetchLaneCountries } from "@/components/LaneCountrySelect";

export const KIND_META = {
  corridor: { label: "Trade corridor", fields: ["origin", "destination", "product"], blurb: "Any origin → any destination. Duty, FTA, documents, buyers." },
  country: { label: "Country profile", fields: ["destination", "product"], blurb: "Tariffs, imports and verified buyers for any market." },
  product: { label: "Product", fields: ["product", "hs", "origin", "destination"], blurb: "HS code, duty, demand and buyers for any product." },
  industry: { label: "Industry", fields: ["industry", "origin", "destination"], blurb: "Sector view — markets, duty and buyers." },
  region: { label: "Export region", fields: ["region", "product"], blurb: "Duty, demand and buyers across a region." },
  guide: { label: "Export guide", fields: ["product", "origin", "destination"], blurb: "A product × market guide we have not published yet." },
};
const FIELD = {
  origin: { label: "Exporting country", ph: "e.g. India" },
  destination: { label: "Importing country", ph: "e.g. Germany" },
  product: { label: "Product name", ph: "e.g. Basmati rice" },
  hs: { label: "HS code (optional)", ph: "e.g. 100630" },
  industry: { label: "Industry / sector", ph: "e.g. Pharmaceuticals" },
  region: { label: "Region", ph: "Europe · Middle East · Asia-Pacific · Americas · Africa" },
};

export function exploreUrl(kind, v) {
  const q = new URLSearchParams({ kind, ...Object.fromEntries(Object.entries(v).filter(([, x]) => x)) });
  return `/brain/explore?${q.toString()}`;
}

/** Form used on the index/detail pages and at the top of /brain/explore. */
export function BrainExploreForm({ kind, defaults = {}, onSubmit, testIdPrefix = "explore", compact = false }) {
  const [v, setV] = useState({ origin: kind === "corridor" || kind === "guide" ? "India" : "", ...defaults });
  const [countries, setCountries] = useState([]);
  useEffect(() => { fetchLaneCountries().then(setCountries); }, []);
  useEffect(() => { setV((s) => ({ ...s, ...defaults })); }, [kind]); // eslint-disable-line react-hooks/exhaustive-deps
  const fields = KIND_META[kind]?.fields || [];
  const set = (k) => (e) => setV((s) => ({ ...s, [k]: e.target.value }));
  const submit = (e) => { e.preventDefault(); onSubmit(v); };
  return (
    <form onSubmit={submit} data-testid={`${testIdPrefix}-form`} className={`grid gap-3 ${compact ? "sm:grid-cols-2" : "sm:grid-cols-2 lg:grid-cols-4"}`}>
      <datalist id="explore-countries">{countries.map((c) => <option key={c.code} value={c.name} />)}</datalist>
      {fields.map((k) => (
        <label key={k} className="block">
          <span className="text-[11px] font-mono-display tracking-widest uppercase text-slate-400">{FIELD[k].label}</span>
          <input data-testid={`${testIdPrefix}-${k}`} value={v[k] || ""} onChange={set(k)} placeholder={FIELD[k].ph}
            list={k === "origin" || k === "destination" ? "explore-countries" : undefined}
            className="mt-1 w-full glass rounded-xl px-3 py-2.5 text-sm bg-transparent outline-none focus:border-cyan-400/50" />
        </label>
      ))}
      <div className="flex items-end">
        <button type="submit" data-testid={`${testIdPrefix}-submit`} className="btn-primary w-full justify-center">
          <Brain size={15} weight="duotone" /> Ask the Brain <ArrowRight size={13} weight="bold" />
        </button>
      </div>
    </form>
  );
}

/** "Can't find your corridor / market / product? Let the Vametra AI Brain build it" — dropped on every catalogue page. */
export function BrainExploreCTA({ kind = "corridor", defaults = {}, title, testIdPrefix = "explore-cta" }) {
  const nav = useNavigate();
  const meta = KIND_META[kind];
  return (
    <section className="max-w-7xl mx-auto px-6 sm:px-10 mt-12" data-testid={testIdPrefix}>
      <div className="glass-strong rounded-3xl p-6 sm:p-8 border border-cyan-400/15">
        <div className="flex items-center gap-2 text-[11px] font-mono-display tracking-[0.18em] uppercase text-cyan-300">
          <Brain size={14} weight="duotone" /> Vametra AI Brain · check any other {meta.label.toLowerCase()}
        </div>
        <h2 className="font-display font-bold text-base md:text-lg mt-3">
          {title || `Not seeing your ${meta.label.toLowerCase()}? The Brain will build it on demand.`}
        </h2>
        <p className="mt-2 text-sm text-slate-400 max-w-2xl">
          {meta.blurb} Live duty from World Bank WITS, measured demand from OEC, verified buyer counts and
          AI-written process guidance — presented like the pages on this site, generated when you ask.
        </p>
        <div className="mt-5">
          <BrainExploreForm kind={kind} defaults={defaults} testIdPrefix={testIdPrefix} onSubmit={(v) => nav(exploreUrl(kind, v))} />
        </div>
      </div>
    </section>
  );
}
