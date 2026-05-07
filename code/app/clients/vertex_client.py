import json
import logging
import re
from typing import Optional, Dict, Any, List

from google import genai
from google.genai import types

from app.core import settings

logger = logging.getLogger(__name__)


class VertexClient:

    def __init__(self):
        self.model_id = settings.VERTEX_MODEL_ID
        self.project_id = settings.GCP_PROJECT_ID
        self.location = settings.GCP_LOCATION
        self.client = None

        if self.project_id:
            self.client = genai.Client(
                vertexai=True,
                project=self.project_id,
                location=self.location,
                http_options=types.HttpOptions(api_version="v1"),
            )

    def converse(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        try:
            if not self.client:
                raise ValueError(
                    "Projeto GCP não configurado. Defina GOOGLE_CLOUD_PROJECT antes de iniciar a API."
                )

            if not messages:
                raise ValueError("Lista de mensagens vazia")

            first_message = messages[0]
            contents = first_message.get("contents")

            if not contents:
                raise ValueError("Mensagem inválida para envio ao Vertex AI")

            response = self.client.models.generate_content(
                model=self.model_id,
                contents=contents,
                config=types.GenerateContentConfig(
                    max_output_tokens=max_tokens,
                    temperature=temperature,
                    response_mime_type="application/json",
                ),
            )

            response_text = response.text
            if not response_text:
                response_text = self._extract_text_from_candidates(response)

            return {
                "output": {
                    "message": {
                        "content": [{"text": response_text or ""}]
                    }
                }
            }
        except Exception as e:
            raise Exception(
                f"Erro ao comunicar com Vertex AI ({self.model_id}): {str(e)}"
            ) from e

    def _extract_text_from_candidates(self, response: Any) -> str:
        candidates = getattr(response, "candidates", None) or []

        text_parts = []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            if not content:
                continue

            parts = getattr(content, "parts", None) or []
            for part in parts:
                part_text = getattr(part, "text", None)
                if part_text:
                    text_parts.append(part_text)

        return "\n".join(text_parts).strip()

    def extract_json_from_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        logger.debug("Extraindo JSON da resposta...")

        def clean_json_text(content: str) -> str:
            content = re.sub(r"[\u0000-\u001f\u007f-\u009f]", "", content)
            content = re.sub(r"\s+", " ", content)
            return content.strip()

        try:
            match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if not match:
                logger.error("Nenhum JSON válido encontrado na resposta")
                logger.debug(f"Resposta recebida: {response_text[:200]}...")
                return None

            json_str = clean_json_text(match.group(0))

            try:
                extracted_data = json.loads(json_str)
                return extracted_data
            except json.JSONDecodeError:
                json_str = re.sub(r"[^\x20-\x7E]", " ", json_str)
                json_str = re.sub(r"\s+", " ", json_str)
                extracted_data = json.loads(json_str)
                return extracted_data

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Erro ao decodificar JSON: {e}")
            logger.debug(f"Resposta bruta recebida: {response_text[:500]}...")
            return None

    def prepare_document_message(
        self,
        doc_bytes: bytes,
        prompt: str,
        doc_name: str = "Document",
    ) -> Dict[str, Any]:
        _ = doc_name

        pdf_part = types.Part.from_bytes(
            data=doc_bytes,
            mime_type="application/pdf",
        )

        return {
            "contents": [
                pdf_part,
                prompt,
            ]
        }


vertex_client = VertexClient()
