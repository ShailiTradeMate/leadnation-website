import React, { useEffect, useState } from "react";
import { adminOps, errText } from "@/lib/adminOps";
import { Banner, input } from "./Modal";
import { SealCheck, ArrowUUpLeft } from "@phosphor-icons/react";

export default function SignoffQueue({ onDone }) {
  const [rows, setRows] = useState([]);
  const [notes, setNotes] = useState({});
  const [busy, setBusy] = useState("");
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");
  const [open, setOpen] = useState(true);

  const load = async () => {
    try { setRows((await adminOps.signoffQueue()).queue || []); }
    catch (e) { setErr(errText(e, "Could not load the sign-off queue.")); }
  };
  useEffect(() => { load(); /* eslint-disable-next-line */ }, []);

  const act = async (r, action, decision) => {
    setBusy(`${r.submission_id}-${action}`); setErr(""); setOk("");
    try {
      const res = await adminOps.signoff(r.uid, {
        submission_id: r.submission_id, action, decision,
        note: notes[r.submission_id] || null,
      });
      setOk(res.message || `Signed off — buyer marked ${res.status || decision} and notified.`);
      await load();
      onDone && onDone();
    } catch (e) { setErr(errText(e, "Sign-off failed.")); }
    finally { setBusy(""); }
  };

  if (rows.length === 0 && !err) return null;

  return (
    <div className="glass-strong rounded-2xl p-4" data-testid="signoff-queue">
      <button onClick={() => setOpen((o) => !o)} className="flex items-center gap-2 text-sm font-semibold">
        <SealCheck size={16} className="text-amber-300" /> Ready for your final sign-off
        <span className="text-xs font-mono-display text-amber-300" data-testid="signoff-count">{rows.length}</span>
      </button>
      {open && (
        <div className="mt-3 space-y-2">
          <Banner testid="signoff-error">{err}</Banner>
          <Banner kind="ok" testid="signoff-ok">{ok}</Banner>
          {rows.map((r) => (
            <div key={r.submission_id} data-testid={`signoff-row-${r.uid}`}
              className="rounded-xl bg-white/[0.03] border border-white/10 p-3">
              <div className="flex flex-wrap items-center gap-2 text-sm">
                <span className="font-medium">{r.name || r.email}</span>
                <span className="text-xs text-slate-400">{r.email}</span>
                <span className={`text-[10px] uppercase px-2 py-0.5 rounded-full ${r.recommended === "approve" ? "bg-emerald-500/20 text-emerald-300" : "bg-rose-500/20 text-rose-300"}`}>
                  {r.recommended}
                </span>
                <span className="text-[11px] text-slate-500">by {r.recommended_by}</span>
              </div>
              {r.reviewer_note && <div className="text-xs text-slate-300 mt-1">“{r.reviewer_note}”</div>}
              <div className="flex flex-wrap gap-2 mt-3">
                <input className={`${input} !w-auto flex-1 min-w-[180px]`} placeholder="Your note (optional)"
                  data-testid={`signoff-note-${r.uid}`} value={notes[r.submission_id] || ""}
                  onChange={(e) => setNotes((p) => ({ ...p, [r.submission_id]: e.target.value }))} />
                <button data-testid={`signoff-confirm-${r.uid}`} onClick={() => act(r, "confirm")}
                  disabled={busy === `${r.submission_id}-confirm`}
                  className="btn-primary !py-2 text-xs disabled:opacity-50">Confirm {r.recommended}</button>
                <button data-testid={`signoff-override-${r.uid}`}
                  onClick={() => act(r, "override", r.recommended === "approve" ? "reject" : "approve")}
                  disabled={busy === `${r.submission_id}-override`}
                  className="btn-ghost !py-2 text-xs disabled:opacity-50">
                  Override → {r.recommended === "approve" ? "reject" : "approve"}
                </button>
                <button data-testid={`signoff-decline-${r.uid}`} onClick={() => act(r, "decline")}
                  disabled={busy === `${r.submission_id}-decline`}
                  className="btn-ghost !py-2 text-xs disabled:opacity-50">
                  <ArrowUUpLeft size={13} /> Return to sub-admin
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
