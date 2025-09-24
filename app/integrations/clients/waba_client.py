import os, httpx
class WABAClient:
    def __init__(self):
        self.base=os.environ.get("WABA_BASE_URL","").rstrip("/")
        self.token=os.environ.get("WABA_TOKEN","")
        self.client=httpx.AsyncClient(timeout=20)
    async def send_text(self, phone: str, text: str, template: str|None=None, variables: list|None=None):
        url=f"{self.base}/messages"
        payload={"messaging_product":"whatsapp","to":phone}
        if template:
            payload["type"]="template"
            payload["template"]={"name":template,"language":{"code":"pt_BR"},"components":[{"type":"body","parameters":[{"type":"text","text":v} for v in (variables or [])]}]}
        else:
            payload["type"]="text"; payload["text"]={"body": text}
        r=await self.client.post(url, json=payload, headers={"Authorization": f"Bearer {self.token}"})
        r.raise_for_status(); return r.json()
    async def close(self): await self.client.aclose()
