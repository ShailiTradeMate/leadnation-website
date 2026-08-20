import React, { useEffect, useState, useCallback } from "react";
import { API } from "@/lib/api";
import { getVerifyQueue, decideVerification } from "@/lib/verifyApi";
import { CircleNotch, CheckCircle, XCircle, SealCheck, ArrowClockwise, FileText, User } from "@phosphor-icons/react";

const STATUSES = [
  { k: "needs_review", l: "Needs review" },
  { k: "verified", l: "Approved" },
  { k: "rejected", l: "Rejected" },
];

const fileUrl = (fid) => (fid ? `${API}/storage/file/${fid}` : null);

export default function VerificationReview() {
  const [status, setStatus] = useState("needs_review");
  const [data, setData] = useState({ items: [], counts: {} });
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState("");
  const [notes, setNotes] = useState({});
  const [err, setErr] = useState("");

  const load = useCallback(async () => {
    setLoading(true); setErr("");
    try { setData(await getVerifyQueue(status)); }
    catch (e) { setErr("Could not load the verification queue. Make sure you're signed in as admin."); }
    setLoading(false);
  }, [status]);

  useEffect(() => { load(); }, [load]);

  const decide = async (sid, decision) => {
    setBusyId(sid + decision);
    try { await decideVerification(sid, decision, notes[sid] || ""); await load(); }
    catch (e) { setErr("Action failed. Please retry."); }
    setBusyId("");
  };

  return (
    <div data-testid="admin-verify-review">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h2 className="font-display font-bold text-xl flex items-center gap-2">
          <SealCheck size={20} className="text-cyan-300" weight="fill" /> Verified Buyer Requests
        </h2>
        <button onClick={load} className="btn-ghost text-sm" data-testid="verify-review-refresh"><ArrowClockwise size={15} /> Refresh</button>
      </div>

      <div className="flex gap-2 mt-4 flex-wrap">
        {STATUSES.map((s) => (
          <button key={s.k} data-testid={`verify-review-tab-${s.k}`} onClick={() => setStatus(s.k)}
            className={`px-3 py-1.5 rounded-lg text-sm border ${status === s.k ? "bg-cyan-500/20 text-cyan-100 border-cyan-400/30" : "text-slate-300 hover:bg-white/5 border-transparent"}`}>
            {s.l} <span className="text-xs opacity-70">({data.counts?.[s.k] ?? 0})</span>
          </button>
        ))}
      </div>

      {err && <div className="text-rose-300 text-sm mt-3" data-testid="verify-review-error">{err}</div>}

      {loading ? (
        <div className="py-16 grid place-items-center text-slate-400"><CircleNotch size={22} className="animate-spin" /></div>
      ) : (data.items || []).length === 0 ? (
        <div className="py-16 text-center text-slate-400" data-testid="verify-review-empty">No requests in this list.</div>
      ) : (
        <div className="grid gap-4 mt-4">
          {data.items.map((it) => {
            const selfie = it.checks?.selfie || {};
            const docc = it.checks?.document || {};
            return (
              <div key={it.id} className="glass rounded-2xl p-4" data-testid={`verify-review-card-${it.id}`}>
                <div className="grid md:grid-cols-[128px_128px_1fr] gap-4">
                  <div>
                    <div className="text-[10px] uppercase tracking-widest text-slate-400 mb-1">Selfie</div>
                    {fileUrl(it.selfie_file_id) ? (
                      <img src={fileUrl(it.selfie_file_id)} alt="selfie" className="w-32 h-32 rounded-xl object-cover border border-white/10" data-testid={`verify-review-selfie-${it.id}`} />
                    ) : <div className="w-32 h-32 rounded-xl bg-white/5 grid place-items-center text-slate-500"><User size={24} /></div>}
                  </div>
                  <div>
                    <div className="text-[10px] uppercase tracking-widest text-slate-400 mb-1">Document</div>
                    {it.document_file_id ? (
                      <a href={fileUrl(it.document_file_id)} target="_blank" rel="noreferrer" data-testid={`verify-review-doc-${it.id}`}>
                        <img src={fileUrl(it.document_file_id)} alt="document" className="w-32 h-32 rounded-xl object-cover border border-white/10"
                          onError={(e) => { e.currentTarget.replaceWith(Object.assign(document.createElement("div"), { className: "w-32 h-32 rounded-xl bg-white/5 grid place-items-center text-xs text-cyan-300", textContent: "Open file" })); }} />
                      </a>
                    ) : <div className="w-32 h-32 rounded-xl bg-white/5 grid place-items-center text-slate-500"><FileText size={24} /></div>}
                  </div>
                  <div className="min-w-0">
                    <div className="font-semibold text-white">{it.customer_id ? `#${it.customer_id}` : "(no Customer ID yet)"} · {it.role || "—"}</div>
                    <div className="text-xs text-slate-400 mt-0.5">
                      Confidence: {Math.round((it.confidence || 0) * 100)}% · {it.created_at ? new Date(it.created_at).toLocaleString() : ""}
                    </div>
                    {docc.company_name && <div className="text-sm text-slate-300 mt-1">Company: {docc.company_name}</div>}
                    {docc.registration_number && <div className="text-xs text-slate-400">Reg. no: {docc.registration_number}</div>}
                    <ul className="text-xs text-slate-400 mt-2 list-disc ml-4 space-y-0.5">
                      {selfie.duplicate_face && <li className="text-amber-300">Duplicate face detected</li>}
                      {selfie.is_human_face === false && <li className="text-amber-300">No clear human face</li>}
                      {selfie.ai_generated_likelihood > 0.35 && <li className="text-amber-300">Possible AI-generated image</li>}
                      {(it.reasons || []).slice(0, 3).map((r, i) => <li key={i}>{r}</li>)}
                    </ul>

                    {status === "needs_review" && (
                      <div className="mt-3">
                        <input value={notes[it.id] || ""} onChange={(e) => setNotes((n) => ({ ...n, [it.id]: e.target.value }))}
                          placeholder="Reviewer note (optional)" data-testid={`verify-review-note-${it.id}`}
                          className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm outline-none focus:border-cyan-400/40 mb-2" />
                        <div className="flex gap-2">
                          <button onClick={() => decide(it.id, "approve")} disabled={busyId === it.id + "approve"} className="btn-primary text-sm" data-testid={`verify-review-approve-${it.id}`}>
                            {busyId === it.id + "approve" ? <CircleNotch size={14} className="animate-spin" /> : <CheckCircle size={15} />} Approve
                          </button>
                          <button onClick={() => decide(it.id, "reject")} disabled={busyId === it.id + "reject"} className="btn-ghost text-sm !text-rose-200" data-testid={`verify-review-reject-${it.id}`}>
                            {busyId === it.id + "reject" ? <CircleNotch size={14} className="animate-spin" /> : <XCircle size={15} />} Reject
                          </button>
                        </div>
                      </div>
                    )}
                    {it.reviewer && <div className="text-xs text-slate-500 mt-2">Reviewed by {it.reviewer}{it.review_note ? ` · "${it.review_note}"` : ""}</div>}
                    {it.geid && <div className="text-xs text-emerald-300 mt-1">Buyer ID: {it.geid}</div>}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
