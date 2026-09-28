"""Focused verification for Markdown drag & drop (WP-P12-04-05 §8, SBC-02).

The tests drive the real Qt drag/drop event types (``QDragEnterEvent``,
``QDragMoveEvent``, ``QDragLeaveEvent``, ``QDropEvent``) into the drop area and
verify acceptance, the shared source-selection path and the GUI state.  No
native drag session is started.

Rejected payloads are checked for the retained cases: unsupported file, folder,
non-local URL, payload without URLs and drop while ``CONVERTING``.  SBC-02
supersedes the old multi-file rejection guard: the frozen product decision is
that a multi-file payload *is* accepted and adds every valid unique source to
the batch.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, List

import pytest

if TYPE_CHECKING:  # pragma: no cover - typing only
    from md_converter.gui.drop_zone import DropZone
    from md_converter.gui.main_window import MainWindow

pytest.importorskip("PySide6", reason="PySide6 (GUI dev dependency) is not installed")

#: Qt needs a platform plugin even when a test only constructs widgets.  Set
#: here (not in a directory ``conftest.py``) because the test tree is not a
#: package and a second ``conftest`` would shadow ``md_converter/tests/conftest.py``.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from md_converter.gui import file_picker  # noqa: E402 - the Qt guard must run first
from md_converter.gui.main_window import DROP_HINT_TEXT, DROP_RELEASE_HINT_TEXT  # noqa: E402
from md_converter.gui.state import GuiState  # noqa: E402

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


def _mime_for(paths: List[Path]):
    """Return MIME data carrying local file URLs for ``paths``."""
    from PySide6.QtCore import QMimeData, QUrl

    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(path)) for path in paths])
    return mime


def _drag_enter_mime(zone: "DropZone", mime) -> bool:
    """Send a drag-enter event carrying ``mime``; return the accept result.

    The payload is kept alive by the caller for the duration of the call: Qt
    events do not take ownership of the ``QMimeData`` they are given.
    """
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtGui import QDragEnterEvent

    event = QDragEnterEvent(
        QPoint(10, 10),
        Qt.DropAction.CopyAction,
        mime,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    zone.dragEnterEvent(event)
    return bool(event.isAccepted())


def _drag_enter(zone: "DropZone", paths: List[Path]) -> bool:
    """Send a drag-enter event carrying ``paths`` to ``zone``."""
    return _drag_enter_mime(zone, _mime_for(paths))


def _drag_move(zone: "DropZone", paths: List[Path]) -> bool:
    """Send a drag-move event carrying ``paths`` to ``zone``."""
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtGui import QDragMoveEvent

    mime = _mime_for(paths)
    event = QDragMoveEvent(
        QPoint(10, 10),
        Qt.DropAction.CopyAction,
        mime,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    zone.dragMoveEvent(event)
    return bool(event.isAccepted())


def _drag_leave(zone: "DropZone") -> None:
    """Send a drag-leave event to ``zone``."""
    from PySide6.QtGui import QDragLeaveEvent

    event = QDragLeaveEvent()
    zone.dragLeaveEvent(event)


def _drop_mime(zone: "DropZone", mime) -> bool:
    """Send a drop event carrying ``mime``; return the accept result."""
    from PySide6.QtCore import QPointF, Qt
    from PySide6.QtGui import QDropEvent

    event = QDropEvent(
        QPointF(10.0, 10.0),
        Qt.DropAction.CopyAction,
        mime,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    zone.dropEvent(event)
    return bool(event.isAccepted())


def _drop(zone: "DropZone", paths: List[Path]) -> bool:
    """Send a drop event carrying ``paths`` to ``zone``."""
    return _drop_mime(zone, _mime_for(paths))


# ============================================================
# Valid single-file drop
# ============================================================


def test_valid_single_markdown_drop_enters_ready(tmp_path: Path) -> None:
    """WP §5: a valid single ``.md`` drop selects the source and enters READY."""
    markdown = _write_markdown(tmp_path / "notes.md")
    window = _make_window()
    try:
        window.show()
        _process_events()

        assert _drag_enter(window.drop_zone, [markdown]) is True
        assert _drop(window.drop_zone, [markdown]) is True
        _process_events()

        assert window.state is GuiState.READY
        assert window.state_model.source == str(markdown)
        assert window.convert_button.isEnabled() is True
        assert window.source_label.text() == "notes.md"
    finally:
        window.close()


def test_drop_uses_shared_selection_logic(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """WP §4: picker and drag & drop both route through the shared validator."""
    markdown = _write_markdown(tmp_path / "notes.md")
    window = _make_window()
    try:
        seen: List[object] = []
        original = file_picker.validate_markdown_source

        def recording(path):
            seen.append(path)
            return original(path)

        monkeypatch.setattr(file_picker, "validate_markdown_source", recording)
        monkeypatch.setattr(
            file_picker, "ask_for_markdown_sources", lambda *args, **kwargs: (str(markdown),)
        )

        # Picker path
        window.select_file_button.click()
        assert window.state is GuiState.READY
        picker_calls = len(seen)
        assert picker_calls >= 1

        # Drop path (same file, after clearing the selection)
        window.reset()
        _drop(window.drop_zone, [markdown])

        assert window.state is GuiState.READY
        assert window.state_model.source == str(markdown)
        assert len(seen) > picker_calls
        assert str(markdown) in {str(entry) for entry in seen}
    finally:
        window.close()


def test_hover_feedback_appears_and_is_restored(tmp_path: Path) -> None:
    """WP §6: simple text feedback while a valid drag hovers the area."""
    markdown = _write_markdown(tmp_path / "notes.md")
    window = _make_window()
    try:
        assert window.drop_label.text() == DROP_HINT_TEXT

        _drag_enter(window.drop_zone, [markdown])
        assert window.drop_label.text() == DROP_RELEASE_HINT_TEXT

        _drag_leave(window.drop_zone)
        assert window.drop_label.text() == DROP_HINT_TEXT

        _drag_enter(window.drop_zone, [markdown])
        _drop(window.drop_zone, [markdown])
        assert window.drop_label.text() == DROP_HINT_TEXT
    finally:
        window.close()


def test_drag_move_keeps_accepting_valid_payload(tmp_path: Path) -> None:
    """A valid drag stays accepted while moving over the area."""
    markdown = _write_markdown(tmp_path / "notes.md")
    window = _make_window()
    try:
        _drag_enter(window.drop_zone, [markdown])

        assert _drag_move(window.drop_zone, [markdown]) is True
    finally:
        window.close()


# ============================================================
# Rejected payloads
# ============================================================


def test_unsupported_file_drop_is_rejected(tmp_path: Path) -> None:
    """WP §5: an unsupported file never becomes the source."""
    text_file = _write_markdown(tmp_path / "notes.txt")
    window = _make_window()
    try:
        assert _drag_enter(window.drop_zone, [text_file]) is False
        assert _drop(window.drop_zone, [text_file]) is False
        assert window.state is GuiState.EMPTY
        assert window.state_model.source is None
        assert window.source_label.text() == ""
    finally:
        window.close()


def test_folder_drop_is_rejected(tmp_path: Path) -> None:
    """WP §5: folder input is rejected in P12-04."""
    folder = tmp_path / "docs"
    folder.mkdir()
    window = _make_window()
    try:
        assert _drag_enter(window.drop_zone, [folder]) is False
        assert _drop(window.drop_zone, [folder]) is False
        assert window.state is GuiState.EMPTY
    finally:
        window.close()


def test_multiple_markdown_files_are_added_as_a_batch(tmp_path: Path) -> None:
    """SBC-02: a multi-file payload becomes the ordered batch selection."""
    first = _write_markdown(tmp_path / "first.md")
    second = _write_markdown(tmp_path / "second.md")
    third = _write_markdown(tmp_path / "third.md")
    window = _make_window()
    try:
        window.show()
        _process_events()
        assert _drag_enter(window.drop_zone, [first, second, third]) is True
        assert _drop(window.drop_zone, [first, second, third]) is True

        assert window.state is GuiState.READY
        assert window.batch_selection.sources == (first, second, third)
        assert window.batch_list.count() == 3
        assert window.batch_area.isVisible() is True
        assert window.convert_button.text() == "Convert 3 Files"
    finally:
        window.close()


def test_mixed_payload_keeps_the_valid_files(tmp_path: Path) -> None:
    """SBC-02: a non-Markdown item is skipped without disturbing the batch."""
    markdown = _write_markdown(tmp_path / "notes.md")
    other = _write_markdown(tmp_path / "notes.txt")
    window = _make_window()
    try:
        assert _drop(window.drop_zone, [markdown, other]) is True

        assert window.state is GuiState.READY
        assert window.batch_selection.sources == (markdown,)
        assert "Skipped 1 item" in window.notice_label.text()
    finally:
        window.close()


def test_second_drop_adds_to_the_existing_batch(tmp_path: Path) -> None:
    """SBC-02: dropping more files adds valid unique sources to the list."""
    first = _write_markdown(tmp_path / "first.md")
    second = _write_markdown(tmp_path / "second.md")
    window = _make_window()
    try:
        assert _drop(window.drop_zone, [first]) is True
        assert _drop(window.drop_zone, [second, first]) is True

        assert window.batch_selection.sources == (first, second)
        assert "already in the list" in window.notice_label.text()
    finally:
        window.close()


def test_non_local_url_is_rejected(tmp_path: Path) -> None:
    """A non-file URL is not a local Markdown source."""
    from PySide6.QtCore import QMimeData, QUrl

    window = _make_window()
    try:
        mime = QMimeData()
        mime.setUrls([QUrl("https://example.com/notes.md")])

        assert _drop_mime(window.drop_zone, mime) is False
        assert window.state is GuiState.EMPTY
    finally:
        window.close()


def test_payload_without_urls_is_rejected() -> None:
    """Plain text drags carry no source."""
    from PySide6.QtCore import QMimeData

    window = _make_window()
    try:
        mime = QMimeData()
        mime.setText("notes.md")

        assert _drop_mime(window.drop_zone, mime) is False
        assert window.state is GuiState.EMPTY
    finally:
        window.close()


def test_rejected_drop_preserves_existing_selection(tmp_path: Path) -> None:
    """WP §5: a rejected drop keeps the current valid source."""
    markdown = _write_markdown(tmp_path / "notes.md")
    text_file = _write_markdown(tmp_path / "notes.txt")
    window = _make_window()
    try:
        _drop(window.drop_zone, [markdown])
        assert window.state is GuiState.READY

        assert _drop(window.drop_zone, [text_file]) is False
        assert window.state is GuiState.READY
        assert window.state_model.source == str(markdown)
        assert window.source_label.text() == "notes.md"
    finally:
        window.close()


# ============================================================
# CONVERTING protection
# ============================================================


def test_drop_during_converting_does_not_change_state(tmp_path: Path) -> None:
    """WP §5: drops cannot alter an in-flight conversion."""
    first = _write_markdown(tmp_path / "first.md")
    second = _write_markdown(tmp_path / "second.md")
    window = _make_window()
    try:
        window.set_source(str(first))
        window.request_convert()
        assert window.state is GuiState.CONVERTING

        # Acceptance is disabled by the GUI state ...
        assert window.drop_zone.acceptDrops() is False

        # ... and even if a drop is delivered (forced here), the shared source
        # path must not alter the in-flight conversion.
        _ = _drop(window.drop_zone, [second])
        _process_events()

        assert window.state is GuiState.CONVERTING
        assert window.state_model.source == str(first)
    finally:
        window.close()


def test_drop_acceptance_returns_after_completion(tmp_path: Path) -> None:
    """Completion states allow input again (WP-P12-04-03 §4, SBC-02)."""
    first = _write_markdown(tmp_path / "first.md")
    second = _write_markdown(tmp_path / "second.md")
    window = _make_window()
    try:
        window.set_source_file(str(first))
        window.request_convert()
        window.simulate_success()
        assert window.drop_zone.acceptDrops() is True

        assert _drop(window.drop_zone, [second]) is True

        assert window.state is GuiState.READY
        assert window.batch_selection.sources == (first, second)
    finally:
        window.close()
