"""
data_service.py
Carga, limpieza y feature engineering del dataset HR.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from functools import lru_cache

DATA_PATH = Path(__file__).parent.parent / "data" / "HRDataset_v14.csv"

# Columnas con leakage (solo conocidas DESPUÉS de la terminación)
LEAKAGE_COLS = ["DateofTermination", "TermReason", "EmploymentStatus"]

# Columnas identificadoras / no predictivas
ID_COLS = ["Employee_Name", "EmpID", "State", "Zip", "ManagerName",
           "LastPerformanceReview_Date"]

# IDs redundantes (ya tenemos la versión texto)
REDUNDANT_IDS = ["MarriedID", "MaritalStatusID", "GenderID", "EmpStatusID",
                 "DeptID", "PerfScoreID", "PositionID"]


@lru_cache(maxsize=1)
def load_raw() -> pd.DataFrame:
    """Carga el CSV con encoding correcto y limpia espacios en strings."""
    df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
    # Limpiar espacios en columnas de texto
    str_cols = df.select_dtypes(include="object").columns
    df[str_cols] = df[str_cols].apply(lambda c: c.str.strip())
    return df


def load_clean() -> pd.DataFrame:
    """
    Retorna el DataFrame limpio con feature engineering aplicado.
    NO elimina columnas de leakage aquí — eso se hace en ml_service.
    Sí calcula Age y Tenure para uso en analytics y ML.
    """
    df = load_raw().copy()

    reference_date = pd.Timestamp("2019-12-31")

    # Feature engineering de fechas
    # DOB formato MM/DD/YY (año 2 dígitos) — corregir pivot de siglo manualmente
    df["DOB_parsed"] = pd.to_datetime(df["DOB"], format="%m/%d/%y", errors="coerce")
    # Python interpreta 00-68 como 2000-2068; los que queden en futuro se corrigen a siglo XX
    future_mask = df["DOB_parsed"].dt.year > reference_date.year
    df.loc[future_mask, "DOB_parsed"] = df.loc[future_mask, "DOB_parsed"] - pd.DateOffset(years=100)

    df["HireDate_parsed"] = pd.to_datetime(df["DateofHire"], format="%m/%d/%Y", errors="coerce")
    df["TermDate_parsed"] = pd.to_datetime(df["DateofTermination"], errors="coerce")

    df["Age"] = ((reference_date - df["DOB_parsed"]).dt.days / 365.25).round(1)
    df["Tenure_days"] = (
        df["TermDate_parsed"].fillna(reference_date) - df["HireDate_parsed"]
    ).dt.days

    # Columna de año de contratación (para tendencias)
    df["HireYear"] = df["HireDate_parsed"].dt.year
    df["TermYear"] = df["TermDate_parsed"].dt.year

    # Normalizar HispanicLatino a booleano
    df["HispanicLatino"] = df["HispanicLatino"].str.lower().map(
        {"yes": 1, "no": 0}
    ).fillna(0).astype(int)

    # Limpiar ManagerID nulos
    df["ManagerID"] = df["ManagerID"].fillna(-1).astype(int)

    return df


def get_active_employees() -> pd.DataFrame:
    """Retorna solo empleados activos (Termd == 0)."""
    return load_clean().query("Termd == 0").copy()


def get_terminated_employees() -> pd.DataFrame:
    """Retorna solo empleados terminados (Termd == 1)."""
    return load_clean().query("Termd == 1").copy()
