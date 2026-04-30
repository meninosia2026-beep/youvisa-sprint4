"""Modelos persistidos no banco de dados.

A modelagem segue o requisito da Sprint 4 de organizar dados gerados durante
as interações de forma estruturada, com tabelas para Processos, Documentos,
Sessões de Chat e Logs de Interação (eventos)."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Process(Base):
    """Processo de visto/passaporte de um cliente."""

    __tablename__ = "processes"

    id = Column(String, primary_key=True, default=_uuid)
    customer_name = Column(String, nullable=False)
    customer_email = Column(String, nullable=False, index=True)
    visa_type = Column(String, nullable=False)  # ex.: turismo, estudo, trabalho
    destination_country = Column(String, nullable=False)
    status = Column(String, nullable=False, default="aberto")  # aberto/em_analise/aprovado/recusado
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    documents = relationship("Document", back_populates="process", cascade="all, delete-orphan")
    sessions = relationship("ChatSession", back_populates="process")


class Document(Base):
    """Documento associado a um processo."""

    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=_uuid)
    process_id = Column(String, ForeignKey("processes.id"), nullable=False)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pendente")  # pendente/recebido/aprovado/rejeitado
    uploaded_at = Column(DateTime, nullable=True)

    process = relationship("Process", back_populates="documents")


class ChatSession(Base):
    """Sessão de atendimento via chatbot."""

    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=_uuid)
    process_id = Column(String, ForeignKey("processes.id"), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    process = relationship("Process", back_populates="sessions")
    interactions = relationship(
        "Interaction", back_populates="session", cascade="all, delete-orphan", order_by="Interaction.created_at"
    )


class Interaction(Base):
    """Log estruturado de uma interação (pergunta + resposta).

    Atende ao requisito da Sprint 4 de registro estruturado das interações,
    armazenando pergunta, resposta, intenção identificada, entidades extraídas,
    identificador da sessão e timestamp.
    """

    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    user_message = Column(Text, nullable=False)
    bot_response = Column(Text, nullable=False)
    intent = Column(String, nullable=True)
    intent_confidence = Column(Float, nullable=True)
    entities = Column(Text, nullable=True)  # JSON serializado
    blocked_by_governance = Column(Integer, default=0, nullable=False)  # 0 = não, 1 = sim
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    session = relationship("ChatSession", back_populates="interactions")
