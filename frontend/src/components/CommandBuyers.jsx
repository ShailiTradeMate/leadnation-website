import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";
import { ArrowRight } from "@phosphor-icons/react";

export const CommandBuyers = () => {
  const [q, setQ] = useState(""), [rows, setRows] = useState([]), [total, setTotal] = useState(0), [err, setErr] = useState("");
  useEffect(() => {
    let live = true;
    const timer = setTimeout(() => api.get("/buyers/search", {params:{q, limit:12}}).then(r => {
      if (live) {setRows(r.data.buyers); setTotal(r.data.total); setErr("");}
    }).catch(() => live && setErr("Unable to load buyers. Please retry.")), 250);
    return () => {live = false; clearTimeout(timer);};
  }, [q]);
  return <section data-testid="cc-buyers" className="space-y-5 min-w-0">
    <div className="flex flex-wrap items-center justify-between gap-3"><h2 className="font-semibold text-lg">Verified Buyers</h2><Link data-testid="cc-buyers-view-all" to="/buyers" className="btn-ghost !py-2 text-xs">All buyers <ArrowRight size={15} /></Link></div>
    <input data-testid="cc-buyers-search" aria-label="Search verified buyers" className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 outline-none" placeholder="Company, product, city, country…" value={q} onChange={e => setQ(e.target.value)} />
    <p data-testid="cc-buyers-total" className="text-xs text-slate-400">{total.toLocaleString()} verified buyers</p>
    {err && <p data-testid="cc-buyers-error" role="alert" className="text-rose-300">{err}</p>}
    <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-3">{rows.map(b => <Link key={b.geid} data-testid={`cc-buyer-${b.geid}`} to={`/buyers/${b.geid}`} className="border border-white/10 rounded-lg p-4 hover:border-cyan-400/50 transition-colors min-w-0"><h3 className="font-semibold text-sm break-words">{b.display_name || b.legal_name}</h3><p className="text-xs text-slate-400 mt-2">{b.country_name || b.country} · {b.sector}</p><span className="text-xs text-emerald-300" data-testid={`cc-buyer-status-${b.geid}`}>{b.trust?.band}</span></Link>)}</div>
    {!rows.length && !err && <p data-testid="cc-buyers-empty" className="text-slate-400 text-sm">No matching buyers.</p>}
  </section>;
};