"""RetrievalAgent — busca informações para responder à pergunta.

Combina dados do banco (status do processo, documentos pendentes) com
a base de conhecimento estática (faq.json) e devolve o contexto que será
usado pelo agente de resposta.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models import Process

FAQ_PATH = Path(__file__).resolve().parent.parent / "data" / "faq.json"


@dataclass
class RetrievalContext:
    intent: str
    entities: Dict[str, Any]
    knowledge: Dict[str, Any] = field(default_factory=dict)
    process_summary: Optional[Dict[str, Any]] = None


class RetrievalAgent:
    name = "RetrievalAgent"

    def __init__(self) -> None:
        with FAQ_PATH.open("r", encoding="utf-8") as fh:
            self._faq: Dict[str, Dict[str, str]] = json.load(fh)

    def run(
        self,
        intent: str,
        entities: Dict[str, Any],
        db: Session,
        process_id: Optional[str] = None,
    ) -> RetrievalContext:
        knowledge = self._faq.get(intent, {})
        process_summary = None

        # Quando o usuário fornece um número de processo na própria mensagem,
        # usamos esse valor; caso contrário, usamos o process_id da sessão.
        target_id = entities.get("numero_processo") or process_id

        if target_id and intent == "consultar_status":
            process_summary = self._fetch_process(db, target_id)
        elif intent == "consultar_status" and entities.get("email"):
            process_summary = self._fetch_process_by_email(db, entities["email"])

        return RetrievalContext(
            intent=intent,
            entities=entities,
            knowledge=knowledge,
            process_summary=process_summary,
        )

    @staticmethod
    def _fetch_process(db: Session, process_id: str) -> Optional[Dict[str, Any]]:
        process = db.query(Process).filter(Process.id == process_id).first()
        return _serialize_process(process)

    @staticmethod
    def _fetch_process_by_email(db: Session, email: str) -> Optional[Dict[str, Any]]:
        process = (
            db.query(Process)
            .filter(Process.customer_email == email)
            .order_by(Process.created_at.desc())
            .first()
        )
        return _serialize_process(process)


def _serialize_process(process: Optional[Process]) -> Optional[Dict[str, Any]]:
    if not process:
        return None
    return {
        "id": process.id,
        "customer_name": process.customer_name,
        "visa_type": process.visa_type,
        "destination_country": process.destination_country,
        "status": process.status,
        "updated_at": _fmt(process.updated_at),
        "documents": [
            {"name": doc.name, "status": doc.status}
            for doc in process.documents
        ],
    }


def _fmt(dt: datetime) -> str:
    return dt.strftime("%d/%m/%Y %H:%M")
