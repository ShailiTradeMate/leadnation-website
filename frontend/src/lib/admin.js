import { api } from "@/lib/api";
import { auth } from "@/lib/firebase";

// Admin now uses the SHARED Firebase identity. The api instance already attaches
// the Firebase ID token; admin authorisation is enforced server-side (users.role).
export const adminApi = api;

export function isAdminLoggedIn() {
  return Boolean(auth.currentUser);
}

export async function getAdminToken() {
  try { return auth.currentUser ? await auth.currentUser.getIdToken() : ""; }
  catch (_) { return ""; }
}
