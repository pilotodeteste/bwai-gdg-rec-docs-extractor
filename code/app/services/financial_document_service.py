import os
import logging
import re
from typing import Optional, Dict, Any, List

from app.models.schemas import FinancialDocumentData, FinancialLineItem, BankReceiptData
from app.models.errors import (
    PDFReadError,
    AIAPIError,
    JSONExtractionError,
    DataValidationError,
    ProcessingError,
)
from app.clients.base import AIClientProtocol
from app.clients import vertex_client
from app.prompts import (
    get_standard_nota_prompt,
    get_standard_fatura_prompt,
    get_standard_comprovante_bancario_prompt,
)

logger = logging.getLogger(__name__)


class FinancialDocumentService:

    def __init__(self, ai_client: Optional[AIClientProtocol] = None):
        self._client = ai_client or vertex_client

    def _read_pdf_file(
        self,
        pdf_path: Optional[str] = None,
        pdf_bytes: Optional[bytes] = None,
    ) -> bytes:
        if pdf_bytes is not None:
            if not pdf_bytes:
                raise PDFReadError(
                    "Arquivo PDF está vazio",
                    details="Bytes fornecidos estão vazios",
                )
            return pdf_bytes

        if not pdf_path:
            raise PDFReadError(
                "Nenhum arquivo fornecido",
                details="Forneça pdf_path ou pdf_bytes",
            )

        if not os.path.exists(pdf_path):
            raise PDFReadError(
                f"Arquivo não encontrado: {pdf_path}",
                details="Verifique se o caminho está correto",
            )

        if not os.path.isfile(pdf_path):
            raise PDFReadError(
                f"Caminho não é um arquivo: {pdf_path}",
                details="O caminho fornecido aponta para um diretório",
            )

        try:
            with open(pdf_path, "rb") as doc_file:
                doc_bytes = doc_file.read()

            if not doc_bytes:
                raise PDFReadError(
                    "Arquivo PDF está vazio",
                    details=f"Arquivo: {pdf_path}",
                )

            return doc_bytes

        except (OSError, IOError) as e:
            logger.error(f"Erro ao ler arquivo {pdf_path}: {e}")
            raise PDFReadError(
                f"Erro ao ler arquivo PDF: {str(e)}",
                details=f"Arquivo: {pdf_path}",
            ) from e

    def _get_prompt(self, document_type: str) -> str:
        if document_type == "nota":
            return get_standard_nota_prompt()
        if document_type == "comprovante_bancario":
            return get_standard_comprovante_bancario_prompt()
        return get_standard_fatura_prompt()

    def _prepare_ai_message(
        self,
        doc_bytes: bytes,
        filename: str,
        document_type: str,
    ) -> Dict[str, Any]:
        prompt = self._get_prompt(document_type)
        base_name_without_ext = os.path.splitext(filename)[0]

        return self._client.prepare_document_message(
            doc_bytes=doc_bytes,
            prompt=prompt,
            doc_name=base_name_without_ext,
        )

    def _send_to_ai(self, doc_message: Dict[str, Any]) -> str:
        try:
            response = self._client.converse(messages=[doc_message])

            if not response or "output" not in response:
                raise AIAPIError(
                    "Resposta do modelo inválida",
                    details="Resposta não contém campo 'output'",
                )

            response_text = response["output"]["message"]["content"][0]["text"]

            if not response_text or not isinstance(response_text, str):
                raise AIAPIError(
                    "Resposta do modelo vazia ou inválida",
                    details="Campo 'text' ausente ou não é string",
                )

            return response_text

        except KeyError as e:
            logger.error(f"Erro ao acessar campo na resposta: {e}")
            raise AIAPIError(
                f"Estrutura de resposta inesperada: campo {str(e)} não encontrado",
                details="A resposta do modelo não está no formato esperado",
            ) from e
        except Exception as e:
            if isinstance(e, AIAPIError):
                raise
            logger.error(f"Erro ao comunicar com modelo: {e}")
            raise AIAPIError(
                f"Erro na comunicação com o modelo: {str(e)}",
                details="Verifique conectividade e credenciais GCP",
            ) from e

    def _extract_and_validate_data(self, response_text: str) -> Dict[str, Any]:
        extracted_data = self._client.extract_json_from_response(response_text)

        if not extracted_data:
            logger.error("Falha ao extrair dados JSON da resposta")
            raise JSONExtractionError(
                "Não foi possível extrair JSON válido da resposta do modelo",
                details=f"Resposta: {response_text[:200]}...",
            )

        if not isinstance(extracted_data, dict):
            raise JSONExtractionError(
                "JSON extraído não é um objeto/dicionário",
                details=f"Tipo recebido: {type(extracted_data).__name__}",
            )

        return extracted_data

    def _as_none(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, str):
            normalized = value.strip()
            if normalized.lower() in {"", "null", "n/a", "na", "não informado"}:
                return None
            return normalized
        return str(value)

    def _as_float(self, value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            s = value.strip()
            if s.lower() in {"", "null", "n/a", "na", "não informado"}:
                return None

            # Remove símbolos comuns de moeda/espaços e normaliza separadores.
            s = re.sub(r"[^\d,.-]", "", s)
            if not s:
                return None

            if s.count(",") > 0 and s.count(".") > 0:
                if s.rfind(",") > s.rfind("."):
                    s = s.replace(".", "").replace(",", ".")
                else:
                    s = s.replace(",", "")
            elif s.count(",") > 0:
                s = s.replace(",", ".")

            try:
                return float(s)
            except ValueError:
                return None

        return None

    def _normalize_items(self, raw_items: Any) -> List[FinancialLineItem]:
        if not isinstance(raw_items, list):
            return []

        items: List[FinancialLineItem] = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue

            items.append(
                FinancialLineItem(
                    description=self._as_none(item.get("description")),
                    quantity=self._as_float(item.get("quantity")),
                    unitPrice=self._as_float(item.get("unitPrice")),
                    lineTotal=self._as_float(item.get("lineTotal")),
                    taxRate=self._as_float(item.get("taxRate")),
                    sku=self._as_none(item.get("sku")),
                )
            )
        return items

    def _mask_alnum(
        self,
        value: Optional[str],
        keep_start: int = 2,
        keep_end: int = 2,
    ) -> Optional[str]:
        if value is None:
            return None

        text = str(value)
        alnum_positions = [i for i, c in enumerate(text) if c.isalnum()]
        if not alnum_positions:
            return text

        if len(alnum_positions) <= (keep_start + keep_end):
            positions_to_mask = alnum_positions
        else:
            positions_to_mask = alnum_positions[keep_start: len(alnum_positions) - keep_end]

        chars = list(text)
        for idx in positions_to_mask:
            chars[idx] = "*"
        return "".join(chars)

    def _mask_digits(self, value: Optional[str], keep_last: int = 2) -> Optional[str]:
        if value is None:
            return None

        text = str(value)
        digit_positions = [i for i, c in enumerate(text) if c.isdigit()]
        if not digit_positions:
            return text

        if len(digit_positions) <= keep_last:
            positions_to_mask = digit_positions
        else:
            positions_to_mask = digit_positions[:-keep_last]

        chars = list(text)
        for idx in positions_to_mask:
            chars[idx] = "*"
        return "".join(chars)

    def _mask_email(self, email: str) -> str:
        if "@" not in email:
            return self._mask_alnum(email, keep_start=1, keep_end=1) or email

        local, domain = email.split("@", 1)
        if len(local) <= 2:
            local_masked = "*" * len(local)
        else:
            local_masked = local[0] + ("*" * (len(local) - 2)) + local[-1]
        return f"{local_masked}@{domain}"

    def _mask_name(self, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None

        text = str(value).strip()
        if not text:
            return text

        tokens = re.split(r"(\s+)", text)
        masked_tokens: List[str] = []

        for token in tokens:
            if not token or token.isspace():
                masked_tokens.append(token)
                continue

            chars = list(token)
            alnum_positions = [i for i, c in enumerate(chars) if c.isalnum()]
            if len(alnum_positions) <= 1:
                masked_tokens.append("*" * len(token))
                continue

            for idx in alnum_positions[1:]:
                chars[idx] = "*"
            masked_tokens.append("".join(chars))

        return "".join(masked_tokens)

    def _mask_sensitive_text(self, text: Optional[str]) -> Optional[str]:
        if text is None:
            return None

        result = str(text)

        # CPF
        result = re.sub(
            r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b",
            lambda m: self._mask_digits(m.group(0), keep_last=2) or m.group(0),
            result,
        )

        # CNPJ
        result = re.sub(
            r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b",
            lambda m: self._mask_digits(m.group(0), keep_last=2) or m.group(0),
            result,
        )

        # UUID / chave aleatória
        result = re.sub(
            r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b",
            lambda m: self._mask_alnum(m.group(0), keep_start=4, keep_end=4) or m.group(0),
            result,
        )

        # E-mail (chave PIX tipo e-mail)
        result = re.sub(
            r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
            lambda m: self._mask_email(m.group(0)),
            result,
        )

        # Campo de chave/identificador após labels usuais.
        result = re.sub(
            r"(?i)(\b(?:chave(?:\s+pix)?|id(?:\s+da)?\s*transac[aã]o|autenticac[aã]o|protocolo)\b\s*[:#-]?\s*)([A-Za-z0-9@._/+:-]{5,})",
            lambda m: f"{m.group(1)}{self._mask_alnum(m.group(2), keep_start=2, keep_end=2) or m.group(2)}",
            result,
        )

        # Trecho após "Chave:" (comum em comprovante PIX com espaços/pontuação).
        result = re.sub(
            r"(?i)(chave\s*:\s*)([^\n\r;]+)",
            lambda m: f"{m.group(1)}{self._mask_alnum(m.group(2).strip(), keep_start=2, keep_end=2)}",
            result,
        )

        # Agência/conta informadas em texto livre.
        result = re.sub(
            r"(?i)\b((?:ag(?:encia)?|ag\.?|cc|c\/c|conta)\s*[:\-]?\s*)([0-9][0-9./-]{2,})",
            lambda m: f"{m.group(1)}{self._mask_digits(m.group(2), keep_last=2) or m.group(2)}",
            result,
        )

        # Sequências longas alfanuméricas (ids/chaves sem label explícito).
        result = re.sub(
            r"\b[A-Za-z0-9]{20,}\b",
            lambda m: self._mask_alnum(m.group(0), keep_start=3, keep_end=3) or m.group(0),
            result,
        )

        return result

    def _sanitize_financial_data(self, data: FinancialDocumentData) -> FinancialDocumentData:
        data.supplierTaxId = self._mask_digits(data.supplierTaxId, keep_last=2)
        data.customerTaxId = self._mask_digits(data.customerTaxId, keep_last=2)
        data.customerName = self._mask_name(data.customerName)
        data.paymentMethod = self._mask_sensitive_text(data.paymentMethod)
        data.notes = self._mask_sensitive_text(data.notes)
        return data

    def _sanitize_bank_receipt_data(self, data: BankReceiptData) -> BankReceiptData:
        data.transactionId = self._mask_alnum(data.transactionId, keep_start=4, keep_end=4)
        data.authenticationCode = self._mask_alnum(data.authenticationCode, keep_start=4, keep_end=4)
        data.payerName = self._mask_name(data.payerName)
        data.receiverName = self._mask_name(data.receiverName)
        data.payerDocument = self._mask_digits(data.payerDocument, keep_last=2)
        data.receiverDocument = self._mask_digits(data.receiverDocument, keep_last=2)
        data.payerBranch = self._mask_digits(data.payerBranch, keep_last=1)
        data.receiverBranch = self._mask_digits(data.receiverBranch, keep_last=1)
        data.payerAccount = self._mask_digits(data.payerAccount, keep_last=2)
        data.receiverAccount = self._mask_digits(data.receiverAccount, keep_last=2)
        data.description = self._mask_sensitive_text(data.description)
        data.notes = self._mask_sensitive_text(data.notes)
        return data

    def _normalize_financial_data(
        self,
        extracted_data: Dict[str, Any],
        document_type: str,
    ) -> FinancialDocumentData:
        try:
            raw_type = self._as_none(extracted_data.get("documentType"))
            final_type = raw_type if raw_type in {"nota", "fatura"} else document_type

            data = FinancialDocumentData(
                documentType=final_type,
                documentNumber=self._as_none(extracted_data.get("documentNumber")),
                issueDate=self._as_none(extracted_data.get("issueDate")),
                dueDate=self._as_none(extracted_data.get("dueDate")),
                supplierName=self._as_none(extracted_data.get("supplierName")),
                supplierTaxId=self._as_none(extracted_data.get("supplierTaxId")),
                customerName=self._as_none(extracted_data.get("customerName")),
                customerTaxId=self._as_none(extracted_data.get("customerTaxId")),
                currency=self._as_none(extracted_data.get("currency")),
                subtotal=self._as_float(extracted_data.get("subtotal")),
                taxAmount=self._as_float(extracted_data.get("taxAmount")),
                totalAmount=self._as_float(extracted_data.get("totalAmount")),
                paymentMethod=self._as_none(extracted_data.get("paymentMethod")),
                items=self._normalize_items(extracted_data.get("items")),
                notes=self._as_none(extracted_data.get("notes")),
            )
            return self._sanitize_financial_data(data)

        except Exception as e:
            logger.error(f"Erro ao normalizar dados financeiros: {e}")
            raise DataValidationError(
                f"Erro ao validar e normalizar dados: {str(e)}",
                details="Verifique se o JSON retornado está no formato esperado",
            ) from e

    def _normalize_bank_receipt_data(
        self,
        extracted_data: Dict[str, Any],
    ) -> BankReceiptData:
        try:
            data = BankReceiptData(
                documentType=self._as_none(extracted_data.get("documentType")) or "comprovante_bancario",
                operationType=self._as_none(extracted_data.get("operationType")),
                transactionId=self._as_none(extracted_data.get("transactionId")),
                authenticationCode=self._as_none(extracted_data.get("authenticationCode")),
                bankName=self._as_none(extracted_data.get("bankName")),
                amount=self._as_float(extracted_data.get("amount")),
                feeAmount=self._as_float(extracted_data.get("feeAmount")),
                netAmount=self._as_float(extracted_data.get("netAmount")),
                currency=self._as_none(extracted_data.get("currency")),
                transactionDate=self._as_none(extracted_data.get("transactionDate")),
                transactionTime=self._as_none(extracted_data.get("transactionTime")),
                scheduledFor=self._as_none(extracted_data.get("scheduledFor")),
                status=self._as_none(extracted_data.get("status")),
                payerName=self._as_none(extracted_data.get("payerName")),
                payerDocument=self._as_none(extracted_data.get("payerDocument")),
                payerBank=self._as_none(extracted_data.get("payerBank")),
                payerBranch=self._as_none(extracted_data.get("payerBranch")),
                payerAccount=self._as_none(extracted_data.get("payerAccount")),
                receiverName=self._as_none(extracted_data.get("receiverName")),
                receiverDocument=self._as_none(extracted_data.get("receiverDocument")),
                receiverBank=self._as_none(extracted_data.get("receiverBank")),
                receiverBranch=self._as_none(extracted_data.get("receiverBranch")),
                receiverAccount=self._as_none(extracted_data.get("receiverAccount")),
                channel=self._as_none(extracted_data.get("channel")),
                description=self._as_none(extracted_data.get("description")),
                notes=self._as_none(extracted_data.get("notes")),
            )
            return self._sanitize_bank_receipt_data(data)
        except Exception as e:
            logger.error(f"Erro ao normalizar comprovante bancário: {e}")
            raise DataValidationError(
                f"Erro ao validar e normalizar dados: {str(e)}",
                details="Verifique se o JSON retornado está no formato esperado",
            ) from e

    def process_pdf_bytes(
        self,
        pdf_bytes: bytes,
        filename: str,
        document_type: str,
    ) -> FinancialDocumentData | BankReceiptData:
        try:
            doc_bytes = self._read_pdf_file(pdf_bytes=pdf_bytes)
            doc_message = self._prepare_ai_message(doc_bytes, filename, document_type)
            response_text = self._send_to_ai(doc_message)
            extracted_data = self._extract_and_validate_data(response_text)
            if document_type == "comprovante_bancario":
                return self._normalize_bank_receipt_data(extracted_data)
            return self._normalize_financial_data(extracted_data, document_type)

        except (PDFReadError, AIAPIError, JSONExtractionError, DataValidationError) as e:
            logger.error(f"Erro ao processar {filename}: {e.message}")
            raise

        except Exception as e:
            logger.exception(f"Erro inesperado ao processar {filename}: {e}")
            raise ProcessingError(
                f"Erro inesperado durante processamento: {str(e)}",
                details=f"Arquivo: {filename}",
            ) from e


financial_document_service = FinancialDocumentService()
