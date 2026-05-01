import os
import json
import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from mcp.server.fastmcp import FastMCP
import chromadb
from openai import OpenAI
import google.generativeai as genai
import anthropic
from dotenv import load_dotenv
import httpx

# Database Drivers
import psycopg2
import mysql.connector
import oracledb

# Carrega variáveis de ambiente
load_dotenv()

# Configuração de Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configurações de IA ---
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai").lower()
AI_API_KEY = os.getenv("AI_API_KEY", "sua-chave-aqui")

class AIOrchestrator:
    """Orquestrador para múltiplos provedores de IA."""

    @staticmethod
    def get_response(prompt: str, system_prompt: str) -> str:
        if AI_API_KEY == "sua-chave-aqui" or AI_API_KEY.startswith("sk-dummy"):
            return f"[MOCK] Resposta baseada no provedor {AI_PROVIDER}. Pergunta: {prompt[:30]}..."

        try:
            if AI_PROVIDER == "openai":
                client = OpenAI(api_key=AI_API_KEY)
                resp = client.chat.completions.create(
                    model=os.getenv("AI_MODEL", "gpt-4o-mini"),
                    messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
                    temperature=0
                )
                return resp.choices[0].message.content

            elif AI_PROVIDER == "gemini":
                genai.configure(api_key=AI_API_KEY)
                model = genai.GenerativeModel(os.getenv("AI_MODEL", "gemini-1.5-flash"))
                resp = model.generate_content(f"{system_prompt}\n\n{prompt}")
                return resp.text

            elif AI_PROVIDER == "anthropic":
                client = anthropic.Anthropic(api_key=AI_API_KEY)
                resp = client.messages.create(
                    model=os.getenv("AI_MODEL", "claude-3-5-sonnet-20240620"),
                    system=system_prompt,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1024
                )
                return resp.content[0].text

            elif AI_PROVIDER == "ollama":
                base_url = os.getenv("AI_BASE_URL", "http://localhost:11434")
                payload = {
                    "model": os.getenv("AI_MODEL", "llama3"),
                    "prompt": f"{system_prompt}\n\n{prompt}",
                    "stream": False
                }
                with httpx.Client() as client:
                    resp = client.post(f"{base_url}/api/generate", json=payload)
                    return resp.json().get("response", "")

            elif AI_PROVIDER == "openrouter":
                base_url = "https://openrouter.ai/api/v1"
                headers = {"Authorization": f"Bearer {AI_API_KEY}"}
                payload = {
                    "model": os.getenv("AI_MODEL", "openai/gpt-3.5-turbo"),
                    "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}]
                }
                with httpx.Client() as client:
                    resp = client.post(f"{base_url}/chat/completions", headers=headers, json=payload)
                    return resp.json()['choices'][0]['message']['content']

            else:
                raise ValueError(f"Provedor de IA desconhecido: {AI_PROVIDER}")
        except Exception as e:
            logger.error(f"Erro no provedor {AI_PROVIDER}: {e}")
            raise HTTPException(status_code=500, detail="Erro ao processar com o provedor de IA.")

# --- Gerenciador de Banco de Dados Relacional ---
class DatabaseManager:
    @staticmethod
    def query_db(query: str):
        db_type = os.getenv("DB_TYPE", "mock").lower()

        if db_type == "mock":
            return "Resultado mock do banco de dados relacional."

        try:
            if db_type == "postgres":
                conn = psycopg2.connect(os.getenv("DATABASE_URL"))
                cur = conn.cursor(); cur.execute(query); res = cur.fetchall(); cur.close(); conn.close()
                return str(res)
            elif db_type == "mysql":
                conn = mysql.connector.connect(
                    host=os.getenv("DB_HOST"), user=os.getenv("DB_USER"),
                    password=os.getenv("DB_PASS"), database=os.getenv("DB_NAME")
                )
                cur = conn.cursor(); cur.execute(query); res = cur.fetchall(); cur.close(); conn.close()
                return str(res)
            elif db_type == "oracle":
                conn = oracledb.connect(user=os.getenv("DB_USER"), password=os.getenv("DB_PASS"), dsn=os.getenv("DB_DSN"))
                cur = conn.cursor(); cur.execute(query); res = cur.fetchall(); cur.close(); conn.close()
                return str(res)
            else:
                return "Tipo de banco não suportado."
        except Exception as e:
            logger.error(f"Erro no banco {db_type}: {e}")
            return f"Erro ao acessar banco de dados: {str(e)}"

# --- Banco de Dados Vetorial ---
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection(name="conhecimento_institucional")

if collection.count() == 0:
    collection.add(
        documents=[
            "A Instituição foi fundada em 1990.",
            "Horário: Segunda a Sexta, 08h às 20h.",
            "Cursos: Ciência de Dados, IA, Software.",
            "Local: Av. Paulista, 1000, SP."
        ],
        ids=["d1", "d2", "d3", "d4"]
    )

# --- MCP Server ---
mcp = FastMCP("AssistenteInstitucional")

@mcp.tool()
def buscar_informacao_institucional(query: str) -> str:
    """Busca no banco vetorial (RAG)."""
    results = collection.query(query_texts=[query], n_results=3)
    docs = results.get('documents', [[]])[0]
    distances = results.get('distances', [[]])[0]
    filtered = [d for d, dist in zip(docs, distances) if dist < 1.5]
    return "\n".join(filtered) if filtered else "Nenhuma informação encontrada."

@mcp.tool()
def buscar_dados_relacionais(sql_query: str) -> str:
    """Busca informações em bancos SQL (Postgres, MySQL, Oracle)."""
    return DatabaseManager.query_db(sql_query)

# --- FastAPI ---
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class ChatRequest(BaseModel): message: str
class ChatResponse(BaseModel): response: str

SYSTEM_PROMPT = """Você é um assistente institucional. Responda apenas com o contexto fornecido.
Se não souber, diga: 'Desculpe, não tenho essa informação na minha base de dados.'"""

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # RAG Híbrido: Vetorial + Relacional (Opcional)
    contexto_vetorial = buscar_informacao_institucional(request.message)

    # Exemplo: Se a pergunta for sobre dados estruturados (ex: 'quantos alunos'),
    # o agente poderia decidir usar buscar_dados_relacionais via MCP.
    # Aqui simulamos uma orquestração simples.
    contexto_total = f"Contexto Vetorial: {contexto_vetorial}"

    resposta = AIOrchestrator.get_response(request.message + f"\nContexto: {contexto_total}", SYSTEM_PROMPT)
    return ChatResponse(response=resposta)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
