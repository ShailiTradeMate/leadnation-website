import { ResponsiveSelect } from '@/components/ui/responsive-select';
import { countryFilterOptions } from '@/data/geo';
import React, { useEffect, useState, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import SEO from "@/components/SEO";
import { AnswerFirst } from "@/components/AnswerFirst";
import { PageFaq } from "@/components/PageFaq";
import DownloadCTA from "@/components/DownloadCTA";
import BuyerCard from "@/components/BuyerCard";
import { fetchBuyerMeta, searchBuyers, fetchBuyerSources } from "@/lib/vbieApi";
import { SOURCE_CATEGORIES, USAGE_NOTE } from "@/lib/sourceCategories";
import BuyerDataNotice from "@/components/BuyerDataNotice";
import { MagnifyingGlass, ShieldCheck, Sparkle, Info } from "@phosphor-icons/react";
import { HsCodePicker } from "@/components/HsCodePicker";

const TRUST_MINS = [
  { label: "Any trust", value: 0 },
  { label: "Emerging+ (45)", value: 45 },
  { label: "Trusted+ (65)", value: 65 },
  { label: "Verified (80)", value: 80 },
];

const BUYERS_FAQ = [
  { q: "What is a verified importers list?", a: "A list of importing companies whose trade activity is evidenced in official records and whose contact details have been confirmed. Vametra AI adds sanctions screening and an explainable trust score to every record, so you can see why a buyer is rated the way it is." },
  { q: "How many verified buyers does Vametra AI hold?", a: "{buyerRecords} contact-verified buyer records across {buyerCountries} countries and {buyerSectors} sectors, counted live from the platform. Coverage is stated per market; where a market has no verified records yet, the page says so." },
  { q: "What does the trust score mean?", a: "It summarises the evidence behind a record — source quality, contact resolution, recency and sanctions status — into Verified, Trusted, Emerging or Unverified bands. Every band is explained on the buyer profile." },
  { q: "Is the verified importers list free?", a: "Searching by HS code, market and sector is free, including company names, sectors and trust bands. Contact details, evidence trails, watchlists and exports require an account and an active plan." },
  { q: "Do you sell or show raw datasets?", a: "No. Vametra AI shows verified intelligence, never raw source dumps or scraped lead lists, and a buyer without a working contact is never published." },
];

export default function BuyerIntelligence() {
  const [meta, setMeta] = useState(null);
  const [params] = useSearchParams();
  const [filters, setFilters] = useState({ q: "", country: params.get("country") || "", sector: "", corridor: "", trust_min: 0, hs: params.get("hs") || "" });
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchBuyerMeta().then(setMeta).catch(() => {}); }, []);

  const run = useCallback(() => {
    setLoading(true);
    const params = Object.fromEntries(Object.entries(filters).filter(([, v]) => v !== "" && v !== 0));
    searchBuyers({ ...params, limit: 24 }).then((r) => { setData(r); setLoading(false); }).catch(() => setLoading(false));
  }, [filters]);

  useEffect(() => { const t = setTimeout(run, 250); return () => clearTimeout(t); }, [run]);

  return (
    <>
      <BuyerDataNotice />
      <SEO
        title="Verified Importers List: 32 Countries, Evidence | Vametra AI"
        description="Verified importers list: contact-verified, sanctions-screened buyers across 32 countries and 21 sectors, each with an explainable trust score and cited evidence. Search free by HS code and market."
        path="/buyers"
        breadcrumbs={[{ name: "Home", path: "/" }, { name: "Verified Buyers", path: "/buyers" }]}
        faqs={BUYERS_FAQ}
        keywords="verified buyers, global importers database, buyer intelligence, trade leads with evidence, export buyer discovery"
      />

      {/* Hero */}
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-28 pb-8">
        <div className="text-xs font-mono-display tracking-[0.35em] uppercase text-cyan-300 flex items-center gap-2">
          <Sparkle size={14} weight="fill" /> Verified Buyer Intelligence Engine
        </div>
        <h1 className="mt-3 font-display font-black text-4xl sm:text-5xl lg:text-6xl leading-[1.05]">
          Verified importers list <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 to-violet-400">with evidence</span>, not scraped leads.
        </h1>
        <p className="mt-4 text-base text-slate-400 max-w-2xl">
          Active importers and public-sector buyers, ingested daily from official government
          sources — every record sanctions-screened with an explainable trust score and cited evidence.
          Not a scraped list — a verifiable intelligence graph.
        </p>
        {meta && (
          <div className="mt-6 flex flex-wrap gap-3 text-sm">
            <Stat label="Buyers indexed" value={meta.total} />
            <Stat label="Markets" value={meta.countries?.length || 0} />
            <Stat label="Sectors" value={meta.sectors?.length || 0} />
          </div>
        )}
      </section>

      <section className="max-w-7xl mx-auto px-6 sm:px-10 pb-16 grid lg:grid-cols-12 gap-8">
        {/* Filters */}
        <aside className="lg:col-span-3 space-y-4">
          <div className="glass-strong rounded-3xl p-6 space-y-4 lg:sticky lg:top-24">
            <div className="relative">
              <MagnifyingGlass size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                data-testid="buyer-search-input"
                value={filters.q}
                onChange={(e) => setFilters({ ...filters, q: e.target.value })}
                placeholder="Search company, product…"
                className="w-full glass rounded-xl pl-9 pr-4 py-3 outline-none text-sm"
              />
            </div>
            <Select testid="buyer-filter-country" label="Market" value={filters.country}
              onChange={(v) => setFilters({ ...filters, country: v })}
              options={[{ label: "All markets", value: "" }, ...countryFilterOptions(meta?.countries)]} />
            <Select testid="buyer-filter-sector" label="Sector" value={filters.sector}
              onChange={(v) => setFilters({ ...filters, sector: v })}
              options={[{ label: "All sectors", value: "" }, ...(meta?.sectors || []).map((c) => ({ label: c, value: c }))]} />
            <Select testid="buyer-filter-corridor" label="Trade corridor" value={filters.corridor}
              onChange={(v) => setFilters({ ...filters, corridor: v })}
              options={[{ label: "All corridors", value: "" }, ...(meta?.corridors || []).map((c) => ({ label: c, value: c }))]} />
            <HsCodePicker
              label="HS code"
              testId="buyer-filter-hs"
              placeholder="Any HS code"
              value={filters.hs || ""}
              onChange={(code) => setFilters({ ...filters, hs: code })}
            />
            <Select testid="buyer-filter-trust" label="Minimum trust" value={filters.trust_min}
              onChange={(v) => setFilters({ ...filters, trust_min: Number(v) })}
              options={TRUST_MINS} />
          </div>
        </aside>

        {/* Results */}
        <div className="lg:col-span-9 space-y-5">
          <div className="flex items-center justify-between">
            <div data-testid="buyer-result-count" className="text-sm text-slate-400">
              {loading ? "Searching…" : `${data?.total ?? 0} verified buyers`}
            </div>
            <div className="text-xs text-slate-500 flex items-center gap-1.5">
              <ShieldCheck size={13} weight="fill" className="text-cyan-300" /> Sorted by trust score
            </div>
          </div>

          {meta?.disclaimer && (
            <div className="glass rounded-2xl p-4 flex items-start gap-3 border border-cyan-400/15">
              <Info size={18} className="text-cyan-300 shrink-0 mt-0.5" weight="duotone" />
              <p className="text-xs text-slate-400 leading-relaxed">{meta.disclaimer}</p>
            </div>
          )}

          <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-4">
            {(data?.buyers || []).map((b, i) => <BuyerCard key={b.geid} buyer={b} index={i} />)}
          </div>

          {!loading && data?.buyers?.length === 0 && (
            <div data-testid="buyer-empty" className="glass rounded-3xl p-10 text-center text-slate-400">
              No buyers match these filters yet. Try widening your search.
            </div>
          )}
        </div>
      </section>

      <SourcesSection />

      <AnswerFirst testId="buyers-answer"
        answer="A verified importers list is only useful if every record can be traced to evidence. Vametra AI ingests buyers from official, licence-cleared government sources, resolves a working contact, screens each company against sanctions lists and assigns an explainable trust score — {buyerRecords} records across {buyerCountries} countries and {buyerSectors} sectors. Search is free; contacts and evidence need a plan."
        rows={[
          { label: "Contact-verified buyer records", value: "{buyerRecords}" },
          { label: "Countries covered", value: "{buyerCountries}" },
          { label: "Sectors", value: "{buyerSectors}" },
          { label: "Trust bands", value: "Verified · Trusted · Emerging · Unverified" },
        ]}
        source="Official trade registries; Vametra AI Buyer Intelligence verification"
        links={[
          { to: "/tools/find-buyers", label: "Search buyers by HS code" },
          { to: "/tools/duty-calculator", label: "Custom duty calculator" },
          { to: "/export", label: "Export guides by market" },
          { to: "/corridors/india-to-uae", label: "India → UAE corridor" },
          { to: "/services/buyer-discovery-service", label: "Done-for-you buyer discovery" },
        ]} />
      <PageFaq items={BUYERS_FAQ} heading="Verified importers — frequently asked questions" testIdPrefix="buyers-faq" />
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pb-16"><DownloadCTA /></section>
    </>
  );
}

function SourcesSection() {
  const [src, setSrc] = useState(null);
  useEffect(() => { fetchBuyerSources().then(setSrc).catch(() => {}); }, []);
  return (
    <section data-testid="buyer-sources-section" className="max-w-7xl mx-auto px-6 sm:px-10 pb-16">
      <div className="glass-strong rounded-3xl p-7 sm:p-9">
        <div className="flex items-center gap-2 text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300">
          <ShieldCheck size={14} weight="fill" /> Source Transparency
        </div>
        <h2 className="font-display font-extrabold text-2xl sm:text-3xl mt-3">How Vametra builds Buyer Intelligence</h2>
        <p className="mt-2 text-sm text-slate-400 max-w-3xl">
          Vametra AI combines information from government records, international trade data, public
          procurement records, business registries, industry sources and company-published information.
          We aggregate, process and screen these signals to help you discover relevant buyers directly
          on Vametra.
        </p>
        <div className="mt-5 grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {SOURCE_CATEGORIES.map((s, i) => (
            <div key={i} data-testid={`buyer-source-category-${i}`} className="glass rounded-2xl px-4 py-3">
              <div className="text-sm font-semibold">{s.name}</div>
            </div>
          ))}
        </div>
        <div className="mt-5 flex flex-wrap gap-4 text-xs text-slate-400">
          {src?.sanctions_screening?.denied_parties != null && (
            <span className="flex items-center gap-1.5"><ShieldCheck size={13} weight="fill" className="text-emerald-300" />
              Sanctions-screened against {src.sanctions_screening.denied_parties.toLocaleString()} denied parties ({src.sanctions_screening.provider})</span>
          )}
          {src?.last_ingestion?.finished_at && (
            <span>Last updated: {new Date(src.last_ingestion.finished_at).toLocaleDateString()}</span>
          )}
        </div>
        <p className="mt-4 text-[11px] text-amber-200/70 leading-relaxed max-w-3xl">
          Note: Vametra AI has no contact arrangement with these organisations. Always verify buyer details
          directly and treat any business you conduct with them as at your own risk.
        </p>
        <p data-testid="buyer-usage-note-section" className="mt-2 text-[11px] text-amber-200/70 leading-relaxed max-w-3xl">
          Note: {USAGE_NOTE}
        </p>
      </div>
    </section>
  );
}

function Stat({ label, value }) {
  return (
    <div className="glass rounded-2xl px-4 py-2">
      <span className="font-display font-black text-lg">{value}</span>
      <span className="text-slate-400 ml-2 text-xs uppercase tracking-widest">{label}</span>
    </div>
  );
}

function Select({ label, value, onChange, options, testid }) {
  return (
    <label className="block">
      <div className="text-[10px] font-mono-display tracking-[0.25em] uppercase text-slate-400 mb-2">{label}</div>
      <ResponsiveSelect data-testid={testid} value={value} onChange={(e) => onChange(e.target.value)}
        className="w-full glass rounded-xl px-3 py-2.5 outline-none text-sm">
        {options.map((o) => <option key={String(o.value)} value={o.value} className="bg-[#0a0f24]">{o.label}</option>)}
      </ResponsiveSelect>
    </label>
  );
}
