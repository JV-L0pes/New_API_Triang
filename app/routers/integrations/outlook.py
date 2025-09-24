from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.security import require_api_key
from app.schemas.base import ok, Envelope
from app.integrations.clients.graph_client import GraphClient
router=APIRouter(dependencies=[Depends(require_api_key)], tags=["integrations:outlook"])
class MailIn(BaseModel):
    to:list[str]; subject:str; body_html:str; attachments:list[dict]|None=None
@router.post("/send", response_model=Envelope, summary="Outlook - Enviar e-mail")
async def send(body: MailIn):
    c=GraphClient(); data=await c.send_mail(body.to, body.subject, body.body_html, attachments=body.attachments); await c.close(); return ok(data)
