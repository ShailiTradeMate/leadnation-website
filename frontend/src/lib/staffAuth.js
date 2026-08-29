import axios from "axios";
import { API } from "@/lib/api";

// Website-local sub-admin (staff) session — coexists with the Firebase main admin.
const STAFF_KEY = "vametra_staff_jwt";
const STAFF_INFO = "vametra_staff_info";

export function getStaffToken() {
  try { return localStorage.getItem(STAFF_KEY) || ""; } catch (_) { return ""; }
}
export function getStaffInfo() {
  try { return JSON.parse(localStorage.getItem(STAFF_INFO) || "null"); } catch (_) { return null; }
}
export function isStaff() { return Boolean(getStaffToken()); }
export function staffLogout() {
  try { localStorage.removeItem(STAFF_KEY); localStorage.removeItem(STAFF_INFO); } catch (_) {}
}

export async function staffLogin(identifier, password) {
  const { data } = await axios.post(`${API}/admin-auth/login`, { identifier, password });
  localStorage.setItem(STAFF_KEY, data.token);
  localStorage.setItem(STAFF_INFO, JSON.stringify(data.subadmin || {}));
  return data;
}

// Axios instance for the admin User Section — attaches EITHER the Firebase
// main-admin token OR the sub-admin JWT (X-Staff-Token), whichever is present.
export const staffApi = axios.create({ baseURL: API, timeout: 30000 });
staffApi.interceptors.request.use(async (config) => {
  try {
    const { auth } = await import("@/lib/firebase");
    const u = auth.currentUser;
    if (u) {
      config.headers.Authorization = `Bearer ${await u.getIdToken()}`;
      return config;
    }
  } catch (_) { /* not a Firebase session */ }
  const t = getStaffToken();
  if (t) config.headers["X-Staff-Token"] = t;
  return config;
});
