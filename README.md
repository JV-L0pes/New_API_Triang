# Triângulo Consórcio — Copilot API (All-in-One)

Inclui:
- wsRegVenda 01–11 com parsing SOAP→JSON
- Integrações: CRM, WhatsApp, Outlook/Graph, DocuSign
- Idempotência Postgres (Alembic)
- OpenAPI unificado (`openapi_unified.yaml`) para Copilot Studio

## Rodar local
```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Render
- Build: `pip install -r requirements.txt && alembic upgrade head`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health: `/healthz`
- Defina as variáveis do `.env.example`

## Copilot Studio
- Importe `openapi_unified.yaml`. Use `X-API-Key` em todas as chamadas.
