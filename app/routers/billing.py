from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.security import require_api_key
from app.schemas.base import ok, Envelope
from app.infrastructure.newcon_client import NewconClient
router=APIRouter(dependencies=[Depends(require_api_key)], tags=["billing"])
@router.get("/cnsBancosDebito", response_model=Envelope)
async def bancos():
    nc=NewconClient(); data=await nc.call("cnsBancosDebito", {}); await nc.close(); return ok(data)
class RegistroDebitoIn(BaseModel):
    Numero_Contrato:int; Banco:str; Agencia:str; Conta:str
@router.post("/prcIncluiRegistroDebitoConta", response_model=Envelope)
async def registra(body: RegistroDebitoIn):
    nc=NewconClient(); data=await nc.call("prcIncluiRegistroDebitoConta", body.model_dump()); await nc.close(); return ok(data)
class BoletoIn(BaseModel):
    Numero_Contrato:int|None=None; Data_Vencimento_Boleto:str="1900-01-01"
@router.post("/cnsEmiteBoletoProposta", response_model=Envelope)
async def boleto(body: BoletoIn):
    payload={k:v for k,v in body.model_dump().items() if v is not None}
    nc=NewconClient(); data=await nc.call("cnsEmiteBoletoProposta", payload); await nc.close(); return ok(data)
