# Assistente Virtual Institucional (LangChain + RAG + MCP)

Este projeto é um Assistente Virtual de última geração que utiliza a biblioteca **LangChain** para orquestrar fluxos de RAG (Retrieval-Augmented Generation) e o protocolo **MCP** (Model Context Protocol) para integração de ferramentas.

## Principais Tecnologias

*   **LangChain:** Orquestração de LLMs, Prompts e Chains.
*   **FastAPI:** Interface de API robusta para o frontend.
*   **ChromaDB:** Banco de dados vetorial para busca semântica.
*   **MCP (Model Context Protocol):** Expansão de capacidades através de ferramentas de busca e SQL.
*   **Multi-Provider:** Suporte nativo para OpenAI, Google Gemini, Anthropic, OpenRouter e Ollama.
*   **Multi-Database:** Conectividade com PostgreSQL, MySQL e Oracle.

## Configuração do Ambiente

### Variáveis de Ambiente (.env)

Crie um arquivo `.env` na pasta `backend/` com:

```env
# Configurações de IA
AI_PROVIDER=openai # openai, gemini, anthropic, ollama, openrouter
AI_API_KEY=sua_chave_aqui
AI_MODEL=gpt-4o-mini
AI_BASE_URL=http://localhost:11434/v1 # Opcional para Ollama/OpenRouter

# Configurações de Banco de Dados
DB_TYPE=mock # postgres, mysql, oracle, mock
DATABASE_URL=postgresql://user:pass@localhost/dbname
DB_USER=root
DB_PASS=senha
DB_HOST=localhost
DB_NAME=instituicao
DB_DSN=localhost/xe
```

## Tutorial de Instalação

1.  **Instalar Dependências:**
    ```bash
    cd backend
    pip install -r requirements.txt
    ```

2.  **Iniciar o Servidor:**
    ```bash
    python server.py
    ```

3.  **Executar o Frontend:**
    Abra `frontend/index.html` no seu navegador.

## Como funciona (Fluxo LangChain)

1.  **Entrada:** O usuário envia uma mensagem através do chat widget.
2.  **Recuperação:** O sistema utiliza o `vectorstore` do LangChain (Chroma) para encontrar os documentos mais relevantes.
3.  **Prompt:** Um `ChatPromptTemplate` combina o contexto recuperado, a pergunta do usuário e o `SystemPrompt` rígido.
4.  **Processamento:** O LangChain invoca o LLM configurado (OpenAI, Gemini, etc) através de uma Chain unificada.
5.  **Resposta:** O resultado é processado pelo `StrOutputParser` e enviado de volta ao frontend.

## Deploy com Docker

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build: `docker build -t assistant-langchain .`
Run: `docker run -p 8000:8000 --env-file backend/.env assistant-langchain`
