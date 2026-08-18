import { api } from "@/lib/api";

// Verified Buyer Completion + Verification.
// The website is a CLIENT of the shared DO identity backend — these endpoints
// proxy profile reads/writes to DO and run the reference verification pipeline.
export const getVerifyState = () => api.get("/verify/state").then((r) => r.data);
export const getVerifyDocuments = (country) =>
  api.get("/verify/documents", { params: country ? { country } : {} }).then((r) => r.data);
export const updateVerifyProfile = (patch) =>
  api.put("/verify/profile", { patch }).then((r) => r.data);

export const verifyUpload = (file, kind) => {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("kind", kind);
  return api.post("/verify/upload", fd, {
    headers: { "Content-Type": "multipart/form-data" }, timeout: 120000,
  }).then((r) => r.data);
};

export const analyzeSelfie = (file_id) =>
  api.post("/verify/analyze-selfie", { file_id }, { timeout: 90000 }).then((r) => r.data);
export const analyzeDocument = (file_id, doc_type) =>
  api.post("/verify/analyze-document", { file_id, doc_type }, { timeout: 90000 }).then((r) => r.data);
export const submitVerification = (payload) =>
  api.post("/verify/submit", payload, { timeout: 120000 }).then((r) => r.data);

// Admin human-review queue.
export const getVerifyQueue = (status = "needs_review") =>
  api.get("/verify/admin/queue", { params: { status } }).then((r) => r.data);
export const decideVerification = (sid, decision, note) =>
  api.post(`/verify/admin/${sid}/decide`, { decision, note }).then((r) => r.data);
