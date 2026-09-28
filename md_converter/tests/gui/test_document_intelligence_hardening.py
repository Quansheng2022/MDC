"""Failure, robustness and accessibility hardening (WP-DI-06).

Covered failure cases:

* missing source, unreadable source;
* a result with no diagnostics at all;
* malformed / unexpected diagnostic presentation input;
* a missing output artifact;
* a report produced after a failure.

Covered guardrails: warnings never look fatal, no raw traceback leads the UX,
findings are presented once per group, and the document-quality surface stays
inside the standard layout.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import TYPE_CHECKING, Callable

import pytest

from md_converter.application.conversion_request import ConversionRequest
from md_converter.application.conversion_result import (
    ConversionErrorCategory,
    ConversionResult,
    ConversionStatus,
)
from md_converter.application.conversion_service import ConversionService
from md_converter.application.diagnostics_adapter import (
    ApplicationDiagnostic,
    DiagnosticSummary,
)
from md_converter.gui.preflight_model import (
    PREFLIGHT_CLEAN_TEXT,
    preflight_from_diagnostics,
    preflight_from_result,
)
from md_converter.gui.presentation_model import present_result

if TYPE_CHECKING:  # pragma: no cover - typing only
    from md_converter.gui.main_window import MainWindow

pytest.importorskip("PySide6", reason="PySide6 (GUI dev dependency) is not installed")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402 - the Qt guard must run first

from md_converter.gui.result_details import build_report_text  # noqa: E402 - guard first
from md_converter.gui.state import GuiState  # noqa: E402 - the Qt guard must run first

WARNING_BODY = "#\n\nSome body text.\n"
SUCCESS_BODY = "# Notes\n\nBody text.\n"
FAILURE_BODY = ""


def _pump() -> None:
    """Deliver pending Qt events (queued cross-thread signals)."""
    QApplication.processEvents()


def _wait_until(predicate: Callable[[], bool], timeout_ms: int = 30000) -> bool:
    """Process GUI events until ``predicate`` holds, or the timeout expires."""
    deadline = time.monotonic() + timeout_ms / 1000.0
    while time.monotonic() < deadline:
        _pump()
        if predicate():
            return True
        time.sleep(0.005)
    return predicate()


def _write_markdown(path: Path, body: str = SUCCESS_BODY) -> Path:
    """Write ``body`` as UTF-8 Markdown and return the path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _record(severity: str, code: str, wording: str) -> ApplicationDiagnostic:
    """Return one adapted diagnostic record."""
    return ApplicationDiagnostic(
        severity=severity,
        code=code,
        message=f"{code} technical message",
        user_message=wording,
    )


def _report(result: ConversionResult) -> str:
    """Return the strengthened report text for ``result``."""
    return build_report_text(present_result(result), result)


@pytest.fixture
def window(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> "MainWindow":
    """Provide a window with a deterministic service, idle again at teardown."""
    from md_converter.gui.app import create_application
    from md_converter.gui.main_window import MainWindow

    monkeypatch.chdir(tmp_path)
    create_application([])

    instance = MainWindow()
    instance.service = ConversionService({"word_com": False})
    yield instance

    assert _wait_until(lambda: not instance.worker.is_running), "worker did not stop"
    instance.close()
    _pump()


# ============================================================
# Failure cases
# ============================================================


def test_missing_source_produces_a_bounded_failure_report(tmp_path: Path) -> None:
    """A missing source fails closed with a readable, traceback-free report."""
    service = ConversionService({"word_com": False})
    result = service.convert(ConversionRequest(tmp_path / "does_not_exist.md"))

    assert result.status is ConversionStatus.FAILED
    assert result.error_category is ConversionErrorCategory.INPUT_ERROR
    assert result.is_failed is True

    text = _report(result)
    assert "Status: FAILED" in text
    assert "Traceback" not in text
    assert preflight_from_result(result).is_clean is True


def test_unreadable_source_produces_a_bounded_failure_report(tmp_path: Path) -> None:
    """A source that cannot be decoded fails closed without a traceback."""
    broken = tmp_path / "broken.md"
    broken.write_bytes(b"\xff\xfe\x00 not utf-8")
    service = ConversionService({"word_com": False})

    result = service.convert(ConversionRequest(broken))

    assert result.status is ConversionStatus.FAILED
    assert result.error_category is ConversionErrorCategory.INPUT_ERROR
    text = _report(result)
    assert "Status: FAILED" in text
    # The retained technical evidence stays secondary: the status block leads,
    # and any traceback is rendered last, under "Technical detail".
    assert "Traceback" not in text.split("\n\n")[1]
    if "Traceback" in text:
        assert text.index("Status: FAILED") < text.index("Technical detail")
        assert text.index("Technical detail") < text.index("Traceback")


def test_directory_source_is_rejected_at_the_gui_boundary(
    window: "MainWindow", tmp_path: Path
) -> None:
    """A non-file source is refused at the GUI boundary and reports nothing."""
    directory = tmp_path / "folder.md"
    directory.mkdir()

    assert window.set_source_file(str(directory)) is GuiState.EMPTY
    assert window.preflight_area.isVisible() is False
    assert window.latest_result is None


def test_result_without_diagnostics_is_clean() -> None:
    """No diagnostics means no findings, no panel content and no review text."""
    result = ConversionResult(status=ConversionStatus.SUCCESS, output_path=Path("out.docx"))

    summary = preflight_from_result(result)
    text = _report(result)

    assert summary.is_clean is True
    assert summary.summary_text() == PREFLIGHT_CLEAN_TEXT
    assert "Quality findings" not in text
    assert "Suggested review" not in text


def test_malformed_diagnostic_input_is_tolerated() -> None:
    """Unexpected presentation input never breaks the model or the report."""
    warning = _record("WARNING", "QA_STATIC_WARN", "A heading was adjusted.")
    result = ConversionResult(
        status=ConversionStatus.SUCCESS_WITH_WARNING,
        output_path=Path("out.docx"),
        warnings=(warning,),
        diagnostics=(warning, None, {"severity": "WARNING"}, object()),  # type: ignore[arg-type]
        diagnostic_summary=DiagnosticSummary.from_records((warning,)),
    )

    summary = preflight_from_result(result)
    text = _report(result)

    assert summary.total == 3
    assert summary.warning_count == 2
    assert summary.info_count == 1
    assert "Quality findings (3)" in text
    assert "A heading was adjusted." in text


def test_malformed_input_in_isolation_is_tolerated() -> None:
    """Every malformed shape degrades to an informational item, never a crash."""
    summary = preflight_from_diagnostics(
        [None, object(), "text", 42, {"severity": None, "code": None}]  # type: ignore[list-item]
    )

    assert summary.total == 4
    assert summary.error_count == 0
    assert summary.warning_count == 0
    assert summary.info_count == 4
    assert len(summary.rows()) == 4


def test_missing_artifact_is_reported_and_not_actionable(
    window: "MainWindow", tmp_path: Path
) -> None:
    """A missing artifact is reported; no output action is offered for it."""
    missing = tmp_path / "gone.docx"

    def fake_convert(request: ConversionRequest) -> ConversionResult:
        return ConversionResult(
            status=ConversionStatus.SUCCESS,
            source_path=Path(str(request.source_path)),
            output_path=missing,
        )

    window.service.convert = fake_convert  # type: ignore[method-assign]
    assert window.set_source_file(str(_write_markdown(tmp_path / "notes.md"))) is GuiState.READY
    window.start_conversion()
    assert _wait_until(
        lambda: window.state is not GuiState.CONVERTING and not window.worker.is_running
    )
    window.show()
    _pump()

    assert window.state is GuiState.SUCCESS
    assert window.latest_result is not None
    assert window.latest_result.output_path == missing
    assert window.open_document_button.isVisible() is False
    assert window.open_folder_button.isVisible() is False
    assert f"Output path: {missing}" in _report(window.latest_result)


def test_each_finding_is_listed_once_per_group() -> None:
    """No duplicate flood: a finding appears once inside a presentation group."""
    records = (
        _record("WARNING", "QA_STATIC_WARN", "A heading was adjusted."),
        _record("WARNING", "QA_RENDERED_WARN", "A table was fitted."),
        _record("INFO", "NORM001", "Text nodes were merged."),
    )
    result = ConversionResult(
        status=ConversionStatus.SUCCESS_WITH_WARNING,
        output_path=Path("out.docx"),
        warnings=records[:2],
        diagnostics=records,
        diagnostic_summary=DiagnosticSummary.from_records(records),
    )

    summary = preflight_from_result(result)
    section = _report(result).split("Quality findings (3)", 1)[1].split("Warnings (", 1)[0]

    assert len(summary.rows()) == 3
    for row in summary.rows():
        assert section.count(row) == 1


# ============================================================
# Accessibility / layout hardening
# ============================================================


def test_document_quality_surface_stays_in_the_standard_layout(
    window: "MainWindow", tmp_path: Path
) -> None:
    """The surface is laid out by the shared layout, never by absolute geometry."""
    _convert(window, _write_markdown(tmp_path / "warned.md", WARNING_BODY))
    window.show()
    _pump()

    central = window.centralWidget()
    assert window.preflight_area.parent() is central
    assert window.preflight_area.geometry().width() > 0
    assert central.rect().contains(window.preflight_area.geometry())
    assert window.preflight_list.count() >= 1


def test_long_finding_text_is_not_truncated_in_the_row() -> None:
    """Long wording is preserved verbatim; the view wraps/elides, not the model."""
    long_text = "A very wide table was fitted to the available page width. " * 6
    summary = preflight_from_diagnostics([_record("WARNING", "TABLE001", long_text.strip())])

    assert long_text.strip() in summary.rows()[0]


def _convert(window: "MainWindow", source: Path) -> None:
    """Run one real conversion through the window and wait for completion."""
    assert window.set_source_file(str(source)) is GuiState.READY
    window.start_conversion()
    assert _wait_until(
        lambda: window.state is not GuiState.CONVERTING and not window.worker.is_running
    )
