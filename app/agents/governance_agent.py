"""GovernanceAgent — última camada antes de devolver a resposta ao usuário.

Verifica se a interação está dentro do escopo permitido. Caso a intenção
seja "fora_do_escopo", substitui a resposta gerada por uma mensagem padrão
e marca o evento como bloqueado pela governança.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.utils.prompt_security import governance


OUT_OF_SCOPE_REPLY = (
    "Sou um assistente especializado em vistos, passaportes e processos da "
    "YOUVISA. Não posso ajudar com esse assunto, mas estou disponível para "
    "esclarecer dúvidas sobre seu processo, documentos ou prazos."
)


@dataclass
class GovernedResponse:
    response: str
    blocked: bool


class GovernanceAgent:
    name = "GovernanceAgent"

    def run(self, message: str, intent: str, response: str) -> GovernedResponse:
        verdict = governance.is_in_scope(message, intent)
        if not verdict.allowed:
            return GovernedResponse(response=OUT_OF_SCOPE_REPLY, blocked=True)
        return GovernedResponse(response=response, blocked=False)
