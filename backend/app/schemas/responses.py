from typing import Any

from pydantic import BaseModel, Field


class ApiEnvelope(BaseModel):
    data: Any
    generated_at: str
    symbol: str | None = None
    meta: dict[str, Any] | None = None


class CompanyOut(BaseModel):
    symbol: str
    yahoo_symbol: str
    name: str
    sector: str
    exchange: str = Field(default="NSE")
