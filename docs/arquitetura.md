# YOUVISA — Sprint 4 · Documento de Arquitetura

**Projeto:** YOUVISA — Plataforma de atendimento inteligente para vistos e passaportes
**Sprint:** 4 · Integração inteligente, multiagentes, NLP e governança de IA

## 1. Como os agentes inteligentes foram organizados

A Sprint 4 introduz uma **arquitetura multiagente orquestrada** em pipeline. Cada agente tem uma responsabilidade única e bem delimitada, o que torna o fluxo previsível, auditável e fácil de evoluir. Os agentes ficam em `app/agents/` e são coordenados por um `Orchestrator` que recebe a mensagem do usuário e devolve a resposta final.

| Agente | Responsabilidade | Entrada | Saída |
|---|---|---|---|
| **IntentAgent** | Sanitiza o texto e interpreta a pergunta | Mensagem bruta | Intenção + entidades |
| **RetrievalAgent** | Recupera contexto necessário para responder | Intenção + entidades + sessão/processo | Conhecimento + dados do banco |
| **ResponseAgent** | Gera a resposta usando templates controlados (Prompt Engineering) | Contexto recuperado | Resposta candidata |
| **GovernanceAgent** | Valida escopo e bloqueia respostas fora do domínio | Mensagem + intenção + resposta | Resposta final + flag de bloqueio |

O fluxo é determinístico: `IntentAgent → RetrievalAgent → ResponseAgent → GovernanceAgent`. Em modo `mock` (padrão), as respostas vêm de templates parametrizados por dados reais do banco; o desenho permite trocar o `ResponseAgent` por uma chamada a um LLM (Claude/OpenAI) sem alterar o restante do pipeline.

## 2. Como as perguntas dos usuários são interpretadas

A interpretação acontece no **IntentAgent**, em três passos.

**Sanitização (`app/utils/prompt_security.py`).** A mensagem é cortada em 1.500 caracteres e padrões clássicos de **prompt injection** são neutralizados via regex (ex.: "ignore as instruções anteriores", "act as DAN", "reveal your prompt"). Isso protege a aplicação contra tentativas de manipulação do modelo.

**Classificação de Intenção (`app/nlp/intent_classifier.py`).** A mensagem é normalizada (lowercase + remoção de acentos + tokenização + descarte de stopwords em português) e comparada via similaridade de **Jaccard** com os exemplos de cada intenção catalogada em `app/data/intents.json`. Cobertura atual: `consultar_status`, `documentos_necessarios`, `prazo_processo`, `tipos_de_visto`, `saudacao`, `agradecimento`, `fora_do_escopo`. A intenção com a maior similaridade vence; abaixo do limiar (0,18), a mensagem é classificada como `fora_do_escopo` — esta é a primeira camada de governança.

**Extração de Entidades (`app/nlp/entity_extractor.py`).** Usando dicionários e regex, são extraídos: tipo de visto (turismo / estudo / trabalho / imigrante), tipo de documento (passaporte, RG, comprovantes), país de destino, e-mail e número do processo (UUID). Essas entidades são usadas pelo `RetrievalAgent` e pelo `ResponseAgent` para personalizar a resposta — por exemplo, um pedido de "documentos para visto de estudo" devolve a lista correta com base no FAQ.

A combinação dessas três etapas dá ao sistema robustez para entender variações ("Quanto tempo demora?" / "Qual o prazo?" / "Em quantos dias fica pronto?") e responder de forma consistente.

## 3. Como as interações são registradas no sistema

Toda interação é registrada em **dois canais complementares**, garantindo rastreabilidade e suportando consultas posteriores.

**Banco de dados estruturado (SQLite + SQLAlchemy).** O módulo `app/models.py` define quatro tabelas:

- `processes` — processos de visto/passaporte;
- `documents` — documentos vinculados a um processo;
- `chat_sessions` — sessões de atendimento (opcionalmente vinculadas a um processo);
- `interactions` — log estruturado de cada par pergunta-resposta.

A tabela `interactions` armazena: pergunta do usuário, resposta gerada, intenção identificada, confiança da classificação, entidades em JSON, identificador da sessão, flag `blocked_by_governance` e timestamp. Esse modelo permite reconstruir todo o atendimento de um cliente, filtrar por processo e identificar bloqueios feitos pela governança.

**Logs estruturados em JSONL (`app/utils/logger.py`).** Em paralelo, cada evento (`session_created`, `intent_classified`, `interaction_logged`, `process_status_updated`, etc.) é gravado em `logs/events.jsonl` no formato JSON Lines. Esse formato é trivial de consumir por ferramentas de análise (ELK, BigQuery, pandas) e fornece um rastro independente do banco operacional, útil para auditoria.

A interface web (`frontend/`) consome o endpoint `GET /api/history` para apresentar o histórico em tempo real, exibindo intenção, entidades reconhecidas e o flag de governança em cada interação. Dessa forma, o usuário (e o time de operações) acompanha o atendimento de ponta a ponta com total transparência.
