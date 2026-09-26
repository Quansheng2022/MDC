"""Focused verification for output-folder selection (WP-P12-04-06 §9/V6).

The output folder is a *session preference*: the GUI stores the chosen
directory, displays it, and nothing more.  No DOCX file name is derived here -
that stays with the approved application/service behavior (WP §5).

The module also walks the complete mock P12-04 workflow
(EMPTY -> READY -> optional output folder -> CONVERTING -> simulated outcome)
for both source entry points (file picker and drag & drop).
"""

from __future__ import annotations

import ast
import os
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Optional, Tuple

import pytest

if TYPE_CHECKING:  # pragma: no cover - typing only
    from md_converter.gui.main_window import MainWindow

pytest.importorskip("PySide6", reason="PySide6 (GUI dev dependency) is not installed")

#: Qt needs a platform plugin even when a test only constructs widgets.  Set
#: here (not in a directory ``conftest.py``) because the test tree is not a
#: package and a second ``conftest`` would shadow ``md_converter/tests/conftest.py``.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from md_converter.gui import file_picker  # noqa: E402 - the Qt guard must run first
from md_converter.gui.state import STATE_EFFECTS, GuiState  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[3]
GUI_DIR = PROJECT_ROOT / "md_converter" / "gui"

#: Simulated completion -> (window hook, expected state).
_COMPLETIONS: Dict[GuiState, Tuple[str, GuiState]] = {
    GuiState.SUCCESS: ("simulate_success", GuiState.SUCCESS),
    GuiState.SUCCESS_WITH_WARNING: ("simulate_warning", GuiState.SUCCESS_WITH_WARNING),
    GuiState.FAILED: ("simulate_failure", GuiState.FAILED),
}


def _make_window() -> "MainWindow":
    """Return a fresh ``MainWindow``, ensuring a QApplication exists."""
    from md_converter.gui.app import create_application
    from md_converter.gui.main_window import MainWindow

    create_application([])
    return MainWindow()


def _process_events() -> None:
    """Deliver pending Qt events (layout/visibility) without entering the loop."""
    from PySide6.QtWidgets import QApplication

    QApplication.instance().processEvents()


def _write_markdown(path: Path) -> Path:
    """Write a small Markdown file and return its path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# Notes\n\nBody text.\n", encoding="utf-8")
    return path


def _patch_file_dialog(monkeypatch: pytest.MonkeyPatch, result: Optional[str]) -> None:
    """Point the Markdown file dialog at a fixed result."""
    monkeypatch.setattr(file_picker, "ask_for_markdown_source", lambda *a, **k: result)


def _patch_directory_dialog(monkeypatch: pytest.MonkeyPatch, result: Optional[str]) -> None:
    """Point the output-folder dialog at a fixed result."""
    monkeypatch.setattr(file_picker, "ask_for_output_directory", lambda *a, **k: result)


def _drop(zone, paths) -> bool:
    """Send a real Qt drop event carrying ``paths``; return the accept result."""
    from PySide6.QtCore import QMimeData, QPointF, Qt, QUrl
    from PySide6.QtGui import QDropEvent

    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(path)) for path in paths])
    event = QDropEvent(
        QPointF(10.0, 10.0),
        Qt.DropAction.CopyAction,
        mime,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    zone.dropEvent(event)
    return bool(event.isAccepted())


# ============================================================
# GUI-boundary validation
# ============================================================


def test_existing_directory_is_accepted(tmp_path: Path) -> None:
    """A present directory is a usable output choice."""
    directory = tmp_path / "out"
    directory.mkdir()

    assert file_picker.validate_output_directory(directory) == directory
    assert file_picker.validate_output_directory(str(directory)) == directory


def test_missing_directory_is_rejected(tmp_path: Path) -> None:
    """A missing folder must not create an undefined preference."""
    assert file_picker.validate_output_directory(tmp_path / "missing") is None


def test_file_is_not_an_output_directory(tmp_path: Path) -> None:
    """A file is not a folder choice."""
    markdown = _write_markdown(tmp_path / "notes.md")

    assert file_picker.validate_output_directory(markdown) is None


@pytest.mark.parametrize("value", [None, "", "   "])
def test_blank_directory_is_rejected(value: Optional[str]) -> None:
    """An empty selection is not a folder choice."""
    assert file_picker.validate_output_directory(value) is None


# ============================================================
# Directory dialog seam
# ============================================================


def test_directory_dialog_uses_caption_and_start_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The chooser is opened with the product caption and current folder."""
    captured = {}

    def fake_open(parent, title, directory):
        captured.update(parent=parent, title=title, directory=directory)
        return str(tmp_path)

    monkeypatch.setattr(file_picker, "_open_directory_dialog", fake_open)

    selected = file_picker.ask_for_output_directory(None, directory=tmp_path)

    assert selected == str(tmp_path)
    assert captured["title"] == file_picker.DIRECTORY_DIALOG_TITLE
    assert captured["directory"] == str(tmp_path)


def test_directory_dialog_defaults_to_home(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without a current choice the chooser starts in the user's home."""
    captured = {}

    def fake_open(parent, title, directory):
        captured["directory"] = directory
        return ""

    monkeypatch.setattr(file_picker, "_open_directory_dialog", fake_open)

    assert file_picker.ask_for_output_directory() is None
    assert captured["directory"] == str(Path.home())


def test_cancelled_directory_dialog_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """Cancel is not an error (WP §7)."""
    monkeypatch.setattr(file_picker, "_open_directory_dialog", lambda *a, **k: "")

    assert file_picker.ask_for_output_directory() is None


# ============================================================
# Window behavior
# ============================================================


def test_default_presentation_is_default_location() -> None:
    """WP-P12-05-03: the default presentation is "Default location"."""
    from md_converter.gui.main_window import OUTPUT_VALUE_TEXT

    window = _make_window()
    try:
        assert OUTPUT_VALUE_TEXT == "Default location"
        assert window.output_directory is None
        assert window.output_value_label.text() == OUTPUT_VALUE_TEXT
        assert window.output_value_label.toolTip() == ""
        assert window.change_output_button.isEnabled() is True
    finally:
        window.close()


def test_change_uses_chooser_and_displays_selection(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """WP §7: Change opens the chooser and the folder is displayed."""
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    _patch_directory_dialog(monkeypatch, str(output_dir))
    window = _make_window()
    try:
        window.change_output_button.click()
        _process_events()

        assert window.output_directory == output_dir
        assert str(output_dir) in window.output_value_label.toolTip()
        assert window.output_value_label.text() != ""
        assert window.state is GuiState.EMPTY
    finally:
        window.close()


def test_long_output_folder_is_elided(tmp_path: Path) -> None:
    """WP §7: long folders are shortened for display, full path kept in tooltip."""
    from md_converter.gui.main_window import OUTPUT_PATH_MAX_CHARS

    output_dir = tmp_path / ("o" * 40) / ("u" * 40)
    output_dir.mkdir(parents=True)
    window = _make_window()
    try:
        window.set_output_directory(output_dir)

        assert "\u2026" in window.output_value_label.text()
        assert len(window.output_value_label.text()) <= OUTPUT_PATH_MAX_CHARS
        assert window.output_value_label.toolTip() == str(output_dir)
        assert window.output_directory == output_dir
    finally:
        window.close()


def test_cancel_preserves_previous_output_choice(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """WP §7: cancelling keeps the current choice."""
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    _patch_directory_dialog(monkeypatch, str(output_dir))
    window = _make_window()
    try:
        window.change_output_button.click()
        assert window.output_directory == output_dir

        _patch_directory_dialog(monkeypatch, None)
        window.change_output_button.click()

        assert window.output_directory == output_dir

        # ... and cancelling from the default also keeps "Default location".
        fresh = _make_window()
        try:
            _patch_directory_dialog(monkeypatch, None)
            fresh.change_output_button.click()
            assert fresh.output_directory is None
        finally:
            fresh.close()
    finally:
        window.close()


def test_invalid_output_selection_is_ignored(tmp_path: Path) -> None:
    """WP §7: a missing/non-folder selection does not create undefined state."""
    markdown = _write_markdown(tmp_path / "notes.md")
    window = _make_window()
    try:
        assert window.set_output_directory(tmp_path / "missing") is None
        assert window.set_output_directory(markdown) is None
        assert window.set_output_directory("") is None
        assert window.output_directory is None
    finally:
        window.close()


def test_output_change_is_disabled_while_converting(tmp_path: Path) -> None:
    """Input changes are restricted during CONVERTING (state effect)."""
    markdown = _write_markdown(tmp_path / "notes.md")
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    window = _make_window()
    try:
        window.set_source(str(markdown))
        window.set_output_directory(output_dir)
        assert window.change_output_button.isEnabled() is True

        window.request_convert()
        assert window.change_output_button.isEnabled() is False

        window.simulate_success()
        assert window.change_output_button.isEnabled() is True
        assert window.output_directory == output_dir
    finally:
        window.close()


def test_state_effects_cover_output_change() -> None:
    """The output control is driven by the shared effect table (WP §7)."""
    for state, effect in STATE_EFFECTS.items():
        assert isinstance(effect.change_output_enabled, bool), state
    assert STATE_EFFECTS[GuiState.CONVERTING].change_output_enabled is False
    assert STATE_EFFECTS[GuiState.EMPTY].change_output_enabled is True
    assert STATE_EFFECTS[GuiState.READY].change_output_enabled is True


# ============================================================
# Complete mock workflow (WP §8)
# ============================================================


@pytest.mark.parametrize("entry", ["picker", "drop"])
@pytest.mark.parametrize("completion", list(_COMPLETIONS))
def test_mock_gui_workflow(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    entry: str,
    completion: GuiState,
) -> None:
    """Launch -> EMPTY -> READY -> output folder -> CONVERTING -> outcome."""
    markdown = _write_markdown(tmp_path / "notes.md")
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    window = _make_window()
    try:
        window.show()
        _process_events()

        # Launch: EMPTY, Convert unavailable.
        assert window.state is GuiState.EMPTY
        assert window.convert_button.isEnabled() is False

        # Select (picker) or drop a Markdown file -> READY.
        if entry == "picker":
            _patch_file_dialog(monkeypatch, str(markdown))
            window.select_file_button.click()
        else:
            assert _drop(window.drop_zone, [markdown]) is True
        assert window.state is GuiState.READY
        assert window.convert_button.isEnabled() is True
        assert window.source_label.text() == "notes.md"

        # Optionally choose an output folder (session preference only).
        _patch_directory_dialog(monkeypatch, str(output_dir))
        window.change_output_button.click()
        assert window.output_directory == output_dir

        # Convert -> CONVERTING (no real conversion happens).
        assert window.request_convert() is GuiState.CONVERTING
        assert window.convert_button.isEnabled() is False
        assert window.output_directory == output_dir

        # Simulated completion.
        hook, expected = _COMPLETIONS[completion]
        assert getattr(window, hook)() is expected
        assert window.convert_button.isEnabled() is False
        assert window.output_directory == output_dir

        window.close()
        _process_events()
        assert window.isVisible() is False
    finally:
        window.close()


# ============================================================
# Architecture guard
# ============================================================


def test_gui_has_no_docx_naming_or_frontmatter_logic() -> None:
    """WP §5/§12: the GUI never invents DOCX naming or frontmatter behaviour."""
    forbidden_names = {"sanitize_output_title", "parse_frontmatter"}

    modules = sorted(GUI_DIR.glob("*.py"))
    assert modules
    for module in modules:
        tree = ast.parse(module.read_text(encoding="utf-8"))
        strings = [
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        ]
        assert not [text for text in strings if ".docx" in text.lower()], module.name

        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        names |= {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        assert not names & forbidden_names, module.name
