"""Focused verification for the main window foundation (WP-P12-04-02 §9).

The window is verified as a *visible shell*: required controls exist, carry
plain-language labels, survive resizing, and are not wired to conversion.

The controls are inert placeholders at this stage.  Later work packages add the
GUI state model (WP-P12-04-03), file picker (WP-P12-04-04), drag & drop
(WP-P12-04-05) and output selection (WP-P12-04-06); the stage guards marked
below are expected to be updated by those work packages.
"""

from __future__ import annotations

import ast
import os
from pathlib import Path
from typing import TYPE_CHECKING, Set

import pytest

if TYPE_CHECKING:  # pragma: no cover - typing only
    from md_converter.gui.main_window import MainWindow

pytest.importorskip("PySide6", reason="PySide6 (GUI dev dependency) is not installed")

#: Qt needs a platform plugin even when a test only constructs widgets.  Set
#: here (not in a directory ``conftest.py``) because the test tree is not a
#: package and a second ``conftest`` would shadow ``md_converter/tests/conftest.py``.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = Path(__file__).resolve().parents[3]
GUI_DIR = PROJECT_ROOT / "md_converter" / "gui"

#: Object names of the WP-P12-04-02 shell controls.
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

#: Conversion-core / application-layer modules the GUI layer must not import.
FORBIDDEN_IMPORT_PREFIXES = (
    "md_converter.application",
    "md_converter.compiler",
    "md_converter.parser",
    "md_converter.pipeline",
    "md_converter.renderer",
)


def _make_window() -> "MainWindow":
    """Return a fresh ``MainWindow``, ensuring a QApplication exists."""
    from md_converter.gui.app import create_application
    from md_converter.gui.main_window import MainWindow

    create_application([])
    return MainWindow()


def _process_events() -> None:
    """Deliver pending Qt events (layout/resize) without entering the loop."""
    from PySide6.QtWidgets import QApplication

    QApplication.instance().processEvents()


def _imported_modules(path: Path) -> Set[str]:
    """Return the module names imported by ``path``."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module:
                names.add(module)
            names.update(f"{module}.{alias.name}".lstrip(".") for alias in node.names)
    return names


# ============================================================
# Required controls and labels
# ============================================================


def test_window_renders_required_controls() -> None:
    """WP §4: every shell control is present in the window."""
    from PySide6.QtWidgets import QWidget

    window = _make_window()
    try:
        for object_name in REQUIRED_WIDGETS:
            assert window.findChild(QWidget, object_name) is not None, object_name
    finally:
        window.close()


def test_controls_have_understandable_labels() -> None:
    """WP §5: plain product language, no technical or CLI-style wording."""
    from PySide6.QtWidgets import QWidget

    from md_converter.gui.main_window import (
        CHANGE_OUTPUT_TEXT,
        CONVERT_TEXT,
        DROP_HINT_TEXT,
        OUTPUT_CAPTION_TEXT,
        OUTPUT_VALUE_TEXT,
        SELECT_FILE_TEXT,
    )

    expected_text = {
        "dropLabel": DROP_HINT_TEXT,
        "selectFileButton": SELECT_FILE_TEXT,
        "outputCaptionLabel": OUTPUT_CAPTION_TEXT,
        "outputValueLabel": OUTPUT_VALUE_TEXT,
        "changeOutputButton": CHANGE_OUTPUT_TEXT,
        "convertButton": CONVERT_TEXT,
    }

    window = _make_window()
    try:
        for object_name, text in expected_text.items():
            widget = window.findChild(QWidget, object_name)
            assert widget is not None, object_name
            assert widget.text() == text
            assert text and text.strip() == text
            assert "--" not in text
            assert "CompilerContext" not in text
            assert "ConversionService" not in text

        # The status text is state-driven from WP-P12-04-03 onwards; its exact
        # per-state wording is asserted by the GUI state-model tests.
        status = window.findChild(QWidget, "statusLabel")
        assert status is not None
        assert status.text().strip()
        assert "--" not in status.text()
    finally:
        window.close()


def test_resize_keeps_primary_layout_intact() -> None:
    """WP §9: resizing (including the minimum size) keeps controls visible."""
    from PySide6.QtWidgets import QWidget

    window = _make_window()
    try:
        window.show()
        _process_events()

        for width, height in ((640, 480), (1024, 768), (1600, 1000)):
            window.resize(width, height)
            _process_events()
            for object_name in REQUIRED_WIDGETS:
                widget = window.findChild(QWidget, object_name)
                assert widget is not None, object_name
                assert widget.isVisible(), f"{object_name} hidden at {width}x{height}"
    finally:
        window.close()


# ============================================================
# Stage guards: behavior is not implemented by this work package
# ============================================================


def test_convert_is_not_wired_to_conversion() -> None:
    """WP §6/§9: Convert is an inert placeholder and changes nothing.

    Stage guard: the state model (WP-P12-04-03) now owns Convert enablement; the
    real action is wired through the application service by a later work
    package, which will update this guard.
    """
    window = _make_window()
    try:
        window.show()
        _process_events()
        status_before = window.status_label.text()

        window.convert_button.click()
        _process_events()

        assert window.convert_button.isEnabled() is False
        assert window.status_label.text() == status_before
    finally:
        window.close()


def test_drop_acceptance_follows_gui_state() -> None:
    """Drop acceptance is driven by the GUI state (WP-P12-04-05).

    Replaces the WP-P12-04-02 stage guard now that drag & drop exists: the
    window itself still implements no drag/drop handlers - the drop area owns
    them - and the drop area accepts input only in states that allow it.
    """
    from md_converter.gui.main_window import MainWindow

    window = _make_window()
    try:
        assert window.drop_zone.acceptDrops() is True
        for handler in ("dragEnterEvent", "dragMoveEvent", "dragLeaveEvent", "dropEvent"):
            assert handler not in MainWindow.__dict__, handler

        window.set_source("notes.md")
        assert window.drop_zone.acceptDrops() is True

        window.request_convert()
        assert window.drop_zone.acceptDrops() is False
    finally:
        window.close()


def test_gui_layer_imports_no_conversion_core() -> None:
    """WP §10: no Core / application-service import inside the GUI layer."""
    modules = sorted(GUI_DIR.glob("*.py"))

    assert modules
    for module in modules:
        offenders = {
            name for name in _imported_modules(module) if name.startswith(FORBIDDEN_IMPORT_PREFIXES)
        }
        assert not offenders, f"{module.name} imports {sorted(offenders)}"
