"""
Test unit untuk line_builder.py
"""
import pytest
from src.line_builder import build_lines


def make_word(text, x1, y1, x2, y2, conf=0.95):
    return {
        "text": text,
        "bbox": [x1, y1, x2, y2],
        "conf": conf,
        "cx": (x1 + x2) / 2,
        "cy": (y1 + y2) / 2,
    }


def test_single_line():
    words = [
        make_word("INDOMARET", 10, 10, 120, 30),
        make_word("CIBADUYUT", 130, 12, 240, 30),
    ]
    lines = build_lines(words)
    assert len(lines) == 1
    assert "INDOMARET" in lines[0]["text"]
    assert "CIBADUYUT" in lines[0]["text"]


def test_two_lines():
    words = [
        make_word("INDOMARET", 10, 10, 120, 30),
        make_word("TOTAL", 10, 80, 80, 100),
        make_word("45500", 90, 80, 150, 100),
    ]
    lines = build_lines(words)
    assert len(lines) == 2


def test_y_norm_range():
    words = [
        make_word("A", 10, 10, 50, 30),
        make_word("B", 10, 100, 50, 120),
    ]
    lines = build_lines(words)
    norms = [l["y_norm"] for l in lines]
    assert min(norms) == pytest.approx(0.0, abs=0.05)
    assert max(norms) == pytest.approx(1.0, abs=0.05)


def test_empty_words():
    assert build_lines([]) == []
