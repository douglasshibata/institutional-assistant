import os
import pytest
import requests_mock
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from institutional_agent import (
    consultar_base_institucional,
    institutional_agent,
    MockAgentLLM
)

def test_consultar_base_institucional_success():
    """Test that the WeKnora RAG tool successfully parses and formats results."""
    mock_url = "http://localhost:8000/api/v1/chat/completions"

    mock_response_data = {
        "results": [
            {
                "text": "O ressarcimento de transporte deve ser solicitado via SEI.",
                "metadata": {
                    "source_file": "Portaria_123.pdf",
                    "page": "12"
                }
            },
            {
                "text": "O valor máximo diário é de R$ 50,00.",
                "metadata": {
                    "source_file": "Instrucao_Normativa_04.pdf",
                    "page": "3"
                }
            }
        ]
    }

    with requests_mock.Mocker() as m:
        m.post(mock_url, json=mock_response_data)

        # Invoke the tool directly
        result = consultar_base_institucional.invoke({"query": "transporte"})

        assert "Portaria_123.pdf" in result
        assert "Pág. 12" in result
        assert "Instrucao_Normativa_04.pdf" in result
        assert "Pág. 3" in result
        assert "O ressarcimento de transporte deve ser solicitado via SEI." in result

def test_consultar_base_institucional_no_results():
    """Test the tool behavior when no results are found."""
    mock_url = "http://localhost:8000/api/v1/chat/completions"
    mock_response_data = {"results": []}

    with requests_mock.Mocker() as m:
        m.post(mock_url, json=mock_response_data)

        result = consultar_base_institucional.invoke({"query": "algo inexistente"})
        assert result == "Nenhuma informação institucional relevante foi encontrada para esta dúvida."

def test_consultar_base_institucional_exception():
    """Test tool resilience against HTTP errors or network timeouts."""
    mock_url = "http://localhost:8000/api/v1/chat/completions"

    with requests_mock.Mocker() as m:
        m.post(mock_url, status_code=500)

        result = consultar_base_institucional.invoke({"query": "erro"})
        assert "Erro ao comunicar com a base de conhecimento institucional" in result

def test_mock_agent_llm_behavior():
    """Test the custom MockAgentLLM logic for tool calls and final responses."""
    llm = MockAgentLLM()

    # First turn: no tool message in history
    messages = [HumanMessage(content="Como solicito reembolso?")]
    res = llm.invoke(messages)

    # Should trigger tool call
    assert isinstance(res, AIMessage)
    assert len(res.tool_calls) == 1
    assert res.tool_calls[0]["name"] == "consultar_base_institucional"

    # Second turn: tool response in history
    messages = [
        HumanMessage(content="Como solicito reembolso?"),
        AIMessage(content="", tool_calls=[{"name": "consultar_base_institucional", "args": {"query": "Como solicito reembolso?"}, "id": "call_1"}]),
        ToolMessage(content="Use o formulário SEI para transporte.", name="consultar_base_institucional", tool_call_id="call_1")
    ]

    res2 = llm.invoke(messages)
    assert isinstance(res2, AIMessage)
    assert "De acordo com a base de conhecimento consultada" in res2.content
    assert "Use o formulário SEI para transporte" in res2.content

def test_agent_integration_with_mock_llm():
    """Test the end-to-end React Agent flow utilizing MockAgentLLM and Mock WeKnora API."""
    mock_url = "http://localhost:8000/api/v1/chat/completions"
    mock_response_data = {
        "results": [
            {
                "text": "Procedimento de reembolso de transporte: anexar comprovantes.",
                "metadata": {
                    "source_file": "Guia_Reembolso.pdf",
                    "page": "5"
                }
            }
        ]
    }

    with requests_mock.Mocker() as m:
        m.post(mock_url, json=mock_response_data)

        inputs = {"messages": [("user", "Qual o procedimento para ressarcimento?")]}
        outputs = institutional_agent.invoke(inputs)

        messages = outputs["messages"]
        # Ensure there are human, AI with tool call, Tool, and final AI messages
        assert len(messages) >= 4

        # Check that we invoked the tool
        tool_called = any(
            msg.type == "tool" and "Guia_Reembolso.pdf" in msg.content
            for msg in messages
        )
        assert tool_called, "Tool was not called or results were not passed correctly."

        # Check that the final answer is present and grounded
        final_msg = messages[-1]
        assert final_msg.type == "ai"
        assert "De acordo com a base de conhecimento consultada" in final_msg.content
        assert "Procedimento de reembolso de transporte" in final_msg.content
