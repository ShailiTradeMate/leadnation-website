import { useEffect, useState } from "react";
import { adminApi } from "@/lib/admin";
import { MetaLogo, Key, WarningCircle, ArrowsClockwise, EnvelopeSimple, Eye, CursorClick, Target } from "@phosphor-icons/react";

const n = (v, d = 0) => (v == null || v === "" ? "—" : Number(v).toLocaleString("en-IN", { maximumFractionDigits: d }));
const paise = (v) => (v == null ? "—" : `₹${n(Number(v) / 100, 2)}`);
const dt = (iso) => (iso && iso !== "never" ? new Date(iso).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" }) : iso || "—");

function Stat({ label, value, icon: I, tone = "text-cyan-300", testid }) {
  return (
    <div className="glass rounded-xl px-4 py-3" data-testid={testid}>
      <div className="flex items-center justify-between text-[11px] uppercase tracking-widest text-slate-400"><span>{label}</span>{I && <I size={14} weight="duotone" className={tone} />}</div>
      <div className="font-display font-bold text-xl mt-1" data-testid={`${testid}-value`}>{value}</div>
    </div>
  );
}

function ExpiryBadge({ token }) {
  if (!token) return null;
  const d = token.daysLeft;
  const tone = d == null ? "bg-white/10 text-slate-300" : d <= 3 ? "bg-rose-500/20 text-rose-200" : d <= 7 ? "bg-amber-500/20 text-amber-200" : "bg-emerald-500/15 text-emerald-200";
  return (
    <span className={`text-xs px-3 py-1 rounded-full inline-flex items-center gap-1 max-w-full ${tone}`} data-testid="meta-token-expiry">
      <Key size={13} /> {token.valid ? (d == null ? "Token never expires" : `Token expires in ${Math.floor(d)}d · ${dt(token.expiresAt)}`) : "Token invalid or expired"}
    </span>
  );
}

export default function MetaAdsPanel({ range }) {
  const [data, setData] = useState(null);
  const [check, setCheck] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const load = () => {
    setErr("");
    Promise.all([adminApi.get(`/admin/meta/panel?range=${range}`), adminApi.get("/admin/meta/token-check")])
      .then(([p, c]) => { setData(p.data); setCheck(c.data); })
      .catch((e) => setErr(e?.response?.data?.detail?.message || e?.response?.data?.detail || "Could not reach Meta"));
  };
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [range]);

  const act = async (path) => {
    setBusy(true); setErr("");
    try { await adminApi.post(path); load(); }
    catch (e) { setErr(e?.response?.data?.detail?.message || e?.response?.data?.detail || "Action failed"); }
    finally { setBusy(false); }
  };

  if (data && !data.configured) {
    return <section className="glass-strong rounded-2xl p-5" data-testid="meta-not-configured"><div className="flex items-center gap-2"><MetaLogo size={22} weight="duotone" className="text-sky-300" /><h3 className="font-display font-bold text-lg">Meta Ads (Marketing API)</h3></div><p className="text-sm text-slate-400 mt-2">Meta token / app credentials are not configured on this server.</p></section>;
  }
  const p = data?.primary, ins = data?.insights || [], camps = data?.campaigns || [];
  const tot = ins.reduce((a, r) => ({ spend: a.spend + Number(r.spend || 0), impressions: a.impressions + Number(r.impressions || 0), clicks: a.clicks + Number(r.clicks || 0), reach: a.reach + Number(r.reach || 0) }), { spend: 0, impressions: 0, clicks: 0, reach: 0 });
  const leads = ins.reduce((a, r) => a + (r.actions || []).filter((x) => x.action_type === "lead" || x.action_type === "onsite_conversion.lead_grouped").reduce((s, x) => s + Number(x.value || 0), 0), 0);

  return (
    <section className="glass-strong rounded-2xl p-5 space-y-4" data-testid="marketing-meta">
      <header className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="flex items-center gap-2 flex-wrap"><MetaLogo size={22} weight="duotone" className="text-sky-300" /><h3 className="font-display font-bold text-lg">Meta Ads · Marketing API</h3><span className="text-[11px] uppercase tracking-widest text-slate-500">read-only</span></div>
        <div className="flex items-center gap-2 flex-wrap">
          <ExpiryBadge token={data?.token} />
          <button data-testid="meta-exchange-token" disabled={busy} onClick={() => act("/admin/meta/exchange-token")} className="btn-ghost !py-1.5 !px-3 text-xs" title="Exchange the short-lived token in the secret card for a 60-day token"><ArrowsClockwise size={14} className={busy ? "animate-spin" : ""} /> Renew 60-day token</button>
          <button data-testid="meta-token-check-run" disabled={busy} onClick={() => act("/admin/meta/token-check/run")} className="btn-ghost !py-1.5 !px-3 text-xs"><EnvelopeSimple size={14} /> Run expiry check</button>
        </div>
      </header>
      {err && <div className="text-sm text-amber-200 flex items-center gap-2" data-testid="meta-error"><WarningCircle size={16} /> {String(err)}</div>}
      {data?.errors?.token && <div className="text-sm text-rose-200" data-testid="meta-token-error">Token problem: {data.errors.token.message || JSON.stringify(data.errors.token)}</div>}
      {!data && !err && <div className="text-sm text-slate-400" data-testid="meta-loading">Reading ad account from Meta…</div>}

      {p && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <Stat label="Ad account" value={<span className="text-base">{p.name}<span className="block text-[11px] font-normal text-slate-400">act_{p.account_id} · {p.statusLabel} · {p.currency}</span></span>} testid="meta-account" />
            <Stat label="Lifetime spent · Balance" value={`${paise(p.amount_spent)} · ${paise(p.balance)}`} testid="meta-spent" />
            <Stat label={`Spend (${range.replace("last_", "").replace("d", " days")})`} value={`₹${n(tot.spend, 2)}`} icon={Target} tone="text-emerald-300" testid="meta-spend" />
            <Stat label="Impr · Clicks · Leads" value={`${n(tot.impressions)} · ${n(tot.clicks)} · ${n(leads)}`} icon={Eye} testid="meta-impr" />
          </div>
          <div className="text-xs text-slate-400 flex flex-wrap gap-x-4 gap-y-1" data-testid="meta-token-meta">
            <span>Token: {data.usingLongLived ? "long-lived (60-day)" : "short-lived from secret card"}</span>
            <span>Data access until {dt(data.token?.dataAccessExpiresAt)}</span>
            {check?.checkedAt && <span data-testid="meta-last-check">Last expiry check {dt(check.checkedAt)} · {check.sent ? "reminder emailed" : check.stage ? "reminder already sent" : "no reminder due"}</span>}
            <span>Reminder emails go out 7 / 3 / 1 days before expiry (daily 09:00 IST).</span>
          </div>
          {camps.length === 0 ? (
            <p className="text-sm text-slate-500" data-testid="meta-no-campaigns">No campaigns in this ad account yet — nothing is running or spending. Drafts are created only on your explicit approval.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm" data-testid="meta-campaigns">
                <thead><tr className="text-left text-[11px] uppercase tracking-widest text-slate-400"><th className="py-2 pr-3 font-medium">Campaign</th><th className="py-2 pr-3 font-medium">Status</th><th className="py-2 pr-3 font-medium">Objective</th><th className="py-2 pr-3 font-medium">Budget</th><th className="py-2 pr-3 font-medium">Spend</th><th className="py-2 pr-3 font-medium">Impr</th><th className="py-2 pr-3 font-medium">Clicks</th><th className="py-2 pr-3 font-medium">CTR</th></tr></thead>
                <tbody>{camps.map((c) => { const i = ins.find((r) => r.campaign_name === c.name) || {}; return (
                  <tr key={c.id} className="border-t border-white/5">
                    <td className="py-2 pr-3 text-slate-200 max-w-[260px] truncate">{c.name}</td>
                    <td className="py-2 pr-3"><span className={`text-[11px] px-2 py-0.5 rounded-full ${c.effective_status === "ACTIVE" ? "bg-emerald-500/15 text-emerald-200" : "bg-white/10 text-slate-300"}`}>{c.effective_status || c.status}</span></td>
                    <td className="py-2 pr-3 text-slate-300">{c.objective}</td>
                    <td className="py-2 pr-3 text-slate-300">{c.daily_budget ? `${paise(c.daily_budget)}/day` : c.lifetime_budget ? `${paise(c.lifetime_budget)} total` : "—"}</td>
                    <td className="py-2 pr-3 text-slate-300">₹{n(i.spend, 2)}</td><td className="py-2 pr-3 text-slate-300">{n(i.impressions)}</td><td className="py-2 pr-3 text-slate-300">{n(i.clicks)}</td><td className="py-2 pr-3 text-slate-300">{i.ctr ? `${n(i.ctr, 2)}%` : "—"}</td>
                  </tr>); })}</tbody>
              </table>
            </div>
          )}
        </>
      )}
      {data?.errors?.account && <div className="text-sm text-amber-200" data-testid="meta-account-error">Account read failed: {data.errors.account.message || JSON.stringify(data.errors.account)}</div>}
      <p className="text-[11px] text-slate-500 flex items-center gap-1"><CursorClick size={12} /> Spend, budgets and balance are shown as Meta reports them (INR, converted from paise).</p>
    </section>
  );
}
