# Institutional Assistant AI - CLAUDE.md

Guia de comandos, arquitetura corporativa e diretrizes de desenvolvimento para o Institutional Assistant AI.

## Comandos de Build e Execução

### Infraestrutura Local (Docker Compose V2)
```bash
# Subir PostgreSQL 16, Qdrant e Redis 7
docker compose -f deploy/docker-compose.yml up -d postgres qdrant redis
```

### Backend (Python 3.12 / FastAPI)
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend (Angular 19)
```bash
cd frontend
npm install
npm run start
```

## Diretrizes de Desenvolvimento

- **Permission-Aware RAG:** Consultas vetoriais no Qdrant devem sempre aplicar filtros de autorização baseados no usuário (`allowed_roles`, `department`, `is_public`).
- **Sanitização de PII & Anti-Jailbreak:** Todas as requisições de chat passam por filtros de segurança antes de atingir qualquer agente ou retriever.
- **Streaming Token a Token:** Utilizar Server-Sent Events (SSE) emitindo primeiro metadados de fontes (`event: sources`) e sequencialmente os tokens (`event: token`).
- **Respostas Ancoradas:** Citações explícitas de documentos de origem, página e nível de confidencialidade são obrigatórias para mitigar alucinações.
