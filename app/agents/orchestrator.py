"""Orquestrador multiagente.

Coordena o fluxo de atendimento, encadeando os agentes especializados:

    Usuário ─▶ IntentAgent ─▶ RetrievalAgent ─▶ ResponseAgent ─▶ GovernanceAgent ─▶ Resposta

A cada execução o orquestrador:
  1. Garante uma sessão de chat (cria nova caso necessário).
  2. Executa o pipeline.
  3. Persiste a interação em banco e em log estruturado (JSONL).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.agents.governance_agent import GovernanceAgent
from app.agents.intent_agent import IntentAgent
from app.agents.response_agent import ResponseAgent
from app.agents.retrieval_agent import RetrievalAgent
from app.models import ChatSession, Interaction
from app.utils.logger import log_event


@dataclass
class OrchestrationResult:
    session_id: str
    intent: str
    confidence: float
    entities: Dict[str, Any]
    response: str
    blocked_by_governance: bool
    timestamp: datetime


class Orchestrator:
    """Orquestra o fluxo multiagente da Sprint 4."""

    def __init__(self) -> None:
        self.intent_agent = IntentAgent()
        self.retrieval_agent = RetrievalAgent()
        self.response_agent = ResponseAgent()
        self.governance_agent = GovernanceAgent()

    def handle_message(
        self,
        db: Session,
        message: str,
        session_id: Optional[str] = None,
        process_id: Optional[str] = None,
    ) -> OrchestrationResult:
        # 1) Garante uma sessão de chat válida.
        session = self._get_or_create_session(db, session_id, process_id)
        log_event("session_active", {"session_id": session.id, "process_id": session.process_id})

        # 2) Pipeline de agentes.
        intent_result = self.intent_agent.run(message)
        log_event(
            "intent_classified",
            {
                "session_id": session.id,
                "intent": intent_result.intent,
                "confidence": intent_result.confidence,
                "entities": intent_result.entities,
            },
        )

        retrieval_ctx = self.retrieval_agent.run(
            intent=intent_result.intent,
            entities=intent_result.entities,
            db=db,
            process_id=session.process_id or process_id,
        )

        candidate_response = self.response_agent.run(retrieval_ctx)
        governed = self.governance_agent.run(
            intent_result.sanitized_message, intent_result.intent, candidate_response
        )

        # 3) Persistência da interação.
        interaction = Interaction(
            session_id=session.id,
            user_message=message,
            bot_response=governed.response,
            intent=intent_result.intent,
            intent_confidence=intent_result.confidence,
            entities=json.dumps(intent_result.entities, ensure_ascii=False),
            blocked_by_governance=1 if governed.blocked else 0,
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)

        log_event(
            "interaction_logged",
            {
                "session_id": session.id,
                "interaction_id": interaction.id,
                "blocked": governed.blocked,
            },
        )

        return OrchestrationResult(
            session_id=session.id,
            intent=intent_result.intent,
            confidence=intent_result.confidence,
            entities=intent_result.entities,
            response=governed.response,
            blocked_by_governance=governed.blocked,
            timestamp=interaction.created_at,
        )

    @staticmethod
    def _get_or_create_session(
        db: Session, session_id: Optional[str], process_id: Optional[str]
    ) -> ChatSession:
        if session_id:
            existing = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if existing:
                # Permite vincular o processo posteriormente.
                if process_id and not existing.process_id:
                    existing.process_id = process_id
                    db.commit()
                return existing

        new_session = ChatSession(process_id=process_id)
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        log_event("session_created", {"session_id": new_session.id})
        return new_session


orchestrator = Orchestrator()
