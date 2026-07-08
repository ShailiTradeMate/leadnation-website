import React, { useState } from "react";
import { Link, useNavigate, Navigate } from "react-router-dom";
import { useAuth } from "@/lib/AuthContext";
import { GoogleLogo, CircleNotch, SignOut, CheckCircle, WarningCircle } from "@phosphor-icons/react";
import SEO from "@/components/SEO";
import { trackEvent, EVENTS } from "@/lib/analytics";

const BUSINESS_ROLES = [
  ["exporter", "Exporter"], ["importer", "Importer"], ["supplier", "Supplier"],
  ["cha", "Customs House Agent (CHA)"], ["export_agent", "Export Agent"], ["consultant", "Consultant"],
];

const Shell = ({ title, sub, children }) => (
  <section className="min-h-[80vh] grid place-items-center px-6 py-20">
    <div className="glass-strong rounded-3xl p-8 w-full max-w-md">
      <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300">LeadNation Account</div>
      <h1 className="font-display font-extrabold text-3xl mt-2">{title}</h1>
      {sub && <p className="text-slate-400 text-sm mt-2">{sub}</p>}
      {children}
    </div>
  </section>
);
const inp = "w-full glass rounded-xl px-4 py-3 outline-none mt-3";

function googleErr(e) {
  const c = e?.code || "";
  if (c.includes("unauthorized-domain")) return "Google sign-in isn't enabled for this domain yet. Please use email/password for now (admin is adding this domain to Firebase).";
  if (c.includes("popup-blocked")) return "Your browser blocked the Google popup — allow popups and try again.";
  if (c.includes("popup-closed") || c.includes("cancelled-popup")) return "Google sign-in was cancelled.";
  return "Google sign-in failed. Please try email/password.";
}

// Password login can fail because the account was created with "Continue with
// Google" (no password). Firebase's Email Enumeration Protection hides which
// provider an email uses, so we can't detect this pre-login — instead we guide
// the user to Google / password reset on the generic invalid-credential error.
function loginErr(e) {
  const c = e?.code || "";
  if (c.includes("too-many-requests")) return "Too many attempts — please wait a minute and try again, or reset your password.";
  if (c.includes("user-disabled")) return "This account has been disabled. Please contact support.";
  if (c.includes("invalid-credential") || c.includes("wrong-password") || c.includes("user-not-found") || c.includes("invalid-login"))
    return "Sign-in failed. If you signed up with Google, use “Continue with Google” below. Otherwise check your email/Customer ID and password, or reset it via “Forgot password?”.";
  return "Login failed — check your email/Customer ID and password.";
}

export function Login() {
  const { login, loginWithCustomerId, google, isAuthed } = useAuth();
  const [ident, setIdent] = useState("");
  const [pw, setPw] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  if (isAuthed) return <Navigate to="/account" replace />;

  const submit = async (e) => {
    e.preventDefault(); setErr(""); setLoading(true);
    try {
      const id = ident.trim();
      if (/^\d{1,6}$/.test(id)) await loginWithCustomerId(id.padStart(5, "0"), pw);
      else await login(id, pw);
      trackEvent(EVENTS.USER_LOGIN, { method: "password" });
      navigate("/account");
    } catch (e) { setErr(loginErr(e)); }
    finally { setLoading(false); }
  };
  const onGoogle = async () => { setErr(""); setLoading(true); try { await google(); trackEvent(EVENTS.USER_LOGIN, { method: "google" }); navigate("/account"); } catch (e) { setErr(googleErr(e)); } finally { setLoading(false); } };

  return (
    <Shell title="Sign in" sub="Use the same account as the LeadNation app.">
      <SEO title="Sign in · LeadNation" description="Sign in to your LeadNation account." path="/login" />
      <form onSubmit={submit} data-testid="login-form">
        <input data-testid="login-identifier" autoFocus className={inp} value={ident} onChange={(e) => setIdent(e.target.value)} placeholder="Email or Customer ID (e.g. 00006)" />
        <input data-testid="login-password" type="password" className={inp} value={pw} onChange={(e) => setPw(e.target.value)} placeholder="Password" />
        {err && <div data-testid="login-error" className="text-rose-300 text-sm mt-2">{err}</div>}
        <button data-testid="login-submit" disabled={loading} className="btn-primary w-full justify-center mt-4 disabled:opacity-50">{loading ? <CircleNotch size={16} className="animate-spin" /> : "Sign in"}</button>
      </form>
      <button data-testid="login-google" onClick={onGoogle} disabled={loading} className="btn-ghost w-full justify-center mt-3 gap-2"><GoogleLogo size={18} weight="bold" /> Continue with Google</button>
      <div className="flex justify-between text-sm mt-5 text-slate-400">
        <Link to="/forgot-password" className="hover:text-cyan-300" data-testid="login-forgot-link">Forgot password?</Link>
        <Link to="/signup" className="hover:text-cyan-300" data-testid="login-signup-link">Create account</Link>
      </div>
    </Shell>
  );
}

export function Signup() {
  const { signup, google, register, isAuthed } = useAuth();
  const [form, setForm] = useState({ full_name: "", email: "", password: "", role: "exporter", mobile_number: "", country: "" });
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  if (isAuthed) return <Navigate to="/account" replace />;
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e) => {
    e.preventDefault(); setErr(""); setLoading(true);
    try {
      await signup(form.email.trim(), form.password);
      await register({ full_name: form.full_name, role: form.role, mobile_number: form.mobile_number, provider: "password", country: form.country });
      trackEvent(EVENTS.USER_REGISTERED, { method: "password", role: form.role, country: form.country });
      navigate("/account");
    } catch (e2) {
      setErr(e2?.code === "auth/email-already-in-use" ? "This email is already registered — try signing in." : "Sign-up failed. Use a valid email and a 6+ character password.");
    } finally { setLoading(false); }
  };
  const onGoogle = async () => {
    setErr(""); setLoading(true);
    try { await google(); await register({ role: form.role, provider: "google" }); trackEvent(EVENTS.USER_REGISTERED, { method: "google", role: form.role }); navigate("/account"); }
    catch (e) { setErr(googleErr(e)); } finally { setLoading(false); }
  };

  return (
    <Shell title="Create your account" sub="One login for the LeadNation website and mobile app.">
      <SEO title="Create account · LeadNation" description="Join LeadNation — global trade intelligence." path="/signup" />
      <form onSubmit={submit} data-testid="signup-form">
        <input data-testid="signup-name" autoFocus className={inp} value={form.full_name} onChange={(e) => set("full_name", e.target.value)} placeholder="Full name" />
        <input data-testid="signup-email" type="email" className={inp} value={form.email} onChange={(e) => set("email", e.target.value)} placeholder="Email" />
        <input data-testid="signup-password" type="password" className={inp} value={form.password} onChange={(e) => set("password", e.target.value)} placeholder="Password (min 6 characters)" />
        <input data-testid="signup-mobile" className={inp} value={form.mobile_number} onChange={(e) => set("mobile_number", e.target.value)} placeholder="Mobile (optional)" />
        <input data-testid="signup-country" className={inp} value={form.country} onChange={(e) => set("country", e.target.value)} placeholder="Country" />
        <select data-testid="signup-role" className={inp} value={form.role} onChange={(e) => set("role", e.target.value)}>
          {BUSINESS_ROLES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
        {err && <div data-testid="signup-error" className="text-rose-300 text-sm mt-2">{err}</div>}
        <button data-testid="signup-submit" disabled={loading} className="btn-primary w-full justify-center mt-4 disabled:opacity-50">{loading ? <CircleNotch size={16} className="animate-spin" /> : "Create account"}</button>
      </form>
      <button data-testid="signup-google" onClick={onGoogle} disabled={loading} className="btn-ghost w-full justify-center mt-3 gap-2"><GoogleLogo size={18} weight="bold" /> Sign up with Google</button>
      <p className="text-[11px] text-slate-500 mt-3 text-center" data-testid="signup-legal">By creating an account you agree to our <Link to="/legal/terms" className="text-cyan-300 hover:underline">Terms</Link> and <Link to="/legal/privacy" className="text-cyan-300 hover:underline">Privacy Policy</Link>.</p>
      <div className="text-sm mt-5 text-slate-400">Already have an account? <Link to="/login" className="hover:text-cyan-300" data-testid="signup-login-link">Sign in</Link></div>
    </Shell>
  );
}

export function ForgotPassword() {
  const { resetPassword } = useAuth();
  const [email, setEmail] = useState("");
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const submit = async (e) => {
    e.preventDefault(); setErr(""); setMsg("");
    try { await resetPassword(email.trim()); setMsg("If that email exists, a reset link is on its way."); }
    catch (_) { setErr("Could not send reset email."); }
  };
  return (
    <Shell title="Reset password" sub="We'll email you a secure reset link.">
      <SEO title="Reset password · LeadNation" description="Reset your LeadNation password." path="/forgot-password" />
      <form onSubmit={submit} data-testid="forgot-form">
        <input data-testid="forgot-email" type="email" autoFocus className={inp} value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" />
        {msg && <div data-testid="forgot-msg" className="text-emerald-300 text-sm mt-2">{msg}</div>}
        {err && <div className="text-rose-300 text-sm mt-2">{err}</div>}
        <button data-testid="forgot-submit" className="btn-primary w-full justify-center mt-4">Send reset link</button>
      </form>
      <div className="text-sm mt-5 text-slate-400"><Link to="/login" className="hover:text-cyan-300">Back to sign in</Link></div>
    </Shell>
  );
}

export function Account() {
  const { account, fbUser, loading, logout, requestOtp, verifyOtp, isAuthed } = useAuth();
  const navigate = useNavigate();
  const [otp, setOtp] = useState("");
  const [vmsg, setVmsg] = useState("");
  const [verifying, setVerifying] = useState(false);
  if (loading) return <Shell title="Loading…" />;
  if (!isAuthed) return <Navigate to="/login" replace />;
  const u = account?.user || {};
  const verified = fbUser?.emailVerified || u.is_email_verified;

  const sendCode = async () => { setVmsg(""); try { const r = await requestOtp(); setVmsg(r.message || "We've emailed you a verification code."); } catch (_) { setVmsg("Could not start verification."); } };
  const doVerify = async () => {
    setVmsg(""); setVerifying(true);
    try { await verifyOtp(otp.trim()); setVmsg("Email verified ✓"); setOtp(""); }
    catch (e) { setVmsg(e?.response?.data?.detail || "Invalid code."); }
    finally { setVerifying(false); }
  };

  return (
    <Shell title="My Account" sub="Shared with the LeadNation mobile app.">
      <SEO title="My Account · LeadNation" description="Your LeadNation account." path="/account" />
      <div className="space-y-3 mt-4" data-testid="account-panel">
        <Row label="Customer ID" value={u.customer_id || "—"} testid="account-customer-id" />
        <Row label="Email" value={u.email || fbUser?.email} />
        <Row label="Name" value={u.full_name || "—"} />
        <Row label="Business role" value={u.user_role || "—"} />
        <Row label="Platform role" value={u.role || "user"} />
        <div className="flex items-center justify-between glass rounded-xl px-4 py-3">
          <span className="text-sm text-slate-400">Email verified</span>
          <span data-testid="account-verified-status" className={`text-sm flex items-center gap-1 ${verified ? "text-emerald-300" : "text-amber-300"}`}>
            {verified ? <><CheckCircle size={15} weight="fill" /> Verified</> : <><WarningCircle size={15} weight="fill" /> Not verified</>}
          </span>
        </div>
        {!verified && (
          <div className="glass rounded-xl p-4 space-y-3" data-testid="account-verify-card">
            <div className="text-sm text-slate-300">Verify your email to unlock everything. Tap <span className="text-cyan-300">Send verification code</span> and enter the code we email you.</div>
            <div className="flex gap-2">
              <input data-testid="account-otp-input" value={otp} onChange={(e) => setOtp(e.target.value)} placeholder="Enter verification code" className="glass rounded-xl px-4 py-2.5 outline-none flex-1" />
              <button data-testid="account-verify-otp" onClick={doVerify} disabled={verifying} className="btn-primary !py-2.5 disabled:opacity-50">{verifying ? <CircleNotch size={15} className="animate-spin" /> : "Verify"}</button>
            </div>
            <button data-testid="account-send-otp" onClick={sendCode} className="text-xs text-cyan-300 hover:underline">Send verification code</button>
          </div>
        )}
        {vmsg && <div data-testid="account-verify-msg" className="text-cyan-300 text-sm">{vmsg}</div>}
        {u.role === "admin" && <button onClick={() => navigate("/admin-cms")} className="btn-ghost w-full justify-center text-sm" data-testid="account-admin-link">Open Admin Console</button>}
        <button data-testid="account-logout" onClick={async () => { await logout(); navigate("/"); }} className="btn-primary w-full justify-center mt-2 gap-2"><SignOut size={16} weight="bold" /> Sign out</button>
      </div>
    </Shell>
  );
}

const Row = ({ label, value, testid }) => (
  <div className="flex items-center justify-between glass rounded-xl px-4 py-3">
    <span className="text-sm text-slate-400">{label}</span>
    <span className="text-sm text-white font-medium" data-testid={testid}>{value}</span>
  </div>
);
