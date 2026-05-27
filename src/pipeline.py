"""
pipeline.py

Entry point pipeline:
  Gambar → PaddleOCRv5 → normalize → build lines → extract fields
  → resolve → category → confidence → validate → JSON

Usage:
  python -m src.pipeline --image path/to/struk.jpg
  python -m src.pipeline --image path/to/struk.jpg --model_dir ./PP-OCRv5_server
"""

from __future__ import annotations
import argparse
import json
import os
from pathlib import Path

from paddleocr import PaddleOCR

from .ocr_adapter import adapt
from .line_builder import build_lines
from .field_extractor import (
    extract_merchant, extract_date, extract_total, extract_items
)
from .category_mapper import map_category
from .confidence import compute_confidence
from .schema_validator import validate_schema


def build_ocr_engine(
    det_model_dir: str = "./PP-OCRv5_server_det",
    rec_model_dir: str = "./PP-OCRv5_server_rec",
    use_gpu: bool = False,
) -> PaddleOCR:
    return PaddleOCR(
        use_angle_cls=True,
        lang="en",                  # gunakan "ch" jika ada mixed Chinese
        det_model_dir=det_model_dir,
        rec_model_dir=rec_model_dir,
        use_gpu=use_gpu,
        show_log=False,
    )


def parse_invoice(image_path: str, ocr_engine: PaddleOCR = None) -> dict:
    """
    Jalankan pipeline penuh, return dict sesuai AI-DS-SPEC.

    Args:
        image_path: path gambar struk/invoice (JPG/PNG)
        ocr_engine: instance PaddleOCR (buat jika None)

    Returns:
        dict dengan field: merchant, date, total, items, category, confidence
    """
    if ocr_engine is None:
        ocr_engine = build_ocr_engine()

    # 1. OCR
    ocr_raw = ocr_engine.ocr(image_path, cls=True)

    # 2. Normalize
    words = adapt(ocr_raw)
    if not words:
        return validate_schema({
            "merchant": "", "date": None, "total": None,
            "items": [], "category": "lainnya", "confidence": 0.0
        })

    # 3. Build lines
    lines = build_lines(words)

    # 4. Extract fields
    merchant, merchant_conf = extract_merchant(lines)
    date, date_conf = extract_date(lines)
    total, total_conf = extract_total(lines)
    items, items_conf = extract_items(lines)

    # 5. Category
    category, category_conf = map_category(merchant, items)

    # 6. Confidence
    overall_conf = compute_confidence(
        merchant_conf, date_conf, total_conf, items_conf, category_conf
    )

    # 7. Validate & return
    return validate_schema({
        "merchant": merchant,
        "date": date,
        "total": total,
        "items": items,
        "category": category,
        "confidence": overall_conf,
    })


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Parse struk/invoice → JSON")
    ap.add_argument("--image", required=True, help="Path ke gambar struk")
    ap.add_argument("--det_model_dir", default="./PP-OCRv5_server_det")
    ap.add_argument("--rec_model_dir", default="./PP-OCRv5_server_rec")
    ap.add_argument("--use_gpu", action="store_true")
    ap.add_argument("--pretty", action="store_true", help="Pretty print JSON")
    args = ap.parse_args()

    engine = build_ocr_engine(
        det_model_dir=args.det_model_dir,
        rec_model_dir=args.rec_model_dir,
        use_gpu=args.use_gpu,
    )
    result = parse_invoice(args.image, engine)
    indent = 2 if args.pretty else None
    print(json.dumps(result, ensure_ascii=False, indent=indent))
