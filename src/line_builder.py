"""
line_builder.py

Menggabungkan word-level bbox hasil OCR menjadi "lines" berdasarkan
proximitas vertikal (cy), lalu sort tiap line secara horizontal.

Output per line:
{
  "text": str,           # gabungan teks kata-kata
  "words": [...],        # list word dicts asli
  "bbox": [x1,y1,x2,y2], # bbox merged
  "cy": float,           # rata-rata center y
  "avg_conf": float,     # rata-rata confidence
  "y_norm": float        # posisi vertikal dinormalisasi 0-1 (0=atas, 1=bawah)
}
"""

from __future__ import annotations
from typing import Any


def build_lines(words: list[dict], y_tolerance_factor: float = 0.6) -> list[dict]:
    """
    Cluster kata menjadi baris berdasarkan jarak cy.
    y_tolerance_factor: perkalian median height kata sebagai threshold.
    """
    if not words:
        return []

    # Estimasi tinggi rata-rata karakter
    heights = [(w["bbox"][3] - w["bbox"][1]) for w in words]
    median_h = _median(heights)
    threshold = median_h * y_tolerance_factor

    # Sort by cy, kemudian cx
    sorted_words = sorted(words, key=lambda w: (w["cy"], w["cx"]))

    clusters: list[list[dict]] = []
    current: list[dict] = [sorted_words[0]]

    for word in sorted_words[1:]:
        if abs(word["cy"] - current[-1]["cy"]) <= threshold:
            current.append(word)
        else:
            clusters.append(sorted(current, key=lambda w: w["cx"]))
            current = [word]
    clusters.append(sorted(current, key=lambda w: w["cx"]))

    # Cari total height untuk normalisasi y
    all_cys = [w["cy"] for w in words]
    cy_min, cy_max = min(all_cys), max(all_cys)
    cy_range = cy_max - cy_min if cy_max != cy_min else 1.0

    lines: list[dict] = []
    for cluster in clusters:
        text = " ".join(w["text"] for w in cluster)
        xs = [w["bbox"][0] for w in cluster] + [w["bbox"][2] for w in cluster]
        ys = [w["bbox"][1] for w in cluster] + [w["bbox"][3] for w in cluster]
        cy_avg = sum(w["cy"] for w in cluster) / len(cluster)
        avg_conf = sum(w["conf"] for w in cluster) / len(cluster)

        lines.append({
            "text": text,
            "words": cluster,
            "bbox": [min(xs), min(ys), max(xs), max(ys)],
            "cy": cy_avg,
            "avg_conf": avg_conf,
            "y_norm": (cy_avg - cy_min) / cy_range,
        })

    return lines


def _median(values: list[float]) -> float:
    s = sorted(values)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0
