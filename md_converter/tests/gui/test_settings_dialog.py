"""Focused verification for the Settings surface (WP-P12-07-02).

The Settings dialog must stay small, bounded and side-effect free:

* it loads the stored GUI preferences into temporary controls;
* Save persists, Cancel discards, Reset to Defaults restores the defaults;
* nothing is written before Save, so Cancel (and ``Esc``) really discard;
* it offers no conversion, QA, naming, diagnostics or account setting;
* it never triggers a conversion and never calls the Core.
"""

from __future__ import annotations

import ast
import os
from pathlib import Path
from typing import TYPE_CHECKING, Iterator, List, Set

import pytest

if TYPE_CHECKING:  # pragma: no cover - typing only
    from md_converter.gui.main_window import MainWindow

pytest.importorskip("PySide6", reason="PySide6 (GUI dev dependency) is not installed")

#: Qt needs a platform plugin even when a test only constructs widgets.  Set
#: here (not in a directory ``conftest.py``) because the test tree is not a
#: package and a second ``conftest`` would shadow ``md_converter/tests/conftest.py``.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QByteArray, QSettings, Qt  # noqa: E402 - guard runs first
from PySide6.QtWidgets import (  # noqa: E402 - guard runs first
    QCheckBox,
    QComboBox,
    QDialog,
    QLineEdit,
    QPlainTextEdit,
    QSpinBox,
    QStackedWidget,
    QTabWidget,
    QTextEdit,
)

from md_converter.gui.preferences import (  # noqa: E402 - guard runs first
    DEFAULT_REMEMBER_FOLDERS,
    GEOMETRY_KEY,
    LAST_SOURCE_DIRECTORY_KEY,
    GuiPreferences,
)
from md_converter.gui.settings_dialog import (  # noqa: E402 - guard runs first
    NOT_REMEMBERED_TEXT,
    SettingsDialog,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
GUI_DIR = PROJECT_ROOT / "md_converter" / "gui"
MAIN_WINDOW_MODULE = "md_converter.gui.main_window"

#: Conversion-core modules the GUI layer must never import (WP-P12-05-03 §5).
FORBIDDEN_IMPORT_PREFIXES = (
    "md_converter.compiler",
    "md_converter.diagnostics",
    "md_converter.parser",
    "md_converter.pipeline",
    "md_converter.renderer",
    "md_converter.services",
    "md_converter.quality_gate",
)


def _store(tmp_path: Path) -> GuiPreferences:
    """Return one isolated file-backed preference store."""
    return GuiPreferences.for_file(tmp_path / "gui_preferences.ini")


def _dialog(prefs: GuiPreferences) -> SettingsDialog:
    """Return a dialog over ``prefs`` with a QApplication guaranteed."""
    from md_converter.gui.app import create_application

    create_application([])
    return SettingsDialog(prefs)


def _stored(tmp_path: Path, key: str) -> object:
    """Return the raw stored value of ``key`` in the isolated store."""
    settings = QSettings(str(tmp_path / "gui_preferences.ini"), QSettings.Format.IniFormat)
    settings.sync()
    return settings.value(key, None)


def _imported_modules(path: Path) -> Set[str]:
    """Return the import targets of ``path``, resolving relative imports."""
    package_parts = list(path.resolve().relative_to(PROJECT_ROOT).with_suffix("").parts)[:-1]
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                keep = len(package_parts) - (node.level - 1)
                base = ".".join(package_parts[:keep]) if keep > 0 else ""
                module = f"{base}.{module}" if module else base
            if module:
                names.add(module)
                names.update(f"{module}.{alias.name}" for alias in node.names)
    return names


def _call_targets(path: Path) -> Set[str]:
    """Return the simple names of every call target in ``path``."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            target = node.func
            if isinstance(target, ast.Name):
                names.add(target.id)
            elif isinstance(target, ast.Attribute):
                names.add(target.attr)
    return names


# ============================================================
# Opening and current values
# ============================================================


def test_dialog_loads_the_current_values(tmp_path: Path) -> None:
    """WP §"Open Settings" + §"current values load"."""
    prefs = _store(tmp_path)
    prefs.set_remember_folders(False)
    dialog = _dialog(prefs)
    try:
        assert dialog.remember_folders is False
        assert dialog.remember_folders_checkbox.isChecked() is False
        assert dialog.remembered_source_value.text() == NOT_REMEMBERED_TEXT
        assert dialog.remembered_output_value.text() == NOT_REMEMBERED_TEXT
    finally:
        dialog.close()


def test_dialog_shows_the_remembered_folders(tmp_path: Path) -> None:
    """Remembered folders are shown as a read-only convenience preview."""
    prefs = _store(tmp_path)
    prefs.remember_source_directory(tmp_path)
    prefs.remember_output_directory(tmp_path)
    dialog = _dialog(prefs)
    try:
        assert dialog.remembered_source_value.text() == str(tmp_path)
        assert dialog.remembered_output_value.text() == str(tmp_path)
    finally:
        dialog.close()


def test_first_launch_shows_the_defaults(tmp_path: Path) -> None:
    """A fresh store opens on the defaults."""
    dialog = _dialog(_store(tmp_path))
    try:
        assert dialog.remember_folders is DEFAULT_REMEMBER_FOLDERS is True
        assert dialog.remembered_source_value.text() == NOT_REMEMBERED_TEXT
    finally:
        dialog.close()


# ============================================================
# Save
# ============================================================


def test_save_persists_the_toggle(tmp_path: Path) -> None:
    """WP §"Save persists"."""
    prefs = _store(tmp_path)
    dialog = _dialog(prefs)
    try:
        dialog.remember_folders_checkbox.setChecked(False)
        dialog.save_button.click()
        assert dialog.result() == int(QDialog.DialogCode.Accepted)
    finally:
        dialog.close()

    assert prefs.remember_folders is False
    assert _store(tmp_path).remember_folders is False


def test_save_keeps_folders_while_remembering_stays_on(tmp_path: Path) -> None:
    """Saving with remembering on keeps the stored folders."""
    prefs = _store(tmp_path)
    prefs.remember_source_directory(tmp_path)
    dialog = _dialog(prefs)
    try:
        dialog.save_button.click()
    finally:
        dialog.close()

    assert prefs.remember_folders is True
    assert prefs.last_source_directory == tmp_path


def test_disabling_remembering_forgets_the_stored_folders(tmp_path: Path) -> None:
    """Turning the convenience off clears the remembered folders on Save."""
    prefs = _store(tmp_path)
    prefs.remember_source_directory(tmp_path)
    dialog = _dialog(prefs)
    try:
        dialog.remember_folders_checkbox.setChecked(False)
        dialog.save_button.click()
    finally:
        dialog.close()

    assert prefs.last_source_directory is None
    assert _stored(tmp_path, LAST_SOURCE_DIRECTORY_KEY) is None


# ============================================================
# Cancel / Escape
# ============================================================


def test_cancel_discards_the_edits(tmp_path: Path) -> None:
    """WP §"Cancel discards"."""
    prefs = _store(tmp_path)
    prefs.set_window_geometry(QByteArray(b"geometry-bytes"))
    dialog = _dialog(prefs)
    try:
        dialog.remember_folders_checkbox.setChecked(False)
        dialog.cancel_button.click()
        assert dialog.result() == int(QDialog.DialogCode.Rejected)
    finally:
        dialog.close()

    assert prefs.remember_folders is True
    assert prefs.window_geometry() == QByteArray(b"geometry-bytes")


def test_escape_discards_the_edits(tmp_path: Path) -> None:
    """``Esc`` closes the dialog without writing anything."""
    from PySide6.QtTest import QTest

    prefs = _store(tmp_path)
    dialog = _dialog(prefs)
    try:
        dialog.remember_folders_checkbox.setChecked(False)
        QTest.keyClick(dialog, Qt.Key.Key_Escape)
        assert dialog.result() == int(QDialog.DialogCode.Rejected)
    finally:
        dialog.close()

    assert prefs.remember_folders is True


# ============================================================
# Reset to defaults
# ============================================================


def test_reset_restores_the_defaults_in_the_form_only(tmp_path: Path) -> None:
    """WP §"Reset to Defaults" - the form changes, the store waits for Save."""
    prefs = _store(tmp_path)
    prefs.set_remember_folders(False)
    prefs.set_window_geometry(QByteArray(b"geometry-bytes"))
    prefs.remember_source_directory(tmp_path)

    dialog = _dialog(prefs)
    try:
        dialog.reset_button.click()
        assert dialog.remember_folders is DEFAULT_REMEMBER_FOLDERS
        assert dialog.reset_requested is True
        assert dialog.remembered_source_value.text() == NOT_REMEMBERED_TEXT
        # Nothing is written until Save.
        assert prefs.remember_folders is False
        assert prefs.window_geometry() == QByteArray(b"geometry-bytes")
    finally:
        dialog.close()


def test_save_after_reset_restores_gui_defaults(tmp_path: Path) -> None:
    """Saving after Reset to Defaults clears the GUI-owned values."""
    prefs = _store(tmp_path)
    prefs.remember_source_directory(tmp_path)
    prefs.set_window_geometry(QByteArray(b"geometry-bytes"))
    dialog = _dialog(prefs)
    try:
        dialog.reset_button.click()
        dialog.save_button.click()
    finally:
        dialog.close()

    assert prefs.remember_folders is DEFAULT_REMEMBER_FOLDERS
    assert prefs.last_source_directory is None
    assert prefs.window_geometry() is None
    assert _stored(tmp_path, GEOMETRY_KEY) is None


def test_reset_followed_by_turning_it_off_saves_the_choice(tmp_path: Path) -> None:
    """The explicit choice made after Reset wins."""
    prefs = _store(tmp_path)
    dialog = _dialog(prefs)
    try:
        dialog.reset_button.click()
        dialog.remember_folders_checkbox.setChecked(False)
        dialog.save_button.click()
    finally:
        dialog.close()

    assert prefs.remember_folders is False


def test_reset_is_cleared_by_reloading(tmp_path: Path) -> None:
    """A reloaded dialog forgets an in-form reset."""
    prefs = _store(tmp_path)
    dialog = _dialog(prefs)
    try:
        dialog.reset_button.click()
        dialog._load_values()
        assert dialog.reset_requested is False
    finally:
        dialog.close()


# ============================================================
# Reopening
# ============================================================


def test_reopening_reflects_the_saved_state(tmp_path: Path) -> None:
    """WP §"reopening reflects state"."""
    prefs = _store(tmp_path)
    first = _dialog(prefs)
    try:
        first.remember_folders_checkbox.setChecked(False)
        first.save_button.click()
    finally:
        first.close()

    second = _dialog(prefs)
    try:
        assert second.remember_folders is False
        assert second.remember_folders_checkbox.isChecked() is False
    finally:
        second.close()


# ============================================================
# Bounded scope
# ============================================================


def test_settings_offers_only_gui_preference_controls(tmp_path: Path) -> None:
    """WP §Forbidden: no conversion/QA/theme/account setting is offered."""
    dialog = _dialog(_store(tmp_path))
    try:
        checkboxes = dialog.findChildren(QCheckBox)
        assert len(checkboxes) == 1
        assert checkboxes[0] is dialog.remember_folders_checkbox

        for forbidden in (QComboBox, QSpinBox, QLineEdit, QTextEdit, QPlainTextEdit):
            assert not dialog.findChildren(forbidden), forbidden.__name__
    finally:
        dialog.close()


def test_settings_stays_a_single_page(tmp_path: Path) -> None:
    """The small setting count does not justify a settings centre."""
    dialog = _dialog(_store(tmp_path))
    try:
        assert not dialog.findChildren(QTabWidget)
        assert not dialog.findChildren(QStackedWidget)
    finally:
        dialog.close()


# ============================================================
# Main window entry point
# ============================================================


@pytest.fixture
def window(tmp_path: Path) -> Iterator["MainWindow"]:
    """Provide a main window over an isolated preference store."""
    from md_converter.gui.app import create_application
    from md_converter.gui.main_window import MainWindow

    create_application([])
    instance = MainWindow(preferences=_store(tmp_path))
    yield instance
    instance.close()


def test_settings_button_opens_the_settings_dialog(
    window: "MainWindow",
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The window offers exactly one Settings entry point."""
    import importlib

    module = importlib.import_module(MAIN_WINDOW_MODULE)
    opened: List[SettingsDialog] = []

    class _RecordingSettingsDialog(SettingsDialog):
        def exec(self) -> int:
            opened.append(self)
            return int(QDialog.DialogCode.Accepted)

    monkeypatch.setattr(module, "SettingsDialog", _RecordingSettingsDialog)
    window.show()

    window.settings_button.click()

    assert len(opened) == 1
    assert opened[0].preferences is window.preferences
    assert opened[0].parent() is window


def test_open_settings_reports_the_dialog_outcome(
    window: "MainWindow",
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``open_settings`` returns whether the user saved."""
    import importlib

    module = importlib.import_module(MAIN_WINDOW_MODULE)
    results = iter([QDialog.DialogCode.Accepted, QDialog.DialogCode.Rejected])

    class _ScriptedSettingsDialog(SettingsDialog):
        def exec(self) -> int:
            return int(next(results))

    monkeypatch.setattr(module, "SettingsDialog", _ScriptedSettingsDialog)

    assert window.open_settings() is True
    assert window.open_settings() is False


def test_settings_never_triggers_a_conversion(
    window: "MainWindow",
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """WP §"no conversion triggered" - Save/Cancel leave the workflow alone."""
    import importlib

    module = importlib.import_module(MAIN_WINDOW_MODULE)

    def _forbidden(request) -> None:
        raise AssertionError("Settings must not trigger a conversion")

    monkeypatch.setattr(window.service, "convert", _forbidden)

    class _SavingSettingsDialog(SettingsDialog):
        def exec(self) -> int:
            self.remember_folders_checkbox.setChecked(not self.remember_folders)
            self.save_button.click()
            return int(self.result())

    monkeypatch.setattr(module, "SettingsDialog", _SavingSettingsDialog)
    window.show()
    state_before = window.state

    window.settings_button.click()

    assert window.state is state_before
    assert window.latest_result is None
    assert window.output_directory is None


# ============================================================
# Boundary
# ============================================================


def test_settings_dialog_imports_no_conversion_core() -> None:
    """The Settings surface imports no compiler/parser/pipeline/renderer/QA."""
    offenders = {
        name
        for name in _imported_modules(GUI_DIR / "settings_dialog.py")
        if name.startswith(FORBIDDEN_IMPORT_PREFIXES)
    }

    assert not offenders, sorted(offenders)


def test_settings_dialog_has_no_process_or_output_side_effects() -> None:
    """The Settings surface never prints, writes files or spawns a process."""
    calls = _call_targets(GUI_DIR / "settings_dialog.py")

    assert "print" not in calls
    assert "open" not in calls
    assert "write_text" not in calls
    assert "Popen" not in calls
    assert "system" not in calls
