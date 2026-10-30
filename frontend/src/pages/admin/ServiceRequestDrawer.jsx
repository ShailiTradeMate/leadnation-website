import React, { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { X, Copy, EnvelopeSimple, PaperPlaneRight } from "@phosphor-icons/react";
import { ResponsiveSelect } from "@/components/ui/responsive-select";

const CLOSED = ["completed", "cancelled"];
const fmt = (s) => (s || "").slice(0, 16).replace("T", " ");

function Section({ title, children, testid }) {
  return (
    <section data-testid={testid} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
      <div className="text-[10px] font-mono-display tracking-widest uppercase text-cyan-300 mb-3">{title}</div>
      {children}
    </section>
  );
}

function Rows({ rows }) {
  return (
    <dl className="grid grid-cols-[110px_minmax(0,1fr)] sm:grid-cols-[130px_minmax(0,1fr)] gap-y-1.5 gap-x-3 text-sm">
      {rows.filter(([, v]) => v !== undefined && v !== null && v !== "").map(([k, v]) => (
        <React.Fragment key={k}><dt className="text-slate-400 text-xs pt-0.5">{k}</dt><dd className="text-slate-100 break-all min-w-0">{v}</dd></React.Fragment>
      ))}
    </dl>
  );
}

function CopyBtn({ value, label }) {
  return (
    <button data-testid={`drawer-copy-${label}`} onClick={() => { navigator.clipboard?.writeText(value); toast.success(`${label} copied`); }}
      className="inline-flex items-center gap-1 text-[11px] text-cyan-300 hover:text-cyan-200"><Copy size={12} /> copy</button>
  );
}

function Conversation({ item, activity, onSendMessage, closed }) {
  const [msg, setMsg] = useState("");
  const [cc, setCc] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const endRef = useRef(null);
  useEffect(() => { endRef.current?.scrollIntoView({ block: "nearest" }); }, [activity.length]);
  const send = async () => {
    if (!msg.trim()) return;
    setBusy(true); setErr("");
    try {
      await onSendMessage({ message: msg.trim(), extraCc: cc.split(/[,;\s]+/).map((x) => x.trim()).filter(Boolean) });
      setMsg(""); setCc("");
    } catch (e) { setErr(e?.response?.data?.detail || "Send failed — please retry"); }
    finally { setBusy(false); }
  };
  return (
    <Section title={`Conversation with customer (${activity.length})`} testid="sr-drawer-conversation">
      <div className="text-[11px] text-slate-500 mb-3">Every email sent from this console appears here. Customer replies arrive in the sender's inbox (Reply-To).</div>
      <div className="space-y-2 max-h-[340px] overflow-y-auto pr-1" data-testid="sr-conversation-thread">
        <div className="flex justify-start"><div className="max-w-[85%] rounded-2xl rounded-tl-sm bg-white/[0.05] px-3 py-2 text-sm">
          <div className="text-[10px] font-mono-display tracking-wider text-emerald-300 mb-1">{item.name} · customer</div>
          <div className="text-slate-100 whitespace-pre-wrap">Requested <b>{item.serviceLabel || item.service}</b>{item.entity ? ` (${item.entity})` : ""}.{item.message ? `\n${item.message}` : ""}</div>
          <div className="text-[10px] text-slate-500 mt-1">{fmt(item.createdAt)}</div>
        </div></div>
        {activity.map((a, i) => (
          <div key={i} className="flex justify-end" data-testid={`sr-conversation-msg-${i}`}>
            <div className={`max-w-[85%] rounded-2xl rounded-tr-sm px-3 py-2 text-sm ${a.kind === "message" ? "bg-cyan-500/15 border border-cyan-400/20" : "bg-white/[0.04] border border-white/10"}`}>
              <div className="text-[10px] font-mono-display tracking-wider text-cyan-300 mb-1">{a.byName || a.by} · {a.role || a.kind}</div>
              {a.kind === "message"
                ? <div className="text-slate-100 whitespace-pre-wrap">{a.text}</div>
                : <div className="text-slate-300">Allocation email sent to <b>{a.to}</b>{a.note ? ` — "${a.note}"` : ""}</div>}
              <div className="text-[10px] text-slate-500 mt-1">{fmt(a.at)} · to {a.to}{a.cc?.length ? ` · cc ${a.cc.join(", ")}` : ""}</div>
            </div>
          </div>
        ))}
        <div ref={endRef} />
      </div>
      <div className="mt-3 space-y-2">
        <textarea data-testid="sr-message-input" rows={3} value={msg} onChange={(e) => setMsg(e.target.value)}
          placeholder={`Write to ${item.name} — sent as an email on the same thread, CC admin@vametra.com${item.assignedCaEmail ? " + CA" : ""}`}
          className="glass rounded-xl px-3 py-2 text-sm w-full" />
        <div className="flex gap-2 items-center">
          <input data-testid="sr-message-cc" value={cc} onChange={(e) => setCc(e.target.value)} placeholder="Extra CC (optional)" className="glass rounded-lg px-3 py-2 text-xs flex-1" />
          <button data-testid="sr-message-send" onClick={send} disabled={busy || !msg.trim()}
            className="rounded-lg px-4 py-2 text-xs font-semibold bg-cyan-500 text-slate-950 hover:bg-cyan-400 disabled:opacity-40 inline-flex items-center gap-1.5">
            {busy ? "Sending…" : "Send email"} <PaperPlaneRight size={13} weight="bold" />
          </button>
        </div>
        {err && <div data-testid="sr-message-error" className="text-xs text-rose-300 bg-rose-500/10 border border-rose-500/30 rounded-lg px-3 py-2">{err}</div>}
      </div>
    </Section>
  );
}

export default function ServiceRequestDrawer({ item, meta, onClose, onSave, onEmailCa, onAllocate, onSendMessage, caReadOnly = false, canEmailCa = true, statusLocked = false, extraActions = null }) {
  const [note, setNote] = useState("");
  const closed = CLOSED.includes(item.status);
  const history = [...(item.history || [])].reverse();
  const activity = item.emailActivity || [];
  const notes = [...(item.notes || [])].reverse();
  const addNote = async () => { if (!note.trim()) return; await onSave({ internalNote: note.trim() }); setNote(""); };

  return (
    <div className="fixed inset-0 z-[70] bg-black/60 backdrop-blur-sm" data-testid="sr-drawer" onClick={onClose}>
      <aside onClick={(e) => e.stopPropagation()} className="absolute right-0 top-0 h-full w-full max-w-2xl bg-[#070b1c] border-l border-white/10 shadow-2xl overflow-y-auto">
        <div className="sticky top-0 z-10 bg-[#070b1c]/95 backdrop-blur px-6 py-4 border-b border-white/10 flex items-start justify-between gap-4">
          <div>
            <div className="text-[10px] font-mono-display tracking-widest uppercase text-slate-400">Service request</div>
            <h2 className="font-display font-bold text-xl leading-tight" data-testid="sr-drawer-title">{item.serviceLabel || item.service}{item.entity ? ` · ${item.entity}` : ""}</h2>
            <div className="text-xs text-slate-400 mt-1 flex items-center gap-2">ID <span className="font-mono-display text-slate-200">{item.id}</span> <CopyBtn value={item.id} label="request-id" /></div>
          </div>
          <button data-testid="sr-drawer-close" onClick={onClose} className="p-2 rounded-lg hover:bg-white/10"><X size={18} /></button>
        </div>

        <div className="p-6 space-y-4">
          <Section title="Status & allocation" testid="sr-drawer-controls">
            <div className="grid sm:grid-cols-2 gap-3">
              <label className="text-xs text-slate-400">Status
                <ResponsiveSelect data-testid="sr-drawer-status" value={item.status || "new"} disabled={statusLocked} onChange={(e) => onSave({ status: e.target.value })} className="glass rounded-lg px-2 py-1.5 text-sm w-full mt-1 disabled:opacity-50">
                  {meta.statuses.map((s) => <option key={s} value={s} className="bg-[#0a0f24]">{s}</option>)}
                </ResponsiveSelect>
                {statusLocked && <div className="text-[11px] text-slate-500 mt-1">Completed is final — ask the main admin to reopen.</div>}
              </label>
              <div className="text-xs text-slate-400">Assigned CA
                <div className="mt-1 text-sm text-slate-100" data-testid="sr-drawer-ca">{item.assignedCa || "— Unassigned —"}{item.assignedCaEmail ? <div className="text-xs text-slate-400">{item.assignedCaEmail}</div> : null}</div>
                {caReadOnly && item.assignedCa && <div className="text-[11px] text-emerald-300 mt-0.5">Assigned to you</div>}
              </div>
            </div>
            <div className="mt-3 flex flex-wrap gap-2 items-center">
              {onAllocate && (
                <button data-testid="sr-drawer-allocate" disabled={closed} onClick={() => onAllocate(item)}
                  className="rounded-lg px-3 py-1.5 text-xs font-semibold bg-cyan-500 text-slate-950 hover:bg-cyan-400 disabled:opacity-40">
                  {item.assignedCa ? "Re-allocate" : "Allocate"}
                </button>
              )}
              {canEmailCa && (
                <button data-testid="sr-drawer-email-ca" disabled={closed} onClick={() => onEmailCa(item)}
                  className="rounded-lg px-3 py-1.5 text-xs font-semibold bg-cyan-500/20 border border-cyan-400/40 text-cyan-200 disabled:opacity-40 hover:bg-cyan-500/30 inline-flex items-center gap-1.5">
                  <EnvelopeSimple size={14} /> Email CA
                </button>
              )}
              {extraActions}
              {item.caNotifiedAt && <span className="text-[11px] text-emerald-300">CA notified ✓ {fmt(item.caNotifiedAt)}</span>}
              {closed && <span className="text-[11px] text-slate-400">Closed — allocation disabled</span>}
            </div>
          </Section>

          <Section title="Request" testid="sr-drawer-request">
            <Rows rows={[["Service", item.serviceLabel || item.service], ["Entity type", item.entity], ["Submitted", fmt(item.createdAt) + " UTC"], ["Notes from customer", item.message || "—"], ["Last updated", item.updatedAt ? `${fmt(item.updatedAt)} by ${item.updatedBy || "—"}` : null]]} />
          </Section>

          <Section title="Customer" testid="sr-drawer-customer">
            <Rows rows={[["Name", item.name], ["Email", <span className="inline-flex flex-wrap items-center gap-2 break-all">{item.email} <CopyBtn value={item.email} label="email" /></span>], ["Phone", item.phone], ["Company", item.company], ["Country", item.country]]} />
          </Section>

          <Section title="Vametra account" testid="sr-drawer-account">
            <Rows rows={(item.profileRows || [["Account", "Submitted as guest (not logged in)"]]).map(([k, v]) => [k, v])} />
          </Section>

          <Section title={`Internal notes (${notes.length}) · never emailed`} testid="sr-drawer-notes">
            <div className="flex gap-2 mb-3">
              <input data-testid="sr-drawer-note-input" value={note} onChange={(e) => setNote(e.target.value)} onKeyDown={(e) => e.key === "Enter" && addNote()} placeholder="Add an internal note…" className="glass rounded-lg px-3 py-2 text-sm flex-1" />
              <button data-testid="sr-drawer-note-add" onClick={addNote} disabled={!note.trim()} className="rounded-lg px-3 py-2 text-xs font-semibold bg-white/10 hover:bg-white/15 disabled:opacity-40">Add</button>
            </div>
            <ul className="space-y-2">
              {notes.map((n, i) => <li key={i} className="text-sm rounded-xl bg-white/[0.04] px-3 py-2"><div className="text-slate-100">{n.text}</div><div className="text-[11px] text-slate-500 mt-0.5">{fmt(n.at)} · {n.by}</div></li>)}
              {notes.length === 0 && <li className="text-xs text-slate-500">No internal notes yet.</li>}
            </ul>
          </Section>

          <Conversation item={item} activity={activity} onSendMessage={onSendMessage} closed={closed} />

          <Section title={`History (${history.length})`} testid="sr-drawer-history">
            <ol className="relative border-l border-white/10 ml-1 space-y-3">
              {history.map((h, i) => (
                <li key={i} className="pl-4 relative">
                  <span className="absolute -left-[5px] top-1.5 w-2 h-2 rounded-full bg-cyan-400" />
                  <div className="text-sm text-slate-100">{(h.changes || []).join(" · ")}</div>
                  <div className="text-[11px] text-slate-500">{fmt(h.at)} · {h.by}</div>
                </li>
              ))}
              <li className="pl-4 relative"><span className="absolute -left-[5px] top-1.5 w-2 h-2 rounded-full bg-slate-500" /><div className="text-sm text-slate-300">Request submitted</div><div className="text-[11px] text-slate-500">{fmt(item.createdAt)} · {item.accountEmail || item.email}</div></li>
            </ol>
          </Section>
        </div>
      </aside>
    </div>
  );
}
