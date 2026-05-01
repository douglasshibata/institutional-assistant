import os
import json
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from mcp.server.fastmcp import FastMCP
import chromadb
from openai import OpenAI
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# --- Configurações ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sua-chave-aqui")
client = OpenAI(api_key=OPENAI_API_KEY)

# --- Banco de Dados Vetorial (ChromaDB) ---
# Inicialização em memória para demonstração
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection(name="conhecimento_institucional")

# Populando o banco com informações de exemplo
if collection.count() == 0:
    collection.add(
        documents=[
            "A Instituição de Tecnologia Avançada foi fundada em 1990 e é líder em educação digital.",
            "O horário de atendimento presencial é de segunda a sexta, das 08:00 às 20:00.",
            "Oferecemos cursos de graduação em Ciência de Dados, Engenharia de Software e IA.",
            "O campus principal está localizado na Avenida Paulista, 1000, São Paulo - SP.",
            "Para suporte técnico, os alunos devem enviar um e-mail para suporte@instituicao.edu.br.",
            "A biblioteca funciona aos sábados das 09:00 às 13:00."
        ],
        metadatas=[{"source": "historia"}, {"source": "horarios"}, {"source": "cursos"}, {"source": "localizacao"}, {"source": "contato"}, {"source": "biblioteca"}],
        ids=["doc1", "doc2", "doc3", "doc4", "doc5", "doc6"]
    )

# --- MCP Server Setup ---
# O servidor MCP expõe ferramentas que podem ser usadas por agentes de IA
mcp = FastMCP("AssistenteInstitucional")

@mcp.tool()
def buscar_informacao_institucional(query: str) -> str:
    """
    Busca informações relevantes na base de dados de conhecimento da instituição
    usando busca vetorial (RAG).
    """
    results = collection.query(
        query_texts=[query],
        n_results=3
    )

    # ChromaDB retorna resultados baseados em distância.
    # Para garantir o comportamento "estritamente restrito", podemos filtrar por distância se necessário.
    docs = results.get('documents', [[]])[0]
    distances = results.get('distances', [[]])[0]

    filtered_docs = []
    for doc, dist in zip(docs, distances):
        # Limiar empírico para ChromaDB (L2 distance padrão)
        if dist < 1.5:
            filtered_docs.append(doc)

    if not filtered_docs:
        return "Nenhuma informação relevante encontrada na base de dados."

    return "\n".join(filtered_docs)

# --- FastAPI Application ---
# Interface Web para o Frontend interagir com o Agente/MCP
app = FastAPI(title="Institutional Assistant API")

# Habilita CORS para permitir requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

# Prompt de Sistema Rígido para evitar alucinações
SYSTEM_PROMPT = """Você é um assistente virtual oficial da Instituição.
Sua missão é ajudar os usuários com informações baseadas estritamente no contexto fornecido.

REGRAS CRÍTICAS:
1. Responda APENAS usando as informações encontradas no contexto fornecido pela ferramenta de busca.
2. Se a informação não estiver presente no contexto, responda exatamente: 'Desculpe, não tenho essa informação na minha base de dados.'
3. Não utilize conhecimentos externos ou invente fatos.
4. Mantenha um tom profissional, prestativo e cordial."""

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint principal que orquestra a lógica RAG:
    1. Recebe a pergunta do usuário.
    2. Usa a ferramenta MCP para buscar contexto no banco vetorial.
    3. Envia a pergunta + contexto para o LLM com o System Prompt rígido.
    """
    user_message = request.message

    try:
        # Busca contexto relevante (RAG) - Chamada interna da ferramenta MCP
        contexto = buscar_informacao_institucional(user_message)

        # Orquestração com OpenAI (ou Mock para testes)
        if OPENAI_API_KEY.startswith("sk-dummy") or OPENAI_API_KEY == "sua-chave-aqui":
            # Resposta Mock para quando não há chave real configurada
            if "Nenhuma informação relevante" in contexto:
                resposta_final = "Desculpe, não tenho essa informação na minha base de dados."
            else:
                resposta_final = f"[MOCK RESPONSE] Baseado no contexto: {contexto[:100]}..."
        else:
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Contexto institucional:\n{contexto}\n\nPergunta do usuário: {user_message}"}
                ],
                temperature=0  # Reduz variabilidade e risco de alucinação
            )
            resposta_final = completion.choices[0].message.content

        return ChatResponse(response=resposta_final)

    except Exception as e:
        print(f"Erro no processamento: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao processar sua solicitação.")

if __name__ == "__main__":
    import uvicorn
    # Inicia o servidor FastAPI na porta 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
