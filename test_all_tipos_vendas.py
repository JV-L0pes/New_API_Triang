#!/usr/bin/env python3
"""
Script para testar todos os tipos de vendas e verificar quais retornam bens disponíveis
"""

import asyncio
import httpx
import json
from typing import List, Dict, Any

API_BASE_URL = "http://localhost:8000"
API_KEY = "test-api-key-123"

async def get_tipos_vendas(codigo_tipo_grupo: str) -> List[Dict[str, Any]]:
    """Busca todos os tipos de vendas para um grupo"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/catalog/cnsTiposVendas",
            params={"Codigo_Tipo_Grupo": codigo_tipo_grupo},
            headers={"X-API-Key": API_KEY}
        )
        response.raise_for_status()
        data = response.json()
        return data["data"]["items"]

async def test_bens_disponiveis(codigo_tipo_grupo: str, codigo_tipo_venda: str) -> Dict[str, Any]:
    """Testa se há bens disponíveis para um tipo de venda"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{API_BASE_URL}/catalog/cnsBensDisponiveis",
                params={
                    "Codigo_Tipo_Grupo": codigo_tipo_grupo,
                    "Codigo_Tipo_Venda": codigo_tipo_venda
                },
                headers={"X-API-Key": API_KEY}
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "codigo_tipo_venda": codigo_tipo_venda,
                "descricao": "N/A",  # Será preenchido depois
                "bens_count": len(data["data"]["items"]) if data["data"]["items"] else 0,
                "has_bens": len(data["data"]["items"]) > 0,
                "status": "success"
            }
        except Exception as e:
            return {
                "codigo_tipo_venda": codigo_tipo_venda,
                "descricao": "N/A",
                "bens_count": 0,
                "has_bens": False,
                "status": "error",
                "error": str(e)
            }

async def main():
    """Função principal"""
    print("🔍 Testando todos os tipos de vendas para AN (Automóveis Nacionais)...")
    print("=" * 80)
    
    # Buscar todos os tipos de vendas
    tipos_vendas = await get_tipos_vendas("AN")
    print(f"📋 Encontrados {len(tipos_vendas)} tipos de vendas")
    print()
    
    # Testar cada tipo de venda
    resultados = []
    for i, tipo_venda in enumerate(tipos_vendas, 1):
        codigo = tipo_venda["Codigo_Tipo_Venda"]
        descricao = tipo_venda["Descricao"]
        
        print(f"[{i:3d}/{len(tipos_vendas)}] Testando {codigo}: {descricao[:50]}...", end=" ")
        
        resultado = await test_bens_disponiveis("AN", codigo)
        resultado["descricao"] = descricao
        resultados.append(resultado)
        
        if resultado["has_bens"]:
            print(f"✅ {resultado['bens_count']} bens")
        elif resultado["status"] == "error":
            print(f"❌ Erro: {resultado.get('error', 'Unknown')}")
        else:
            print("❌ Sem bens")
    
    print()
    print("=" * 80)
    print("📊 RESUMO DOS RESULTADOS:")
    print("=" * 80)
    
    # Filtrar apenas os que têm bens
    com_bens = [r for r in resultados if r["has_bens"]]
    sem_bens = [r for r in resultados if not r["has_bens"] and r["status"] == "success"]
    com_erro = [r for r in resultados if r["status"] == "error"]
    
    print(f"✅ Tipos de vendas COM bens: {len(com_bens)}")
    print(f"❌ Tipos de vendas SEM bens: {len(sem_bens)}")
    print(f"🚨 Tipos de vendas COM ERRO: {len(com_erro)}")
    print()
    
    if com_bens:
        print("🎯 TIPOS DE VENDAS COM BENS DISPONÍVEIS:")
        print("-" * 60)
        for resultado in com_bens:
            print(f"  {resultado['codigo_tipo_venda']:3s}: {resultado['descricao'][:50]:50s} ({resultado['bens_count']} bens)")
        print()
    
    if com_erro:
        print("🚨 TIPOS DE VENDAS COM ERRO:")
        print("-" * 60)
        for resultado in com_erro:
            print(f"  {resultado['codigo_tipo_venda']:3s}: {resultado['descricao'][:50]:50s} - {resultado.get('error', 'Unknown')}")
        print()
    
    # Salvar resultados em arquivo
    with open("resultados_tipos_vendas.json", "w", encoding="utf-8") as f:
        json.dump({
            "resumo": {
                "total_tipos_vendas": len(tipos_vendas),
                "com_bens": len(com_bens),
                "sem_bens": len(sem_bens),
                "com_erro": len(com_erro)
            },
            "detalhes": resultados
        }, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Resultados salvos em: resultados_tipos_vendas.json")
    
    # Conclusão
    if com_bens:
        print(f"\n🎉 SUCESSO! Encontrados {len(com_bens)} tipos de vendas com bens disponíveis!")
        print("   O endpoint cnsBensDisponiveis está funcionando corretamente.")
    else:
        print(f"\n⚠️  ATENÇÃO! Nenhum tipo de venda retornou bens.")
        print("   Pode ser um problema de parsing ou não há bens disponíveis na API Newcon.")

if __name__ == "__main__":
    asyncio.run(main())
