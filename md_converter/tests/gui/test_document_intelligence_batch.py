"""Focused verification for Document Intelligence batch compatibility (WP-DI-05).

The strengthened report and the preflight presentation must stay compatible
with serial batch conversion:

* every file keeps its own findings (no cross-file contamination);
* the aggregate batch report stays summary-only (no batch-only diagnostics);
* the per-file ``Details...`` surface remains the single owner of a file's
  quality findings.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Dict, List, Tuple

import pytest

from md_converter.application.conversion_result import ConversionResult, ConversionStatus
from md_converter.application.diagnostics_adapter import (
    ApplicationDiagnostic,
    DiagnosticSummary,
)
from md_converter.gui.batch import BatchItemStatus, BatchRun

if TYPE_CHECKING:  # pragma: no cover - typing only
    from md_converter.gui.main_window import MainWindow

pytest.importorskip("PySide6", reason="PySide6 (GUI dev dependency) is not installed")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from md_converter.gui.state import GuiState  # noqa: E402 - the Qt guard must run first

SUCCESS_BODY = "# Notes\n\nBody text.\n"
WARNING_BODY = "#\n\nSome body text.\n"
FAILURE_BODY = ""


def _pump() -> None:
    """Deliver pending Qt events (queued cross-thread signals)."""
    from PySide6.QtWidgets import QApplication

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


@pytest.fixture
def window(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> "MainWindow":
    """Provide a window with a deterministic service, idle again at teardown."""
    from md_converter.application.conversion_service import ConversionService
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


def _run_batch(window: "MainWindow", tmp_path: Path, bodies: Dict[str, str]) -> BatchRun:
    """Select ``bodies`` as a batch, convert it, and return the finished run."""
    sources = [_write_markdown(tmp_path / name, body) for name, body in bodies.items()]
    output_dir = tmp_path / "out"
    output_dir.mkdir(exist_ok=True)
    window.set_output_directory(output_dir)
    window.set_source_file(str(sources[0]))
    window.add_source_files([str(source) for source in sources[1:]])
    assert window.start_conversion() is GuiState.CONVERTING
    assert _wait_until(
        lambda: not window.worker.is_running
        and window.state is not GuiState.CONVERTING
        and window.batch_run is not None
        and not window.batch_run.is_running
    )
    run = window.batch_run
    assert run is not None
    return run


def _items_by_name(run: BatchRun) -> Dict[str, object]:
    """Return the retained batch items keyed by source file name."""
    return {item.source_path.name: item for item in run.items}


def _record(severity: str, code: str, wording: str) -> ApplicationDiagnostic:
    """Return one adapted diagnostic record."""
    return ApplicationDiagnostic(
        severity=severity,
        code=code,
        message=f"{code} technical message",
        user_message=wording,
    )


# ============================================================
# Aggregate report stays summary-only
# ============================================================


def test_aggregate_batch_report_carries_no_findings() -> None:
    """The batch report stays an aggregate: no per-file findings are folded in."""
    warning = _record("WARNING", "QA_STATIC_WARN", "A heading was adjusted.")
    warned = ConversionResult(
        status=ConversionStatus.SUCCESS_WITH_WARNING,
        source_path=Path("a.md"),
        output_path=Path("out") / "a.docx",
        warnings=(warning,),
        diagnostics=(warning,),
        diagnostic_summary=DiagnosticSummary.from_records((warning,)),
    )
    clean = ConversionResult(
        status=ConversionStatus.SUCCESS,
        source_path=Path("b.md"),
        output_path=Path("out") / "b.docx",
    )

    run = BatchRun((warned.source_path, clean.source_path))
    run.begin()
    run.record_result(warned)
    run.next_source()
    run.record_result(clean)

    text = run.report_text()

    assert "[SUCCESS_WITH_WARNING] a.md" in text
    assert "[SUCCESS] b.md" in text
    assert "Quality findings" not in text
    assert "QA_STATIC_WARN" not in text
    assert "Suggested review" not in text


def test_batch_summary_counts_stay_derived_from_the_items() -> None:
    """The aggregate counts keep matching the recorded per-file outcomes."""
    results = (
        ConversionResult(status=ConversionStatus.SUCCESS, source_path=Path("a.md")),
        ConversionResult(status=ConversionStatus.SUCCESS, source_path=Path("b.md")),
    )
    run = BatchRun(tuple(result.source_path for result in results))
    run.begin()
    run.record_result(results[0])
    run.next_source()
    run.record_result(results[1])

    assert run.succeeded == 2
    assert run.warnings == 0
    assert run.failed == 0
    assert run.is_complete is True


# ============================================================
# Per-file ownership
# ============================================================


def test_each_file_keeps_its_own_findings(window: "MainWindow", tmp_path: Path) -> None:
    """A warning in one file never leaks into another file's report."""
    from md_converter.gui.result_details import build_report_text

    run = _run_batch(
        window,
        tmp_path,
        {"clean.md": SUCCESS_BODY, "warned.md": WARNING_BODY},
    )
    items = _items_by_name(run)

    clean_item = items["clean.md"]
    warned_item = items["warned.md"]
    clean_report = build_report_text(clean_item.presentation, clean_item.result)
    warned_report = build_report_text(warned_item.presentation, warned_item.result)

    assert clean_item.status is BatchItemStatus.SUCCESS
    assert "Quality findings" not in clean_report
    assert "Suggested review" not in clean_report

    assert warned_item.status is BatchItemStatus.SUCCESS_WITH_WARNING
    assert "Quality findings (1)" in warned_report
    assert "QA_STATIC_WARN" in warned_report
    assert "Suggested review" in warned_report
    assert "clean.md" not in warned_report


def test_mixed_batch_results_keep_finding_ownership(window: "MainWindow", tmp_path: Path) -> None:
    """Success, warning and failure each keep their own status and findings."""
    from md_converter.gui.result_details import build_report_text

    run = _run_batch(
        window,
        tmp_path,
        {
            "first.md": SUCCESS_BODY,
            "broken.md": FAILURE_BODY,
            "third.md": WARNING_BODY,
        },
    )
    items = _items_by_name(run)

    assert items["first.md"].status is BatchItemStatus.SUCCESS
    assert items["broken.md"].status is BatchItemStatus.FAILED
    assert items["third.md"].status is BatchItemStatus.SUCCESS_WITH_WARNING

    broken_report = build_report_text(items["broken.md"].presentation, items["broken.md"].result)
    third_report = build_report_text(items["third.md"].presentation, items["third.md"].result)

    assert "Status: FAILED" in broken_report
    assert "Quality findings (1)" in broken_report
    assert "ERROR" in broken_report
    assert "WARNING" not in broken_report

    assert "Status: SUCCESS_WITH_WARNING" in third_report
    assert "WARNING" in third_report
    assert "ERROR" not in third_report

    assert run.succeeded == 1
    assert run.warnings == 1
    assert run.failed == 1


def test_window_shows_no_single_file_quality_panel_for_a_batch(
    window: "MainWindow", tmp_path: Path
) -> None:
    """A multi-file batch never presents one file's findings as the batch's."""
    _run_batch(window, tmp_path, {"clean.md": SUCCESS_BODY, "warned.md": WARNING_BODY})
    window.show()
    _pump()

    assert window.preflight_area.isVisible() is False
    assert window.preflight_list.count() == 0


def test_batch_report_row_opens_the_owning_file_record(
    window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``Details...`` on a batch row opens that row's retained evidence."""
    import importlib

    run = _run_batch(window, tmp_path, {"clean.md": SUCCESS_BODY, "warned.md": WARNING_BODY})
    module = importlib.import_module("md_converter.gui.batch_report")
    calls: List[Tuple[object, object, object]] = []
    monkeypatch.setattr(
        module,
        "show_result_details",
        lambda parent, presentation, evidence: calls.append((parent, presentation, evidence)),
    )

    dialog = module.BatchReportDialog(run, window)
    try:
        warned_index = [item.source_path.name for item in run.items].index("warned.md")
        dialog.items_view.setCurrentRow(warned_index)
        _pump()
        assert dialog.details_button.isEnabled() is True
        assert dialog.show_selected_details() is True
    finally:
        dialog.close()

    assert len(calls) == 1
    parent, presentation, evidence = calls[0]
    assert parent is dialog
    assert presentation is run.items[warned_index].presentation
    assert evidence is run.items[warned_index].result
    assert presentation.outcome.value == "SUCCESS_WITH_WARNING"


def test_batch_item_without_evidence_disables_details(window: "MainWindow", tmp_path: Path) -> None:
    """An item that retained no evidence offers no details affordance."""
    import importlib

    from md_converter.gui.batch import BatchSelection, source_identity

    selection = BatchSelection()
    source = _write_markdown(tmp_path / "pending.md", SUCCESS_BODY)
    selection.add((source,))
    run = BatchRun(selection.sources)
    run.begin()

    module = importlib.import_module("md_converter.gui.batch_report")
    dialog = module.BatchReportDialog(run, window)
    try:
        assert dialog.selected_item() is not None
        assert source_identity(dialog.selected_item().source_path) == source_identity(source)
        assert dialog.show_selected_details() is False
    finally:
        dialog.close()
