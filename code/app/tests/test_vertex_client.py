from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from app.clients.vertex_client import VertexClient
from app.core import settings


class TestVertexClientInit:

    @patch("app.clients.vertex_client.genai.Client")
    def test_init_success(self, mock_genai_client):
        with patch.object(settings, "GCP_PROJECT_ID", "my-project"), patch.object(settings, "GCP_LOCATION", "global"), patch.object(settings, "VERTEX_MODEL_ID", "gemini-3-flash-preview"):
            client = VertexClient()

        assert client.client == mock_genai_client.return_value
        assert client.model_id == "gemini-3-flash-preview"

    @patch("app.clients.vertex_client.genai.Client")
    def test_init_without_project(self, _):
        with patch.object(settings, "GCP_PROJECT_ID", ""), patch.object(settings, "GCP_LOCATION", "global"):
            client = VertexClient()

        assert client.client is None


class TestExtractJsonFromResponse:

    @pytest.fixture
    def client(self):
        with patch.object(settings, "GCP_PROJECT_ID", "my-project"), patch("app.clients.vertex_client.genai.Client"):
            return VertexClient()

    def test_extract_simple_json(self, client):
        response = '{"name": "Produto", "value": 42}'
        result = client.extract_json_from_response(response)
        assert result == {"name": "Produto", "value": 42}

    def test_extract_json_with_surrounding_text(self, client):
        response = 'Aqui está o resultado: {"name": "Produto"} finalizado'
        result = client.extract_json_from_response(response)
        assert result == {"name": "Produto"}

    def test_extract_invalid_json(self, client):
        response = '{"name": "Produto", invalid}'
        result = client.extract_json_from_response(response)
        assert result is None


class TestPrepareDocumentMessage:

    @pytest.fixture
    def client(self):
        with patch.object(settings, "GCP_PROJECT_ID", "my-project"), patch("app.clients.vertex_client.genai.Client"):
            return VertexClient()

    def test_prepare_basic_message(self, client):
        doc_bytes = b"PDF content here"
        prompt = "Extraia os dados"

        result = client.prepare_document_message(doc_bytes, prompt, "teste")

        assert "contents" in result
        assert len(result["contents"]) == 2
        assert result["contents"][1] == prompt


class TestConverse:

    @pytest.fixture
    def client(self):
        with patch.object(settings, "GCP_PROJECT_ID", "my-project"), patch.object(settings, "GCP_LOCATION", "global"), patch.object(settings, "VERTEX_MODEL_ID", "gemini-3-flash-preview"), patch("app.clients.vertex_client.genai.Client") as mock_genai_client:
            client = VertexClient()
            client.client = mock_genai_client.return_value
            return client

    def test_converse_success(self, client):
        mock_response = SimpleNamespace(text='{"name":"Produto"}')
        client.client.models.generate_content = Mock(return_value=mock_response)

        messages = [{"contents": ["pdf_part", "Teste"]}]
        result = client.converse(messages)

        assert result["output"]["message"]["content"][0]["text"] == '{"name":"Produto"}'
        client.client.models.generate_content.assert_called_once()

    def test_converse_without_project_config(self):
        with patch.object(settings, "GCP_PROJECT_ID", ""), patch("app.clients.vertex_client.genai.Client"):
            client = VertexClient()

        with pytest.raises(Exception) as exc_info:
            client.converse([{"contents": ["pdf_part", "Teste"]}])

        assert "Projeto GCP não configurado" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
