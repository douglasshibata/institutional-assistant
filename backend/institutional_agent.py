import os
import json
import requests
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from langgraph.prebuilt import create_react_agent

# ---------------------------------------------------------------------------
# 1. TOOL DE CONEXÃO COM O RAG INSTITUCIONAL (WEKNORA)
# ---------------------------------------------------------------------------
WEKNORA_API_URL = os.getenv("WEKNORA_API_URL", "http://localhost:8000/api/v1/chat/completions")
WEKNORA_API_KEY = os.getenv("WEKNORA_API_KEY", "your-weknora-api-key")

@tool
def consultar_base_institucional(query: str) -> str:
    """
    Consulta a base de conhecimento institucional (RAG) para obter documentos,
    normas, manuais e regras atualizadas sobre a instituição.

    Args:
        query: A pergunta ou termo de busca do usuário sobre a instituição.
    """
    headers = {
        "Authorization": f"Bearer {WEKNORA_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "query": query,
        "top_k": 3,
        "include_metadata": True
    }

    try:
        response = requests.post(WEKNORA_API_URL, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Formata o contexto retornado com citações das fontes
        context_chunks = []
        for item in data.get("results", []):
            source_doc = item.get("metadata", {}).get("source_file", "Documento Institucional")
            page_num = item.get("metadata", {}).get("page", "N/A")
            content = item.get("text", "")

            context_chunks.append(f"--- Fonte: {source_doc} (Pág. {page_num}) ---\n{content}\n")

        if not context_chunks:
            return "Nenhuma informação institucional relevante foi encontrada para esta dúvida."

        return "\n".join(context_chunks)

    except Exception as e:
        return f"Erro ao comunicar com a base de conhecimento institucional: {str(e)}"

# ---------------------------------------------------------------------------
# 2. CONFIGURAÇÃO DO MODELO E PROMPT SISTEMA
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """Você é o Assistente Virtual Oficial da Instituição.
Sua missão é responder às dúvidas dos usuários finais de forma cortês, clara e precisa.

Diretrizes Obrigatórias:
1. Sempre utilize a ferramenta `consultar_base_institucional` para buscar informações antes de responder qualquer dúvida.
2. Responda APENAS com base nos dados retornados pela ferramenta de consulta.
3. Se a informação não estiver presente na base de conhecimento, informe educadamente que não possui esse dado e oriente o usuário a entrar em contato com o suporte institucional.
4. Mencione explicitamente os documentos e páginas consultados ao final da resposta como fonte de referência.
"""

class MockAgentLLM(BaseChatModel):
    """Mock LLM para testes do agente virtual, suportando bind_tools."""

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, run_manager: Optional[Any] = None, **kwargs: Any) -> ChatResult:
        # Check if we have already called the tool in the conversation history
        has_tool_response = any(msg.type == "tool" for msg in messages)

        if not has_tool_response:
            # Trigger a tool call to fulfill the prompt constraint of consulting first
            user_question = "pergunta institucional"
            for msg in reversed(messages):
                if msg.type == "human":
                    user_question = msg.content
                    break

            message = AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "consultar_base_institucional",
                        "args": {"query": user_question},
                        "id": "call_mock_123"
                    }
                ]
            )
        else:
            # Retrieve tool context
            tool_content = ""
            for msg in reversed(messages):
                if msg.type == "tool":
                    tool_content = msg.content
                    break

            if "Nenhuma informação" in tool_content or "Erro ao comunicar" in tool_content:
                content = "Desculpe, mas não encontrei informações sobre isso na base institucional. Por favor, entre em contato com o suporte institucional."
            else:
                content = f"De acordo com a base de conhecimento consultada:\n{tool_content}\n\nEspero ter ajudado!"

            message = AIMessage(content=content)

        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])

    @property
    def _llm_type(self) -> str:
        return "mock-agent-llm"


AI_API_KEY = os.getenv("AI_API_KEY", "sua-chave-aqui")
if AI_API_KEY == "sua-chave-aqui" or AI_API_KEY.startswith("sk-dummy") or os.getenv("MOCK_LLM", "false").lower() == "true":
    llm = MockAgentLLM()
else:
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1
    )

# ---------------------------------------------------------------------------
# 3. CRIAÇÃO DO AGENTE COM O AGENT STARTER KIT
# ---------------------------------------------------------------------------
tools = [consultar_base_institucional]

try:
    institutional_agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=SYSTEM_PROMPT
    )
except TypeError:
    institutional_agent = create_react_agent(
        model=llm,
        tools=tools,
        state_modifier=SYSTEM_PROMPT
    )

# ---------------------------------------------------------------------------
# 4. EXECUÇÃO DE EXEMPLO
# ---------------------------------------------------------------------------
def responder_usuario(pergunta: str):
    print(f"\n[Usuário]: {pergunta}")

    inputs = {"messages": [("user", pergunta)]}

    for event in institutional_agent.stream(inputs, stream_mode="values"):
        message = event["messages"][-1]
        if message.type == "ai" and message.content:
            print(f"[Assistente]: {message.content}")

if __name__ == "__main__":
    # Exemplo de uso:
    responder_usuario("Qual é o procedimento para solicitar o ressarcimento de transporte?")
