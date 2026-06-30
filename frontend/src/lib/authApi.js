import axios from "axios";

// Shared identity backend (same DB + Firebase as the mobile app).
// The website is a PURE CLIENT — it owns no identity/database logic.
const AUTH_BASE = process.env.REACT_APP_AUTH_API_BASE;

export const authApi = axios.create({
  baseURL: AUTH_BASE,
  timeout: 30000,
});

// Attach the current Firebase ID token (if signed in) to every request.
authApi.interceptors.request.use(async (config) => {
  try {
    const { auth } = await import("@/lib/firebase");
    const u = auth.currentUser;
    if (u) {
      const token = await u.getIdToken();
      config.headers.Authorization = `Bearer ${token}`;
    }
  } catch (_) { /* unauthenticated */ }
  return config;
});
