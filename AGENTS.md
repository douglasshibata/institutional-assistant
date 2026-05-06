# AGENTS.md

Este arquivo fornece instruções e contexto para agentes de IA que trabalham no projeto **Assistente Virtual Institucional**.

## Visão Geral do Projeto
Assistente Virtual que utiliza LangChain para orquestrar fluxos de RAG (Retrieval-Augmented Generation) e o protocolo MCP para integração de ferramentas, fornecendo informações institucionais precisas.

## Tecnologias Utilizadas
- **Orquestração:** LangChain (Chroma, ChatPromptTemplate, Chains).
- **API:** FastAPI.
- **Banco Vetorial:** ChromaDB.
- **Protocolo:** MCP (Model Context Protocol).
- **Provedores AI:** OpenAI, Gemini, Claude, OpenRouter, Ollama.
- **Bancos de Dados:** PostgreSQL, MySQL, Oracle.

## Estrutura de Pastas
- `backend/`: Código principal da API e lógica RAG.
- `frontend/`: Interface de chat (Vanilla JS).

## Comandos Principais
- Build/Instalação: `pip install -r requirements.txt` (em `backend/`)
- Execução: `python server.py`
- Docker: `docker build -t assistant-langchain .`

## Diretrizes de Desenvolvimento
- **Precisão:** Use `temperature=0` para respostas factuais e evite alucinações.
- **Segurança:** Proteção contra Prompt Injection e garantia de apenas leitura (SELECT) em ferramentas SQL.
- **Persona:** Siga rigorosamente o `SystemPrompt` para manter a persona institucional.
- **Privacidade:** Não persista PII de forma insegura em logs ou no ChromaDB.
