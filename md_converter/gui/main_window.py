"""Main window foundation for the MD_Converter GUI (WP-P12-04-02..06, P12-05-03).

Visible shell for the v2.0 workflow (``V2_GUI_UX_SPEC`` §3):

    drop area -> output row -> Convert -> status

Scope limits:

* conversion runs only through the application service
  (:mod:`md_converter.application`); the GUI never imports the compiler,
  parser, pipeline, renderer or QA internals (WP-P12-05-03 §5);
* no diagnostics UX framework and no settings persistence;
* no DOCX naming or frontmatter logic (WP-P12-04-06 §5).

The GUI state model (WP-P12-04-03) governs enablement, the source display and
the status text.  Source selection (WP-P12-04-04) uses the standard file dialog
and drag & drop (WP-P12-04-05) both funnel into
:meth:`MainWindow.set_source_file`, which applies the shared validation before
the single state path :meth:`MainWindow.set_source`.  Output folder selection
(WP-P12-04-06) stores a session preference only: the approved
application/service behavior remains the authority for the final DOCX name.
The Convert action (WP-P12-05-03) builds its request with the shared
:mod:`md_converter.gui.request_builder` and runs
``ConversionService.convert`` through the :class:`~md_converter.gui.worker.GuiWorker`
boundary, so conversion never executes on the GUI thread.  Standard Qt layouts
are used throughout (WP-P12-04-02 §7): no absolute positioning, no custom
painting, no theming.

WP-P12-04-03 adds the explicit GUI state model.  Widget enablement, the source
display and the status text are derived from :mod:`md_converter.gui.state`
through the single :meth:`MainWindow._apply_state` path, so no other method
writes those widget states.

WP-P12-06-02/03 add the bounded outcome UX.  A ``FAILED`` result, a worker
``JobFailure`` and a ``SUCCESS_WITH_WARNING`` result are presented through the
WP-P12-06-01 presentation model: the window only displays the derived summary
and offers a bounded ``Details...`` affordance when the presentation reports
evidence.  A warning stays a successful outcome - it is never routed through
the failure presentation - and a plain ``SUCCESS`` keeps its existing surface.
The presentation model stays the single presentation-semantic authority, and
the retained ``ConversionResult`` / ``JobFailure`` evidence is never modified.

WP-P12-06-05 adds the bounded output actions.  ``Open Document`` and
``Open Folder`` are offered only when the presentation reports an actionable
artifact, and they act on the retained ``ConversionResult.output_path`` verbatim
(see :mod:`md_converter.gui.output_actions`).  No output name is derived or
reconstructed here, and no action triggers a conversion.
"""

from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import Callable, Optional, Union

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..application.conversion_result import ConversionResult
from ..application.conversion_service import ConversionService
from . import file_picker
from .drop_zone import DropZone
from .output_actions import notify_missing_artifact, open_document, open_folder
from .presentation_model import Presentation, present_job_failure, present_result
from .request_builder import build_conversion_request
from .result_details import show_result_details
from .result_mapping import gui_state_for_result
from .state import GuiState, GuiStateModel
from .worker import GuiWorker, JobFailure

__all__ = [
    "CHANGE_OUTPUT_TEXT",
    "CONVERT_MINIMUM_WIDTH",
    "CONVERT_TEXT",
    "DROP_HINT_TEXT",
    "DROP_RELEASE_HINT_TEXT",
    "DROP_ZONE_MINIMUM_HEIGHT",
    "DETAILS_TEXT",
    "MINIMUM_HEIGHT",
    "MINIMUM_WIDTH",
    "MainWindow",
    "OPEN_DOCUMENT_TEXT",
    "OPEN_FOLDER_TEXT",
    "OUTPUT_CAPTION_TEXT",
    "OUTPUT_PATH_MAX_CHARS",
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
#: Transient drag-over feedback (WP-P12-04-05 §6: "text change").
DROP_RELEASE_HINT_TEXT = "Release to select this file"
SELECT_FILE_TEXT = "Select File"
OUTPUT_CAPTION_TEXT = "Output folder:"
#: Default output presentation.  The service resolves the actual location, so
#: the wording does not promise a source-directory default (WP-P12-05-03).
OUTPUT_VALUE_TEXT = "Default location"
CHANGE_OUTPUT_TEXT = "Change"
CONVERT_TEXT = "Convert"

#: Bounded details affordance for presented outcomes (WP-P12-06-02/03).
DETAILS_TEXT = "Details..."

#: Bounded post-conversion output actions (WP-P12-06-05).
OPEN_DOCUMENT_TEXT = "Open Document"
OPEN_FOLDER_TEXT = "Open Folder"

#: GUI states whose result presentation is shown in the result area.  A plain
#: ``SUCCESS`` keeps the existing success surface unchanged (WP-P12-06-03).
_PRESENTED_STATES = (GuiState.SUCCESS_WITH_WARNING, GuiState.FAILED)

#: Layout sizing for the drop area and the primary action.
DROP_ZONE_MINIMUM_HEIGHT = 180
CONVERT_MINIMUM_WIDTH = 140

#: Long-path display strategy (WP-P12-04-04 §7): the file name stays complete,
#: the containing folder is middle-elided to this many characters, and both
#: labels carry the full path as a tooltip.  The full path remains available
#: internally in ``state_model.source``.
SOURCE_PATH_MAX_CHARS = 56

#: Long-path display budget for the output folder row (WP-P12-04-06 §7).
OUTPUT_PATH_MAX_CHARS = 56


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


def _output_display_text(directory: Optional[Path]) -> str:
    """Return the output-folder display text (default: same as source)."""
    if directory is None:
        return OUTPUT_VALUE_TEXT
    return _elide_middle(str(directory), OUTPUT_PATH_MAX_CHARS)


class MainWindow(QMainWindow):
    """Main window foundation: the visible v2.0 workflow shell.

    Attributes:
        state_model: Explicit GUI state model (Qt-free).
        state: Current GUI state (read-only convenience accessor).
        output_directory: Session output-folder preference (``None`` means
            the default location).
        service: Application conversion service (GUI -> service boundary).
        worker: Worker boundary that runs the service off the GUI thread.
        latest_result: Most recent application-layer ``ConversionResult``,
            retained untouched for the P12-06 diagnostics UX.
        latest_job_failure: Most recent worker infrastructure failure, if any;
            kept distinct from application results.
        presentation: Presentation view of the most recent failure, or ``None``
            when no failure is being presented (WP-P12-06-02).
        is_conversion_active: Whether a conversion job is running or its thread
            is still cleaning up (drives the close policy).
        drop_zone: Drop-area placeholder frame.
        drop_label: Instruction text inside the drop area.
        source_label: Selected source display (hidden while EMPTY).
        source_path_label: Containing folder of the selected source.
        select_file_button: Placeholder for the file picker.
        output_value_label: Output destination display.
        change_output_button: Opens the output-folder chooser.
        convert_button: Primary action placeholder.
        status_label: Status area text.
        result_area: Container of the bounded outcome presentation.
        result_summary_label: Concise summary of the presented outcome.
        details_button: Bounded ``Details...`` affordance.
        actions_area: Container of the post-conversion output actions.
        open_document_button: Opens the retained artifact.
        open_folder_button: Opens the folder containing the retained artifact.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Build the window shell.

        Args:
            parent: Optional Qt parent widget.
        """
        super().__init__(parent)
        self.state_model = GuiStateModel()
        self._output_directory: Optional[Path] = None
        self._latest_result: Optional[ConversionResult] = None
        self._latest_job_failure: Optional[JobFailure] = None
        self._presentation: Optional[Presentation] = None
        self.service = ConversionService()
        self.worker = GuiWorker(self)
        self.worker.succeeded.connect(self._on_conversion_result)
        self.worker.failed.connect(self._on_conversion_failure)
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
        self.result_area = self._create_result_area(central)
        layout.addWidget(self.result_area)
        self.actions_area = self._create_actions_area(central)
        layout.addWidget(self.actions_area)

        self.setCentralWidget(central)
        self._apply_state()

    @property
    def state(self) -> GuiState:
        """Return the current GUI state."""
        return self.state_model.state

    @property
    def output_directory(self) -> Optional[Path]:
        """Return the session output-folder preference.

        ``None`` means the default presentation "Default location"
        (WP-P12-05-03): the GUI does not compute a DOCX path from it.
        """
        return self._output_directory

    @property
    def latest_result(self) -> Optional[ConversionResult]:
        """Return the most recent application-layer conversion result.

        The complete result - diagnostics, warnings, errors, quality-gate
        evidence and output path - is retained untouched for the P12-06
        diagnostics UX (WP-P12-05-04 §5).
        """
        return self._latest_result

    @property
    def latest_job_failure(self) -> Optional[JobFailure]:
        """Return the most recent worker infrastructure failure, if any.

        Worker failures keep their own semantics: they are never converted into
        a fabricated ``ConversionResult`` and never overwrite
        :attr:`latest_result`.
        """
        return self._latest_job_failure

    @property
    def presentation(self) -> Optional[Presentation]:
        """Return the presentation view of the most recent completion.

        The value comes from the WP-P12-06-01 presentation model
        (:func:`~md_converter.gui.presentation_model.present_result` /
        :func:`~md_converter.gui.presentation_model.present_job_failure`); the
        window never builds title, summary, count or severity wording itself.
        ``None`` means no completion yet or the outcome presentation was cleared
        by a new workflow.
        """
        return self._presentation

    @property
    def is_conversion_active(self) -> bool:
        """Whether a conversion job is running or still cleaning up.

        The worker boundary is the source of truth: a real conversion always has
        an active job, and ``worker.is_running`` stays ``True`` until the job
        thread has exited and its references were released.  The P12-04 mock
        ``request_convert()`` transition has no job, so it does not block
        closing (WP-P12-05-05 §4).
        """
        return self.worker.is_running

    def closeEvent(self, event: QCloseEvent) -> None:
        """Refuse to close while a conversion is active (WP-P12-05-05 §4).

        Bounded policy: the close request is simply rejected while the
        conversion runs, so no Qt thread or worker object is destroyed
        underneath it.  After the conversion completes and the worker is idle,
        a later close succeeds normally.  No cancellation framework and no
        forced thread termination are involved.

        Args:
            event: Qt close event.
        """
        if self.is_conversion_active:
            event.ignore()
            return
        event.accept()

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
        state = self.state_model.set_source(source)
        if state in (GuiState.READY, GuiState.EMPTY):
            # A new workflow begins: the outcome presentation is cleared while
            # the retained evidence stays available (WP-P12-06-02/03).
            self._presentation = None
        return self._apply_state()

    def reset(self) -> GuiState:
        """Clear the selection and return to ``EMPTY``.

        Returns:
            GuiState: The state after the request.
        """
        state = self.state_model.reset()
        if state is GuiState.EMPTY:
            self._presentation = None
        return self._apply_state()

    def choose_source(self) -> GuiState:
        """Open the Markdown file dialog and apply the chosen source.

        The dialog result is applied through :meth:`set_source_file`, so the
        picker and drag & drop share one validation and state path.
        Cancelling the dialog keeps the current selection, and an invalid
        selection is rejected without entering ``READY`` (user-facing error UX
        belongs to a later work package).

        Returns:
            GuiState: The state after the request.
        """
        chosen = file_picker.ask_for_markdown_source(self)
        if chosen is None:
            return self.state
        return self.set_source_file(chosen)

    def set_source_file(self, path: Optional[Union[str, Path]]) -> GuiState:
        """Validate ``path`` and apply it as the selected source.

        This is the shared source-selection entry point for the file picker and
        for drag & drop (WP-P12-04-05 §4): one validation rule, one source
        display, one state transition.

        Args:
            path: Candidate source path (typically a local ``.md`` file).

        Returns:
            GuiState: The state after the request; unchanged when the candidate
            is not selectable.
        """
        validated = file_picker.validate_markdown_source(path)
        if validated is None:
            return self.state
        return self.set_source(str(validated))

    def set_output_directory(self, directory: Optional[Union[str, Path]]) -> Optional[Path]:
        """Validate ``directory`` and remember it for this session.

        Args:
            directory: Candidate output folder.

        Returns:
            Optional[Path]: The stored preference, or the unchanged preference
            when the candidate is not a usable directory.  Nothing is persisted
            beyond the current session (WP-P12-04-06 §4).
        """
        if not self.state_model.effect.change_output_enabled:
            # Output changes are unavailable in this state (CONVERTING): reuse
            # the state-model effect instead of a second lock (WP-P12-05-05 §3).
            return self._output_directory

        validated = file_picker.validate_output_directory(directory)
        if validated is None:
            return self._output_directory
        self._output_directory = validated
        self._apply_state()
        return self._output_directory

    def choose_output_directory(self) -> Optional[Path]:
        """Open the standard directory chooser and apply the chosen folder.

        Cancelling keeps the current choice (WP-P12-04-06 §7).

        Returns:
            Optional[Path]: The output-folder preference after the request.
        """
        chosen = file_picker.ask_for_output_directory(self, self._output_directory)
        if chosen is None:
            return self._output_directory
        return self.set_output_directory(chosen)

    def _set_drop_hover(self, active: bool) -> None:
        """Show transient drag-over feedback in the drop area hint.

        Args:
            active: ``True`` while a valid file hovers the drop area.
        """
        self.drop_label.setText(DROP_RELEASE_HINT_TEXT if active else DROP_HINT_TEXT)

    def request_convert(self) -> GuiState:
        """Request conversion, moving ``READY`` -> ``CONVERTING``.

        The request is rejected (state unchanged) from every other state, which
        prevents duplicate starts while converting.  This is the state-model
        transition only; the real Convert action is :meth:`start_conversion`.

        Returns:
            GuiState: The state after the request.
        """
        self.state_model.request_convert()
        return self._apply_state()

    def start_conversion(self) -> GuiState:
        """Run the real Convert action for the current selections.

        Flow (WP-P12-05-03 §3): ``READY`` -> ``CONVERTING`` -> one
        ``ConversionRequest`` from the shared request builder -> exactly one
        worker job running ``ConversionService.convert`` outside the GUI thread.
        The GUI leaves ``CONVERTING`` when the job's outcome arrives.

        Returns:
            GuiState: The state after the request.  The state is unchanged when
            the action is unavailable (no source, not ``READY``, or a job is
            already running).
        """
        if self.state is not GuiState.READY or self.worker.is_running:
            return self.state

        request = build_conversion_request(self.state_model.source, self.output_directory)
        if request is None:
            return self.state

        # Start the job first: a refused start must not leave the GUI stuck in
        # CONVERTING.  The transition below happens synchronously, before any
        # queued completion signal can be delivered by the event loop.
        if not self.worker.start(partial(self.service.convert, request)):
            return self.state

        return self.request_convert()

    def _on_conversion_result(self, result: ConversionResult) -> None:
        """Retain and map one application-layer result, then leave ``CONVERTING``.

        The status -> state interpretation lives in
        :func:`md_converter.gui.result_mapping.gui_state_for_result`; this
        callback only stores the evidence and applies the mapped state.
        The failure presentation (WP-P12-06-02) is derived from the retained
        result by the presentation model.

        Args:
            result: Conversion outcome returned by the application service.
        """
        self._latest_result = result
        self._presentation = present_result(result)
        self.state_model.complete(gui_state_for_result(result))
        self._apply_state()

    def _on_conversion_failure(self, failure: JobFailure) -> None:
        """Retain worker failure evidence and leave ``CONVERTING``.

        Args:
            failure: Structured evidence from the worker boundary.
        """
        self._latest_job_failure = failure
        self._presentation = present_job_failure(failure)
        self.state_model.complete_failure()
        self._apply_state()

    def show_details(self) -> bool:
        """Open the bounded details surface for the presented outcome.

        The affordance follows the presentation model: it is offered only for a
        presented outcome whose presentation reports available details, and it
        always shows the retained evidence of that outcome.  The complete
        diagnostics/report view remains WP-P12-06-04.

        Returns:
            bool: ``True`` when the details surface was shown.
        """
        presentation = self._presented_presentation()
        if presentation is None or not presentation.details_available:
            return False
        evidence = self._presentation_evidence(presentation)
        if evidence is None:
            return False
        show_result_details(self, presentation, evidence)
        return True

    def _presented_presentation(self) -> Optional[Presentation]:
        """Return the presentation currently shown in the result area.

        Returns:
            Optional[Presentation]: The presentation for a state that exposes
            outcome details, otherwise ``None`` (for example a plain
            ``SUCCESS``, whose surface is unchanged by WP-P12-06-03).
        """
        if self.state_model.state not in _PRESENTED_STATES:
            return None
        return self._presentation

    def _presentation_evidence(self, presentation: Presentation) -> Optional[object]:
        """Return the retained evidence the given presentation describes."""
        if presentation.is_infrastructure_failure:
            return self._latest_job_failure
        return self._latest_result

    def _actionable_output_path(self) -> Optional[Path]:
        """Return the retained artifact path when the output actions are eligible.

        The path is the retained ``ConversionResult.output_path``, used verbatim:
        it is never rebuilt from the source name, the output-folder preference,
        configuration or a guessed output name.  Eligibility comes from the
        presentation model, which only marks successful outcomes with an
        existing artifact as actionable - so failures and infrastructure
        failures fail closed.

        Returns:
            Optional[Path]: The retained artifact path, or ``None`` when the
            actions are not eligible.
        """
        presentation = self._presentation
        if presentation is None or not presentation.output_actionable:
            return None
        result = self._latest_result
        if result is None or result.output_path is None:
            return None
        return result.output_path

    def open_output_document(self) -> bool:
        """Open the retained output document.

        Returns:
            bool: ``True`` when the platform accepted the request.  A missing
            artifact fails safely with a concise local message and never
            triggers another conversion.
        """
        return self._run_output_action(open_document)

    def open_output_folder(self) -> bool:
        """Open the folder containing the retained output document.

        Returns:
            bool: ``True`` when the platform accepted the request.  A missing
            artifact fails safely with a concise local message and never
            triggers another conversion.
        """
        return self._run_output_action(open_folder)

    def _run_output_action(self, action: Callable[[Path], bool]) -> bool:
        """Run one output action against the retained artifact path.

        Args:
            action: Platform launch helper from
                :mod:`md_converter.gui.output_actions`.

        Returns:
            bool: ``True`` when the platform opened the target.
        """
        path = self._actionable_output_path()
        if path is None:
            return False
        if action(path):
            return True
        notify_missing_artifact(self, path)
        return False

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
        (WP-P12-04-03 §7), including the output-folder display and the
        availability of the Change control (WP-P12-04-06), and the bounded
        outcome presentation (WP-P12-06-02/03).

        Returns:
            GuiState: The current GUI state.
        """
        effect = self.state_model.effect
        self.convert_button.setEnabled(effect.convert_enabled)
        self.select_file_button.setEnabled(effect.select_enabled)
        self.drop_zone.setEnabled(effect.drop_enabled)
        self.drop_zone.setAcceptDrops(effect.drop_enabled)
        self.change_output_button.setEnabled(effect.change_output_enabled)
        source = self.state_model.source
        self.source_label.setText(_source_display_name(source))
        self.source_label.setToolTip(source or "")
        self.source_label.setVisible(effect.source_visible)
        folder_text = _source_display_folder(source)
        self.source_path_label.setText(folder_text)
        self.source_path_label.setToolTip(source or "")
        self.source_path_label.setVisible(effect.source_visible and bool(folder_text))
        self.output_value_label.setText(_output_display_text(self._output_directory))
        self.output_value_label.setToolTip(
            str(self._output_directory) if self._output_directory is not None else ""
        )
        self.status_label.setText(effect.status_text)
        self._apply_result_state()
        self._apply_output_actions()
        return self.state_model.state

    def _apply_result_state(self) -> None:
        """Apply the bounded outcome presentation to the result-area widgets.

        This is part of the single :meth:`_apply_state` write path
        (WP-P12-06-02/03).  The area appears for the presented states
        (``SUCCESS_WITH_WARNING`` and ``FAILED``) only; a plain ``SUCCESS``
        keeps its existing surface.  The summary text and the ``Details...``
        affordance come from the presentation model, never from wording built
        here, and warning evidence is never routed through failure semantics.
        """
        presentation = self._presented_presentation()
        visible = presentation is not None
        self.result_summary_label.setText(presentation.summary if presentation else "")
        self.result_area.setVisible(visible)
        details_visible = bool(presentation is not None and presentation.details_available)
        self.details_button.setVisible(details_visible)
        self.details_button.setEnabled(details_visible)

    def _apply_output_actions(self) -> None:
        """Apply the post-conversion output actions (WP-P12-06-05).

        Part of the single :meth:`_apply_state` write path.  The actions follow
        the presentation model's output eligibility: they are offered only for a
        successful outcome whose retained artifact exists, so failures and
        infrastructure failures never expose a misleading action.
        """
        available = self._actionable_output_path() is not None
        for button in (self.open_document_button, self.open_folder_button):
            button.setVisible(available)
            button.setEnabled(available)

    def _create_drop_zone(self, parent: QWidget) -> DropZone:
        """Create the drop-area placeholder (no drag & drop behavior yet).

        Args:
            parent: Parent widget for the frame.

        Returns:
            DropZone: Drop area holding the instruction text and file button.
        """
        zone = DropZone(parent)
        zone.setMinimumHeight(DROP_ZONE_MINIMUM_HEIGHT)
        zone.source_dropped.connect(self.set_source_file)
        zone.hover_changed.connect(self._set_drop_hover)

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
        """Create the output-location row (folder preference and chooser).

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
        self.change_output_button.clicked.connect(self.choose_output_directory)

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
        self.convert_button.clicked.connect(self.start_conversion)
        # Enablement is applied from the GUI state by _apply_state().

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

    def _create_result_area(self, parent: QWidget) -> QWidget:
        """Create the bounded outcome presentation area (WP-P12-06-02/03).

        The area holds the concise summary of the presented outcome and the
        ``Details...`` affordance.  It is hidden until a warning or failure is
        presented and it stays small: the full diagnostics/report surface is
        WP-P12-06-04.

        Args:
            parent: Parent widget for the container.

        Returns:
            QWidget: The result-area container.
        """
        area = QWidget(parent)
        area.setObjectName("resultArea")
        row = QHBoxLayout(area)
        row.setObjectName("resultAreaLayout")
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        self.result_summary_label = QLabel("", area)
        self.result_summary_label.setObjectName("resultSummaryLabel")
        self.result_summary_label.setWordWrap(True)
        row.addWidget(self.result_summary_label, 1)

        self.details_button = QPushButton(DETAILS_TEXT, area)
        self.details_button.setObjectName("detailsButton")
        self.details_button.clicked.connect(self.show_details)
        row.addWidget(self.details_button, 0)
        return area

    def _create_actions_area(self, parent: QWidget) -> QWidget:
        """Create the bounded post-conversion action area (WP-P12-06-05).

        The area holds ``Open Document`` and ``Open Folder``.  It is hidden
        until a successful conversion produced an artifact that still exists;
        visibility and enablement are applied by :meth:`_apply_output_actions`.

        Args:
            parent: Parent widget for the container.

        Returns:
            QWidget: The output-action container.
        """
        area = QWidget(parent)
        area.setObjectName("actionsArea")
        row = QHBoxLayout(area)
        row.setObjectName("actionsAreaLayout")
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        self.open_document_button = QPushButton(OPEN_DOCUMENT_TEXT, area)
        self.open_document_button.setObjectName("openDocumentButton")
        self.open_document_button.clicked.connect(self.open_output_document)
        self.open_folder_button = QPushButton(OPEN_FOLDER_TEXT, area)
        self.open_folder_button.setObjectName("openFolderButton")
        self.open_folder_button.clicked.connect(self.open_output_folder)

        row.addStretch(1)
        row.addWidget(self.open_document_button)
        row.addWidget(self.open_folder_button)
        row.addStretch(1)
        return area
