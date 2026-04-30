"""Carrega dados de demonstração no banco (apenas se ainda não existirem)."""
from __future__ import annotations

from datetime import datetime, timedelta

from app.database import SessionLocal
from app.models import Document, Process


_SEED = [
    {
        "customer_name": "Mariana Souza",
        "customer_email": "mariana@example.com",
        "visa_type": "turismo",
        "destination_country": "Estados Unidos",
        "status": "em_analise",
        "documents": [
            ("Passaporte", "recebido"),
            ("Foto 5x7", "recebido"),
            ("Comprovante de residência", "pendente"),
            ("Comprovante financeiro", "recebido"),
        ],
    },
    {
        "customer_name": "Lucas Almeida",
        "customer_email": "lucas@example.com",
        "visa_type": "estudo",
        "destination_country": "Canadá",
        "status": "aberto",
        "documents": [
            ("Passaporte", "recebido"),
            ("Carta de aceite", "pendente"),
            ("Comprovante financeiro", "pendente"),
        ],
    },
]


def seed_if_empty() -> None:
    db = SessionLocal()
    try:
        if db.query(Process).count() > 0:
            return
        now = datetime.utcnow()
        for entry in _SEED:
            process = Process(
                customer_name=entry["customer_name"],
                customer_email=entry["customer_email"],
                visa_type=entry["visa_type"],
                destination_country=entry["destination_country"],
                status=entry["status"],
                created_at=now - timedelta(days=10),
                updated_at=now - timedelta(days=2),
            )
            db.add(process)
            db.flush()
            for name, status in entry["documents"]:
                db.add(
                    Document(
                        process_id=process.id,
                        name=name,
                        status=status,
                        uploaded_at=now - timedelta(days=8) if status != "pendente" else None,
                    )
                )
        db.commit()
    finally:
        db.close()
