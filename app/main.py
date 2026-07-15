"""
main.py
Punto de entrada FastAPI. Monta routers y sirve el frontend como archivos estáticos.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.routers import workforce, retention, ml
from app.services.ml_service import load_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Al arrancar, asegura que el modelo esté entrenado y cargado."""
    logger.info("Iniciando HR Dashboard — cargando modelo ML...")
    load_model()
    logger.info("Modelo ML listo.")
    yield


app = FastAPI(
    title="HR Executive Dashboard API",
    description="Dashboard ejecutivo de RRHH con predicción de rotación por ML",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS (necesario si frontend y backend están en dominios distintos durante dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Registrar routers de la API
app.include_router(workforce.router)
app.include_router(retention.router)
app.include_router(ml.router)

# Servir archivos estáticos del frontend
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")


@app.get("/", include_in_schema=False)
async def serve_dashboard():
    """Sirve el dashboard principal."""
    return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "HR Dashboard"}
