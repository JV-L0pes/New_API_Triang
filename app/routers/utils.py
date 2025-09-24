from fastapi import APIRouter, Depends
from app.security import require_api_key
from app.schemas.base import ok, Envelope
router=APIRouter(dependencies=[Depends(require_api_key)], tags=['utils'])
@router.get('/cep/{cep}', response_model=Envelope)
async def cep(cep:str): return ok({'cep':cep})
