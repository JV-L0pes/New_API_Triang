from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.security import require_api_key
from app.schemas.base import ok, Envelope
from app.integrations.clients.crm_client import CRMClient
router=APIRouter(dependencies=[Depends(require_api_key)], tags=["integrations:crm"])
class LeadIn(BaseModel):
    id:str|None=None; nome:str; contato:str; origem:str|None=None; etapa:str|None=None
@router.post("/leads", response_model=Envelope, summary="CRM - Upsert lead")
async def upsert_lead(body: LeadIn):
    c=CRMClient(); data=await c.upsert_lead(body.model_dump()); await c.close(); return ok(data)
class OpportunityIn(BaseModel):
    id:str|None=None; lead_id:str|None=None; valor:float|None=None; etapa:str|None=None
@router.post("/opportunities", response_model=Envelope, summary="CRM - Upsert oportunidade")
async def upsert_opportunity(body: OpportunityIn):
    c=CRMClient(); data=await c.upsert_opportunity(body.model_dump()); await c.close(); return ok(data)
