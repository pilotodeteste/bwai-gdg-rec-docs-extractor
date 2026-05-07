import hmac
import hashlib
import time
import logging
from typing import Dict, Optional
from fastapi import Header, HTTPException
from app.core import settings

logger = logging.getLogger(__name__)

def generate_security_headers(timestamp: int, nonce: str) -> Dict[str, str]:
    message = f"{timestamp}:{nonce}"
    signature = hmac.new(
        settings.API_COMMUNICATION_TOKEN.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return {
        "X-Internal-Token": settings.API_COMMUNICATION_TOKEN,
        "X-Timestamp": str(timestamp),
        "X-Nonce": nonce,
        "X-Signature": signature,
        "X-Source": "bwai-test-api",
        "Content-Type": "application/json"
    }

async def validate_internal_request(
    x_internal_token: str = Header(..., alias="X-Internal-Token"),
    x_timestamp: str = Header(..., alias="X-Timestamp"),
    x_nonce: str = Header(..., alias="X-Nonce"),
    x_signature: str = Header(..., alias="X-Signature"),
    x_source: Optional[str] = Header(None, alias="X-Source")
) -> bool:
    try:
        if x_internal_token != settings.API_COMMUNICATION_TOKEN:
            logger.warning("Token interno inválido recebido")
            raise HTTPException(
                status_code=401, 
                detail="Invalid authentication token"
            )
        
        current_timestamp = int(time.time() * 1000)
        request_timestamp = int(x_timestamp)
        time_difference = abs(current_timestamp - request_timestamp)
        
        if time_difference > 300000:
            logger.warning(f"Timestamp fora da janela válida: {time_difference}ms")
            raise HTTPException(
                status_code=401,
                detail="Request timestamp is too old or in the future"
            )
        
        expected_message = f"{x_timestamp}:{x_nonce}"
        expected_signature = hmac.new(
            settings.API_COMMUNICATION_TOKEN.encode(),
            expected_message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(x_signature, expected_signature):
            logger.warning("Validação de assinatura HMAC falhou")
            raise HTTPException(
                status_code=401,
                detail="Invalid request signature"
            )
        
        if x_source and x_source != "bwai-test-api":
            logger.warning(f"Header de origem inesperado: {x_source}")
            raise HTTPException(
                status_code=401,
                detail="Invalid request source"
            )
        
        return True
        
    except ValueError as e:
        logger.error(f"Erro de validação: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid request format: {str(e)}"
        )
