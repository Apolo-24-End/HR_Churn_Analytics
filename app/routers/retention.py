"""
retention.py
Endpoints: Sección 2 — Análisis de retención histórica.
"""

from fastapi import APIRouter
from app.services.analytics_service import (
    get_retention_rate,
    get_termination_reasons,
    get_turnover_by_department,
    get_hire_term_trend,
    get_turnover_by_recruitment_source,
)

router = APIRouter(prefix="/api/retention", tags=["retention"])


@router.get("/rate")
def retention_rate():
    return get_retention_rate()


@router.get("/reasons")
def termination_reasons():
    return get_termination_reasons()


@router.get("/by-department")
def turnover_by_department():
    return get_turnover_by_department()


@router.get("/trend")
def hire_term_trend():
    return get_hire_term_trend()


@router.get("/by-recruitment-source")
def turnover_by_source():
    return get_turnover_by_recruitment_source()
