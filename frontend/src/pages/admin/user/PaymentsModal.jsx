import React, { useEffect, useState } from "react";
import { Modal, Banner, input } from "./Modal";
import { adminOps, errText } from "@/lib/adminOps";

export default function PaymentsModal({ u, onClose }) {
  const [data, setData] = useState(null);
  const [plan, setPlan] = useState("monthly");
  const [days, setDays] = useState("");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState("");
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");

  const load = async () => {
    try { setData(await adminOps.payments(u.uid)); }
    catch (e) { setErr(errText(e, "Could not load payment details.")); }
  };
  useEffect(() => { load(); /* eslint-disable-next-line */ }, []);

  const act = async (action) => {
    setBusy(action); setErr(""); setOk("");
    try {
      const res = await adminOps.subscription(u.uid, {
        action, plan, days: days ? Number(days) : null, note: note || null,
      });
      setOk(res.stage === "awaiting_signoff" ? res.message : action === "grant"
        ? `${plan} subscription active until ${String(res.until).slice(0, 10)} — buyer notified.`
        : "Subscription removed — buyer notified.");
      await load();
    } catch (e) { setErr(errText(e, "Could not update the subscription.")); }
    finally { setBusy(""); }
  };

  const s = data?.subscription || {};
  return (
    <Modal testid="payments-modal" kicker="Payments & subscription" onClose={onClose} wide
      title={u.name || u.email || "Payment details"}>
      <Banner testid="payments-error">{err}</Banner>
      <Banner kind="ok" testid="payments-ok">{ok}</Banner>
      {!data && <div className="text-sm text-slate-400">Loading…</div>}
      {data && (
        <>
          <div className="grid sm:grid-cols-4 gap-3" data-testid="payments-summary">
            {[["Status", s.status || "None"], ["Plan", s.plan || "—"],
              ["Active until", s.until ? String(s.until).slice(0, 10) : "—"],
              ["Source", s.source || "—"]].map(([l, v]) => (
              <div key={l} className="glass rounded-xl px-3 py-2.5">
                <div className="text-[10px] uppercase tracking-wider text-slate-500">{l}</div>
                <div className="text-sm text-slate-100">{v}</div>
              </div>
            ))}
          </div>

          <div className="mt-5">
            <div className="text-[10px] uppercase tracking-wider text-slate-500 mb-2">Payment history</div>
            <div className="rounded-xl border border-white/10 divide-y divide-white/5 max-h-48 overflow-auto" data-testid="payments-history">
              {data.transactions.length === 0 && <div className="p-3 text-xs text-slate-500">No payments recorded.</div>}
              {data.transactions.map((t) => (
                <div key={t.id} className="px-3 py-2 flex items-center justify-between text-xs">
                  <span className="text-slate-300">{t.plan || t.kind} · {t.gateway}</span>
                  <span className="text-slate-400">{t.currency} {t.amount} · {t.status}</span>
                  <span className="text-slate-500">{String(t.createdAt || "").slice(0, 10)}</span>
                </div>
              ))}
            </div>
            <div className="text-[11px] text-slate-500 mt-2">
              {data.totals.downloads} download(s) · lifetime spend {data.totals.spend}
            </div>
          </div>

          {(data.can_grant || data.can_request_grant) && (
            <div className="mt-6 glass rounded-2xl p-4" data-testid="payments-grant-panel">
              <div className="text-sm font-semibold">{data.can_grant ? "Grant free access" : "Request free months"}</div>
              <div className="grid sm:grid-cols-3 gap-2 mt-3">
                <select data-testid="grant-plan" className={input} value={plan} onChange={(e) => setPlan(e.target.value)}>
                  <option value="monthly">Monthly (30 days)</option>
                  <option value="quarterly">Quarterly (90 days)</option>
                  <option value="annual">Annual (365 days)</option>
                </select>
                <input data-testid="grant-days" className={input} value={days} placeholder="Custom days (optional)"
                  onChange={(e) => setDays(e.target.value.replace(/\D/g, ""))} />
                <input data-testid="grant-note" className={input} value={note} placeholder="Reason (sent to buyer)"
                  onChange={(e) => setNote(e.target.value)} />
              </div>
              <div className="flex gap-2 mt-3">
                <button data-testid="grant-submit" onClick={() => act("grant")} disabled={busy === "grant"}
                  className="btn-primary !py-2 text-xs disabled:opacity-50">
                  {busy === "grant" ? "Submitting…" : data.can_grant ? "Grant & notify" : "Send approval request"}
                </button>
                {data.can_grant && <button data-testid="revoke-submit" onClick={() => act("revoke")} disabled={busy === "revoke"}
                  className="btn-ghost !py-2 text-xs disabled:opacity-50">
                  {busy === "revoke" ? "Removing…" : "Revoke subscription"}
                </button>}
              </div>
            </div>
          )}
        </>
      )}
    </Modal>
  );
}
