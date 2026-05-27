# AI-DS-SPEC — Catatan Implementasi OCR Struk

## Output Schema (Fitur 2: OCR Struk/Invoice)

```json
{
  "merchant": "Indomaret",
  "date": "2026-04-23",
  "total": 45500,
  "items": ["Indomie Goreng x2", "Teh Botol x1"],
  "category": "makanan",
  "confidence": 0.91
}
```

## Valid Category Values

```
makanan | transport | belanja | hiburan | kesehatan | pendidikan | tagihan | pemasukan | lainnya
```

## Confidence

Skala `0.0 – 1.0`. Dihitung dari weighted average confidence tiap field:

| Field | Weight |
|---|---|
| total | 30% |
| merchant | 25% |
| date | 20% |
| items | 15% |
| category | 10% |

Field yang tidak ditemukan mendapat `conf < 0.3` dan memicu penalty terhadap score final.

## Keputusan Arsitektur

- **Rule-based** untuk `date`, `total`: deterministic, mudah di-debug, tidak butuh data training.
- **Heuristik + keyword scoring** untuk `merchant` dan `items`.
- **Lookup dict + regex** untuk `category`: karena enum valid sangat terbatas.
- **Pydantic v2** untuk schema enforcement: mencegah output malformed sampai ke downstream.
- Model NLP dipertimbangkan hanya untuk edge case line labeling bila akurasi < 70% pada field tertentu.
