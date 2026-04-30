"""ResponseAgent — gera a resposta final ao usuário.

No modo "mock" (configurado em settings.llm_mode), as respostas são compostas
por templates controlados a partir do contexto recuperado. Esse desenho
implementa as boas práticas de Prompt Engineering: o template determina o
formato esperado, restringe o escopo das respostas e injeta apenas dados
verificados do banco/FAQ — reduzindo o risco de alucinações.

Quando uma chave de API for adicionada futuramente, basta substituir
_render_with_template por uma chamada ao LLM passando o mesmo contexto.
"""
from __future__ import annotations

from typing import Any, Dict

from app.agents.retrieval_agent import RetrievalContext
from app.config import get_settings


SYSTEM_PROMPT = """Você é o assistente virtual da YOUVISA, especializado em
processos de visto e passaporte. Responda APENAS sobre vistos, passaportes,
documentos e o andamento de processos da plataforma. Se o usuário pedir algo
fora desse escopo, explique educadamente que você não pode ajudar com aquele
assunto. Use linguagem clara, profissional e objetiva. Não invente
informações: se não tiver dado disponível, diga que será necessário
contatar um atendente humano."""


class ResponseAgent:
    name = "ResponseAgent"

    def __init__(self) -> None:
        self._settings = get_settings()

    def run(self, context: RetrievalContext) -> str:
        if self._settings.llm_mode == "mock":
            return self._render_with_template(context)
        # Hook para integração futura com Claude/OpenAI:
        # return call_llm(SYSTEM_PROMPT, context)
        return self._render_with_template(context)

    # ------------------------------------------------------------------
    # Templates controlados (Prompt Engineering)
    # ------------------------------------------------------------------
    def _render_with_template(self, ctx: RetrievalContext) -> str:
        intent = ctx.intent
        ents = ctx.entities
        kb: Dict[str, Any] = ctx.knowledge

        if intent == "consultar_status":
            if ctx.process_summary:
                p = ctx.process_summary
                docs = ", ".join(
                    f"{d['name']} ({d['status']})" for d in p.get("documents", [])
                ) or "nenhum documento cadastrado"
                return (
                    f"Olá, {p['customer_name']}! Encontrei seu processo de visto "
                    f"{p['visa_type']} para {p['destination_country']}.\n"
                    f"• Status atual: {p['status']}\n"
                    f"• Última atualização: {p['updated_at']}\n"
                    f"• Documentos: {docs}"
                )
            return kb.get("no_process", kb.get("default", ""))

        if intent == "documentos_necessarios":
            visa = ents.get("tipo_visto")
            if visa and visa in kb:
                return kb[visa]
            return kb.get("default", "")

        if intent == "prazo_processo":
            visa = ents.get("tipo_visto")
            docs = ents.get("tipo_documento", [])
            if "passaporte" in docs and "passaporte" in kb:
                return kb["passaporte"]
            if visa and visa in kb:
                return kb[visa]
            return kb.get("default", "")

        if intent in {"tipos_de_visto", "saudacao", "agradecimento", "fora_do_escopo"}:
            return kb.get("default", "")

        # Fallback genérico controlado.
        return (
            "Não consegui interpretar sua pergunta com certeza. "
            "Você pode reformular ou perguntar sobre status do processo, "
            "documentos necessários, prazos ou tipos de visto."
        )
