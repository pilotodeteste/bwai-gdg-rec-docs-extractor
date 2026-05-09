from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


class FinancialLineItem(BaseModel):
    description: Optional[str] = Field(None, description="Descrição do item")
    quantity: Optional[float] = Field(None, description="Quantidade")
    unitPrice: Optional[float] = Field(None, description="Preço unitário")
    lineTotal: Optional[float] = Field(None, description="Total da linha")
    taxRate: Optional[float] = Field(None, description="Alíquota de imposto")
    sku: Optional[str] = Field(None, description="SKU ou código do item")


class FinancialDocumentData(BaseModel):
    documentType: str = Field(..., description="Tipo do documento: nota ou fatura")
    documentNumber: Optional[str] = Field(None, description="Número do documento")
    issueDate: Optional[str] = Field(None, description="Data de emissão")
    dueDate: Optional[str] = Field(None, description="Data de vencimento")
    supplierName: Optional[str] = Field(None, description="Nome do fornecedor/emissor")
    supplierTaxId: Optional[str] = Field(None, description="CPF/CNPJ do fornecedor/emissor")
    customerName: Optional[str] = Field(None, description="Nome do cliente/destinatário")
    customerTaxId: Optional[str] = Field(None, description="CPF/CNPJ do cliente/destinatário")
    currency: Optional[str] = Field(None, description="Moeda do documento")
    subtotal: Optional[float] = Field(None, description="Subtotal")
    taxAmount: Optional[float] = Field(None, description="Valor total de impostos")
    totalAmount: Optional[float] = Field(None, description="Valor total do documento")
    paymentMethod: Optional[str] = Field(None, description="Forma de pagamento")
    items: List[FinancialLineItem] = Field(default_factory=list, description="Lista de itens")
    notes: Optional[str] = Field(None, description="Observações adicionais")

    @field_validator("documentType")
    @classmethod
    def validate_document_type(cls, v: str) -> str:
        normalized = (v or "").strip().lower()
        if normalized in {"nota", "fatura"}:
            return normalized
        return "fatura"

    @field_validator("issueDate", "dueDate")
    @classmethod
    def validate_dates(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if isinstance(v, str) and v.strip().lower() in {"", "null", "n/a", "na"}:
            return None
        return v


class BankReceiptData(BaseModel):
    documentType: str = Field(..., description="Tipo do documento: comprovante_bancario")
    operationType: Optional[str] = Field(None, description="Tipo da operação: PIX, TED, DOC, etc.")
    transactionId: Optional[str] = Field(None, description="ID da transação")
    authenticationCode: Optional[str] = Field(None, description="Código de autenticação")
    bankName: Optional[str] = Field(None, description="Banco principal identificado no comprovante")
    amount: Optional[float] = Field(None, description="Valor da transação")
    feeAmount: Optional[float] = Field(None, description="Taxa cobrada")
    netAmount: Optional[float] = Field(None, description="Valor líquido")
    currency: Optional[str] = Field(None, description="Moeda")
    transactionDate: Optional[str] = Field(None, description="Data da transação")
    transactionTime: Optional[str] = Field(None, description="Hora da transação")
    scheduledFor: Optional[str] = Field(None, description="Data/hora agendada")
    status: Optional[str] = Field(None, description="Status: concluído, pendente, etc.")
    payerName: Optional[str] = Field(None, description="Nome do pagador/remetente")
    payerDocument: Optional[str] = Field(None, description="CPF/CNPJ do pagador/remetente")
    payerBank: Optional[str] = Field(None, description="Banco do pagador/remetente")
    payerBranch: Optional[str] = Field(None, description="Agência do pagador/remetente")
    payerAccount: Optional[str] = Field(None, description="Conta do pagador/remetente")
    receiverName: Optional[str] = Field(None, description="Nome do recebedor/destinatário")
    receiverDocument: Optional[str] = Field(None, description="CPF/CNPJ do recebedor/destinatário")
    receiverBank: Optional[str] = Field(None, description="Banco do recebedor/destinatário")
    receiverBranch: Optional[str] = Field(None, description="Agência do recebedor/destinatário")
    receiverAccount: Optional[str] = Field(None, description="Conta do recebedor/destinatário")
    channel: Optional[str] = Field(None, description="Canal da operação: app, internet banking, caixa eletrônico")
    description: Optional[str] = Field(None, description="Descrição/histórico da transação")
    notes: Optional[str] = Field(None, description="Observações adicionais")

    @field_validator("documentType")
    @classmethod
    def validate_document_type(cls, v: str) -> str:
        normalized = (v or "").strip().lower()
        if normalized == "comprovante_bancario":
            return normalized
        return "comprovante_bancario"
