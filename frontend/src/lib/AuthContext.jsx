import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from "react";
import {
  signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut,
  GoogleAuthProvider, signInWithPopup, sendPasswordResetEmail, sendEmailVerification,
  onIdTokenChanged, setPersistence, browserLocalPersistence,
  RecaptchaVerifier, signInWithPhoneNumber,
} from "firebase/auth";
import { auth } from "@/lib/firebase";
import { authApi } from "@/lib/authApi";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

const googleProvider = new GoogleAuthProvider();

// GUARDED: mobile-number (Phone OTP) login stays OFF until Firebase Blaze is
// enabled (real SMS requires billing). Flip REACT_APP_ENABLE_PHONE_LOGIN="true"
// and restart the frontend to activate — no code change needed. Identity/backend
// ownership is unchanged: phone sign-in uses the SAME shared Firebase + uid, and
// the existing self-heal allocates the 5-digit Customer ID via the DO backend.
const PHONE_LOGIN_ENABLED = process.env.REACT_APP_ENABLE_PHONE_LOGIN === "true";

export function AuthProvider({ children }) {
  const [fbUser, setFbUser] = useState(null);
  const [account, setAccount] = useState(null); // { onboarded, user, profile }
  const [loading, setLoading] = useState(true);
  const [activationError, setActivationError] = useState(false); // DO /onboarding/register failed → no Customer ID
  const seqRef = useRef(0);
  const healRef = useRef("");   // uid we've already attempted to self-heal this session
  const recaptchaRef = useRef(null);   // invisible reCAPTCHA (phone login)
  const phoneConfirmRef = useRef(null); // pending signInWithPhoneNumber confirmation

  useEffect(() => { setPersistence(auth, browserLocalPersistence).catch(() => {}); }, []);

  // Build the account from the SHARED backend profile (no local /auth/me).
  // Last-write-wins guard: concurrent refreshes (onIdTokenChanged vs post-register)
  // must not let a stale (pre-allocation) response overwrite a newer one.
  const refreshAccount = useCallback(async () => {
    const my = ++seqRef.current;
    try {
      const u = auth.currentUser;
      if (!u) { if (my === seqRef.current) setAccount(null); return null; }
      let { data: profile } = await authApi.get(`/v1/profiles/${u.uid}`);
      // SELF-HEAL: a Firebase user with no DO profile (returns the `legacy_hydrate`
      // placeholder with customer_id:null) is "half-registered" — the /onboarding/register
      // step never completed. Complete it once so the 5-digit Customer ID is allocated
      // and mobile-app login (which authenticates via the same DO backend) works.
      const needsHeal = !profile?.customer_id;
      if (needsHeal && healRef.current !== u.uid) {
        healRef.current = u.uid;
        let healed = false;
        for (let attempt = 0; attempt < 3 && !healed; attempt++) {
          if (attempt) await new Promise((r) => setTimeout(r, 800 * attempt)); // backoff
          try {
            await authApi.post("/onboarding/register", {
              full_name: u.displayName || "",
              role: "exporter",
              provider: u.providerData?.[0]?.providerId?.includes("google") ? "google" : "password",
            });
            const re = await authApi.get(`/v1/profiles/${u.uid}`);
            if (re?.data?.customer_id) { profile = re.data; healed = true; }
          } catch (_) { /* retry */ }
        }
        setActivationError(!healed);
      } else if (profile?.customer_id) {
        setActivationError(false);
      }
      const isAdminRole = profile?.role === "admin";
      const acct = {
        onboarded: !!profile?.customer_id,
        user: {
          uid: u.uid,
          customer_id: profile?.customer_id || "",
          email: profile?.email || u.email || "",
          full_name: profile?.name || "",
          user_role: isAdminRole ? "admin" : "",
          role: isAdminRole ? "admin" : "user",
          verification_status: profile?.verification_status || "pending",
          is_email_verified: u.emailVerified,
        },
        profile,
      };
      if (my === seqRef.current) {
        // Don't let the DO profiles endpoint's eventually-consistent placeholder
        // (no customer_id right after signup) clobber a known-good account.
        // profiles.role is the PLATFORM role (user/admin) — it does NOT carry the
        // business role, so preserve user_role from the prior (register) state.
        setAccount((prev) => {
          if (!acct.user.customer_id && prev?.user?.customer_id) return prev;
          return {
            ...acct,
            onboarded: !!(acct.user.customer_id || prev?.user?.customer_id),
            user: {
              ...acct.user,
              customer_id: acct.user.customer_id || prev?.user?.customer_id || "",
              full_name: acct.user.full_name || prev?.user?.full_name || "",
              user_role: isAdminRole ? "admin" : (prev?.user?.user_role || ""),
            },
          };
        });
      }
      return acct;
    } catch (_) { return null; }
  }, []);

  useEffect(() => {
    return onIdTokenChanged(auth, async (u) => {
      setFbUser(u || null);
      if (u) await refreshAccount(); else setAccount(null);
      setLoading(false);
    });
  }, [refreshAccount]);

  // Resolve a Customer ID (00001…) → email, then sign in.
  const loginWithCustomerId = async (customerId, password) => {
    const { data } = await authApi.post("/auth/resolve-customer-id", { customer_id: customerId });
    return signInWithEmailAndPassword(auth, data.email, password);
  };

  // ---- Mobile-number (Phone OTP) login — GUARDED by PHONE_LOGIN_ENABLED ----
  // Step 1: send OTP to an E.164 number via Firebase Phone Auth (invisible reCAPTCHA).
  const startPhoneLogin = async (e164) => {
    if (!PHONE_LOGIN_ENABLED) { const e = new Error("phone-login-disabled"); e.code = "phone/disabled"; throw e; }
    if (!recaptchaRef.current) {
      recaptchaRef.current = new RecaptchaVerifier(auth, "recaptcha-container", { size: "invisible" });
    }
    phoneConfirmRef.current = await signInWithPhoneNumber(auth, e164, recaptchaRef.current);
    return true;
  };
  // Step 2: confirm the OTP → signs in on the SAME shared Firebase (uid).
  // onIdTokenChanged → refreshAccount() self-heals to allocate the Customer ID via DO backend.
  const confirmPhoneOtp = async (code) => {
    if (!phoneConfirmRef.current) { const e = new Error("no-otp-session"); e.code = "phone/no-session"; throw e; }
    const cred = await phoneConfirmRef.current.confirm(code);
    await refreshAccount();
    return cred;
  };

  const value = {
    fbUser, account, loading,
    isAuthed: !!fbUser,
    isAdmin: account?.user?.role === "admin",
    activationError,
    retryActivation: async () => { healRef.current = ""; setActivationError(false); return refreshAccount(); },
    phoneLoginEnabled: PHONE_LOGIN_ENABLED,
    startPhoneLogin,
    confirmPhoneOtp,
    refreshAccount,
    login: (email, pw) => signInWithEmailAndPassword(auth, email, pw),
    loginWithCustomerId,
    signup: async (email, pw) => {
      const cred = await createUserWithEmailAndPassword(auth, email, pw);
      try { await sendEmailVerification(cred.user); } catch (_) {}
      return cred;
    },
    register: async (body) => {
      const { data: d } = await authApi.post("/onboarding/register", body);
      const u = auth.currentUser;
      // Optimistically reflect the freshly-allocated Customer ID — the DO profiles
      // endpoint is eventually-consistent and lags a few seconds after register.
      if (u && d?.customer_id) {
        const isAdminRole = d.role === "admin";
        setAccount({
          onboarded: true,
          user: {
            uid: u.uid,
            customer_id: d.customer_id,
            email: u.email || "",
            full_name: body.full_name || "",
            user_role: isAdminRole ? "admin" : (body.role || ""),
            role: isAdminRole ? "admin" : "user",
            verification_status: d.verification_status || "pending",
            is_email_verified: u.emailVerified,
          },
          profile: { uid: u.uid, customer_id: d.customer_id, name: body.full_name || "",
                     email: u.email || "", role: body.role || "", verification_status: d.verification_status || "pending" },
        });
      }
      refreshAccount();
      return d;
    },
    google: async () => { const cred = await signInWithPopup(auth, googleProvider); return cred; },
    resetPassword: (email) => sendPasswordResetEmail(auth, email),
    resendVerification: () => (auth.currentUser ? sendEmailVerification(auth.currentUser) : Promise.reject()),
    requestOtp: () => authApi.post("/auth/send-otp", { type: "email", value: auth.currentUser?.email }).then((r) => r.data),
    verifyOtp: (otp) => authApi.post("/auth/verify-otp", { type: "email", value: auth.currentUser?.email, otp }).then(async (r) => {
      try {
        if (auth.currentUser) { await auth.currentUser.getIdToken(true); await auth.currentUser.reload(); setFbUser(auth.currentUser); }
      } catch (_) {}
      await refreshAccount();
      return r.data;
    }),
    logout: () => {
      try { recaptchaRef.current?.clear?.(); } catch (_) {}
      recaptchaRef.current = null; phoneConfirmRef.current = null;
      return signOut(auth);
    },
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
