import React, { useEffect, useState } from "react";
import { Modal, Banner, input } from "./Modal";
import { adminOps, errText } from "@/lib/adminOps";
import { Phone, EnvelopeSimple, Buildings } from "@phosphor-icons/react";

const Row = ({ I, label, value, href, testid }) => (
  <div className="flex items-center justify-between px-4 py-3 rounded-xl bg-white/5 border border-white/10">
    <span className="flex items-center gap-2 text-xs text-slate-400"><I size={14} /> {label}</span>
    {value ? (
      <a data-testid={testid} href={href} className="text-sm text-cyan-300 hover:underline">{value}</a>
    ) : <span className="text-sm text-slate-500">—</span>}
  </div>
);

export default function ContactModal({ u, onClose }) {
  const [notes, setNotes] = useState([]);
  const [channel, setChannel] = useState("call");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const load = async () => {
    try { setNotes((await adminOps.notes(u.uid)).notes || []); }
    catch (e) { setErr(errText(e, "Could not load contact notes.")); }
  };
  useEffect(() => { load(); /* eslint-disable-next-line */ }, []);

  const add = async () => {
    if (!note.trim()) return;
    setBusy(true); setErr("");
    try { await adminOps.addNote(u.uid, { channel, note }); setNote(""); await load(); }
    catch (e) { setErr(errText(e, "Could not save the note.")); }
    finally { setBusy(false); }
  };

  return (
    <Modal testid="contact-modal" kicker="Contact buyer" onClose={onClose}
      title={u.name || u.email || "Contact details"}>
      <Banner testid="contact-error">{err}</Banner>
      <div className="space-y-2">
        <Row I={Phone} label="Mobile" value={u.mobile} href={`tel:${u.mobile}`} testid="contact-mobile" />
        <Row I={EnvelopeSimple} label="Email" value={u.email} href={`mailto:${u.email}`} testid="contact-email" />
        <Row I={Buildings} label="Company email" value={u.company_email} href={`mailto:${u.company_email}`} testid="contact-company-email" />
        <Row I={Phone} label="Company contact" value={u.company_phone} href={`tel:${u.company_phone}`} testid="contact-company-phone" />
      </div>

      <div className="mt-6">
        <div className="text-[10px] uppercase tracking-wider text-slate-500 mb-2">Log a contact attempt (internal)</div>
        <div className="flex gap-2">
          <select data-testid="contact-channel" value={channel} onChange={(e) => setChannel(e.target.value)}
            className={`${input} !w-32`}>
            <option value="call">Call</option>
            <option value="email">Email</option>
            <option value="whatsapp">WhatsApp</option>
            <option value="note">Note</option>
          </select>
          <input data-testid="contact-note" className={input} value={note} placeholder="What happened?"
            onChange={(e) => setNote(e.target.value)} />
          <button data-testid="contact-note-save" onClick={add} disabled={busy} className="btn-ghost !py-2 text-xs whitespace-nowrap disabled:opacity-50">
            {busy ? "Saving…" : "Add"}
          </button>
        </div>
        <div className="mt-3 space-y-1.5 max-h-48 overflow-auto" data-testid="contact-notes">
          {notes.length === 0 && <div className="text-xs text-slate-500">No contact notes yet.</div>}
          {notes.map((n) => (
            <div key={n._id || n.at} className="text-xs text-slate-300 bg-white/[0.03] rounded-lg px-3 py-2">
              <span className="text-cyan-300 uppercase text-[10px] mr-2">{n.channel}</span>{n.note}
              <span className="text-slate-500 ml-2">— {n.by}, {String(n.at || "").slice(0, 16).replace("T", " ")}</span>
            </div>
          ))}
        </div>
      </div>
    </Modal>
  );
}
