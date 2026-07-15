# 🧠 HR Churn Analytics — Executive Dashboard

> Dashboard ejecutivo de Recursos Humanos con predicción de rotación de personal mediante Machine Learning.

[![Live Demo](https://img.shields.io/badge/🌐_Live_Demo-hr--churn--analytics.onrender.com-DBABBE?style=for-the-badge)](https://hr-churn-analytics.onrender.com)
[![Python](https://img.shields.io/badge/Python-3.11-797B84?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-BAA1A7?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Scikit-learn](https://img.shields.io/badge/scikit--learn-1.4-EDD2E0?style=for-the-badge&logo=scikitlearn&logoColor=797B84)](https://scikit-learn.org)

---

## 🔗 Demo en vivo

**[https://hr-churn-analytics.onrender.com](https://hr-churn-analytics.onrender.com)**

> ⚠️ El servicio corre en el plan gratuito de Render. Si lleva inactivo un rato, el primer acceso puede tardar ~30 segundos en despertar.

---

## 📌 ¿Qué es este proyecto?

Sistema web para el jefe de Recursos Humanos que combina **análisis descriptivo** e **inteligencia predictiva** sobre una fuerza laboral de 311 empleados. Permite tomar decisiones basadas en datos sobre retención de talento, distribución salarial, fuentes de reclutamiento y riesgo individual de rotación.

---

## 🗂️ Dataset

| Atributo | Detalle |
|---|---|
| Fuente | HRDataset v14 (Dr. Rich Huebner & Dr. Carla Patalano) |
| Registros | 311 empleados |
| Variables | 36 columnas (demografía, rendimiento, salario, reclutamiento, asistencia) |
| Target ML | `Termd` — 0 = Activo / 1 = Terminado (33.4% positivos) |

---

## 🖥️ Secciones del Dashboard

### 👥 1. Fuerza Laboral
Vista general del capital humano activo:
- KPIs: total empleados, activos, salario promedio, tasa de rotación global
- Headcount activo por departamento
- Distribución de género
- Distribución salarial por rangos
- Antigüedad promedio por departamento

### 📉 2. Análisis de Retención
Análisis histórico de salidas:
- Tasa de retención vs rotación
- Top 10 razones de terminación
- Rotación por departamento (%)
- Tendencia de contrataciones vs terminaciones por año
- Efectividad por fuente de reclutamiento

### 🤖 3. Panel de Riesgo ML
Predicción individual de rotación:
- Modelo ganador con métricas (ROC-AUC, F1, Accuracy)
- Tabla comparativa de los 4 modelos evaluados
- Distribución de riesgo entre empleados activos (Alto / Medio / Bajo)
- Top 10 features más influyentes
- Ranking de empleados por score de riesgo con toggle de anonimización

---

## 🤖 Pipeline de Machine Learning

Se entrenaron y compararon **4 modelos de clasificación** usando `StratifiedKFold (k=5)`:

| Modelo | ROC-AUC | F1-Score | Accuracy |
|---|---|---|---|
| **Gradient Boosting** ⭐ | **90.4%** | **76.6%** | **84.9%** |
| Logistic Regression | 90.1% | 73.2% | 82.6% |
| XGBoost | 88.8% | 75.4% | 84.3% |
| Random Forest | 89.0% | 68.8% | 81.7% |

**Selección:** Gradient Boosting ganó por ROC-AUC, la métrica más relevante para datos desbalanceados.

### Técnicas aplicadas
- **SMOTE** para balancear el desbalance de clases (~33% positivos)
- **OneHotEncoder** para variables categóricas (departamento, cargo, fuente de reclutamiento, etc.)
- **StandardScaler** para variables numéricas
- **Exclusión de leakage**: `DateofTermination`, `TermReason` y `EmploymentStatus` fueron eliminadas del modelo (solo conocidas post-terminación)
- Umbrales de riesgo por **percentiles relativos** del colectivo activo (Top 25% = Alto)

### Top features de riesgo

```
Tenure_days              ████████████████░░░░  65.2%
RecruitmentSource        ████░░░░░░░░░░░░░░░░   6.6%
Position                 ██░░░░░░░░░░░░░░░░░░   3.9%
Salary                   █░░░░░░░░░░░░░░░░░░░   2.7%
Absences                 █░░░░░░░░░░░░░░░░░░░   2.1%
```

---

## 🏗️ Arquitectura

```
[ HRDataset_v14.csv ]
        ↓
[ FastAPI Backend ]  ←→  [ ML Pipeline (Gradient Boosting) ]
        ↓  REST API (JSON)
[ Frontend HTML/CSS/JS ]  →  Chart.js visualizations
        ↓
[ Render Web Service ]
```

FastAPI sirve tanto la API REST como los archivos estáticos del frontend desde un único servicio. El modelo se entrena automáticamente en el primer arranque si no existe el artefacto `.pkl`.

---

## 🗃️ Estructura del proyecto

```
hr-churn-analytics/
├── app/
│   ├── main.py                  # FastAPI entry point + static files
│   ├── routers/
│   │   ├── workforce.py         # GET /api/workforce/*
│   │   ├── retention.py         # GET /api/retention/*
│   │   └── ml.py                # GET /api/risk/*
│   ├── services/
│   │   ├── data_service.py      # Carga, limpieza y feature engineering
│   │   ├── analytics_service.py # Cálculos de negocio (KPIs, tendencias)
│   │   └── ml_service.py        # Entrenamiento, selección y predicción
│   ├── schemas/
│   │   └── responses.py         # Pydantic schemas
│   └── data/
│       └── HRDataset_v14.csv
├── ml/
│   └── artifacts/               # Modelo .pkl (generado en runtime)
├── frontend/
│   ├── index.html               # Dashboard SPA de 3 secciones
│   ├── css/styles.css           # Paleta de colores personalizada
│   └── js/
│       ├── api.js               # Wrapper fetch() para la API
│       ├── charts.js            # Gráficas Chart.js
│       └── dashboard.js         # Navegación y orquestación
├── render.yaml                  # Configuración de deploy
├── requirements.txt
└── .python-version              # Python 3.11.9
```

---

## 🎨 Paleta de colores

| Color | Hex | Uso |
|---|---|---|
| Lavanda claro | `#EDD2E0` | Fondo de página y cards |
| Melocotón | `#EDBBB4` | Riesgo bajo / hover / chart-2 |
| Malva rosa | `#DBABBE` | Acento primario / botones / chart-1 |
| Rosa polvoso | `#BAA1A7` | Bordes / texto secundario / chart-3 |
| Gris pizarra | `#797B84` | Sidebar / texto principal / riesgo alto |

---

## ⚙️ Stack tecnológico

**Backend**
- [FastAPI](https://fastapi.tiangolo.com/) — API REST + servidor de archivos estáticos
- [pandas](https://pandas.pydata.org/) — procesamiento de datos
- [scikit-learn](https://scikit-learn.org/) — modelos ML y preprocesamiento
- [XGBoost](https://xgboost.readthedocs.io/) — modelo candidato
- [imbalanced-learn](https://imbalanced-learn.org/) — SMOTE para balanceo de clases
- [joblib](https://joblib.readthedocs.io/) — serialización del modelo

**Frontend**
- HTML5 + CSS3 vanilla
- [Chart.js](https://www.chartjs.org/) — visualizaciones interactivas
- [Tailwind CSS](https://tailwindcss.com/) (CDN) — utilidades de estilos
- JavaScript ES6 Modules

**Infraestructura**
- [Render](https://render.com/) — Web Service (plan gratuito)

---

## 🚀 Ejecutar localmente

```bash
# 1. Clonar el repositorio
git clone https://github.com/Apolo-24-End/HR_Churn_Analytics.git
cd HR_Churn_Analytics

# 2. Crear entorno virtual e instalar dependencias
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Levantar el servidor
uvicorn app.main:app --reload

# 4. Abrir en el navegador
# http://localhost:8000
```

---

## 📡 Endpoints de la API

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/api/workforce/summary` | KPIs generales de la fuerza laboral |
| GET | `/api/workforce/department-breakdown` | Headcount y salarios por departamento |
| GET | `/api/workforce/demographics` | Género, estado civil, salario, antigüedad |
| GET | `/api/retention/rate` | Tasas de retención y rotación |
| GET | `/api/retention/reasons` | Top razones de terminación |
| GET | `/api/retention/trend` | Tendencia de contrataciones vs terminaciones |
| GET | `/api/risk/employees` | Empleados activos con score de riesgo |
| GET | `/api/risk/distribution` | Conteo por nivel de riesgo |
| GET | `/api/risk/model-metrics` | Métricas de todos los modelos evaluados |
| GET | `/api/risk/feature-importance` | Top features del modelo ganador |

Documentación interactiva disponible en: [`/docs`](https://hr-churn-analytics.onrender.com/docs)

---

## 👤 Autor

Desarrollado como proyecto de Data Analytics & Machine Learning.

[![GitHub](https://img.shields.io/badge/GitHub-Apolo--24--End-797B84?style=flat-square&logo=github)](https://github.com/Apolo-24-End)
