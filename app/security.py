import os, hmac, hashlib
from fastapi import Header, HTTPException, Request

async def require_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    expected = os.environ.get("API_KEY", "")
    if not expected or x_api_key != expected:
        raise HTTPException(status_code=401, detail="invalid api key")

def verify_hmac(request: Request, signature: str | None, secret_env: str) -> None:
    secret = os.environ.get(secret_env, "")
    if not secret or not signature:
        return  # skip if not set
    body = getattr(request, "_body", None)
    if body is None:
        body = b""
    mac = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(mac, signature):
        raise HTTPException(status_code=401, detail="invalid webhook signature")
