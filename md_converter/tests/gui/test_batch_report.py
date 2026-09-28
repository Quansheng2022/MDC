"""Focused verification for the lightweight batch report surface (SBC-05).

The dialog is presentation only: it renders the retained batch evidence that
``BatchRun`` already assembled, keeps the aggregate text read-only, offers the
single existing report surface for a selected row, and stays keyboard usable.
"""

from __future__ import annotations

import importlib
import os
from pathlib import Path
from typing import List

import pytest

from md_converter.application.conversion_result import (
    ConversionErrorCategory,
    ConversionResult,
    ConversionStatus,
)
from md_converter.application.diagnostics_adapter import ApplicationDiagnostic
from md_converter.gui.batch import BatchRun

pytest.importorskip("PySide6", reason="PySide6 (GUI dev dependency) is not installed")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt  # noqa: E402 - the Qt guard must run first
from PySide6.QtTest import QTest  # noqa: E402 - the Qt guard must run first
from PySide6.QtWidgets import QApplication, QDialog  # noqa: E402 - the Qt guard must run first

from md_converter.gui.batch_report import (  # noqa: E402 - the Qt guard must run first
    BATCH_ITEMS_ACCESSIBLE_NAME,
    BATCH_REPORT_ACCESSIBLE_NAME,
    BATCH_REPORT_TITLE,
    CLOSE_TEXT,
    COPY_TEXT,
    DETAILS_TEXT,
    BatchReportDialog,
    batch_item_row_text,
)

BATCH_REPORT_MODULE = "md_converter.gui.batch_report"


def _application() -> QApplication:
    """Return the process QApplication, creating it when necessary."""
    from md_converter.gui.app import create_application

    return create_application([])


def _completed_run(tmp_path: Path) -> BatchRun:
    """Return a finished three-file batch with all three outcome kinds."""
    record = ApplicationDiagnostic(
        severity="WARNING",
        code="QA_STATIC_WARN",
        message="QA_STATIC_WARN technical message",
        user_message="A heading style was adjusted.",
    )
    success_doc = tmp_path / "a.docx"
    warning_doc = tmp_path / "b.docx"
    success_doc.write_bytes(b"PK\x03\x04")
    warning_doc.write_bytes(b"PK\x03\x04")

    run = BatchRun([tmp_path / "a.md", tmp_path / "b.md", tmp_path / "c.md"])
    run.begin()
    run.record_result(ConversionResult(status=ConversionStatus.SUCCESS, output_path=success_doc))
    run.next_source()
    run.record_result(
        ConversionResult(
            status=ConversionStatus.SUCCESS_WITH_WARNING,
            output_path=warning_doc,
            warnings=(record,),
            diagnostics=(record,),
        )
    )
    run.next_source()
    run.record_result(
        ConversionResult(
            status=ConversionStatus.FAILED,
            error_category=ConversionErrorCategory.CONVERSION_ERROR,
            error_message="The document could not be generated.",
        )
    )
    run.next_source()
    return run


def test_dialog_presents_the_aggregate_report(tmp_path: Path) -> None:
    """§22: the dialog shows the derived summary and the retained report text."""
    _application()
    run = _completed_run(tmp_path)
    dialog = BatchReportDialog(run)
    try:
        assert dialog.windowTitle() == BATCH_REPORT_TITLE
        assert dialog.summary_label.text() == run.status_line()
        assert dialog.report_view.isReadOnly() is True
        assert dialog.report_view.toPlainText() == run.report_text()
        assert dialog.report_text == run.report_text()
    finally:
        dialog.close()


def test_every_item_gets_a_row_and_a_tooltip(tmp_path: Path) -> None:
    """§23: each source is listed with its own status."""
    _application()
    run = _completed_run(tmp_path)
    dialog = BatchReportDialog(run)
    try:
        rows = [dialog.items_view.item(index).text() for index in range(dialog.items_view.count())]
        assert rows == [batch_item_row_text(item) for item in run.items]
        assert rows[0].endswith("succeeded")
        assert rows[1].endswith("warning")
        assert rows[2].endswith("failed")
        assert str(tmp_path / "c.md") in dialog.items_view.item(2).toolTip()
    finally:
        dialog.close()


def test_details_action_reuses_the_single_report_surface(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """§23: per-row evidence opens the accepted report surface, not a second one."""
    _application()
    module = importlib.import_module(BATCH_REPORT_MODULE)
    calls: List[tuple] = []
    monkeypatch.setattr(
        module,
        "show_result_details",
        lambda parent, presentation, evidence: calls.append((parent, presentation, evidence)),
    )

    run = _completed_run(tmp_path)
    dialog = BatchReportDialog(run)
    try:
        assert dialog.details_button.isEnabled() is True
        assert dialog.show_selected_details() is True
        parent, presentation, evidence = calls[0]
        assert parent is dialog
        assert presentation is run.items[0].presentation
        assert evidence is run.items[0].result
    finally:
        dialog.close()


def test_details_action_is_disabled_without_evidence(tmp_path: Path) -> None:
    """A row without retained evidence offers no details action."""
    _application()
    run = BatchRun([tmp_path / "a.md", tmp_path / "b.md"])
    run.begin()
    run.record_result(
        ConversionResult(status=ConversionStatus.SUCCESS, output_path=tmp_path / "a.docx")
    )
    run.abort("stopped")

    dialog = BatchReportDialog(run)
    try:
        dialog.items_view.setCurrentRow(1)
        assert dialog.selected_item() is not None
        assert dialog.selected_item().status.value == "PENDING"
        assert dialog.details_button.isEnabled() is False
        assert dialog.show_selected_details() is False
        assert "NOT PROCESSED" in dialog.report_text
    finally:
        dialog.close()


def test_copy_button_copies_the_report(tmp_path: Path) -> None:
    """The aggregate report can be copied without any export or upload."""
    _application()
    run = _completed_run(tmp_path)
    dialog = BatchReportDialog(run)
    try:
        QApplication.clipboard().clear()
        dialog.copy_button.click()
        assert QApplication.clipboard().text() == run.report_text()
    finally:
        dialog.close()


def test_close_button_and_escape_reject_the_dialog(tmp_path: Path) -> None:
    """The surface is dismissable from the keyboard and the button."""
    _application()
    run = _completed_run(tmp_path)
    dialog = BatchReportDialog(run)
    try:
        dialog.show()
        QTest.keyClick(dialog, Qt.Key.Key_Escape)
        assert dialog.result() == int(QDialog.DialogCode.Rejected)
    finally:
        dialog.close()


def test_report_surface_is_keyboard_reachable(tmp_path: Path) -> None:
    """§31: the report surfaces carry accessible names and take focus."""
    _application()
    run = _completed_run(tmp_path)
    dialog = BatchReportDialog(run)
    try:
        assert dialog.items_view.accessibleName() == BATCH_ITEMS_ACCESSIBLE_NAME
        assert dialog.report_view.accessibleName() == BATCH_REPORT_ACCESSIBLE_NAME
        assert dialog.details_button.accessibleName() == DETAILS_TEXT
        assert dialog.copy_button.accessibleName() == COPY_TEXT
        assert dialog.close_button.accessibleName() == CLOSE_TEXT
        assert dialog.items_view.focusPolicy() & Qt.FocusPolicy.TabFocus
        assert dialog.report_view.focusPolicy() & Qt.FocusPolicy.TabFocus
    finally:
        dialog.close()
