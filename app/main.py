"""Entrypoint FastAPI da YOUVISA - Sprint 4."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api import chat, history, processes
from app.config import get_settings
from app.database import init_db
from app.seed import seed_if_empty

settings = get_settings()

app = FastAPI(
    title=f"{settings.app_name} - API",
    description="Plataforma de atendimento inteligente para vistos e passaportes (Sprint 4).",
    version=__version__,
)

# CORS aberto para facilitar testes locais (frontend e API no mesmo host).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_db()
    seed_if_empty()


@app.get("/api/health")
def healthcheck() -> dict:
    return {"status": "ok", "app": settings.app_name, "version": __version__, "llm_mode": settings.llm_mode}


# Routers
app.include_router(chat.router)
app.include_router(processes.router)
app.include_router(history.router)


# Frontend estático servido em /
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    def root() -> FileResponse:
        return FileResponse(str(FRONTEND_DIR / "index.html"))
