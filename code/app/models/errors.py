from typing import Optional

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
