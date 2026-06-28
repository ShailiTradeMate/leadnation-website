import axios from "axios";
import { API } from "@/lib/api";

const KEY = "ln_admin_jwt";

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
  if (t) cfg.headers["Authorization"] = `Bearer ${t}`;
  return cfg;
});

export async function adminLogin(username, password) {
  const { data } = await adminApi.post("/auth/admin/login", { username, password });
  setAdminToken(data.token);
  return data;
}
