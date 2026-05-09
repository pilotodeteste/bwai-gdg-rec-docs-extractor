# BWAI GDG Recife - Docs Extractor

API em FastAPI para extração estruturada de PDFs com Vertex AI (Gemini), com foco educacional para demos e workshops.

## Endpoints

- `GET /health`
- `POST /process-nota`
- `POST /process-fatura`
- `POST /process-comprovante-bancario`

## Segurança (importante)

- Nunca suba arquivo de chave (`*.json`, `*.pem`, etc.) para o GitHub.
- Nunca suba `.env` com credenciais reais.
- Use `.env.example` como modelo e mantenha os valores reais apenas no `.env` local.
- A resposta da API aplica mascaramento em dados sensíveis (CPF/CNPJ, IDs de transação, conta/agência e dados sensíveis em texto livre).

## Requisitos

- Python 3.12+
- Projeto GCP com billing ativo
- Vertex AI API habilitada
- Service Account com permissão para Vertex AI

## Setup local

1. Clone e entre no repositório.
2. Crie e ative o ambiente virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Instale dependências:

```bash
pip install -r requirements.txt
```

4. Crie seu `.env` a partir do exemplo:

```bash
cp .env.example .env
```

5. Edite o `.env` com seus dados reais:

```env
GOOGLE_CLOUD_PROJECT=seu-projeto-gcp
GOOGLE_CLOUD_LOCATION=global
VERTEX_MODEL_ID=gemini-3-flash-preview
GOOGLE_APPLICATION_CREDENTIALS=/caminho/seguro/service-account.json
HOST=0.0.0.0
PORT=8000
```

## Executar

```bash
cd code
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Swagger: `http://localhost:8000/docs`

## Testes rápidos

```bash
curl -X POST "http://localhost:8000/process-nota" \
  -F "file=@/caminho/para/sua-nota.pdf;type=application/pdf"
```

```bash
curl -X POST "http://localhost:8000/process-fatura" \
  -F "file=@/caminho/para/sua-fatura.pdf;type=application/pdf"
```

```bash
curl -X POST "http://localhost:8000/process-comprovante-bancario" \
  -F "file=@/caminho/para/seu-comprovante.pdf;type=application/pdf"
```

## Prompts usados

- `code/app/prompts/standard_nota_prompt.txt`
- `code/app/prompts/standard_fatura_prompt.txt`
- `code/app/prompts/standard_comprovante_bancario_prompt.txt`

## Referências

- Gemini 3 Flash: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-flash
- Get started Gemini 3: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/start/get-started-with-gemini-3
- Gen AI SDK Python: https://googleapis.github.io/python-genai/index.html
- Vertex AI authentication: https://cloud.google.com/vertex-ai/docs/authentication
