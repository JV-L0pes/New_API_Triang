from fastapi import APIRouter, Depends, Query
from datetime import date
from app.security import require_api_key
from app.schemas.base import ok, Envelope
from app.infrastructure.newcon_client import NewconClient
router=APIRouter(dependencies=[Depends(require_api_key)], tags=["catalog"])
@router.get("/cnsTiposGrupos", response_model=Envelope)
async def tipos(): nc=NewconClient(); data=await nc.call("cnsTiposGrupos", {}); await nc.close(); return ok(data)
@router.get("/cnsTiposVendas", response_model=Envelope)
async def vendas(Codigo_Tipo_Grupo:str): nc=NewconClient(); data=await nc.call("cnsTiposVendas", {"Codigo_Tipo_Grupo": Codigo_Tipo_Grupo}); await nc.close(); return ok(data)
@router.get("/cnsBensDisponiveis", response_model=Envelope)
async def bens(Codigo_Tipo_Grupo:str, Codigo_Tipo_Venda:str, valor_busca:float=None, tolerancia_percentual:float=5.0): 
    from app.infrastructure.cache import hybrid_cache
    
    # Chave do cache baseada nos parâmetros
    cache_key = f"bens_disponiveis:{Codigo_Tipo_Grupo}:{Codigo_Tipo_Venda}"
    
    async def fetch_bens():
        nc=NewconClient()
        # Codigo_Filial sempre será 001 (hardcoded)
        data=await nc.call("cnsBensDisponiveis", {
            "Codigo_Filial": "001",
            "Codigo_Tipo_Grupo": Codigo_Tipo_Grupo,
            "Codigo_Tipo_Venda": Codigo_Tipo_Venda
        })
        await nc.close()
        return data
    
    # Busca no cache (TTL de 30 minutos = 1800 segundos)
    data = await hybrid_cache.get_or_set(cache_key, fetch_bens, ttl_seconds=1800)
    
    # Se não especificou valor de busca, retorna todos os bens
    if valor_busca is None:
        return ok(data)
    
    # Aplicar tolerância e buscar o mais próximo
    if "items" in data and data["items"]:
        items = data["items"]
        
        # Calcular tolerância (±5% por padrão)
        tolerancia_valor = valor_busca * (tolerancia_percentual / 100)
        valor_min = valor_busca - tolerancia_valor
        valor_max = valor_busca + tolerancia_valor
        
        # Filtrar bens dentro da tolerância
        bens_tolerancia = []
        for item in items:
            if "Valor_Bem" in item and item["Valor_Bem"]:
                valor_bem = float(item["Valor_Bem"])
                if valor_min <= valor_bem <= valor_max:
                    bens_tolerancia.append(item)
        
        # Se encontrou bens na tolerância, retorna eles
        if bens_tolerancia:
            return ok({"items": bens_tolerancia, "filtro_aplicado": f"Tolerância ±{tolerancia_percentual}%", "valor_busca": valor_busca})
        
        # Se não encontrou na tolerância, busca o mais próximo
        bens_com_valor = [item for item in items if "Valor_Bem" in item and item["Valor_Bem"]]
        if bens_com_valor:
            # Ordenar por proximidade do valor buscado
            bens_com_valor.sort(key=lambda x: abs(float(x["Valor_Bem"]) - valor_busca))
            mais_proximo = bens_com_valor[0]
            return ok({
                "items": [mais_proximo], 
                "filtro_aplicado": "Mais próximo disponível (fora da tolerância)",
                "valor_busca": valor_busca,
                "valor_encontrado": mais_proximo["Valor_Bem"]
            })
    
    return ok(data)
@router.get("/cnsPrazosDisponiveis", response_model=Envelope)
async def prazos(Codigo_Unidade:int, Codigo_Tipo_Grupo:str, Codigo_Tipo_Venda:str, Codigo_Bem:int, Codigo_Representante:int,
                 Situacao_Grupo:str=Query("A", pattern="^[AFX]$"), Pessoa:str=Query("F", pattern="^[FJ]$"),
                 Ordem_Pesquisa:str=Query("P", pattern="^[PG]$"), Codigo_Filial:int=1, Prazo:int=0, Dia_Vencimento:int=0,
                 Data_Assembleia:date=date.today(), Codigo_Grupo:int=0, SN_Rateia:str=Query("S", pattern="^[SN]$")):
    payload={"Codigo_Unidade":Codigo_Unidade,"Codigo_Tipo_Grupo":Codigo_Tipo_Grupo,"Codigo_Tipo_Venda":Codigo_Tipo_Venda,"Codigo_Bem":Codigo_Bem,
             "Codigo_Representante":Codigo_Representante,"Situacao_Grupo":Situacao_Grupo,"Pessoa":Pessoa,"Ordem_Pesquisa":Ordem_Pesquisa,
             "Codigo_Filial":Codigo_Filial,"Prazo":Prazo,"Dia_Vencimento":Dia_Vencimento,"Data_Assembleia":Data_Assembleia.isoformat(),
             "Codigo_Grupo":Codigo_Grupo,"SN_Rateia":SN_Rateia}
    nc=NewconClient(); data=await nc.call("cnsPrazosDisponiveis", payload); await nc.close(); return ok(data)
@router.get("/cnsRegraCobranca", response_model=Envelope)
async def regra(Codigo_Grupo:int, Prazo:int): nc=NewconClient(); data=await nc.call("cnsRegraCobranca", {"Codigo_Grupo":Codigo_Grupo,"Prazo":Prazo}); await nc.close(); return ok(data)
@router.get("/cnsCaracteristicasGrupos", response_model=Envelope)
async def car(Codigo_Grupo:int): nc=NewconClient(); data=await nc.call("cnsCaracteristicasGrupos", {"Codigo_Grupo":Codigo_Grupo}); await nc.close(); return ok(data)
@router.get("/cnsReservaCotas", response_model=Envelope)
async def reserva(Codigo_Grupo_Inicial:int, Codigo_Grupo_Final:int): nc=NewconClient(); data=await nc.call("cnsReservaCotas", {"Codigo_Grupo_Inicial":Codigo_Grupo_Inicial,"Codigo_Grupo_Final":Codigo_Grupo_Final}); await nc.close(); return ok(data)
@router.get("/cnsCalendarioAssembleias", response_model=Envelope)
async def cal(): nc=NewconClient(); data=await nc.call("cnsCalendarioAssembleias", {}); await nc.close(); return ok(data)
