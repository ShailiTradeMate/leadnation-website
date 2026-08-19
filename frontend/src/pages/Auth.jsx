import React, { useState } from "react";
import { Link, useNavigate, Navigate } from "react-router-dom";
import { useAuth } from "@/lib/AuthContext";
import { GoogleLogo, CircleNotch, SignOut, CheckCircle, WarningCircle } from "@phosphor-icons/react";
import SEO from "@/components/SEO";
import { trackEvent, EVENTS } from "@/lib/analytics";
import { COUNTRY_CODES, CC_BY_ISO, toE164 } from "@/lib/countryCodes";

const BUSINESS_ROLES = [
  ["exporter", "Exporter"], ["importer", "Importer"], ["supplier", "Supplier"],
  ["cha", "Customs House Agent (CHA)"], ["export_agent", "Export Agent"], ["consultant", "Consultant"],
];

const Shell = ({ title, sub, children }) => (
  <section className="min-h-[80vh] grid place-items-center px-6 py-20">
    <div className="glass-strong rounded-3xl p-8 w-full max-w-md">
      <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300">Vametra AI Account</div>
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

function phoneErr(e) {
  const c = e?.code || "";
  if (c === "phone/disabled") return "Mobile sign-in isn't live yet — please use Email / Customer ID or Google.";
  if (c === "phone/format") return "Enter your number in international format, e.g. +919812345678.";
  if (c === "phone/no-session") return "Your code session expired — please request a new code.";
  if (c.includes("invalid-verification-code")) return "That code is incorrect. Please re-check and try again.";
  if (c.includes("code-expired")) return "This code expired — request a new one.";
  if (c.includes("too-many-requests")) return "Too many attempts — please wait a little and try again.";
  if (c.includes("quota") || c.includes("billing")) return "SMS is temporarily unavailable. Please use Email / Customer ID or Google.";
  return "Mobile sign-in failed. Please try again or use Email / Customer ID.";
}

export function Login() {
  const { login, loginWithCustomerId, google, isAuthed, phoneLoginEnabled, startPhoneLogin, confirmPhoneOtp } = useAuth();
  const [mode, setMode] = useState("credentials"); // "credentials" | "mobile"
  const [ident, setIdent] = useState("");
  const [pw, setPw] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);
  // mobile-login state
  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState("");
  const [otpSent, setOtpSent] = useState(false);
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

  const sendPhone = async (e) => {
    e.preventDefault(); setErr(""); setLoading(true);
    try {
      const num = phone.trim();
      if (!/^\+[1-9]\d{6,14}$/.test(num)) throw Object.assign(new Error("bad"), { code: "phone/format" });
      await startPhoneLogin(num); setOtpSent(true);
    } catch (e2) { setErr(phoneErr(e2)); }
    finally { setLoading(false); }
  };
  const verifyPhone = async (e) => {
    e.preventDefault(); setErr(""); setLoading(true);
    try { await confirmPhoneOtp(otp.trim()); trackEvent(EVENTS.USER_LOGIN, { method: "phone" }); navigate("/account"); }
    catch (e2) { setErr(phoneErr(e2)); }
    finally { setLoading(false); }
  };

  const TabBtn = ({ id, label }) => (
    <button type="button" data-testid={`login-tab-${id}`} onClick={() => { setMode(id); setErr(""); }}
      className={`flex-1 py-2 rounded-xl text-sm font-medium transition-all ${mode === id ? "tab-active text-white" : "text-slate-400 hover:text-white"}`}>{label}</button>
  );

  return (
    <Shell title="Sign in" sub="Use the same account as the Vametra AI app.">
      <SEO title="Sign in · Vametra AI" description="Sign in to your Vametra AI account." path="/login" />
      <div className="flex gap-1 glass rounded-2xl p-1 mt-4" data-testid="login-tabs">
        <TabBtn id="credentials" label="Email / Customer ID" />
        <TabBtn id="mobile" label="Mobile number" />
      </div>

      {mode === "credentials" && (
        <>
          <form onSubmit={submit} data-testid="login-form" className="mt-2">
            <input data-testid="login-identifier" autoFocus className={inp} value={ident} onChange={(e) => setIdent(e.target.value)} placeholder="Email or Customer ID (e.g. 00006)" />
            <input data-testid="login-password" type="password" className={inp} value={pw} onChange={(e) => setPw(e.target.value)} placeholder="Password" />
            {err && <div data-testid="login-error" className="text-rose-300 text-sm mt-2">{err}</div>}
            <button data-testid="login-submit" disabled={loading} className="btn-primary w-full justify-center mt-4 disabled:opacity-50">{loading ? <CircleNotch size={16} className="animate-spin" /> : "Sign in"}</button>
          </form>
          <button data-testid="login-google" onClick={onGoogle} disabled={loading} className="btn-ghost w-full justify-center mt-3 gap-2"><GoogleLogo size={18} weight="bold" /> Continue with Google</button>
        </>
      )}

      {mode === "mobile" && (
        <div className="mt-2" data-testid="login-mobile-panel">
          {!phoneLoginEnabled ? (
            <div data-testid="login-phone-note" className="glass rounded-xl p-4 text-sm text-slate-300 mt-2">
              📱 Mobile-number sign-in is launching soon. For now, please use <button type="button" className="text-cyan-300 hover:underline" onClick={() => setMode("credentials")}>Email / Customer ID</button> or Google.
            </div>
          ) : !otpSent ? (
            <form onSubmit={sendPhone} data-testid="login-phone-send-form">
              <input data-testid="login-phone-input" autoFocus className={inp} value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="Mobile number (e.g. +9198…)" />
              {err && <div data-testid="login-error" className="text-rose-300 text-sm mt-2">{err}</div>}
              <button data-testid="login-phone-send" disabled={loading} className="btn-primary w-full justify-center mt-4 disabled:opacity-50">{loading ? <CircleNotch size={16} className="animate-spin" /> : "Send code"}</button>
            </form>
          ) : (
            <form onSubmit={verifyPhone} data-testid="login-phone-verify-form">
              <input data-testid="login-phone-otp" autoFocus className={inp} value={otp} onChange={(e) => setOtp(e.target.value)} placeholder="Enter the 6-digit code" />
              {err && <div data-testid="login-error" className="text-rose-300 text-sm mt-2">{err}</div>}
              <button data-testid="login-phone-verify" disabled={loading} className="btn-primary w-full justify-center mt-4 disabled:opacity-50">{loading ? <CircleNotch size={16} className="animate-spin" /> : "Verify & sign in"}</button>
              <button type="button" data-testid="login-phone-restart" onClick={() => { setOtpSent(false); setOtp(""); setErr(""); }} className="text-xs text-cyan-300 hover:underline mt-3">Use a different number</button>
            </form>
          )}
        </div>
      )}

      <div id="recaptcha-container" />
      <div className="flex justify-between text-sm mt-5 text-slate-400">
        <Link to="/forgot-password" className="hover:text-cyan-300" data-testid="login-forgot-link">Forgot password?</Link>
        <Link to="/signup" className="hover:text-cyan-300" data-testid="login-signup-link">Create account</Link>
      </div>
    </Shell>
  );
}

export function Signup() {
  const { signup, google, register, isAuthed } = useAuth();
  const [form, setForm] = useState({ full_name: "", email: "", password: "", role: "exporter", mobile_number: "", countryIso: "IN" });
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  if (isAuthed) return <Navigate to="/account" replace />;
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  const sel = CC_BY_ISO[form.countryIso] || CC_BY_ISO.IN;
  const mobileE164 = toE164(sel.dial, form.mobile_number); // "" when left blank (optional)

  const submit = async (e) => {
    e.preventDefault(); setErr(""); setLoading(true);
    try {
      await signup(form.email.trim(), form.password);
      // mobile is OPTIONAL and stored in E.164 in the shared users record (both keys for app compatibility).
      await register({ full_name: form.full_name, role: form.role, mobile_number: mobileE164, mobile: mobileE164, provider: "password", country: sel.name });
      trackEvent(EVENTS.USER_REGISTERED, { method: "password", role: form.role, country: sel.name });
      navigate("/account");
    } catch (e2) {
      setErr(e2?.code === "auth/email-already-in-use" ? "This email is already registered — try signing in." : "Sign-up failed. Use a valid email and a 6+ character password.");
    } finally { setLoading(false); }
  };
  const onGoogle = async () => {
    setErr(""); setLoading(true);
    try { await google(); await register({ role: form.role, mobile_number: mobileE164, mobile: mobileE164, country: sel.name, provider: "google" }); trackEvent(EVENTS.USER_REGISTERED, { method: "google", role: form.role }); navigate("/account"); }
    catch (e) { setErr(googleErr(e)); } finally { setLoading(false); }
  };

  return (
    <Shell title="Create your account" sub="One login for the Vametra AI website and mobile app.">
      <SEO title="Create account · Vametra AI" description="Join Vametra AI — global trade intelligence." path="/signup" />
      <form onSubmit={submit} data-testid="signup-form">
        <input data-testid="signup-name" autoFocus className={inp} value={form.full_name} onChange={(e) => set("full_name", e.target.value)} placeholder="Full name" />
        <input data-testid="signup-email" type="email" className={inp} value={form.email} onChange={(e) => set("email", e.target.value)} placeholder="Email" />
        <input data-testid="signup-password" type="password" className={inp} value={form.password} onChange={(e) => set("password", e.target.value)} placeholder="Password (min 6 characters)" />
        <div className="flex gap-2 mt-3">
          <select data-testid="signup-dial" aria-label="Country code" value={form.countryIso} onChange={(e) => set("countryIso", e.target.value)}
            className="glass rounded-xl px-3 py-3 outline-none w-36 shrink-0">
            {COUNTRY_CODES.map((c) => <option key={c.iso} value={c.iso}>{c.flag} {c.dial}</option>)}
          </select>
          <input data-testid="signup-mobile" type="tel" inputMode="tel" className="flex-1 glass rounded-xl px-4 py-3 outline-none" value={form.mobile_number} onChange={(e) => set("mobile_number", e.target.value)} placeholder="Mobile number (optional)" />
        </div>
        <p data-testid="signup-mobile-note" className="text-[11px] text-slate-500 mt-1.5">Your mobile number will be used for faster login and account recovery when Phone Login becomes available.</p>
        {mobileE164 && <p data-testid="signup-mobile-preview" className="text-[11px] text-cyan-300/80 mt-1">Saved as {mobileE164}</p>}
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
      <SEO title="Reset password · Vametra AI" description="Reset your Vametra AI password." path="/forgot-password" />
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
    <Shell title="My Account" sub="Shared with the Vametra AI mobile app.">
      <SEO title="My Account · Vametra AI" description="Your Vametra AI account." path="/account" />
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
