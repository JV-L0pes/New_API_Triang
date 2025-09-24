from typing import Any, Callable
from .redis_client import redis_client
from .memory_cache import memory_cache

class HybridCache:
    def __init__(self):
        self.redis_available = False
    
    async def initialize(self):
        """Inicializa o cache híbrido"""
        self.redis_available = await redis_client.connect()
        if self.redis_available:
            print("🚀 Usando Redis como cache principal")
        else:
            print("⚠️ Usando cache em memória como fallback")
    
    async def get(self, key: str) -> Any:
        """Busca valor no cache (Redis primeiro, depois memória)"""
        if self.redis_available:
            value = await redis_client.get(key)
            if value is not None:
                return value
        
        # Fallback para memória
        return await memory_cache.get(key)
    
    async def set(self, key: str, value: Any, ttl_seconds: int = 1800) -> bool:
        """Salva valor no cache (Redis e memória)"""
        success = True
        
        if self.redis_available:
            success = await redis_client.set(key, value, ttl_seconds)
        
        # Sempre salva na memória como backup
        await memory_cache.set(key, value, ttl_seconds)
        
        return success
    
    async def delete(self, key: str) -> bool:
        """Remove valor do cache (Redis e memória)"""
        redis_success = True
        if self.redis_available:
            redis_success = await redis_client.delete(key)
        
        memory_success = await memory_cache.delete(key)
        
        return redis_success and memory_success
    
    async def get_or_set(self, key: str, fetch_func: Callable, ttl_seconds: int = 1800) -> Any:
        """Busca no cache ou executa função e salva resultado"""
        # Tenta buscar no cache
        cached_value = await self.get(key)
        if cached_value is not None:
            return cached_value
        
        # Cache miss - executa função
        try:
            result = await fetch_func()
            await self.set(key, result, ttl_seconds)
            return result
        except Exception as e:
            print(f"❌ Erro ao executar função: {e}")
            raise
    
    async def disconnect(self):
        """Desconecta do Redis"""
        if self.redis_available:
            await redis_client.disconnect()

# Instância global do cache híbrido
hybrid_cache = HybridCache()
