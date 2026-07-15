/**
 * charts.js — Inicialización y actualización de todas las gráficas Chart.js.
 */

// ─── PALETA ─────────────────────────────────────────────────────
const C = {
  mauve:  "#DBABBE",
  peach:  "#EDBBB4",
  dusty:  "#BAA1A7",
  slate:  "#797B84",
  bg:     "#EDD2E0",
  white:  "#FFFFFF",
};

const PALETTE = [C.mauve, C.peach, C.dusty, C.slate, C.bg,
                 "#c7949e", "#e8a89d", "#a88a95", "#6b6d76", "#d4b8c8"];

Chart.defaults.font.family = "'Inter', 'Segoe UI', sans-serif";
Chart.defaults.color = C.slate;
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.legend.labels.pointStyleWidth = 10;

const instances = {};

function destroyIfExists(id) {
  if (instances[id]) { instances[id].destroy(); delete instances[id]; }
}

// ─── HELPERS ────────────────────────────────────────────────────
function barChart(id, labels, data, label, color = C.mauve, horizontal = false) {
  destroyIfExists(id);
  const ctx = document.getElementById(id);
  if (!ctx) return;
  instances[id] = new Chart(ctx, {
    type: "bar",
    data: { labels, datasets: [{ label, data, backgroundColor: color, borderRadius: 6 }] },
    options: {
      indexAxis: horizontal ? "y" : "x",
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: "rgba(186,161,167,0.15)" }, ticks: { font: { size: 11 } } },
        y: { grid: { color: "rgba(186,161,167,0.15)" }, ticks: { font: { size: 11 } } },
      },
    },
  });
}

function pieChart(id, labels, data, title = "") {
  destroyIfExists(id);
  const ctx = document.getElementById(id);
  if (!ctx) return;
  instances[id] = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: PALETTE.slice(0, data.length),
        borderWidth: 2,
        borderColor: C.white,
        hoverOffset: 6,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "62%",
      plugins: {
        legend: { position: "right", labels: { font: { size: 11 }, padding: 12 } },
        title: title ? { display: true, text: title, font: { size: 12 } } : { display: false },
      },
    },
  });
}

function lineChart(id, labels, datasets) {
  destroyIfExists(id);
  const ctx = document.getElementById(id);
  if (!ctx) return;
  instances[id] = new Chart(ctx, {
    type: "line",
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "top" } },
      scales: {
        x: { grid: { color: "rgba(186,161,167,0.15)" } },
        y: { grid: { color: "rgba(186,161,167,0.15)" }, beginAtZero: true },
      },
    },
  });
}

function horizontalBarMulti(id, labels, datasets) {
  destroyIfExists(id);
  const ctx = document.getElementById(id);
  if (!ctx) return;
  instances[id] = new Chart(ctx, {
    type: "bar",
    data: { labels, datasets },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "top" } },
      scales: {
        x: { stacked: false, grid: { color: "rgba(186,161,167,0.15)" }, ticks: { font: { size: 11 } } },
        y: { stacked: false, grid: { display: false }, ticks: { font: { size: 10 } } },
      },
    },
  });
}

// ─── SECCIÓN 1: WORKFORCE ────────────────────────────────────────
export function renderWorkforceCharts(deptBreakdown, demographics, tenureByDept) {
  // Headcount por departamento
  barChart(
    "chart-dept-headcount",
    deptBreakdown.map(d => d.Department),
    deptBreakdown.map(d => d.active),
    "Empleados activos",
    C.mauve,
  );

  // Distribución de género (doughnut)
  const gender = demographics.gender;
  pieChart("chart-gender", Object.keys(gender), Object.values(gender));

  // Distribución salarial
  const salary = demographics.salary_distribution;
  barChart(
    "chart-salary",
    Object.keys(salary),
    Object.values(salary),
    "Empleados",
    C.peach,
  );

  // Antigüedad promedio por departamento
  barChart(
    "chart-tenure-dept",
    tenureByDept.map(d => d.Department),
    tenureByDept.map(d => d.avg_tenure_years),
    "Años promedio",
    C.dusty,
    true,
  );
}

// ─── SECCIÓN 2: RETENCIÓN ────────────────────────────────────────
export function renderRetentionCharts(reasons, deptTurnover, trend, bySource) {
  // Top razones de terminación
  barChart(
    "chart-term-reasons",
    reasons.map(r => r.reason),
    reasons.map(r => r.count),
    "Empleados",
    C.slate,
    true,
  );

  // Rotación por departamento
  barChart(
    "chart-dept-turnover",
    deptTurnover.map(d => d.Department),
    deptTurnover.map(d => d.turnover_rate),
    "% Rotación",
    C.mauve,
  );

  // Tendencia contrataciones vs terminaciones
  lineChart("chart-trend", trend.map(t => t.year), [
    {
      label: "Contrataciones",
      data: trend.map(t => t.hires),
      borderColor: C.mauve,
      backgroundColor: "rgba(219,171,190,0.15)",
      tension: 0.3,
      fill: true,
    },
    {
      label: "Terminaciones",
      data: trend.map(t => t.terminations),
      borderColor: C.slate,
      backgroundColor: "rgba(121,123,132,0.1)",
      tension: 0.3,
      fill: true,
    },
  ]);

  // Rotación por fuente de reclutamiento
  horizontalBarMulti("chart-source-turnover",
    bySource.map(s => s.RecruitmentSource),
    [
      {
        label: "Total contratados",
        data: bySource.map(s => s.total),
        backgroundColor: C.peach,
        borderRadius: 4,
      },
      {
        label: "Terminados",
        data: bySource.map(s => s.terminated),
        backgroundColor: C.slate,
        borderRadius: 4,
      },
    ],
  );
}

// ─── SECCIÓN 3: RIESGO ML ────────────────────────────────────────
export function renderRiskDistribution(dist) {
  pieChart(
    "chart-risk-dist",
    ["Alto", "Medio", "Bajo"],
    [dist.Alto, dist.Medio, dist.Bajo],
  );
  // Override colors para riesgo
  if (instances["chart-risk-dist"]) {
    instances["chart-risk-dist"].data.datasets[0].backgroundColor = [
      C.slate, C.dusty, C.peach,
    ];
    instances["chart-risk-dist"].update();
  }
}

export function renderFeatureImportance(features) {
  barChart(
    "chart-feature-importance",
    features.map(f => f.feature.replace(/_/g, " ")),
    features.map(f => f.importance),
    "Importancia",
    C.mauve,
    true,
  );
}
