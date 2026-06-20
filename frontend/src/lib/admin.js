import axios from "axios";
import { API } from "@/lib/api";

const KEY = "ln_admin_token";

export function getAdminToken() {
  try { return localStorage.getItem(KEY) || ""; } catch (_) { return ""; }
}
export function setAdminToken(t) {
  try { if (t) localStorage.setItem(KEY, t); else localStorage.removeItem(KEY); } catch (_) {}
}
export function isAdminLoggedIn() {
  return Boolean(getAdminToken());
}

export const adminApi = axios.create({ baseURL: API, timeout: 15000 });
adminApi.interceptors.request.use((cfg) => {
  const t = getAdminToken();
  if (t) cfg.headers["X-Admin-Token"] = t;
  return cfg;
});

export async function adminLogin(token) {
  const { data } = await adminApi.post("/admin/login", { token });
  setAdminToken(token);
  return data;
}
