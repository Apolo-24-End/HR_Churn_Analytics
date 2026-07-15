"""
workforce.py
Endpoints: Sección 1 — Vista general de la fuerza laboral.
"""

from fastapi import APIRouter
from app.services.analytics_service import (
    get_workforce_summary,
    get_department_breakdown,
    get_demographics,
    get_department_avg_tenure,
)

router = APIRouter(prefix="/api/workforce", tags=["workforce"])


@router.get("/summary")
def workforce_summary():
    return get_workforce_summary()


@router.get("/department-breakdown")
def department_breakdown():
    return get_department_breakdown()


@router.get("/demographics")
def demographics():
    return get_demographics()


@router.get("/tenure-by-department")
def tenure_by_department():
    return get_department_avg_tenure()
