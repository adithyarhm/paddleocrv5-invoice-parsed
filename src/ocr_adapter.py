"""
ocr_adapter.py

Normalisasi output mentah PaddleOCRv5 ke format internal:
[
  {
    "text": str,
    "bbox": [x1, y1, x2, y2],   # bounding box (int pixels)
    "conf": float,              # confidence OCR 0-1
    "cx": float,                # center x
    "cy": float                 # center y
  },
  ...
]

PaddleOCR output format:
  result = [
    [
      [[[x1,y1],[x2,y2],[x3,y3],[x4,y4]], (text, conf)],
      ...
    ]
  ]
"""

from typing import Any


def adapt(ocr_raw: list[Any]) -> list[dict]:
    """
    Konversi output PaddleOCRv5 ke list of word dicts.
    Support format quad-point dan axis-aligned bbox.
    """
    words: list[dict] = []
    # Flatten nested list dari PaddleOCR
    lines_raw = ocr_raw[0] if (ocr_raw and isinstance(ocr_raw[0], list)) else ocr_raw

    for item in lines_raw:
        if item is None:
            continue
        try:
            bbox_pts, (text, conf) = item
        except (TypeError, ValueError):
            continue

        if not text or not text.strip():
            continue

        # Convert quad points → axis-aligned bbox
        xs = [p[0] for p in bbox_pts]
        ys = [p[1] for p in bbox_pts]
        x1, y1, x2, y2 = min(xs), min(ys), max(xs), max(ys)

        words.append({
            "text": text.strip(),
            "bbox": [int(x1), int(y1), int(x2), int(y2)],
            "conf": float(conf),
            "cx": (x1 + x2) / 2.0,
            "cy": (y1 + y2) / 2.0,
        })

    return words
