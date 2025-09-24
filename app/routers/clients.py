from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.security import require_api_key
from app.schemas.base import ok, Envelope
from app.infrastructure.newcon_client import NewconClient
router=APIRouter(dependencies=[Depends(require_api_key)], tags=["clients"])
@router.get("/cnsCliente", response_model=Envelope)
async def cns_cliente(Documento: str | None = None, Codigo_Cliente: int | None = None):
    params={}
    if Documento: params["Documento"]=Documento
    if Codigo_Cliente: params["Codigo_Cliente"]=Codigo_Cliente
    nc=NewconClient(); data=await nc.call("cnsCliente", params); await nc.close()
    return ok(data)
class ManutencaoClienteIn(BaseModel):
    Codigo_Cliente:int|None=None; Nome:str; Documento:str; Email:str|None=None; Telefone:str|None=None
@router.post("/prcManutencaoCliente_new", response_model=Envelope)
async def manutencao(body: ManutencaoClienteIn):
    nc=NewconClient(); data=await nc.call("prcManutencaoCliente_new", body.model_dump()); await nc.close()
    return ok(data)
