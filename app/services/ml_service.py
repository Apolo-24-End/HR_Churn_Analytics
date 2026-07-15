"""
ml_service.py
Entrenamiento, selección y predicción del modelo de riesgo de rotación.
"""

import pandas as pd
import numpy as np
import joblib
import logging
from pathlib import Path

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.metrics import roc_auc_score, f1_score, make_scorer

try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline

from .data_service import load_clean, LEAKAGE_COLS, ID_COLS, REDUNDANT_IDS

logger = logging.getLogger(__name__)

ARTIFACTS_DIR = Path(__file__).parent.parent.parent / "ml" / "artifacts"
MODEL_PATH = ARTIFACTS_DIR / "best_model.pkl"
META_PATH = ARTIFACTS_DIR / "model_meta.pkl"

# Columnas a excluir del modelo
EXCLUDE_COLS = LEAKAGE_COLS + ID_COLS + REDUNDANT_IDS + [
    "DOB", "DateofHire", "DOB_parsed", "HireDate_parsed", "TermDate_parsed",
    "HireYear", "TermYear", "Termd", "ManagerID"
]

NUMERICAL_FEATURES = [
    "Salary", "EngagementSurvey", "EmpSatisfaction", "SpecialProjectsCount",
    "DaysLateLast30", "Absences", "Age", "Tenure_days", "FromDiversityJobFairID",
    "HispanicLatino",
]

CATEGORICAL_FEATURES = [
    "Sex", "MaritalDesc", "CitizenDesc", "RaceDesc",
    "Department", "Position", "RecruitmentSource", "PerformanceScore",
]


def _get_features_target(df: pd.DataFrame):
    """Prepara X e y eliminando columnas no usadas."""
    feature_cols = NUMERICAL_FEATURES + CATEGORICAL_FEATURES
    # Asegurar que todas las columnas existen
    feature_cols = [c for c in feature_cols if c in df.columns]
    X = df[feature_cols].copy()
    y = df["Termd"].copy()
    return X, y


def _build_preprocessor() -> ColumnTransformer:
    num_cols = [c for c in NUMERICAL_FEATURES]
    cat_cols = [c for c in CATEGORICAL_FEATURES]
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), num_cols),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols),
        ],
        remainder="drop",
    )


def _build_candidates(preprocessor: ColumnTransformer) -> dict:
    candidates = {
        "LogisticRegression": ImbPipeline([
            ("pre", preprocessor),
            ("smote", SMOTE(random_state=42)),
            ("clf", LogisticRegression(max_iter=1000, random_state=42, class_weight="balanced")),
        ]),
        "RandomForest": ImbPipeline([
            ("pre", preprocessor),
            ("smote", SMOTE(random_state=42)),
            ("clf", RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced")),
        ]),
        "GradientBoosting": ImbPipeline([
            ("pre", preprocessor),
            ("smote", SMOTE(random_state=42)),
            ("clf", GradientBoostingClassifier(n_estimators=200, random_state=42)),
        ]),
    }
    if XGBOOST_AVAILABLE:
        candidates["XGBoost"] = ImbPipeline([
            ("pre", preprocessor),
            ("smote", SMOTE(random_state=42)),
            ("clf", XGBClassifier(
                n_estimators=200, random_state=42, use_label_encoder=False,
                eval_metric="logloss", scale_pos_weight=2,
            )),
        ])
    return candidates


def train_and_select() -> dict:
    """
    Entrena todos los modelos candidatos, los evalúa con StratifiedKFold(5)
    y guarda el mejor por ROC-AUC. Retorna el reporte de evaluación.
    """
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    df = load_clean()
    X, y = _get_features_target(df)

    preprocessor = _build_preprocessor()
    candidates = _build_candidates(preprocessor)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scoring = {
        "roc_auc": "roc_auc",
        "f1": make_scorer(f1_score),
        "accuracy": "accuracy",
    }

    results = {}
    for name, pipeline in candidates.items():
        logger.info(f"Evaluando: {name}")
        scores = cross_validate(pipeline, X, y, cv=cv, scoring=scoring, n_jobs=-1)
        results[name] = {
            "roc_auc": round(float(scores["test_roc_auc"].mean()), 4),
            "roc_auc_std": round(float(scores["test_roc_auc"].std()), 4),
            "f1": round(float(scores["test_f1"].mean()), 4),
            "accuracy": round(float(scores["test_accuracy"].mean()), 4),
        }

    # Seleccionar mejor modelo por ROC-AUC
    best_name = max(results, key=lambda k: results[k]["roc_auc"])
    best_pipeline = candidates[best_name]

    # Entrenar con todo el dataset
    best_pipeline.fit(X, y)

    # Extraer importancia de features
    feature_importance = _extract_feature_importance(best_pipeline, X)

    meta = {
        "best_model_name": best_name,
        "results": results,
        "feature_importance": feature_importance,
        "feature_cols": NUMERICAL_FEATURES + CATEGORICAL_FEATURES,
    }

    joblib.dump(best_pipeline, MODEL_PATH)
    joblib.dump(meta, META_PATH)
    logger.info(f"Mejor modelo: {best_name} | ROC-AUC: {results[best_name]['roc_auc']}")

    return meta


def _extract_feature_importance(pipeline, X: pd.DataFrame) -> list[dict]:
    """Extrae importancia de features del clasificador dentro del pipeline."""
    try:
        clf = pipeline.named_steps["clf"]
        pre = pipeline.named_steps["pre"]

        # Obtener nombres de features tras OHE
        cat_enc = pre.named_transformers_["cat"]
        cat_names = list(cat_enc.get_feature_names_out(CATEGORICAL_FEATURES))
        all_names = NUMERICAL_FEATURES + cat_names

        if hasattr(clf, "feature_importances_"):
            importances = clf.feature_importances_
        elif hasattr(clf, "coef_"):
            importances = np.abs(clf.coef_[0])
        else:
            return []

        fi = pd.DataFrame({"feature": all_names, "importance": importances})
        fi = fi.sort_values("importance", ascending=False).head(15)
        fi["importance"] = fi["importance"].round(4)
        return fi.to_dict(orient="records")
    except Exception as e:
        logger.warning(f"No se pudo extraer feature importance: {e}")
        return []


def load_model():
    """Carga el modelo serializado. Si no existe, lo entrena."""
    if not MODEL_PATH.exists():
        logger.info("Modelo no encontrado — entrenando...")
        train_and_select()
    return joblib.load(MODEL_PATH), joblib.load(META_PATH)


def predict_risk(df_active: pd.DataFrame) -> pd.DataFrame:
    """
    Predice el riesgo de rotación para empleados activos.
    Retorna el df con columnas: risk_score, risk_label.
    """
    model, meta = load_model()
    feature_cols = [c for c in (NUMERICAL_FEATURES + CATEGORICAL_FEATURES) if c in df_active.columns]
    X = df_active[feature_cols].copy()

    proba = model.predict_proba(X)[:, 1]
    df_result = df_active[["Employee_Name", "EmpID", "Department", "Position",
                            "Salary", "PerformanceScore", "Absences"]].copy()
    df_result["risk_score"] = (proba * 100).round(1)

    # Umbrales relativos al colectivo de activos (top 25% = Alto, 25-60% = Medio, resto = Bajo)
    p60 = float(np.percentile(proba * 100, 60))
    p75 = float(np.percentile(proba * 100, 75))

    def _label(score):
        if score >= p75:
            return "Alto"
        elif score >= p60:
            return "Medio"
        return "Bajo"

    df_result["risk_label"] = df_result["risk_score"].apply(_label)
    return df_result.sort_values("risk_score", ascending=False)


def get_model_metrics() -> dict:
    _, meta = load_model()
    return {
        "best_model": meta["best_model_name"],
        "results": meta["results"],
        "feature_importance": meta["feature_importance"],
    }
