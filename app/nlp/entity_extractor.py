"""Extração de entidades (Entity Extraction).

Implementação por dicionário + regex, identificando:
  - tipo_visto (turismo, estudo, trabalho, imigrante)
  - tipo_documento (passaporte, RG, foto etc.)
  - pais (Estados Unidos, Canadá, Portugal etc.)
  - numero_processo (UUID-like)
  - email
"""
from __future__ import annotations

import re
from typing import Any, Dict

from unidecode import unidecode


_VISA_TYPES = {
    "turismo": ["turismo", "turista", "lazer", "passeio", "viagem", "ferias"],
    "estudo": ["estudo", "estudante", "estudar", "intercambio", "f1", "faculdade", "curso"],
    "trabalho": ["trabalho", "trabalhar", "emprego", "h1b", "l1", "profissional"],
    "imigrante": ["imigrante", "residencia permanente", "morar", "imigracao"],
}

_DOC_TYPES = {
    "passaporte": ["passaporte"],
    "rg": ["rg", "identidade"],
    "cpf": ["cpf"],
    "foto": ["foto", "fotografia"],
    "comprovante_residencia": ["comprovante de residencia", "endereco"],
    "comprovante_renda": ["comprovante de renda", "holerite", "imposto de renda"],
}

_COUNTRIES = {
    "Estados Unidos": ["estados unidos", "eua", "americano", "america", "usa"],
    "Canadá": ["canada", "canadense"],
    "Portugal": ["portugal", "portugues"],
    "Espanha": ["espanha", "espanhol"],
    "Reino Unido": ["reino unido", "inglaterra", "ingles", "uk"],
    "Alemanha": ["alemanha", "alemao"],
    "Japão": ["japao", "japones"],
    "Austrália": ["australia", "australiano"],
}

_EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
_UUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)


def _has_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)


def extract(message: str) -> Dict[str, Any]:
    """Retorna um dicionário com as entidades encontradas na mensagem."""
    normalized = unidecode(message.lower())
    found: Dict[str, Any] = {}

    # Tipo de visto
    for visa, terms in _VISA_TYPES.items():
        if _has_any(normalized, terms):
            found["tipo_visto"] = visa
            break

    # Tipo de documento
    docs = [doc for doc, terms in _DOC_TYPES.items() if _has_any(normalized, terms)]
    if docs:
        found["tipo_documento"] = docs

    # País
    for country, terms in _COUNTRIES.items():
        if _has_any(normalized, terms):
            found["pais"] = country
            break

    # Email
    email_match = _EMAIL_RE.search(message)
    if email_match:
        found["email"] = email_match.group(0)

    # Número de processo (UUID)
    uuid_match = _UUID_RE.search(message)
    if uuid_match:
        found["numero_processo"] = uuid_match.group(0)

    return found
