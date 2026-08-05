import os
import json
import logging
import requests
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logger = logging.getLogger(__name__)

# Configurações de API e LLM
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai").lower()
AI_API_KEY = os.getenv("AI_API_KEY", "sua-chave-aqui")
WEKNORA_API_URL = os.getenv("WEKNORA_API_URL", "http://localhost:8000/api/v1/chat/completions")
WEKNORA_API_KEY = os.getenv("WEKNORA_API_KEY", "your-weknora-api-key")

# --- MOCK LLM PARA TESTES COMPATÍVEL COM LANGCHAIN/LANGGRAPH ---
class MockAgentLLM(BaseChatModel):
    """Mock LLM para testes compatível com LangChain e que simula chamadas de ferramentas."""
    def bind_tools(self, tools: List[Any], **kwargs: Any) -> "MockAgentLLM":
        """Simula o bind_tools necessário pelo create_react_agent do LangGraph."""
        return self

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any
    ) -> ChatResult:
        # Se ferramentas forem vinculadas, simula uma chamada de ferramenta primeiro se não houver ToolMessage ainda
        has_tool_message = any(msg.type == "tool" for msg in messages)

        if kwargs.get("tools") and not has_tool_message:
            # Retorna uma chamada de ferramenta simulada
            tool_call = {
                "name": "consultar_base_institucional",
                "args": {"query": messages[-1].content},
                "id": "call_123"
            }
            message = AIMessage(
                content="Vou consultar a base de conhecimento institucional.",
                tool_calls=[tool_call]
            )
        else:
            # Retorna a resposta final baseada no contexto fornecido
            context = ""
            for msg in messages:
                if msg.type == "tool":
                    context = msg.content
                    break

            content = (
                f"[MOCK] Resposta oficial da Instituição.\n\n"
                f"Com base na base de conhecimento:\n{context}\n\n"
                f"Fonte: Documento de Testes (Pág. 1)"
            )
            message = AIMessage(content=content)

        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])

    @property
    def _llm_type(self) -> str:
        return "mock"

def get_agent_llm():
    if AI_API_KEY == "sua-chave-aqui" or AI_API_KEY.startswith("sk-dummy") or os.getenv("MOCK_AGENT", "false").lower() == "true":
        return MockAgentLLM()

    if AI_PROVIDER == "openai":
        return ChatOpenAI(model=os.getenv("AI_MODEL", "gpt-4o-mini"), api_key=AI_API_KEY, temperature=0.1)
    elif AI_PROVIDER == "gemini":
        return ChatGoogleGenerativeAI(model=os.getenv("AI_MODEL", "gemini-1.5-flash"), google_api_key=AI_API_KEY, temperature=0.1)
    elif AI_PROVIDER == "anthropic":
        return ChatAnthropic(model=os.getenv("AI_MODEL", "claude-3-5-sonnet-20240620"), api_key=AI_API_KEY, temperature=0.1)
    elif AI_PROVIDER == "ollama" or AI_PROVIDER == "openrouter" or AI_PROVIDER == "nvidia":
        default_base_url = "http://localhost:11434/v1"
        default_model = "llama3"

        if AI_PROVIDER == "openrouter":
            default_base_url = "https://openrouter.ai/api/v1"
            default_model = "google/gemma-2-9b-it:free"
        elif AI_PROVIDER == "nvidia":
            default_base_url = "https://integrate.api.nvidia.com/v1"
            default_model = "meta/llama-3.1-8b-instruct"

        base_url = os.getenv("AI_BASE_URL", default_base_url)
        model = os.getenv("AI_MODEL", default_model)

        return ChatOpenAI(model=model, api_key=AI_API_KEY, base_url=base_url, temperature=0.1)
    else:
        raise ValueError(f"Provedor {AI_PROVIDER} não suportado.")

# ---------------------------------------------------------------------------
# 1. TOOL DE CONEXÃO COM O RAG INSTITUCIONAL (WEKNORA)
# ---------------------------------------------------------------------------
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
llm = get_agent_llm()

SYSTEM_PROMPT = """Você é o Assistente Virtual Oficial da Instituição.
Sua missão é responder às dúvidas dos usuários finais de forma cortês, clara e precisa.

Diretrizes Obrigatórias:
1. Sempre utilize a ferramenta `consultar_base_institucional` para buscar informações antes de responder qualquer dúvida.
2. Responda APENAS com base nos dados retornados pela ferramenta de consulta.
3. Se a informação não estiver presente na base de conhecimento, informe educadamente que não possui esse dado e oriente o usuário a entrar em contato com o suporte institucional.
4. Mencione explicitamente os documentos e páginas consultados ao final da resposta como fonte de referência.
"""

# ---------------------------------------------------------------------------
# 3. CRIAÇÃO DO AGENTE COM O AGENT STARTER KIT
# ---------------------------------------------------------------------------
tools = [consultar_base_institucional]

# Criação do agente com compatibilidade dinâmica entre versões do LangGraph (prompt vs state_modifier)
try:
    institutional_agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=SYSTEM_PROMPT
    )
except TypeError:
    # Fallback para versões anteriores do LangGraph
    institutional_agent = create_react_agent(
        model=llm,
        tools=tools,
        state_modifier=SYSTEM_PROMPT
    )

# ---------------------------------------------------------------------------
# 4. AUXILIARES DE EXECUÇÃO
# ---------------------------------------------------------------------------
def get_agent_response(pergunta: str) -> str:
    """Executa o agente síncronamente e retorna a resposta final do assistente."""
    inputs = {"messages": [("user", pergunta)]}
    result = institutional_agent.invoke(inputs)
    messages = result.get("messages", [])
    for msg in reversed(messages):
        if msg.type == "ai" and msg.content:
            return msg.content
    return "Desculpe, ocorreu um erro ao gerar a resposta."

async def get_agent_response_async(pergunta: str) -> str:
    """Executa o agente assíncronamente e retorna a resposta final do assistente."""
    inputs = {"messages": [("user", pergunta)]}
    result = await institutional_agent.ainvoke(inputs)
    messages = result.get("messages", [])
    for msg in reversed(messages):
        if msg.type == "ai" and msg.content:
            return msg.content
    return "Desculpe, ocorreu um erro ao gerar a resposta."

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
