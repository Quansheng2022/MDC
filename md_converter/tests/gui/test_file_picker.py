"""Focused verification for Markdown file selection (WP-P12-04-04 §9).

Three layers are verified:

* GUI-boundary validation of a selected path;
* the standard-dialog seam (filter, title, cancel handling);
* the window binding - clicking Select File moves EMPTY -> READY through the
  shared state model, displays the source, and never starts conversion.

The dialog itself is replaced through the ``file_picker`` module seam, so no
native dialog is ever opened during tests.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Optional

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


def _write_markdown(path: Path, body: str = "# Notes\n\nBody text.\n") -> Path:
    """Write ``body`` as UTF-8 Markdown and return the path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _patch_dialog(monkeypatch: pytest.MonkeyPatch, result: Optional[str]) -> None:
    """Point the picker dialog at a fixed result."""
    monkeypatch.setattr(file_picker, "ask_for_markdown_source", lambda *args, **kwargs: result)


# ============================================================
# GUI-boundary validation
# ============================================================


def test_valid_markdown_path_is_accepted(tmp_path: Path) -> None:
    """A present ``.md`` file is a selectable source."""
    markdown = _write_markdown(tmp_path / "notes.md")

    assert file_picker.validate_markdown_source(markdown) == markdown
    assert file_picker.validate_markdown_source(str(markdown)) == markdown


def test_missing_path_is_rejected(tmp_path: Path) -> None:
    """A missing path must not enter READY (WP §6)."""
    assert file_picker.validate_markdown_source(tmp_path / "missing.md") is None


def test_directory_is_rejected(tmp_path: Path) -> None:
    """A directory is not a Markdown file."""
    directory = tmp_path / "docs"
    directory.mkdir()

    assert file_picker.validate_markdown_source(directory) is None


@pytest.mark.parametrize("name", ["notes.txt", "notes.markdown", "notes.mdown", "notes"])
def test_unsupported_extension_is_rejected(tmp_path: Path, name: str) -> None:
    """Only the supported Markdown extension is accepted (WP §4)."""
    path = _write_markdown(tmp_path / name)

    assert file_picker.validate_markdown_source(path) is None


def test_extension_match_is_case_insensitive(tmp_path: Path) -> None:
    """``.MD`` is the same supported extension on Windows."""
    path = _write_markdown(tmp_path / "NOTES.MD")

    assert file_picker.validate_markdown_source(path) == path


@pytest.mark.parametrize("value", [None, "", "   "])
def test_blank_candidate_is_rejected(value: Optional[str]) -> None:
    """An empty selection is not a source."""
    assert file_picker.validate_markdown_source(value) is None


def test_picker_contract_covers_markdown_only() -> None:
    """No additional source format is introduced (WP §4/§11)."""
    assert file_picker.MARKDOWN_EXTENSIONS == (".md",)
    assert "*.md" in file_picker.MARKDOWN_FILTER


# ============================================================
# Standard dialog seam
# ============================================================


def test_dialog_uses_markdown_filter(monkeypatch: pytest.MonkeyPatch) -> None:
    """The dialog is opened with the Markdown filter and product caption."""
    captured = {}

    def fake_open(parent, title, directory, file_filter):
        captured.update(parent=parent, title=title, directory=directory, file_filter=file_filter)
        return "/tmp/notes.md"

    monkeypatch.setattr(file_picker, "_open_dialog", fake_open)

    selected = file_picker.ask_for_markdown_source(None, directory="C:/docs")

    assert selected == "/tmp/notes.md"
    assert captured["file_filter"] == file_picker.MARKDOWN_FILTER
    assert captured["title"] == file_picker.DIALOG_TITLE
    assert captured["directory"] == "C:/docs"


def test_dialog_defaults_to_home_directory(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without an explicit directory the dialog starts in the user's home."""
    captured = {}

    def fake_open(parent, title, directory, file_filter):
        captured["directory"] = directory
        return ""

    monkeypatch.setattr(file_picker, "_open_dialog", fake_open)

    assert file_picker.ask_for_markdown_source() is None
    assert captured["directory"] == str(Path.home())


def test_cancelled_dialog_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """Cancel is not an error (WP §5)."""
    monkeypatch.setattr(file_picker, "_open_dialog", lambda *args, **kwargs: "")

    assert file_picker.ask_for_markdown_source() is None


# ============================================================
# Window binding
# ============================================================


def test_select_valid_file_enters_ready(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Selecting a valid file moves EMPTY -> READY without starting conversion."""
    markdown = _write_markdown(tmp_path / "notes.md")
    _patch_dialog(monkeypatch, str(markdown))
    window = _make_window()
    try:
        window.show()
        _process_events()

        window.select_file_button.click()
        _process_events()

        assert window.state is GuiState.READY
        assert window.state_model.source == str(markdown)
        assert window.convert_button.isEnabled() is True
        assert window.source_label.text() == "notes.md"
        assert window.source_label.isVisible() is True
        assert window.source_label.toolTip() == str(markdown)
        assert window.source_path_label.isVisible() is True
        assert window.source_path_label.toolTip() == str(markdown)
        assert window.status_label.text() == STATE_EFFECTS[GuiState.READY].status_text
    finally:
        window.close()


def test_cancel_keeps_empty_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """Cancelling from EMPTY changes nothing and raises nothing."""
    _patch_dialog(monkeypatch, None)
    window = _make_window()
    try:
        window.select_file_button.click()
        _process_events()

        assert window.state is GuiState.EMPTY
        assert window.convert_button.isEnabled() is False
        assert window.source_label.text() == ""
        assert window.status_label.text() == STATE_EFFECTS[GuiState.EMPTY].status_text
    finally:
        window.close()


def test_cancel_preserves_existing_selection(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Cancelling keeps the current valid selection (WP §5)."""
    markdown = _write_markdown(tmp_path / "notes.md")
    _patch_dialog(monkeypatch, str(markdown))
    window = _make_window()
    try:
        window.select_file_button.click()
        assert window.state is GuiState.READY

        _patch_dialog(monkeypatch, None)
        window.select_file_button.click()

        assert window.state is GuiState.READY
        assert window.source_label.text() == "notes.md"
        assert window.state_model.source == str(markdown)
    finally:
        window.close()


def test_invalid_selection_does_not_enter_ready(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A missing, non-file or unsupported selection is rejected (WP §6)."""
    _patch_dialog(monkeypatch, str(tmp_path / "missing.md"))
    window = _make_window()
    try:
        window.select_file_button.click()
        _process_events()

        assert window.state is GuiState.EMPTY
        assert window.convert_button.isEnabled() is False
        assert window.source_label.text() == ""

        directory = tmp_path / "docs"
        directory.mkdir()
        _patch_dialog(monkeypatch, str(directory))
        window.select_file_button.click()
        assert window.state is GuiState.EMPTY

        text_file = _write_markdown(tmp_path / "notes.txt")
        _patch_dialog(monkeypatch, str(text_file))
        window.select_file_button.click()
        assert window.state is GuiState.EMPTY
        assert window.convert_button.isEnabled() is False
    finally:
        window.close()


def test_reselect_updates_source(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Selecting another valid file replaces the displayed source."""
    first = _write_markdown(tmp_path / "first.md")
    second = _write_markdown(tmp_path / "second.md")
    window = _make_window()
    try:
        _patch_dialog(monkeypatch, str(first))
        window.select_file_button.click()
        assert window.source_label.text() == "first.md"

        _patch_dialog(monkeypatch, str(second))
        window.select_file_button.click()

        assert window.state is GuiState.READY
        assert window.source_label.text() == "second.md"
        assert window.state_model.source == str(second)
    finally:
        window.close()


def test_long_folder_is_elided_but_path_is_kept(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """WP §7: long folders are shortened for display, the full path is retained."""
    from md_converter.gui.main_window import SOURCE_PATH_MAX_CHARS

    markdown = _write_markdown(tmp_path / ("d" * 40) / ("e" * 40) / "notes.md")
    _patch_dialog(monkeypatch, str(markdown))
    window = _make_window()
    try:
        window.select_file_button.click()

        folder_text = window.source_path_label.text()
        assert window.source_label.text() == "notes.md"
        assert "\u2026" in folder_text
        assert len(folder_text) <= SOURCE_PATH_MAX_CHARS
        assert window.source_path_label.toolTip() == str(markdown)
        assert window.state_model.source == str(markdown)
    finally:
        window.close()


def test_selection_is_ignored_while_converting(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Select File is unavailable during CONVERTING: no dialog, no source change."""
    calls = []
    monkeypatch.setattr(
        file_picker,
        "ask_for_markdown_source",
        lambda *args, **kwargs: calls.append(1),
    )
    window = _make_window()
    try:
        window.set_source("notes.md")
        window.request_convert()
        assert window.select_file_button.isEnabled() is False

        window.select_file_button.click()

        assert calls == []
        assert window.state is GuiState.CONVERTING
        assert window.source_label.text() == "notes.md"
    finally:
        window.close()
