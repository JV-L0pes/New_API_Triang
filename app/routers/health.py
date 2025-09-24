from fastapi import APIRouter
import os
router=APIRouter()
@router.get('/healthz')
async def healthz(): return {'ok': True}

