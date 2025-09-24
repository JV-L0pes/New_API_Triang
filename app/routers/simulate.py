from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel
from app.security import require_api_key
from app.schemas.base import ok, Envelope
from app.infrastructure.newcon_client import NewconClient
router=APIRouter(dependencies=[Depends(require_api_key)], tags=["simulate"])
class SimuladorIn(BaseModel):
    Codigo_Grupo:int; Prazo:int; Valor_Bem:float
@router.post("/cnsSimulador", response_model=Envelope)
async def sim(body: SimuladorIn, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    nc=NewconClient(); data=await nc.call("cnsSimulador", body.model_dump()); await nc.close()
    return ok({"simulacao": data, "idempotency_key": idempotency_key})
