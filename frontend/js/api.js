/**
 * api.js — Wrapper de fetch() para todos los endpoints del backend.
 * Detecta automáticamente la base URL (local vs Render).
 */

const BASE_URL = window.location.origin;

async function apiFetch(endpoint) {
  const res = await fetch(`${BASE_URL}${endpoint}`);
  if (!res.ok) throw new Error(`API error ${res.status}: ${endpoint}`);
  return res.json();
}

// ─── WORKFORCE ──────────────────────────────────────────────────
export const api = {
  workforce: {
    summary:           () => apiFetch("/api/workforce/summary"),
    departmentBreakdown: () => apiFetch("/api/workforce/department-breakdown"),
    demographics:      () => apiFetch("/api/workforce/demographics"),
    tenureByDept:      () => apiFetch("/api/workforce/tenure-by-department"),
  },

  // ─── RETENTION ────────────────────────────────────────────────
  retention: {
    rate:              () => apiFetch("/api/retention/rate"),
    reasons:           () => apiFetch("/api/retention/reasons"),
    byDepartment:      () => apiFetch("/api/retention/by-department"),
    trend:             () => apiFetch("/api/retention/trend"),
    bySource:          () => apiFetch("/api/retention/by-recruitment-source"),
  },

  // ─── ML RISK ──────────────────────────────────────────────────
  risk: {
    employees:         (anonymize = false) =>
                         apiFetch(`/api/risk/employees?anonymize=${anonymize}`),
    distribution:      () => apiFetch("/api/risk/distribution"),
    modelMetrics:      () => apiFetch("/api/risk/model-metrics"),
    featureImportance: () => apiFetch("/api/risk/feature-importance"),
  },
};
