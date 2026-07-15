"""
ml.py
Endpoints: Sección 3 — Panel de riesgo ML.
"""

from fastapi import APIRouter, Query
from app.services.ml_service import predict_risk, get_model_metrics
from app.services.data_service import get_active_employees

router = APIRouter(prefix="/api/risk", tags=["ml"])


@router.get("/employees")
def risk_employees(anonymize: bool = Query(False, description="Ocultar nombres reales")):
    """Lista de empleados activos con su score de riesgo de rotación."""
    df_active = get_active_employees()
    result_df = predict_risk(df_active)

    records = result_df.to_dict(orient="records")

    if anonymize:
        for i, rec in enumerate(records):
            rec["Employee_Name"] = f"Empleado #{i + 1}"
            rec["EmpID"] = 0

    # Serializar risk_label (Categorical) a string
    for rec in records:
        rec["risk_label"] = str(rec["risk_label"])

    return records


@router.get("/distribution")
def risk_distribution():
    """Conteo de empleados por nivel de riesgo (Alto / Medio / Bajo)."""
    df_active = get_active_employees()
    result_df = predict_risk(df_active)
    dist = result_df["risk_label"].astype(str).value_counts().to_dict()
    return {"Alto": dist.get("Alto", 0), "Medio": dist.get("Medio", 0), "Bajo": dist.get("Bajo", 0)}


@router.get("/model-metrics")
def model_metrics():
    """Métricas de evaluación de todos los modelos y el ganador."""
    return get_model_metrics()


@router.get("/feature-importance")
def feature_importance():
    """Top features que más influyen en la predicción de rotación."""
    metrics = get_model_metrics()
    return metrics["feature_importance"]
