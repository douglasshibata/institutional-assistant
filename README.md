# Assistente Virtual Institucional (RAG + MCP)

Este projeto é um Assistente Virtual Full-Stack que utiliza RAG (Retrieval-Augmented Generation) e MCP (Model Context Protocol) para fornecer respostas precisas baseadas em bases de dados institucionais (Vetoriais e Relacionais).

## Arquitetura

1.  **Backend (Python + FastAPI + MCP):**
    *   **Provedores de IA:** Suporte para OpenAI, Google Gemini, Anthropic Claude, OpenRouter e Ollama.
    *   **Bancos de Dados:** Integração com ChromaDB (Vetorial), PostgreSQL, MySQL e Oracle (Relacionais).
    *   **MCP:** Ferramentas para busca semântica e consultas SQL.
2.  **Frontend (Vanilla JS):**
    *   Chat widget flutuante, moderno e injetável.

## Configuração do Ambiente

### Variáveis de Ambiente (.env)

Crie um arquivo `.env` na pasta `backend/` com as seguintes opções:

```env
# Configuração de IA
AI_PROVIDER=openai # openai, gemini, anthropic, openrouter, ollama
AI_API_KEY=sua_chave_aqui
AI_MODEL=gpt-4o-mini # ou modelo correspondente do provedor
AI_BASE_URL=http://localhost:11434 # Apenas para Ollama

# Configuração de Banco de Dados (Opcional)
DB_TYPE=mock # postgres, mysql, oracle, mock
DATABASE_URL=postgres://user:pass@localhost:5432/dbname # Para Postgres
DB_HOST=localhost
DB_USER=root
DB_PASS=senha
DB_NAME=instituicao
DB_DSN=localhost/xe # Para Oracle
```

## Tutorial Passo-a-Passo

### 1. Instalação Local

1.  Navegue até o backend: `cd backend`
2.  Instale as dependências: `pip install -r requirements.txt`
3.  Inicie o servidor: `python server.py`

### 2. Deploy com Docker

Crie um `Dockerfile` na raiz:

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
EXPOSE 8000
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build e Run:
```bash
docker build -t assistant-backend .
docker run -p 8000:8000 --env-file backend/.env assistant-backend
```

## Demonstração de Funcionamento

1.  **Início:** O usuário abre o chat no site.
2.  **Pergunta:** O usuário pergunta "Qual o horário da biblioteca?".
3.  **Recuperação (RAG):**
    *   O backend usa a ferramenta MCP `buscar_informacao_institucional` para pesquisar no ChromaDB.
    *   O contexto encontrado é injetado no prompt.
4.  **Geração:** O provedor de IA escolhido (ex: Gemini) gera a resposta baseada estritamente no contexto.
5.  **Resposta:** O usuário recebe a resposta formatada no chat widget.

---
**Nota:** O sistema é estritamente restrito. Se a informação não for encontrada nas bases configuradas, o assistente recusará a resposta para evitar alucinações.
