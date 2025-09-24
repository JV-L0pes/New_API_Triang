from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from app.security import require_api_key, verify_hmac
from app.schemas.base import ok, Envelope
from app.integrations.clients.docusign_client import DocuSignClient
router=APIRouter(dependencies=[Depends(require_api_key)], tags=["integrations:docusign"])
class EnvelopeIn(BaseModel):
    Numero_Contrato:int; emails:list[str]; nome:str; pdf_base64:str
@router.post("/envelope", response_model=Envelope, summary="DocuSign - Criar envelope")
async def create_envelope(body: EnvelopeIn):
    c=DocuSignClient(); data=await c.create_envelope(f"Proposta {body.Numero_Contrato}", body.emails, body.pdf_base64, f"Proposta_{body.Numero_Contrato}.pdf"); await c.close(); return ok({"envelope": data})
@router.post("/webhook", response_model=Envelope, summary="DocuSign - Webhook")
async def webhook(request: Request):
    body = await request.body(); request._body = body
    verify_hmac(request, request.headers.get("X-DocuSign-Signature-1"), "WEBHOOK_HMAC_SECRET")
    return ok({"received": True})
