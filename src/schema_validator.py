"""
schema_validator.py

Validasi dan normalisasi output final sesuai AI-DS-SPEC.
Menggunakan Pydantic v2 untuk strict type enforcement.
"""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, field_validator, model_validator
import re


VALID_CATEGORIES = [
    "makanan", "transport", "belanja", "hiburan",
    "kesehatan", "pendidikan", "tagihan", "pemasukan", "lainnya"
]

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class InvoiceOutput(BaseModel):
    merchant: str = ""
    date: Optional[str] = None
    total: Optional[int] = None
    items: list[str] = []
    category: str = "lainnya"
    confidence: float = 0.0

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        if v not in VALID_CATEGORIES:
            return "lainnya"
        return v

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not DATE_RE.match(v):
            return None
        return v

    @field_validator("confidence")
    @classmethod
    def clamp_confidence(cls, v: float) -> float:
        return round(max(0.0, min(1.0, v)), 4)

    @field_validator("total")
    @classmethod
    def validate_total(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            return None
        return v

    @field_validator("merchant")
    @classmethod
    def clean_merchant(cls, v: str) -> str:
        return v.strip()

    def to_dict(self) -> dict:
        return self.model_dump()


def validate_schema(raw: dict) -> dict:
    """Validasi raw dict ke InvoiceOutput, return dict."""
    out = InvoiceOutput(**raw)
    return out.to_dict()
