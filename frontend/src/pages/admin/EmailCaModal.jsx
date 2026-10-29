import React, { useEffect, useState } from "react";
import { adminApi } from "@/lib/admin";
import { toast } from "sonner";
import { X, PaperPlaneRight } from "@phosphor-icons/react";

export default function EmailCaModal({ item, onClose, onSent }) {
  const [to, setTo] = useState(item.assignedCaEmail || "");
  const [extraCc, setExtraCc] = useState("");
  const [note, setNote] = useState("");
  const [preview, setPreview] = useState(null);
  const [err, setErr] = useState("");
  const [sending, setSending] = useState(false);
  const ccList = () => extraCc.split(/[,;\s]+/).map((x) => x.trim()).filter(Boolean);

  useEffect(() => {
    const t = setTimeout(() => {
      setErr("");
      adminApi.post(`/admin/service-requests/${item.id}/email-ca`, { to, extraCc: ccList(), note, dryRun: true })
        .then((r) => setPreview(r.data))
        .catch((e) => { setPreview(null); setErr(e?.response?.data?.detail || "Could not build preview"); });
    }, 350);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [to, extraCc, note, item.id]);

  const send = async () => {
    setSending(true); setErr("");
    try {
      const r = await adminApi.post(`/admin/service-requests/${item.id}/email-ca`, { to, extraCc: ccList(), note });
      toast.success(`Sent to ${r.data.to} · CC ${r.data.cc.join(", ")}`);
      onSent(r.data.item);
      onClose();
    } catch (e) {
      setErr(e?.response?.data?.detail || "Send failed — please retry");
    } finally { setSending(false); }
  };

  const inp = "glass rounded-lg px-3 py-2 text-sm w-full";
  return (
    <div className="fixed inset-0 z-[80] bg-black/70 backdrop-blur-sm flex items-center justify-center p-4" data-testid="email-ca-modal" onClick={onClose}>
      <div className="glass-strong rounded-3xl w-full max-w-4xl max-h-[92vh] overflow-hidden flex flex-col" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
          <div>
            <div className="text-[10px] font-mono-display tracking-widest uppercase text-cyan-300">Email CA · allocation</div>
            <div className="font-display font-bold text-lg">{item.serviceLabel || item.service} · {item.name}</div>
          </div>
          <button data-testid="email-ca-close" onClick={onClose} className="p-2 rounded-lg hover:bg-white/10"><X size={18} /></button>
        </div>
        <div className="grid md:grid-cols-[360px_1fr] gap-0 flex-1 min-h-0">
          <div className="p-6 space-y-4 border-r border-white/10 overflow-y-auto">
            <label className="block text-xs text-slate-400">To (CA email)
              <input data-testid="email-ca-to" type="email" value={to} onChange={(e) => setTo(e.target.value)} className={`${inp} mt-1`} placeholder="ca@example.com" />
            </label>
            <div className="text-xs text-slate-400">CC (always included)
              <div className="mt-1 flex flex-wrap gap-1.5" data-testid="email-ca-locked-cc">
                {(preview?.lockedCc || [item.email, "admin@vametra.com"]).map((e) => <span key={e} className="rounded-full px-2.5 py-1 bg-white/5 border border-white/10 text-[11px] text-slate-200">{e}</span>)}
              </div>
            </div>
            <label className="block text-xs text-slate-400">Extra CC (optional, comma separated)
              <input data-testid="email-ca-extra-cc" value={extraCc} onChange={(e) => setExtraCc(e.target.value)} className={`${inp} mt-1`} placeholder="associate@firm.com, other@firm.com" />
            </label>
            <label className="block text-xs text-slate-400">Note to CA (optional)
              <textarea data-testid="email-ca-note" rows={3} value={note} onChange={(e) => setNote(e.target.value)} className={`${inp} mt-1`} placeholder="e.g. Customer prefers a call after 6 pm" />
            </label>
            <div className="text-xs text-slate-500">Subject<div className="text-slate-200 mt-1" data-testid="email-ca-subject">{preview?.subject || "—"}</div></div>
            {err && <div data-testid="email-ca-error" className="text-xs text-rose-300 bg-rose-500/10 border border-rose-500/30 rounded-lg px-3 py-2">{err}</div>}
            <button data-testid="email-ca-send" disabled={!preview || sending} onClick={send}
              className="w-full rounded-xl px-4 py-3 font-semibold bg-cyan-500 text-slate-950 hover:bg-cyan-400 disabled:opacity-40 flex items-center justify-center gap-2">
              {sending ? "Sending…" : "Send"} <PaperPlaneRight size={16} weight="bold" />
            </button>
          </div>
          <div className="bg-white/[0.02] min-h-[320px]">
            {preview ? <iframe title="preview" data-testid="email-ca-preview" srcDoc={preview.html} className="w-full h-full min-h-[60vh] bg-transparent" />
              : <div className="h-full grid place-items-center text-slate-500 text-sm">{err ? "Fix the error to see the preview" : "Building preview…"}</div>}
          </div>
        </div>
      </div>
    </div>
  );
}
