# Assistente Virtual Institucional (RAG + MCP)

Este projeto consiste em um Assistente Virtual inteligente projetado para responder perguntas estritamente baseadas na base de conhecimento de uma instituição, utilizando a arquitetura RAG (Retrieval-Augmented Generation) e o protocolo MCP (Model Context Protocol).

## Arquitetura

1.  **Backend (Python + FastAPI + MCP):**
    *   **FastAPI:** Provê o endpoint `/api/chat` para comunicação com o frontend.
    *   **MCP (Model Context Protocol):** Utiliza o `FastMCP` para expor a ferramenta `buscar_informacao_institucional`.
    *   **ChromaDB:** Banco de dados vetorial em memória que armazena o conhecimento institucional.
    *   **OpenAI GPT-4o-mini:** LLM responsável por gerar as respostas baseadas no contexto recuperado.
2.  **Frontend (Vanilla JS + CSS):**
    *   Widget flutuante moderno e responsivo que pode ser injetado em qualquer página HTML.

## Pré-requisitos

*   Python 3.10 ou superior
*   Chave de API da OpenAI

## Instalação e Execução

### 1. Configurar o Backend

Navegue até a pasta do backend:
```bash
cd backend
```

Instale as dependências:
```bash
pip install -r requirements.txt
```

Configure sua chave de API:
Crie um arquivo `.env` na pasta `backend/` ou exporte a variável:
```bash
export OPENAI_API_KEY='sua-chave-aqui'
```

Inicie o servidor:
```bash
python server.py
```
O servidor estará rodando em `http://localhost:8000`.

### 2. Executar o Frontend

Basta abrir o arquivo `frontend/index.html` em qualquer navegador moderno.

## Como funciona o RAG

Quando você faz uma pergunta no chat:
1.  O backend recebe a pergunta.
2.  A ferramenta **MCP** faz uma busca semântica no **ChromaDB**.
3.  O contexto recuperado é injetado em um **Prompt de Sistema rígido**.
4.  O LLM gera a resposta. Se a informação não estiver no contexto, ele responde: *"Desculpe, não tenho essa informação na minha base de dados."*

## Testes sugeridos

*   **Pergunta válida:** "Quais cursos vocês oferecem?"
*   **Pergunta sobre localização:** "Onde fica o campus?"
*   **Pergunta fora da base:** "Qual o resultado do jogo de futebol de ontem?" (Deve retornar a mensagem de erro padrão).
