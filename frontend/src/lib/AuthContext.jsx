import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
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

  useEffect(() => { setPersistence(auth, browserLocalPersistence).catch(() => {}); }, []);

  // Build the account from the SHARED backend profile (no local /auth/me).
  const refreshAccount = useCallback(async () => {
    try {
      const u = auth.currentUser;
      if (!u) { setAccount(null); return null; }
      const { data: profile } = await authApi.get(`/v1/profiles/${u.uid}`);
      const isAdminRole = profile?.role === "admin";
      const acct = {
        onboarded: !!profile?.customer_id,
        user: {
          uid: u.uid,
          customer_id: profile?.customer_id || "",
          email: profile?.email || u.email || "",
          full_name: profile?.name || "",
          user_role: isAdminRole ? "admin" : (profile?.role || ""),
          role: isAdminRole ? "admin" : "user",
          verification_status: profile?.verification_status || "pending",
          is_email_verified: u.emailVerified,
        },
        profile,
      };
      setAccount(acct);
      return acct;
    } catch (_) { setAccount(null); return null; }
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
    register: (body) => authApi.post("/onboarding/register", body).then((r) => r.data).then((d) => { refreshAccount(); return d; }),
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
