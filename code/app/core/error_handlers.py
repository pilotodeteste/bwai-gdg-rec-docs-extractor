import logging
from typing import Dict, Type
from fastapi import HTTPException, status

from app.models.errors import (
    ProcessingError,
    PDFReadError,
    AIAPIError,
    JSONExtractionError,
    DataValidationError,
)
from app.core.enums import ErrorCode

logger = logging.getLogger(__name__)


ERROR_MAPPING: Dict[Type[Exception], tuple] = {
    PDFReadError: (status.HTTP_400_BAD_REQUEST, ErrorCode.PDF_READ_ERROR),
    AIAPIError: (status.HTTP_503_SERVICE_UNAVAILABLE, ErrorCode.AI_API_ERROR),
    JSONExtractionError: (status.HTTP_422_UNPROCESSABLE_ENTITY, ErrorCode.JSON_EXTRACTION_ERROR),
    DataValidationError: (status.HTTP_422_UNPROCESSABLE_ENTITY, ErrorCode.DATA_VALIDATION_ERROR),
    ProcessingError: (status.HTTP_500_INTERNAL_SERVER_ERROR, ErrorCode.PROCESSING_ERROR),
}

ERROR_MESSAGES: Dict[Type[Exception], str] = {
    PDFReadError: "Erro ao ler arquivo PDF",
    AIAPIError: "Erro no serviço de processamento",
    JSONExtractionError: "Não foi possível extrair dados do PDF",
    DataValidationError: "Dados extraídos são inválidos",
    ProcessingError: "Erro no processamento",
}


def handle_processing_error(error: Exception, request_id: str) -> HTTPException:
    error_type = type(error)
    
    status_code, error_code = ERROR_MAPPING.get(
        error_type,
        (status.HTTP_500_INTERNAL_SERVER_ERROR, ErrorCode.UNKNOWN_ERROR)
    )
    
    base_message = ERROR_MESSAGES.get(error_type, "Erro interno")
    
    if isinstance(error, ProcessingError):
        detail = f"{base_message}: {error.message}"
        if error.details:
            detail += f". {error.details}"
    else:
        detail = f"{base_message}: {str(error)}"
    
    logger.error(f"[{request_id}] {error_code.value}: {detail}")
    
    return HTTPException(
        status_code=status_code,
        detail=detail
    )


def handle_unexpected_error(error: Exception, request_id: str) -> HTTPException:
    logger.exception(f"[{request_id}] Erro inesperado: {error}")
    
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Erro interno no processamento: {str(error)}"
    )
