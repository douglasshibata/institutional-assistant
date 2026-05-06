# Assistente Institucional - CLAUDE.md

Guia de comandos e diretrizes para o Assistente Virtual Institucional.

## Comandos de Build e Execução

### Backend (Python/FastAPI)
```bash
cd institutional-assistant/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python server.py
```

### Frontend (Vanilla JS)
O frontend é composto por arquivos estáticos em `institutional-assistant/frontend/`. Pode ser servido por qualquer servidor HTTP ou aberto diretamente (`index.html`).

### Docker
```bash
docker build -t assistant-langchain .
docker run -p 8000:8000 --env-file backend/.env assistant-langchain
```

## Diretrizes de Desenvolvimento

- **Orquestração:** Utilize LangChain para fluxos de RAG.
- **Banco Vetorial:** ChromaDB é utilizado para busca semântica.
- **Segurança:** O sistema utiliza um `SystemPrompt` rígido para evitar alucinações e manter a persona institucional.
- **Provedores de IA:** Suporta OpenAI, Gemini, Claude e Ollama via variáveis de ambiente.
- **Banco de Dados:** Suporte para PostgreSQL, MySQL e Oracle via SQLAlchemy/LangChain SQLDatabase.
