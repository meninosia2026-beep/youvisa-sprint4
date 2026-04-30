"""Configuração do banco de dados (SQLite + SQLAlchemy)."""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import get_settings

settings = get_settings()

# `check_same_thread=False` permite usar a mesma conexão SQLite com FastAPI.
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency injection para sessões do banco."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Cria todas as tabelas registradas no Base.metadata."""
    # Importa modelos para que sejam registrados no metadata.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
