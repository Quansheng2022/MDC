"""Focused verification for the batch selection surface (SBC-02).

Covered: the multi-selection surface itself (visibility, order, duplicate-name
context, Remove, Clear), the bounded notice, the Convert wording, the mutation
lock during ``CONVERTING`` and the accessibility baseline of the new controls.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, List

import pytest

if TYPE_CHECKING:  # pragma: no cover - typing only
    from md_converter.gui.main_window import MainWindow

pytest.importorskip("PySide6", reason="PySide6 (GUI dev dependency) is not installed")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402 - the Qt guard must run first

from md_converter.gui.main_window import (  # noqa: E402 - the Qt guard must run first
    BATCH_CAPTION_TEXT,
    BATCH_CLEAR_TEXT,
    BATCH_LIST_ACCESSIBLE_NAME,
    BATCH_REMOVE_TEXT,
    CONVERT_MANY_TEMPLATE,
    CONVERT_TEXT,
    OPEN_BATCH_FOLDER_TEXT,
    VIEW_BATCH_REPORT_TEXT,
)
from md_converter.gui.state import GuiState  # noqa: E402 - the Qt guard must run first


def _make_window() -> "MainWindow":
    """Return a fresh ``MainWindow``, ensuring a QApplication exists."""
    from md_converter.gui.app import create_application
    from md_converter.gui.main_window import MainWindow

    create_application([])
    return MainWindow()


def _pump() -> None:
    """Deliver pending Qt events (layout/visibility)."""
    QApplication.instance().processEvents()


def _markdown(tmp_path: Path, name: str) -> Path:
    """Write a minimal Markdown source and return its path."""
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# Notes\n\nBody text.\n", encoding="utf-8")
    return path


def _select(window: "MainWindow", paths: List[Path]) -> None:
    """Select ``paths`` as a batch through the shared selection path."""
    window.set_source_file(str(paths[0]))
    if len(paths) > 1:
        window.add_source_files([str(path) for path in paths[1:]])


# ============================================================
# Surface visibility
# ============================================================


def test_empty_selection_shows_no_batch_surface(tmp_path: Path) -> None:
    """§8.1: nothing selected means no batch surface at all."""
    window = _make_window()
    try:
        window.show()
        _pump()

        assert window.state is GuiState.EMPTY
        assert window.batch_area.isVisible() is False
        assert window.batch_summary_area.isVisible() is False
        assert window.notice_label.isVisible() is False
        assert window.convert_button.text() == CONVERT_TEXT
    finally:
        window.close()


def test_single_selection_keeps_the_light_surface(tmp_path: Path) -> None:
    """§33: one file must not become a batch-management experience."""
    window = _make_window()
    try:
        window.show()
        _pump()
        assert window.set_source_file(str(_markdown(tmp_path, "notes.md"))) is GuiState.READY

        assert window.batch_area.isVisible() is False
        assert window.source_label.text() == "notes.md"
        assert window.convert_button.text() == CONVERT_TEXT
    finally:
        window.close()


def test_multi_selection_shows_the_ordered_list(tmp_path: Path) -> None:
    """§8.2: the selected files are listed in execution order."""
    window = _make_window()
    try:
        window.show()
        _pump()
        sources = [_markdown(tmp_path, name) for name in ("a.md", "b.md", "c.md")]
        _select(window, sources)

        assert window.batch_area.isVisible() is True
        assert window.batch_caption_label.text() == BATCH_CAPTION_TEXT
        assert window.batch_count_label.text() == "3 files selected"
        rows = [window.batch_list.item(index).text() for index in range(window.batch_list.count())]
        assert rows == ["a.md", "b.md", "c.md"]
        assert window.convert_button.text() == CONVERT_MANY_TEMPLATE.format(count=3)
        assert window.source_label.text() == "3 files selected"
    finally:
        window.close()


def test_duplicate_file_names_keep_folder_context(tmp_path: Path) -> None:
    """§8.2: duplicate names are still distinguishable in the list."""
    window = _make_window()
    try:
        first = _markdown(tmp_path / "one", "notes.md")
        second = _markdown(tmp_path / "two", "notes.md")
        _select(window, [first, second])

        labels = window.source_display_labels()
        assert len(labels) == 2
        assert labels[0] != labels[1]
        assert labels[0].startswith("notes.md (")
        assert "one" in labels[0]
        assert "two" in labels[1]
    finally:
        window.close()


def test_every_row_carries_the_full_path_as_tooltip(tmp_path: Path) -> None:
    """§9: the row keeps the complete path available without widening the list."""
    window = _make_window()
    try:
        sources = [_markdown(tmp_path, name) for name in ("a.md", "b.md")]
        _select(window, sources)

        assert window.batch_list.item(0).toolTip() == str(sources[0])
        assert window.batch_list.item(1).toolTip() == str(sources[1])
    finally:
        window.close()


# ============================================================
# List operations
# ============================================================


def test_remove_drops_only_the_highlighted_entries(tmp_path: Path) -> None:
    """§9: individual entries can be removed before conversion."""
    window = _make_window()
    try:
        sources = [_markdown(tmp_path, name) for name in ("a.md", "b.md", "c.md")]
        _select(window, sources)

        window.batch_list.item(1).setSelected(True)
        assert window.batch_remove_button.isEnabled() is True
        assert window.remove_selected_sources() is GuiState.READY

        assert window.batch_selection.sources == (sources[0], sources[2])
        assert window.batch_list.count() == 2
        assert "Removed" in window.notice_label.text()
    finally:
        window.close()


def test_removing_until_one_file_returns_to_the_light_surface(tmp_path: Path) -> None:
    """A batch that shrinks back to one file behaves like a single selection."""
    window = _make_window()
    try:
        sources = [_markdown(tmp_path, name) for name in ("a.md", "b.md")]
        _select(window, sources)

        window.batch_list.item(1).setSelected(True)
        window.remove_selected_sources()

        assert window.batch_selection.sources == (sources[0],)
        assert window.batch_area.isVisible() is False
        assert window.convert_button.text() == CONVERT_TEXT
        assert window.state is GuiState.READY
    finally:
        window.close()


def test_clear_empties_the_selection(tmp_path: Path) -> None:
    """§9: the complete list can be cleared and the workflow restarts."""
    window = _make_window()
    try:
        _select(window, [_markdown(tmp_path, name) for name in ("a.md", "b.md")])

        assert window.clear_sources() is GuiState.EMPTY
        assert window.batch_selection.is_empty is True
        assert window.batch_list.count() == 0
        assert window.batch_area.isVisible() is False
        assert window.convert_button.isEnabled() is False
    finally:
        window.close()


def test_remove_requires_a_highlighted_entry(tmp_path: Path) -> None:
    """Remove is a no-op (and disabled) without a selection."""
    window = _make_window()
    try:
        sources = [_markdown(tmp_path, name) for name in ("a.md", "b.md")]
        _select(window, sources)
        window.batch_list.clearSelection()
        _pump()

        assert window.batch_remove_button.isEnabled() is False
        assert window.remove_selected_sources() is GuiState.READY
        assert window.batch_selection.sources == tuple(sources)
    finally:
        window.close()


def test_clear_is_a_no_op_without_a_selection() -> None:
    """Clearing an empty workflow changes nothing."""
    window = _make_window()
    try:
        assert window.clear_sources() is GuiState.EMPTY
        assert window.state_model.source is None
    finally:
        window.close()


# ============================================================
# Bounded feedback
# ============================================================


def test_notice_appears_for_skipped_items_and_clears_on_a_new_selection(
    tmp_path: Path,
) -> None:
    """§9.2: bounded feedback explains skipped items and does not linger."""
    window = _make_window()
    try:
        window.show()
        _pump()
        markdown = _markdown(tmp_path, "notes.md")
        other = tmp_path / "notes.txt"
        other.write_text("not markdown\n", encoding="utf-8")

        window.set_source_file(str(markdown))
        window.add_source_files([str(other)])
        assert window.notice_label.isVisible() is True
        assert "Skipped 1 item" in window.notice_label.text()

        window.set_source_file(str(markdown))
        assert window.notice_label.isVisible() is False
        assert window.notice_label.text() == ""
    finally:
        window.close()


def test_invalid_drop_does_not_change_the_batch(tmp_path: Path) -> None:
    """§26: invalid payloads never corrupt the active list."""
    window = _make_window()
    try:
        sources = [_markdown(tmp_path, name) for name in ("a.md", "b.md")]
        _select(window, sources)
        window.add_source_files([str(tmp_path / "missing.md"), "   "])

        assert window.batch_selection.sources == tuple(sources)
        assert "Skipped 2 items" in window.notice_label.text()
    finally:
        window.close()


# ============================================================
# Mutation lock during conversion
# ============================================================


def test_selection_is_locked_while_converting(tmp_path: Path) -> None:
    """§20: list mutation is unavailable while a batch is running."""
    window = _make_window()
    try:
        sources = [_markdown(tmp_path, name) for name in ("a.md", "b.md")]
        extra = _markdown(tmp_path, "c.md")
        _select(window, sources)
        window.request_convert()

        assert window.batch_list.isEnabled() is False
        assert window.batch_remove_button.isEnabled() is False
        assert window.batch_clear_button.isEnabled() is False
        assert window.clear_sources() is GuiState.CONVERTING
        assert window.add_source_files([str(extra)]) is GuiState.CONVERTING
        assert window.batch_selection.sources == tuple(sources)
    finally:
        window.close()


# ============================================================
# Accessibility
# ============================================================


def test_batch_controls_carry_accessible_names(tmp_path: Path) -> None:
    """§31: the batch controls are understandable to assistive technology."""
    window = _make_window()
    try:
        assert window.batch_list.accessibleName() == BATCH_LIST_ACCESSIBLE_NAME
        assert window.batch_remove_button.accessibleName() == BATCH_REMOVE_TEXT
        assert window.batch_clear_button.accessibleName() == BATCH_CLEAR_TEXT
        assert window.open_batch_folder_button.accessibleName() == OPEN_BATCH_FOLDER_TEXT
        assert window.view_batch_report_button.accessibleName() == VIEW_BATCH_REPORT_TEXT
        assert window.batch_summary_label.accessibleName()
        assert window.notice_label.accessibleName()
    finally:
        window.close()


def test_batch_list_and_operations_are_keyboard_reachable(tmp_path: Path) -> None:
    """§31: the list and its operations are reachable with the keyboard."""
    from PySide6.QtCore import Qt

    window = _make_window()
    try:
        _select(window, [_markdown(tmp_path, name) for name in ("a.md", "b.md")])
        window.show()
        _pump()

        assert window.batch_list.focusPolicy() & Qt.FocusPolicy.TabFocus
        assert window.batch_remove_button.focusPolicy() & Qt.FocusPolicy.TabFocus
        assert window.batch_clear_button.focusPolicy() & Qt.FocusPolicy.TabFocus
        assert window.batch_list.item(0).text()
    finally:
        window.close()


def test_wording_has_no_technical_jargon(tmp_path: Path) -> None:
    """§30: the batch surfaces use plain product language."""
    window = _make_window()
    try:
        _select(window, [_markdown(tmp_path, name) for name in ("a.md", "b.md")])
        texts = [
            window.batch_caption_label.text(),
            window.batch_count_label.text(),
            window.batch_remove_button.text(),
            window.batch_clear_button.text(),
            window.convert_button.text(),
            window.open_batch_folder_button.text(),
            window.view_batch_report_button.text(),
            window.open_batch_folder_button.toolTip(),
            window.view_batch_report_button.toolTip(),
            window.batch_list.toolTip(),
        ]
        for text in texts:
            assert text.strip() == text
            for jargon in ("--", "CompilerContext", "ConversionService", "AST", "QA"):
                assert jargon not in text, (text, jargon)
    finally:
        window.close()
