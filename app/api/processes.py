"""Endpoints para gerenciamento de processos de visto/passaporte."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Document, Process
from app.schemas import DocumentOut, ProcessCreate, ProcessOut, StatusUpdate
from app.utils.logger import log_event

router = APIRouter(prefix="/api/processes", tags=["processes"])


_DEFAULT_DOCS = ["Passaporte", "Foto 5x7", "Comprovante de residência", "Comprovante financeiro"]


@router.post("", response_model=ProcessOut, status_code=201)
def create_process(payload: ProcessCreate, db: Session = Depends(get_db)) -> ProcessOut:
    process = Process(
        customer_name=payload.customer_name,
        customer_email=payload.customer_email,
        visa_type=payload.visa_type,
        destination_country=payload.destination_country,
    )
    db.add(process)
    db.flush()  # garante o id antes de criar documentos.

    for doc_name in _DEFAULT_DOCS:
        db.add(Document(process_id=process.id, name=doc_name, status="pendente"))

    db.commit()
    db.refresh(process)
    log_event("process_created", {"process_id": process.id, "customer_email": process.customer_email})
    return _serialize(process)


@router.get("", response_model=List[ProcessOut])
def list_processes(db: Session = Depends(get_db)) -> List[ProcessOut]:
    processes = db.query(Process).order_by(Process.created_at.desc()).all()
    return [_serialize(p) for p in processes]


@router.get("/{process_id}", response_model=ProcessOut)
def get_process(process_id: str, db: Session = Depends(get_db)) -> ProcessOut:
    process = db.query(Process).filter(Process.id == process_id).first()
    if not process:
        raise HTTPException(status_code=404, detail="Processo não encontrado")
    return _serialize(process)


@router.patch("/{process_id}/status", response_model=ProcessOut)
def update_status(process_id: str, payload: StatusUpdate, db: Session = Depends(get_db)) -> ProcessOut:
    process = db.query(Process).filter(Process.id == process_id).first()
    if not process:
        raise HTTPException(status_code=404, detail="Processo não encontrado")
    process.status = payload.status
    db.commit()
    db.refresh(process)
    log_event("process_status_updated", {"process_id": process.id, "status": process.status})
    return _serialize(process)


def _serialize(process: Process) -> ProcessOut:
    return ProcessOut(
        id=process.id,
        customer_name=process.customer_name,
        customer_email=process.customer_email,
        visa_type=process.visa_type,
        destination_country=process.destination_country,
        status=process.status,
        created_at=process.created_at,
        updated_at=process.updated_at,
        documents=[
            DocumentOut(
                id=d.id, name=d.name, status=d.status, uploaded_at=d.uploaded_at
            )
            for d in process.documents
        ],
    )
