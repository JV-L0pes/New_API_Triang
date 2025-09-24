from fastapi import FastAPI
from dotenv import load_dotenv
import os

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

from app.routers import health, utils, catalog, simulate, proposals, clients, billing
from app.routers.integrations import crm, whatsapp, outlook, docusign, reports
from app.infrastructure.cache import hybrid_cache

app = FastAPI(
    title="Triângulo Consórcio - API Copilot",
    version="6.0.0",
    description="wsRegVenda 01–11 + integrações (CRM, WhatsApp, Outlook/Graph, DocuSign, Reports) com SOAP→JSON."
)

@app.on_event("startup")
async def startup_event():
    """Inicializa o cache híbrido na startup"""
    await hybrid_cache.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    """Desconecta do Redis na shutdown"""
    await hybrid_cache.disconnect()

# Core wsRegVenda
app.include_router(health.router, prefix="")
app.include_router(utils.router, prefix="/utils")
app.include_router(catalog.router, prefix="/catalog")
app.include_router(simulate.router, prefix="/simulate")
app.include_router(proposals.router, prefix="/proposals")
app.include_router(clients.router, prefix="/clients")
app.include_router(billing.router, prefix="/billing")

# Integrations
app.include_router(crm.router, prefix="/integrations/crm")
app.include_router(whatsapp.router, prefix="/integrations/whatsapp")
app.include_router(outlook.router, prefix="/integrations/outlook")
app.include_router(docusign.router, prefix="/integrations/docusign")
app.include_router(reports.router, prefix="/reports")
