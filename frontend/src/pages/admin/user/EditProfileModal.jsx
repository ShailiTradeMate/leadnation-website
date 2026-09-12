import React, { useState } from "react";
import { Modal, Banner, Field, input } from "./Modal";
import { adminOps, errText } from "@/lib/adminOps";
import { COUNTRIES, statesFor } from "@/data/geo";

export default function EditProfileModal({ u, onClose, onDone }) {
  const [f, setF] = useState({
    name: u.name || "", mobile: u.mobile || "", country: u.country || "", state: u.state || "",
    city: u.city || "", role: u.category || "",
    company_name: u.company_name || "", company_email: u.company_email || "",
    company_phone: u.company_phone || "",
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");
  const states = statesFor(f.country);
  const set = (k, v) => setF((p) => ({ ...p, [k]: v }));

  const save = async () => {
    setBusy(true); setErr(""); setOk("");
    try {
      const patch = {
        name: f.name || undefined, mobile: f.mobile || undefined,
        country: f.country || undefined, state: f.state || undefined,
        city: f.city || undefined, role: f.role || undefined,
        company_details: {
          company_name: f.company_name || undefined,
          company_email: f.company_email || undefined,
          company_phone: f.company_phone || undefined,
        },
      };
      const res = await adminOps.editProfile(u.uid, patch);
      setOk(res.stage === "awaiting_signoff" ? res.message : res.changes?.length
        ? `Saved ${res.changes.length} change(s). The buyer has been emailed by the Brain.`
        : "No changes detected — nothing was sent to the buyer.");
      onDone && onDone();
    } catch (e) { setErr(errText(e, "Could not save the profile.")); }
    finally { setBusy(false); }
  };

  return (
    <Modal testid="edit-profile-modal" kicker="Edit buyer profile" onClose={onClose} wide
      title={u.name || u.email || "Buyer profile"}>
      <Banner testid="edit-error">{err}</Banner>
      <Banner kind="ok" testid="edit-ok">{ok}</Banner>
      <p className="text-xs text-slate-400 mb-4">
        Sub-admin changes require main-admin approval before they take effect.
      </p>
      <div className="grid sm:grid-cols-2 gap-3">
        <Field label="Full name"><input data-testid="edit-name" className={input} value={f.name} onChange={(e) => set("name", e.target.value)} /></Field>
        <Field label="Mobile number"><input data-testid="edit-mobile" className={input} value={f.mobile} onChange={(e) => set("mobile", e.target.value)} /></Field>
        <Field label="Country">
          <select data-testid="edit-country" className={input} value={f.country}
            onChange={(e) => { set("country", e.target.value); set("state", ""); }}>
            <option value="">Select country</option>
            {COUNTRIES.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </Field>
        <Field label="State / Province">
          {states.length > 0 ? (
            <select data-testid="edit-state" className={input} value={f.state} onChange={(e) => set("state", e.target.value)}>
              <option value="">Select state</option>
              {states.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          ) : (
            <input data-testid="edit-state" className={input} value={f.state} onChange={(e) => set("state", e.target.value)} placeholder="State / Province" />
          )}
        </Field>
        <Field label="City"><input data-testid="edit-city" className={input} value={f.city} onChange={(e) => set("city", e.target.value)} /></Field>
        <Field label="User category"><input data-testid="edit-role" className={input} value={f.role} onChange={(e) => set("role", e.target.value)} placeholder="Importer / Exporter / Trader" /></Field>
        <Field label="Company name"><input data-testid="edit-company" className={input} value={f.company_name} onChange={(e) => set("company_name", e.target.value)} /></Field>
        <Field label="Company email"><input data-testid="edit-company-email" className={input} value={f.company_email} onChange={(e) => set("company_email", e.target.value)} /></Field>
        <Field label="Company contact"><input data-testid="edit-company-phone" className={input} value={f.company_phone} onChange={(e) => set("company_phone", e.target.value)} /></Field>
      </div>
      <button data-testid="edit-save" onClick={save} disabled={busy}
        className="btn-primary mt-5 w-full justify-center disabled:opacity-50">
        {busy ? "Submitting…" : "Submit changes"}
      </button>
    </Modal>
  );
}
