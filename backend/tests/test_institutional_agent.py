import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Ensure the backend directory is in the sys.path so we can import server and institutional_agent
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import app
from institutional_agent import (
    consultar_base_institucional,
    get_agent_response,
    get_agent_response_async,
    MockAgentLLM
)

@pytest.fixture
def client():
    return TestClient(app)

def test_consultar_base_institucional_success():
    """Testa se a ferramenta de consulta retorna corretamente as informações formatadas."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {
                "text": "O ressarcimento de transporte deve ser solicitado via portal interno.",
                "metadata": {
                    "source_file": "manual_transporte.pdf",
                    "page": 5
                }
            }
        ]
    }

    with patch("requests.post", return_value=mock_response):
        result = consultar_base_institucional.invoke("ressarcimento transporte")
        assert "manual_transporte.pdf" in result
        assert "Pág. 5" in result
        assert "O ressarcimento de transporte deve ser solicitado via portal interno." in result

def test_consultar_base_institucional_no_results():
    """Testa o comportamento quando a consulta não retorna resultados."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": []}

    with patch("requests.post", return_value=mock_response):
        result = consultar_base_institucional.invoke("termo inexistente")
        assert "Nenhuma informação institucional" in result

def test_consultar_base_institucional_exception():
    """Testa se exceções na consulta são tratadas corretamente."""
    with patch("requests.post", side_effect=Exception("Erro de conexão")):
        result = consultar_base_institucional.invoke("qualquer consulta")
        assert "Erro ao comunicar com a base de conhecimento" in result

def test_get_agent_response_mock():
    """Testa a geração síncrona da resposta utilizando o MockAgentLLM."""
    with patch.dict(os.environ, {"MOCK_AGENT": "true"}):
        resposta = get_agent_response("Qual o horário de funcionamento?")
        assert "[MOCK]" in resposta
        assert "Resposta oficial da Instituição." in resposta

@pytest.mark.asyncio
async def test_get_agent_response_async_mock():
    """Testa a geração assíncrona da resposta utilizando o MockAgentLLM."""
    with patch.dict(os.environ, {"MOCK_AGENT": "true"}):
        resposta = await get_agent_response_async("Qual o horário de funcionamento?")
        assert "[MOCK]" in resposta
        assert "Resposta oficial da Instituição." in resposta

def test_chat_endpoint_weknora(client):
    """Testa se o endpoint do FastAPI utiliza o agente WeKnora quando configurado."""
    with patch.dict(os.environ, {"USE_WEKNORA_AGENT": "true", "MOCK_AGENT": "true"}):
        response = client.post("/api/chat", json={"message": "Qual é a paulista?"})
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "[MOCK]" in data["response"]

def test_chat_endpoint_chroma_fallback(client):
    """Testa o fallback para o ChromaDB original quando USE_WEKNORA_AGENT=false."""
    with patch.dict(os.environ, {"USE_WEKNORA_AGENT": "false"}):
        # Como o Chroma está em modo mock com FakeEmbeddings na inicialização do server,
        # ele retornará a resposta baseada no mock do LLM original.
        response = client.post("/api/chat", json={"message": "Qual é o campus?"})
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "[LANGCHAIN MOCK]" in data["response"]
