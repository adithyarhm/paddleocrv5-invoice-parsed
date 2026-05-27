"""
category_mapper.py

Mapping merchant/items ke category enum AI-DS-SPEC:
  makanan | transport | belanja | hiburan | kesehatan |
  pendidikan | tagihan | pemasukan | lainnya

Prioritas:
  1. Merchant exact match
  2. Merchant keyword match
  3. Items keyword match
  4. Fallback: lainnya
"""

from __future__ import annotations
import re


VALID_CATEGORIES = frozenset([
    "makanan", "transport", "belanja", "hiburan",
    "kesehatan", "pendidikan", "tagihan", "pemasukan", "lainnya"
])

# ─── Merchant keyword → category ───────────────────────────────────────────────
MERCHANT_MAP: list[tuple[str, str]] = [
    # Ritel / supermarket
    (r"indomaret|alfamart|alfamidi|lawson|circle\s*k|hero|carrefour|hypermart"
     r"|superindo|ranch\s*market|farmers\s*market|lotte\s*mart", "belanja"),
    # Restoran / makanan
    (r"kfc|mcdonald|burger\s*king|wendy|pizza\s*hut|domino|a&w"
     r"|kopi\s*kenangan|starbucks|janji\s*jiwa|fore|kenangan|flash\s*coffee"
     r"|warung|wartel|warteg|soto|bakso|mie|ayam|padang|nasi|cafe|coffee"
     r"|mixue|chatime|xiboba|gong\s*cha|sushi|ramen|takoyaki|kebab", "makanan"),
    # Transport
    (r"grab|gojek|gocar|goride|maxim|indriver|blue\s*bird|transjakarta"
     r"|pertalite|pertamax|spbu|shell|vivo\s*energy|total\s*energi", "transport"),
    # Kesehatan
    (r"apotek|apotik|kimia\s*farma|century\s*healthcare|guardian|watsons"
     r"|klinik|puskesmas|rs\b|rumah\s*sakit|laborat|lab\b", "kesehatan"),
    # Hiburan
    (r"cgv|cinema\s*xxi|bioskop|cinepolis|timezone|funworld|karaoke"
     r"|spotify|netflix|disney|vidio\b|indihome", "hiburan"),
    # Pendidikan
    (r"gramedia|togamas|toko\s*buku|univ|sekolah|kursus|bimbel", "pendidikan"),
    # Tagihan
    (r"pln|pdam|telkom|telkomsel|xl\b|indosat|tri\b|smartfren"
     r"|token\s*listrik|tagihan", "tagihan"),
]

# ─── Item keyword → category ───────────────────────────────────────────────────
ITEM_MAP: list[tuple[str, str]] = [
    (r"indomie|mie|nasi|ayam|bakso|soto|kopi|teh|air\s*mineral|aqua|susu"
     r"|roti|snack|keripik|biscuit|biscuit|coklat|kue|jajan", "makanan"),
    (r"bensin|pertalite|pertamax|solar|bbm|tol|tiket\s*(bus|kereta|pesawat)", "transport"),
    (r"obat|vitamin|suplemen|masker|alkohol|betadine|perban", "kesehatan"),
    (r"buku|alat\s*tulis|pulpen|pensil|penggaris", "pendidikan"),
    (r"pulsa|paket\s*data|token\s*listrik", "tagihan"),
    (r"baju|celana|sepatu|sandal|tas|dompet", "belanja"),
]


def map_category(merchant: str, items: list[str]) -> tuple[str, float]:
    """
    Return (category, confidence).
    """
    merchant_lower = merchant.lower()

    for pattern, cat in MERCHANT_MAP:
        if re.search(pattern, merchant_lower, re.IGNORECASE):
            return cat, 0.90

    items_text = " ".join(items).lower()
    for pattern, cat in ITEM_MAP:
        if re.search(pattern, items_text, re.IGNORECASE):
            return cat, 0.75

    # Heuristik tambahan: jika merchant atau items gabungan punya kata 'makan'
    combined = (merchant_lower + " " + items_text)
    if re.search(r"makan|minum|food|drink|cafe|resto", combined, re.IGNORECASE):
        return "makanan", 0.60

    return "lainnya", 0.40
