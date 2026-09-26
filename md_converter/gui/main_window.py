"""Main window foundation for the MD_Converter GUI (WP-P12-04-02).

Visible shell for the v2.0 workflow (``V2_GUI_UX_SPEC`` §3):

    drop area -> output row -> Convert -> status

Scope limits for this work package:

* no conversion call, no Core / ``ConversionService`` import;
* no file picker, drag & drop or output-selection behavior;
* no worker/thread, diagnostics UX or settings.

The controls are present as inert placeholders; the GUI state model and the
behavior behind them arrive with later work packages (WP-P12-04-03 onwards).
Standard Qt layouts are used throughout (WP-P12-04-02 §7): no absolute
positioning, no custom painting, no theming.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

__all__ = [
    "CHANGE_OUTPUT_TEXT",
    "CONVERT_MINIMUM_WIDTH",
    "CONVERT_TEXT",
    "DROP_HINT_TEXT",
    "DROP_ZONE_MINIMUM_HEIGHT",
    "MINIMUM_HEIGHT",
    "MINIMUM_WIDTH",
    "MainWindow",
    "OUTPUT_CAPTION_TEXT",
    "OUTPUT_VALUE_TEXT",
    "SELECT_FILE_TEXT",
    "STATUS_TEXT",
    "WINDOW_HEIGHT",
    "WINDOW_TITLE",
    "WINDOW_WIDTH",
]

#: Window title (``V2_GUI_UX_SPEC`` §3 reference layout).
WINDOW_TITLE = "MD Converter"

#: Stable initial window size.
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 600

#: Lower bound that keeps the layout usable when resized.
MINIMUM_WIDTH = 640
MINIMUM_HEIGHT = 480

#: Visible labels.  Plain product language only (WP-P12-04-02 §5).
DROP_HINT_TEXT = "Drop Markdown file here"
SELECT_FILE_TEXT = "Select File"
OUTPUT_CAPTION_TEXT = "Output folder:"
OUTPUT_VALUE_TEXT = "Same as source"
CHANGE_OUTPUT_TEXT = "Change"
CONVERT_TEXT = "Convert"
STATUS_TEXT = "Ready"

#: Layout sizing for the drop area and the primary action.
DROP_ZONE_MINIMUM_HEIGHT = 180
CONVERT_MINIMUM_WIDTH = 140


class MainWindow(QMainWindow):
    """Main window foundation: the visible v2.0 workflow shell.

    Attributes:
        drop_zone: Drop-area placeholder frame.
        drop_label: Instruction text inside the drop area.
        select_file_button: Placeholder for the file picker.
        output_value_label: Current output destination display.
        change_output_button: Placeholder for output selection.
        convert_button: Primary action placeholder.
        status_label: Status area text.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Build the window shell.

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
        layout.setObjectName("mainLayout")
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(14)

        self.drop_zone = self._create_drop_zone(central)
        layout.addWidget(self.drop_zone, 1)
        layout.addLayout(self._create_output_row(central))
        layout.addLayout(self._create_convert_row(central))
        self.status_label = self._create_status_label(central)
        layout.addWidget(self.status_label)

        self.setCentralWidget(central)

    def _create_drop_zone(self, parent: QWidget) -> QFrame:
        """Create the drop-area placeholder (no drag & drop behavior yet).

        Args:
            parent: Parent widget for the frame.

        Returns:
            QFrame: Drop area holding the instruction text and file button.
        """
        zone = QFrame(parent)
        zone.setObjectName("dropZone")
        zone.setFrameShape(QFrame.Shape.StyledPanel)
        zone.setFrameShadow(QFrame.Shadow.Sunken)
        zone.setMinimumHeight(DROP_ZONE_MINIMUM_HEIGHT)

        zone_layout = QVBoxLayout(zone)
        zone_layout.setObjectName("dropZoneLayout")
        zone_layout.setSpacing(12)
        zone_layout.addStretch(1)

        self.drop_label = QLabel(DROP_HINT_TEXT, zone)
        self.drop_label.setObjectName("dropLabel")
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        zone_layout.addWidget(self.drop_label)

        self.select_file_button = QPushButton(SELECT_FILE_TEXT, zone)
        self.select_file_button.setObjectName("selectFileButton")
        # File-picker behavior is implemented by WP-P12-04-04.
        self.select_file_button.setEnabled(False)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        button_row.addWidget(self.select_file_button)
        button_row.addStretch(1)
        zone_layout.addLayout(button_row)
        zone_layout.addStretch(1)
        return zone

    def _create_output_row(self, parent: QWidget) -> QHBoxLayout:
        """Create the output-location row (display-only placeholder).

        Args:
            parent: Parent widget for the labels and button.

        Returns:
            QHBoxLayout: The output row.
        """
        row = QHBoxLayout()
        row.setObjectName("outputRow")
        row.setSpacing(8)

        caption = QLabel(OUTPUT_CAPTION_TEXT, parent)
        caption.setObjectName("outputCaptionLabel")
        self.output_value_label = QLabel(OUTPUT_VALUE_TEXT, parent)
        self.output_value_label.setObjectName("outputValueLabel")
        self.change_output_button = QPushButton(CHANGE_OUTPUT_TEXT, parent)
        self.change_output_button.setObjectName("changeOutputButton")
        # Output selection is implemented by WP-P12-04-06.
        self.change_output_button.setEnabled(False)

        row.addWidget(caption)
        row.addWidget(self.output_value_label)
        row.addStretch(1)
        row.addWidget(self.change_output_button)
        return row

    def _create_convert_row(self, parent: QWidget) -> QHBoxLayout:
        """Create the centered primary Convert row.

        Args:
            parent: Parent widget for the button.

        Returns:
            QHBoxLayout: The Convert row.
        """
        row = QHBoxLayout()
        row.setObjectName("convertRow")

        self.convert_button = QPushButton(CONVERT_TEXT, parent)
        self.convert_button.setObjectName("convertButton")
        self.convert_button.setMinimumWidth(CONVERT_MINIMUM_WIDTH)
        self.convert_button.setDefault(True)
        # Real conversion is not authorized in P12-04 (WP-P12-04-02 §6).
        self.convert_button.setEnabled(False)

        row.addStretch(1)
        row.addWidget(self.convert_button)
        row.addStretch(1)
        return row

    @staticmethod
    def _create_status_label(parent: QWidget) -> QLabel:
        """Create the status area (static text until WP-P12-04-03).

        Args:
            parent: Parent widget for the label.

        Returns:
            QLabel: The status label.
        """
        label = QLabel(STATUS_TEXT, parent)
        label.setObjectName("statusLabel")
        return label
