"""
analytics_service.py
Cálculos de negocio para el dashboard: workforce y retención.
"""

import pandas as pd
from .data_service import load_clean, get_active_employees, get_terminated_employees


# ─── WORKFORCE ────────────────────────────────────────────────────────────────

def get_workforce_summary() -> dict:
    df = load_clean()
    active = df[df["Termd"] == 0]
    terminated = df[df["Termd"] == 1]

    return {
        "total_employees": int(len(df)),
        "active_employees": int(len(active)),
        "terminated_employees": int(len(terminated)),
        "turnover_rate": round(len(terminated) / len(df) * 100, 1),
        "avg_salary_active": int(active["Salary"].mean()),
        "avg_age_active": round(float(active["Age"].mean()), 1),
        "avg_tenure_days": int(active["Tenure_days"].mean()),
        "total_departments": int(df["Department"].nunique()),
    }


def get_department_breakdown() -> list[dict]:
    df = load_clean()
    result = (
        df.groupby("Department")
        .agg(
            total=("EmpID", "count"),
            active=("Termd", lambda x: (x == 0).sum()),
            terminated=("Termd", lambda x: (x == 1).sum()),
            avg_salary=("Salary", "mean"),
        )
        .reset_index()
    )
    result["turnover_rate"] = (result["terminated"] / result["total"] * 100).round(1)
    result["avg_salary"] = result["avg_salary"].round(0).astype(int)
    return result.to_dict(orient="records")


def get_demographics() -> dict:
    active = get_active_employees()

    _gender_map = {"M": "Masculino", "F": "Femenino"}
    gender = {_gender_map.get(k, k): v for k, v in active["Sex"].value_counts().items()}

    marital = active["MaritalDesc"].value_counts().to_dict()

    race = active["RaceDesc"].value_counts().to_dict()

    # Distribución salarial (bins)
    salary_bins = pd.cut(
        active["Salary"],
        bins=[0, 50000, 70000, 90000, 110000, 999999],
        labels=["<50k", "50-70k", "70-90k", "90-110k", ">110k"],
    ).value_counts().sort_index()

    # Distribución de antigüedad en años
    active = active.copy()
    active["Tenure_years"] = (active["Tenure_days"] / 365.25).round(0).astype(int)
    tenure_dist = (
        active["Tenure_years"]
        .clip(0, 15)
        .value_counts()
        .sort_index()
        .to_dict()
    )

    return {
        "gender": gender,
        "marital_status": marital,
        "race": race,
        "salary_distribution": {str(k): int(v) for k, v in salary_bins.items()},
        "tenure_distribution": {str(k): int(v) for k, v in tenure_dist.items()},
    }


def get_department_avg_tenure() -> list[dict]:
    active = get_active_employees().copy()
    active["Tenure_years"] = (active["Tenure_days"] / 365.25).round(1)
    result = (
        active.groupby("Department")["Tenure_years"]
        .mean()
        .round(1)
        .reset_index()
        .rename(columns={"Tenure_years": "avg_tenure_years"})
    )
    return result.to_dict(orient="records")


# ─── RETENCIÓN ────────────────────────────────────────────────────────────────

def get_retention_rate() -> dict:
    df = load_clean()
    total = len(df)
    terminated = int((df["Termd"] == 1).sum())
    active = int((df["Termd"] == 0).sum())

    term = get_terminated_employees()
    avg_tenure_before_leaving = round(float(term["Tenure_days"].mean() / 365.25), 1)

    return {
        "total": total,
        "active": active,
        "terminated": terminated,
        "turnover_rate_pct": round(terminated / total * 100, 1),
        "retention_rate_pct": round(active / total * 100, 1),
        "avg_tenure_before_leaving_years": avg_tenure_before_leaving,
    }


def get_termination_reasons() -> list[dict]:
    term = get_terminated_employees()
    reasons = (
        term["TermReason"]
        .value_counts()
        .reset_index()
        .rename(columns={"TermReason": "reason", "count": "count"})
    )
    return reasons.head(10).to_dict(orient="records")


def get_turnover_by_department() -> list[dict]:
    df = load_clean()
    result = (
        df.groupby("Department")
        .apply(
            lambda g: pd.Series({
                "total": len(g),
                "terminated": int((g["Termd"] == 1).sum()),
                "turnover_rate": round((g["Termd"] == 1).mean() * 100, 1),
            })
        )
        .reset_index()
    )
    return result.to_dict(orient="records")


def get_hire_term_trend() -> list[dict]:
    df = load_clean()

    hires = (
        df.groupby("HireYear")["EmpID"]
        .count()
        .reset_index()
        .rename(columns={"EmpID": "hires", "HireYear": "year"})
    )

    terms = (
        df[df["Termd"] == 1]
        .groupby("TermYear")["EmpID"]
        .count()
        .reset_index()
        .rename(columns={"EmpID": "terminations", "TermYear": "year"})
    )

    trend = hires.merge(terms, on="year", how="outer").fillna(0).sort_values("year")
    trend["hires"] = trend["hires"].astype(int)
    trend["terminations"] = trend["terminations"].astype(int)
    trend["year"] = trend["year"].astype(int)
    return trend.to_dict(orient="records")


def get_turnover_by_recruitment_source() -> list[dict]:
    df = load_clean()
    result = (
        df.groupby("RecruitmentSource")
        .agg(
            total=("EmpID", "count"),
            terminated=("Termd", "sum"),
        )
        .reset_index()
    )
    result["turnover_rate"] = (result["terminated"] / result["total"] * 100).round(1)
    result["terminated"] = result["terminated"].astype(int)
    result["total"] = result["total"].astype(int)
    return result.sort_values("turnover_rate", ascending=False).to_dict(orient="records")
