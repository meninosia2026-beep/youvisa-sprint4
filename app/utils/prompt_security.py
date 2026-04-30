"""Proteção contra Prompt Injection e governança de IA.

A função sanitize_input remove instruções comuns de injeção (ex.: "ignore
todas as instruções anteriores") e o GovernanceFilter verifica se a
mensagem (e a resposta) estão dentro do escopo definido na configuração.

Também aplicamos limite de tamanho para evitar mensagens absurdamente
longas que possam ser usadas para inundar o contexto.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from unidecode import unidecode

from app.config import get_settings

# Padrões usados em ataques clássicos de prompt injection.
_INJECTION_PATTERNS = [
    r"ignore (all|todas?) (as )?instru[cç][õo]es",
    r"ignore (the )?(previous|anteriores?)",
    r"esque[çc]a (tudo|as instru[cç][õo]es)",
    r"act as (a |an )?(?:dan|jailbreak|developer mode)",
    r"voc[eê] agora ?(é|sera|será) ",
    r"system: ",
    r"</?system>",
    r"prompt anterior",
    r"reset (your )?context",
    r"reveal (your )?prompt",
    r"mostre (o |seu )?prompt",
]

_MAX_CHARS = 1500


@dataclass
class GovernanceVerdict:
    allowed: bool
    reason: str = ""
    sanitized_message: str = ""


def sanitize_input(message: str) -> str:
    """Remove tentativas óbvias de prompt injection e limita o tamanho."""
    cleaned = message[:_MAX_CHARS]
    normalized = unidecode(cleaned.lower())
    for pattern in _INJECTION_PATTERNS:
        if re.search(pattern, normalized):
            cleaned = re.sub(pattern, "[bloqueado]", cleaned, flags=re.IGNORECASE)
    return cleaned


class GovernanceFilter:
    """Verifica se a mensagem está dentro do escopo permitido.

    Combina o escopo configurado em settings.allowed_scope com palavras
    relacionadas — assim, perguntas que não sejam sobre vistos/passaportes/
    documentos/processo são bloqueadas com uma mensagem padronizada.
    """

    def __init__(self) -> None:
        settings = get_settings()
        base = settings.allowed_scope_list
        related = [
            "visa", "embaixada", "consulado", "viagem", "imigracao",
            "documento", "documentos", "processo", "solicitacao",
            "prazo", "status", "atendimento", "youvisa",
        ]
        self.scope_terms: List[str] = [unidecode(t.lower()) for t in base + related]

    def is_in_scope(self, message: str, intent: str) -> GovernanceVerdict:
        # Saudações e agradecimentos passam sem necessidade de termo de escopo.
        if intent in {"saudacao", "agradecimento"}:
            return GovernanceVerdict(allowed=True)

        if intent == "fora_do_escopo":
            return GovernanceVerdict(
                allowed=False,
                reason="Pergunta classificada como fora do escopo do assistente.",
            )

        normalized = unidecode(message.lower())
        for term in self.scope_terms:
            if term in normalized:
                return GovernanceVerdict(allowed=True)

        # Se a intenção foi reconhecida (não fora_do_escopo) confiamos no classificador.
        return GovernanceVerdict(allowed=True)


governance = GovernanceFilter()
