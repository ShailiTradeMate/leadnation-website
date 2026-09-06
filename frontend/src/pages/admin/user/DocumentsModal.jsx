import React, { useRef, useState } from "react";
import { Modal, Banner, Field, input } from "./Modal";
import { adminOps, errText } from "@/lib/adminOps";
import { FileText, UploadSimple } from "@phosphor-icons/react";

export default function DocumentsModal({ u, onClose, onDone }) {
  const [kind, setKind] = useState("document");
  const [label, setLabel] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");
  const fileRef = useRef(null);

  const upload = async () => {
    const file = fileRef.current?.files?.[0];
    if (!file) { setErr("Choose a file to upload."); return; }
    setBusy(true); setErr(""); setOk("");
    try {
      await adminOps.uploadDocument(u.uid, file, kind, label);
      setOk("Document uploaded and attached. The buyer has been notified by email.");
      if (fileRef.current) fileRef.current.value = "";
      onDone && onDone();
    } catch (e) { setErr(errText(e, "Upload failed.")); }
    finally { setBusy(false); }
  };

  return (
    <Modal testid="documents-modal" kicker="Documents" onClose={onClose}
      title={`${u.name || u.email || "Buyer"} · documents`}>
      <Banner testid="documents-error">{err}</Banner>
      <Banner kind="ok" testid="documents-ok">{ok}</Banner>

      <div className="space-y-2" data-testid="documents-existing">
        {u.documents?.length ? u.documents.map((d, i) => (
          <a key={i} href={`${process.env.REACT_APP_BACKEND_URL}${d.url}`} target="_blank" rel="noreferrer"
            className="flex items-center gap-2 px-4 py-3 rounded-xl bg-white/5 border border-white/10 hover:border-cyan-400/40 text-sm">
            <FileText size={14} className="text-cyan-300" /> {d.label}
          </a>
        )) : <div className="text-sm text-slate-400">No documents on file.</div>}
      </div>

      <div className="mt-6 glass rounded-2xl p-4">
        <div className="text-sm font-semibold flex items-center gap-2"><UploadSimple size={15} className="text-cyan-300" /> Upload on the buyer's behalf</div>
        <div className="grid sm:grid-cols-2 gap-3 mt-3">
          <Field label="Type">
            <select data-testid="doc-kind" className={input} value={kind} onChange={(e) => setKind(e.target.value)}>
              <option value="document">Business document</option>
              <option value="selfie">Selfie / photo ID</option>
            </select>
          </Field>
          <Field label="Label (optional)">
            <input data-testid="doc-label" className={input} value={label} onChange={(e) => setLabel(e.target.value)} placeholder="GST certificate" />
          </Field>
        </div>
        <input data-testid="doc-file" ref={fileRef} type="file" className="mt-3 text-xs text-slate-300" />
        <button data-testid="doc-upload" onClick={upload} disabled={busy}
          className="btn-primary mt-4 w-full justify-center disabled:opacity-50">
          {busy ? "Uploading…" : "Upload & notify buyer"}
        </button>
      </div>
    </Modal>
  );
}
