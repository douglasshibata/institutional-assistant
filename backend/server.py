import os
import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# LangChain Imports
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langchain_chroma import Chroma
from langchain_community.embeddings import FakeEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# Carrega variáveis de ambiente
load_dotenv()

# Configuração de Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configurações ---
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai").lower()
AI_API_KEY = os.getenv("AI_API_KEY", "sua-chave-aqui")
DB_TYPE = os.getenv("DB_TYPE", "mock").lower()

# --- Banco de Dados Vetorial (LangChain + Chroma) ---
# Usamos embeddings fake para o modo mock/demonstração inicial
if AI_API_KEY == "sua-chave-aqui" or AI_API_KEY.startswith("sk-dummy"):
    embeddings = FakeEmbeddings(size=1536)
else:
    embeddings = OpenAIEmbeddings()

vectorstore = Chroma(
    collection_name="conhecimento_institucional",
    embedding_function=embeddings,
    persist_directory="./chroma_db"
)

# Popula o banco se estiver vazio
if len(vectorstore.get()['ids']) == 0:
    vectorstore.add_texts(
        texts=[
            "A Instituição foi fundada em 1990 e foca em tecnologia.",
            "Horário de atendimento: Segunda a Sexta, 08h às 20h.",
            "Cursos disponíveis: IA, Ciência de Dados e Desenvolvimento de Software.",
            "O campus fica na Avenida Paulista, 1000, São Paulo."
        ],
        metadatas=[{"source": "institucional"}] * 4
    )

# --- Banco de Dados Relacional (LangChain SQLDatabase) ---
def get_sql_db():
    if DB_TYPE == "mock": return None
    try:
        if DB_TYPE == "postgres":
            return SQLDatabase.from_uri(os.getenv("DATABASE_URL"))
        elif DB_TYPE == "mysql":
            uri = f"mysql+mysqlconnector://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
            return SQLDatabase.from_uri(uri)
        elif DB_TYPE == "oracle":
            uri = f"oracle+oracledb://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_DSN')}"
            return SQLDatabase.from_uri(uri)
    except Exception as e:
        logger.error(f"Erro ao conectar no banco SQL: {e}")
        return None
    return None

sql_db = get_sql_db()

# --- Orquestração de IA (LangChain LLM) ---
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from typing import Any

from langchain_core.outputs import ChatResult, ChatGeneration

class MockLLM(BaseChatModel):
    """Mock LLM para testes compatível com LangChain."""
    def _generate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, run_manager: Optional[Any] = None, **kwargs: Any) -> ChatResult:
        message = AIMessage(content=f"[LANGCHAIN MOCK] Provedor: {AI_PROVIDER}. Resposta gerada para o contexto fornecido.")
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])

    @property
    def _llm_type(self) -> str:
        return "mock"

def get_llm():
    if AI_API_KEY == "sua-chave-aqui" or AI_API_KEY.startswith("sk-dummy"):
        return MockLLM()

    if AI_PROVIDER == "openai":
        return ChatOpenAI(model=os.getenv("AI_MODEL", "gpt-4o-mini"), api_key=AI_API_KEY, temperature=0)
    elif AI_PROVIDER == "gemini":
        return ChatGoogleGenerativeAI(model=os.getenv("AI_MODEL", "gemini-1.5-flash"), google_api_key=AI_API_KEY, temperature=0)
    elif AI_PROVIDER == "anthropic":
        return ChatAnthropic(model=os.getenv("AI_MODEL", "claude-3-5-sonnet-20240620"), api_key=AI_API_KEY, temperature=0)
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

        return ChatOpenAI(model=model, api_key=AI_API_KEY, base_url=base_url, temperature=0)
    else:
        raise ValueError(f"Provedor {AI_PROVIDER} não suportado.")

llm = get_llm()

# --- MCP Server ---
mcp = FastMCP("AssistenteInstitucional")

@mcp.tool()
def buscar_informacao_institucional(query: str) -> str:
    """Busca informações no banco vetorial da instituição."""
    docs = vectorstore.similarity_search(query, k=3)
    return "\n".join([d.page_content for d in docs])

@mcp.tool()
def consultar_dados_relacionais(query: str) -> str:
    """Executa consultas em bancos SQL (Postgres, MySQL, Oracle)."""
    if sql_db:
        return sql_db.run(query)
    return "Banco relacional não configurado ou em modo mock."

# --- FastAPI App ---
app = FastAPI(title="LangChain Institutional Assistant")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class ChatRequest(BaseModel): message: str
class ChatResponse(BaseModel): response: str

SYSTEM_PROMPT = """Você é um assistente virtual da Instituição.
Responda APENAS com base no contexto fornecido.
Se a informação não estiver no contexto, diga exatamente: 'Desculpe, não tenho essa informação na minha base de dados.'"""

# LangChain Chain (RAG)
prompt_template = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("user", "Contexto:\n{context}\n\nPergunta: {question}")
])

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # Se a variável USE_WEKNORA_AGENT for true, utiliza o novo agente integrado com o Agent Starter Kit e WeKnora
        use_weknora = os.getenv("USE_WEKNORA_AGENT", "true").lower() == "true"
        if use_weknora:
            from institutional_agent import get_agent_response_async
            resposta = await get_agent_response_async(request.message)
            return ChatResponse(response=resposta)

        # Recuperação original (ChromaDB local)
        # Usamos run_in_threadpool para não bloquear o loop de eventos com chamadas síncronas
        from starlette.concurrency import run_in_threadpool
        contexto = await run_in_threadpool(buscar_informacao_institucional, request.message)

        if not contexto or "Nenhuma informação" in contexto:
             return ChatResponse(response="Desculpe, não tenho essa informação na minha base de dados.")

        # Geração via Chain
        chain = prompt_template | llm | StrOutputParser()
        # Se o LLM suportar ainvoke, usamos; caso contrário, run_in_threadpool
        if hasattr(llm, "ainvoke"):
            resposta = await chain.ainvoke({"context": contexto, "question": request.message})
        else:
            resposta = await run_in_threadpool(chain.invoke, {"context": contexto, "question": request.message})

        return ChatResponse(response=resposta)
    except Exception as e:
        logger.error(f"Erro no processamento: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
