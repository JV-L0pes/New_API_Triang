from datetime import date
from fastapi import APIRouter, Depends, Response
from app.security import require_api_key
from app.schemas.base import ok, Envelope
router=APIRouter(dependencies=[Depends(require_api_key)], tags=["reports"])
@router.get("/vendas", response_model=Envelope, summary="Relatório de vendas (JSON)")
async def vendas(from_date: date, to_date: date):
    return ok({"periodo":{"from":from_date.isoformat(),"to":to_date.isoformat()},"kpis":{"propostas":0,"contratos":0,"faturamento":0.0}})
@router.get("/vendas.csv", summary="Relatório de vendas (CSV)")
async def vendas_csv(from_date: date, to_date: date):
    csv=f"from,to,propostas,contratos,faturamento\n{from_date},{to_date},0,0,0.00\n"
    return Response(content=csv, media_type="text/csv")
