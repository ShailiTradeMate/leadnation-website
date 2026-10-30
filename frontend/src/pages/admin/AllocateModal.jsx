import React, { useState } from "react";
import { adminApi } from "@/lib/admin";
import { toast } from "sonner";
import { X, UserPlus } from "@phosphor-icons/react";
import { ResponsiveSelect } from "@/components/ui/responsive-select";

const EXTERNAL = "__external__";

export default function AllocateModal({ item, meta, onClose, onDone }) {
  const [pick, setPick] = useState(item.assignedCaId || (item.assignedCa ? EXTERNAL : ""));
  const [name, setName] = useState(item.assignedCaId ? "" : (item.assignedCa || ""));
  const [email, setEmail] = useState(item.assignedCaEmail || "");
  const [note, setNote] = useState("");
  const [sendEmail, setSendEmail] = useState(true);
  const [extraCc, setExtraCc] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const inp = "glass rounded-lg px-3 py-2 text-sm w-full mt-1";

  const choose = (v) => {
    setPick(v);
    const ca = meta.cas.find((c) => c.id === v);
    if (ca) { setEmail(ca.email || ""); setName(""); }
  };

  const submit = async () => {
    setBusy(true); setErr("");
    const body = { note, sendEmail, extraCc: extraCc.split(/[,;\s]+/).map((x) => x.trim()).filter(Boolean), assignedCaEmail: email };
    if (pick && pick !== EXTERNAL) body.assignedCaId = pick; else body.assignedCa = name;
    try {
      const r = await adminApi.post(`/admin/service-requests/${item.id}/allocate`, body);
      toast.success(sendEmail ? `Allocated & emailed ${r.data.to}` : "Allocated");
      onDone(r.data.item);
      onClose();
    } catch (e) { setErr(e?.response?.data?.detail || "Allocation failed"); }
    finally { setBusy(false); }
  };

  const valid = (pick && pick !== EXTERNAL) || name.trim();
  return (
    <div className="fixed inset-0 z-[80] bg-black/70 backdrop-blur-sm flex items-center justify-center p-4" data-testid="allocate-modal" onClick={onClose}>
      <div className="glass-strong rounded-3xl w-full max-w-md" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
          <div>
            <div className="text-[10px] font-mono-display tracking-widest uppercase text-cyan-300">Allocate request</div>
            <div className="font-display font-bold">{item.serviceLabel || item.service} · {item.name}</div>
          </div>
          <button data-testid="allocate-close" onClick={onClose} className="p-2 rounded-lg hover:bg-white/10"><X size={18} /></button>
        </div>
        <div className="p-6 space-y-3">
          <label className="block text-xs text-slate-400">CA / employee
            <ResponsiveSelect data-testid="allocate-ca" value={pick} onChange={(e) => choose(e.target.value)} className={inp}>
              <option value="" className="bg-[#0a0f24]">— Select —</option>
              {meta.cas.map((c) => <option key={c.id} value={c.id} className="bg-[#0a0f24]">{c.name}{c.email ? ` · ${c.email}` : ""}</option>)}
              <option value={EXTERNAL} className="bg-[#0a0f24]">External CA / employee (type details)</option>
            </ResponsiveSelect>
          </label>
          {pick === EXTERNAL && (
            <label className="block text-xs text-slate-400">Name
              <input data-testid="allocate-name" value={name} onChange={(e) => setName(e.target.value)} className={inp} placeholder="e.g. Mehta & Associates" />
            </label>
          )}
          <label className="block text-xs text-slate-400">CA email {sendEmail ? "(required to send the allocation email)" : "(optional)"}
            <input data-testid="allocate-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} className={inp} placeholder="ca@firm.com" />
          </label>
          <label className="block text-xs text-slate-400">Note to CA (optional)
            <textarea data-testid="allocate-note" rows={2} value={note} onChange={(e) => setNote(e.target.value)} className={inp} placeholder="e.g. Urgent — customer travelling next week" />
          </label>
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input data-testid="allocate-send-email" type="checkbox" checked={sendEmail} onChange={(e) => setSendEmail(e.target.checked)} className="accent-cyan-400" />
            Send allocation email now <span className="text-xs text-slate-500">(CC {item.email} + admin@vametra.com)</span>
          </label>
          {sendEmail && <input data-testid="allocate-extra-cc" value={extraCc} onChange={(e) => setExtraCc(e.target.value)} className="glass rounded-lg px-3 py-2 text-xs w-full" placeholder="Extra CC (optional, comma separated)" />}
          {err && <div data-testid="allocate-error" className="text-xs text-rose-300 bg-rose-500/10 border border-rose-500/30 rounded-lg px-3 py-2">{err}</div>}
          <button data-testid="allocate-submit" disabled={busy || !valid} onClick={submit}
            className="w-full rounded-xl px-4 py-3 font-semibold bg-cyan-500 text-slate-950 hover:bg-cyan-400 disabled:opacity-40 inline-flex items-center justify-center gap-2">
            <UserPlus size={16} weight="bold" /> {busy ? "Allocating…" : (sendEmail ? "Allocate & send email" : "Allocate")}
          </button>
        </div>
      </div>
    </div>
  );
}
