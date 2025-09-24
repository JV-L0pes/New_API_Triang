import os, httpx, time
import jwt
class DocuSignClient:
    def __init__(self):
        self.base=os.environ.get("DOCUSIGN_BASE_URL","").rstrip("/")
        self.integrator=os.environ.get("DOCUSIGN_INTEGRATOR_KEY","")
        self.user=os.environ.get("DOCUSIGN_USER_ID","")
        self.account=os.environ.get("DOCUSIGN_ACCOUNT_ID","")
        self.private_key=os.environ.get("DOCUSIGN_PRIVATE_KEY","").encode()
        self.client=httpx.AsyncClient(timeout=30)
        self.token=None
    async def _get_token(self):
        now=int(time.time())
        payload={"iss": self.integrator, "sub": self.user, "aud": "account-d.docusign.com", "iat": now, "exp": now+3600, "scope":"signature impersonation"}
        jwt_assertion=jwt.encode(payload, self.private_key, algorithm="RS256")
        r=await self.client.post("https://account-d.docusign.com/oauth/token", data={"grant_type":"urn:ietf:params:oauth:grant-type:jwt-bearer","assertion": jwt_assertion})
        r.raise_for_status(); self.token=r.json()["access_token"]
    async def create_envelope(self, subject: str, emails: list[str], pdf_base64: str, name: str):
        if not self.token: await self._get_token()
        url=f"{self.base}/v2.1/accounts/{self.account}/envelopes"
        doc={"documentBase64": pdf_base64, "name": name, "fileExtension":"pdf", "documentId":"1"}
        recipients={"signers":[{"email": emails[0], "name": name, "recipientId":"1", "routingOrder":"1"}]}
        body={"emailSubject": subject, "documents":[doc], "recipients": recipients, "status":"sent"}
        r=await self.client.post(url, json=body, headers={"Authorization": f"Bearer {self.token}"})
        r.raise_for_status(); return r.json()
    async def close(self): await self.client.aclose()
