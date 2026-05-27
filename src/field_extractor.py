"""
field_extractor.py

Ekstraksi kandidat field dari normalized lines:
- merchant: heuristik header receipt
- date: regex multi-format → normalize ke YYYY-MM-DD
- total: keyword scoring + kandidat ranked
- items: filter body receipt
"""

from __future__ import annotations
import re
from dateutil import parser as date_parser
from typing import Optional


# ─── MERCHANT ──────────────────────────────────────────────────────────────────

MERCHANT_SKIP_PATTERNS = [
    r"\d{2}[/\-]\d{2}[/\-]\d{2,4}",   # tanggal
    r"\d{2}:\d{2}",                     # jam
    r"npwp",
    r"\bno\b",
    r"telp|phone|hp|fax",
    r"alamat|address|jl\.|jalan",
    r"kasir|cashier|operator",
    r"struk|invoice|receipt|kwitansi",
    r"\bwifi\b|password",
    r"terima kasih|thank you",
]


def extract_merchant(lines: list[dict]) -> tuple[str, float]:
    """
    Cari merchant dari baris-baris header (y_norm < 0.25).
    Return (merchant_text, confidence).
    """
    candidates = [l for l in lines if l["y_norm"] < 0.25]
    if not candidates:
        candidates = lines[:3]

    scored: list[tuple[float, dict]] = []
    for line in candidates:
        t = line["text"]
        skip = any(re.search(p, t, re.IGNORECASE) for p in MERCHANT_SKIP_PATTERNS)
        if skip:
            continue

        # Lebih tinggi skor kalau dominan huruf kapital dan cukup panjang
        alpha = [c for c in t if c.isalpha()]
        if not alpha:
            continue
        cap_ratio = sum(1 for c in alpha if c.isupper()) / len(alpha)
        length_bonus = min(len(t) / 30.0, 1.0)
        # Bonus kalau ada di y_norm sangat atas
        top_bonus = max(0, 0.3 - line["y_norm"])
        score = cap_ratio * 0.5 + length_bonus * 0.3 + top_bonus * 0.2
        scored.append((score, line))

    if not scored:
        return "", 0.3

    scored.sort(key=lambda x: -x[0])
    best_score, best_line = scored[0]
    conf = min(0.95, 0.5 + best_score * 0.5)
    return best_line["text"].title(), conf


# ─── DATE ──────────────────────────────────────────────────────────────────────

DATE_PATTERNS = [
    r"(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})",    # YYYY-MM-DD
    r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})",    # DD/MM/YYYY
    r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{2})",    # DD/MM/YY
    r"(\d{1,2})\s+(Jan|Feb|Mar|Apr|Mei|Jun|Jul|Agu|Sep|Okt|Nov|Des|Me|Ag)\s+(\d{2,4})",
    r"(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{2,4})",
]

MONTH_ID_TO_EN = {
    "jan": "jan", "feb": "feb", "mar": "mar",
    "apr": "apr", "mei": "may", "me": "may",
    "jun": "jun", "jul": "jul",
    "agu": "aug", "ag": "aug",
    "sep": "sep", "okt": "oct",
    "nov": "nov", "des": "dec",
}


def extract_date(lines: list[dict]) -> tuple[Optional[str], float]:
    """
    Cari tanggal dari seluruh lines.
    Return (date_string YYYY-MM-DD atau None, confidence).
    """
    for line in lines:
        raw = line["text"]
        for pat in DATE_PATTERNS:
            m = re.search(pat, raw, re.IGNORECASE)
            if m:
                try:
                    raw_date = _normalize_id_month(m.group(0))
                    parsed = date_parser.parse(raw_date, dayfirst=True)
                    return parsed.strftime("%Y-%m-%d"), min(0.95, line["avg_conf"] + 0.1)
                except (ValueError, OverflowError):
                    continue
    return None, 0.2


def _normalize_id_month(text: str) -> str:
    for id_m, en_m in MONTH_ID_TO_EN.items():
        text = re.sub(id_m, en_m, text, flags=re.IGNORECASE)
    return text


# ─── TOTAL ─────────────────────────────────────────────────────────────────────

TOTAL_KEYWORDS_HIGH = [
    r"grand\s*total", r"total\s*belanja", r"total\s*harga",
    r"jumlah\s*bayar", r"amount\s*due", r"amount\s*payable",
]
TOTAL_KEYWORDS_MED = [
    r"\btotal\b", r"\bjumlah\b", r"\bsubtotal\b",
]
TOTAL_KEYWORDS_NEG = [
    r"kembalian", r"\bcash\b", r"\bdebit\b", r"\bkredit\b",
    r"diskon", r"discount", r"\bppn\b", r"\btax\b",
    r"service\s*charge", r"voucher", r"\btunai\b",
    r"rounding", r"nominal",
]

AMOUNT_RE = re.compile(r"[\d.,]{3,}")


def extract_total(lines: list[dict]) -> tuple[Optional[int], float]:
    """
    Cari total dari candidates berdasarkan keyword scoring.
    Return (total_int atau None, confidence).
    """
    candidates: list[tuple[float, int]] = []

    for line in lines:
        t = line["text"]
        amounts = [_parse_amount(a) for a in AMOUNT_RE.findall(t) if _parse_amount(a) > 100]
        if not amounts:
            continue

        score = 0.0
        if any(re.search(p, t, re.IGNORECASE) for p in TOTAL_KEYWORDS_HIGH):
            score += 10
        elif any(re.search(p, t, re.IGNORECASE) for p in TOTAL_KEYWORDS_MED):
            score += 7

        if any(re.search(p, t, re.IGNORECASE) for p in TOTAL_KEYWORDS_NEG):
            score -= 5

        # Bonus posisi bawah
        score += line["y_norm"] * 3
        # Penalty jika ada di baris paling atas
        if line["y_norm"] < 0.1:
            score -= 3

        if score > 2:
            best_amount = max(amounts)
            candidates.append((score, best_amount))

    if not candidates:
        return None, 0.1

    candidates.sort(key=lambda x: -x[0])
    best_score, best_amount = candidates[0]
    conf = min(0.95, 0.4 + (best_score / 15.0) * 0.5)
    return best_amount, conf


def _parse_amount(s: str) -> int:
    """Konversi '45.500' atau '45,500' ke int."""
    s = s.replace(".", "").replace(",", "")
    try:
        return int(s)
    except ValueError:
        return 0


# ─── ITEMS ─────────────────────────────────────────────────────────────────────

FOOTER_KEYWORDS = [
    r"\btotal\b", r"\bjumlah\b", r"kembalian", r"\bcash\b",
    r"\bdebit\b", r"\bkredit\b", r"bayar", r"kasir",
    r"terima kasih", r"thank you", r"npwp", r"\bppn\b",
    r"service charge", r"voucher", r"\bpoin\b",
]
HEADER_BOUNDARY_RE = re.compile(
    r"(item|nama|produk|keterangan|qty|pcs|satuan|harga)",
    re.IGNORECASE
)


def extract_items(lines: list[dict]) -> tuple[list[str], float]:
    """
    Ekstrak baris item dari body receipt.
    Return (list[str] items, confidence).
    """
    # Deteksi batas header
    header_end_idx = 0
    for i, line in enumerate(lines):
        if HEADER_BOUNDARY_RE.search(line["text"]):
            header_end_idx = i + 1
            break
    if header_end_idx == 0:
        # Gunakan heuristik: lewati ~20% atas
        header_end_idx = max(1, int(len(lines) * 0.2))

    # Deteksi footer start
    footer_start_idx = len(lines)
    for i in range(len(lines) - 1, header_end_idx - 1, -1):
        if any(re.search(p, lines[i]["text"], re.IGNORECASE) for p in FOOTER_KEYWORDS[:6]):
            footer_start_idx = i
            break

    body_lines = lines[header_end_idx:footer_start_idx]

    items: list[str] = []
    for line in body_lines:
        t = line["text"].strip()
        if len(t) < 3:
            continue
        if any(re.search(p, t, re.IGNORECASE) for p in FOOTER_KEYWORDS):
            continue
        items.append(t)

    conf = 0.7 if len(items) > 0 else 0.2
    return items, conf
