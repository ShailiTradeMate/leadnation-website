import React, { useEffect, useState } from "react";
import { adminOps, errText } from "@/lib/adminOps";
import { Banner, input } from "./Modal";
import { Trash } from "@phosphor-icons/react";

export default function DeleteQueue({ onDone }) {
  const [rows, setRows] = useState([]);
  const [confirmText, setConfirmText] = useState({});
  const [busy, setBusy] = useState("");
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");

  const load = async () => {
    try { setRows((await adminOps.deleteRequests()).queue || []); }
    catch (e) { setErr(errText(e, "Could not load delete requests.")); }
  };
  useEffect(() => { load(); /* eslint-disable-next-line */ }, []);

  const approve = async (r) => {
    setBusy(`${r.id}-approve`); setErr(""); setOk("");
    try {
      const res = await adminOps.hardDelete(r.uid, {
        confirm: confirmText[r.id] || "", note: r.business_case, request_id: r.id,
      });
      setOk(`${r.user_email} erased everywhere (registry: ${res.identity?.do_registry}, sign-in: ${res.identity?.firebase}).`);
      if (res.warnings?.length) setErr(`Partial removal — ${res.warnings.join("; ")}.`);
      await load();
      onDone && onDone();
    } catch (e) { setErr(errText(e, "Delete failed.")); }
    finally { setBusy(""); }
  };

  const decline = async (r) => {
    setBusy(`${r.id}-decline`); setErr(""); setOk("");
    try { await adminOps.declineDeleteRequest(r.id); setOk("Request declined."); await load(); }
    catch (e) { setErr(errText(e, "Could not decline.")); }
    finally { setBusy(""); }
  };

  if (rows.length === 0 && !err) return null;

  return (
    <div className="glass-strong rounded-2xl p-4" data-testid="delete-queue">
      <div className="flex items-center gap-2 text-sm font-semibold">
        <Trash size={16} className="text-rose-300" /> Hard-delete requests awaiting your approval
        <span className="text-xs font-mono-display text-rose-300" data-testid="delete-queue-count">{rows.length}</span>
      </div>
      <div className="mt-3 space-y-2">
        <Banner testid="delete-queue-error">{err}</Banner>
        <Banner kind="ok" testid="delete-queue-ok">{ok}</Banner>
        {rows.map((r) => (
          <div key={r.id} data-testid={`delete-request-${r.uid}`}
            className="rounded-xl bg-white/[0.03] border border-white/10 p-3">
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <span className="font-medium">{r.user_name || r.user_email}</span>
              <span className="text-xs text-slate-400">{r.user_email}</span>
              <span className="text-[11px] text-slate-500">ID {r.customer_id || "—"} · requested by {r.requested_by}</span>
            </div>
            <div className="text-xs text-slate-300 mt-1">“{r.business_case}”</div>
            <div className="flex flex-wrap gap-2 mt-3">
              <input className={`${input} !w-auto min-w-[160px]`} placeholder="Type DELETE to approve"
                data-testid={`delete-request-confirm-${r.uid}`} value={confirmText[r.id] || ""}
                onChange={(e) => setConfirmText((p) => ({ ...p, [r.id]: e.target.value }))} />
              <button data-testid={`delete-request-approve-${r.uid}`} onClick={() => approve(r)}
                disabled={busy === `${r.id}-approve` || (confirmText[r.id] || "").trim().toUpperCase() !== "DELETE"}
                className="btn-primary !py-2 text-xs !bg-rose-500/80 hover:!bg-rose-500 disabled:opacity-40">
                Approve & erase everywhere
              </button>
              <button data-testid={`delete-request-decline-${r.uid}`} onClick={() => decline(r)}
                disabled={busy === `${r.id}-decline`} className="btn-ghost !py-2 text-xs disabled:opacity-50">
                Decline
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
