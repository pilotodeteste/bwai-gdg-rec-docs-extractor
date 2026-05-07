from typing import Protocol, Dict, Any, Optional, List


class AIClientProtocol(Protocol):
    
    def converse(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int = 4096,
        temperature: float = 0.0
    ) -> Dict[str, Any]:
        ...
    
    def extract_json_from_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        ...
    
    def prepare_document_message(
        self,
        doc_bytes: bytes,
        prompt: str,
        doc_name: str = "Document"
    ) -> Dict[str, Any]:
        ...

