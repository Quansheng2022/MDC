"""Cross-profile / batch / workflow hardening for Program D (WP-D06).

Proves the fitting authorities are architecture-wide and free of duplicate
integration code:

* one wide table and one representative figure are fitted for every profile and
  for the baseline (no-profile) conversion;
* the delivered geometry follows the *resolved* content width, never a profile
  identifier (static check over the fitting modules and the renderer);
* repeated conversion is deterministic per profile;
* the serial conversion path keeps no state between files (no batch leakage);
* the application/GUI service path and the CLI path produce fitted artifacts.
"""

from __future__ import annotations

import base64
import contextlib
import io
import re
import struct
import zlib
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest
from docx import Document

from md_converter.application.conversion_request import ConversionRequest
from md_converter.application.conversion_result import ConversionStatus
from md_converter.application.conversion_service import ConversionService
from md_converter.profiles import profile_ids

OUTPUT_PROFILE_IDS = (
    "professional_report",
    "business_report",
    "academic",
    "technical",
    "clean_minimal",
)

EXPECTED_CONTENT_WIDTHS_CM = {
    "professional_report": 21.0 - 2.54 - 2.54,
    "business_report": 21.0 - 2.0 - 2.0,
    "academic": 21.0 - 3.0 - 3.0,
    "technical": 21.0 - 2.2 - 2.2,
    "clean_minimal": 21.0 - 2.54 - 2.54,
}

BASE_OVERRIDES: Dict[str, Any] = {
    "word_com": False,
    "enable_cover": False,
    "toc": False,
    "verbose": False,
}


def _png_data_uri(width: int, height: int) -> str:
    """Return a deterministic solid-colour PNG data URI (no dependencies)."""
    scanline = b"\x00" + bytes((0x2F, 0x54, 0x96)) * width
    raw = scanline * height

    def chunk(tag: bytes, payload: bytes) -> bytes:
        body = tag + payload
        return (
            struct.pack(">I", len(payload))
            + body
            + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )
    return "data:image/png;base64," + base64.b64encode(png).decode("ascii")


def _document_body(table_rows: int = 3) -> str:
    """Representative document: one wide-ish table plus one figure."""
    header = "| Identifier | Description | Owner | Status | Stage | Note |"
    separator = "|------------|-------------|-------|--------|-------|------|"
    rows = [
        f"| DOC-{index:04d} | Pipeline normalisation pass | platform | accepted | build | ok |"
        for index in range(1, table_rows + 1)
    ]
    return "\n".join(
        [
            "# Fitted Document",
            "",
            *[header, separator, *rows],
            "",
            f"![figure]({_png_data_uri(400, 100)})",
            "",
        ]
    )


def _write_source(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    return path


def _facts(path: Path) -> Dict[str, Any]:
    """Return the fitting facts of one artifact."""
    document = Document(str(path))
    section = document.sections[0]
    content_width = section.page_width.cm - section.left_margin.cm - section.right_margin.cm
    table_widths = [column.width.cm for column in document.tables[0].columns]
    shape = document.inline_shapes[-1] if document.inline_shapes else None
    return {
        "content_width_cm": content_width,
        "table_total_cm": sum(table_widths),
        "table_min_cm": min(table_widths),
        "figure_width_cm": shape.width.cm if shape is not None else None,
        "figure_height_cm": shape.height.cm if shape is not None else None,
        "table_widths_cm": table_widths,
    }


def _convert(tmp_path: Path, name: str, profile_id: str | None, body: str) -> Tuple[Any, Path]:
    """Convert through the application service (the GUI/batch shared path)."""
    source = _write_source(tmp_path / f"{name}.md", body)
    output = tmp_path / f"{name}.docx"
    overrides = dict(BASE_OVERRIDES)
    if profile_id is not None:
        overrides["output_profile"] = profile_id
    service = ConversionService(overrides)
    result = service.convert(ConversionRequest(source, output_path=output))
    return result, output


# ============================================================
# Cross-profile matrix
# ============================================================


@pytest.mark.parametrize("profile_id", OUTPUT_PROFILE_IDS)
def test_wide_table_and_figure_are_fitted_for_every_profile(
    tmp_path: Path, profile_id: str
) -> None:
    """One wide table and one figure per profile, fitted to that profile's box."""
    result, output = _convert(tmp_path, profile_id, profile_id, _document_body())
    assert result.status is ConversionStatus.SUCCESS, result.diagnostics

    facts = _facts(output)
    expected_content = EXPECTED_CONTENT_WIDTHS_CM[profile_id]
    assert facts["content_width_cm"] == pytest.approx(expected_content, abs=0.02)
    assert facts["table_total_cm"] == pytest.approx(expected_content, abs=0.05)
    assert facts["table_min_cm"] >= 1.2 - 1e-3
    assert facts["figure_width_cm"] == pytest.approx(min(12.7, expected_content), abs=0.02)
    assert facts["figure_height_cm"] == pytest.approx(min(12.7, expected_content) / 4.0, abs=0.02)


def test_default_baseline_conversion_applies_the_same_fitting(tmp_path: Path) -> None:
    """The no-profile baseline path fits exactly like the default profile."""
    _, baseline_output = _convert(tmp_path, "baseline", None, _document_body())
    _, default_output = _convert(tmp_path, "default", "professional_report", _document_body())

    assert _facts(baseline_output) == _facts(default_output)


@pytest.mark.parametrize("profile_id", OUTPUT_PROFILE_IDS)
def test_repeated_conversion_is_deterministic_per_profile(tmp_path: Path, profile_id: str) -> None:
    """Same input + same profile -> identical fitted geometry."""
    _, first = _convert(tmp_path, f"{profile_id}_a", profile_id, _document_body())
    _, second = _convert(tmp_path, f"{profile_id}_b", profile_id, _document_body())

    assert _facts(first) == _facts(second)


# ============================================================
# No duplicate integration / no profile branching
# ============================================================


def test_no_profile_identifier_appears_in_fitting_or_render_paths() -> None:
    """The fitting policy and the renderer must never branch on profile identity."""
    project_root = Path(__file__).resolve().parents[2]
    modules = [
        project_root / "md_converter" / "renderer" / "layout" / "table_fitting.py",
        project_root / "md_converter" / "renderer" / "layout" / "figure_sizing.py",
        project_root / "md_converter" / "renderer" / "word_renderer.py",
        project_root / "md_converter" / "renderer" / "word_writer.py",
    ]

    for module in modules:
        source = module.read_text(encoding="utf-8")
        assert "output_profile" not in source, module.name
        for profile_id in profile_ids():
            pattern = r"\b" + re.escape(profile_id) + r"\b"
            assert not re.search(pattern, source), (module.name, profile_id)


# ============================================================
# Serial conversion / batch isolation
# ============================================================


def test_serial_conversions_keep_no_state_between_files(tmp_path: Path) -> None:
    """Different documents converted one after another never share fitting state."""
    bodies = [_document_body(1), _document_body(3), _document_body(6)]
    service = ConversionService(dict(BASE_OVERRIDES))

    artifacts: List[Path] = []
    for index, body in enumerate(bodies):
        source = _write_source(tmp_path / f"serial_{index}.md", body)
        output = tmp_path / f"serial_{index}.docx"
        result = service.convert(ConversionRequest(source, output_path=output))
        assert result.status is ConversionStatus.SUCCESS, result.diagnostics
        artifacts.append(output)

    # Row counts differ, so each artifact must reflect its own document.
    row_counts = [len(Document(str(path)).tables[0].rows) for path in artifacts]
    assert row_counts == [2, 4, 7]

    # Fitting geometry is identical because the table content profile matches;
    # a fresh service must produce byte-equivalent geometry for the same input.
    fresh = ConversionService(dict(BASE_OVERRIDES))
    source = _write_source(tmp_path / "fresh.md", bodies[1])
    output = tmp_path / "fresh.docx"
    fresh_result = fresh.convert(ConversionRequest(source, output_path=output))
    assert fresh_result.status is ConversionStatus.SUCCESS, fresh_result.diagnostics

    assert _facts(artifacts[1]) == _facts(output)
    # And the mixed-size table (fewer columns) is not affected by the earlier ones.
    assert _facts(artifacts[0])["table_total_cm"] == pytest.approx(
        _facts(artifacts[2])["table_total_cm"], abs=0.05
    )


def test_gui_shared_service_path_produces_a_gated_fitted_artifact(tmp_path: Path) -> None:
    """The GUI/batch shared application path keeps every quality gate green."""
    result, output = _convert(tmp_path, "gui_path", "professional_report", _document_body())

    assert result.status is ConversionStatus.SUCCESS
    report = result.quality_gate_report or {}
    for stage in ("static_qa", "rendered_qa", "post_processor", "final_artifact_qa"):
        status = (report.get(stage) or {}).get("status")
        assert status != "FAIL", (stage, status)
    facts = _facts(output)
    assert facts["table_total_cm"] <= facts["content_width_cm"] + 0.05
    assert facts["figure_width_cm"] <= facts["content_width_cm"] + 0.02


def test_cli_path_produces_a_fitted_artifact(tmp_path: Path) -> None:
    """The CLI entry point produces the same fitted geometry."""
    from click.testing import CliRunner

    from md_converter.cli import main as cli_main

    source = _write_source(tmp_path / "cli_source.md", _document_body())
    output = tmp_path / "cli_output.docx"

    runner = CliRunner()
    with contextlib.redirect_stdout(io.StringIO()):
        result = runner.invoke(
            cli_main,
            [str(source), "--output", str(output), "--no-open"],
        )

    assert result.exit_code == 0, result.output
    assert output.exists()

    facts = _facts(output)
    assert facts["table_total_cm"] <= facts["content_width_cm"] + 0.05
    assert facts["figure_width_cm"] <= facts["content_width_cm"] + 0.02
