import { api } from "@/lib/api";

// VBIE — Verified Buyer Intelligence Engine. All buyer data is served by the
// single Global Trade Intelligence Server (website backend) and shared web+app.
export const fetchBuyerMeta = () => api.get("/buyers/meta").then((r) => r.data);
export const searchBuyers = (params = {}) => api.get("/buyers/search", { params }).then((r) => r.data);
export const fetchBuyer = (geid) => api.get(`/buyers/${geid}`).then((r) => r.data);
export const fetchBuyerEvidence = (geid) => api.get(`/buyers/${geid}/evidence`).then((r) => r.data);
export const claimBuyer = (geid, payload) => api.post(`/buyers/${geid}/claim`, payload).then((r) => r.data);
export const fetchBuyerSources = () => api.get("/buyers/sources").then((r) => r.data);

export const TRUST_COLORS = {
  emerald: "bg-emerald-500/15 text-emerald-300 border-emerald-400/30",
  cyan: "bg-cyan-500/15 text-cyan-300 border-cyan-400/30",
  amber: "bg-amber-500/15 text-amber-300 border-amber-400/30",
  slate: "bg-slate-500/15 text-slate-300 border-slate-400/30",
};
