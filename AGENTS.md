# AGENTS.md

Este arquivo fornece instruções e diretrizes de governança e desenvolvimento para agentes de IA que trabalham no projeto **Institutional Assistant AI**.

## Visão Geral do Projeto
O **Institutional Assistant AI** é uma plataforma corporativa *on-premise/private-cloud* para orquestração de conhecimento institucional, automação de rotinas e assistência contextual segura sob o modelo Zero Data Leakage.

## Tecnologias e Camadas
- **API & Gateway:** FastAPI (Python 3.12+), Server-Sent Events (SSE), Pydantic BaseSettings.
- **Orquestração de Agentes:** LangGraph (State Machine / Task Router) com separação estrita entre FAQ e automação.
- **Banco Vetorial & RBAC:** Qdrant com filtragem de payload em tempo de execução (`is_public`, `department`, `allowed_roles`).
- **Bancos e Cache:** PostgreSQL 16 (Auditoria, Sessões, Histórico de Mensagens) e Redis 7 (Cache Semântico e Sessões).
- **Frontend Corporativo:** Angular 19 com SSE Token Streaming e OIDC/SSO.
- **Provedores LLM:** On-Premise/Local (vLLM, Ollama) ou VPCs privadas dedicadas (Azure OpenAI, AWS Bedrock).

## Estrutura Canônica
- `backend/app/api/`: Endpoints REST e streaming SSE (`/stream`).
- `backend/app/core/`: Configurações (`config.py`), sanitização de PII e anti-jailbreak (`guardrails.py`), validação JWT (`security.py`).
- `backend/app/rag/`: Segmentação (`chunking.py`), embeddings (`embedder.py`) e busca ciente de permissões (`retriever.py`).
- `backend/app/agents/`: Grafo LangGraph com router e subagentes operacionais.
- `deploy/`: Orquestração Docker Compose V2 e Helm Charts.

## Diretrizes de Segurança e Governança (Enterprise)
1. **Permission-Aware Retrieval:** Metadados de documentos DEVEM incluir ACLs (`department`, `allowed_roles`, `is_public`). Toda query vetorial DEVE aplicar filtros de autorização do usuário solicitante.
2. **Prevenção de Fuga (PII):** Todo input de usuário DEVE passar por `sanitize_pii` antes de ser submetido ao modelo ou retriever.
3. **Guardrails Anti-Jailbreak:** Validar inputs contra tentativas de override de prompt de sistema (`check_injection`) retornando HTTP 400.
4. **Precisão e Citação Exata:** Respostas DEVEM ser ancoradas com metadados de documento, página e classificação de sigilo, com `temperature=0` em chamadas factuais.
5. **Auditoria:** Toda interação (usuário, departamento, documento acessado, classificação de sigilo) deve ser registrada para trilha de auditoria e conformidade LGPD/GDPR.
