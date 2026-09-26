"""Main window foundation for the MD_Converter GUI (WP-P12-04-02/03/04).

Visible shell for the v2.0 workflow (``V2_GUI_UX_SPEC`` §3):

    drop area -> output row -> Convert -> status

Scope limits for this work package:

* no conversion call, no Core / ``ConversionService`` import;
* no file picker, drag & drop or output-selection behavior;
* no worker/thread, diagnostics UX or settings.

The GUI state model (WP-P12-04-03) governs enablement, the source display and
the status text.  Source selection (WP-P12-04-04) uses the standard file dialog
and funnels into :meth:`MainWindow.set_source`; drag & drop, output selection
and conversion wiring arrive with later work packages.  Standard Qt layouts are
used throughout (WP-P12-04-02 §7): no absolute positioning, no custom painting,
no theming.

WP-P12-04-03 adds the explicit GUI state model.  Widget enablement, the source
display and the status text are derived from :mod:`md_converter.gui.state`
through the single :meth:`MainWindow._apply_state` path, so no other method
writes those widget states.
"""

from __future__ import annotations

from pathlib import Path
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

from . import file_picker
from .state import GuiState, GuiStateModel

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
    "SOURCE_PATH_MAX_CHARS",
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

#: Layout sizing for the drop area and the primary action.
DROP_ZONE_MINIMUM_HEIGHT = 180
CONVERT_MINIMUM_WIDTH = 140

#: Long-path display strategy (WP-P12-04-04 §7): the file name stays complete,
#: the containing folder is middle-elided to this many characters, and both
#: labels carry the full path as a tooltip.  The full path remains available
#: internally in ``state_model.source``.
SOURCE_PATH_MAX_CHARS = 56


def _source_display_name(source: Optional[str]) -> str:
    """Return the file-name text shown for a selected source."""
    if not source:
        return ""
    return Path(source).name or source


def _source_display_folder(source: Optional[str]) -> str:
    """Return the middle-elided containing folder shown for a selected source."""
    if not source:
        return ""
    folder = Path(source).parent
    folder_text = str(folder)
    if folder_text in ("", "."):
        return ""
    return _elide_middle(folder_text, SOURCE_PATH_MAX_CHARS)


def _elide_middle(text: str, max_chars: int) -> str:
    """Shorten ``text`` to ``max_chars`` characters, eliding its middle."""
    if max_chars <= 1 or len(text) <= max_chars:
        return text
    head = (max_chars - 1) // 2
    tail = max_chars - 1 - head
    if tail <= 0:
        return f"{text[:head]}\u2026"
    return f"{text[:head]}\u2026{text[-tail:]}"


class MainWindow(QMainWindow):
    """Main window foundation: the visible v2.0 workflow shell.

    Attributes:
        state_model: Explicit GUI state model (Qt-free).
        state: Current GUI state (read-only convenience accessor).
        drop_zone: Drop-area placeholder frame.
        drop_label: Instruction text inside the drop area.
        source_label: Selected source display (hidden while EMPTY).
        source_path_label: Containing folder of the selected source.
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
        self.state_model = GuiStateModel()
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
        self._apply_state()

    @property
    def state(self) -> GuiState:
        """Return the current GUI state."""
        return self.state_model.state

    def set_source(self, source: Optional[str]) -> GuiState:
        """Select a source and return the resulting GUI state.

        This is the state-model entry point for source selection; the file
        picker (WP-P12-04-04) and drag & drop (WP-P12-04-05) call it once their
        behavior is implemented.

        Args:
            source: Display label of the selected source.

        Returns:
            GuiState: The state after the request.
        """
        self.state_model.set_source(source)
        return self._apply_state()

    def reset(self) -> GuiState:
        """Clear the selection and return to ``EMPTY``.

        Returns:
            GuiState: The state after the request.
        """
        self.state_model.reset()
        return self._apply_state()

    def choose_source(self) -> GuiState:
        """Open the Markdown file dialog and apply the chosen source.

        The dialog path is validated at the GUI boundary and then applied
        through :meth:`set_source`, so source selection has exactly one state
        path.  Cancelling the dialog keeps the current selection, and an
        invalid selection is rejected without entering ``READY`` (user-facing
        error UX belongs to a later work package).

        Returns:
            GuiState: The state after the request.
        """
        chosen = file_picker.ask_for_markdown_source(self)
        if chosen is None:
            return self.state
        validated = file_picker.validate_markdown_source(chosen)
        if validated is None:
            return self.state
        return self.set_source(str(validated))

    def request_convert(self) -> GuiState:
        """Request conversion, moving ``READY`` -> ``CONVERTING``.

        The request is rejected (state unchanged) from every other state, which
        prevents duplicate starts while converting.  No conversion work is
        performed in P12-04.

        Returns:
            GuiState: The state after the request.
        """
        self.state_model.request_convert()
        return self._apply_state()

    def simulate_success(self) -> GuiState:
        """Apply the mocked ``CONVERTING`` -> ``SUCCESS`` completion.

        Returns:
            GuiState: The state after the transition.
        """
        self.state_model.complete_success()
        return self._apply_state()

    def simulate_warning(self) -> GuiState:
        """Apply the mocked ``CONVERTING`` -> ``SUCCESS_WITH_WARNING`` completion.

        Returns:
            GuiState: The state after the transition.
        """
        self.state_model.complete_warning()
        return self._apply_state()

    def simulate_failure(self) -> GuiState:
        """Apply the mocked ``CONVERTING`` -> ``FAILED`` completion.

        Returns:
            GuiState: The state after the transition.
        """
        self.state_model.complete_failure()
        return self._apply_state()

    def _apply_state(self) -> GuiState:
        """Apply the current state effects to the widgets.

        This is the *only* place that writes workflow-driven widget state
        (WP-P12-04-03 §7).  Output-selection availability is not part of the
        workflow state; its control stays disabled until WP-P12-04-06.

        Returns:
            GuiState: The current GUI state.
        """
        effect = self.state_model.effect
        self.convert_button.setEnabled(effect.convert_enabled)
        self.select_file_button.setEnabled(effect.select_enabled)
        self.drop_zone.setEnabled(effect.drop_enabled)
        source = self.state_model.source
        self.source_label.setText(_source_display_name(source))
        self.source_label.setToolTip(source or "")
        self.source_label.setVisible(effect.source_visible)
        folder_text = _source_display_folder(source)
        self.source_path_label.setText(folder_text)
        self.source_path_label.setToolTip(source or "")
        self.source_path_label.setVisible(effect.source_visible and bool(folder_text))
        self.status_label.setText(effect.status_text)
        return self.state_model.state

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

        self.source_label = QLabel("", zone)
        self.source_label.setObjectName("sourceLabel")
        self.source_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.source_label.setWordWrap(True)
        zone_layout.addWidget(self.source_label)

        self.source_path_label = QLabel("", zone)
        self.source_path_label.setObjectName("sourcePathLabel")
        self.source_path_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        zone_layout.addWidget(self.source_path_label)

        # File-picker behavior is implemented by WP-P12-04-04; button
        # enablement is applied from the GUI state by _apply_state().
        self.select_file_button = QPushButton(SELECT_FILE_TEXT, zone)
        self.select_file_button.setObjectName("selectFileButton")
        self.select_file_button.clicked.connect(self.choose_source)

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
        # Enablement is applied from the GUI state by _apply_state();
        # real conversion is not authorized in P12-04 (WP-P12-04-02 §6).

        row.addStretch(1)
        row.addWidget(self.convert_button)
        row.addStretch(1)
        return row

    def _create_status_label(self, parent: QWidget) -> QLabel:
        """Create the status area, initially showing the state model text.

        Args:
            parent: Parent widget for the label.

        Returns:
            QLabel: The status label.
        """
        label = QLabel(self.state_model.effect.status_text, parent)
        label.setObjectName("statusLabel")
        return label
