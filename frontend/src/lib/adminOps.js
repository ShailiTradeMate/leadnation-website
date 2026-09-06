import { staffApi } from "@/lib/staffAuth";

export const adminOps = {
  permissions: () => staffApi.get("/admin/permissions").then((r) => r.data),
  review: (uid, payload) => staffApi.post(`/admin/users/${uid}/review`, payload).then((r) => r.data),
  signoffQueue: () => staffApi.get("/admin/signoff").then((r) => r.data),
  signoff: (uid, payload) => staffApi.post(`/admin/users/${uid}/signoff`, payload).then((r) => r.data),
  editProfile: (uid, patch) => staffApi.patch(`/admin/users/${uid}/profile`, { patch }).then((r) => r.data),
  notes: (uid) => staffApi.get(`/admin/users/${uid}/notes`).then((r) => r.data),
  addNote: (uid, payload) => staffApi.post(`/admin/users/${uid}/notes`, payload).then((r) => r.data),
  payments: (uid) => staffApi.get(`/admin/users/${uid}/payments`).then((r) => r.data),
  subscription: (uid, payload) => staffApi.post(`/admin/users/${uid}/subscription`, payload).then((r) => r.data),
  remove: (uid, payload) => staffApi.post(`/admin/users/${uid}/delete`, payload).then((r) => r.data),
  activity: (uid) => staffApi.get(`/admin/users/${uid}/activity`).then((r) => r.data),
  uploadDocument: (uid, file, kind, label) => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("kind", kind);
    fd.append("label", label || "");
    return staffApi.post(`/admin/users/${uid}/documents`, fd, {
      headers: { "Content-Type": "multipart/form-data" },
    }).then((r) => r.data);
  },
};

export const errText = (e, fallback = "Something went wrong.") =>
  e?.response?.data?.detail || e?.message || fallback;
