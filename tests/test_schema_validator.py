"""
Test unit untuk schema_validator.py
"""
import pytest
from src.schema_validator import validate_schema


def test_valid_full():
    raw = {
        "merchant": "Indomaret",
        "date": "2026-04-23",
        "total": 45500,
        "items": ["Indomie Goreng x2", "Teh Botol x1"],
        "category": "makanan",
        "confidence": 0.91,
    }
    out = validate_schema(raw)
    assert out["merchant"] == "Indomaret"
    assert out["date"] == "2026-04-23"
    assert out["total"] == 45500
    assert out["confidence"] == pytest.approx(0.91, abs=0.001)


def test_invalid_category_fallback():
    raw = {"merchant": "X", "category": "makan-makan", "confidence": 0.5}
    out = validate_schema(raw)
    assert out["category"] == "lainnya"


def test_invalid_date_becomes_none():
    raw = {"merchant": "X", "date": "23-04-2026", "confidence": 0.5}
    out = validate_schema(raw)
    assert out["date"] is None


def test_confidence_clamped():
    out = validate_schema({"confidence": 1.5})
    assert out["confidence"] <= 1.0

    out2 = validate_schema({"confidence": -0.5})
    assert out2["confidence"] >= 0.0
