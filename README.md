# PaddleOCRv5 Invoice Parser

Pipeline OCR receipt/invoice → JSON sesuai [AI-DS-SPEC](docs/AI-DS-SPEC-notes.md).

Menggunakan **PP-OCRv5** (server-grade detection + recognition) sebagai backbone OCR, diikuti **rule-based parser + lightweight category classifier** untuk menghasilkan output JSON:

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

## Struktur Repo

```
├── PP-OCRv5_server_det/     # Model weights (detection)
├── PP-OCRv5_server_rec/     # Model weights (recognition)
├── src/
│   ├── ocr_adapter.py       # Normalisasi output PaddleOCRv5
│   ├── line_builder.py      # Rekonstruksi line dari word-level bbox
│   ├── field_extractor.py   # Ekstraksi merchant/date/total/items
│   ├── field_resolver.py    # Ranking + resolusi kandidat
│   ├── category_mapper.py   # Rule + fallback category classifier
│   ├── confidence.py        # Perhitungan confidence score
│   ├── schema_validator.py  # Validasi output sesuai AI-DS-SPEC
│   └── pipeline.py          # Entry point end-to-end
├── tests/
│   ├── test_field_extractor.py
│   ├── test_line_builder.py
│   └── samples/             # Contoh gambar & expected JSON
├── notebooks/
│   └── pipeline_demo.ipynb
├── requirements.txt
└── README.md
```

## Quickstart

```bash
pip install -r requirements.txt
python -m src.pipeline --image path/to/struk.jpg
```

## Output Schema (AI-DS-SPEC)

| Field | Type | Keterangan |
|---|---|---|
| `merchant` | string | Nama merchant/toko |
| `date` | string (YYYY-MM-DD) | Tanggal transaksi |
| `total` | int | Total belanja (Rp) |
| `items` | list[str] | Daftar item belanja |
| `category` | string (enum) | Kategori transaksi |
| `confidence` | float (0–1) | Keyakinan model |

Valid values `category`: `makanan \| transport \| belanja \| hiburan \| kesehatan \| pendidikan \| tagihan \| pemasukan \| lainnya`
