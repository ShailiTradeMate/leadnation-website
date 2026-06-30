import React, { createContext, useContext, useState, useEffect, useRef, useCallback } from "react";
import { api } from "@/lib/api";

const ProjectCtx = createContext(null);
export const useProject = () => useContext(ProjectCtx);

const SESSION_KEY = "ln_trade_session";
function getSession() {
  let s = localStorage.getItem(SESSION_KEY);
  if (!s) { s = (crypto?.randomUUID?.() || `g-${Date.now()}-${Math.random().toString(36).slice(2)}`); localStorage.setItem(SESSION_KEY, s); }
  return s;
}

const num = (v) => (v === "" || v == null ? 0 : parseFloat(v) || 0);
const coreHash = (p) => p ? JSON.stringify([p.hs, p.exporter, p.importer, p.quantity, p.transactionCurrency, p.globalCurrency, p.marginPct, p.costs]) : "";

export function ProjectProvider({ children }) {
  const session = useRef(getSession());
  const [projects, setProjects] = useState([]);
  const [current, setCurrent] = useState(null);
  const [quoteLoading, setQuoteLoading] = useState(false);
  const [insights, setInsights] = useState("");
  const [insightsLoading, setInsightsLoading] = useState(false);
  const hdrs = { headers: { "X-Trade-Session": session.current } };
  const cc = { headers: { "X-Trade-Session": session.current }, timeout: 90000 };
  const saveTimer = useRef(null);
  const recomputeTimer = useRef(null);
  const lastHash = useRef("");
  const curRef = useRef(null);
  useEffect(() => { curRef.current = current; }, [current]);

  const refreshList = useCallback(async () => {
    try { const { data } = await api.get("/projects", hdrs); setProjects(data.projects || []); } catch (_) {}
  }, []);
  useEffect(() => { refreshList(); }, [refreshList]);

  // merge guest projects into account after login
  useEffect(() => {
    const t = setTimeout(async () => {
      try { await api.post("/projects/merge", {}, hdrs); refreshList(); } catch (_) {}
    }, 2500);
    return () => clearTimeout(t);
  }, [refreshList]);

  const createProject = async (body) => {
    const { data } = await api.post("/projects", body, hdrs);
    setCurrent(data); lastHash.current = coreHash(data); setInsights(""); refreshList();
    return data;
  };
  const loadProject = async (id) => {
    const { data } = await api.get(`/projects/${id}`, hdrs);
    setCurrent(data); lastHash.current = coreHash(data); setInsights("");
    return data;
  };
  const deleteProject = async (id) => { await api.delete(`/projects/${id}`, hdrs); if (current?.id === id) setCurrent(null); refreshList(); };
  const pinProject = async (id) => { await api.post(`/projects/${id}/pin`, {}, hdrs); refreshList(); };
  const duplicateProject = async (id) => { const { data } = await api.post(`/projects/${id}/duplicate`, {}, hdrs); refreshList(); return data; };
  const addVersion = async (kind, label, snapshot) => {
    if (!current) return;
    await api.post(`/projects/${current.id}/version`, { kind, label, snapshot }, hdrs);
    loadProject(current.id);
  };

  const persist = useCallback((patch, activity) => {
    if (!current?.id) return;
    clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(async () => {
      try { const { data } = await api.put(`/projects/${current.id}`, { patch, activity }, hdrs);
        setCurrent((c) => (c && c.id === data.id ? { ...data, lastQuote: c.lastQuote ?? data.lastQuote, costs: c.costs ?? data.costs } : c)); refreshList(); } catch (_) {}
    }, 700);
  }, [current, refreshList]);

  // local field update (optimistic) + persist
  const update = useCallback((patch, activity) => {
    setCurrent((c) => (c ? { ...c, ...patch } : c));
    persist(patch, activity);
  }, [persist]);

  // nested cost edit — always merges into the LATEST costs (avoids stale-closure races)
  const patchCosts = useCallback((k, v) => {
    const costs = { ...((curRef.current || {}).costs || {}), [k]: v };
    setCurrent((c) => (c ? { ...c, costs } : c));
    persist({ costs });
  }, [persist]);

  const recompute = useCallback(async (proj) => {
    const p = proj || current;
    if (!p || (!p.hs && !p.product)) return;
    const fobUnit = ["exw", "packing", "inland", "thc", "customsDocs"].reduce((s, k) => s + num((p.costs || {})[k]), 0);
    if (fobUnit <= 0) return;
    setQuoteLoading(true);
    try {
      const { data } = await api.post("/command-center/quote", {
        hs: p.hs, product: p.hs ? "" : p.product, exporter: p.exporter, importer: p.importer,
        quantity: num(p.quantity) || 1, unit: p.unit || "unit",
        costs: Object.fromEntries(["exw", "packing", "inland", "thc", "customsDocs", "freight", "insurance"].map((k) => [k, num((p.costs || {})[k])])),
        marginPct: num(p.marginPct), transactionCurrency: p.transactionCurrency, globalCurrency: p.globalCurrency,
      }, cc);
      if (data.ok) {
        setCurrent((c) => ({ ...c, lastQuote: data }));
        if (p.id) api.put(`/projects/${p.id}`, { patch: { lastQuote: data } }, hdrs)
          .then(({ data: doc }) => { setCurrent((c) => (c && c.id === doc.id ? { ...c, health: doc.health, summary: doc.summary } : c)); refreshList(); })
          .catch(() => {});
        // fetch Brain insights in background
        setInsightsLoading(true); setInsights("");
        api.post("/command-center/insights", { quote: data }, cc)
          .then(({ data: ins }) => { if (ins.ok) setInsights(ins.advisor || ""); })
          .catch(() => {}).finally(() => setInsightsLoading(false));
      }
    } finally { setQuoteLoading(false); }
  }, [current, refreshList]);

  // REACTIVE GRAPH: when core inputs change, debounce-recompute everything
  useEffect(() => {
    if (!current) return;
    const h = coreHash(current);
    if (h === lastHash.current) return;
    lastHash.current = h;
    clearTimeout(recomputeTimer.current);
    recomputeTimer.current = setTimeout(() => recompute(current), 650);
    return () => clearTimeout(recomputeTimer.current);
  }, [current, recompute]);

  return (
    <ProjectCtx.Provider value={{
      session: session.current, projects, current, setCurrent, quoteLoading, insights, insightsLoading,
      refreshList, createProject, loadProject, deleteProject, pinProject, duplicateProject, addVersion,
      update, recompute, hdrs, patchCosts,
    }}>
      {children}
    </ProjectCtx.Provider>
  );
}
