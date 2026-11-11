# 📘 Tutorial de Operação e Implantação: Institutional Assistant AI

Guia passo a passo para configuração de ambiente, parametrização, execução dos microserviços, testes de validação e troubleshooting da plataforma **Institutional Assistant AI** (`institutional-assistant`).

---

## 🛠️ 1. Visão Geral da Arquitetura Corporativa

O **Institutional Assistant AI** é uma plataforma corporativa *on-premise* / *private-cloud* para orquestração de conhecimento institucional, automação de processos internos e assistência contextual com:
- **Permission-Aware Retrieval (RBAC/ABAC):** Filtragem no banco vetorial Qdrant baseada em papéis (`allowed_roles`), departamento (`department`) e visibilidade pública (`is_public`).
- **Prevenção de Fuga de Dados (Zero External Leakage):** Sanitização por Regex para CPFs, e-mails e cartões, além de bloqueio de prompt injection/jailbreak.
- **Streaming Token a Token:** Endpoint SSE (Server-Sent Events) via FastAPI com emissão assíncrona de fontes/citações antes dos tokens do modelo.
- **Orquestração e Armazenamento:** PostgreSQL 16 para auditoria e conversas, Redis 7 para cache semântico/sessões e Qdrant para busca vetorial HNSW.
- **Frontend Corporativo:** Interface Angular 19 com suporte a SSE token streaming e autenticação OIDC/SSO.

- **Tecnologias Principais:** Python 3.12+, FastAPI, Qdrant, PostgreSQL 16, Redis 7, Angular 19, Docker Compose V2.
- **Diretório do Módulo:** `institutional-assistant`

---

## 📋 2. Pré-requisitos do Sistema

Antes de iniciar a configuração local ou em homologação, garanta que os seguintes componentes estejam instalados:

- **Git:** Para versionamento e gestão de código.
- **Python 3.12+:** Com gerenciador `venv` ou `uv`.
- **Node.js 20+ e npm:** Para o frontend Angular 19.
- **Docker Engine & Docker Compose (Compose V2):** Para orquestração dos contêineres de banco, cache e serviços.

---

## 🚀 3. Passo a Passo de Setup e Instalação

### Passo 1: Acessar a Pasta do Projeto
```bash
cd institutional-assistant
```

### Passo 2: Configurar o Arquivo de Variáveis de Ambiente
Copie o template de ambiente e configure seus parâmetros:
```bash
cp .env.example .env
```

### Passo 3: Inicializar a Infraestrutura com Docker Compose
Suba os serviços essenciais (PostgreSQL 16, Qdrant Vector DB, Redis 7):
```bash
docker compose -f deploy/docker-compose.yml up -d postgres qdrant redis
```

### Passo 4: Instalar Dependências e Subir o Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Passo 5: Inicializar o Frontend Web
```bash
cd ../frontend
npm install
npm run start
```

---

## ⚙️ 4. Configuração do Ambiente (.env)

O arquivo `.env` localizado no diretório raiz de `institutional-assistant` parametriza a segurança e conexões do sistema:

```ini
# Core API
PROJECT_NAME="Institutional Assistant AI"
ENVIRONMENT=development
SECRET_KEY=sua_chave_secreta_jwt_min_32_bytes_super_segura
ACCESS_TOKEN_EXPIRE_MINUTES=480

# Databases & Cache
DATABASE_URL=postgresql+asyncpg://assistant_user:secure_password_here@localhost:5432/assistant_db
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=institutional_docs
REDIS_URL=redis://localhost:6379/0

# LLM & Embeddings (Local On-Premise ou Provedor Privado)
OPENAI_API_BASE=http://localhost:11434/v1
OPENAI_API_KEY=ollama
LLM_MODEL_NAME=mistral:7b-instruct
EMBEDDING_MODEL_NAME=bge-large-en-v1.5
```

---

## 🧪 5. Testes e Validação de Segurança

### Executar Suíte de Testes Automatizados
```bash
cd institutional-assistant/backend
PYTHONPATH=. pytest tests/ -v
```

### Validações de Governança e Regras Críticas:
1. **Filtro RBAC/ABAC:** Testar consultas onde o colaborador não possui o papel ou departamento necessário para recuperar documentos confidenciais.
2. **Filtro Anti-Jailbreak:** Testar inputs com padrões de override de prompt (ex: `ignore all instructions`) e verificar código de erro 400.
3. **Sanitização de PII:** Enviar perguntas contendo CPFs e e-mails e confirmar que os logs e payloads repassam os dados com as tags `[CPF_REMOVIDO]` e `[EMAIL_REMOVIDO]`.

---

## 🔍 6. Troubleshooting e Resolução de Problemas

1. **Porta em uso ou Conflito de Rede:**
   - Verifique portas ocupadas (`8000` para API, `6333` para Qdrant, `5432` para PostgreSQL e `6379` para Redis).
   - Para reiniciar os containers: `docker compose -f deploy/docker-compose.yml down` e suba novamente com `up -d`.
2. **Falha de Conexão com Qdrant:**
   - Confirme se o container `institutional_vector_db` está ativo com `docker ps`.
   - Teste a conectividade: `curl http://localhost:6333/healthz`.
3. **Healthcheck do PostgreSQL pendente:**
   - Verifique logs do banco com `docker logs institutional_postgres`.
   - Certifique-se de que a senha em `.env` coincide com o `POSTGRES_PASSWORD` configurado no `deploy/docker-compose.yml`.
