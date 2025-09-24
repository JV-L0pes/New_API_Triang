import asyncio
from typing import Any, Optional, Callable
from datetime import datetime, timedelta
import json

class MemoryCache:
    def __init__(self):
        self._cache = {}
        self._timestamps = {}
    
    async def get(self, key: str) -> Optional[Any]:
        """Busca valor no cache em memória"""
        if key not in self._cache:
            return None
            
        # Verifica se expirou
        if key in self._timestamps:
            if datetime.now() > self._timestamps[key]:
                del self._cache[key]
                del self._timestamps[key]
                return None
        
        return self._cache[key]
    
    async def set(self, key: str, value: Any, ttl_seconds: int = 1800) -> bool:
        """Salva valor no cache em memória"""
        self._cache[key] = value
        self._timestamps[key] = datetime.now() + timedelta(seconds=ttl_seconds)
        return True
    
    async def delete(self, key: str) -> bool:
        """Remove valor do cache"""
        if key in self._cache:
            del self._cache[key]
        if key in self._timestamps:
            del self._timestamps[key]
        return True
    
    async def get_or_set(self, key: str, fetch_func: Callable, ttl_seconds: int = 1800) -> Any:
        """Busca no cache ou executa função e salva resultado"""
        # Tenta buscar no cache
        cached_value = await self.get(key)
        if cached_value is not None:
            print(f"📦 Memory Cache HIT: {key}")
            return cached_value
        
        # Cache miss - executa função
        print(f"🔄 Memory Cache MISS: {key} - executando função")
        try:
            result = await fetch_func()
            await self.set(key, result, ttl_seconds)
            return result
        except Exception as e:
            print(f"❌ Erro ao executar função: {e}")
            raise
    
    def clear(self):
        """Limpa todo o cache"""
        self._cache.clear()
        self._timestamps.clear()

# Instância global do cache em memória
memory_cache = MemoryCache()
