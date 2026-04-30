"""Endpoints relacionados ao chatbot."""
from __future__ import annotations

import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.orchestrator import orchestrator
from app.database import get_db
from app.models import Interaction
from app.schemas import ChatRequest, ChatResponse, InteractionOut

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def send_message(payload: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    """Envia uma mensagem ao chatbot e devolve a resposta orquestrada."""
    result = orchestrator.handle_message(
        db=db,
        message=payload.message,
        session_id=payload.session_id,
        process_id=payload.process_id,
    )
    return ChatResponse(
        session_id=result.session_id,
        intent=result.intent,
        confidence=result.confidence,
        entities=result.entities,
        response=result.response,
        blocked_by_governance=result.blocked_by_governance,
        timestamp=result.timestamp,
    )


@router.get("/{session_id}/history", response_model=List[InteractionOut])
def get_session_history(session_id: str, db: Session = Depends(get_db)) -> List[InteractionOut]:
    """Retorna o histórico estruturado de uma sessão de chat."""
    interactions = (
        db.query(Interaction)
        .filter(Interaction.session_id == session_id)
        .order_by(Interaction.created_at.asc())
        .all()
    )
    if not interactions:
        # Mantém a UX previsível: sessão inexistente devolve lista vazia.
        return []
    return [_serialize(i) for i in interactions]


def _serialize(interaction: Interaction) -> InteractionOut:
    entities = {}
    if interaction.entities:
        try:
            entities = json.loads(interaction.entities)
        except json.JSONDecodeError:
            entities = {}
    return InteractionOut(
        id=interaction.id,
        session_id=interaction.session_id,
        user_message=interaction.user_message,
        bot_response=interaction.bot_response,
        intent=interaction.intent,
        intent_confidence=interaction.intent_confidence,
        entities=entities,
        blocked_by_governance=bool(interaction.blocked_by_governance),
        created_at=interaction.created_at,
    )
