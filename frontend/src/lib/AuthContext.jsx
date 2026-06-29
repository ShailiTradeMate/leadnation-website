import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import {
  signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut,
  GoogleAuthProvider, signInWithPopup, sendPasswordResetEmail, sendEmailVerification,
  onIdTokenChanged, setPersistence, browserLocalPersistence,
} from "firebase/auth";
import { auth } from "@/lib/firebase";
import { api } from "@/lib/api";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

const googleProvider = new GoogleAuthProvider();

export function AuthProvider({ children }) {
  const [fbUser, setFbUser] = useState(null);
  const [account, setAccount] = useState(null); // { onboarded, user, profile }
  const [loading, setLoading] = useState(true);

  useEffect(() => { setPersistence(auth, browserLocalPersistence).catch(() => {}); }, []);

  const refreshAccount = useCallback(async () => {
    try { const { data } = await api.get("/auth/me"); setAccount(data); return data; }
    catch (_) { setAccount(null); return null; }
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
    const { data } = await api.post("/auth/resolve-customer-id", { customer_id: customerId });
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
    register: (body) => api.post("/onboarding/register", body).then((r) => r.data).then((d) => { refreshAccount(); return d; }),
    google: async () => { const cred = await signInWithPopup(auth, googleProvider); return cred; },
    resetPassword: (email) => sendPasswordResetEmail(auth, email),
    resendVerification: () => (auth.currentUser ? sendEmailVerification(auth.currentUser) : Promise.reject()),
    logout: () => signOut(auth),
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
