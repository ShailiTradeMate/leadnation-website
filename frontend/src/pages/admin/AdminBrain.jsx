import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Brain, ArrowLeft, ArrowsClockwise, Database, Cpu, Question, Warning } from "@phosphor-icons/react";
import { adminApi, isAdminLoggedIn, getAdminToken } from "@/lib/admin";

const Panel = ({ title, icon: I, children, testid }) => (
  <div className="glass-strong rounded-2xl p-5" data-testid={testid}>
    <div className="text-xs font-mono-display tracking-[0.25em] uppercase text-cyan-300 flex items-center gap-2 mb-3">
      {I && <I size={14} weight="duotone" />} {title}
    </div>
    {children}
  </div>
);

const Stat = ({ label, value }) => (
  <div className="glass rounded-xl px-4 py-3">
    <div className="text-2xl font-display font-extrabold text-white">{value}</div>
    <div className="text-[11px] text-slate-400 uppercase tracking-wider mt-1">{label}</div>
  </div>
);

const Bars = ({ items, labelKey = "value", testid }) => (
  <div className="space-y-2" data-testid={testid}>
    {(!items || items.length === 0) && <div className="text-sm text-slate-500">No data yet.</div>}
    {items?.map((it, i) => (
      <div key={i} className="flex items-center justify-between text-sm">
        <span className="text-slate-300 truncate">{it[labelKey] || it.question}</span>
        <span className="text-cyan-300 font-mono-display text-xs ml-2">{it.count}</span>
      </div>
    ))}
  </div>
);

export default function AdminBrain() {
  const [data, setData] = useState(null);
  const [reseeding, setReseeding] = useState(false);
  const navigate = useNavigate();

  const load = () => adminApi.get("/admin/brain/overview").then((r) => setData(r.data)).catch(() => navigate("/admin-login"));

  useEffect(() => {
    if (!isAdminLoggedIn()) { navigate("/admin-login"); return; }
    load(); // eslint-disable-next-line
  }, [navigate]);

  const reseed = async () => {
    setReseeding(true);
    try { await adminApi.post("/admin/brain/knowledge/reseed"); await load(); } finally { setReseeding(false); }
  };

  if (!data) return <section className="max-w-7xl mx-auto px-6 pt-28 pb-24 text-slate-400">Loading Brain analytics…</section>;

  return (
    <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-24 pb-24">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <button onClick={() => navigate("/admin-cms")} className="text-xs text-slate-400 hover:text-cyan-300 flex items-center gap-1 mb-2" data-testid="brain-admin-back"><ArrowLeft size={12} /> Back to CMS</button>
          <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300 flex items-center gap-2"><Brain size={16} weight="duotone" /> Brain Control</div>
          <h1 className="font-display font-extrabold text-4xl sm:text-5xl mt-2">Intelligence Dashboard</h1>
        </div>
        <button onClick={reseed} disabled={reseeding} className="btn-ghost !py-2 text-xs disabled:opacity-50" data-testid="brain-reseed-btn">
          <ArrowsClockwise size={14} weight="bold" className={reseeding ? "animate-spin" : ""} /> {reseeding ? "Reseeding…" : "Reseed Knowledge Base"}
        </button>
      </div>

      {/* Provider + KB + AI usage */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 mt-8">
        <Stat label="AI Provider" value={<span className="capitalize">{data.provider.active}</span>} />
        <Stat label="Knowledge Base" value={data.knowledgeBase.total} />
        <Stat label="Total Queries" value={data.aiUsage.totalQueries} />
        <Stat label="Answer Rate" value={`${data.aiUsage.answerRate}%`} />
      </div>

      <div className="mt-4 glass rounded-xl px-4 py-3 text-xs text-slate-400" data-testid="brain-provider-note">
        Provider <span className="text-cyan-300 capitalize">{data.provider.active}</span> · live AI {data.provider.live ? "enabled" : "deferred (mock orchestration)"} · supports {data.provider.supported.join(", ")}.
      </div>

      <div className="grid lg:grid-cols-2 gap-4 mt-6">
        <Panel title="Engine Health" icon={Cpu} testid="brain-engine-health">
          <div className="grid sm:grid-cols-2 gap-2">
            {data.engineHealth.map((e) => (
              <div key={e.engine} className="flex items-center justify-between glass rounded-lg px-3 py-2 text-sm">
                <span className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-emerald-400" /> {e.engine.replace(/_/g, " ")}</span>
                <span className="text-cyan-300 font-mono-display text-xs">{e.calls}</span>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Knowledge Base Status" icon={Database} testid="brain-kb-status">
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {Object.entries(data.knowledgeBase.byKind || {}).map(([k, v]) => (
              <div key={k} className="glass rounded-lg px-3 py-2">
                <div className="text-lg font-display font-bold text-white">{v}</div>
                <div className="text-[10px] uppercase tracking-wider text-slate-400">{k}</div>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Most Asked Questions" icon={Question} testid="brain-top-questions">
          <Bars items={data.mostAskedQuestions} labelKey="question" />
        </Panel>

        <Panel title="Trending Searches" icon={Question} testid="brain-trending">
          <Bars items={data.trendingSearches} labelKey="question" />
        </Panel>

        <Panel title="Top Countries" testid="brain-top-countries"><Bars items={data.topCountries} /></Panel>
        <Panel title="Top Products" testid="brain-top-products"><Bars items={data.topProducts} /></Panel>
        <Panel title="Top HSN Codes" testid="brain-top-hsn"><Bars items={data.topHsn} /></Panel>
        <Panel title="Top Business Services" testid="brain-top-services"><Bars items={data.topServices} /></Panel>

        <Panel title="Failed Queries" icon={Warning} testid="brain-failed">
          <div className="space-y-1.5">
            {(!data.failedQueries || data.failedQueries.length === 0) && <div className="text-sm text-slate-500">None — every query was answered.</div>}
            {data.failedQueries?.map((f, i) => <div key={i} className="text-sm text-amber-200/80">{f.question}</div>)}
          </div>
        </Panel>

        <Panel title="Knowledge Gaps" icon={Warning} testid="brain-gaps">
          <div className="space-y-1.5">
            {(!data.knowledgeGaps || data.knowledgeGaps.length === 0) && <div className="text-sm text-slate-500">No gaps detected.</div>}
            {data.knowledgeGaps?.map((g, i) => <div key={i} className="text-sm text-slate-300">{g}</div>)}
          </div>
        </Panel>
      </div>
    </section>
  );
}
