"""Focused verification for the document-quality (preflight) UX (WP-DI-03).

The surface is the smallest compatible UX from the implementation plan: a
compact, read-only section under the workflow that presents the findings the
authoritative conversion already reported.  These tests pin the accepted
product rules:

* the panel only appears when there is something to show;
* warnings stay non-blocking and the document is still produced;
* existing fatal errors keep their existing meaning;
* findings are textual, keyboard reachable and never colour-only;
* the window composes no wording of its own.
"""

from __future__ import annotations

import ast
import os
import time
from pathlib import Path
from typing import TYPE_CHECKING, Callable, List

import pytest

if TYPE_CHECKING:  # pragma: no cover - typing only
    from md_converter.gui.main_window import MainWindow

pytest.importorskip("PySide6", reason="PySide6 (GUI dev dependency) is not installed")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt  # noqa: E402 - the Qt guard must run first
from PySide6.QtTest import QTest  # noqa: E402 - the Qt guard must run first
from PySide6.QtWidgets import QApplication, QVBoxLayout  # noqa: E402 - guard runs first

from md_converter.gui.main_window import (  # noqa: E402 - the Qt guard must run first
    PREFLIGHT_CAPTION_TEXT,
    PREFLIGHT_LIST_ACCESSIBLE_NAME,
    PREFLIGHT_TOOLTIP,
)
from md_converter.gui.state import GuiState  # noqa: E402 - the Qt guard must run first

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MAIN_WINDOW_MODULE = PROJECT_ROOT / "md_converter" / "gui" / "main_window.py"

SUCCESS_BODY = "# Notes\n\nBody text.\n"
WARNING_BODY = "#\n\nSome body text.\n"
FAILURE_BODY = ""

#: Diagnostic fields the window must never interpret itself.
FORBIDDEN_WINDOW_ATTRIBUTES = (
    "diagnostics",
    "diagnostic_summary",
    "errors",
    "quality_gate_report",
    "technical_detail",
    "warnings",
)


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


def _convert(window: "MainWindow", source: Path) -> None:
    """Run one real conversion through the window and wait for completion."""
    assert window.set_source_file(str(source)) is GuiState.READY
    window.start_conversion()
    assert _wait_until(
        lambda: window.state is not GuiState.CONVERTING and not window.worker.is_running
    )


def _rows(window: "MainWindow") -> List[str]:
    """Return the presented finding rows of the window."""
    return [
        window.preflight_list.item(index).text() for index in range(window.preflight_list.count())
    ]


# ============================================================
# Appearance rules
# ============================================================


def test_panel_is_hidden_before_any_conversion(window: "MainWindow", tmp_path: Path) -> None:
    """Nothing is presented before a conversion: no empty panel, no Tab stop."""
    window.show()
    _pump()

    assert window.preflight_area.isVisible() is False
    assert window.preflight_list.count() == 0

    assert window.set_source_file(str(_write_markdown(tmp_path / "notes.md"))) is GuiState.READY
    window.show()
    _pump()
    assert window.preflight_area.isVisible() is False


def test_panel_stays_hidden_for_a_clean_document(window: "MainWindow", tmp_path: Path) -> None:
    """A document without findings keeps the accepted compact surface."""
    _convert(window, _write_markdown(tmp_path / "clean.md"))
    window.show()
    _pump()

    assert window.state is GuiState.SUCCESS
    assert window.preflight_area.isVisible() is False
    assert window.preflight_list.count() == 0


def test_panel_lists_findings_after_a_warning_conversion(
    window: "MainWindow", tmp_path: Path
) -> None:
    """A warning is presented with counts, severity wording and traceability."""
    _convert(window, _write_markdown(tmp_path / "warned.md", WARNING_BODY))
    window.show()
    _pump()

    assert window.state is GuiState.SUCCESS_WITH_WARNING
    assert window.preflight_area.isVisible() is True

    rows = _rows(window)
    assert len(rows) == window.preflight_list.count() == 1
    assert "WARNING" in rows[0]
    assert "QA_STATIC_WARN" in rows[0]
    assert window.preflight_summary_label.text().strip()

    result = window.latest_result
    assert result is not None and result.diagnostic_summary is not None
    assert window.preflight_summary_label.text() == result.diagnostic_summary.user_message


def test_error_findings_are_presented(window: "MainWindow", tmp_path: Path) -> None:
    """A failed conversion presents its error findings without inventing any."""
    _convert(window, _write_markdown(tmp_path / "broken.md", FAILURE_BODY))
    window.show()
    _pump()

    assert window.state is GuiState.FAILED
    assert window.preflight_area.isVisible() is True
    rows = _rows(window)
    assert rows
    assert any("ERROR" in row for row in rows)


# ============================================================
# Accepted semantics are unchanged
# ============================================================


def test_warning_does_not_block_the_conversion(window: "MainWindow", tmp_path: Path) -> None:
    """A warning-only document is still produced and still actionable."""
    _convert(window, _write_markdown(tmp_path / "warned.md", WARNING_BODY))
    window.show()
    _pump()

    result = window.latest_result
    assert result is not None
    assert result.is_success_with_warning is True
    assert result.output_path is not None and result.output_path.exists()
    assert window.open_document_button.isEnabled() is True
    assert window.convert_button.isEnabled() is False
    assert window.details_button.isEnabled() is True


def test_fatal_errors_keep_their_existing_meaning(window: "MainWindow", tmp_path: Path) -> None:
    """A failed conversion offers no output action and no false success."""
    _convert(window, _write_markdown(tmp_path / "broken.md", FAILURE_BODY))
    window.show()
    _pump()

    assert window.state is GuiState.FAILED
    assert window.open_document_button.isVisible() is False
    assert window.open_folder_button.isVisible() is False
    assert window.details_button.isEnabled() is True


def test_selecting_another_source_clears_the_findings(window: "MainWindow", tmp_path: Path) -> None:
    """Findings belong to one document and never leak to the next selection."""
    warned = _write_markdown(tmp_path / "warned.md", WARNING_BODY)
    _convert(window, warned)
    window.show()
    _pump()
    assert window.preflight_area.isVisible() is True

    assert window.set_source_file(str(_write_markdown(tmp_path / "clean.md"))) is GuiState.READY
    window.show()
    _pump()

    assert window.preflight_area.isVisible() is False
    assert window.preflight_summary_label.text() == ""
    assert window.preflight_list.count() == 0


def test_reconverting_does_not_duplicate_rows(window: "MainWindow", tmp_path: Path) -> None:
    """Repeated conversions refresh the panel instead of appending to it."""
    source = _write_markdown(tmp_path / "warned.md", WARNING_BODY)

    _convert(window, source)
    first = len(_rows(window))
    _convert(window, source)

    assert first == len(_rows(window))


# ============================================================
# Accessibility
# ============================================================


def test_panel_carries_accessible_identities(window: "MainWindow") -> None:
    """The surface is named for assistive technology."""
    assert window.preflight_list.accessibleName() == PREFLIGHT_LIST_ACCESSIBLE_NAME
    assert window.preflight_summary_label.accessibleName().strip()
    assert window.preflight_list.toolTip() == PREFLIGHT_TOOLTIP
    labels = window.preflight_area.findChildren(type(window.preflight_summary_label))
    assert PREFLIGHT_CAPTION_TEXT in [label.text() for label in labels]


def test_findings_are_keyboard_reachable_when_visible(window: "MainWindow", tmp_path: Path) -> None:
    """The visible panel joins the workflow Tab order; a hidden one is skipped."""
    _convert(window, _write_markdown(tmp_path / "warned.md", WARNING_BODY))
    window.show()
    _pump()

    assert window.preflight_list.focusPolicy() & Qt.FocusPolicy.TabFocus
    window.select_file_button.setFocus()
    _pump()

    visited = []
    for _ in range(10):
        QTest.keyClick(QApplication.focusWidget(), Qt.Key.Key_Tab)
        _pump()
        current = QApplication.focusWidget()
        visited.append(current)
        if current is window.preflight_list:
            break

    assert window.preflight_list in visited
    assert window.batch_list not in visited


def test_findings_are_textual_not_colour_only(window: "MainWindow", tmp_path: Path) -> None:
    """Every row names its severity, so no meaning depends on colour."""
    _convert(window, _write_markdown(tmp_path / "warned.md", WARNING_BODY))

    rows = _rows(window)
    assert rows
    for row in rows:
        assert any(word in row for word in ("ERROR", "FATAL", "WARNING", "INFO"))


def test_panel_uses_the_standard_layout(window: "MainWindow") -> None:
    """The surface uses the shared layout: no absolute positioning, no styling."""
    assert isinstance(window.centralWidget().layout(), QVBoxLayout)
    source = MAIN_WINDOW_MODULE.read_text(encoding="utf-8")
    for styling in ("setStyleSheet", "setGeometry"):
        assert styling not in source, styling
    assert window.preflight_area.parent() is not None


# ============================================================
# Window boundary
# ============================================================


def test_window_still_composes_no_finding_wording() -> None:
    """The window reads no raw diagnostic field and builds no finding text."""
    tree = ast.parse(MAIN_WINDOW_MODULE.read_text(encoding="utf-8"))
    attributes = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}

    assert not (attributes & set(FORBIDDEN_WINDOW_ATTRIBUTES))

    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
    assert "preflight_from_result" in imported
