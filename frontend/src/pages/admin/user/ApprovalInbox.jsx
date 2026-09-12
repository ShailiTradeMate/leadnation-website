import React, { useEffect, useState } from "react";
import { CheckCircle, ArrowsClockwise, XCircle } from "@phosphor-icons/react";
import { staffApi } from "@/lib/staffAuth";
import { Modal, Banner, input } from "./Modal";
import { errText } from "@/lib/adminOps";

const LABELS = { review: "Verification decision", profile_edit: "Profile / demographics", subscription: "Free access", document: "Document change", hard_delete: "Hard delete", registry_claim: "Registry onboarding" };
export default function ApprovalInbox({ onDone }) {
  const [data, setData] = useState(null), [err, setErr] = useState("");
  const [selected, setSelected] = useState([]), [confirm, setConfirm] = useState(null);
  const [phrase, setPhrase] = useState(""), [busy, setBusy] = useState(false), [result, setResult] = useState([]);
  const load = async () => {
    try { setData((await staffApi.get("/admin/approvals")).data); setErr(""); }
    catch (e) { setErr(errText(e)); }
  };
  useEffect(() => { load(); }, []);
  const pending = (data?.requests || []).filter(r => ["pending", "failed"].includes(r.status));
  const open = (rows, action) => { setConfirm({ rows, action }); setPhrase(""); setResult([]); };
  const decide = async () => {
    setBusy(true); setErr(""); const outcomes = [];
    try {
      // Small independent requests avoid gateway timeouts; progress survives partial failures.
      const ordered = [...confirm.rows].sort((a, b) => Number(a.kind === "hard_delete") - Number(b.kind === "hard_delete"));
      for (const r of ordered) {
        try {
          const { data: d } = await staffApi.post("/admin/approvals/decide", {
            request_ids: [r.id], action: confirm.action, confirm_delete: phrase,
          }, { timeout: 180000 });
          outcomes.push(...d.results);
        } catch (e) { outcomes.push({ id: r.id, status: "failed", error: errText(e) }); }
        setResult([...outcomes]);
      }
      setSelected([]); await load(); onDone?.();
    } finally { setBusy(false); }
  };
  const hasDelete = confirm?.action === "approve" && confirm.rows.some(r => r.kind === "hard_delete");
  return <section data-testid="approval-inbox" className="border-y border-white/10 py-5 space-y-3 min-w-0">
    <div className="flex items-center justify-between flex-wrap gap-3">
      <h2 className="font-semibold text-lg" data-testid="approval-inbox-count">{data?.is_main ? "Approval inbox" : "My approval requests"} · {pending.length}</h2>
      <div className="flex gap-2 flex-wrap">
        <button data-testid="approval-refresh" title="Refresh requests" onClick={load} disabled={busy} className="btn-ghost !p-2"><ArrowsClockwise size={17} /></button>
        {data?.is_main && <>
          <button data-testid="bulk-approve-all" disabled={!pending.length || busy} onClick={() => open(pending, "approve")} className="btn-primary !py-2 text-xs disabled:opacity-40"><CheckCircle size={16} /> Bulk approve all ({pending.length})</button>
          <button data-testid="bulk-approve-selected" disabled={!selected.length || busy} onClick={() => open(pending.filter(r => selected.includes(r.id)), "approve")} className="btn-ghost !py-2 text-xs disabled:opacity-40">Approve selected ({selected.length})</button>
        </>}
      </div>
    </div>
    <Banner testid="approval-error">{err}</Banner>
    {!data && !err && <p data-testid="approval-loading">Loading requests…</p>}
    {data && !pending.length && <p className="text-sm text-slate-400" data-testid="approval-empty">No pending requests.</p>}
    <div className="space-y-2 max-h-[32rem] overflow-y-auto">
      {pending.map(r => <article key={r.id} data-testid={`approval-request-${r.id}`} className="border border-white/10 rounded-lg p-3 min-w-0 break-words">
        <div className="flex items-start gap-3">
          {data.is_main && <input type="checkbox" aria-label={`Select ${r.name} ${LABELS[r.kind]}`} data-testid={`approval-select-${r.id}`} checked={selected.includes(r.id)} onChange={e => setSelected(s => e.target.checked ? [...s, r.id] : s.filter(id => id !== r.id))} className="mt-1 accent-cyan-400" />}
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap justify-between gap-2"><strong className={r.kind === "hard_delete" ? "text-rose-300" : "text-cyan-200"}>{LABELS[r.kind]}</strong><span className="text-xs text-slate-400">{r.requested_by} · {r.requested_at?.slice(0, 16).replace("T", " ")}</span></div>
            <p className="text-sm mt-1" data-testid={`approval-user-${r.id}`}>{r.name || r.email} · {r.customer_id || "ID pending"}</p>
            <p className="text-xs text-slate-400 break-all">{r.email}</p>
            <p className="text-sm mt-2" data-testid={`approval-note-${r.id}`}>{r.note || "No business case supplied"}</p>
            <pre className="text-xs text-slate-300 whitespace-pre-wrap break-all mt-2" data-testid={`approval-details-${r.id}`}>{JSON.stringify(r.payload, null, 2)}</pre>
            {r.verification && <details data-testid={`approval-kyc-${r.id}`} className="mt-2"><summary data-testid={`approval-kyc-toggle-${r.id}`} className="cursor-pointer text-cyan-300 text-sm">KYC documents & checks</summary><div className="flex gap-3 flex-wrap my-2">{["selfie_file_id", "document_file_id"].map(k => r.verification[k] && <a data-testid={`approval-file-${r.id}-${k}`} key={k} target="_blank" rel="noreferrer" className="underline text-sm" href={`${process.env.REACT_APP_BACKEND_URL}/api/storage/file/${r.verification[k]}`}>{k === "selfie_file_id" ? "Selfie" : "Company KYC"}</a>)}</div><pre className="text-xs whitespace-pre-wrap break-all">{JSON.stringify(r.verification.checks, null, 2)}</pre></details>}
            {r.error && <p className="text-sm text-rose-300" data-testid={`approval-failure-${r.id}`}>{r.error}</p>}
            {data.is_main && <div className="flex gap-2 mt-3 flex-wrap">
              <button data-testid={`approval-approve-${r.id}`} disabled={busy} onClick={() => open([r], "approve")} className="btn-ghost !py-1 text-xs"><CheckCircle size={15} /> Approve request</button>
              <button data-testid={`approval-decline-${r.id}`} disabled={busy} onClick={() => open([r], "decline")} className="btn-ghost !py-1 text-xs text-rose-300"><XCircle size={15} /> Decline request</button>
            </div>}
          </div>
        </div>
      </article>)}
    </div>
    {data?.requests.some(r => ["approved", "declined", "processing", "cancelled"].includes(r.status)) && <details data-testid="approval-history"><summary data-testid="approval-history-toggle" className="cursor-pointer text-sm text-slate-400">Recent decisions & processing</summary>
      {data.requests.filter(r => ["approved", "declined", "processing", "cancelled"].includes(r.status)).slice(0, 25).map(r => <p key={r.id} data-testid={`approval-history-${r.id}`} className="text-xs break-words py-1">{r.name} · {LABELS[r.kind]} · {r.status} · {r.decided_by || r.requested_by}</p>)}
    </details>}
    {confirm && <Modal testid="bulk-approval-confirm" title={`${confirm.action === "approve" ? "Approve" : "Decline"} ${confirm.rows.length} request(s)?`} onClose={() => !busy && setConfirm(null)}>
      <div data-testid="bulk-approval-summary" className="space-y-2 max-h-64 overflow-auto text-sm break-words">{confirm.rows.map(r => <p key={r.id}>{r.name || r.email} — {LABELS[r.kind]}{r.payload.decision ? `: ${r.payload.decision}` : ""}{r.kind === "subscription" ? `: ${r.payload.days || ({monthly:30, quarterly:90, annual:365}[r.payload.plan])} days` : ""}</p>)}</div>
      {hasDelete && <label className="block mt-4 text-sm text-rose-300">Permanent account deletion included. Type DELETE<input data-testid="bulk-delete-confirmation" value={phrase} onChange={e => setPhrase(e.target.value)} className={`${input} mt-2`} /></label>}
      {result.length > 0 && <div data-testid="bulk-approval-results" className="mt-4 text-sm space-y-2" role="status">{result.map(r => <p key={r.id} className={r.status === "failed" ? "text-rose-300" : "text-emerald-300"}>{confirm.rows.find(x => x.id === r.id)?.name || r.id}: {r.status}{r.error ? ` — ${r.error}` : ""}</p>)}</div>}
      <button data-testid="bulk-approval-submit" disabled={busy || (hasDelete && phrase !== "DELETE") || result.length > 0} onClick={decide} className="btn-primary w-full justify-center mt-5 disabled:opacity-40">{busy ? `Processing ${result.length}/${confirm.rows.length}…` : "Confirm decisions"}</button>
    </Modal>}
  </section>;
}