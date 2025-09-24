import json
from fastapi import APIRouter, Depends, Request, Header
from app.security import require_api_key, verify_hmac
from app.schemas.base import ok, Envelope
from app.integrations.clients.waba_client import WABAClient
router=APIRouter(dependencies=[Depends(require_api_key)], tags=["integrations:whatsapp"])
@router.get("/webhook", summary="WhatsApp - Verificação webhook")
async def verify(mode: str | None=None, hub_challenge: str | None=None, hub_verify_token: str | None=None):
    return hub_challenge or ""
@router.post("/webhook", response_model=Envelope, summary="WhatsApp - Inbound webhook")
async def inbound(request: Request, x_hub_signature_256: str | None = Header(default=None)):
    body = await request.body(); request._body = body
    verify_hmac(request, x_hub_signature_256, "WEBHOOK_HMAC_SECRET")
    payload=json.loads(body.decode() or "{}")
    return ok({"received": True, "entries": len(payload.get("entry", []))})
@router.post("/send", response_model=Envelope, summary="WhatsApp - Enviar mensagem")
async def send(to: str, text: str | None = None, template: str | None = None):
    c=WABAClient(); data=await c.send_text(to, text or "", template=template); await c.close(); return ok(data)
