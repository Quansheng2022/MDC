"""Main window baseline for the MD_Converter GUI (WP-P12-04-01).

The first window is intentionally minimal (WP-P12-04-01 §5): application
title, stable initial size, a central widget with a layout, and placeholder
content that proves the bootstrap.

Interactive controls (file selection, drag & drop, output selection, convert
action, state feedback) belong to later work packages; this module must not
pre-empt them.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

__all__ = [
    "MINIMUM_HEIGHT",
    "MINIMUM_WIDTH",
    "MainWindow",
    "PLACEHOLDER_TEXT",
    "WINDOW_HEIGHT",
    "WINDOW_TITLE",
    "WINDOW_WIDTH",
]

#: Window title (``V2_GUI_UX_SPEC`` §3 reference layout).
WINDOW_TITLE = "MD Converter"

#: Stable initial window size.
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 600

#: Lower bound that keeps the bootstrap layout usable when resized.
MINIMUM_WIDTH = 640
MINIMUM_HEIGHT = 480

#: Placeholder content proving the bootstrap.  It states the product job only;
#: no control is advertised before the corresponding work package exists.
PLACEHOLDER_TEXT = "MD Converter \u2014 Markdown to DOCX"


class MainWindow(QMainWindow):
    """Minimal main window proving the GUI bootstrap."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Build the bootstrap window.

        Args:
            parent: Optional Qt parent widget.
        """
        super().__init__(parent)
        self.setObjectName("MainWindow")
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(MINIMUM_WIDTH, MINIMUM_HEIGHT)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

        central = QWidget(self)
        central.setObjectName("centralWidget")
        layout = QVBoxLayout(central)
        layout.setObjectName("centralLayout")

        placeholder = QLabel(PLACEHOLDER_TEXT, central)
        placeholder.setObjectName("placeholderLabel")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(placeholder)

        self.setCentralWidget(central)
