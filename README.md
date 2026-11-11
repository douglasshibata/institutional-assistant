# 🏛️ Institutional Assistant AI (Enterprise Knowledge & Task Copilot)

O **Institutional Assistant AI** é uma plataforma corporativa *on-premise* / *private-cloud* para orquestração de conhecimento institucional, automação de processos internos e assistência contextual. Projetado sob os princípios de **Isolamento Estrito de Dados**, **Zero External Data Leakage** e **Autorização Fina (Document-Level Access Control)**, o sistema conecta colaboradores à base de conhecimento verificada da instituição via Retrieval-Augmented Generation (RAG) de alta fidelidade e agentes autônomos orientados a tarefas.

---

## 🏛️ 1. Topologia da Arquitetura do Sistema

```text
                                  +-----------------------------+
                                  |   Web Client (Angular 19)   |
                                  |   - SSE Token Streaming     |
                                  |   - OIDC / SSO Authentication|
                                  +--------------+--------------+
                                                 | HTTPS / WSS
                                                 v
+-------------------------------------------------------------------------------------------------+
|                                GATEWAY & API LAYER (FastAPI)                                    |
|                                                                                                 |
|   - OAuth2 / JWT Auth Middleware          - Rate Limiter & Audit Logger                         |
|   - PII Sanitizer & Masking Engine        - Prompt Injection & Jailbreak Guardrail              |
+------------------------------------------------┬------------------------------------------------+
                                                 │
                                                 v
+-------------------------------------------------------------------------------------------------+
|                                 CORE AI & WORKFLOW ORCHESTRATOR                                 |
|                                                                                                 |
|   ┌────────────────────────────────┐                 ┌──────────────────────────────────────┐   |
|   │     Agent State Machine        │ ──────────────► │      Permission-Aware RAG Engine     │   |
|   │    (LangGraph Task Router)     │                 │   (Hybrid Search: BM25 + Vector HNSW)│   |
|   └────────────────┬───────────────┘                 └──────────────────┬───────────────────┘   |
|                    │                                                    │                       |
+--------------------┼────────────────────────────────────────────────────┼-----------------------+
                     │ Dispara Ações Internas                             │ Busca de Contexto
                     v                                                    v
+------------------------------------+               +--------------------------------------------+
|     ENTERPRISE CONNECTORS          |               |          STORAGE & VECTOR FABRIC           |
|  - Active Directory / LDAP         |               |  - Qdrant / pgvector (Payload Filter RBAC) |
|  - ERP & Service Desk (Jira/SNOW)  |               |  - PostgreSQL 16 (Auditoria e Conversas)   |
|  - Document Repositories (SharePoint/S3)           |  - Redis 7 (Cache Semântico e Sessões)     |
+------------------------------------+               +--------------------------------------------+
```

---

## 🌟 2. Diferenciais & Segurança Corporativa

* **Permission-Aware Retrieval (Controle de Acesso em Nível de Chunk):**
  * Ao indexar documentos (políticas de RH, contratos, manuais), os metadados registram listas de controle de acesso (ACLs).
  * A busca vetorial aplica filtros em tempo de execução: o colaborador só recupera fragmentos compatíveis com seus cargos, departamentos e grupos do Active Directory/OIDC.
* **Prevenção de Fuga de Dados (Zero External Leakage):**
  * Suporte nativo a provedores locais (vLLM / Ollama com Mistral/Llama 3) ou instâncias privadas dedicadas (Azure OpenAI / AWS Bedrock VPC).
  * Sanitização de PII (CPFs, e-mails, dados sensíveis) antes do envio para qualquer modelo.
* **Respostas Ancoradas com Citação Exata (Grounded Citations):**
  * Toda resposta do RAG referencia o documento de origem, página, data de vigência e grau de confidencialidade, eliminando alucinações institucionais.
* **Agente com Máquina de Estados (LangGraph):**
  * Separação estrita entre consultas de FAQ institucional e comandos operacionais (abertura de chamados, agendamentos, aprovações).

---

## 📁 3. Estrutura Canônica de Diretórios

```text
institutional-assistant/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py               # Injeção de dependências (Auth, DB, UserContext)
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   ├── auth.py       # Handshake SSO/OIDC
│   │   │       │   ├── chat.py       # Endpoint SSE para streaming de respostas
│   │   │       │   ├── documents.py  # Ingestão e gerenciamento de arquivos
│   │   │       │   └── tasks.py      # Automação de rotinas internas
│   │   │       └── router.py
│   │   ├── core/
│   │   │   ├── config.py             # Validação estrita via Pydantic BaseSettings
│   │   │   ├── guardrails.py         # Filtro anti-jailbreak e mascaramento de PII
│   │   │   └── security.py           # Validação JWT e parsing de permissões
│   │   ├── db/
│   │   │   ├── session.py            # Sessão PostgreSQL (SQLAlchemy 2.0 async)
│   │   │   └── vector_store.py       # Cliente Qdrant / pgvector
│   │   ├── models/                   # Tabelas: Users, AuditLog, ChatSession, Message
│   │   ├── rag/
│   │   │   ├── chunking.py           # Segmentação semântica e hierárquica
│   │   │   ├── embedder.py           # Gerenciador de embeddings (ex: text-embedding-3 / BGE)
│   │   │   └── retriever.py          # Busca híbrida + Reranker (Cross-Encoder)
│   │   ├── agents/
│   │   │   ├── state.py              # Definição do estado global do grafo
│   │   │   ├── task_agent.py         # Subagentes operacionais
│   │   │   └── supervisor.py         # Roteador LangGraph
│   │   └── schemas/                  # Pydantic Schemas de I/O
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py                       # Factory e montagem do ciclo de vida da API
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── core/                 # Auth interceptors, Guards, StreamService
│   │   │   ├── features/chat/        # Interface de conversa com markdown e citações
│   │   │   └── shared/               # Componentes visuais acessíveis (WCAG)
│   ├── package.json
│   └── angular.json
├── deploy/
│   ├── docker-compose.yml
│   └── helm/                         # Charts Kubernetes para ambientes corporativos
├── .env.example
└── README.md
```

---

## ⚙️ 4. Implementação dos Módulos Principais

### A. RAG Ciente de Permissões com Filtro de Payload (`backend/app/rag/retriever.py`)
Garante que o colaborador consulte apenas documentos autorizados pelos seus grupos institucionais:

```python
from typing import List, Dict, Any
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
from app.core.config import settings

class PermissionAwareRetriever:
    def __init__(self, qdrant_client: AsyncQdrantClient, embedding_client):
        self.client = qdrant_client
        self.embedding_client = embedding_client
        self.collection_name = settings.QDRANT_COLLECTION_NAME

    async def retrieve(
        self,
        query: str,
        user_roles: List[str],
        department: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        query_vector = await self.embedding_client.aembed_query(query)

        # Filtro de permissão: chunk público OU do departamento do usuário OU de seus papéis
        permission_filter = models.Filter(
            should=[
                models.FieldCondition(
                    key="is_public",
                    match=models.MatchValue(value=True),
                ),
                models.FieldCondition(
                    key="department",
                    match=models.MatchValue(value=department),
                ),
                models.FieldCondition(
                    key="allowed_roles",
                    match=models.MatchAny(any=user_roles),
                ),
            ]
        )

        search_result = await self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=permission_filter,
            limit=top_k,
            with_payload=True
        )

        return [
            {
                "content": hit.payload["page_content"],
                "source": hit.payload["source_document"],
                "page": hit.payload.get("page", 1),
                "score": hit.score,
                "classification": hit.payload.get("confidentiality", "INTERNAL")
            }
            for hit in search_result
        ]
```

### B. Streaming com SSE e Sanitização (`backend/app/api/v1/endpoints/chat.py`)
Entrega de respostas token a token com cabeçalhos Server-Sent Events (SSE) e validação de contexto:

```python
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from app.api.deps import get_current_user, get_retriever, get_orchestrator
from app.schemas.chat_schema import ChatQueryRequest
from app.core.guardrails import sanitize_pii, check_injection

router = APIRouter()

@router.post("/stream")
async def chat_stream_endpoint(
    request: ChatQueryRequest,
    current_user = Depends(get_current_user),
    retriever = Depends(get_retriever),
    orchestrator = Depends(get_orchestrator)
):
    # 1. Checagem de injeção de prompt e sanitização de dados
    if check_injection(request.message):
        raise HTTPException(status_code=400, detail="Tentativa de prompt injection detectada.")

    clean_message = sanitize_pii(request.message)

    # 2. Recuperação com escopo de permissões do usuário
    context_chunks = await retriever.retrieve(
        query=clean_message,
        user_roles=current_user.roles,
        department=current_user.department,
        top_k=4
    )

    async def event_generator():
        # Envia metadados de fontes antes do texto
        sources_meta = [
            {"doc": c["source"], "page": c["page"], "classification": c["classification"]}
            for c in context_chunks
        ]
        yield f"event: sources\ndata: {json.dumps(sources_meta)}\n\n"

        # Stream dos tokens gerados pelo modelo
        async for token in orchestrator.astream_response(clean_message, context_chunks, current_user):
            payload = json.dumps({"token": token})
            yield f"event: token\ndata: {payload}\n\n"

        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

### C. Guardrails e Sanitização de PII (`backend/app/core/guardrails.py`)
Evita o vazamento acidental de informações sigilosas e bloqueia ataques estruturados:

```python
import re

PATTERNS = {
    "CPF": r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b|\b\d{11}\b",
    "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b",
    "CREDIT_CARD": r"\b(?:\d{4}[-\s]?){3}\d{4}\b"
}

INJECTION_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"(?i)system\s+prompt\s+override",
    r"(?i)you\s+are\s+now\s+in\s+developer\s+mode"
]

def sanitize_pii(text: str) -> str:
    sanitized = text
    for label, pattern in PATTERNS.items():
        sanitized = re.sub(pattern, f"[{label}_REMOVIDO]", sanitized)
    return sanitized

def check_injection(text: str) -> bool:
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text):
            return True
    return False
```

---

## 🐳 5. Orquestração Multi-Serviço (`deploy/docker-compose.yml`)

Ambiente pronto para desenvolvimento e homologação privada em conformidade com Docker Compose V2:

```yaml
services:
  api:
    build:
      context: ../backend
      dockerfile: Dockerfile
    container_name: institutional_api
    restart: always
    ports:
      - "8000:8000"
    env_file:
      - ../.env
    depends_on:
      postgres:
        condition: service_healthy
      qdrant:
        condition: service_started
      redis:
        condition: service_started

  qdrant:
    image: qdrant/qdrant:v1.11.0
    container_name: institutional_vector_db
    restart: always
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

  postgres:
    image: postgres:16-alpine
    container_name: institutional_postgres
    restart: always
    environment:
      POSTGRES_DB: assistant_db
      POSTGRES_USER: assistant_user
      POSTGRES_PASSWORD: secure_password_here
    ports:
      - "5432:5432"
    volumes:
      - pg_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U assistant_user -d assistant_db"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: institutional_redis
    ports:
      - "6379:6379"

volumes:
  qdrant_data:
  pg_data:
```

---

## 🚀 6. Guia de Configuração e Execução

### 1. Pré-requisitos
* **Python 3.12+**
* **Node.js 20+ e npm** (para o frontend Angular 19)
* **Docker & Docker Compose** (especificação Compose V2)

### 2. Configuração de Variáveis de Ambiente (`.env`)

```ini
# Core API
PROJECT_NAME="Institutional Assistant AI"
ENVIRONMENT=production
SECRET_KEY=sua_chave_secreta_jwt_min_32_bytes

# Databases
DATABASE_URL=postgresql+asyncpg://assistant_user:secure_password_here@localhost:5432/assistant_db
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=institutional_docs
REDIS_URL=redis://localhost:6379/0

# LLM & Embeddings (Local ou Provedor Privado)
OPENAI_API_BASE=http://localhost:11434/v1  # ou URL da Azure OpenAI privada
OPENAI_API_KEY=ollama                     # ou chave do tenant privado
LLM_MODEL_NAME=mistral:7b-instruct
EMBEDDING_MODEL_NAME=bge-large-en-v1.5
```

### 3. Execução dos Serviços

**Subir Bancos e Storage:**
```bash
docker compose -f deploy/docker-compose.yml up -d postgres qdrant redis
```

**Iniciar Backend (FastAPI):**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Iniciar Frontend (Angular 19):**
```bash
cd frontend
npm install
npm run start
```

---

## 📊 Matriz Comparativa: Versão Anterior vs. Versão Corporativa Refatorada

| Dimensão | Versão Anterior | Versão Corporativa Refatorada |
|---|---|---|
| **Arquitetura de Segurança** | "Designed with strict privacy" (abstrato) | RBAC/ABAC com filtragem nativa de payload no banco vetorial |
| **Pipeline de Resposta** | Invocação síncrona monolítica | Streaming com Server-Sent Events (SSE) e desacoplamento de citações |
| **Prevenção de Fuga (PII)** | Não existente | Sanitização por Regex antes do RAG e bloqueio de prompt injection |
| **Stack de Dados** | Menciona apenas "LangChain" | Qdrant (Vector HNSW) + PostgreSQL 16 (Auditoria) + Redis (Cache) |
| **Confiabilidade de Fatos** | Respostas genéricas de LLM | Respostas estritamente ancoradas com metadados de documento, página e sigilo |
| **Execução e Orquestração** | Comandos soltos e incompletos | Docker Compose integrado com healthchecks e estrutura de pastas em camadas |
