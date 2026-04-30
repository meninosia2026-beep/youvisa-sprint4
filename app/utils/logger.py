"""Logger estruturado em formato JSON Lines para os eventos do chatbot.

Toda interação registrada via chat também é gravada em logs/events.jsonl
em formato JSON, facilitando consultas/diagnósticos posteriores.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
EVENTS_FILE = LOG_DIR / "events.jsonl"

_logger = logging.getLogger("youvisa")
_logger.setLevel(logging.INFO)
if not _logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s"))
    _logger.addHandler(handler)


def log_event(event: str, payload: Dict[str, Any]) -> None:
    """Registra um evento estruturado no console e no arquivo JSONL."""
    record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event": event,
        **payload,
    }
    _logger.info("%s | %s", event, json.dumps(payload, ensure_ascii=False, default=str))
    with EVENTS_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
