import os, httpx
class GraphClient:
    def __init__(self):
        self.tenant=os.environ.get("GRAPH_TENANT_ID","")
        self.client_id=os.environ.get("GRAPH_CLIENT_ID","")
        self.client_secret=os.environ.get("GRAPH_CLIENT_SECRET","")
        self.client=httpx.AsyncClient(timeout=20)
        self.token=None
    async def _get_token(self):
        url=f"https://login.microsoftonline.com/{self.tenant}/oauth2/v2.0/token"
        data={"grant_type":"client_credentials","client_id":self.client_id,"client_secret":self.client_secret,"scope":"https://graph.microsoft.com/.default"}
        r=await self.client.post(url, data=data); r.raise_for_status(); self.token=r.json()["access_token"]
    async def send_mail(self, to: list[str], subject: str, body_html: str, attachments: list[dict]|None=None):
        if not self.token: await self._get_token()
        url="https://graph.microsoft.com/v1.0/users/me/sendMail"
        msg={"message": {"subject": subject, "body": {"contentType":"HTML","content": body_html}, "toRecipients": [{"emailAddress":{"address": x}} for x in to]},"saveToSentItems": True}
        if attachments:
            msg["message"]["attachments"]=[{"@odata.type":"#microsoft.graph.fileAttachment","name":a["filename"],"contentBytes":a["base64"]} for a in attachments]
        r=await self.client.post(url, json=msg, headers={"Authorization": f"Bearer {self.token}"}); r.raise_for_status(); return {"ok": True}
    async def close(self): await self.client.aclose()
