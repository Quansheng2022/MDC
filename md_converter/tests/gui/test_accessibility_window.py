"""Focused verification for keyboard, focus, accessibility and window
behaviour (WP-P12-07-05).

Covered:

* a logical Tab order and standard activation behaviour;
* a bounded accessibility baseline (accessible names, text-based status);
* the read-only report stays keyboard reachable;
* the accepted window behaviour (sane minimum, safe geometry, normal close) and
  the frozen rule that an active worker blocks an unsafe close;
* a bounded High-DPI smoke run in a real Qt process.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING, Iterator, List
from unittest import mock

import pytest

if TYPE_CHECKING:  # pragma: no cover - typing only
    from md_converter.gui.main_window import MainWindow

pytest.importorskip("PySide6", reason="PySide6 (GUI dev dependency) is not installed")

#: Qt needs a platform plugin even when a test only constructs widgets.  Set
#: here (not in a directory ``conftest.py``) because the test tree is not a
#: package and a second ``conftest`` would shadow ``md_converter/tests/conftest.py``.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QByteArray, Qt  # noqa: E402 - guard runs first
from PySide6.QtGui import QKeySequence  # noqa: E402 - guard runs first
from PySide6.QtTest import QTest  # noqa: E402 - guard runs first
from PySide6.QtWidgets import QApplication, QDialog, QWidget  # noqa: E402 - guard runs first

from md_converter.gui.main_window import (  # noqa: E402 - guard runs first
    ABOUT_TEXT,
    CHANGE_OUTPUT_ACCESSIBLE_NAME,
    DROP_ZONE_ACCESSIBLE_DESCRIPTION,
    DROP_ZONE_ACCESSIBLE_NAME,
    MINIMUM_HEIGHT,
    MINIMUM_WIDTH,
    SELECT_FILE_TEXT,
    SETTINGS_TEXT,
    SHORTCUT_SELECT_FILE,
    SHORTCUT_SETTINGS,
    STATUS_ACCESSIBLE_NAME,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from md_converter.gui.state import STATE_EFFECTS, GuiState  # noqa: E402 - guard runs first

PROJECT_ROOT = Path(__file__).resolve().parents[3]
GUI_DIR = PROJECT_ROOT / "md_converter" / "gui"
MAIN_WINDOW_MODULE = GUI_DIR / "main_window.py"
APP_MODULE = GUI_DIR / "app.py"

_SENTINEL = "HIDPI_SMOKE="

#: Controls that must carry an accessible name (WP-P12-07-05 baseline).
ACCESSIBLE_CONTROLS = (
    "dropZone",
    "dropLabel",
    "selectFileButton",
    "outputValueLabel",
    "changeOutputButton",
    "convertButton",
    "statusLabel",
    "detailsButton",
    "openDocumentButton",
    "openFolderButton",
    "settingsButton",
    "aboutButton",
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
    """Deliver pending Qt events."""
    QApplication.instance().processEvents()


def _markdown(tmp_path: Path, name: str = "notes.md") -> Path:
    """Write a minimal Markdown source and return its path."""
    path = tmp_path / name
    path.write_text("# Notes\n\nBody text.\n", encoding="utf-8")
    return path


def _run_python(code: str, env_overrides: dict) -> subprocess.CompletedProcess:
    """Run ``code`` in a fresh interpreter of the active virtual environment."""
    return subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        env={**os.environ, "QT_QPA_PLATFORM": "offscreen", **env_overrides},
        timeout=240,
    )


def _wait_for_idle(window: "MainWindow", timeout: float = 30.0) -> None:
    """Process events until the window's worker is idle."""
    deadline = time.monotonic() + timeout
    while window.worker.is_running and time.monotonic() < deadline:
        _pump()
        time.sleep(0.005)


# ============================================================
# Keyboard and focus
# ============================================================


def test_tab_order_follows_the_workflow(window: "MainWindow", tmp_path: Path) -> None:
    """WP §Keyboard/Focus: logical Tab order through the visible controls.

    A source is selected first so Convert is enabled: a disabled control is
    correctly skipped by Tab, which is the accepted state-model behaviour.
    """
    assert window.set_source_file(str(_markdown(tmp_path))) is GuiState.READY
    window.show()
    _pump()

    expected = [
        window.select_file_button,
        window.change_output_button,
        window.convert_button,
        window.settings_button,
        window.about_button,
    ]
    window.select_file_button.setFocus()
    _pump()
    assert QApplication.focusWidget() is expected[0]

    for following in expected[1:]:
        QTest.keyClick(QApplication.focusWidget(), Qt.Key.Key_Tab)
        _pump()
        assert QApplication.focusWidget() is following


def test_hidden_result_actions_are_skipped_by_tab(window: "MainWindow") -> None:
    """A Tab stop never lands on a hidden action."""
    assert window.details_button.isVisible() is False
    assert window.open_document_button.isVisible() is False
    assert window.open_folder_button.isVisible() is False


def test_enter_activates_the_primary_action(window: "MainWindow", tmp_path: Path) -> None:
    """WP §Keyboard/Focus: standard Enter activation of Convert."""
    assert window.set_source_file(str(_markdown(tmp_path))) is GuiState.READY
    window.show()
    _pump()
    window.convert_button.setFocus()

    with mock.patch.object(window, "start_conversion") as started:
        started.return_value = GuiState.CONVERTING
        QTest.keyClick(window.convert_button, Qt.Key.Key_Return)
        _pump()

    assert started.called


def test_space_activates_a_checkbox() -> None:
    """WP §Keyboard/Focus: standard Space behaviour in a dialog control."""
    from md_converter.gui.app import create_application
    from md_converter.gui.preferences import GuiPreferences
    from md_converter.gui.settings_dialog import SettingsDialog

    create_application([])
    dialog = SettingsDialog(GuiPreferences.session())
    try:
        dialog.remember_folders_checkbox.setFocus()
        before = dialog.remember_folders_checkbox.isChecked()
        QTest.keyClick(dialog.remember_folders_checkbox, Qt.Key.Key_Space)
        assert dialog.remember_folders_checkbox.isChecked() is not before
    finally:
        dialog.close()


def test_standard_shortcuts_are_installed(window: "MainWindow") -> None:
    """WP §Keyboard/Focus: two bounded, standard shortcuts."""
    assert window.select_file_action.shortcut() == QKeySequence(SHORTCUT_SELECT_FILE)
    assert window.settings_action.shortcut() == QKeySequence(SHORTCUT_SETTINGS)
    assert SHORTCUT_SELECT_FILE == "Ctrl+O"
    assert SHORTCUT_SETTINGS == "Ctrl+,"


def test_shortcut_opens_the_picker_through_the_existing_action(
    window: "MainWindow",
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``Ctrl+O`` reuses the existing Select File action."""
    import importlib

    module = importlib.import_module("md_converter.gui.main_window")
    calls: List[object] = []
    monkeypatch.setattr(
        module.file_picker,
        "ask_for_markdown_sources",
        lambda parent, directory=None: calls.append(directory) or (),
    )

    window.select_file_action.trigger()

    assert len(calls) == 1
    assert window.state is GuiState.EMPTY


def test_no_configurable_shortcut_system(window: "MainWindow") -> None:
    """WP §Keyboard/Focus: no shortcut configuration surface exists."""
    actions = window.actions()

    assert len(actions) == 2
    assert {action.objectName() for action in actions} == {"selectFileAction", "settingsAction"}


# ============================================================
# Accessibility baseline
# ============================================================


def test_important_controls_have_accessible_names(window: "MainWindow") -> None:
    """WP §Accessibility: meaningful accessible names."""
    for object_name in ACCESSIBLE_CONTROLS:
        widget = window.findChild(QWidget, object_name)
        assert widget is not None, object_name
        assert widget.accessibleName().strip(), object_name


def test_accessible_names_match_the_visible_wording(window: "MainWindow") -> None:
    """The accessible identity is understandable, not technical."""
    assert window.select_file_button.accessibleName() == SELECT_FILE_TEXT
    assert window.change_output_button.accessibleName() == CHANGE_OUTPUT_ACCESSIBLE_NAME
    assert window.status_label.accessibleName() == STATUS_ACCESSIBLE_NAME
    assert window.settings_button.accessibleName() == SETTINGS_TEXT
    assert window.about_button.accessibleName() == ABOUT_TEXT
    assert window.drop_zone.accessibleName() == DROP_ZONE_ACCESSIBLE_NAME
    assert window.drop_zone.accessibleDescription() == DROP_ZONE_ACCESSIBLE_DESCRIPTION


def test_status_is_never_conveyed_by_color_alone() -> None:
    """WP §Accessibility: every outcome carries explicit wording."""
    texts = [STATE_EFFECTS[state].status_text for state in GuiState]

    assert all(text.strip() for text in texts)
    assert len(set(texts)) == len(texts)
    assert "Converting" in STATE_EFFECTS[GuiState.CONVERTING].status_text
    assert "warnings" in STATE_EFFECTS[GuiState.SUCCESS_WITH_WARNING].status_text
    assert "failed" in STATE_EFFECTS[GuiState.FAILED].status_text.lower()


def test_gui_does_not_style_by_color() -> None:
    """No colour-only signal: the GUI sets no stylesheet or palette."""
    source = MAIN_WINDOW_MODULE.read_text(encoding="utf-8")

    for styling in ("setStyleSheet", "QPalette", "setPalette", "QColor", "setForeground"):
        assert styling not in source, styling


def test_result_summary_is_textual(window: "MainWindow", tmp_path: Path) -> None:
    """A presented warning is readable as text, not implied by a colour."""
    from md_converter.application.conversion_result import (
        ConversionResult,
        ConversionStatus,
    )
    from md_converter.application.diagnostics_adapter import ApplicationDiagnostic

    record = ApplicationDiagnostic(
        severity="WARNING",
        code="QA_STATIC_WARN",
        message="QA_STATIC_WARN technical message",
        user_message="A heading style was adjusted.",
    )
    result = ConversionResult(
        status=ConversionStatus.SUCCESS_WITH_WARNING,
        warnings=(record,),
        diagnostics=(record,),
    )

    assert window.set_source_file(str(_markdown(tmp_path))) is GuiState.READY
    window.request_convert()
    window._on_conversion_result(result)
    window.show()
    _pump()

    assert window.result_area.isVisible() is True
    assert window.result_summary_label.text().strip()


def test_report_surface_is_keyboard_accessible() -> None:
    """WP §Accessibility: the read-only report is reachable and closable."""
    from md_converter.application.conversion_result import (
        ConversionErrorCategory,
        ConversionResult,
        ConversionStatus,
    )
    from md_converter.gui.app import create_application
    from md_converter.gui.presentation_model import present_result
    from md_converter.gui.result_details import (
        CLOSE_TEXT,
        COPY_TEXT,
        EVIDENCE_ACCESSIBLE_NAME,
        SUMMARY_ACCESSIBLE_NAME,
        ResultDetailsDialog,
        build_report_text,
    )

    create_application([])
    result = ConversionResult(
        status=ConversionStatus.FAILED,
        error_category=ConversionErrorCategory.CONVERSION_ERROR,
        error_message="The document could not be generated.",
    )
    presentation = present_result(result)
    dialog = ResultDetailsDialog(presentation, build_report_text(presentation, result))
    try:
        assert dialog.evidence_view.accessibleName() == EVIDENCE_ACCESSIBLE_NAME
        assert dialog.summary_label.accessibleName() == SUMMARY_ACCESSIBLE_NAME
        assert dialog.copy_button.accessibleName() == COPY_TEXT
        assert dialog.close_button.accessibleName() == CLOSE_TEXT
        assert dialog.evidence_view.focusPolicy() & Qt.FocusPolicy.TabFocus

        QTest.keyClick(dialog, Qt.Key.Key_Escape)
        assert dialog.result() == int(QDialog.DialogCode.Rejected)
    finally:
        dialog.close()


def test_dialogs_are_dismissable_with_escape(window: "MainWindow") -> None:
    """WP §Keyboard/Focus: ``Esc`` closes the user-facing dialogs."""
    from md_converter.gui.about_dialog import AboutDialog
    from md_converter.gui.settings_dialog import SettingsDialog

    for dialog in (SettingsDialog(window.preferences, window), AboutDialog(window)):
        try:
            QTest.keyClick(dialog, Qt.Key.Key_Escape)
            assert dialog.result() == int(QDialog.DialogCode.Rejected)
        finally:
            dialog.close()


# ============================================================
# Window behaviour
# ============================================================


def test_minimum_size_is_sane(window: "MainWindow") -> None:
    """WP §Window Behavior: a sane minimum size that still fits the layout."""
    assert (window.minimumWidth(), window.minimumHeight()) == (MINIMUM_WIDTH, MINIMUM_HEIGHT)
    assert MINIMUM_WIDTH < WINDOW_WIDTH and MINIMUM_HEIGHT < WINDOW_HEIGHT
    assert MINIMUM_WIDTH >= 600 and MINIMUM_HEIGHT >= 400

    window.show()
    _pump()
    window.resize(200, 150)
    _pump()
    assert window.width() >= MINIMUM_WIDTH
    assert window.height() >= MINIMUM_HEIGHT


def test_invalid_stored_geometry_fails_safe(tmp_path: Path) -> None:
    """WP §Window Behavior: an unreadable geometry falls back to the default."""
    from md_converter.gui.app import create_application
    from md_converter.gui.main_window import MainWindow
    from md_converter.gui.preferences import GuiPreferences

    create_application([])
    prefs = GuiPreferences.for_file(tmp_path / "prefs.ini")
    prefs.set_window_geometry(QByteArray(b"this is not a geometry"))

    instance = MainWindow(preferences=prefs)
    try:
        assert (instance.width(), instance.height()) == (WINDOW_WIDTH, WINDOW_HEIGHT)
    finally:
        instance.close()


def test_window_shows_and_closes_normally(window: "MainWindow") -> None:
    """WP §Window Behavior: normal close behaviour is unchanged."""
    window.show()
    _pump()
    assert window.isVisible() is True

    window.close()
    _pump()
    assert window.isVisible() is False


def test_active_worker_still_blocks_an_unsafe_close(
    window: "MainWindow",
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """WP §Window Behavior: the frozen close rule is preserved."""
    import threading

    from md_converter.application.conversion_result import ConversionResult, ConversionStatus

    release = threading.Event()

    def blocking(request) -> ConversionResult:
        release.wait(timeout=30)
        return ConversionResult(status=ConversionStatus.SUCCESS)

    monkeypatch.setattr(window.service, "convert", blocking)
    window.set_source_file(str(_markdown(tmp_path)))
    window.start_conversion()
    window.show()
    _pump()

    try:
        assert window.is_conversion_active is True
        window.close()
        assert window.isVisible() is True
    finally:
        release.set()
        _wait_for_idle(window)

    window.close()
    _pump()
    assert window.isVisible() is False


# ============================================================
# High-DPI
# ============================================================


def test_no_deprecated_high_dpi_attributes_are_set() -> None:
    """WP §High-DPI: Qt 6 scaling defaults are used, not legacy attributes."""
    source = APP_MODULE.read_text(encoding="utf-8")

    for legacy in ("AA_EnableHighDpiScaling", "AA_UseHighDpiPixmaps", "setAttribute"):
        assert legacy not in source, legacy


def test_high_dpi_smoke_keeps_primary_controls_usable() -> None:
    """Bounded High-DPI smoke: the window layout survives scaled rendering."""
    code = "\n".join(
        [
            "import os",
            "os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')",
            "from PySide6.QtWidgets import QWidget",
            "from md_converter.gui.app import create_application",
            "from md_converter.gui.main_window import MainWindow",
            "app = create_application([])",
            "window = MainWindow()",
            "window.show()",
            "app.processEvents()",
            "names = ('dropZone', 'dropLabel', 'selectFileButton', 'outputValueLabel',",
            "         'changeOutputButton', 'convertButton', 'statusLabel',",
            "         'settingsButton', 'aboutButton')",
            "rect = window.rect()",
            "inside = True",
            "for name in names:",
            "    widget = window.findChild(QWidget, name)",
            "    assert widget is not None, name",
            "    assert widget.isVisible(), name",
            "    top_left = widget.mapTo(window, widget.rect().topLeft())",
            "    bottom_right = widget.mapTo(window, widget.rect().bottomRight())",
            "    if not (rect.contains(top_left) and rect.contains(bottom_right)):",
            "        inside = False",
            "ratio = app.primaryScreen().devicePixelRatio()",
            "window.close()",
            "print('" + _SENTINEL + "%s,%s' % (inside, ratio))",
        ]
    )

    proc = _run_python(code, {"QT_SCALE_FACTOR": "2"})

    assert proc.returncode == 0, proc.stderr
    lines = [line for line in proc.stdout.splitlines() if line.startswith(_SENTINEL)]
    assert len(lines) == 1, proc.stdout
    inside, ratio = lines[0][len(_SENTINEL) :].split(",")
    assert inside == "True", proc.stdout
    assert float(ratio) >= 1.0, proc.stdout
