import os, httpx
import xml.etree.ElementTree as ET
import xmltodict
import re

class NewconClient:
    def __init__(self):
        self.base = os.environ.get("NEWCON_BASE_URL","").rstrip("/")
        self.mode = os.environ.get("NEWCON_MODE","soap").lower()
        self.soap_ns = os.environ.get("SOAP_NAMESPACE","http://tempuri.org/")
        self.timeout = int(os.environ.get("NEWCON_TIMEOUT_SECONDS","30"))
        self.client = httpx.AsyncClient(timeout=self.timeout)

    async def call(self, method: str, params: dict):
        if self.mode == "rest":
            r = await self.client.get(f"{self.base}/{method}", params=params)
            r.raise_for_status()
            return r.json() if "application/json" in r.headers.get("content-type","") else {"raw": r.text}
        xml = await self._soap_call(method, params)
        try:
            return self._parse(method, xml)
        except Exception as e:
            return {"raw": xml, "parse_error": str(e)}

    async def _soap_call(self, method: str, params: dict) -> str:
        env = self._soap_envelope(method, params)
        # A URL base já inclui o .asmx, então não precisamos adicionar novamente
        url = self.base  # https://webatendimento.consorciotriangulo.com.br/wsregvenda/wsRegVenda.asmx
        headers = {"Content-Type": "text/xml; charset=utf-8", "SOAPAction": f"http://www.cnpm.com.br/{method}"}
        
        # Debug: log da requisição
        try:
            r = await self.client.post(url, content=env, headers=headers)
            r.raise_for_status()
            return r.text
        except Exception as e:
            raise

    def _soap_envelope(self, method: str, params: dict) -> bytes:
        # Usar o namespace correto da Newcon (como no projeto legado)
        soap_env = "http://schemas.xmlsoap.org/soap/envelope/"
        newcon_ns = "http://www.cnpm.com.br/"
        
        root = ET.Element("{%s}Envelope" % soap_env)
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        root.set("xmlns:xsd", "http://www.w3.org/2001/XMLSchema")
        root.set("xmlns:soap", soap_env)
        
        body = ET.SubElement(root, "{%s}Body" % soap_env)
        m = ET.SubElement(body, method)
        m.set("xmlns", newcon_ns)
        
        for k, v in params.items():
            if v is not None:
                el = ET.SubElement(m, k)
                el.text = str(v)
        
        return ET.tostring(root, encoding="utf-8", xml_declaration=True)

    def _parse(self, method: str, xml_text: str) -> dict:
        """Parse XML response para dict Python usando xmltodict (igual à API legada)"""
        try:
            # Parse XML para dict usando xmltodict (igual à API legada)
            parsed = xmltodict.parse(xml_text)
            
            # Extrai o resultado da resposta SOAP
            if 'soap:Envelope' in parsed:
                body = parsed['soap:Envelope']['soap:Body']
                # Pega a primeira chave que não seja 'soap:Body'
                for key, value in body.items():
                    if not key.startswith('soap:'):
                        # Remove o sufixo 'Response' se existir
                        result_key = key.replace('Response', '') + 'Result'
                        if result_key in value:
                            result = value[result_key]
                        else:
                            result = value
                        
                        # Normaliza chaves comuns do dataset (diffgr:diffgram -> diffgram)
                        if isinstance(result, dict):
                            result = self._normalize_dataset_keys(result)
                        return self._extract_items_from_dataset(result, method)

            # Se não é SOAP, verifica se é um DataSet direto da Newcon
            if 'DataSet' in parsed:
                result = parsed['DataSet']
                # Normaliza chaves comuns do dataset (diffgr:diffgram -> diffgram)
                if isinstance(result, dict):
                    result = self._normalize_dataset_keys(result)
                return self._extract_items_from_dataset(result, method)

            return {"items": []}
        except Exception as e:
            # Se falhar o parse, retorna estrutura vazia
            return {"items": [], "parse_error": str(e)}

    def _normalize_dataset_keys(self, data: dict) -> dict:
        """Normaliza chaves do payload Newcon para formato esperado pelos parsers (igual à API legada)"""
        try:
            # Copia raso para evitar mutação inesperada
            out = dict(data)
            # Normaliza diffgram
            if 'diffgram' not in out and 'diffgr:diffgram' in out:
                out['diffgram'] = out.pop('diffgr:diffgram')
            # Algumas respostas trazem 'Diffgram' capitalizado
            if 'diffgram' not in out and 'Diffgram' in out:
                out['diffgram'] = out.pop('Diffgram')
            # Dentro do diffgram, às vezes o NewDataSet vem com namespace
            dg = out.get('diffgram')
            if isinstance(dg, dict):
                # Se existir apenas uma chave, pegar o seu valor caso traga wrapper
                if 'NewDataSet' not in dg and len(dg.keys()) == 1:
                    only_key = next(iter(dg.keys()))
                    maybe_nds = dg.get(only_key)
                    if isinstance(maybe_nds, dict) and 'NewDataSet' in maybe_nds:
                        out['diffgram'] = maybe_nds
                # Em alguns casos, NewDataSet pode estar sob chave vazia
                if 'NewDataSet' not in out['diffgram']:
                    for k, v in list(out['diffgram'].items()):
                        if isinstance(v, dict) and 'NewDataSet' in v:
                            out['diffgram'] = v
                            break
            return out
        except Exception:
            return data

    def _extract_items_from_dataset(self, dataset: dict, method: str) -> dict:
        """Extrai items do dataset usando a mesma lógica da API legada"""
        try:
            if not dataset or "diffgram" not in dataset:
                return {"items": []}
            
            nds = dataset["diffgram"].get("NewDataSet")
            if not isinstance(nds, dict):
                return {"items": []}
            
            rows = []
            for _, val in nds.items():
                if isinstance(val, list):
                    rows.extend([item for item in val if isinstance(item, dict)])
                elif isinstance(val, dict):
                    rows.append(val)
            
            return {"items": rows}
        except Exception as e:
            return {"items": [], "extract_error": str(e)}

        # Para outros métodos, retorna estrutura básica
        return {"items": []}
    
    async def close(self):
        """Fecha o cliente HTTP"""
        await self.client.aclose()
