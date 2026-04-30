# YOUVISA — Sprint 4

Plataforma de **atendimento inteligente** para vistos e passaportes. Esta entrega da Sprint 4 consolida os módulos das sprints anteriores em um fluxo unificado de **agentes inteligentes**, com interpretação de linguagem natural, registro estruturado de interações e governança de IA.

## 🎥 Demonstração em vídeo

Veja o sistema em funcionamento (até 3 minutos):

▶ **[Assistir no YouTube](https://youtu.be/50RbDbicGEI)**

O vídeo mostra a interação do usuário com o chatbot, a interpretação de perguntas sobre o processo, a resposta gerada pelo sistema, o registro da interação no histórico e a interface funcional para consulta de informações.

## Sumário

1. [Visão geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Como executar](#como-executar)
4. [Endpoints da API](#endpoints-da-api)
5. [Fluxo de atendimento](#fluxo-de-atendimento)
6. [Governança de IA](#governança-de-ia)
7. [Estrutura de pastas](#estrutura-de-pastas)
8. [Próximos passos](#próximos-passos)

---

## Visão geral

A YOUVISA recebe documentos, gera tarefas automáticas, responde perguntas frequentes e acompanha o status dos processos. Na Sprint 4 esses recursos passam a operar de forma coordenada por meio de um **fluxo multiagente**, garantindo previsibilidade e rastreabilidade do atendimento.

Principais capacidades desta entrega:

- Chatbot integrado ao processo do cliente, com sessão persistente.
- Quatro agentes especializados orquestrados em pipeline.
- Classificação de intenção (Intent Classification) e extração de entidades em português.
- Registro estruturado de interações em SQLite + logs JSONL.
- Engenharia de prompt com escopo controlado e proteção contra prompt injection.
- Frontend único para conversar, visualizar o processo e auditar o histórico.

## Arquitetura

```
┌──────────────┐    HTTP     ┌──────────────────────────────────────────────┐
│  Frontend    │──────────▶ │  FastAPI                                     │
│  HTML/CSS/JS │            │  ├─ /api/chat                                │
└──────────────┘            │  ├─ /api/processes                           │
                            │  ├─ /api/history                             │
                            │  └─ Orquestrador multiagente                 │
                            │     ├─ IntentAgent     (NLP)                 │
                            │     ├─ RetrievalAgent  (banco + FAQ)         │
                            │     ├─ ResponseAgent   (prompt engineering)  │
                            │     └─ GovernanceAgent (escopo + injection)  │
                            └──────────────────────────────────────────────┘
                                          │
                                  SQLite + logs/events.jsonl
```

Detalhes por componente:

- **IntentAgent** — sanitiza a mensagem (remove tentativas de prompt injection), classifica a intenção via similaridade de tokens (Jaccard) e extrai entidades como tipo de visto, país, e-mail e número de processo.
- **RetrievalAgent** — combina dados estruturados do banco (status do processo, documentos do cliente) com a base de conhecimento estática `app/data/faq.json`.
- **ResponseAgent** — monta a resposta final usando templates controlados (Prompt Engineering). No modo `mock` (padrão) não chama LLM externo; o desenho permite trocar para Claude/OpenAI alterando apenas a configuração.
- **GovernanceAgent** — última camada antes de devolver a resposta: confere se a interação está dentro do escopo permitido (vistos, passaportes, documentos, processo) e bloqueia respostas fora desse domínio.

## Como executar

### Requisitos

- Python 3.10+
- pip

### Passo a passo

```bash
# 1) Clonar o repositório
git clone <url-do-repo>
cd youvisa-sprint4

# 2) Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate     # Linux/macOS
# .venv\Scripts\activate      # Windows

# 3) Instalar dependências
pip install -r requirements.txt

# 4) Copiar variáveis de ambiente
cp .env.example .env

# 5) Rodar a aplicação
uvicorn app.main:app --reload
```

Acesse:

- **Interface web**: http://localhost:8000
- **Documentação Swagger**: http://localhost:8000/docs
- **Health check**: http://localhost:8000/api/health

Na primeira execução o banco SQLite é criado automaticamente e dois processos de demonstração são carregados (Mariana — visto de turismo / EUA; Lucas — visto de estudo / Canadá), permitindo interagir com o chatbot imediatamente.

## Endpoints da API

| Método | Caminho | Descrição |
|-------|---------|-----------|
| `GET`  | `/api/health` | Verifica se a API está online. |
| `POST` | `/api/chat` | Envia mensagem ao chatbot (body: `message`, `session_id?`, `process_id?`). |
| `GET`  | `/api/chat/{session_id}/history` | Histórico estruturado de uma sessão. |
| `POST` | `/api/processes` | Cria um novo processo. |
| `GET`  | `/api/processes` | Lista processos. |
| `GET`  | `/api/processes/{id}` | Detalha um processo (inclui documentos). |
| `PATCH`| `/api/processes/{id}/status` | Atualiza o status de um processo. |
| `GET`  | `/api/history` | Histórico geral de interações (filtros: `process_id`, `limit`). |

Exemplo de chamada ao chat:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Qual o status do meu processo?", "process_id":"<id-do-processo>"}'
```

## Fluxo de atendimento

1. O usuário envia uma mensagem pelo frontend.
2. O **Orquestrador** garante uma sessão de chat (cria caso não exista) e a vincula ao processo selecionado.
3. O **IntentAgent** sanitiza a entrada, classifica a intenção e extrai entidades.
4. O **RetrievalAgent** monta o contexto, buscando o processo correspondente e a entrada relevante do FAQ.
5. O **ResponseAgent** preenche o template controlado de resposta.
6. O **GovernanceAgent** valida o escopo e, se necessário, substitui a resposta por uma mensagem padrão de fora do escopo.
7. A interação é persistida em SQLite (`interactions`) e em `logs/events.jsonl`.

## Governança de IA

- Sanitização de entrada com regex contra padrões clássicos de prompt injection (ex.: "ignore as instruções anteriores").
- Limite de 1.500 caracteres por mensagem.
- Escopo controlado via variável `ALLOWED_SCOPE` no `.env`.
- Templates de resposta determinísticos: o sistema só pode responder a partir do conteúdo do FAQ ou de dados verificados do banco.
- Toda interação carrega o flag `blocked_by_governance` quando filtrada, garantindo rastreabilidade.

## Estrutura de pastas

```
youvisa-sprint4/
├── app/
│   ├── agents/          # Orquestrador + 4 agentes especializados
│   ├── api/             # Routers FastAPI (chat, processes, history)
│   ├── data/            # FAQ e definição de intenções
│   ├── nlp/             # Intent classifier e entity extractor
│   ├── utils/           # Logger estruturado e proteção contra prompt injection
│   ├── config.py
│   ├── database.py
│   ├── main.py          # Entrypoint FastAPI
│   ├── models.py        # SQLAlchemy
│   ├── schemas.py       # Pydantic
│   └── seed.py          # Dados de demonstração
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── docs/
│   └── arquitetura.md   # Documento curto da Sprint 4 (1-2 páginas)
├── requirements.txt
├── .env.example
└── README.md
```

## Próximos passos

- Substituir o modo `mock` por integração com a API do Claude (basta trocar `LLM_MODE` no `.env` e implementar o conector em `ResponseAgent.run`).
- Ampliar o conjunto de exemplos no `intents.json` para cobrir variações regionais.
- Adicionar autenticação por token nas APIs.
- Exportar o histórico de interações para um data warehouse (BigQuery/PostgreSQL) para análises agregadas.
