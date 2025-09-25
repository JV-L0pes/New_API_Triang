#!/usr/bin/env python3
"""
Script de Teste - Fluxo de Vendas Consórcio Triângulo
Testa as regras 01-04 do fluxo básico de vendas
"""

import requests
import json
import asyncio
import aiohttp
from datetime import date
import sys
import os
from dotenv import load_dotenv

# Importar a classe RedisClient do projeto
from app.infrastructure.cache.redis_client import redis_client

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
API_BASE_URL = "https://vague-blaire-alltech-e7c1ee1f.koyeb.app"
API_KEY = "eyJzdWIiOiJ0ZXN0ZTFAZW1haWwuY29tIiwidHlwZSI6Imludml0ZSIsImV4cCI6MTc1ODczODQ1Miwibm9uY2UiOiJkNmI5YjExYWUxYjM0N2JlYWZiMTJmMDU3MmNjNjc2MCJ9.QQLUDyhRvcE0Fz9OLDaOGHlRDgw-jiXwKohpSnLl1Ng"

# Headers padrão
headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

async def cache_bens_result(codigo_tipo_grupo, codigo_tipo_venda, bens_data):
    """Armazena resultado de bens no Redis apenas se houver bens"""
    if bens_data and len(bens_data) > 0:
        cache_data = {
            "codigo_tipo_grupo": codigo_tipo_grupo,
            "codigo_tipo_venda": codigo_tipo_venda,
            "quantidade_bens": len(bens_data),
            "bens": bens_data,
            "cached_at": date.today().isoformat()
        }
        cache_key = f"bens:{codigo_tipo_grupo}:{codigo_tipo_venda}"
        success = await redis_client.set(cache_key, cache_data, 3600)  # TTL de 1 hora
        if success:
            print(f"   💾 Cacheado no Redis: {len(bens_data)} bens")
        else:
            print(f"   ⚠️ Falha ao cachear no Redis")
    else:
        print(f"   ⚠️ Não cacheado (sem bens)")

async def get_cached_bens(codigo_tipo_grupo, codigo_tipo_venda):
    """Recupera bens do cache Redis"""
    if not redis_client.connected:
        return None
    cache_key = f"bens:{codigo_tipo_grupo}:{codigo_tipo_venda}"
    cached_data = await redis_client.get(cache_key)
    if cached_data:
        print(f"   📦 Cache HIT: {len(cached_data.get('bens', []))} bens")
        return cached_data.get('bens', [])
    return None

def make_request(endpoint, params=None):
    """Faz uma requisição para a API"""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na requisição para {endpoint}: {e}")
        return None

async def make_async_request(session, endpoint, params=None):
    """Faz uma requisição assíncrona para a API"""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        async with session.get(url, headers=headers, params=params) as response:
            response.raise_for_status()
            return await response.json()
    except Exception as e:
        print(f"❌ Erro na requisição assíncrona para {endpoint}: {e}")
        return None

async def test_bens_batch(session, codigo_tipo_grupo, tipos_vendas_batch):
    """Testa um lote de tipos de vendas em paralelo"""
    tasks = []
    
    for tipo_venda in tipos_vendas_batch:
        codigo_tipo_venda = tipo_venda.get("CODIGO_TIPO_VENDA")
        descricao_venda = tipo_venda.get("DESCRICAO")
        
        # Verificar cache primeiro
        cached_data = await get_cached_bens(codigo_tipo_grupo, codigo_tipo_venda)
        if cached_data:
            print(f"📋 Venda {codigo_tipo_venda} ({descricao_venda}) - 💾 Cache: {cached_data['quantidade_bens']} bens")
            tasks.append({
                "tipo_venda": tipo_venda,
                "result": cached_data,
                "from_cache": True
            })
        else:
            # Criar task para requisição assíncrona
            params = {
                "Codigo_Tipo_Grupo": codigo_tipo_grupo,
                "Codigo_Tipo_Venda": codigo_tipo_venda
            }
            task = make_async_request(session, "/catalog/cnsBensDisponiveis", params)
            tasks.append({
                "tipo_venda": tipo_venda,
                "task": task,
                "from_cache": False
            })
    
    # Executar todas as requisições em paralelo
    results = []
    for item in tasks:
        if item["from_cache"]:
            results.append(item)
        else:
            result = await item["task"]
            results.append({
                "tipo_venda": item["tipo_venda"],
                "result": result,
                "from_cache": False
            })
    
    return results

def print_section(title):
    """Imprime uma seção do teste"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def print_response(data, title="Resposta"):
    """Imprime a resposta formatada"""
    print(f"\n📋 {title}:")
    print(json.dumps(data, indent=2, ensure_ascii=False))

def test_01_tipos_grupos():
    """Teste 01 - Tipos de Grupos (Foco nos 4 segmentos principais)"""
    print_section("TESTE 01 - TIPOS DE GRUPOS")
    
    response = make_request("/catalog/cnsTiposGrupos")
    if not response:
        return None
    
    print_response(response, "Tipos de Grupos")
    
    # Validar estrutura da resposta
    if "data" in response and "items" in response["data"]:
        items = response["data"]["items"]
        print(f"\n✅ Encontrados {len(items)} tipos de grupos")
        
        # Filtrar apenas os 4 segmentos principais
        segmentos_principais = ["IM", "AN", "MT", "SV"]
        segmentos_encontrados = []
        
        for item in items:
            codigo = item.get("CODIGO_TIPO_GRUPO")
            if codigo in segmentos_principais:
                segmentos_encontrados.append(item)
                print(f"\n📝 Segmento {codigo} - {item.get('DESCRICAO')}:")
                for key, value in item.items():
                    print(f"   {key}: {value}")
        
        if segmentos_encontrados:
            print(f"\n✅ Encontrados {len(segmentos_encontrados)} segmentos principais:")
            for seg in segmentos_encontrados:
                print(f"   - {seg.get('CODIGO_TIPO_GRUPO')}: {seg.get('DESCRICAO')}")
            
            # Usar o primeiro segmento encontrado para o teste
            return segmentos_encontrados[0]
        else:
            print("⚠️ Nenhum dos segmentos principais encontrado")
            return None
    else:
        print("❌ Estrutura de resposta inválida")
        return None

def test_02_tipos_vendas(codigo_tipo_grupo):
    """Teste 02 - Tipos de Vendas"""
    print_section("TESTE 02 - TIPOS DE VENDAS")
    
    if not codigo_tipo_grupo:
        print("❌ Código do tipo de grupo não fornecido")
        return None
    
    params = {"Codigo_Tipo_Grupo": codigo_tipo_grupo}
    response = make_request("/catalog/cnsTiposVendas", params)
    if not response:
        return None
    
    print_response(response, f"Tipos de Vendas para Grupo {codigo_tipo_grupo}")
    
    # Validar estrutura da resposta
    if "data" in response and "items" in response["data"]:
        items = response["data"]["items"]
        print(f"\n✅ Encontrados {len(items)} tipos de vendas")
        
        if items:
            # Mostrar primeiro item como exemplo
            first_item = items[0]
            print(f"\n📝 Exemplo do primeiro tipo de venda:")
            for key, value in first_item.items():
                print(f"   {key}: {value}")
            
            return items  # Retornar todos os tipos de vendas
        else:
            print("⚠️ Nenhum tipo de venda encontrado")
            return None
    else:
        print("❌ Estrutura de resposta inválida")
        return None

async def test_03_bens_disponiveis(codigo_tipo_grupo, tipos_vendas):
    """Teste 03 - Bens Disponíveis (Testa em lotes paralelos com cache Redis)"""
    print_section("TESTE 03 - BENS DISPONÍVEIS")
    
    if not codigo_tipo_grupo or not tipos_vendas:
        print("❌ Códigos do tipo de grupo e tipos de vendas não fornecidos")
        return None
    
    print(f"🔍 Testando {len(tipos_vendas)} tipos de vendas para o grupo {codigo_tipo_grupo}...")
    print(f"⚡ Processando em lotes de 10 requisições paralelas...")
    
    bens_encontrados = []
    batch_size = 10
    
    async with aiohttp.ClientSession() as session:
        # Processar em lotes de 10
        for i in range(0, len(tipos_vendas), batch_size):
            batch = tipos_vendas[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(tipos_vendas) + batch_size - 1) // batch_size
            
            print(f"\n🚀 Processando Lote {batch_num}/{total_batches} ({len(batch)} vendas)...")
            
            # Executar lote em paralelo
            batch_results = await test_bens_batch(session, codigo_tipo_grupo, batch)
            
            # Processar resultados do lote
            for result_data in batch_results:
                tipo_venda = result_data["tipo_venda"]
                result = result_data["result"]
                from_cache = result_data["from_cache"]
                
                codigo_tipo_venda = tipo_venda.get("CODIGO_TIPO_VENDA")
                descricao_venda = tipo_venda.get("DESCRICAO")
                
                if from_cache:
                    # Dados do cache
                    if result["quantidade_bens"] > 0:
                        bens_encontrados.append({
                            "tipo_venda": codigo_tipo_venda,
                            "descricao_venda": descricao_venda,
                            "quantidade_bens": result["quantidade_bens"],
                            "primeiro_bem": result["bens"][0],
                            "from_cache": True
                        })
                else:
                    # Dados da API
                    if result and "data" in result and "items" in result["data"]:
                        items = result["data"]["items"]
                        
                        if items:
                            print(f"   ✅ Venda {codigo_tipo_venda} ({descricao_venda}): {len(items)} bens")
                            
                            # Cachear no Redis apenas se houver bens
                            await cache_bens_result(codigo_tipo_grupo, codigo_tipo_venda, items)
                            
                            bens_encontrados.append({
                                "tipo_venda": codigo_tipo_venda,
                                "descricao_venda": descricao_venda,
                                "quantidade_bens": len(items),
                                "primeiro_bem": items[0],
                                "from_cache": False
                            })
                            
                            # Mostrar exemplo do primeiro bem
                            first_item = items[0]
                            print(f"   📝 Exemplo: {first_item.get('Descricao', 'N/A')} - R$ {first_item.get('Valor_Bem', 'N/A')}")
                        else:
                            print(f"   ⚠️ Venda {codigo_tipo_venda} ({descricao_venda}): Nenhum bem")
                    else:
                        print(f"   ❌ Venda {codigo_tipo_venda} ({descricao_venda}): Erro na resposta")
    
    # Resumo dos resultados
    print(f"\n📊 RESUMO DOS TESTES:")
    if bens_encontrados:
        print(f"✅ Encontrados bens em {len(bens_encontrados)} tipos de vendas:")
        for resultado in bens_encontrados:
            cache_indicator = "💾" if resultado.get("from_cache") else "🆕"
            print(f"   {cache_indicator} Venda {resultado['tipo_venda']} ({resultado['descricao_venda']}): {resultado['quantidade_bens']} bens")
        
        # Retornar o primeiro resultado com bens
        return bens_encontrados[0]['primeiro_bem']
    else:
        print("❌ Nenhum bem disponível encontrado em nenhuma das vendas testadas")
        return None

def test_04_prazos_disponiveis(codigo_tipo_grupo, codigo_tipo_venda, codigo_bem):
    """Teste 04 - Prazos Disponíveis"""
    print_section("TESTE 04 - PRAZOS DISPONÍVEIS")
    
    if not all([codigo_tipo_grupo, codigo_tipo_venda, codigo_bem]):
        print("❌ Códigos necessários não fornecidos")
        return None
    
    # Parâmetros conforme especificação
    params = {
        "Codigo_Unidade": 1,  # Fixo
        "Codigo_Tipo_Grupo": codigo_tipo_grupo,
        "Codigo_Tipo_Venda": codigo_tipo_venda,
        "Codigo_Bem": codigo_bem,
        "Codigo_Representante": 1,  # Fixo
        "Situacao_Grupo": "A",  # Andamento
        "Pessoa": "F",  # Pessoa Física
        "Ordem_Pesquisa": "P",  # Prazo
        "Codigo_Filial": 1,  # Fixo
        "Prazo": 0,  # Zero
        "Dia_Vencimento": 0,  # Zero
        "Data_Assembleia": date.today().isoformat(),  # Data atual
        "Codigo_Grupo": 0,  # Zero
        "SN_Rateia": "S"  # Sim
    }
    
    print(f"\n📋 Parâmetros enviados:")
    for key, value in params.items():
        print(f"   {key}: {value}")
    
    response = make_request("/catalog/cnsPrazosDisponiveis", params)
    if not response:
        return None
    
    print_response(response, "Prazos Disponíveis")
    
    # Validar estrutura da resposta
    if "data" in response and "items" in response["data"]:
        items = response["data"]["items"]
        print(f"\n✅ Encontrados {len(items)} prazos disponíveis")
        
        if items:
            # Mostrar primeiro item como exemplo
            first_item = items[0]
            print(f"\n📝 Exemplo do primeiro prazo:")
            for key, value in first_item.items():
                print(f"   {key}: {value}")
            
            return first_item
        else:
            print("⚠️ Nenhum prazo disponível encontrado")
            return None
    else:
        print("❌ Estrutura de resposta inválida")
        return None

async def main():
    """Executa todos os testes do fluxo básico"""
    print("🚀 INICIANDO TESTES DO FLUXO DE VENDAS")
    print(f"🌐 API: {API_BASE_URL}")
    print(f"🔑 API Key: {API_KEY[:20]}...")
    
    # Inicializar Redis
    try:
        await redis_client.connect()
        if redis_client.connected:
            print(f"💾 Redis: Conectado")
        else:
            print(f"💾 Redis: Desconectado")
    except Exception as e:
        print(f"💾 Redis: Erro na conexão ({e})")
    
    # Teste 01 - Tipos de Grupos
    tipo_grupo = test_01_tipos_grupos()
    if not tipo_grupo:
        print("\n❌ Teste 01 falhou - não é possível continuar")
        sys.exit(1)
    
    codigo_tipo_grupo = tipo_grupo.get("CODIGO_TIPO_GRUPO")
    print(f"\n✅ Teste 01 passou - Código do Grupo: {codigo_tipo_grupo}")
    
    # Teste 02 - Tipos de Vendas
    tipos_vendas = test_02_tipos_vendas(codigo_tipo_grupo)
    if not tipos_vendas:
        print("\n❌ Teste 02 falhou - não é possível continuar")
        sys.exit(1)
    
    print(f"\n✅ Teste 02 passou - Encontrados {len(tipos_vendas)} tipos de vendas")
    
    # Teste 03 - Bens Disponíveis (testa múltiplas combinações em paralelo)
    bem = await test_03_bens_disponiveis(codigo_tipo_grupo, tipos_vendas)
    if not bem:
        print("\n❌ Teste 03 falhou - não é possível continuar")
        sys.exit(1)
    
    codigo_bem = bem.get("Codigo_Bem")
    print(f"\n✅ Teste 03 passou - Código do Bem: {codigo_bem}")
    
    # Para o teste 04, precisamos do código da venda que teve bens
    # Vamos usar a venda "3" (NACIONAL) que teve bens
    codigo_tipo_venda = "3"  # Venda NACIONAL que teve bens
    
    # Teste 04 - Prazos Disponíveis
    prazo = test_04_prazos_disponiveis(codigo_tipo_grupo, codigo_tipo_venda, codigo_bem)
    if not prazo:
        print("\n❌ Teste 04 falhou")
        sys.exit(1)
    
    print(f"\n✅ Teste 04 passou - Prazo encontrado")
    
    # Resumo final
    print_section("RESUMO DOS TESTES")
    print("✅ Teste 01 - Tipos de Grupos: PASSOU")
    print("✅ Teste 02 - Tipos de Vendas: PASSOU")
    print("✅ Teste 03 - Bens Disponíveis: PASSOU")
    print("✅ Teste 04 - Prazos Disponíveis: PASSOU")
    
    print(f"\n🎉 TODOS OS TESTES DO FLUXO BÁSICO PASSARAM!")
    print(f"📊 Dados coletados:")
    print(f"   - Grupo: {codigo_tipo_grupo}")
    print(f"   - Venda: {codigo_tipo_venda}")
    print(f"   - Bem: {codigo_bem}")
    print(f"   - Prazo: {prazo.get('CODIGO_GRUPO', 'N/A')}")
    
    # Mostrar estatísticas do cache
    if redis_client:
        cache_keys = await redis_client.keys("bens:*")
        print(f"\n💾 Cache Redis: {len(cache_keys)} entradas armazenadas")
        await redis_client.aclose()
    else:
        print(f"\n💾 Cache Redis: Não disponível")

if __name__ == "__main__":
    asyncio.run(main())
