"""
responses.py
Schemas Pydantic para las respuestas de la API.
"""

from pydantic import BaseModel
from typing import Any


class WorkforceSummary(BaseModel):
    total_employees: int
    active_employees: int
    terminated_employees: int
    turnover_rate: float
    avg_salary_active: int
    avg_age_active: float
    avg_tenure_days: int
    total_departments: int


class ApiResponse(BaseModel):
    status: str = "ok"
    data: Any
