"""Drop area widget: single-file Markdown drag & drop (WP-P12-04-05).

The widget owns drag & drop *acceptance* only: it decides which payloads are
acceptable (exactly one local Markdown file) and reports them.  Validation and
the state transition stay in the shared source-selection path
(``MainWindow.set_source_file``), so the file picker and drag & drop cannot
diverge (WP-P12-04-05 §4).

Simple Qt handling only: no custom animation, no theming, no drop framework.
Folder input, multi-file batches and recursive drops are explicitly rejected
(WP-P12-04-05 §5/§7).
"""

from __future__ import annotations

from typing import Optional, Union

from PySide6.QtCore import Signal
from PySide6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDragMoveEvent, QDropEvent
from PySide6.QtWidgets import QFrame, QWidget

from . import file_picker

__all__ = ["DropZone"]


class DropZone(QFrame):
    """Framed drop area that accepts a single Markdown file.

    Signals:
        source_dropped: Emitted with the local path of a valid dropped file.
        hover_changed: Emitted with ``True`` while a valid drag hovers the area,
            and with ``False`` when the drag leaves or is dropped.
    """

    source_dropped = Signal(str)
    hover_changed = Signal(bool)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Create the drop area frame.

        Args:
            parent: Optional Qt parent widget.
        """
        super().__init__(parent)
        self.setObjectName("dropZone")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Sunken)
        # A drop area accepts drops by default; MainWindow applies the GUI state
        # (which disables acceptance while CONVERTING).
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Accept a valid single Markdown payload; ignore anything else.

        Everything rejected here is never dropped, so unsupported files,
        folders and multi-file payloads cannot be applied silently.
        Acceptance is also gated by the GUI state: input is unavailable while
        ``CONVERTING`` (see the state effects applied by ``MainWindow``).
        """
        if not self.acceptDrops() or self._dropped_source(event) is None:
            event.ignore()
            return
        event.acceptProposedAction()
        self.hover_changed.emit(True)

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        """Keep accepting while a valid payload hovers the area."""
        if not self.acceptDrops() or self._dropped_source(event) is None:
            event.ignore()
            return
        event.acceptProposedAction()

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        """Clear the hover feedback when the drag leaves the area."""
        self.hover_changed.emit(False)
        event.accept()

    def dropEvent(self, event: QDropEvent) -> None:
        """Select the dropped Markdown file, or reject the payload.

        A payload is applied only while the drop area accepts input, so a forced
        drop during ``CONVERTING`` is rejected here as well as by the state
        model.
        """
        source = self._dropped_source(event) if self.acceptDrops() else None
        self.hover_changed.emit(False)
        if source is None:
            event.ignore()
            return
        event.acceptProposedAction()
        self.source_dropped.emit(source)

    @staticmethod
    def _dropped_source(
        event: Union[QDragEnterEvent, QDragMoveEvent, QDropEvent],
    ) -> Optional[str]:
        """Return the single dropped Markdown path, or ``None`` when rejected.

        The shared source validation is reused, so the picker and the drop area
        apply identical rules (WP-P12-04-05 §4).

        Args:
            event: Drag/drop event carrying the proposed payload.

        Returns:
            Optional[str]: The validated local path, or ``None`` when the
            payload is not exactly one local Markdown file.
        """
        mime = event.mimeData()
        if not mime.hasUrls():
            return None
        urls = mime.urls()
        if len(urls) != 1:
            # Multiple files: reject instead of silently choosing the first.
            return None
        url = urls[0]
        if not url.isLocalFile():
            return None
        validated = file_picker.validate_markdown_source(url.toLocalFile())
        if validated is None:
            return None
        return str(validated)
