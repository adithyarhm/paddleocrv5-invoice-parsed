"""
confidence.py

Hitung confidence score akhir dari gabungan konfiden tiap field.
Weighted average dengan penalty untuk field yang tidak ditemukan.
"""


def compute_confidence(
    merchant_conf: float,
    date_conf: float,
    total_conf: float,
    items_conf: float,
    category_conf: float,
) -> float:
    """
    Weighted confidence:
      total      (paling krusial)  30%
      merchant                    25%
      date                        20%
      items                       15%
      category                    10%

    Penalty bila total atau merchant tidak ditemukan (conf < 0.3).
    """
    weights = {
        "total": 0.30,
        "merchant": 0.25,
        "date": 0.20,
        "items": 0.15,
        "category": 0.10,
    }
    values = {
        "total": total_conf,
        "merchant": merchant_conf,
        "date": date_conf,
        "items": items_conf,
        "category": category_conf,
    }

    raw = sum(weights[k] * values[k] for k in weights)

    # Penalty bila field kritis tidak ditemukan
    if total_conf < 0.3:
        raw *= 0.6
    if merchant_conf < 0.3:
        raw *= 0.85

    return round(max(0.0, min(1.0, raw)), 4)
