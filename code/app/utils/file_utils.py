import os
import tempfile
import logging
from typing import Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class TempFileManager:

    def __init__(self, suffix: str = '.pdf'):
        self.suffix = suffix
        self.temp_path: str | None = None
    
    def create_from_bytes(self, content: bytes) -> str:
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=self.suffix)
            temp_file.write(content)
            temp_file.flush()
            self.temp_path = temp_file.name
            temp_file.close()
            
            logger.info(f"Arquivo temporário criado: {self.temp_path}")
            return self.temp_path
            
        except Exception as e:
            logger.error(f"Erro ao criar arquivo temporário: {e}")
            raise
    
    def cleanup(self):
        if self.temp_path and os.path.exists(self.temp_path):
            try:
                os.unlink(self.temp_path)
                logger.info(f"Arquivo temporário removido: {self.temp_path}")
            except Exception as e:
                logger.warning(f"Erro ao remover arquivo temporário: {e}")
            finally:
                self.temp_path = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


def validate_pdf_file(filename: str) -> Tuple[bool, str]:
    if not filename:
        return False, "Nome do arquivo não fornecido"
    
    if not filename.lower().endswith('.pdf'):
        return False, "Apenas arquivos PDF são aceitos"
    
    invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
    if any(char in filename for char in invalid_chars):
        return False, "Nome do arquivo contém caracteres inválidos"
    
    return True, ""


def sanitize_filename(filename: str) -> str:
    name_without_ext = Path(filename).stem
    
    sanitized = name_without_ext.replace(' ', '_')
    sanitized = ''.join(c for c in sanitized if c.isalnum() or c in ('-', '_'))
    
    return sanitized if sanitized else "document"
