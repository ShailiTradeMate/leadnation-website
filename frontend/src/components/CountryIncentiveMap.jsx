import React, { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { ArrowSquareOut, CaretDown, MagnifyingGlass, Buildings } from "@phosphor-icons/react";

const KIND_LABEL = {
  remission: "Duty/tax remission", drawback: "Duty drawback", "tax-refund": "Tax refund",
  "temporary-import": "Duty-free inputs", finance: "Export finance", insurance: "Credit insurance",
  grant: "Market-development grant",
};

export const CountryIncentiveMap = ({ testIdPrefix = "inc-map" }) => {
  const [rows, setRows] = useState([]);
  const [meta, setMeta] = useState(null);
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(null);
  const [detail, setDetail] = useState({});

  useEffect(() => {
    api.get("/incentives/countries").then(({ data }) => { setRows(data.countries || []); setMeta(data); }).catch(() => {});
  }, []);

  const filtered = useMemo(() => {
    const t = q.trim().toLowerCase();
    return t ? rows.filter((r) => r.name.toLowerCase().includes(t)) : rows;
  }, [rows, q]);

  const toggle = async (code) => {
    if (open === code) { setOpen(null); return; }
    setOpen(code);
    if (!detail[code]) {
      try { const { data } = await api.get(`/incentives/${code}`); setDetail((d) => ({ ...d, [code]: data })); } catch (_) {}
    }
  };

  return (
    <div className="glass-strong rounded-3xl p-6" data-testid={`${testIdPrefix}-root`}>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300 flex items-center gap-2">
            <Buildings size={14} weight="duotone" /> Country benefits map
          </div>
          <h3 className="font-display font-bold text-lg md:text-lg mt-2">Export support in {rows.length || "—"} exporting countries</h3>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            Every scheme below is published by that country's own authority and linked to its official page.
            Rates are only shown where a government publishes an official rate schedule.
          </p>
        </div>
        <div className="relative">
          <MagnifyingGlass size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input data-testid={`${testIdPrefix}-search`} value={q} onChange={(e) => setQ(e.target.value)}
            placeholder="Find your country"
            className="glass rounded-xl pl-9 pr-3 py-2.5 text-sm w-full sm:w-64 outline-none focus:border-cyan-400/40" />
        </div>
      </div>

      <div className="mt-5 grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {filtered.map((r) => (
          <div key={r.code} className="glass rounded-2xl overflow-hidden">
            <button data-testid={`${testIdPrefix}-${r.code}`} onClick={() => toggle(r.code)}
              className="w-full text-left px-4 py-3 flex items-center gap-3 hover:bg-white/5 transition-colors">
              <span className="flex-1">
                <span className="font-medium text-sm">{r.name}</span>
                <span className="block text-[11px] text-slate-400 mt-0.5">
                  {r.schemes} official scheme{r.schemes > 1 ? "s" : ""}{r.hasRateSchedule ? " · rate schedule published" : ""}
                </span>
              </span>
              <CaretDown size={14} className={`text-cyan-300 transition-transform ${open === r.code ? "rotate-180" : ""}`} />
            </button>
            {open === r.code && (
              <div className="px-4 pb-4 space-y-2" data-testid={`${testIdPrefix}-detail-${r.code}`}>
                {(detail[r.code]?.schemes || []).map((s, i) => (
                  <a key={i} href={s.url} target="_blank" rel="noopener noreferrer"
                    className="block rounded-xl bg-white/[0.04] border border-white/10 px-3 py-2.5 hover:border-cyan-400/30 transition-colors">
                    <div className="text-sm text-cyan-200 font-medium flex items-start gap-1">
                      {s.name} <ArrowSquareOut size={11} className="mt-1 shrink-0" />
                    </div>
                    <div className="text-[11px] text-slate-400 mt-0.5">{s.authority} · {KIND_LABEL[s.kind] || s.kind}</div>
                    <div className="text-[12px] text-slate-300 mt-1 leading-relaxed">{s.gives}</div>
                  </a>
                ))}
                {detail[r.code]?.note && <div className="text-[11px] text-amber-300/80">{detail[r.code].note}</div>}
              </div>
            )}
          </div>
        ))}
      </div>
      {meta && <div className="text-[11px] text-slate-500 mt-4">Official sources verified {meta.verifiedOn}. {meta.disclaimer}</div>}
    </div>
  );
};

export default CountryIncentiveMap;
