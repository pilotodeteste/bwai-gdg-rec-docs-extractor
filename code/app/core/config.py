import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT / ".env.local", override=True)


class Settings:
    GCP_PROJECT_ID: str = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    GCP_LOCATION: str = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
    VERTEX_MODEL_ID: str = os.getenv("VERTEX_MODEL_ID", "gemini-3-flash-preview")

    API_TITLE: str = "API de Processamento de Documentos"
    API_DESCRIPTION: str = "API para processar documentos PDF (nota e fatura) usando Vertex AI"
    API_VERSION: str = "2.0.0"

    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    API_COMMUNICATION_TOKEN: str = os.getenv("API_COMMUNICATION_TOKEN", "")
    PUBLIC_API_URL: str = os.getenv("PUBLIC_API_URL", "http://localhost:3000")
    CALLBACK_ENDPOINT: str = (
        f"{os.getenv('PUBLIC_API_URL', 'http://localhost:3000')}/ai-integration/webhook/callback"
    )

settings = Settings()
