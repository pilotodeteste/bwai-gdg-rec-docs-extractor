from fastapi import FastAPI
import uvicorn
from app.core import settings
from app.routers.pdf_router import pdf_router
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION
)

app.include_router(pdf_router)

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("BWAI Test API Iniciando")
    logger.info(f"Projeto GCP: {settings.GCP_PROJECT_ID or 'Não configurado'}")
    logger.info(f"Região GCP: {settings.GCP_LOCATION}")
    logger.info(f"Modelo Vertex: {settings.VERTEX_MODEL_ID}")
    logger.info("=" * 60)

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("BWAI Test API Encerrando")

if __name__ == "__main__":
    print("Iniciando API de Processamento de Documentos...")
    print(f"Documentacao disponivel em: http://{settings.HOST}:{settings.PORT}/docs")
    print("Endpoints disponiveis:")
    print("  POST /process-nota - Processa nota e retorna JSON extraído")
    print("  POST /process-fatura - Processa fatura e retorna JSON extraído")
    print("  POST /process-comprovante-bancario - Processa comprovante bancário e retorna JSON extraído")
    print("  GET  /health - Verificacao de saude da API")
    
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
