from fastapi import APIRouter, Depends, Header, Path
from pydantic import BaseModel
from app.security import require_api_key
from app.schemas.base import ok, Envelope
from app.infrastructure.newcon_client import NewconClient
from app.utils import idempotency_pg as idem
router=APIRouter(dependencies=[Depends(require_api_key)], tags=["proposals"])
class IncluiReservaIn(BaseModel):
    Codigo_Cota:int; Data_Validade:str
@router.post("/prcIncluiReservaCotas", response_model=Envelope)
async def reserva(body: IncluiReservaIn, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    if idempotency_key:
        c=idem.get("prcIncluiReservaCotas", idempotency_key, body.model_dump())
        if c: return ok(c | {"idempotency_key": idempotency_key})
    nc=NewconClient(); data=await nc.call("prcIncluiReservaCotas", body.model_dump()); await nc.close()
    res={"resultado": data.get("resultado", data)}
    if idempotency_key: idem.save("prcIncluiReservaCotas", idempotency_key, body.model_dump(), res)
    return ok(res | {"idempotency_key": idempotency_key})
class PropostaIn(BaseModel):
    Codigo_Grupo:int; Codigo_Bem:int; Prazo:int; Codigo_Cliente:int; Numero_Assembleia_Emissao:int|None=None
@router.post("/prcIncluiProposta", response_model=Envelope)
async def proposta(body: PropostaIn, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    if idempotency_key:
        c=idem.get("prcIncluiProposta", idempotency_key, body.model_dump())
        if c: return ok(c | {"idempotency_key": idempotency_key})
    payload=body.model_dump()
    nc=NewconClient(); data=await nc.call("prcIncluiProposta", payload); await nc.close()
    res={"resultado": data.get("resultado", data)}
    if idempotency_key: idem.save("prcIncluiProposta", idempotency_key, body.model_dump(), res)
    return ok(res | {"idempotency_key": idempotency_key})
class RecebimentoIn(BaseModel):
    Valor: float | None = None
@router.post("/{Numero_Contrato}/prcIncluiPropostaRecebimento", response_model=Envelope)
async def recv(Numero_Contrato: int = Path(...), body: RecebimentoIn | None = None):
    payload={"Numero_Contrato": Numero_Contrato}
    if body and body.Valor is not None: payload["Valor"]=body.Valor
    nc=NewconClient(); data=await nc.call("prcIncluiPropostaRecebimento", payload); await nc.close()
    return ok({"resultado": data.get("resultado", data), "Numero_Contrato": Numero_Contrato})
@router.post("/{Numero_Contrato}/cnsEmiteProposta", response_model=Envelope)
async def pdf(Numero_Contrato: int = Path(...)):
    nc=NewconClient(); data=await nc.call("cnsEmiteProposta", {"Numero_Contrato": Numero_Contrato}); await nc.close()
    return ok({"resultado": data.get("resultado", data), "Numero_Contrato": Numero_Contrato})
