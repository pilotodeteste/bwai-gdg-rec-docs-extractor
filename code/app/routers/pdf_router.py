from fastapi import APIRouter, HTTPException, UploadFile, File
import logging
import uuid

from app.models.schemas import FinancialDocumentData, BankReceiptData
from app.services.financial_document_service import financial_document_service
from app.models.errors import (
    PDFReadError,
    AIAPIError,
    JSONExtractionError,
    DataValidationError,
    ProcessingError,
)
from app.core.error_handlers import handle_processing_error, handle_unexpected_error

logger = logging.getLogger(__name__)

pdf_router = APIRouter(tags=["PDF Processing"])


def _ensure_pdf(file: UploadFile) -> None:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Apenas arquivos PDF são permitidos",
        )


@pdf_router.post("/process-nota", response_model=FinancialDocumentData)
async def process_nota(file: UploadFile = File(...)):
    request_id = str(uuid.uuid4())
    _ensure_pdf(file)

    logger.info(f"[{request_id}] Processando NOTA: {file.filename}")

    try:
        content = await file.read()
        return financial_document_service.process_pdf_bytes(
            content,
            file.filename,
            document_type="nota",
        )
    except (
        PDFReadError,
        AIAPIError,
        JSONExtractionError,
        DataValidationError,
        ProcessingError,
    ) as e:
        raise handle_processing_error(e, request_id)
    except Exception as e:
        raise handle_unexpected_error(e, request_id)


@pdf_router.post("/process-fatura", response_model=FinancialDocumentData)
async def process_fatura(file: UploadFile = File(...)):
    request_id = str(uuid.uuid4())
    _ensure_pdf(file)

    logger.info(f"[{request_id}] Processando FATURA: {file.filename}")

    try:
        content = await file.read()
        return financial_document_service.process_pdf_bytes(
            content,
            file.filename,
            document_type="fatura",
        )
    except (
        PDFReadError,
        AIAPIError,
        JSONExtractionError,
        DataValidationError,
        ProcessingError,
    ) as e:
        raise handle_processing_error(e, request_id)
    except Exception as e:
        raise handle_unexpected_error(e, request_id)


@pdf_router.post("/process-comprovante-bancario", response_model=BankReceiptData)
async def process_comprovante_bancario(file: UploadFile = File(...)):
    request_id = str(uuid.uuid4())
    _ensure_pdf(file)

    logger.info(f"[{request_id}] Processando COMPROVANTE BANCÁRIO: {file.filename}")

    try:
        content = await file.read()
        return financial_document_service.process_pdf_bytes(
            content,
            file.filename,
            document_type="comprovante_bancario",
        )
    except (
        PDFReadError,
        AIAPIError,
        JSONExtractionError,
        DataValidationError,
        ProcessingError,
    ) as e:
        raise handle_processing_error(e, request_id)
    except Exception as e:
        raise handle_unexpected_error(e, request_id)


@pdf_router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "API de processamento de documentos operacional",
        "endpoints": {
            "POST /process-nota": "Processa nota e retorna JSON extraído",
            "POST /process-fatura": "Processa fatura e retorna JSON extraído",
            "POST /process-comprovante-bancario": "Processa comprovante bancário e retorna JSON extraído",
            "GET /health": "Verificação de saúde da API",
        },
    }
