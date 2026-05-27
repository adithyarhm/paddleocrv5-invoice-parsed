"""
Test unit untuk field_extractor.py
"""
import pytest
from src.line_builder import build_lines
from src.field_extractor import (
    extract_merchant, extract_date, extract_total, extract_items
)


def make_line(text, y_norm, conf=0.92):
    """Buat line dict minimal untuk testing."""
    return {
        "text": text,
        "words": [],
        "bbox": [0, 0, 100, 20],
        "cy": y_norm * 1000,
        "avg_conf": conf,
        "y_norm": y_norm,
    }


# ─── Merchant ──────────────────────────────────────────────────────────────────

def test_merchant_basic():
    lines = [
        make_line("INDOMARET CIBADUYUT", 0.02),
        make_line("JL. CIBADUYUT NO. 5", 0.06),
        make_line("23/04/2026 10:30", 0.10),
    ]
    merchant, conf = extract_merchant(lines)
    assert "Indomaret" in merchant
    assert conf > 0.5


def test_merchant_skip_date_line():
    lines = [
        make_line("23/04/2026", 0.03),
        make_line("KOPI KENANGAN", 0.07),
    ]
    merchant, conf = extract_merchant(lines)
    assert "Kopi Kenangan" in merchant


# ─── Date ──────────────────────────────────────────────────────────────────────

def test_date_slash_format():
    lines = [make_line("Tgl: 23/04/2026", 0.10)]
    date, conf = extract_date(lines)
    assert date == "2026-04-23"
    assert conf > 0.5


def test_date_dash_format():
    lines = [make_line("2026-04-23 10:30", 0.10)]
    date, conf = extract_date(lines)
    assert date == "2026-04-23"


def test_date_not_found():
    lines = [make_line("TOTAL 45500", 0.80)]
    date, conf = extract_date(lines)
    assert date is None
    assert conf < 0.5


# ─── Total ─────────────────────────────────────────────────────────────────────

def test_total_found():
    lines = [
        make_line("INDOMIE GORENG x2 14.000", 0.60),
        make_line("TEH BOTOL x1 5.500", 0.65),
        make_line("TOTAL 45.500", 0.85),
    ]
    total, conf = extract_total(lines)
    assert total == 45500
    assert conf > 0.5


def test_total_not_kembalian():
    lines = [
        make_line("TOTAL 45.500", 0.85),
        make_line("KEMBALIAN 4.500", 0.90),
    ]
    total, conf = extract_total(lines)
    assert total == 45500


# ─── Items ─────────────────────────────────────────────────────────────────────

def test_items_basic():
    lines = [
        make_line("INDOMARET", 0.02),
        make_line("NAMA BARANG   QTY   HARGA", 0.20),  # header table
        make_line("INDOMIE GORENG x2   14.000", 0.45),
        make_line("TEH BOTOL x1        5.500", 0.55),
        make_line("TOTAL 45.500", 0.85),
    ]
    items, conf = extract_items(lines)
    assert len(items) >= 1
    assert any("INDOMIE" in i for i in items)
