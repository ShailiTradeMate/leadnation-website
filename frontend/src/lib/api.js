import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

export const api = axios.create({
  baseURL: API,
  timeout: 30000,
});

// Attach the current Firebase ID token (if signed in) to every request.
api.interceptors.request.use(async (config) => {
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

export const fetchCountries = () => api.get("/countries").then((r) => r.data);
export const fetchBusinessTypes = () => api.get("/business-types").then((r) => r.data);
export const fetchTradeDirections = () => api.get("/trade-directions").then((r) => r.data);
export const fetchProducts = () => api.get("/products").then((r) => r.data);
export const fetchTradeNews = () => api.get("/trade-news").then((r) => r.data);
export const fetchNewsFeed = (params = {}) => api.get("/news/feed", { params }).then((r) => r.data);
export const fetchNewsDetail = (id) => api.get(`/news/${id}`).then((r) => r.data);
export const fetchExpos = () => api.get("/expos").then((r) => r.data);
export const fetchEvents = (params = {}) => api.get("/events/list", { params }).then((r) => r.data);
export const fetchEventFilters = () => api.get("/events/filters").then((r) => r.data);
export const fetchEventPricing = (params = {}) => api.get("/events/pricing", { params }).then((r) => r.data);
export const fetchEventDetail = (id) => api.get(`/events/${id}`).then((r) => r.data);
export const submitEvent = (payload) => api.post("/events/submit", payload).then((r) => r.data);
export const uploadFile = (formData) =>
  api.post("/storage/upload", formData, { headers: { "Content-Type": "multipart/form-data" }, timeout: 120000 }).then((r) => r.data);
export const fetchIndiaFeatures = () => api.get("/india-features").then((r) => r.data);
export const fetchCustoms = (country, direction) =>
  api.get(`/customs-compliance`, { params: { country, direction } }).then((r) => r.data);
export const postProductInfo = (payload) => api.post(`/product-info`, payload).then((r) => r.data);
export const searchAll = (q) => api.get(`/search`, { params: { q } }).then((r) => r.data);
export const createLead = (payload) => api.post(`/leads`, payload).then((r) => r.data);
