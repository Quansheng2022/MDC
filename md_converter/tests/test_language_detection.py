"""Tests for CJK/Latin language detection and run segmentation."""

import pytest

from md_converter.renderer.layout.language_detection import (
    TextScript,
    detect_language,
    segment_text,
)


def test_cjk_dominant_justifies() -> None:
    """Chinese-dominant text uses justified alignment."""
    profile = detect_language("用户通过浏览器访问系统，点击登录按钮。")

    assert profile.cjk_ratio == pytest.approx(1.0)
    assert profile.dominant == "cjk"
    assert profile.alignment() == "justified"


def test_latin_dominant_left_aligns() -> None:
    """Latin-dominant text uses left alignment."""
    profile = detect_language("The user accesses the system through a browser and clicks login.")

    assert profile.dominant == "latin"
    assert profile.alignment() == "left"


def test_mixed_text_justifies() -> None:
    """Mixed CJK/Latin text justifies like Chinese."""
    profile = detect_language("支持 CSV 格式导出，并支持 JSON 格式导出。")

    assert profile.alignment() == "justified"


def test_url_heavy_left_aligns() -> None:
    """URL-heavy paragraphs stay left-aligned."""
    profile = detect_language("API 文档: https://example.com/api/v1/get?id=123")

    assert profile.url_heavy is True
    assert profile.alignment() == "left"


def test_atomic_sequences_kept_together() -> None:
    """Numbers, percentages, currencies and URLs remain single runs."""
    segments = segment_text("支持 35.6% 的增长率，$12.8B 融资，版本 1.2.3。")

    texts = [s.text for s in segments if s.atomic]

    assert "35.6%" in texts
    assert "$12.8B" in texts
    assert "1.2.3" in texts


def test_url_and_email_atomic() -> None:
    """URLs and emails are never split."""
    segments = segment_text("访问 https://example.com/api 或 mailto:dev@example.com")

    atomic_texts = [s.text for s in segments if s.atomic]
    assert "https://example.com/api" in atomic_texts
    assert "dev@example.com" in atomic_texts


def test_cjk_and_latin_segments_split() -> None:
    """CJK and Latin text split into separate runs."""
    segments = segment_text("Hello 世界 World")

    cjk_segments = [s for s in segments if s.script == TextScript.CJK]
    latin_segments = [s for s in segments if s.script == TextScript.LATIN]

    assert "".join(s.text for s in cjk_segments).strip() == "世界"
    assert "".join(s.text for s in latin_segments) == "HelloWorld"
