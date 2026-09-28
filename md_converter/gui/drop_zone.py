"""Drop area widget: Markdown drag & drop (WP-P12-04-05, SBC-02).

The widget owns drag & drop *acceptance* only: it decides which payloads are
acceptable (at least one local Markdown file) and reports the payload.  The
authorized multi-file payload of Serial Batch Conversion is accepted;
validation, duplicate filtering and the state transition stay in the shared
source-selection path (``MainWindow.add_source_files``), so the file picker and
drag & drop cannot diverge (WP-P12-04-05 §4).

Simple Qt handling only: no custom animation, no theming, no drop framework.
Folders, non-local URLs and payloads without a single acceptable Markdown file
are rejected; recursive folder discovery stays out of scope (product
specification §26).
"""

from __future__ import annotations

from typing import List, Optional, Union

from PySide6.QtCore import Signal
from PySide6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDragMoveEvent, QDropEvent
from PySide6.QtWidgets import QFrame, QWidget

from . import file_picker

__all__ = ["DropZone"]


class DropZone(QFrame):
    """Framed drop area that accepts one or more Markdown files.

    Signals:
        sources_dropped: Emitted with the local paths of the dropped payload
            when at least one of them is a selectable Markdown file.  The
            payload is passed on unvalidated so the shared selection path
            reports every skipped item.
        hover_changed: Emitted with ``True`` while a valid drag hovers the area,
            and with ``False`` when the drag leaves or is dropped.
    """

    sources_dropped = Signal(list)
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
        """Accept a payload containing Markdown files; ignore anything else.

        Everything rejected here is never dropped, so unsupported files, folders
        and non-local payloads cannot be applied silently.  Acceptance is also
        gated by the GUI state: input is unavailable while ``CONVERTING`` (see
        the state effects applied by ``MainWindow``).
        """
        if not self.acceptDrops() or self._dropped_candidates(event) is None:
            event.ignore()
            return
        event.acceptProposedAction()
        self.hover_changed.emit(True)

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        """Keep accepting while a valid payload hovers the area."""
        if not self.acceptDrops() or self._dropped_candidates(event) is None:
            event.ignore()
            return
        event.acceptProposedAction()

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        """Clear the hover feedback when the drag leaves the area."""
        self.hover_changed.emit(False)
        event.accept()

    def dropEvent(self, event: QDropEvent) -> None:
        """Report the dropped Markdown files, or reject the payload.

        A payload is applied only while the drop area accepts input, so a forced
        drop during ``CONVERTING`` is rejected here as well as by the state
        model.
        """
        candidates = self._dropped_candidates(event) if self.acceptDrops() else None
        self.hover_changed.emit(False)
        if candidates is None:
            event.ignore()
            return
        event.acceptProposedAction()
        self.sources_dropped.emit(list(candidates))

    @staticmethod
    def _dropped_candidates(
        event: Union[QDragEnterEvent, QDragMoveEvent, QDropEvent],
    ) -> Optional[List[str]]:
        """Return the dropped local paths, or ``None`` when the payload is rejected.

        The shared source validation is reused, so the picker and the drop area
        apply identical rules (WP-P12-04-05 §4).

        Args:
            event: Drag/drop event carrying the proposed payload.

        Returns:
            Optional[List[str]]: The local paths of the payload when at least
            one of them is a selectable Markdown file; ``None`` when the payload
            carries no local files or no acceptable source.
        """
        mime = event.mimeData()
        if not mime.hasUrls():
            return None
        candidates: List[str] = []
        acceptable = False
        for url in mime.urls():
            if not url.isLocalFile():
                continue
            local_path = url.toLocalFile()
            candidates.append(local_path)
            if file_picker.validate_markdown_source(local_path) is not None:
                acceptable = True
        if not candidates or not acceptable:
            return None
        return candidates
