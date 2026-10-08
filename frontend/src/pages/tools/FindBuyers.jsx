import React, { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ToolShell, Card } from "@/components/ToolShell";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { api } from "@/lib/api";
import { HsCodePicker } from "@/components/HsCodePicker";
import { ResponsiveSelect } from "@/components/ui/responsive-select";
import { BrainNextSteps } from "@/components/BrainNextSteps";
import { fetchLaneCountries } from "@/components/LaneCountrySelect";
import { Users, Lock, ArrowRight, ShieldCheck, CircleNotch, Bell } from "@phosphor-icons/react";

const inputCls = "w-full glass rounded-xl px-4 py-3 outline-none";
const TRUST = {
  emerald: "bg-emerald-500/15 text-emerald-300", cyan: "bg-cyan-500/15 text-cyan-300",
  amber: "bg-amber-500/15 text-amber-300", slate: "bg-slate-500/15 text-slate-300", violet: "bg-violet-500/15 text-violet-300",
};

export default function FindBuyers() {
  const [p] = useSearchParams();
  const [meta, setMeta] = useState(null);
  const [lane, setLane] = useState([]);
  const [hs, setHs] = useState(p.get("hs") || "100630");
  const [hsRow, setHsRow] = useState(null);
  const [country, setCountry] = useState(p.get("country") || "");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.get("/buyers/meta").then((r) => setMeta(r.data)).catch(() => {});
    fetchLaneCountries().then(setLane);
  }, []);

  useEffect(() => {
    if (!hs) return;
    let dead = false;
    setLoading(true);
    api.get("/buyers/search", { params: { hs, country: country || undefined, limit: 6 } })
      .then((r) => { if (!dead) setData(r.data); })
      .catch(() => { if (!dead) setData(null); })
      .finally(() => { if (!dead) setLoading(false); });
    return () => { dead = true; };
  }, [hs, country]);

  const covered = meta?.countries || [];
  const uncoveredPick = country && !covered.includes(country);
  const destCode = lane.find((c) => c.name === country)?.code || "";

  return (
    <>
      <SEO title="Buyer Discovery · Verified Importers by HS Code & Country"
        description="Search 27,000+ verified importer records by HS code and market. See trust scores, sectors and HS families for free; unlock contacts, evidence and watchlists in Buyer Intelligence."
        path="/tools/find-buyers"
        keywords="find buyers for export, verified importers by HS code, buyer database Europe, importers Germany India, export leads, B2B buyer discovery"
      />
      <ToolShell testIdPrefix="fb" label="Buyer Discovery"
        title="Who imports your product — by HS code, by country."
        sub="Pick an HS code and a market. You see real importer records with trust scores from the Vametra Buyer Intelligence Engine — the same records inside the full /buyers workspace. Markets without coverage show honest demand data, never invented buyers.">
        <div className="grid lg:grid-cols-12 gap-8">
          <div className="lg:col-span-4 min-w-0 glass-strong rounded-3xl p-6 sm:p-7 space-y-4">
            <Field label="Product / HS code (5,606 codes)">
              <HsCodePicker label="" testId="fb-hs-picker" value={hs} onChange={(code, row) => { setHs(code); setHsRow(row || null); }} />
            </Field>
            <Field label={`Market (${covered.length} with verified buyer coverage)`}>
              <ResponsiveSelect data-testid="fb-country" className={inputCls} value={country} onChange={(e) => setCountry(e.target.value)}>
                <option value="">All covered markets</option>
                {covered.map((c) => <option key={c} value={c}>{c}</option>)}
              </ResponsiveSelect>
            </Field>
            {meta && <p className="text-[11px] text-slate-500 leading-relaxed" data-testid="fb-disclaimer">{meta.disclaimer}</p>}
            <Link to={`/buyers?hs=${hs}${country ? `&country=${encodeURIComponent(country)}` : ""}`} data-testid="fb-open-buyers" className="btn-primary w-full justify-center">
              Open full Buyer Intelligence <ArrowRight size={14} weight="bold" />
            </Link>
          </div>

          <div className="lg:col-span-8 min-w-0 space-y-4">
            {loading && <div className="glass rounded-3xl p-8 text-center text-slate-400"><CircleNotch size={18} className="animate-spin inline mr-2" /> Searching verified importer records…</div>}
            {!loading && data && (
              <>
                <div data-testid="fb-result" className="glass-strong rounded-3xl p-6 sm:p-7">
                  <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300 flex items-center gap-2">
                    <Users size={14} weight="duotone" /> {data.total.toLocaleString()} verified importer{data.total === 1 ? "" : "s"} · HS {hs}{country ? ` · ${country}` : " · all covered markets"}
                  </div>
                  {hsRow?.description && <div className="mt-1 text-sm text-slate-400">{hsRow.description}</div>}
                </div>
                {data.total === 0 && (
                  <div className="glass rounded-3xl p-6 border border-amber-400/20" data-testid="fb-empty">
                    <div className="flex items-center gap-2 font-display font-bold"><Bell size={18} weight="duotone" className="text-amber-300" /> No verified buyers yet for this HS code{country ? ` in ${country}` : ""}.</div>
                    <p className="text-sm text-slate-400 mt-2">Coverage is expanding market by market. Try the 4-digit HS family, another covered market, or check real import demand for this product below.</p>
                    <div className="flex flex-wrap gap-2 mt-3">
                      <Link to={`/tools/product-research?hs=${hs}`} className="btn-ghost text-sm" data-testid="fb-empty-demand">See who imports HS {hs} (real data)</Link>
                      <Link to="/buyers" className="btn-ghost text-sm">Browse all covered markets</Link>
                    </div>
                  </div>
                )}
                <div className="grid sm:grid-cols-2 gap-4">
                  {data.buyers.map((b, i) => (
                    <Link key={b.geid} to={`/buyers/${b.geid}`} data-testid={`fb-card-${i}`} className="glass rounded-3xl p-5 hover:border-cyan-400/30 transition-colors block">
                      <div className="flex items-start justify-between gap-2">
                        <div className="font-display font-bold leading-tight">{b.display_name || b.legal_name}</div>
                        <div className={`shrink-0 text-[10px] px-2 py-1 rounded-full font-mono-display tracking-widest uppercase flex items-center gap-1 ${TRUST[b.trust?.color] || TRUST.slate}`}>
                          <ShieldCheck size={11} weight="fill" /> {b.trust?.band} {b.trust?.score}
                        </div>
                      </div>
                      <div className="text-xs text-slate-400 mt-1">{b.city ? `${b.city} · ` : ""}{b.country_name} · {b.sector}</div>
                      <div className="mt-3 flex flex-wrap gap-1.5">{(b.hs_families || []).slice(0, 5).map((h) => <span key={h} className="text-[10px] font-mono-display px-2 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-400/20 text-cyan-200">HS {h}</span>)}</div>
                      <div className="mt-3 text-xs text-slate-400 flex items-center gap-1">{b.has_contact ? <><Lock size={12} /> Contact available with plan</> : `${b.evidence_count} evidence record${b.evidence_count === 1 ? "" : "s"}`}</div>
                    </Link>
                  ))}
                </div>
                {data.total > data.buyers.length && (
                  <div className="glass-strong rounded-3xl p-6 flex items-center gap-4 border border-cyan-400/20 flex-wrap" data-testid="fb-locked">
                    <Lock size={26} className="text-cyan-300" weight="duotone" />
                    <div className="flex-1 min-w-[200px]">
                      <div className="font-display font-bold">{(data.total - data.buyers.length).toLocaleString()} more verified importers for this search.</div>
                      <div className="text-sm text-slate-400">Full profiles, evidence trail, contact unlock and watchlists are inside Buyer Intelligence.</div>
                    </div>
                    <Link to={`/buyers?hs=${hs}${country ? `&country=${encodeURIComponent(country)}` : ""}`} className="btn-primary" data-testid="fb-locked-cta">See all {data.total.toLocaleString()} <ArrowRight size={14} weight="bold" /></Link>
                  </div>
                )}
                <BrainNextSteps tool="buyers" testIdPrefix="fb-next"
                  inputs={{ hs, destination: destCode, product: hsRow?.description || "" }}
                  result={{ hsCode: hs, total: data.total, country: country || "all covered markets", topSectors: [...new Set(data.buyers.map((b) => b.sector))].slice(0, 3), trustBands: [...new Set(data.buyers.map((b) => b.trust?.band))].filter(Boolean) }} />
              </>
            )}
            {uncoveredPick && <Card title="Coverage note"><p className="text-sm text-slate-400 mt-2">This market is not yet in the verified buyer dataset.</p></Card>}
          </div>
        </div>
      </ToolShell>
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-12 pb-12"><DownloadCTA /></section>
    </>
  );
}
function Field({ label, children }) {
  return <label className="block"><div className="text-[10px] font-mono-display tracking-[0.25em] uppercase text-slate-400 mb-2">{label}</div>{children}</label>;
}
