from typing import Any
from pydantic import BaseModel

class ErrorOut(BaseModel):
    code: str
    message: str

class Envelope(BaseModel):
    ok: bool
    data: Any | None = None
    error: ErrorOut | None = None

def ok(data: Any) -> Envelope:
    return Envelope(ok=True, data=data)

def fail(code: str, message: str) -> Envelope:
    return Envelope(ok=False, error=ErrorOut(code=code, message=message))
