"""Endpoints para consulta do histórico geral de interações."""
from __future__ import annotations

import json
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ChatSession, Interaction
from app.schemas import InteractionOut

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("", response_model=List[InteractionOut])
def list_interactions(
    db: Session = Depends(get_db),
    process_id: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
) -> List[InteractionOut]:
    query = db.query(Interaction).order_by(Interaction.created_at.desc())

    if process_id:
        # Filtra interações cujas sessões pertencem ao processo informado.
        session_ids = [
            s.id for s in db.query(ChatSession).filter(ChatSession.process_id == process_id).all()
        ]
        query = query.filter(Interaction.session_id.in_(session_ids))

    interactions = query.limit(limit).all()
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
