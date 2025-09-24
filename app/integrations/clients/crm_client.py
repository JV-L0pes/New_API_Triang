import os, httpx
class CRMClient:
    def __init__(self):
        self.base=os.environ.get("CRM_BASE_URL","").rstrip("/")
        self.key=os.environ.get("CRM_API_KEY","")
        self.client=httpx.AsyncClient(timeout=20)
    async def upsert_lead(self, payload: dict):
        r=await self.client.post(f"{self.base}/leads", json=payload, headers={"Authorization": f"Bearer {self.key}"})
        r.raise_for_status(); return r.json()
    async def upsert_opportunity(self, payload: dict):
        r=await self.client.post(f"{self.base}/opportunities", json=payload, headers={"Authorization": f"Bearer {self.key}"})
        r.raise_for_status(); return r.json()
    async def close(self): await self.client.aclose()
