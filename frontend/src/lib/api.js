import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

export const api = axios.create({
  baseURL: API,
  timeout: 15000,
});

export const fetchCountries = () => api.get("/countries").then((r) => r.data);
export const fetchBusinessTypes = () => api.get("/business-types").then((r) => r.data);
export const fetchTradeDirections = () => api.get("/trade-directions").then((r) => r.data);
export const fetchProducts = () => api.get("/products").then((r) => r.data);
export const fetchTradeNews = () => api.get("/trade-news").then((r) => r.data);
export const fetchExpos = () => api.get("/expos").then((r) => r.data);
export const fetchIndiaFeatures = () => api.get("/india-features").then((r) => r.data);
export const fetchCustoms = (country, direction) =>
  api.get(`/customs-compliance`, { params: { country, direction } }).then((r) => r.data);
export const postProductInfo = (payload) => api.post(`/product-info`, payload).then((r) => r.data);
export const searchAll = (q) => api.get(`/search`, { params: { q } }).then((r) => r.data);
export const createLead = (payload) => api.post(`/leads`, payload).then((r) => r.data);
