import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from "react";
import {
  signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut,
  GoogleAuthProvider, signInWithPopup, sendPasswordResetEmail, sendEmailVerification,
  onIdTokenChanged, setPersistence, browserLocalPersistence,
} from "firebase/auth";
import { auth } from "@/lib/firebase";
import { authApi } from "@/lib/authApi";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

const googleProvider = new GoogleAuthProvider();

export function AuthProvider({ children }) {
  const [fbUser, setFbUser] = useState(null);
  const [account, setAccount] = useState(null); // { onboarded, user, profile }
  const [loading, setLoading] = useState(true);
  const seqRef = useRef(0);

  useEffect(() => { setPersistence(auth, browserLocalPersistence).catch(() => {}); }, []);

  // Build the account from the SHARED backend profile (no local /auth/me).
  // Last-write-wins guard: concurrent refreshes (onIdTokenChanged vs post-register)
  // must not let a stale (pre-allocation) response overwrite a newer one.
  const refreshAccount = useCallback(async () => {
    const my = ++seqRef.current;
    try {
      const u = auth.currentUser;
      if (!u) { if (my === seqRef.current) setAccount(null); return null; }
      const { data: profile } = await authApi.get(`/v1/profiles/${u.uid}`);
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

  const value = {
    fbUser, account, loading,
    isAuthed: !!fbUser,
    isAdmin: account?.user?.role === "admin",
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
    logout: () => signOut(auth),
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
