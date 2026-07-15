/**
 * dashboard.js — Orquestación principal del dashboard.
 * Carga datos de la API, coordina navegación y renderiza secciones.
 */

import { api } from "./api.js";
import {
  renderWorkforceCharts,
  renderRetentionCharts,
  renderRiskDistribution,
  renderFeatureImportance,
} from "./charts.js";

// ─── ESTADO ─────────────────────────────────────────────────────
let anonymized = false;
let riskEmployees = [];

// ─── NAVEGACIÓN ─────────────────────────────────────────────────
function switchSection(id) {
  document.querySelectorAll(".section").forEach(s => s.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
  document.getElementById(`section-${id}`)?.classList.add("active");
  document.getElementById(`nav-${id}`)?.classList.add("active");
}

// ─── LOADER ─────────────────────────────────────────────────────
function showLoader(msg = "Cargando datos...") {
  const el = document.getElementById("loader");
  if (el) { el.querySelector("p").textContent = msg; el.style.display = "flex"; }
}

function hideLoader() {
  const el = document.getElementById("loader");
  if (el) el.style.display = "none";
}

// ─── HELPERS ────────────────────────────────────────────────────
function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function fmtNum(n) { return Number(n).toLocaleString("es-PE"); }
function fmtPct(n) { return `${n}%`; }
function fmtSol(n) { return `S/ ${fmtNum(n)}`; }

// ─── SECCIÓN 1: WORKFORCE ────────────────────────────────────────
async function loadWorkforce() {
  const [summary, deptBreakdown, demographics, tenureByDept] = await Promise.all([
    api.workforce.summary(),
    api.workforce.departmentBreakdown(),
    api.workforce.demographics(),
    api.workforce.tenureByDept(),
  ]);

  // KPIs
  setText("kpi-total",      fmtNum(summary.total_employees));
  setText("kpi-active",     fmtNum(summary.active_employees));
  setText("kpi-salary",     fmtSol(summary.avg_salary_active));
  setText("kpi-turnover",   fmtPct(summary.turnover_rate));

  // Gráficas
  renderWorkforceCharts(deptBreakdown, demographics, tenureByDept);
}

// ─── SECCIÓN 2: RETENCIÓN ────────────────────────────────────────
async function loadRetention() {
  const [rate, reasons, byDept, trend, bySource] = await Promise.all([
    api.retention.rate(),
    api.retention.reasons(),
    api.retention.byDepartment(),
    api.retention.trend(),
    api.retention.bySource(),
  ]);

  // KPIs
  setText("kpi-ret-rate",    fmtPct(rate.retention_rate_pct));
  setText("kpi-ret-turnover", fmtPct(rate.turnover_rate_pct));
  setText("kpi-ret-term",    fmtNum(rate.terminated));
  setText("kpi-ret-tenure",  `${rate.avg_tenure_before_leaving_years} años`);

  // Gráficas
  renderRetentionCharts(reasons, byDept, trend, bySource);
}

// ─── SECCIÓN 3: RIESGO ML ────────────────────────────────────────
async function loadRisk() {
  const [dist, metrics, features, employees] = await Promise.all([
    api.risk.distribution(),
    api.risk.modelMetrics(),
    api.risk.featureImportance(),
    api.risk.employees(anonymized),
  ]);

  riskEmployees = employees;

  // Mejor modelo
  setText("best-model-name", metrics.best_model);

  // Métricas del mejor modelo
  const best = metrics.results[metrics.best_model];
  setText("metric-auc",      (best.roc_auc * 100).toFixed(1) + "%");
  setText("metric-f1",       (best.f1 * 100).toFixed(1) + "%");
  setText("metric-acc",      (best.accuracy * 100).toFixed(1) + "%");

  // Otros modelos (tabla comparativa)
  const tableBody = document.getElementById("models-table-body");
  if (tableBody) {
    tableBody.innerHTML = Object.entries(metrics.results)
      .sort(([, a], [, b]) => b.roc_auc - a.roc_auc)
      .map(([name, m]) => `
        <tr class="${name === metrics.best_model ? 'best-row' : ''}">
          <td>${name}</td>
          <td>${(m.roc_auc * 100).toFixed(1)}%</td>
          <td>${(m.f1 * 100).toFixed(1)}%</td>
          <td>${(m.accuracy * 100).toFixed(1)}%</td>
        </tr>`)
      .join("");
  }

  // Gráficas
  renderRiskDistribution(dist);
  renderFeatureImportance(features.slice(0, 10));

  // Tabla de empleados
  renderEmployeeTable(employees);
}

function renderEmployeeTable(employees) {
  const tbody = document.getElementById("risk-table-body");
  if (!tbody) return;
  tbody.innerHTML = employees.slice(0, 20).map(emp => {
    const badgeClass = { Alto: "badge-alto", Medio: "badge-medio", Bajo: "badge-bajo" }[emp.risk_label] || "badge-bajo";
    return `
      <tr>
        <td>${emp.Employee_Name}</td>
        <td>${emp.Department}</td>
        <td>${emp.Position}</td>
        <td>
          <div class="score-bar-wrapper">
            <div class="score-bar">
              <div class="score-bar-fill" style="width:${emp.risk_score}%"></div>
            </div>
            <span class="score-text">${emp.risk_score}%</span>
          </div>
        </td>
        <td><span class="badge ${badgeClass}">${emp.risk_label}</span></td>
        <td>${emp.Absences}</td>
      </tr>`;
  }).join("");
}

// ─── TOGGLE ANONIMIZAR ───────────────────────────────────────────
async function toggleAnonymize() {
  anonymized = !anonymized;
  const btn = document.getElementById("btn-anon");
  if (btn) btn.textContent = anonymized ? "👤 Mostrar nombres" : "🙈 Anonimizar";

  const employees = await api.risk.employees(anonymized);
  riskEmployees = employees;
  renderEmployeeTable(employees);
}

// ─── INIT ────────────────────────────────────────────────────────
async function init() {
  showLoader("Iniciando dashboard y modelo ML... (puede tardar ~30s en Render)");

  try {
    // Cargar las 3 secciones en paralelo
    await Promise.all([
      loadWorkforce(),
      loadRetention(),
      loadRisk(),
    ]);
  } catch (err) {
    console.error("Error cargando datos:", err);
    hideLoader();
    alert("Error conectando con el servidor. Verifica que la API esté corriendo.");
    return;
  }

  hideLoader();
  switchSection("workforce"); // Sección inicial

  // Navegación
  document.querySelectorAll(".nav-item[data-section]").forEach(btn => {
    btn.addEventListener("click", () => switchSection(btn.dataset.section));
  });

  // Botón anonimizar
  document.getElementById("btn-anon")?.addEventListener("click", toggleAnonymize);
}

document.addEventListener("DOMContentLoaded", init);
