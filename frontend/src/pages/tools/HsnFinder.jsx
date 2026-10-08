import React, { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ToolShell, Card } from "@/components/ToolShell";
import SEO from "@/components/SEO";
import DownloadCTA from "@/components/DownloadCTA";
import { api } from "@/lib/api";
import { MagnifyingGlass, CircleNotch, Gift, Scales, Receipt, ArrowRight } from "@phosphor-icons/react";
import { HsCodePicker } from "@/components/HsCodePicker";
import { LaneCountrySelect } from "@/components/LaneCountrySelect";
import { BrainNextSteps } from "@/components/BrainNextSteps";

const inputCls = "w-full glass rounded-xl px-4 py-3 outline-none";
const EXAMPLES = ["Basmati rice", "Agarbatti", "Turmeric", "Cotton t-shirt", "Paracetamol tablets", "Centrifugal pump"];

export default function HsnFinder() {
  const [p] = useSearchParams();
  const [form, setForm] = useState({ productName: p.get("q") || "", description: "", hs6: p.get("hs") || "", destination: p.get("to") || "784" });
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const submit = async (e, override) => {
    e?.preventDefault();
    const body = { ...form, ...(override || {}) };
    if (!body.productName.trim() && !body.hs6) { setErr("Type a product name or pick an HS code."); return; }
    setLoading(true); setErr("");
    try {
      const { data } = await api.post("/hsn-finder", body, { timeout: 60000 });
      setData(data);
      if (!data.results?.length) setErr("No HS line matched. Try a simpler product word (e.g. 'rice', 'pump') or pick from the directory.");
    } catch (_) { setErr("Classification service unavailable — please retry."); }
    finally { setLoading(false); }
  };
  useEffect(() => { if (form.productName || form.hs6) submit(); }, []); // eslint-disable-line

  const top = data?.results?.[0];

  return (
    <>
      <SEO
        title="HSN Code Finder · All 5,606 HS Codes with RoDTEP & Import Duty"
        description="Find the correct HS / HSN code for any product from the complete WCO HS-2022 nomenclature, with DGFT RoDTEP rate, IGST slab and the live import duty at your destination. Free, instant, India-first."
        path="/tools/hsn-finder"
        keywords="HSN code finder, HS code search, HSN code for basmati rice, HSN code for agarbatti, RoDTEP rate by HS code, HS code lookup India"
      />
      <ToolShell testIdPrefix="hsn" label="HSN Finder"
        title="Find your HS code — then see what it earns and costs."
        sub="Type the product as you'd say it ('agarbatti', 'cotton t-shirt'). We rank the matching lines from all 5,606 WCO HS-2022 codes, attach the DGFT RoDTEP rate and IGST slab, and pull the live import duty at your destination for the top matches.">
        <div className="grid lg:grid-cols-12 gap-8">
          <form onSubmit={submit} className="lg:col-span-5 min-w-0 glass-strong rounded-3xl p-6 sm:p-7 space-y-4">
            <Field label="Product name">
              <input data-testid="hsn-product" value={form.productName} placeholder="e.g. Agarbatti, Basmati rice, Turmeric"
                onChange={(e) => setForm({ ...form, productName: e.target.value, hs6: "" })} className={inputCls} />
            </Field>
            <div className="flex flex-wrap gap-1.5">
              {EXAMPLES.map((x) => <button type="button" key={x} data-testid={`hsn-example-${x.toLowerCase().replace(/\s+/g, "-")}`} onClick={() => { setForm({ ...form, productName: x, hs6: "" }); submit(null, { productName: x, hs6: "" }); }} className="text-xs px-2.5 py-1 rounded-full bg-white/5 hover:bg-cyan-500/15 text-slate-300 hover:text-cyan-200 transition-colors">{x}</button>)}
            </div>
            <Field label="Extra description (optional)">
              <input data-testid="hsn-description" value={form.description} placeholder="e.g. knitted, 100% cotton, retail pack" onChange={(e) => setForm({ ...form, description: e.target.value })} className={inputCls} />
            </Field>
            <Field label="Or pick directly from the HS directory">
              <HsCodePicker label="" testId="hsn-directory-picker" value={form.hs6}
                onChange={(code, row) => { const nf = { ...form, hs6: code, productName: row?.description || form.productName }; setForm(nf); if (code) submit(null, nf); }} />
            </Field>
            <Field label="Destination for import duty">
              <LaneCountrySelect testId="hsn-destination" className={inputCls} value={form.destination} onChange={(e) => setForm({ ...form, destination: e.target.value })} />
            </Field>
            <button data-testid="hsn-submit" className="btn-primary w-full justify-center" disabled={loading}>
              {loading ? <><CircleNotch size={16} className="animate-spin" /> Classifying…</> : <><MagnifyingGlass size={16} weight="bold" /> Find HS code</>}
            </button>
            {err && <div data-testid="hsn-error" className="text-amber-300 text-sm">{err}</div>}
          </form>

          <div className="lg:col-span-7 min-w-0 space-y-4">
            {data?.results?.map((r, i) => (
              <div key={r.code} data-testid={`hsn-result-${i}`} className={`glass-strong rounded-3xl p-6 ${i === 0 ? "border border-cyan-400/25" : ""}`}>
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300">HS {r.code} · Chapter {r.chapter}{i === 0 ? " · Best match" : ""}</div>
                  <div className="text-[10px] uppercase tracking-widest text-slate-400 font-mono-display">{r.sectionName}</div>
                </div>
                <h2 className="font-display font-bold text-xl sm:text-2xl mt-2">{r.title}</h2>
                <div className="mt-4 grid sm:grid-cols-3 gap-3">
                  <Mini icon={Gift} label="RoDTEP (DGFT)" value={r.rodtep ? `${r.rodtep.rate}% of FOB` : "Not listed"} sub={r.rodtep ? "Appendix 4R · chapter-level" : "Check Appendix 4R"} />
                  <Mini icon={Receipt} label="IGST / GST" value={`${r.igstSlab}%`} sub={`${r.igstSource || "chapter default"} · verify 8-digit line`} />
                  <Mini icon={Scales} label={`Import duty · ${data.destinationName || "destination"}`}
                    value={r.importDuty ? `${r.importDuty.rate}%` : i < 3 ? "No WITS record" : "—"}
                    sub={r.importDuty ? `${r.importDuty.type} · ${r.importDuty.year} · WITS` : i < 3 ? "try another destination" : "top 3 only"} />
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  <Link to={`/tools/duty-calculator?hs=${r.code}&from=356&to=${form.destination}`} data-testid={`hsn-${i}-duty`} className="btn-ghost !py-2 text-xs">Full duty & FTA check</Link>
                  <Link to={`/tools/product-research?hs=${r.code}`} data-testid={`hsn-${i}-demand`} className="btn-ghost !py-2 text-xs">Who imports it</Link>
                  <Link to={`/hsn/${r.code}`} data-testid={`hsn-${i}-detail`} className="btn-ghost !py-2 text-xs">HS page <ArrowRight size={12} /></Link>
                </div>
              </div>
            ))}
            {data && (
              <>
                <div className="text-[11px] text-slate-500 px-1" data-testid="hsn-sources">Sources: {data.sources.join(" · ")}. {data.note}</div>
                {top && <BrainNextSteps tool="hsn" testIdPrefix="hsn-next"
                  inputs={{ hs: top.code, destination: form.destination, product: form.productName || top.title }}
                  result={{ hsCode: top.code, title: top.title, rodtep: top.rodtep, igstSlab: top.igstSlab, importDuty: top.importDuty, alternatives: data.results.slice(1, 3).map((r) => `${r.code} ${r.title}`) }} />}
              </>
            )}
            {!data && !loading && (
              <Card title="How classification works">
                <p className="text-sm text-slate-400 mt-2 leading-relaxed">HS6 is the international level used by every customs authority. India adds two digits (ITC-HS 8-digit) for the exact line on your shipping bill. Start here, then confirm the 8-digit line with your CHA or in the Customs & Compliance Engine.</p>
              </Card>
            )}
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
function Mini({ icon: I, label, value, sub }) {
  return (
    <div className="glass rounded-2xl p-3">
      <div className="text-[10px] uppercase tracking-[0.2em] text-slate-400 font-mono-display flex items-center gap-1">{I && <I size={11} weight="duotone" className="text-cyan-300" />}{label}</div>
      <div className="mt-1 font-display font-bold text-base">{value}</div>
      {sub && <div className="text-[10px] text-slate-500 mt-0.5">{sub}</div>}
    </div>
  );
}
