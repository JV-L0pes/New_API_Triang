import os
import json
import asyncio
from typing import Optional, Any
import redis.asyncio as redis
from datetime import timedelta

class RedisClient:
    def __init__(self):
        self.redis_url = os.environ.get("REDIS_URL", "")
        self.upstash_rest_url = os.environ.get("UPSTASH_REDIS_REST_URL", "")
        self.upstash_token = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "")
        self.client: Optional[redis.Redis] = None
        self.connected = False
        self.is_upstash = False
        
    async def connect(self):
        """Conecta ao Redis (tradicional ou Upstash)"""
        # Prioriza Upstash se configurado
        if self.upstash_rest_url and self.upstash_token:
            try:
                # Converte URL REST do Upstash para URL Redis tradicional
                # https://neutral-penguin-9127.upstash.io -> redis://neutral-penguin-9127.upstash.io:6379
                redis_host = self.upstash_rest_url.replace("https://", "").replace("http://", "")
                
                # Usar configuração SSL mais compatível
                self.client = redis.Redis(
                    host=redis_host,
                    port=6379,
                    password=self.upstash_token,
                    decode_responses=True,
                    ssl=True,
                    ssl_cert_reqs=None
                )
                await self.client.ping()
                self.connected = True
                self.is_upstash = True
                print("✅ Upstash Redis conectado com sucesso")
                return True
            except Exception as e:
                print(f"❌ Erro ao conectar Upstash Redis: {e}")
                self.connected = False
                return False
        
        # Fallback para Redis tradicional
        elif self.redis_url:
            try:
                self.client = redis.from_url(self.redis_url, decode_responses=True)
                await self.client.ping()
                self.connected = True
                self.is_upstash = False
                print("✅ Redis tradicional conectado com sucesso")
                return True
            except Exception as e:
                print(f"❌ Erro ao conectar Redis tradicional: {e}")
                self.connected = False
                return False
        
        else:
            print("⚠️ Nenhuma configuração Redis encontrada - usando cache em memória")
            return False
    
    async def disconnect(self):
        """Desconecta do Redis"""
        if self.client:
            await self.client.aclose()
            self.connected = False
    
    async def get(self, key: str) -> Optional[Any]:
        """Busca valor no cache"""
        if not self.connected or not self.client:
            return None
            
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"❌ Erro ao buscar no Redis: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl_seconds: int = 1800) -> bool:
        """Salva valor no cache com TTL (padrão 30 minutos)"""
        if not self.connected or not self.client:
            return False
            
        try:
            json_value = json.dumps(value, ensure_ascii=False)
            await self.client.setex(key, ttl_seconds, json_value)
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar no Redis: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Remove valor do cache"""
        if not self.connected or not self.client:
            return False
            
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            print(f"❌ Erro ao deletar do Redis: {e}")
            return False
    
    async def get_or_set(self, key: str, fetch_func, ttl_seconds: int = 1800) -> Any:
        """Busca no cache ou executa função e salva resultado"""
        # Tenta buscar no cache
        cached_value = await self.get(key)
        if cached_value is not None:
            print(f"📦 Cache HIT: {key}")
            return cached_value
        
        # Cache miss - executa função
        print(f"🔄 Cache MISS: {key} - executando função")
        try:
            result = await fetch_func()
            await self.set(key, result, ttl_seconds)
            return result
        except Exception as e:
            print(f"❌ Erro ao executar função: {e}")
            raise

# Instância global do Redis
redis_client = RedisClient()
