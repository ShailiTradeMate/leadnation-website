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
const EXAMPLES = ["Laptop", "Basmati rice", "Agarbatti", "Cotton t-shirt", "Smartphone", "Centrifugal pump"];

export default function HsnFinder() {
  const [p] = useSearchParams();
  const [form, setForm] = useState({ productName: p.get("q") || "", description: "", hs6: p.get("hs") || "", origin: p.get("from") || "356", destination: p.get("to") || "784" });
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
        title="HS Code Finder · All 5,606 HS Codes with Import Duty for Any Trade Lane"
        description="Find the correct HS / HSN code for any product from the complete WCO HS-2022 nomenclature. Pick your exporting and importing country to see the live MFN and preferential import duty, destination VAT and origin-specific export benefits. Free, instant, global."
        path="/tools/hsn-finder"
        keywords="HS code finder, HSN code finder, HS code search, harmonized system code lookup, import duty by HS code, HS code for laptop, HS code for basmati rice, tariff code lookup"
      />
      <ToolShell testIdPrefix="hsn" label="HSN Finder"
        title="Find your HS code — then see what it costs on your trade lane."
        sub="Type the product as you'd say it ('laptop', 'agarbatti', 'cotton t-shirt'). We rank the matching lines from all 5,606 WCO HS-2022 codes, then pull the live import duty into your importing country — including any preferential rate for your exporting country — plus destination VAT and origin-specific export benefits.">
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
            <div className="grid grid-cols-2 gap-3">
              <Field label="Exporting from">
                <LaneCountrySelect testId="hsn-origin" className={inputCls} value={form.origin} onChange={(e) => setForm({ ...form, origin: e.target.value })} />
              </Field>
              <Field label="Importing to">
                <LaneCountrySelect testId="hsn-destination" className={inputCls} value={form.destination} onChange={(e) => setForm({ ...form, destination: e.target.value })} />
              </Field>
            </div>
            <button data-testid="hsn-submit" className="btn-primary w-full justify-center" disabled={loading}>
              {loading ? <><CircleNotch size={16} className="animate-spin" /> Classifying…</> : <><MagnifyingGlass size={16} weight="bold" /> Find HS code</>}
            </button>
            {err && <div data-testid="hsn-error" className="text-amber-300 text-sm">{err}</div>}
          </form>

          <div className="lg:col-span-7 min-w-0 space-y-4">
            {data?.results?.map((r, i) => (
              <div key={r.code} data-testid={`hsn-result-${i}`} className={`glass-strong rounded-3xl p-6 ${i === 0 ? "border border-cyan-400/25" : ""}`}>
                <div className="flex items-start justify-between gap-3 flex-wrap">
                  <div className="flex items-center gap-3 flex-wrap">
                    <span data-testid={`hsn-${i}-code`} className={`font-mono-display font-extrabold tracking-wider rounded-xl px-3 py-1.5 border ${i === 0 ? "text-3xl sm:text-4xl text-cyan-200 bg-cyan-500/15 border-cyan-400/40 shadow-[0_0_24px_rgba(34,211,238,0.25)]" : "text-2xl text-cyan-300 bg-cyan-500/10 border-cyan-400/20"}`}>{r.code}</span>
                    <div className="text-[10px] font-mono-display tracking-[0.25em] uppercase text-slate-400">HS code · Chapter {r.chapter}{i === 0 ? <span className="text-emerald-300"> · Best match</span> : ""}</div>
                  </div>
                  <div className="text-[10px] uppercase tracking-widest text-slate-400 font-mono-display">{r.sectionName}</div>
                </div>
                <h2 className="font-display font-bold text-xl sm:text-2xl mt-3">{r.title}</h2>
                <div className="mt-1 text-xs text-slate-400">{data.originName || "Any origin"} → {data.destinationName || "destination"}</div>
                <div className="mt-4 grid sm:grid-cols-3 gap-3">
                  <Mini icon={Scales} label={`Import duty · ${data.destinationName || "destination"}`}
                    value={r.importDuty ? `${r.importDuty.rate}%` : i < 3 ? "No WITS record" : "—"}
                    sub={r.importDuty ? `MFN applied · ${r.importDuty.year} · WITS` : i < 3 ? "try another importing country" : "top 3 only"} />
                  <Mini icon={Gift} label={`Preferential · from ${data.originName || "origin"}`}
                    value={r.preferentialDuty ? `${r.preferentialDuty.rate}%` : r.importDuty ? "None found" : "—"}
                    sub={r.preferentialDuty ? `${r.preferentialDuty.type} · ${r.preferentialDuty.year} · needs Certificate of Origin` : r.importDuty ? "MFN rate applies" : i < 3 ? "no tariff record" : "top 3 only"} />
                  <Mini icon={Receipt} label={r.destinationVat ? `${r.destinationVat.label} · ${data.destinationName}` : "Destination VAT / GST"}
                    value={r.destinationVat?.rate != null ? `${r.destinationVat.rate}%` : "—"}
                    sub={form.destination === "356" ? `${r.igstSource || "chapter default"} · verify 8-digit line` : "standard rate · on CIF + duty"} />
                </div>
                {form.origin === "356" && (
                  <div className="mt-3 glass rounded-2xl px-4 py-3 flex items-center gap-3 text-sm" data-testid={`hsn-${i}-origin-benefit`}>
                    <Gift size={16} weight="duotone" className="text-emerald-300 shrink-0" />
                    <span className="text-slate-300">Export benefit from India (RoDTEP, DGFT Appendix 4R): <strong className="text-emerald-300">{r.rodtep ? `${r.rodtep.rate}% of FOB` : "not listed for this chapter"}</strong>{r.igstSlab != null ? <span className="text-slate-400"> · India GST on this line ≈ {r.igstSlab}%</span> : null}</span>
                  </div>
                )}
                <div className="mt-4 flex flex-wrap gap-2">
                  <Link to={`/tools/duty-calculator?hs=${r.code}&from=${form.origin}&to=${form.destination}`} data-testid={`hsn-${i}-duty`} className="btn-ghost !py-2 text-xs">Full duty & FTA check</Link>
                  <Link to={`/tools/product-research?hs=${r.code}`} data-testid={`hsn-${i}-demand`} className="btn-ghost !py-2 text-xs">Who imports it</Link>
                  <Link to={`/hsn/${r.code}`} data-testid={`hsn-${i}-detail`} className="btn-ghost !py-2 text-xs">HS page <ArrowRight size={12} /></Link>
                </div>
              </div>
            ))}
            {data && (
              <>
                <div className="text-[11px] text-slate-500 px-1" data-testid="hsn-sources">Sources: {data.sources.join(" · ")}. {data.note}</div>
                {top && <BrainNextSteps tool="hsn" testIdPrefix="hsn-next"
                  inputs={{ hs: top.code, origin: form.origin, destination: form.destination, product: form.productName || top.title }}
                  result={{ hsCode: top.code, title: top.title, importDuty: top.importDuty, preferentialDuty: top.preferentialDuty, destinationVat: top.destinationVat, exportBenefitOrigin: form.origin === "356" ? top.rodtep : null, alternatives: data.results.slice(1, 3).map((r) => `${r.code} ${r.title}`) }} />}
              </>
            )}
            {!data && !loading && (
              <Card title="How classification works">
                <p className="text-sm text-slate-400 mt-2 leading-relaxed">The first six digits (HS6) are identical in every country — that is what we classify here. Each national schedule then adds its own digits (India ITC-HS 8, EU CN 8, US HTS 10). Start here, then confirm the national line with your customs broker or in the Customs & Compliance Engine.</p>
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
