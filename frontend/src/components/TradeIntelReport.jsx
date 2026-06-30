import React, { useState } from "react";
import { createPortal } from "react-dom";
import { Printer, X, FilePdf, CircleNotch, CheckCircle, LockSimple } from "@phosphor-icons/react";
import { createLead } from "@/lib/api";
import { useAuth } from "@/lib/AuthContext";

const fmtUSD = (n) => {
  if (n == null) return "—";
  if (n >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
  if (n >= 1e6) return `$${(n / 1e6).toFixed(1)}M`;
  return `$${Number(n).toLocaleString()}`;
};
const num = (n) => (n == null ? "—" : Number(n).toLocaleString());
const dateStr = (iso) => { try { return new Date(iso || Date.now()).toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" }); } catch { return ""; } };

/* tiny markdown → light-theme elements (headings, bullets, bold) */
function ReportMarkdown({ text }) {
  if (!text) return <p className="text-slate-500 text-sm">Narrative unavailable.</p>;
  const lines = text.split("\n");
  const out = [];
  let list = [];
  const flush = (k) => { if (list.length) { out.push(<ul key={`u${k}`} className="list-disc pl-5 space-y-1 my-2">{list}</ul>); list = []; } };
  const inline = (s) => s.split(/(\*\*[^*]+\*\*)/g).map((p, i) => p.startsWith("**") && p.endsWith("**")
    ? <strong key={i} className="text-slate-900 font-semibold">{p.slice(2, -2)}</strong> : <span key={i}>{p}</span>);
  lines.forEach((raw, i) => {
    const l = raw.trim();
    if (!l) { flush(i); return; }
    if (/^#{1,3}\s/.test(l)) { flush(i); out.push(<h4 key={i} className="font-bold text-slate-900 text-[15px] mt-4 mb-1">{inline(l.replace(/^#{1,3}\s/, ""))}</h4>); return; }
    if (/^[-*•]\s/.test(l)) { list.push(<li key={i} className="text-[13px] text-slate-700 leading-relaxed">{inline(l.replace(/^[-*•]\s/, ""))}</li>); return; }
    flush(i);
    out.push(<p key={i} className="text-[13px] text-slate-700 leading-relaxed my-1.5">{inline(l)}</p>);
  });
  flush("end");
  return <div>{out}</div>;
}

const Section = ({ n, title, children, brk }) => (
  <section className={`report-page mt-7 ${brk ? "report-break" : ""}`}>
    <div className="flex items-center gap-2 border-b-2 border-slate-900 pb-1.5 mb-3">
      <span className="text-[11px] font-bold text-white bg-slate-900 rounded px-1.5 py-0.5">{String(n).padStart(2, "0")}</span>
      <h3 className="font-bold text-slate-900 text-base tracking-tight">{title}</h3>
    </div>
    {children}
  </section>
);

function ReportDoc({ data, preparedFor }) {
  const ts = data.tradeStats;
  const duty = data.duty;
  const p = data.price;
  const fx = data.fx;
  return (
    <div id="trade-report-print" className="bg-white text-slate-800 mx-auto" style={{ maxWidth: 820 }}>
      <div className="px-9 py-8">
        {/* Cover header */}
        <div className="report-page flex items-start justify-between border-b-4 border-cyan-500 pb-5">
          <div>
            <div className="flex items-center gap-2">
              <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-cyan-500 to-violet-600" />
              <div>
                <div className="font-extrabold text-xl text-slate-900 leading-none">LeadNation</div>
                <div className="text-[10px] tracking-[0.25em] text-slate-500 uppercase">Trade Intelligence</div>
              </div>
            </div>
            <h1 className="font-extrabold text-2xl text-slate-900 mt-5 leading-tight">Trade Intelligence Report</h1>
            <p className="text-slate-600 text-sm mt-1">{data.description || `HS ${data.hsCode}`}</p>
            <p className="text-cyan-700 font-semibold text-sm mt-0.5">{data.exporter?.name || "Any origin"} → {data.importer?.name} · HS {data.hsCode}</p>
          </div>
          <div className="text-right text-[11px] text-slate-500 shrink-0 pl-4">
            <div>Generated</div>
            <div className="font-semibold text-slate-800">{dateStr(data.generatedAt)}</div>
            {preparedFor?.name && (<><div className="mt-2">Prepared for</div>
              <div className="font-semibold text-slate-800">{preparedFor.name}</div>
              {preparedFor.company && <div className="text-slate-600">{preparedFor.company}</div>}</>)}
          </div>
        </div>

        {/* Snapshot strip */}
        <div className="report-page grid grid-cols-4 gap-3 mt-5">
          {[
            ["World trade", ts ? fmtUSD(ts.totalWorldTradeUSD) : "—", ts ? ts.year : ""],
            ["Import duty", duty?.importDuty ? `${duty.importDuty.rate}%` : "—", duty?.importDuty?.type || ""],
            ["Export benefit", duty?.exportBenefit ? `${duty.exportBenefit.rate}%` : "—", duty?.exportBenefit?.scheme || "of FOB"],
            ["Sample landed", p ? fmtUSD(p.landedUSD) : "—", "per $10k FOB"],
          ].map(([k, v, s], i) => (
            <div key={i} className="rounded-xl bg-slate-50 border border-slate-200 p-3">
              <div className="text-[10px] uppercase tracking-wider text-slate-500">{k}</div>
              <div className="font-extrabold text-slate-900 text-lg leading-tight mt-0.5">{v}</div>
              <div className="text-[10px] text-slate-500 truncate">{s}</div>
            </div>
          ))}
        </div>

        {/* 1 Executive brief */}
        <Section n={1} title="Executive Brief">
          <ReportMarkdown text={data.narrative} />
        </Section>

        {/* 2 Product & classification */}
        <Section n={2} title="Product & HS Classification">
          <table className="w-full text-[13px]">
            <tbody>
              <tr className="border-b border-slate-100"><td className="py-1.5 text-slate-500 w-44">HS code (HS6)</td><td className="font-semibold text-slate-900">{data.hsCode}</td></tr>
              <tr className="border-b border-slate-100"><td className="py-1.5 text-slate-500">Description</td><td className="text-slate-800">{data.description || "—"}</td></tr>
              <tr className="border-b border-slate-100"><td className="py-1.5 text-slate-500">Export origin</td><td className="text-slate-800">{data.exporter?.name || "Any origin"}</td></tr>
              <tr><td className="py-1.5 text-slate-500">Import destination</td><td className="text-slate-800">{data.importer?.name}</td></tr>
            </tbody>
          </table>
        </Section>

        {/* 3 Global trade statistics */}
        {ts && (
          <Section n={3} title="Global Trade Statistics">
            <p className="text-[13px] text-slate-700">World trade value in <strong>{ts.year}</strong>: <strong className="text-cyan-700">{fmtUSD(ts.totalWorldTradeUSD)}</strong>. Source: {ts.source}.</p>
            {ts.trend?.length > 1 && (
              <div className="mt-3 flex items-end gap-1.5 h-20">
                {ts.trend.slice(-8).map((t, i) => {
                  const max = Math.max(...ts.trend.map((x) => x.value)) || 1;
                  return (<div key={i} className="flex-1 flex flex-col items-center justify-end">
                    <div className="w-full bg-cyan-500/80 rounded-t" style={{ height: `${Math.max(6, (t.value / max) * 100)}%` }} />
                    <div className="text-[9px] text-slate-500 mt-1">{t.year}</div>
                  </div>);
                })}
              </div>
            )}
          </Section>
        )}

        {/* 4 Top importers */}
        {ts?.topImporters?.length > 0 && (
          <Section n={4} title="Top Importing Markets">
            <Ranked rows={ts.topImporters} />
          </Section>
        )}

        {/* 5 Top exporters */}
        {ts?.topExporters?.length > 0 && (
          <Section n={5} title="Leading Exporting Countries">
            <Ranked rows={ts.topExporters} />
          </Section>
        )}

        {/* 6 Duty & benefits */}
        {duty && (
          <Section n={6} title="Duty & Benefits (this lane)">
            <table className="w-full text-[13px]">
              <tbody>
                {duty.importDuty && <tr className="border-b border-slate-100"><td className="py-1.5 text-slate-500 w-52">Import duty into {data.importer?.name}</td><td className="font-semibold text-slate-900">{duty.importDuty.rate}% {duty.importDuty.type} ({duty.importDuty.year})</td></tr>}
                {duty.preferential && <tr className="border-b border-slate-100"><td className="py-1.5 text-slate-500">Preferential / FTA rate</td><td className="font-semibold text-emerald-700">{duty.preferential.rate}%</td></tr>}
                {duty.indiaBreakdown && <tr className="border-b border-slate-100"><td className="py-1.5 text-slate-500">India breakdown</td><td className="text-slate-800">BCD {duty.indiaBreakdown.basicCustomsDuty}% + SWS {duty.indiaBreakdown.socialWelfareSurcharge}% + IGST {duty.indiaBreakdown.igst}%</td></tr>}
                {duty.exportBenefit && <tr><td className="py-1.5 text-slate-500">Export benefit</td><td className="text-slate-800">{duty.exportBenefit.scheme}: <strong className="text-emerald-700">{duty.exportBenefit.rate}% of FOB</strong></td></tr>}
              </tbody>
            </table>
          </Section>
        )}

        {/* 7 Tariff comparison */}
        {data.tariffComparison?.length > 0 && (
          <Section n={7} title="Tariff Comparison by Market">
            <table className="w-full text-[13px]">
              <thead><tr className="text-left text-slate-500 border-b border-slate-200"><th className="py-1.5 font-medium">Destination market</th><th className="font-medium">Applied rate</th><th className="font-medium">Year</th></tr></thead>
              <tbody>{data.tariffComparison.map((c, i) => (
                <tr key={i} className="border-b border-slate-100"><td className="py-1.5 text-slate-800">{c.country}</td><td className="font-semibold text-cyan-700">{c.rate}%</td><td className="text-slate-500">{c.year}</td></tr>
              ))}</tbody>
            </table>
          </Section>
        )}

        {/* 8 Currency & FX */}
        {fx && (
          <Section n={8} title="Currency & Exchange Rates">
            <table className="w-full text-[13px]">
              <tbody>
                <tr className="border-b border-slate-100"><td className="py-1.5 text-slate-500 w-52">Your transaction currency</td><td className="font-semibold text-slate-900">1 USD = {fx.transactionRate} {fx.transactionCurrency}</td></tr>
                {data.exporterCurrency && data.exporterCurrency !== fx.transactionCurrency && (
                  <tr><td className="py-1.5 text-slate-500">{data.exporter?.name} local currency</td><td className="font-semibold text-violet-700">1 USD = {fx.exporterRate} {fx.exporterCurrency}</td></tr>
                )}
              </tbody>
            </table>
            <p className="text-[10px] text-slate-400 mt-1.5">Live rates via open.er-api.com.</p>
          </Section>
        )}

        {/* 9 Landed cost */}
        {p && (
          <Section n={9} title="Landed Cost Estimate">
            <p className="text-[12px] text-slate-500 mb-2">Illustrative for a US$10,000 FOB shipment (freight ${num(p.assumptionsUSD?.freight)}, insurance ${num(p.assumptionsUSD?.insurance)}).</p>
            <table className="w-full text-[13px]">
              <tbody>
                <tr className="border-b border-slate-100"><td className="py-1.5 text-slate-500 w-52">CIF value</td><td className="text-slate-800">{fmtUSD(p.cifUSD)}</td></tr>
                <tr className="border-b border-slate-100"><td className="py-1.5 text-slate-500">Duty @ {p.dutyRatePct}%</td><td className="text-slate-800">{fmtUSD(p.dutyUSD)}</td></tr>
                <tr className="border-b border-slate-100"><td className="py-1.5 text-slate-500">Landed cost (USD)</td><td className="font-bold text-emerald-700">{fmtUSD(p.landedUSD)}</td></tr>
                {p.landedTransaction != null && <tr className="border-b border-slate-100"><td className="py-1.5 text-slate-500">In your currency</td><td className="font-semibold text-cyan-700">{num(p.landedTransaction)} {p.transactionCurrency}</td></tr>}
                {p.landedExporter != null && p.exporterCurrency !== p.transactionCurrency && <tr><td className="py-1.5 text-slate-500">In {data.exporter?.name} currency</td><td className="font-semibold text-violet-700">{num(p.landedExporter)} {p.exporterCurrency}</td></tr>}
              </tbody>
            </table>
          </Section>
        )}

        {/* 10 Logistics */}
        {data.freightModes?.length > 0 && (
          <Section n={10} title="Freight & Logistics Options">
            <div className="flex flex-wrap gap-2">{data.freightModes.map((m, i) => (
              <span key={i} className="text-[12px] bg-slate-100 border border-slate-200 rounded-full px-3 py-1 text-slate-700">{m}</span>
            ))}</div>
          </Section>
        )}

        {/* 11 Next steps */}
        <Section n={11} title="Recommended Next Steps">
          <ol className="list-decimal pl-5 space-y-1.5 text-[13px] text-slate-700">
            <li>Validate the HS classification with your CHA and confirm the destination's current applied tariff.</li>
            <li>Request quotes from 2–3 freight forwarders for the modes above and lock Incoterms (e.g. CIF/FOB).</li>
            <li>Check eligibility & documentation for the export benefit{duty?.exportBenefit ? ` (${duty.exportBenefit.scheme})` : ""} and any FTA preferential rate.</li>
            <li>Shortlist verified buyers/suppliers in the top importing markets and begin outreach.</li>
            <li>Use the LeadNation app to track leads, duties and shipments on the move.</li>
          </ol>
        </Section>

        {/* Sources & disclaimer */}
        <section className="report-page mt-7 pt-4 border-t border-slate-200">
          <p className="text-[11px] text-slate-500"><strong className="text-slate-700">Sources & methodology:</strong> Trade statistics from {ts?.source || "OEC World / UN Comtrade"}; tariffs from World Bank WITS/TRAINS; India duty from CBIC; export benefits from DGFT; live FX from open.er-api.com. Figures are indicative and updated periodically.</p>
          <p className="text-[11px] text-slate-400 mt-2"><strong>Disclaimer:</strong> This report is for informational purposes only and does not constitute legal, financial or customs advice. Verify all duties, benefits and compliance requirements with the relevant authorities before transacting.</p>
          <div className="flex items-center justify-between mt-4 text-[11px] text-slate-500">
            <span>© {new Date().getFullYear()} LeadNation · Global Trade Intelligence</span>
            <span>leadnation.app · +91 82371 61088</span>
          </div>
        </section>
      </div>
    </div>
  );
}

function Ranked({ rows }) {
  const max = Math.max(...rows.map((r) => r.value || 0)) || 1;
  return (
    <div className="space-y-1.5">
      {rows.slice(0, 8).map((r, i) => (
        <div key={i} className="flex items-center gap-3 text-[12px]">
          <span className="w-5 text-slate-400 text-right">{i + 1}</span>
          <span className="w-36 text-slate-800 truncate">{r.country}</span>
          <div className="flex-1 h-3 bg-slate-100 rounded overflow-hidden"><div className="h-full bg-cyan-500/80" style={{ width: `${Math.max(3, (r.value / max) * 100)}%` }} /></div>
          <span className="w-20 text-right text-slate-700">{fmtUSD(r.value)}</span>
          <span className="w-12 text-right text-slate-400">{r.share != null ? `${r.share}%` : ""}</span>
        </div>
      ))}
    </div>
  );
}

const fld = "w-full rounded-xl bg-slate-800/60 border border-white/10 px-4 py-3 outline-none text-white text-sm focus:border-cyan-400/40";

export function ReportButton({ data }) {
  const { isAuthed, account } = useAuth();
  const [stage, setStage] = useState("idle"); // idle | gate | preview
  const [form, setForm] = useState({ name: "", email: "", company: "", country: "", phone: "" });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const preparedFor = isAuthed
    ? { name: account?.user?.full_name || account?.user?.email || "", company: "" }
    : { name: form.name, company: form.company };

  const openReport = () => { if (isAuthed) setStage("preview"); else setStage("gate"); };

  const submitGate = async (e) => {
    e.preventDefault(); setErr("");
    if (!form.name.trim() || !form.email.trim()) { setErr("Please enter your name and email."); return; }
    setBusy(true);
    try {
      await createLead({
        name: form.name.trim(), email: form.email.trim(), phone: form.phone.trim() || null,
        country: form.country.trim() || null, source: "trade-intelligence-report",
        message: `Company: ${form.company || "—"} · Report: HS ${data.hsCode} ${data.description || ""} · Lane: ${data.exporter?.name || "Any"} → ${data.importer?.name}`,
      });
      setStage("preview");
    } catch (_) { setErr("Could not submit — please check your details and try again."); }
    finally { setBusy(false); }
  };

  return (
    <>
      <button data-testid="compile-download-report" onClick={openReport}
        className="btn-primary gap-2"><FilePdf size={16} weight="bold" /> Download premium report</button>

      {/* Lead capture gate */}
      {stage === "gate" && createPortal(
        <div className="fixed inset-0 z-[100] grid place-items-center p-4 bg-black/70 backdrop-blur-sm no-print" data-testid="lead-gate-modal">
          <form onSubmit={submitGate} className="glass-strong rounded-3xl p-7 w-full max-w-md">
            <div className="flex items-center gap-2 text-cyan-300 text-xs font-mono-display tracking-[0.25em] uppercase"><LockSimple size={14} weight="bold" /> Free report</div>
            <h3 className="font-display font-extrabold text-2xl mt-2 text-white">Get your Trade Intelligence Report</h3>
            <p className="text-slate-400 text-sm mt-1">Tell us where to send it. Instant download — no spam.</p>
            <div className="space-y-3 mt-5">
              <input data-testid="lead-name" className={fld} placeholder="Full name *" value={form.name} onChange={(e) => set("name", e.target.value)} />
              <input data-testid="lead-email" type="email" className={fld} placeholder="Work email *" value={form.email} onChange={(e) => set("email", e.target.value)} />
              <input data-testid="lead-company" className={fld} placeholder="Company" value={form.company} onChange={(e) => set("company", e.target.value)} />
              <div className="grid grid-cols-2 gap-3">
                <input data-testid="lead-country" className={fld} placeholder="Country" value={form.country} onChange={(e) => set("country", e.target.value)} />
                <input data-testid="lead-phone" className={fld} placeholder="Phone (optional)" value={form.phone} onChange={(e) => set("phone", e.target.value)} />
              </div>
            </div>
            {err && <div data-testid="lead-error" className="text-rose-300 text-sm mt-3">{err}</div>}
            <div className="flex gap-2 mt-5">
              <button type="button" onClick={() => setStage("idle")} className="btn-ghost flex-1 justify-center">Cancel</button>
              <button type="submit" disabled={busy} data-testid="lead-submit" className="btn-primary flex-1 justify-center disabled:opacity-50">{busy ? <CircleNotch size={16} className="animate-spin" /> : <>Get report</>}</button>
            </div>
          </form>
        </div>, document.body
      )}

      {/* Report preview + print */}
      {stage === "preview" && createPortal(
        <div className="fixed inset-0 z-[100] bg-slate-900/80 backdrop-blur-sm overflow-auto report-scroll" data-testid="report-preview">
          <div className="no-print sticky top-0 z-10 flex items-center justify-between gap-3 px-5 py-3 bg-slate-950/90 border-b border-white/10">
            <div className="flex items-center gap-2 text-white text-sm"><CheckCircle size={18} weight="fill" className="text-emerald-400" /> Your report is ready</div>
            <div className="flex items-center gap-2">
              <button data-testid="report-print" onClick={() => window.print()} className="btn-primary gap-2"><Printer size={16} weight="bold" /> Print / Save as PDF</button>
              <button data-testid="report-close" onClick={() => setStage("idle")} className="btn-ghost gap-1"><X size={16} /> Close</button>
            </div>
          </div>
          <div className="py-6 px-3">
            <div className="mx-auto shadow-2xl rounded-lg overflow-hidden" style={{ maxWidth: 820 }}>
              <ReportDoc data={data} preparedFor={preparedFor} />
            </div>
          </div>
        </div>, document.body
      )}
    </>
  );
}
