"""
pipeline.py

Entry point pipeline:
  Gambar → PaddleOCRv5 → normalize → build lines → extract fields
  → resolve → category → confidence → validate → JSON

Usage:
  python -m src.pipeline --image path/to/struk.jpg
  python -m src.pipeline --image path/to/struk.jpg \\
      --det_model_dir ./PP-OCRv5_server_det \\
      --rec_model_dir ./PP-OCRv5_server_rec \\
      --device gpu

Valid PaddleOCR v3.x __init__ common args:
  device, engine, enable_hpi, use_tensorrt, precision,
  enable_mkldnn, mkldnn_cache_capacity, cpu_threads, enable_cinn

NOTE: show_log, use_gpu, use_angle_cls tidak lagi didukung di v3.x.
"""

from __future__ import annotations
import argparse
import json

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
    device: str = "cpu",
) -> PaddleOCR:
    """
    Buat instance PaddleOCR kompatibel dengan v3.x (PaddleOCR >= 3.0).

    Parameter yang VALID di v3.x:
      text_detection_model_dir   : path model deteksi
      text_recognition_model_dir : path model rekognisi
      use_textline_orientation   : ganti use_angle_cls
      ocr_version                : 'PP-OCRv5' | 'PP-OCRv4' | 'PP-OCRv3'
      device                     : 'cpu' | 'gpu' | 'gpu:0'
      lang                       : 'en' | 'ch' | dll

    Parameter yang sudah DIHAPUS di v3.x:
      show_log, use_gpu, use_angle_cls, det_model_dir, rec_model_dir
    """
    return PaddleOCR(
        text_detection_model_dir=det_model_dir,
        text_recognition_model_dir=rec_model_dir,
        use_textline_orientation=True,
        ocr_version="PP-OCRv5",
        lang="en",
        device=device,
    )


def parse_invoice(image_path: str, ocr_engine: PaddleOCR = None) -> dict:
    """
    Jalankan pipeline penuh, return dict sesuai AI-DS-SPEC.

    Args:
        image_path: path gambar struk/invoice (JPG/PNG)
        ocr_engine: instance PaddleOCR (buat baru jika None)

    Returns:
        dict: merchant, date, total, items, category, confidence
    """
    if ocr_engine is None:
        ocr_engine = build_ocr_engine()

    # 1. OCR — v3.x tidak butuh cls=True
    ocr_raw = ocr_engine.ocr(image_path)

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
    date, date_conf         = extract_date(lines)
    total, total_conf       = extract_total(lines)
    items, items_conf       = extract_items(lines)

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
    ap = argparse.ArgumentParser(description="Parse struk/invoice → JSON (AI-DS-SPEC)")
    ap.add_argument("--image", required=True, help="Path ke gambar struk (JPG/PNG)")
    ap.add_argument("--det_model_dir", default="./PP-OCRv5_server_det",
                    help="Dir model deteksi")
    ap.add_argument("--rec_model_dir", default="./PP-OCRv5_server_rec",
                    help="Dir model rekognisi")
    ap.add_argument("--device", default="cpu",
                    help="Device inferensi: cpu | gpu | gpu:0")
    ap.add_argument("--pretty", action="store_true", help="Pretty print JSON output")
    args = ap.parse_args()

    engine = build_ocr_engine(
        det_model_dir=args.det_model_dir,
        rec_model_dir=args.rec_model_dir,
        device=args.device,
    )
    result = parse_invoice(args.image, engine)
    indent = 2 if args.pretty else None
    print(json.dumps(result, ensure_ascii=False, indent=indent))
