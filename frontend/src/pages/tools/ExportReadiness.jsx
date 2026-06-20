import React, { useState } from "react";
import { ToolShell, CTARow } from "@/components/ToolShell";
import SEO from "@/components/SEO";
import DownloadCTA from "@/components/DownloadCTA";
import { api } from "@/lib/api";
import { ClipboardText, CheckSquare, Square, ArrowRight } from "@phosphor-icons/react";

const QUESTIONS = [
  { key: "iec", label: "Do you have an IEC code?" },
  { key: "gst", label: "Do you have a GST registration?" },
  { key: "website", label: "Do you have a business website?" },
  { key: "packagingReady", label: "Is your packaging export-ready?" },
  { key: "certifications", label: "Do you have product certifications (ISO / FSSAI / Halal etc.)?" },
  { key: "experience", label: "Have you exported before?" },
];

export default function ExportReadiness() {
  const [answers, setAnswers] = useState({ iec: false, gst: false, website: false, packagingReady: false, certifications: false, experience: false });
  const [lead, setLead] = useState({ name: "", email: "", phone: "" });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1);

  const submit = async () => {
    setLoading(true);
    try {
      const { data } = await api.post("/export-readiness", { ...answers, ...lead });
      setResult(data);
      setStep(3);
    } finally { setLoading(false); }
  };

  return (
    <>
      <SEO title="Export Readiness Score · Free 60-second Assessment"
        description="Score your export readiness in 60 seconds. Get a personalised, actionable roadmap to your first international shipment — free."
        path="/tools/export-readiness"
        keywords="export readiness score, export checklist, India exporter readiness, ready to export"
      />
      <ToolShell testIdPrefix="er" label="Export Readiness"
        title="Are you ready to export? Find out in 60 seconds."
        sub="Six simple questions. One personalised roadmap. The first step toward your first international shipment."
      >
        <div className="max-w-3xl">
          {step === 1 && (
            <div className="glass-strong rounded-3xl p-7 space-y-3">
              <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300">Step 1 · Assessment</div>
              <h2 className="font-display font-bold text-2xl">Tell us where you stand</h2>
              <div className="mt-4 space-y-2">
                {QUESTIONS.map((q) => (
                  <button
                    key={q.key}
                    data-testid={`er-q-${q.key}`}
                    onClick={() => setAnswers({ ...answers, [q.key]: !answers[q.key] })}
                    className="w-full glass rounded-2xl px-4 py-3 flex items-center gap-3 text-left hover:border-cyan-400/30 transition-all"
                  >
                    {answers[q.key] ? <CheckSquare size={22} weight="fill" className="text-cyan-300" /> : <Square size={22} className="text-slate-500" />}
                    <span className="text-sm text-white">{q.label}</span>
                  </button>
                ))}
              </div>
              <button data-testid="er-next" onClick={() => setStep(2)} className="btn-primary mt-3">Next · Get my score <ArrowRight size={14} weight="bold" /></button>
            </div>
          )}

          {step === 2 && (
            <div className="glass-strong rounded-3xl p-7 space-y-3">
              <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300">Step 2 · Unlock report</div>
              <h2 className="font-display font-bold text-2xl">Where should we send your roadmap?</h2>
              <p className="text-slate-400 text-sm">Enter your details below to view your score and personalised recommendations.</p>
              <Field label="Name"><input data-testid="er-name" value={lead.name} onChange={(e) => setLead({ ...lead, name: e.target.value })} className="w-full glass rounded-xl px-4 py-3 outline-none" /></Field>
              <Field label="Email"><input data-testid="er-email" type="email" value={lead.email} onChange={(e) => setLead({ ...lead, email: e.target.value })} className="w-full glass rounded-xl px-4 py-3 outline-none" /></Field>
              <Field label="Phone / WhatsApp"><input data-testid="er-phone" value={lead.phone} onChange={(e) => setLead({ ...lead, phone: e.target.value })} className="w-full glass rounded-xl px-4 py-3 outline-none" /></Field>
              <button data-testid="er-submit" onClick={submit} className="btn-primary mt-3" disabled={loading || !lead.email}>
                {loading ? "Calculating…" : "Show me my score"}
              </button>
            </div>
          )}

          {step === 3 && result && (
            <div data-testid="er-result" className="glass-strong rounded-3xl p-8">
              <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300 flex items-center gap-2">
                <ClipboardText size={14} weight="duotone" /> Export readiness score
              </div>
              <div className="mt-3 flex items-end gap-4 flex-wrap">
                <div className="text-7xl font-display font-extrabold gradient-text">{result.score}</div>
                <div className="pb-2 text-slate-400">/ 100 · <span className="text-white">{result.band}</span></div>
              </div>
              <p className="mt-3 text-slate-300">{result.summary}</p>
              <div className="mt-7">
                <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300 mb-3">Your roadmap</div>
                <ul className="space-y-2">
                  {result.recommendations.map((r, i) => (
                    <li key={i} data-testid={`er-rec-${i}`} className="glass rounded-2xl p-4 flex items-start gap-2 text-sm">
                      <span className="text-cyan-300 font-mono-display tracking-widest text-[10px] mt-1">{String(i + 1).padStart(2, "0")}</span>
                      {r}
                    </li>
                  ))}
                </ul>
              </div>
              <CTARow testIdPrefix="er-cta" />
            </div>
          )}
        </div>
      </ToolShell>
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-12 pb-12"><DownloadCTA /></section>
    </>
  );
}
function Field({ label, children }) {
  return <label className="block"><div className="text-[10px] font-mono-display tracking-[0.25em] uppercase text-slate-400 mb-2">{label}</div>{children}</label>;
}
