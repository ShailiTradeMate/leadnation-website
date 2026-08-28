import React, { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import SEO from "@/components/SEO";
import VerifiedBadge from "@/components/VerifiedBadge";
import { useAuth } from "@/lib/AuthContext";
import { COUNTRIES, statesFor } from "@/data/geo";
import {
  getVerifyState, updateVerifyProfile, verifyUpload,
  analyzeSelfie, analyzeDocument, submitVerification, getVerifyDocuments,
} from "@/lib/verifyApi";
import CameraCapture from "@/components/CameraCapture";
import VerifyWait from "@/components/VerifyWait";
import {
  SealCheck, IdentificationCard, Camera, FileText, CircleNotch,
  CheckCircle, WarningCircle, ArrowRight, ShieldCheck, Buildings, UploadSimple,
} from "@phosphor-icons/react";

const ROLES = ["Importer", "Exporter", "Both (Import & Export)", "Wholesaler", "Distributor", "Manufacturer", "Trader"];

// Give mobile users a rear-camera document capture; laptop users upload documents (no webcam capture).
const IS_MOBILE = typeof navigator !== "undefined" && /Android|iPhone|iPad|iPod|Mobile|Windows Phone/i.test(navigator.userAgent);

const buildPatch = (form, profile) => {
  const patch = {};
  for (const [k, v] of Object.entries(form)) {
    if (v === "" || v == null) continue;
    if (k.startsWith("company_details.")) {
      patch.company_details = patch.company_details || { ...(profile?.company_details || {}) };
      patch.company_details[k.split(".")[1]] = v;
    } else if (k === "products" || k === "hsn_codes") {
      patch[k] = String(v).split(",").map((s) => s.trim()).filter(Boolean);
    } else patch[k] = v;
  }
  return patch;
};

function Step({ n, active, done, label, Icon }) {
  return (
    <div className="flex items-center gap-2" data-testid={`verify-step-${n}`}>
      <div className={`w-8 h-8 rounded-full grid place-items-center border ${done ? "bg-emerald-500/20 border-emerald-400/40 text-emerald-200" : active ? "bg-cyan-500/20 border-cyan-400/40 text-cyan-200" : "bg-white/5 border-white/10 text-slate-400"}`}>
        {done ? <CheckCircle size={16} weight="fill" /> : <Icon size={15} />}
      </div>
      <span className={`text-xs hidden sm:block ${active || done ? "text-white" : "text-slate-400"}`}>{label}</span>
    </div>
  );
}

function PField({ path, label, value, onChange, provided, list, optional }) {
  const empty = !value;
  return (
    <label className="block">
      <span className="text-[11px] uppercase tracking-widest text-slate-400">
        {label}{list ? " (comma separated)" : ""}
        {provided && <span className="text-emerald-300"> · from account</span>}
        {!provided && empty && !optional && <span className="text-amber-300"> · required</span>}
      </span>
      <input data-testid={`verify-field-${path.replace(/\./g, "-")}`}
        className="w-full mt-1 bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-sm outline-none focus:border-cyan-400/40"
        value={value || ""} onChange={(e) => onChange(path, e.target.value)} />
    </label>
  );
}

function CheckResult({ ok, title, lines }) {
  return (
    <div className={`rounded-xl border p-3 mt-3 text-sm ${ok ? "bg-emerald-500/10 border-emerald-400/30" : "bg-amber-500/10 border-amber-400/30"}`} data-testid="verify-check-result">
      <div className="flex items-center gap-2 font-semibold">
        {ok ? <CheckCircle size={16} className="text-emerald-300" weight="fill" /> : <WarningCircle size={16} className="text-amber-300" weight="fill" />}
        {title}
      </div>
      {(lines || []).length > 0 && (
        <ul className="mt-1.5 ml-5 list-disc text-slate-300 space-y-0.5">
          {lines.map((l, i) => <li key={i}>{l}</li>)}
        </ul>
      )}
    </div>
  );
}

export default function VerifyBuyer() {
  const { isAuthed, loading, fbUser, account } = useAuth();
  const navigate = useNavigate();
  const [state, setState] = useState(null);
  const [step, setStep] = useState(0);
  const [busy, setBusy] = useState("");
  const [err, setErr] = useState("");

  const [form, setForm] = useState({});
  const [role, setRole] = useState("");
  const [selfie, setSelfie] = useState(null);       // {file_id, url, analysis}
  const [doc, setDoc] = useState(null);             // {file_id, url, analysis}
  const [docType, setDocType] = useState("");
  const [docCatalog, setDocCatalog] = useState({});
  const [consent, setConsent] = useState(false);
  const [weeklyOptIn, setWeeklyOptIn] = useState(true);
  const [result, setResult] = useState(null);
  const [cameraFor, setCameraFor] = useState(null); // 'selfie' | 'document'
  const seededRef = useRef(false);
  const [provided, setProvided] = useState({});     // fields already on the profile at load

  const refresh = useCallback(async () => {
    const s = await getVerifyState();
    setState(s);
    setRole(s?.profile?.role || "");
    if (!seededRef.current && s?.profile) {
      const p = s.profile;
      const cd = p.company_details || {};
      const seed = {
        name: p.name || p.full_name || "",
        country: p.country || "",
        state: p.state || p.province || "",
        city: p.city || "",
        products: Array.isArray(p.products) ? p.products.join(", ") : (p.products || ""),
        "company_details.company_name": cd.company_name || cd.name || "",
        "company_details.company_email": cd.company_email || "",
        "company_details.company_phone": cd.company_phone || "",
        "company_details.address": cd.address || "",
      };
      setForm(seed);
      // Track which values arrived pre-filled (so the UI can show "provided" vs "needs completion").
      const prov = {};
      Object.entries(seed).forEach(([k, v]) => { if (v) prov[k] = true; });
      setProvided(prov);
      seededRef.current = true;
    }
    return s;
  }, []);

  useEffect(() => {
    if (loading) return;
    if (!isAuthed) { navigate("/login?next=/verify"); return; }
    refresh().catch(() => setErr("Could not load your profile. Please retry."));
  }, [isAuthed, loading, refresh, navigate]);

  useEffect(() => {
    const country = state?.profile?.country;
    getVerifyDocuments(country).then((d) => setDocCatalog(d || {})).catch(() => {});
  }, [state?.profile?.country]);

  const missing = state?.completion?.missing || [];
  const status = state?.verification_status || "unverified";
  const onField = (path, val) => setForm((f) => ({ ...f, [path]: val }));
  const stateOptions = useMemo(() => statesFor(form.country), [form.country]);
  const onCountry = (e) => {
    const c = e.target.value;
    // Reset the dependent state when the country changes.
    setForm((f) => ({ ...f, country: c, state: "" }));
  };

  const docOptions = useMemo(() => {
    const arrs = [docCatalog?.business_documents, docCatalog?.trade_documents, docCatalog?.personal_documents];
    const out = [];
    arrs.forEach((a) => (a || []).forEach((d) => {
      const label = typeof d === "string" ? d : (d.label || d.name || d.key || "");
      if (label) out.push(label);
    }));
    return out;
  }, [docCatalog]);

  const saveProfile = async () => {
    setErr("");
    if (!role) { setErr("Please select your trade role to continue."); return; }
    setBusy("profile");
    try {
      const patch = buildPatch(form, state?.profile);  // only the fields the user actually filled
      if (Object.keys(patch).length) { await updateVerifyProfile(patch); await refresh(); }
      setStep(1);  // role is persisted at submit — step progression is decoupled from writes
    } catch (e) { setErr("Could not save your details. Please retry."); }
    setBusy("");
  };

  const handleUpload = async (file, kind) => {
    setErr(""); setBusy(kind);
    try {
      const up = await verifyUpload(file, kind);
      if (kind === "selfie") {
        const analysis = await analyzeSelfie(up.id);
        setSelfie({ ...up, analysis });
      } else {
        const analysis = await analyzeDocument(up.id, docType);
        setDoc({ ...up, analysis });
      }
    } catch (e) { setErr("Upload/analysis failed. Please try a clearer photo."); }
    setBusy("");
  };

  const submit = async () => {
    setErr(""); setBusy("submit");
    const rv = role || state?.profile?.role || "Importer";
    const roleValue = rv.toLowerCase().includes("both") ? "both" : rv.split(" ")[0].toLowerCase();
    try {
      const r = await submitVerification({
        role: roleValue,
        consent,
        selfie_file_id: selfie?.id,
        document_file_id: doc?.id || null,
        doc_type: docType || null,
        notify_opt_in: weeklyOptIn,
        profile_patch: {},
      });
      setResult(r);
      await refresh();
      setStep(4);
    } catch (e) {
      setErr(e?.response?.data?.detail || "Submission failed. Please retry.");
    }
    setBusy("");
  };

  if (loading || (!state && !err)) {
    return <div className="min-h-[60vh] grid place-items-center text-slate-400"><CircleNotch size={22} className="animate-spin" /></div>;
  }

  // Already verified → celebration state.
  if (status === "verified" && step !== 4) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-14 text-center">
        <SEO title="Verified Member · Vametra AI" description="Your Vametra AI Verified Buyer status." path="/verify" />
        <div className="w-16 h-16 mx-auto rounded-full bg-emerald-500/20 border border-emerald-400/40 grid place-items-center mb-4">
          <SealCheck size={30} className="text-emerald-300" weight="fill" />
        </div>
        <h1 className="font-display font-extrabold text-3xl">You're a Verified Member</h1>
        <p className="text-slate-300 mt-2">Your identity and business are verified. You're now listed as a Verified Buyer on Vametra AI.</p>
        <div className="mt-4 flex justify-center"><VerifiedBadge status="verified" size="lg" /></div>
        {state?.geid && <p className="text-xs text-slate-500 mt-3">Buyer ID: <span className="font-mono text-slate-300">{state.geid}</span></p>}
        <div className="mt-6 flex gap-3 justify-center">
          <Link to="/account" className="btn-ghost" data-testid="verify-go-account">Back to account</Link>
          <Link to="/buyers" className="btn-primary" data-testid="verify-go-buyers">Explore Verified Buyers</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
      <SEO title="Get Verified · Vametra AI" description="Complete your profile and become a Verified Buyer on Vametra AI." path="/verify" />

      <div className="text-center mb-6">
        <div className="w-12 h-12 mx-auto rounded-2xl bg-gradient-to-br from-cyan-500 to-violet-600 grid place-items-center mb-3">
          <ShieldCheck size={24} weight="fill" />
        </div>
        <h1 className="font-display font-extrabold text-3xl sm:text-4xl">Become a Verified Buyer</h1>
        <p className="text-slate-300 mt-2 max-w-xl mx-auto text-sm">
          Complete your business profile, verify your identity with a live selfie and a business document, and get the <span className="text-emerald-300">Verified Member</span> badge.
        </p>
        {status !== "unverified" && <div className="mt-3 flex justify-center"><VerifiedBadge status={status} /></div>}
      </div>

      {/* Stepper */}
      <div className="glass rounded-2xl p-4 flex items-center justify-between gap-2 mb-5">
        <Step n={0} active={step === 0} done={step > 0} label="Profile" Icon={IdentificationCard} />
        <div className="flex-1 h-px bg-white/10" />
        <Step n={1} active={step === 1} done={step > 1} label="Selfie" Icon={Camera} />
        <div className="flex-1 h-px bg-white/10" />
        <Step n={2} active={step === 2} done={step > 2} label="Document" Icon={FileText} />
        <div className="flex-1 h-px bg-white/10" />
        <Step n={3} active={step === 3} done={step > 3} label="Submit" Icon={SealCheck} />
      </div>

      {err && <div className="rounded-xl border border-rose-400/30 bg-rose-500/10 text-rose-200 text-sm px-4 py-3 mb-4" data-testid="verify-error">{err}</div>}

      <div className="glass-strong rounded-3xl p-6 sm:p-8">
        {/* STEP 0 — Profile completion */}
        {step === 0 && (
          <div data-testid="verify-step-profile">
            <div className="flex items-center justify-between mb-1">
              <h2 className="font-display font-bold text-lg">Complete your business profile</h2>
              <span className="text-xs text-slate-400">{state?.completion?.percent ?? 0}% complete</span>
            </div>
            <div className="h-1.5 rounded-full bg-white/10 overflow-hidden mb-5">
              <div className="h-full bg-gradient-to-r from-cyan-400 to-emerald-400" style={{ width: `${state?.completion?.percent ?? 0}%` }} />
            </div>

            {/* From your account — pre-filled at signup, no need to re-enter */}
            <div className="rounded-xl border border-white/10 bg-white/5 p-4 mb-5" data-testid="verify-prefill-summary">
              <div className="text-[11px] uppercase tracking-widest text-slate-400 mb-2.5 flex items-center gap-2">
                <CheckCircle size={13} className="text-emerald-300" weight="fill" /> From your account
              </div>
              <div className="grid sm:grid-cols-3 gap-3 text-sm">
                <div>
                  <div className="text-slate-500 text-[11px] uppercase tracking-wider">Email</div>
                  <div className="text-slate-200 truncate" data-testid="verify-prefill-email">{state?.profile?.email || account?.user?.email || fbUser?.email || "—"}</div>
                </div>
                <div>
                  <div className="text-slate-500 text-[11px] uppercase tracking-wider">Mobile</div>
                  <div className="text-slate-200" data-testid="verify-prefill-mobile">{state?.profile?.mobile || state?.profile?.mobile_number || account?.user?.mobile || fbUser?.phoneNumber || "—"}</div>
                </div>
                <div>
                  <div className="text-slate-500 text-[11px] uppercase tracking-wider">Category</div>
                  <div className="text-slate-200" data-testid="verify-prefill-category">{role || state?.profile?.role || account?.user?.user_role || "—"}</div>
                </div>
              </div>
            </div>

            <div className="text-[11px] uppercase tracking-widest text-slate-400 mb-3">Complete the remaining details</div>
            <div className="grid sm:grid-cols-2 gap-4">
              {/* Trade role / user category */}
              <label className="block">
                <span className="text-[11px] uppercase tracking-widest text-slate-400">Trade role / category{role ? "" : <span className="text-amber-300"> · required</span>}</span>
                <select data-testid="verify-field-role" value={role} onChange={(e) => setRole(e.target.value)}
                  className="w-full mt-1 bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-sm outline-none focus:border-cyan-400/40">
                  <option value="">Select role…</option>
                  {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
                </select>
              </label>

              {/* Full name */}
              <PField path="name" label="Full name" value={form.name} onChange={onField} provided={provided.name} />

              {/* Country dropdown */}
              <label className="block">
                <span className="text-[11px] uppercase tracking-widest text-slate-400">
                  Country{form.country ? "" : <span className="text-amber-300"> · required</span>}
                </span>
                <select data-testid="verify-field-country" value={form.country || ""} onChange={onCountry}
                  className="w-full mt-1 bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-sm outline-none focus:border-cyan-400/40">
                  <option value="">Select country…</option>
                  {COUNTRIES.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </label>

              {/* State — dependent dropdown, free-text fallback */}
              <label className="block">
                <span className="text-[11px] uppercase tracking-widest text-slate-400">
                  State / Province{form.state ? "" : <span className="text-amber-300"> · required</span>}
                </span>
                {stateOptions.length > 0 ? (
                  <select data-testid="verify-field-state" value={form.state || ""} onChange={(e) => onField("state", e.target.value)}
                    className="w-full mt-1 bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-sm outline-none focus:border-cyan-400/40">
                    <option value="">Select state / province…</option>
                    {stateOptions.map((s) => <option key={s} value={s}>{s}</option>)}
                  </select>
                ) : (
                  <input data-testid="verify-field-state" value={form.state || ""} onChange={(e) => onField("state", e.target.value)}
                    placeholder={form.country ? "Enter state / province" : "Select a country first"}
                    className="w-full mt-1 bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-sm outline-none focus:border-cyan-400/40" />
                )}
              </label>

              {/* City */}
              <PField path="city" label="City" value={form.city} onChange={onField} provided={provided.city} />

              {/* Products */}
              <PField path="products" label="Products you trade" value={form.products} onChange={onField} provided={provided.products} list />

              {/* Company details */}
              <PField path="company_details.company_name" label="Company name" value={form["company_details.company_name"]} onChange={onField} provided={provided["company_details.company_name"]} />
              <PField path="company_details.company_email" label="Company email" value={form["company_details.company_email"]} onChange={onField} provided={provided["company_details.company_email"]} />
              <PField path="company_details.company_phone" label="Company contact number" value={form["company_details.company_phone"]} onChange={onField} provided={provided["company_details.company_phone"]} />
              <PField path="company_details.address" label="Company address (optional)" value={form["company_details.address"]} onChange={onField} provided={provided["company_details.address"]} optional />
            </div>

            {missing.length === 0 && (
              <p className="text-sm text-emerald-300 mt-4 flex items-center gap-2" data-testid="verify-profile-complete"><CheckCircle size={16} weight="fill" /> Your profile is complete.</p>
            )}

            <button data-testid="verify-save-profile" onClick={saveProfile} disabled={busy === "profile"}
              className="btn-primary mt-6 w-full justify-center">
              {busy === "profile" ? <CircleNotch size={16} className="animate-spin" /> : <>Save &amp; continue <ArrowRight size={15} /></>}
            </button>
          </div>
        )}

        {/* STEP 1 — Selfie */}
        {step === 1 && (
          <div data-testid="verify-step-selfie">
            <h2 className="font-display font-bold text-lg mb-1">Verify it's really you</h2>
            <p className="text-sm text-slate-400 mb-4">Take a clear, well-lit selfie. We check for a real, live person and screen out AI-generated or duplicate photos.</p>

            {selfie?.url && <img src={`${process.env.REACT_APP_BACKEND_URL}${selfie.url}`} alt="selfie preview" className="w-28 h-28 rounded-2xl object-cover mb-3 border border-white/10" data-testid="verify-selfie-preview" />}

            <div className="flex flex-wrap gap-3">
              <label className="btn-ghost cursor-pointer inline-flex" data-testid="verify-selfie-input-label">
                <UploadSimple size={16} /> {selfie ? "Upload another" : "Upload photo"}
                <input type="file" accept="image/*" className="hidden" data-testid="verify-selfie-input"
                  onChange={(e) => e.target.files?.[0] && handleUpload(e.target.files[0], "selfie")} />
              </label>
              <button type="button" onClick={() => setCameraFor("selfie")} className="btn-ghost inline-flex" data-testid="verify-selfie-camera">
                <Camera size={16} /> {selfie ? "Retake with camera" : "Use camera"}
              </button>
            </div>
            {busy === "selfie" && <VerifyWait />}

            {selfie?.analysis && (
              <CheckResult ok={selfie.analysis.passed}
                title={selfie.analysis.passed ? "Selfie looks good" : "Selfie needs attention"}
                lines={[
                  selfie.analysis.duplicate_face ? "This face is already registered to another account." : null,
                  selfie.analysis.is_human_face === false ? "No clear human face detected." : null,
                  (selfie.analysis.ai_generated_likelihood > 0.35) ? "Possible AI-generated / edited image." : null,
                  ...(selfie.analysis.reasons || []).slice(0, 2),
                ].filter(Boolean)} />
            )}

            <div className="flex gap-3 mt-6">
              <button onClick={() => setStep(0)} className="btn-ghost" data-testid="verify-selfie-back">Back</button>
              <button data-testid="verify-selfie-continue" onClick={() => setStep(2)} disabled={!selfie}
                className="btn-primary flex-1 justify-center">Continue <ArrowRight size={15} /></button>
            </div>
          </div>
        )}

        {/* STEP 2 — Document */}
        {step === 2 && (
          <div data-testid="verify-step-document">
            <h2 className="font-display font-bold text-lg mb-1">Verify your business</h2>
            <p className="text-sm text-slate-400 mb-4">Upload one official business document (e.g. GST / IEC / incorporation / trade license). We read and check it automatically.</p>

            <label className="block mb-3">
              <span className="text-[11px] uppercase tracking-widest text-slate-400">Document type</span>
              <select data-testid="verify-doc-type" value={docType} onChange={(e) => setDocType(e.target.value)}
                className="w-full mt-1 bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-sm outline-none focus:border-cyan-400/40">
                <option value="">Select document…</option>
                {docOptions.map((o) => <option key={o} value={o}>{o}</option>)}
                <option value="Other business document">Other business document</option>
              </select>
            </label>

            {doc?.url && <div className="text-xs text-slate-400 mb-2 flex items-center gap-2" data-testid="verify-doc-name"><FileText size={14} /> {doc.filename}</div>}

            <div className="flex flex-wrap gap-3">
              <label className="btn-ghost cursor-pointer inline-flex" data-testid="verify-doc-input-label">
                <UploadSimple size={16} /> {doc ? "Replace document" : "Upload document"}
                <input type="file" accept="image/*,application/pdf" className="hidden" data-testid="verify-doc-input"
                  onChange={(e) => e.target.files?.[0] && handleUpload(e.target.files[0], "document")} />
              </label>
              {IS_MOBILE && (
                <button type="button" onClick={() => setCameraFor("document")} className="btn-ghost inline-flex" data-testid="verify-doc-camera">
                  <Camera size={16} /> Use camera
                </button>
              )}
            </div>
            {!IS_MOBILE && <p className="text-[11px] text-slate-500 mt-2" data-testid="verify-doc-camera-note">Tip: open Vametra AI on your phone to snap the document with your camera.</p>}
            {busy === "document" && <VerifyWait label="reading and verifying your document" />}

            {doc?.analysis && (
              <CheckResult ok={doc.analysis.passed}
                title={doc.analysis.passed ? `Document read: ${doc.analysis.document_type || "business document"}` : "Document needs a clearer photo"}
                lines={[
                  doc.analysis.company_name ? `Company: ${doc.analysis.company_name}` : null,
                  doc.analysis.registration_number ? `Reg. no: ${doc.analysis.registration_number}` : null,
                  doc.analysis.tamper_signs ? "Possible tampering detected." : null,
                ].filter(Boolean)} />
            )}

            <div className="flex gap-3 mt-6">
              <button onClick={() => setStep(1)} className="btn-ghost" data-testid="verify-doc-back">Back</button>
              <button data-testid="verify-doc-continue" onClick={() => setStep(3)}
                className="btn-primary flex-1 justify-center">Continue <ArrowRight size={15} /></button>
            </div>
            <button onClick={() => setStep(3)} className="text-xs text-slate-400 hover:text-slate-200 mt-3 underline" data-testid="verify-doc-skip">Skip for now (goes to manual review)</button>
          </div>
        )}

        {/* STEP 3 — Consent + submit */}
        {step === 3 && (
          <div data-testid="verify-step-submit">
            <h2 className="font-display font-bold text-lg mb-1">Consent &amp; submit</h2>
            <p className="text-sm text-slate-400 mb-4">Review and confirm to be listed as a Verified Buyer.</p>

            <div className="rounded-xl border border-white/10 bg-white/5 p-4 text-sm space-y-2">
              <div className="flex items-center gap-2"><Buildings size={16} className="text-cyan-300" /> {state?.profile?.company_details?.company_name || state?.profile?.company_details?.name || state?.profile?.name || "—"}</div>
              <div className="text-slate-400">Role: {role || state?.profile?.role || "—"} · Country: {state?.profile?.country || "—"}</div>
              <div className="flex items-center gap-3 text-xs text-slate-400">
                <span className={selfie ? "text-emerald-300" : ""}>{selfie ? "✓ Selfie added" : "○ No selfie"}</span>
                <span className={doc ? "text-emerald-300" : ""}>{doc ? "✓ Document added" : "○ No document"}</span>
              </div>
            </div>

            <label className="flex items-start gap-3 mt-4 text-sm cursor-pointer" data-testid="verify-consent-label">
              <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)}
                className="mt-1 accent-cyan-400" data-testid="verify-consent-checkbox" />
              <span className="text-slate-300">I confirm the information is accurate and I consent to being listed as a Verified Buyer on Vametra AI, with my business contact details shown to active subscribers.</span>
            </label>

            <label className="flex items-start gap-3 mt-3 text-sm cursor-pointer" data-testid="verify-optin-label">
              <input type="checkbox" checked={weeklyOptIn} onChange={(e) => setWeeklyOptIn(e.target.checked)}
                className="mt-1 accent-cyan-400" data-testid="verify-optin-checkbox" />
              <span className="text-slate-300">Email me a weekly account-status summary and Verified Buyer updates. <span className="text-slate-500">(You can turn this off anytime.)</span></span>
            </label>

            <div className="flex gap-3 mt-6">
              <button onClick={() => setStep(2)} className="btn-ghost" data-testid="verify-submit-back">Back</button>
              <button data-testid="verify-submit-btn" onClick={submit} disabled={!consent || !selfie || busy === "submit"}
                className="btn-primary flex-1 justify-center">
                {busy === "submit" ? <CircleNotch size={16} className="animate-spin" /> : <>Submit for verification <SealCheck size={15} /></>}
              </button>
            </div>
            {busy === "submit" && <VerifyWait label="verifying your identity and business" />}
          </div>
        )}

        {/* STEP 4 — Result */}
        {step === 4 && result && (
          <div className="text-center" data-testid="verify-step-result">
            {result.status === "verified" ? (
              <>
                <div className="w-16 h-16 mx-auto rounded-full bg-emerald-500/20 border border-emerald-400/40 grid place-items-center mb-3"><SealCheck size={30} className="text-emerald-300" weight="fill" /></div>
                <h2 className="font-display font-extrabold text-2xl">Verified! 🎉</h2>
                <p className="text-slate-300 mt-2">Your identity and business passed our checks. You're now a Verified Buyer.</p>
              </>
            ) : result.status === "rejected" ? (
              <>
                <div className="w-16 h-16 mx-auto rounded-full bg-rose-500/20 border border-rose-400/40 grid place-items-center mb-3"><WarningCircle size={30} className="text-rose-300" weight="fill" /></div>
                <h2 className="font-display font-extrabold text-2xl">We couldn't verify this</h2>
                <p className="text-slate-300 mt-2">{(result.reasons || []).join(" ") || "Please try again with a clearer live selfie and a valid business document."}</p>
                <button onClick={() => { setResult(null); setSelfie(null); setDoc(null); setConsent(false); setStep(1); }} className="btn-primary mt-5" data-testid="verify-retry">Try again</button>
              </>
            ) : (
              <>
                <div className="w-16 h-16 mx-auto rounded-full bg-amber-500/20 border border-amber-400/40 grid place-items-center mb-3"><SealCheck size={30} className="text-amber-300" weight="fill" /></div>
                <h2 className="font-display font-extrabold text-2xl">Submitted for review</h2>
                <p className="text-slate-300 mt-2">Thanks! Our team is reviewing your submission and you'll get the Verified Member badge once approved (usually within 24–48h).</p>
              </>
            )}
            <div className="mt-4 flex justify-center"><VerifiedBadge status={result.status} size="lg" /></div>
            <Link to="/account" className="btn-ghost mt-6 inline-flex" data-testid="verify-result-account">Back to account</Link>
          </div>
        )}

        {cameraFor && (
          <CameraCapture
            facingMode={cameraFor === "selfie" ? "user" : "environment"}
            onCapture={(file) => { const k = cameraFor; setCameraFor(null); handleUpload(file, k); }}
            onClose={() => setCameraFor(null)}
          />
        )}
      </div>
    </div>
  );
}
