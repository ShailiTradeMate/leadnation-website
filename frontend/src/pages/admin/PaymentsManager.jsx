import { useEffect, useState } from "react";
import { adminApi } from "@/lib/admin";
import { CurrencyInr, Receipt, MagnifyingGlass } from "@phosphor-icons/react";

const money = (a, c) => (String(c).toLowerCase() === "inr" ? `₹${Number(a || 0).toLocaleString("en-IN")}` : `$${Number(a || 0).toFixed(2)}`);
const fmt = (d) => (d ? new Date(d).toLocaleString() : "—");

export default function PaymentsManager() {
  const [data, setData] = useState(null);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    adminApi.get(`/payments/admin/transactions?limit=300${status ? `&status=${status}` : ""}`)
      .then((r) => setData(r.data)).catch(() => setData({ transactions: [] })).finally(() => setLoading(false));
  };
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [status]);

  const rows = (data?.transactions || []).filter((t) =>
    !q || Object.values(t).some((v) => typeof v === "string" && v.toLowerCase().includes(q.toLowerCase())));

  return (
    <div data-testid="admin-payments" className="space-y-5">
      <div className="grid sm:grid-cols-3 gap-3">
        <Card label="Paid transactions" value={data?.paidCount ?? "—"} icon={<Receipt size={18} weight="fill" className="text-cyan-300" />} />
        <Card label="Revenue (India)" value={data ? `₹${Number(data.revenueINR || 0).toLocaleString("en-IN")}` : "—"} icon={<CurrencyInr size={18} weight="fill" className="text-emerald-300" />} />
        <Card label="Revenue (International)" value={data ? `$${Number(data.revenueUSD || 0).toFixed(2)}` : "—"} icon={<CurrencyInr size={18} weight="fill" className="text-emerald-300" />} />
      </div>

      <div className="flex items-center gap-2 flex-wrap">
        <div className="relative flex-1 min-w-[220px]">
          <MagnifyingGlass size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input data-testid="payments-search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search name, email, txn id, country…"
            className="w-full bg-white/5 border border-white/10 rounded-xl pl-9 pr-3 py-2 text-sm" />
        </div>
        {["", "paid", "initiated"].map((s) => (
          <button key={s || "all"} data-testid={`payments-filter-${s || "all"}`} onClick={() => setStatus(s)}
            className={`px-3 py-1.5 rounded-full text-xs uppercase tracking-widest ${status === s ? "tab-active text-white" : "bg-white/5 text-slate-300"}`}>
            {s || "all"}
          </button>
        ))}
        <span className="text-xs text-slate-400 ml-auto" data-testid="payments-count">{rows.length} record{rows.length === 1 ? "" : "s"}</span>
      </div>

      <div className="glass-strong rounded-2xl overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-[10px] uppercase tracking-widest text-slate-400 border-b border-white/10">
              <th className="text-left px-3 py-3">Date</th>
              <th className="text-left">Transaction ID</th>
              <th className="text-left">Customer</th>
              <th className="text-left">User / Customer ID</th>
              <th className="text-left">Mobile</th>
              <th className="text-left">Country</th>
              <th className="text-left">Gateway · Mode</th>
              <th className="text-left">Plan</th>
              <th className="text-right">Amount</th>
              <th className="text-left">Status</th>
              <th className="text-left">Invoice</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((t) => (
              <tr key={t.id} data-testid={`payment-row-${t.id}`} className="border-b border-white/5 hover:bg-white/5">
                <td className="px-3 py-3 text-slate-400 whitespace-nowrap">{fmt(t.paidAt || t.createdAt)}</td>
                <td className="font-mono text-[11px] text-cyan-200">{t.txnId}</td>
                <td><div className="text-slate-200">{t.name || "—"}</div><div className="text-slate-500">{t.email || "—"}</div></td>
                <td className="text-slate-400"><div className="font-mono text-[10px]">{t.userId}</div>{t.customerId ? <div className="text-slate-500 text-[10px]">{t.customerId}</div> : null}</td>
                <td className="text-slate-400">{t.mobile || "—"}</td>
                <td className="text-slate-300">{t.country || t.region || "—"}</td>
                <td className="text-slate-300 capitalize">{t.gateway}{t.method ? ` · ${t.method}` : ""}</td>
                <td className="text-slate-200">{t.plan}</td>
                <td className="text-right font-semibold text-slate-100">{money(t.amount, t.currency)}</td>
                <td><span className={`px-2 py-0.5 rounded-full text-[10px] ${t.status === "paid" ? "bg-emerald-500/10 text-emerald-300" : "bg-white/5 text-slate-400"}`}>{t.status}</span></td>
                <td className="text-slate-400 font-mono text-[10px]">{t.invoice || "—"}</td>
              </tr>
            ))}
            {!loading && rows.length === 0 && <tr><td colSpan={11} className="px-4 py-8 text-center text-slate-500">No payments yet.</td></tr>}
            {loading && <tr><td colSpan={11} className="px-4 py-8 text-center text-slate-500">Loading…</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const Card = ({ label, value, icon }) => (
  <div className="glass-strong rounded-2xl p-4 flex items-center gap-3">
    <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center">{icon}</div>
    <div><div className="text-[10px] uppercase tracking-widest text-slate-400">{label}</div><div className="font-display font-bold text-lg">{value}</div></div>
  </div>
);
