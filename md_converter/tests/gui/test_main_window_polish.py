"""Focused GUI regression for the product polish (WP-P12-07-04).

The polish work is cosmetic, so the guard is deliberately narrow: the frozen
workflow, the required controls and every existing semantic must be unchanged,
while spacing, wording, tooltips and sizing stay consistent.

The assertions stay on widget facts (labels, tooltips, minimum widths, margins)
so the test is a regression guard rather than a style opinion.
"""

from __future__ import annotations

import ast
import os
from pathlib import Path
from typing import TYPE_CHECKING, Iterator, Set

import pytest

if TYPE_CHECKING:  # pragma: no cover - typing only
    from md_converter.gui.main_window import MainWindow

pytest.importorskip("PySide6", reason="PySide6 (GUI dev dependency) is not installed")

#: Qt needs a platform plugin even when a test only constructs widgets.  Set
#: here (not in a directory ``conftest.py``) because the test tree is not a
#: package and a second ``conftest`` would shadow ``md_converter/tests/conftest.py``.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import (  # noqa: E402 - guard runs first
    QApplication,
    QMenuBar,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QWidget,
    QWizard,
)

from md_converter.gui.main_window import (  # noqa: E402 - guard runs first
    ABOUT_TEXT,
    ABOUT_TOOLTIP,
    CHANGE_OUTPUT_TEXT,
    CHANGE_OUTPUT_TOOLTIP,
    CONVERT_MINIMUM_WIDTH,
    CONVERT_TEXT,
    CONVERT_TOOLTIP,
    DETAILS_TEXT,
    DETAILS_TOOLTIP,
    DROP_HINT_TEXT,
    DROP_SUB_HINT_TEXT,
    DROP_ZONE_TOOLTIP,
    FOOTER_BUTTON_MINIMUM_WIDTH,
    LAYOUT_MARGIN_BOTTOM,
    LAYOUT_MARGIN_HORIZONTAL,
    LAYOUT_MARGIN_TOP,
    LAYOUT_SPACING,
    OPEN_DOCUMENT_TEXT,
    OPEN_DOCUMENT_TOOLTIP,
    OPEN_FOLDER_TEXT,
    OPEN_FOLDER_TOOLTIP,
    SECONDARY_BUTTON_MINIMUM_WIDTH,
    SELECT_FILE_TEXT,
    SELECT_FILE_TOOLTIP,
    SETTINGS_TEXT,
    SETTINGS_TOOLTIP,
)
from md_converter.gui.state import GuiState  # noqa: E402 - guard runs first

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MAIN_WINDOW_MODULE = PROJECT_ROOT / "md_converter" / "gui" / "main_window.py"

#: Object names of the frozen workflow controls (WP-P12-04-02 shell).
REQUIRED_WIDGETS = (
    "dropZone",
    "dropLabel",
    "selectFileButton",
    "outputCaptionLabel",
    "outputValueLabel",
    "changeOutputButton",
    "convertButton",
    "statusLabel",
)

#: Conversion states the polish must not add to or rename.
FROZEN_STATES = (
    "EMPTY",
    "READY",
    "CONVERTING",
    "SUCCESS",
    "SUCCESS_WITH_WARNING",
    "FAILED",
)


@pytest.fixture
def window(tmp_path: Path) -> Iterator["MainWindow"]:
    """Provide a main window over an isolated preference store."""
    from md_converter.gui.app import create_application
    from md_converter.gui.main_window import MainWindow
    from md_converter.gui.preferences import GuiPreferences

    create_application([])
    instance = MainWindow(preferences=GuiPreferences.for_file(tmp_path / "prefs.ini"))
    yield instance
    instance.close()


def _pump() -> None:
    """Deliver pending Qt events (layout/resize)."""
    QApplication.instance().processEvents()


def _markdown(tmp_path: Path, name: str = "notes.md") -> Path:
    """Write a minimal Markdown source and return its path."""
    path = tmp_path / name
    path.write_text("# Notes\n\nBody text.\n", encoding="utf-8")
    return path


# ============================================================
# Frozen workflow and controls
# ============================================================


def test_required_controls_are_unchanged(window: "MainWindow") -> None:
    """WP §Frozen Workflow: every existing control is still present."""
    for object_name in REQUIRED_WIDGETS:
        assert window.findChild(QWidget, object_name) is not None, object_name


def test_workflow_states_are_unchanged() -> None:
    """WP §Frozen Workflow: EMPTY -> READY -> CONVERTING -> outcomes only."""
    assert tuple(member.name for member in GuiState) == FROZEN_STATES


def test_state_paths_still_work(window: "MainWindow", tmp_path: Path) -> None:
    """The polish did not disturb the existing state transitions."""
    assert window.state is GuiState.EMPTY
    assert window.set_source_file(str(_markdown(tmp_path))) is GuiState.READY
    assert window.request_convert() is GuiState.CONVERTING
    assert window.simulate_warning() is GuiState.SUCCESS_WITH_WARNING
    assert window.reset() is GuiState.EMPTY


def test_label_wording_is_unchanged(window: "MainWindow") -> None:
    """The accepted primary wording survives the polish."""
    assert window.drop_label.text() == DROP_HINT_TEXT
    assert window.select_file_button.text() == SELECT_FILE_TEXT
    assert window.change_output_button.text() == CHANGE_OUTPUT_TEXT
    assert window.convert_button.text() == CONVERT_TEXT
    assert window.details_button.text() == DETAILS_TEXT
    assert window.open_document_button.text() == OPEN_DOCUMENT_TEXT
    assert window.open_folder_button.text() == OPEN_FOLDER_TEXT
    assert window.settings_button.text() == SETTINGS_TEXT
    assert window.about_button.text() == ABOUT_TEXT


def test_empty_state_wording_is_helpful_and_local(window: "MainWindow") -> None:
    """WP §Authorized: empty-state wording explains what is accepted."""
    assert window.drop_sub_label.text() == DROP_SUB_HINT_TEXT
    assert ".md" in DROP_SUB_HINT_TEXT
    assert DROP_SUB_HINT_TEXT.strip() == DROP_SUB_HINT_TEXT
    assert "computer" in DROP_SUB_HINT_TEXT


# ============================================================
# Consistency
# ============================================================


def test_layout_uses_one_margin_and_spacing_scale(window: "MainWindow") -> None:
    """WP §Authorized: consistent margins and spacing."""
    layout = window.centralWidget().layout()
    margins = layout.contentsMargins()

    assert margins.left() == margins.right() == LAYOUT_MARGIN_HORIZONTAL
    assert margins.top() == LAYOUT_MARGIN_TOP
    assert margins.bottom() == LAYOUT_MARGIN_BOTTOM
    assert layout.spacing() == LAYOUT_SPACING


def test_primary_controls_carry_tooltips(window: "MainWindow") -> None:
    """WP §Authorized: tooltips on the controls the user acts on."""
    expected = {
        "dropZone": DROP_ZONE_TOOLTIP,
        "selectFileButton": SELECT_FILE_TOOLTIP,
        "changeOutputButton": CHANGE_OUTPUT_TOOLTIP,
        "convertButton": CONVERT_TOOLTIP,
        "detailsButton": DETAILS_TOOLTIP,
        "openDocumentButton": OPEN_DOCUMENT_TOOLTIP,
        "openFolderButton": OPEN_FOLDER_TOOLTIP,
        "settingsButton": SETTINGS_TOOLTIP,
        "aboutButton": ABOUT_TOOLTIP,
    }

    for object_name, tooltip in expected.items():
        widget = window.findChild(QWidget, object_name)
        assert widget is not None, object_name
        assert widget.toolTip() == tooltip
        assert tooltip.strip() == tooltip
        assert tooltip


def test_button_sizing_is_consistent(window: "MainWindow") -> None:
    """WP §Authorized: even button sizing across the three action groups."""
    assert window.convert_button.minimumWidth() == CONVERT_MINIMUM_WIDTH
    assert window.select_file_button.minimumWidth() == SECONDARY_BUTTON_MINIMUM_WIDTH
    assert window.change_output_button.minimumWidth() == SECONDARY_BUTTON_MINIMUM_WIDTH
    assert window.settings_button.minimumWidth() == FOOTER_BUTTON_MINIMUM_WIDTH
    assert window.about_button.minimumWidth() == FOOTER_BUTTON_MINIMUM_WIDTH


def test_wording_has_no_technical_jargon(window: "MainWindow") -> None:
    """WP §Authorized: plain product language only."""
    texts = [
        window.drop_label.text(),
        window.drop_sub_label.text(),
        window.select_file_button.text(),
        window.change_output_button.text(),
        window.convert_button.text(),
        window.status_label.text(),
    ]
    texts += [widget.toolTip() for widget in window.findChildren(QWidget) if widget.toolTip()]

    for text in texts:
        for jargon in ("--", "CompilerContext", "ConversionService", "AST", "QA"):
            assert jargon not in text, (text, jargon)


def test_polish_added_no_new_workflow(window: "MainWindow") -> None:
    """WP §Forbidden: no dashboard, sidebar, wizard or extra state."""
    for widget_type in (QTabWidget, QSplitter, QToolBar, QStatusBar, QWizard, QMenuBar):
        assert not window.findChildren(widget_type), widget_type.__name__


def test_polish_added_exactly_two_entry_points(window: "MainWindow") -> None:
    """WP §Authorized: Settings and About are the only new surfaces."""
    from PySide6.QtWidgets import QPushButton

    new_buttons = {"settingsButton", "aboutButton"}
    dialog_entry_points = {
        button.objectName()
        for button in window.findChildren(QPushButton)
        if button.objectName() in new_buttons
    }

    assert dialog_entry_points == new_buttons


def test_polished_layout_survives_the_minimum_size(window: "MainWindow") -> None:
    """The accepted minimum size still shows the primary controls."""
    window.show()
    _pump()

    for width, height in ((640, 480), (1024, 768), (1600, 1000)):
        window.resize(width, height)
        _pump()
        for object_name in REQUIRED_WIDGETS + ("settingsButton", "aboutButton"):
            widget = window.findChild(QWidget, object_name)
            assert widget is not None, object_name
            assert widget.isVisible(), f"{object_name} hidden at {width}x{height}"


def test_polish_touched_no_semantic_code() -> None:
    """The polish is presentational: conversion semantics stay outside the window."""
    tree = ast.parse(MAIN_WINDOW_MODULE.read_text(encoding="utf-8"))
    resolved = MAIN_WINDOW_MODULE.resolve().relative_to(PROJECT_ROOT)
    package_parts = list(resolved.with_suffix("").parts)[:-1]
    imported: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                keep = len(package_parts) - (node.level - 1)
                base = ".".join(package_parts[:keep]) if keep > 0 else ""
                module = f"{base}.{module}" if module else base
            if module:
                imported.add(module)
                imported.update(f"{module}.{alias.name}" for alias in node.names)

    offenders = {
        name
        for name in imported
        if name.startswith(
            (
                "md_converter.compiler",
                "md_converter.parser",
                "md_converter.pipeline",
                "md_converter.renderer",
                "md_converter.services",
                "md_converter.quality_gate",
            )
        )
    }
    assert not offenders, sorted(offenders)

    calls = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert "compile_file" not in calls
    assert "get_quality_gate_report" not in calls
