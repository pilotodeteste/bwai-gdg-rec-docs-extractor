from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class ErrorDetail(BaseModel):
    code: str = Field(..., description="Código do erro")
    message: str = Field(..., description="Mensagem de erro")
    details: Optional[str] = Field(None, description="Detalhes adicionais")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ErrorResponse(BaseModel):
    error: ErrorDetail = Field(..., description="Detalhes do erro")
    request_id: Optional[str] = Field(None, description="ID da requisição para rastreamento")


class ValidationError(BaseModel):
    field: str = Field(..., description="Campo com erro")
    message: str = Field(..., description="Mensagem de erro")
    value: Optional[Any] = Field(None, description="Valor que causou o erro")

class ProcessingError(Exception):
    def __init__(self, message: str, details: Optional[str] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)

class PDFReadError(ProcessingError):
    pass

class AIAPIError(ProcessingError):
    pass

class JSONExtractionError(ProcessingError):
    pass

class DataValidationError(ProcessingError):
    pass
