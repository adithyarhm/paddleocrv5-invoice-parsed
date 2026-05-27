"""
Test unit untuk category_mapper.py
"""
import pytest
from src.category_mapper import map_category


def test_indomaret_belanja():
    cat, conf = map_category("Indomaret", [])
    assert cat == "belanja"


def test_kopi_kenangan_makanan():
    cat, conf = map_category("Kopi Kenangan", [])
    assert cat == "makanan"


def test_grab_transport():
    cat, conf = map_category("GrabCar", [])
    assert cat == "transport"


def test_apotek_kesehatan():
    cat, conf = map_category("Apotek Kimia Farma", [])
    assert cat == "kesehatan"


def test_items_fallback_makanan():
    cat, conf = map_category("Toko Serba Ada", ["indomie goreng x2", "teh botol x1"])
    assert cat == "makanan"


def test_unknown_merchant_lainnya():
    cat, conf = map_category("Bengkel Pak Budi", ["oli mesin", "busi"])
    assert cat == "lainnya"
