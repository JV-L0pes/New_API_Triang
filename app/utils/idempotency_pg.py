import os, json, hashlib, datetime
from typing import Optional
# from sqlalchemy import create_engine, text  # Comentado - não vamos usar banco próprio
DB_URL = os.environ.get("DATABASE_URL_IDEMPOTENCY","")
# engine = create_engine(DB_URL, pool_pre_ping=True, pool_recycle=300) if DB_URL else None
engine = None  # Desabilitado - sem banco próprio
def _hash(payload: dict | None) -> str:
    return hashlib.sha256((json.dumps(payload, sort_keys=True) if payload else "").encode()).hexdigest()
def save(route: str, key: str, payload: dict | None, response: dict, ttl_seconds: int = 86400):
    if not engine: return
    k = f"{route}:{key}:{_hash(payload)}"
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(seconds=ttl_seconds)
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO idempotency (k, route, payload_hash, response, expires_at)
            VALUES (:k, :route, :payload_hash, :response, :expires_at)
            ON CONFLICT (k) DO UPDATE SET response=EXCLUDED.response, expires_at=EXCLUDED.expires_at
        """), dict(k=k, route=route, payload_hash=_hash(payload), response=json.dumps(response), expires_at=expires_at))
def get(route: str, key: str, payload: dict | None) -> Optional[dict]:
    if not engine: return None
    k = f"{route}:{key}:{_hash(payload)}"
    with engine.begin() as conn:
        row = conn.execute(text("""SELECT response, expires_at FROM idempotency WHERE k=:k"""), dict(k=k)).fetchone()
        if not row: return None
        response, expires_at = row
        if expires_at and expires_at < datetime.datetime.utcnow():
            conn.execute(text("DELETE FROM idempotency WHERE k=:k"), dict(k=k)); return None
        return json.loads(response)
