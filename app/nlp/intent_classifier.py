"""Classificador de Intenção (Intent Classification).

Implementação simples e didática usando similaridade de tokens (Jaccard) com
normalização (lowercase + remoção de acentos + tokens curtos descartados).
Não depende de bibliotecas pesadas e é determinística — adequada para o
contexto acadêmico da Sprint 4.

Cada exemplo de cada intenção é tokenizado. A pergunta do usuário é comparada
com cada exemplo e a intenção com a maior similaridade é selecionada.
Se nenhuma intenção atingir um threshold mínimo, classificamos como
"fora_do_escopo".
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

from unidecode import unidecode

INTENTS_PATH = Path(__file__).resolve().parent.parent / "data" / "intents.json"

# Palavras de baixa carga semântica que não devem influenciar a classificação.
_STOPWORDS = {
    "a", "o", "os", "as", "um", "uma", "uns", "umas",
    "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
    "que", "se", "para", "por", "pra", "pro", "com", "sem", "ao", "à",
    "e", "ou", "mas", "meu", "minha", "meus", "minhas",
    "eu", "tu", "voce", "voces", "ele", "ela", "eles", "elas", "nos",
    "esta", "este", "esse", "essa", "isso", "aquilo",
    "ja", "tambem", "muito", "bem", "ai", "la",
}

_THRESHOLD = 0.18  # similaridade mínima para considerar uma intenção válida


def _normalize(text: str) -> List[str]:
    """Lowercase, remove acentos e mantém tokens significativos."""
    text = unidecode(text.lower())
    tokens = re.findall(r"[a-z0-9]+", text)
    return [t for t in tokens if len(t) > 1 and t not in _STOPWORDS]


def _jaccard(a: List[str], b: List[str]) -> float:
    set_a, set_b = set(a), set(b)
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


class IntentClassifier:
    def __init__(self, intents_path: Path = INTENTS_PATH):
        with intents_path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        self._intents: List[Dict] = data["intents"]
        # Pré-tokeniza os exemplos de cada intenção.
        self._tokenized: Dict[str, List[List[str]]] = {
            intent["name"]: [_normalize(ex) for ex in intent["examples"]]
            for intent in self._intents
        }

    def classify(self, message: str) -> Tuple[str, float]:
        """Retorna (intent_name, confidence) para a mensagem do usuário."""
        tokens = _normalize(message)
        if not tokens:
            return "fora_do_escopo", 0.0

        best_intent = "fora_do_escopo"
        best_score = 0.0
        for intent_name, examples in self._tokenized.items():
            for ex_tokens in examples:
                score = _jaccard(tokens, ex_tokens)
                if score > best_score:
                    best_score = score
                    best_intent = intent_name

        if best_score < _THRESHOLD:
            return "fora_do_escopo", best_score
        return best_intent, round(best_score, 3)


# Instância pronta para uso (singleton leve).
classifier = IntentClassifier()
