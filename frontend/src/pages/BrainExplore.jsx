import React, { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Brain, ArrowRight, Compass, FileText, ShieldCheck, ChartLineUp, CalendarBlank, Newspaper, Warning } from "@phosphor-icons/react";
import SEO from "@/components/SEO";
import { SectionLabel } from "@/components/PageHero";
import { Card, ChipList } from "@/components/ToolShell";
import { PageFaq } from "@/components/PageFaq";
import { BrainExploreForm, KIND_META, exploreUrl, saveExploreMemory } from "@/components/BrainExplore";
import { BrainThinking } from "@/components/BrainThinking";
import { api } from "@/lib/api";

const money = (v) => (v == null ? "—" : v >= 1e9 ? `$${(v / 1e9).toFixed(1)}B` : v >= 1e6 ? `$${(v / 1e6).toFixed(0)}M` : `$${(v / 1e3).toFixed(0)}K`);
const KV = ({ label, value, accent, testId }) => (
  <div className="glass rounded-2xl p-4" data-testid={testId}>
    <div className="text-[10px] font-mono-display tracking-widest uppercase text-slate-400">{label}</div>
    <div className={`mt-1 font-display font-bold text-lg ${accent ? "text-cyan-300" : ""}`}>{value ?? "—"}</div>
  </div>
);

export default function BrainExplore() {
  const [sp] = useSearchParams();
  const nav = useNavigate();
  const kind = KIND_META[sp.get("kind")] ? sp.get("kind") : "corridor";
  const params = Object.fromEntries(["origin", "destination", "product", "hs", "industry", "region"].map((k) => [k, sp.get(k) || ""]));
  const hasQuery = Object.values(params).some(Boolean);
  const [state, setState] = useState("idle");
  const [r, setR] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    if (hasQuery) saveExploreMemory(params);
    if (!hasQuery) { setState("idle"); setR(null); return; }
    let live = true;
    setState("loading"); setErr("");
    api.post("/brain/explore", { kind, ...params }, { timeout: 120000 })
      .then((res) => { if (live) { setR(res.data); setState("done"); } })
      .catch((e) => { if (live) { setErr(e?.response?.data?.detail || "The Brain could not build this report. Check the fields and try again."); setState("error"); } });
    return () => { live = false; };
  }, [sp.toString()]); // eslint-disable-line react-hooks/exhaustive-deps

  const n = r?.narrative || {};
  const duty = r?.duty, demand = r?.demand, buyers = r?.buyers;
  return (
    <div className="relative">
      <SEO title={r ? `${r.title} · Vametra AI Brain` : "Explore any corridor, market or product · Vametra AI Brain"}
        description="On-demand trade intelligence for any lane: live duty, demand, verified buyers and AI-written guidance." path="/brain/explore" noindex />
      <section className="relative pt-20 pb-8 sm:pt-24">
        <div className="aurora" />
        <div className="relative max-w-7xl mx-auto px-6 sm:px-10">
          <SectionLabel testId="explore-label">Vametra AI Brain · on-demand report</SectionLabel>
          <h1 data-testid="explore-title" className="font-display font-extrabold tracking-tight text-4xl sm:text-5xl lg:text-6xl mt-5 leading-[1.05] max-w-4xl">
            {r ? r.h1 : "Any corridor. Any market. Any product."}
          </h1>
          <p className="mt-4 text-slate-300 max-w-2xl text-base sm:text-lg">
            {r ? n.tagline : "Pick what you need and the Brain assembles it from live duty, demand and buyer data — the same structure as our published pages, built when you ask."}
          </p>
          <div className="mt-6 flex gap-2 flex-wrap" data-testid="explore-kind-tabs">
            {Object.entries(KIND_META).map(([k, m]) => (
              <button key={k} data-testid={`explore-tab-${k}`} onClick={() => nav(`/brain/explore?kind=${k}`)}
                className={`px-3.5 py-1.5 rounded-full text-sm border transition-colors ${k === kind ? "bg-cyan-500/15 border-cyan-400/40 text-cyan-200" : "glass border-transparent hover:border-cyan-400/30"}`}>{m.label}</button>
            ))}
          </div>
          <div className="mt-5 glass-strong rounded-3xl p-5 sm:p-6">
            <BrainExploreForm key={kind + sp.toString()} kind={kind} defaults={params} onSubmit={(v) => nav(exploreUrl(kind, v))} />
          </div>
        </div>
      </section>

      <div className="max-w-7xl mx-auto px-6 sm:px-10 pb-20">
        {state === "loading" && <BrainThinking testId="explore-loading" />}
        {state === "error" && <div data-testid="explore-error" className="glass rounded-3xl p-6 text-sm text-rose-300 flex items-center gap-2"><Warning size={16} /> {err}</div>}

        {r && (
          <>
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4" data-testid="explore-kv">
              <KV label="Applied import duty" accent testId="explore-kv-duty"
                value={duty?.importDuty ? `${duty.importDuty.rate}% ${duty.importDuty.type} (${duty.importDuty.year})` : "Not in WITS"} />
              <KV label="Preferential rate" testId="explore-kv-pref" value={duty?.preferential ? `${duty.preferential.rate}% · ${duty.preferential.type}` : duty ? "None reported" : "—"} />
              <KV label={`${r.destination || "Market"} imports (${demand?.year || "—"})`} testId="explore-kv-demand"
                value={demand?.countryImportsUSD != null ? `${money(demand.countryImportsUSD)}${demand.countryRank ? ` · #${demand.countryRank}` : ""}` : demand ? `World ${money(demand.worldImportsUSD)}` : "—"} />
              <KV label="Verified buyers" testId="explore-kv-buyers" value={buyers?.covered ? `${buyers.total.toLocaleString()}${buyers.matchingHs ? ` · ${buyers.matchingHs} in this HS` : ""}` : buyers ? "Coverage expanding" : "—"} />
            </div>
            {r.notes?.length > 0 && (
              <div data-testid="explore-notes" className="mt-4 text-[12px] text-amber-200/90 glass rounded-2xl p-4 space-y-1">{r.notes.map((x, i) => <div key={i}>{x}</div>)}</div>
            )}

            <section className="mt-8 grid lg:grid-cols-2 gap-5" data-testid="explore-process">
              <Card title="Export process" Icon={Compass}><p className="mt-3 text-slate-300 text-sm leading-relaxed">{n.exportProcess}</p></Card>
              <Card title="Import process" Icon={Compass}><p className="mt-3 text-slate-300 text-sm leading-relaxed">{n.importProcess}</p></Card>
              <Card title="Customs information" Icon={ShieldCheck}><p className="mt-3 text-slate-300 text-sm leading-relaxed">{n.customsInfo}</p>
                {duty?.notes?.length > 0 && <ul className="mt-3 text-[12px] text-slate-400 list-disc pl-4 space-y-1">{duty.notes.map((x, i) => <li key={i}>{x}</li>)}</ul>}
              </Card>
              <Card title="Documents required" Icon={FileText}><div className="mt-3"><ChipList items={n.documents || []} testIdPrefix="explore-doc" /></div></Card>
              {(n.popularProducts || []).length > 0 && (
                <Card title="Established products on this lane" className="lg:col-span-2"><div className="mt-3"><ChipList items={n.popularProducts} variant="violet" testIdPrefix="explore-prod" /></div></Card>
              )}
              {r.regionCountries?.length > 0 && (
                <Card title={`${r.region} — tariff-reporting markets`} className="lg:col-span-2"><div className="mt-3"><ChipList items={r.regionCountries} testIdPrefix="explore-region-c" /></div></Card>
              )}
            </section>

            {demand && (
              <section className="mt-5 grid lg:grid-cols-2 gap-5" data-testid="explore-demand">
                <Card title={`Top importers · ${demand.description || `HS ${r.hs6}`} (${demand.year})`} Icon={ChartLineUp}>
                  <ul className="mt-3 space-y-1.5 text-sm">{demand.topImporters.map((x) => <li key={x.country} className="flex justify-between"><span>{x.country}</span><span className="text-slate-400">{money(x.value)}</span></li>)}</ul>
                </Card>
                <Card title="Leading exporters" Icon={ChartLineUp}>
                  <ul className="mt-3 space-y-1.5 text-sm">{demand.topExporters.map((x) => <li key={x.country} className="flex justify-between"><span>{x.country}</span><span className="text-slate-400">{money(x.value)}</span></li>)}</ul>
                </Card>
              </section>
            )}

            {(r.expos?.length > 0 || r.news?.length > 0) && (
              <section className="mt-5 grid lg:grid-cols-2 gap-5">
                {r.expos?.length > 0 && <Card title={`Trade expos · ${r.destination}`} Icon={CalendarBlank}><ul className="mt-3 space-y-2 text-sm">{r.expos.map((e, i) => <li key={i}><Link to={e.id ? `/expo/${e.id}` : "/expo"} className="hover:text-cyan-300">{e.name || e.title}</Link><span className="text-slate-500 text-xs ml-2">{String(e.startDate || e.starts_at || "").slice(0, 10)}</span></li>)}</ul></Card>}
                {r.news?.length > 0 && <Card title={`Trade news · ${r.destination}`} Icon={Newspaper}><ul className="mt-3 space-y-2 text-sm">{r.news.map((x, i) => <li key={i}><a href={x.url || "/trade-news"} target="_blank" rel="noopener noreferrer" className="hover:text-cyan-300">{x.title}</a><span className="text-slate-500 text-xs ml-2">{x.source || ""}</span></li>)}</ul></Card>}
              </section>
            )}

            {n.opportunities && <p className="mt-6 text-sm text-slate-300 max-w-3xl" data-testid="explore-opportunities">{n.opportunities}</p>}

            <section className="mt-8 grid sm:grid-cols-2 lg:grid-cols-4 gap-3" data-testid="explore-actions">
              <Link to={`/tools/duty-calculator?hs=${r.hs6 || ""}`} data-testid="explore-cta-duty" className="glass rounded-2xl p-4 hover:border-cyan-400/40 border border-transparent"><div className="text-sm font-semibold">Custom duty calculator</div><div className="text-[11px] text-slate-400">Any origin, any HS code</div></Link>
              <Link to={`/tools/landed-cost-calculator?hs=${r.hs6 || ""}`} data-testid="explore-cta-landed" className="glass rounded-2xl p-4 hover:border-cyan-400/40 border border-transparent"><div className="text-sm font-semibold">Landed cost</div><div className="text-[11px] text-slate-400">FOB → CIF → landed</div></Link>
              <Link to="/tools/find-buyers" data-testid="explore-cta-buyers" className="glass rounded-2xl p-4 hover:border-cyan-400/40 border border-transparent"><div className="text-sm font-semibold">Find verified buyers</div><div className="text-[11px] text-slate-400">{buyers?.covered ? `${buyers.total.toLocaleString()} records in ${r.destination}` : "Coverage by market"}</div></Link>
              <Link to={`/brain?q=${encodeURIComponent(`Deep dive: ${r.title}. What else should I check before shipping?`)}`} data-testid="explore-cta-brain" className="glass rounded-2xl p-4 hover:border-cyan-400/40 border border-transparent"><Brain size={16} weight="duotone" className="text-cyan-300" /><div className="text-sm font-semibold mt-1">Continue with the Brain</div><div className="text-[11px] text-slate-400">Ask follow-up questions</div></Link>
            </section>

            {r.closestPublished?.length > 0 && (
              <div className="mt-6 flex flex-wrap gap-2" data-testid="explore-published">
                <span className="text-[11px] text-slate-400 self-center">Published pages for this lane:</span>
                {r.closestPublished.map((l) => <Link key={l.to} to={l.to} className="text-[12px] glass rounded-full px-3 py-1.5 hover:border-cyan-400/40 inline-flex items-center gap-1">{l.label} <ArrowRight size={11} /></Link>)}
              </div>
            )}

            <div className="-mx-6 sm:-mx-10"><PageFaq items={r.faqs || []} heading={`${r.title} — frequently asked questions`} testIdPrefix="explore-faq" /></div>

            <div className="mt-10 text-[11px] text-slate-500 max-w-3xl leading-relaxed" data-testid="explore-sources">
              Sources: {r.sources.map((s) => `${s.name} (${s.for})`).join(" · ")}. {r.disclaimer} Generated {String(r.generatedAt).slice(0, 10)}{r.aiLive ? "" : " · narrative fallback (AI unavailable)"}.
            </div>
          </>
        )}
      </div>
    </div>
  );
}
