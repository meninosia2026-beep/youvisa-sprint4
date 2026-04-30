"""Schemas Pydantic usados pela camada de API."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    process_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    intent: str
    confidence: float
    entities: Dict[str, Any]
    response: str
    blocked_by_governance: bool
    timestamp: datetime


class InteractionOut(BaseModel):
    id: int
    session_id: str
    user_message: str
    bot_response: str
    intent: Optional[str]
    intent_confidence: Optional[float]
    entities: Optional[Dict[str, Any]]
    blocked_by_governance: bool
    created_at: datetime


class DocumentOut(BaseModel):
    id: str
    name: str
    status: str
    uploaded_at: Optional[datetime]


class ProcessCreate(BaseModel):
    customer_name: str
    customer_email: str
    visa_type: str
    destination_country: str


class ProcessOut(BaseModel):
    id: str
    customer_name: str
    customer_email: str
    visa_type: str
    destination_country: str
    status: str
    created_at: datetime
    updated_at: datetime
    documents: List[DocumentOut]


class StatusUpdate(BaseModel):
    status: str
