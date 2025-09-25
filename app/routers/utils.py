from fastapi import APIRouter, Depends, HTTPException
from app.security import require_api_key
from app.schemas.base import ok, Envelope
from app.infrastructure.cache import hybrid_cache
from app.infrastructure.cache.redis_client import redis_client
import os
from dotenv import load_dotenv

load_dotenv()

router=APIRouter(dependencies=[Depends(require_api_key)], tags=['utils'])

@router.get('/cep/{cep}', response_model=Envelope)
async def cep(cep:str): return ok({'cep':cep})

@router.get('/debug/env', response_model=Envelope, summary="Debug - Variáveis de ambiente")
async def debug_env():
    """
    Debug: Mostra as variáveis de ambiente relacionadas ao Redis.
    """
    return ok({
        "UPSTASH_REDIS_REST_URL": os.getenv("UPSTASH_REDIS_REST_URL", "NÃO CONFIGURADO"),
        "UPSTASH_REDIS_REST_TOKEN": "***" + os.getenv("UPSTASH_REDIS_REST_TOKEN", "NÃO CONFIGURADO")[-4:] if os.getenv("UPSTASH_REDIS_REST_TOKEN") else "NÃO CONFIGURADO",
        "REDIS_URL": os.getenv("REDIS_URL", "NÃO CONFIGURADO"),
        "all_env_keys": [key for key in os.environ.keys() if "REDIS" in key.upper()]
    })

@router.delete('/cache/clear', response_model=Envelope, summary="Limpar todo o cache Redis")
async def clear_cache():
    """
    Limpa completamente o cache Redis.
    
    ⚠️ ATENÇÃO: Esta operação remove TODOS os dados do cache Redis!
    Use com cuidado em produção.
    """
    try:
        # Garantir que o Redis está conectado
        if not redis_client.connected:
            await redis_client.connect()
        
        if not redis_client.connected or not redis_client.client:
            raise HTTPException(status_code=500, detail="Erro ao conectar com Redis")
        
        # Contar chaves antes da limpeza
        keys_before = await redis_client.client.dbsize()
        
        # Limpar todo o banco de dados
        await redis_client.client.flushdb()
        
        # Verificar se foi limpo
        keys_after = await redis_client.client.dbsize()
        
        return ok({
            "message": "Cache Redis limpo com sucesso",
            "keys_before": keys_before,
            "keys_after": keys_after,
            "keys_removed": keys_before - keys_after
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao limpar cache: {str(e)}")

@router.get('/cache/stats', response_model=Envelope, summary="Estatísticas do cache Redis")
async def cache_stats():
    """
    Retorna estatísticas do cache Redis.
    """
    try:
        # Garantir que o Redis está conectado
        if not redis_client.connected:
            await redis_client.connect()
        
        if not redis_client.connected or not redis_client.client:
            raise HTTPException(status_code=500, detail="Erro ao conectar com Redis")
        
        # Obter estatísticas
        total_keys = await redis_client.client.dbsize()
        
        # Contar chaves por padrão
        bens_keys_list = await redis_client.client.keys("bens:*")
        cache_keys_list = await redis_client.client.keys("*cache*")
        bens_keys = len(bens_keys_list)
        cache_keys = len(cache_keys_list)
        other_keys = total_keys - bens_keys - cache_keys
        
        # Obter informações do servidor
        info = await redis_client.client.info()
        
        return ok({
            "total_keys": total_keys,
            "keys_by_type": {
                "bens": bens_keys,
                "cache": cache_keys,
                "other": other_keys
            },
            "redis_info": {
                "version": info.get("redis_version", "N/A"),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
                "used_memory_human": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0)
            }
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")

@router.delete('/cache/bens', response_model=Envelope, summary="Limpar apenas cache de bens")
async def clear_bens_cache():
    """
    Limpa apenas o cache de bens disponíveis.
    """
    try:
        # Garantir que o Redis está conectado
        if not redis_client.connected:
            await redis_client.connect()
        
        if not redis_client.connected or not redis_client.client:
            raise HTTPException(status_code=500, detail="Erro ao conectar com Redis")
        
        # Encontrar todas as chaves de bens
        bens_keys = await redis_client.client.keys("bens:*")
        
        # Deletar chaves de bens
        deleted_count = 0
        if bens_keys:
            deleted_count = await redis_client.client.delete(*bens_keys)
        
        return ok({
            "message": "Cache de bens limpo com sucesso",
            "keys_deleted": deleted_count,
            "keys_found": len(bens_keys)
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao limpar cache de bens: {str(e)}")
