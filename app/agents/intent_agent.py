"""IntentAgent — interpreta a pergunta do usuário.

Responsável por:
  1. Sanitizar a entrada (proteção contra prompt injection).
  2. Classificar a intenção da mensagem.
  3. Extrair entidades relevantes (tipo de visto, país, e-mail, etc.).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict

from app.nlp import entity_extractor
from app.nlp.intent_classifier import classifier
from app.utils.prompt_security import sanitize_input


@dataclass
class IntentResult:
    sanitized_message: str
    intent: str
    confidence: float
    entities: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class IntentAgent:
    name = "IntentAgent"

    def run(self, message: str) -> IntentResult:
        sanitized = sanitize_input(message)
        intent, confidence = classifier.classify(sanitized)
        entities = entity_extractor.extract(sanitized)
        return IntentResult(
            sanitized_message=sanitized,
            intent=intent,
            confidence=confidence,
            entities=entities,
        )
