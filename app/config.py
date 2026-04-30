"""Configuração centralizada da aplicação.

Carrega variáveis de ambiente a partir de um arquivo .env (quando presente).
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações lidas de variáveis de ambiente."""

    app_name: str = "YOUVISA"
    app_env: str = "development"
    database_url: str = "sqlite:///./youvisa.db"

    # "mock" -> respostas simuladas. Trocar para "claude" ou "openai" liga LLMs reais.
    llm_mode: str = "mock"
    llm_api_key: str = ""

    # Escopo permitido para o assistente (governança).
    allowed_scope: str = "visto,passaporte,documentos,processo,status"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_scope_list(self) -> List[str]:
        return [s.strip().lower() for s in self.allowed_scope.split(",") if s.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
