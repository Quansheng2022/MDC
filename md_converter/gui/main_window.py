"""Main window foundation for the MD_Converter GUI (WP-P12-04-02..06, P12-05-03).

Visible shell for the v2.0 workflow (``V2_GUI_UX_SPEC`` §3):

    drop area -> output row -> Convert -> status

Scope limits:

* conversion runs only through the application service
  (:mod:`md_converter.application`); the GUI never imports the compiler,
  parser, pipeline, renderer or QA internals (WP-P12-05-03 §5);
* no diagnostics UX framework (WP-P12-06) and only the bounded GUI-local
  preferences of WP-P12-07-01 (window geometry, last-used folders);
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

WP-P12-07-01 adds the GUI-local preferences (:mod:`md_converter.gui.preferences`):
the window restores a safely validated geometry, the file and folder choosers
start in the last-used folder, and the document's own ``output_path`` remains
the only output authority.  A remembered output folder is GUI convenience only -
it is never restored as an output override, so the approved application default
output behaviour is preserved unless the user explicitly selects a folder.

WP-P12-07-02/03 add the two bounded product surfaces behind the footer entry
points: the compact Settings dialog (:mod:`md_converter.gui.settings_dialog`)
and the read-only About / product-information dialog
(:mod:`md_converter.gui.about_dialog`).  Both are presentation plus the small
GUI-local preferences; neither starts a conversion.

SBC-02..05 add the authorized Serial Batch Conversion orchestration.  The
window keeps one ordered selection (:class:`~md_converter.gui.batch.BatchSelection`)
and drives one :class:`~md_converter.gui.batch.BatchRun` through the *existing*
single-file execution path: every source is still converted by
``ConversionService.convert`` on the worker boundary, and the next source is
started only when the previous job is terminal and the boundary is idle again
(``GuiWorker.idle``).  The window owns no conversion semantics: it records the
retained per-item evidence, presents the derived progress line, the batch
summary and the lightweight batch report, and stops the queue only for a
batch-level infrastructure problem.  A one-file selection keeps the accepted
single-file surface unchanged.
"""

from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import Callable, List, Optional, Sequence, Union

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..application.conversion_result import ConversionResult
from ..application.conversion_service import ConversionService
from . import file_picker
from .about_dialog import AboutDialog
from .batch import (
    BatchRun,
    BatchRunError,
    BatchSelection,
    source_identity,
)
from .batch_report import show_batch_report
from .drop_zone import DropZone
from .output_actions import (
    notify_missing_artifact,
    open_directory,
    open_document,
    open_folder,
)
from .preferences import GuiPreferences, available_screen_rects, geometry_is_usable
from .presentation_model import Presentation, present_job_failure, present_result
from .request_builder import build_conversion_request
from .result_details import show_result_details
from .result_mapping import gui_state_for_result
from .settings_dialog import SettingsDialog
from .state import GuiState, GuiStateModel
from .worker import GuiWorker, JobFailure

__all__ = [
    "ABOUT_TEXT",
    "ABOUT_TOOLTIP",
    "BATCH_CAPTION_TEXT",
    "BATCH_CLEAR_TEXT",
    "BATCH_COUNT_TEMPLATE",
    "BATCH_LIST_ACCESSIBLE_NAME",
    "BATCH_LIST_MINIMUM_HEIGHT",
    "BATCH_LIST_TOOLTIP",
    "BATCH_REMOVE_TEXT",
    "BATCH_STATUS_TEXT",
    "BATCH_STOPPED_NOTICE_TEXT",
    "DROP_ZONE_ACCESSIBLE_NAME",
    "DROP_ZONE_ACCESSIBLE_DESCRIPTION",
    "CHANGE_OUTPUT_TEXT",
    "CHANGE_OUTPUT_TOOLTIP",
    "CHANGE_OUTPUT_ACCESSIBLE_NAME",
    "CONVERT_MINIMUM_WIDTH",
    "CONVERT_MANY_TEMPLATE",
    "CONVERT_MANY_TOOLTIP",
    "CONVERT_TEXT",
    "CONVERT_TOOLTIP",
    "DETAILS_TEXT",
    "DETAILS_TOOLTIP",
    "DROP_HINT_TEXT",
    "DROP_RELEASE_HINT_TEXT",
    "DROP_SUB_HINT_TEXT",
    "DROP_ZONE_TOOLTIP",
    "DROP_ZONE_MINIMUM_HEIGHT",
    "FOOTER_BUTTON_MINIMUM_WIDTH",
    "LAYOUT_MARGIN_BOTTOM",
    "LAYOUT_MARGIN_HORIZONTAL",
    "LAYOUT_MARGIN_TOP",
    "LAYOUT_SPACING",
    "MINIMUM_HEIGHT",
    "MINIMUM_WIDTH",
    "MainWindow",
    "OPEN_DOCUMENT_TEXT",
    "OPEN_DOCUMENT_TOOLTIP",
    "OPEN_BATCH_FOLDER_TEXT",
    "OPEN_BATCH_FOLDER_TOOLTIP",
    "OPEN_FOLDER_TEXT",
    "OPEN_FOLDER_TOOLTIP",
    "OUTPUT_CAPTION_TEXT",
    "OUTPUT_PATH_MAX_CHARS",
    "OUTPUT_VALUE_TEXT",
    "SECONDARY_BUTTON_MINIMUM_WIDTH",
    "SELECT_FILE_TEXT",
    "SELECT_FILE_TOOLTIP",
    "SETTINGS_TEXT",
    "SETTINGS_TOOLTIP",
    "SHORTCUT_SELECT_FILE",
    "SHORTCUT_SETTINGS",
    "SOURCE_PATH_MAX_CHARS",
    "STATUS_ACCESSIBLE_NAME",
    "VIEW_BATCH_REPORT_TEXT",
    "VIEW_BATCH_REPORT_TOOLTIP",
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
DROP_HINT_TEXT = "Drop Markdown files here"
#: Secondary empty-state wording (WP-P12-07-04): what the drop area expects and
#: where the conversion happens.  No unbounded privacy claim is made.
DROP_SUB_HINT_TEXT = "Markdown files (.md) are converted on this computer."
#: Transient drag-over feedback (WP-P12-04-05 §6: "text change").
DROP_RELEASE_HINT_TEXT = "Release to add these files"
SELECT_FILE_TEXT = "Select File"
OUTPUT_CAPTION_TEXT = "Output folder:"
#: Default output presentation.  The service resolves the actual location, so
#: the wording does not promise a source-directory default (WP-P12-05-03).
OUTPUT_VALUE_TEXT = "Default location"
CHANGE_OUTPUT_TEXT = "Change"
CONVERT_TEXT = "Convert"

#: Primary-action wording for a multi-file batch (product specification §8.2).
CONVERT_MANY_TEMPLATE = "Convert {count} Files"

#: Batch selection surface (product specification §8.1/§8.2).
BATCH_CAPTION_TEXT = "Markdown Files"
BATCH_COUNT_TEMPLATE = "{count} files selected"
BATCH_REMOVE_TEXT = "Remove"
BATCH_CLEAR_TEXT = "Clear"

#: Batch completion surface (product specification §8.4).
BATCH_STATUS_TEXT = "Batch complete."
OPEN_BATCH_FOLDER_TEXT = "Open Output Folder"
VIEW_BATCH_REPORT_TEXT = "View Batch Report"

#: Bounded notice shown when a batch-level problem stopped the queue.
BATCH_STOPPED_NOTICE_TEXT = (
    "Batch stopped: the next conversion could not be started. "
    "The files that were already converted are listed below."
)

#: Bounded details affordance for presented outcomes (WP-P12-06-02/03).
DETAILS_TEXT = "Details..."

#: Bounded post-conversion output actions (WP-P12-06-05).
OPEN_DOCUMENT_TEXT = "Open Document"
OPEN_FOLDER_TEXT = "Open Folder"

#: Single Settings entry point (WP-P12-07-02).
SETTINGS_TEXT = "Settings"

#: Single About / product-information entry point (WP-P12-07-03).
ABOUT_TEXT = "About"

#: GUI states whose result presentation is shown in the result area.  A plain
#: ``SUCCESS`` keeps the existing success surface unchanged (WP-P12-06-03).
_PRESENTED_STATES = (GuiState.SUCCESS_WITH_WARNING, GuiState.FAILED)

#: Layout sizing for the drop area and the primary action.
DROP_ZONE_MINIMUM_HEIGHT = 180
CONVERT_MINIMUM_WIDTH = 140

#: Consistent minimum widths for the secondary and footer actions
#: (WP-P12-07-04: even button sizing).
SECONDARY_BUTTON_MINIMUM_WIDTH = 112
FOOTER_BUTTON_MINIMUM_WIDTH = 96

#: Layout metrics (WP-P12-07-04: one consistent margin and spacing scale).
LAYOUT_MARGIN_HORIZONTAL = 28
LAYOUT_MARGIN_TOP = 24
LAYOUT_MARGIN_BOTTOM = 20
LAYOUT_SPACING = 16

#: Short, plain-language tooltips (WP-P12-07-04).
DROP_ZONE_TOOLTIP = "Drop Markdown files (.md) here"
SELECT_FILE_TOOLTIP = "Choose the Markdown files (.md) to convert"
CHANGE_OUTPUT_TOOLTIP = "Choose where the Word document is saved"
CONVERT_TOOLTIP = "Convert the selected Markdown file to a Word document"
CONVERT_MANY_TOOLTIP = "Convert every file in the list, one after another"
DETAILS_TOOLTIP = "Show the conversion report"
OPEN_DOCUMENT_TOOLTIP = "Open the generated Word document"
OPEN_FOLDER_TOOLTIP = "Open the folder that contains the document"
OPEN_BATCH_FOLDER_TOOLTIP = "Open the folder that contains the converted documents"
VIEW_BATCH_REPORT_TOOLTIP = "Show the result of every file in this batch"
SETTINGS_TOOLTIP = "Open settings"
ABOUT_TOOLTIP = "About MD Converter"

#: Accessible names for controls whose visible text is not a complete label
#: (WP-P12-07-05).  Buttons keep their visible text as the accessible name.
DROP_ZONE_ACCESSIBLE_NAME = "Markdown file drop area"
DROP_ZONE_ACCESSIBLE_DESCRIPTION = "Drop one or more Markdown files here, or choose Select File"
STATUS_ACCESSIBLE_NAME = "Status"
CHANGE_OUTPUT_ACCESSIBLE_NAME = "Change output folder"
BATCH_LIST_ACCESSIBLE_NAME = "Markdown files in this batch"
BATCH_LIST_TOOLTIP = "Files are converted in this order"

#: Batch list surface metrics.
BATCH_LIST_MINIMUM_HEIGHT = 96

#: Two standard desktop shortcuts (WP-P12-07-05).  No configurable shortcut
#: system exists; these are the only accelerators the window installs.
SHORTCUT_SELECT_FILE = "Ctrl+O"
SHORTCUT_SETTINGS = "Ctrl+,"

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


def _validate_source(value: Union[str, Path]) -> Optional[Path]:
    """Validate one candidate through the shared GUI-boundary rule (SBC-02).

    The lookup is dynamic on purpose: the file picker, the drop area and the
    batch selection then provably apply exactly one validation rule, including
    when the rule is replaced by tooling.

    Args:
        value: Candidate source from a dialog, a drop payload or a caller.

    Returns:
        Optional[Path]: The selectable source, or ``None`` when rejected.
    """
    return file_picker.validate_markdown_source(value)


class MainWindow(QMainWindow):
    """Main window foundation: the visible v2.0 workflow shell.

    Attributes:
        state_model: Explicit GUI state model (Qt-free).
        state: Current GUI state (read-only convenience accessor).
        output_directory: Session output-folder preference (``None`` means
            the default location).
        service: Application conversion service (GUI -> service boundary).
        worker: Worker boundary that runs the service off the GUI thread.
        batch_selection: Ordered, duplicate-free selection of Markdown sources
            (SBC-02).  Its order is the execution order.
        batch_run: The active or last-finished batch, or ``None`` when no batch
            has been started for the current selection.
        latest_result: Most recent application-layer ``ConversionResult``,
            retained untouched for the P12-06 diagnostics UX.
        latest_job_failure: Most recent worker infrastructure failure, if any;
            kept distinct from application results.
        presentation: Presentation view of the most recent failure, or ``None``
            when no failure is being presented (WP-P12-06-02).
        preferences: GUI-local preference store (WP-P12-07-01).  It owns the
            window geometry and the last-used folders only.
        select_file_action: ``Ctrl+O`` accelerator for Select File
            (WP-P12-07-05).
        settings_action: ``Ctrl+,`` accelerator for Settings (WP-P12-07-05).
        is_conversion_active: Whether a conversion job is running or its thread
            is still cleaning up (drives the close policy).
        drop_zone: Drop-area placeholder frame.
        drop_label: Instruction text inside the drop area.
        drop_sub_label: Secondary empty-state wording inside the drop area.
        batch_area: Container of the multi-file selection surface (SBC-02); it
            appears when two or more files are selected.
        batch_list: Ordered list of the selected files with per-file status.
        batch_count_label: "3 files selected" summary of the selection.
        batch_remove_button: Removes the highlighted entries.
        batch_clear_button: Clears the whole selection.
        notice_label: Bounded feedback for skipped or duplicate selection items.
        batch_summary_area: Container of the batch completion summary.
        batch_summary_label: Derived batch counts.
        open_batch_folder_button: Opens the batch output folder.
        view_batch_report_button: Opens the lightweight batch report.
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
        settings_button: Single Settings entry point (WP-P12-07-02).
        about_button: Single About entry point (WP-P12-07-03).
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        preferences: Optional[GuiPreferences] = None,
    ) -> None:
        """Build the window shell.

        Args:
            parent: Optional Qt parent widget.
            preferences: Optional GUI-local preference store.  Defaults to an
                isolated process-local store, so a window that was not given one
                never reads or writes the real user settings.
        """
        super().__init__(parent)
        self.state_model = GuiStateModel()
        self._output_directory: Optional[Path] = None
        self._latest_result: Optional[ConversionResult] = None
        self._latest_job_failure: Optional[JobFailure] = None
        self._presentation: Optional[Presentation] = None
        self._selection = BatchSelection(_validate_source)
        self._batch: Optional[BatchRun] = None
        self._notice_text = ""
        self.preferences = preferences if preferences is not None else GuiPreferences.session()
        self.service = ConversionService()
        self.worker = GuiWorker(self)
        self.worker.succeeded.connect(self._on_conversion_result)
        self.worker.failed.connect(self._on_conversion_failure)
        # The next source of a serial batch starts only when the previous job
        # has finished *and* the boundary is idle again (SBC-04).
        self.worker.idle.connect(self._on_worker_idle)
        self.setObjectName("MainWindow")
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(MINIMUM_WIDTH, MINIMUM_HEIGHT)
        self._restore_saved_geometry()

        central = QWidget(self)
        central.setObjectName("centralWidget")
        layout = QVBoxLayout(central)
        layout.setObjectName("mainLayout")
        layout.setContentsMargins(
            LAYOUT_MARGIN_HORIZONTAL,
            LAYOUT_MARGIN_TOP,
            LAYOUT_MARGIN_HORIZONTAL,
            LAYOUT_MARGIN_BOTTOM,
        )
        layout.setSpacing(LAYOUT_SPACING)

        self.drop_zone = self._create_drop_zone(central)
        layout.addWidget(self.drop_zone, 1)
        self.batch_area = self._create_batch_area(central)
        layout.addWidget(self.batch_area)
        layout.addLayout(self._create_output_row(central))
        layout.addLayout(self._create_convert_row(central))
        self.status_label = self._create_status_label(central)
        layout.addWidget(self.status_label)
        self.notice_label = self._create_notice_label(central)
        layout.addWidget(self.notice_label)
        self.batch_summary_area = self._create_batch_summary_area(central)
        layout.addWidget(self.batch_summary_area)
        self.result_area = self._create_result_area(central)
        layout.addWidget(self.result_area)
        self.actions_area = self._create_actions_area(central)
        layout.addWidget(self.actions_area)
        layout.addLayout(self._create_footer_row(central))

        self.setCentralWidget(central)
        self._configure_accessibility()
        self._configure_shortcuts()
        self._configure_tab_order()
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
    def batch_selection(self) -> BatchSelection:
        """Return the ordered selection of Markdown sources (SBC-02).

        The selection holds the files the user added through the picker or
        drag & drop; its order is the conversion order.  It carries no
        conversion state and no rendering state.
        """
        return self._selection

    @property
    def batch_run(self) -> Optional[BatchRun]:
        """Return the active or last-finished batch, or ``None``.

        ``None`` means no batch was started for the current selection (for
        example while the selection is being built, or after a selection
        change that cleared the previous run).
        """
        return self._batch

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

        A close that is actually accepted also stores the window geometry for
        the next launch (WP-P12-07-01).  A refused close stores nothing.

        Args:
            event: Qt close event.
        """
        if self.is_conversion_active:
            event.ignore()
            return
        self._save_geometry()
        event.accept()

    def _restore_saved_geometry(self) -> None:
        """Apply the stored window geometry, falling back to the default size.

        The stored geometry is used only when the platform restored it and the
        result is still usable on an attached screen (WP-P12-07-01 "invalid or
        off-screen geometry fails safely").  Otherwise the documented initial
        size is used and the window is placed on the first available screen, so
        a stale geometry can never hide the window.
        """
        stored = self.preferences.window_geometry()
        if stored is not None and self.restoreGeometry(stored):
            if geometry_is_usable(self.geometry(), available_screen_rects()):
                return
        self._reset_geometry()

    def _reset_geometry(self) -> None:
        """Return the window to the documented initial size and a visible spot."""
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        screens = available_screen_rects()
        if not screens:
            return
        target = screens[0]
        left = target.x() + max((target.width() - WINDOW_WIDTH) // 2, 0)
        top = target.y() + max((target.height() - WINDOW_HEIGHT) // 2, 0)
        self.move(left, top)

    def _save_geometry(self) -> None:
        """Store the current window geometry in the GUI preference store."""
        self.preferences.set_window_geometry(self.saveGeometry())
        self.preferences.sync()

    def set_source(self, source: Optional[str]) -> GuiState:
        """Select a source and return the resulting GUI state.

        This is the state-model entry point: it applies a display label and the
        ``READY``/``EMPTY`` transition, and it is what a caller that is not
        going through the file system (a mock, an embedded launcher, a test)
        should use.  The real selections arrive through
        :meth:`set_source_file` (one file) or :meth:`add_source_files` (a
        picker multi-selection or a drop payload), which keep the batch
        selection and this state model in step.

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

        The batch selection, the batch run and the bounded notice are cleared
        with it, so the window is back in the state it started in.

        Returns:
            GuiState: The state after the request.
        """
        if not self.state_model.effect.select_enabled:
            # Input mutation is unavailable while a conversion is active.
            return self.state
        state = self.state_model.reset()
        if state is GuiState.EMPTY:
            self._presentation = None
            self._selection.clear()
            self._batch = None
            self._notice_text = ""
        return self._apply_state()

    def choose_source(self) -> GuiState:
        """Open the Markdown file dialog and add the chosen sources.

        The dialog supports the authorized multi-file selection (SBC-02) and its
        result is applied through :meth:`add_source_files`, so the picker and
        drag & drop share one validation, duplicate-filtering and state path.
        Cancelling the dialog keeps the current selection.

        The dialog starts in the remembered source folder when there is one
        (WP-P12-07-01); that folder is a starting location only.

        Returns:
            GuiState: The state after the request.
        """
        if not self.state_model.effect.select_enabled:
            # The control is disabled while converting; the guard also protects
            # programmatic callers (WP-P12-05-05 §3).
            return self.state
        chosen = file_picker.ask_for_markdown_sources(self, self.preferences.last_source_directory)
        if not chosen:
            return self.state
        return self.add_source_files(chosen)

    def set_source_file(self, path: Optional[Union[str, Path]]) -> GuiState:
        """Validate ``path`` and make it the *only* selected source.

        This is the single-source entry point: it replaces the whole selection,
        which is what a caller that wants exactly one document to convert (and
        what the accepted single-file workflow) expects.  It applies the shared
        :func:`~md_converter.gui.file_picker.validate_markdown_source` rule and
        one state transition, so a rejected candidate leaves the workflow
        untouched.

        Args:
            path: Candidate source path (typically a local ``.md`` file).

        Returns:
            GuiState: The state after the request; unchanged when the candidate
            is not selectable.
        """
        validated = file_picker.validate_markdown_source(path)
        if validated is None:
            return self.state
        if not self.state_model.effect.select_enabled:
            return self.state
        # GUI convenience only (WP-P12-07-01): the containing folder becomes the
        # starting location of the next chooser.  The conversion request is
        # unaffected.
        self.preferences.remember_source_directory(validated.parent)
        self._selection.clear()
        self._selection.add((validated,))
        self._batch = None
        self._notice_text = ""
        return self._sync_selection_state()

    def add_source_files(self, paths: Optional[Sequence[Union[str, Path]]]) -> GuiState:
        """Validate and add ``paths`` to the batch selection.

        This is the shared selection path for the multi-file picker and for
        drag & drop (WP-P12-04-05 §4, SBC-02): one validation rule, one
        duplicate rule and one state transition.  Files that are not selectable
        and files that are already selected never enter the batch and never
        disturb the existing selection; the bounded notice explains what was
        skipped.

        Args:
            paths: Candidate sources, in the order they were chosen or dropped.

        Returns:
            GuiState: The state after the request; unchanged while a conversion
            is active or when nothing was offered.
        """
        candidates = list(paths or ())
        if not candidates or not self.state_model.effect.select_enabled:
            return self.state

        result = self._selection.add(candidates)
        self._notice_text = result.notice_text() or ""
        if not result.changed:
            # Nothing entered the batch: only the bounded notice changes.
            return self._apply_state()

        # GUI convenience only (WP-P12-07-01): the newest file's folder becomes
        # the next chooser's starting location.
        self.preferences.remember_source_directory(result.added[-1].parent)
        self._batch = None
        return self._sync_selection_state()

    def remove_selected_sources(self) -> GuiState:
        """Remove the highlighted entries from the batch selection (SBC-02).

        Returns:
            GuiState: The state after the request.
        """
        if not self.state_model.effect.select_enabled:
            return self.state
        paths = [row.data(Qt.ItemDataRole.UserRole) for row in self.batch_list.selectedItems()]
        selected = [path for path in paths if path]
        if not selected:
            return self.state
        removed = self._selection.remove(selected)
        count = len(removed.added)
        self._notice_text = (
            f"Removed {count} file{'' if count == 1 else 's'} from the list." if count else ""
        )
        self._batch = None
        return self._sync_selection_state()

    def clear_sources(self) -> GuiState:
        """Clear the whole batch selection (SBC-02).

        Returns:
            GuiState: The state after the request.
        """
        return self.reset()

    def source_display_labels(self) -> List[str]:
        """Return the display label of every selected source, in order.

        A file name is enough while it is unique; when two selected files share
        a name, the containing folder is added so the entries stay
        distinguishable (product specification §8.2).
        """
        sources = self._selection.sources
        names = [source.name or str(source) for source in sources]
        labels: List[str] = []
        for index, source in enumerate(sources):
            name = names[index]
            if names.count(name) > 1:
                folder = str(source.parent)
                if folder not in ("", "."):
                    labels.append(f"{name} ({_elide_middle(folder, SOURCE_PATH_MAX_CHARS)})")
                    continue
            labels.append(name)
        return labels

    def _selection_label(self) -> str:
        """Return the state-model label for the current selection.

        One file keeps its full path as the label - the accepted single-file
        display - and a multi-file selection reports its size instead.
        """
        sources = self._selection.sources
        if len(sources) == 1:
            return str(sources[0])
        return BATCH_COUNT_TEMPLATE.format(count=len(sources))

    def _sync_selection_state(self) -> GuiState:
        """Apply the state transition implied by the current selection."""
        self._presentation = None
        self.state_model.set_source(self._selection_label())
        return self._apply_state()

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
        # GUI convenience only (WP-P12-07-01): remember the folder as the next
        # chooser's starting location.  It is not restored as an output override.
        self.preferences.remember_output_directory(validated)
        self._apply_state()
        return self._output_directory

    def choose_output_directory(self) -> Optional[Path]:
        """Open the standard directory chooser and apply the chosen folder.

        Cancelling keeps the current choice (WP-P12-04-06 §7).

        The chooser starts in the current session choice, or in the remembered
        output folder when no folder was chosen in this session
        (WP-P12-07-01).

        Returns:
            Optional[Path]: The output-folder preference after the request.
        """
        start = self._output_directory or self.preferences.last_output_directory
        chosen = file_picker.ask_for_output_directory(self, start)
        if chosen is None:
            return self._output_directory
        return self.set_output_directory(chosen)

    def _set_drop_hover(self, active: bool) -> None:
        """Show transient drag-over feedback in the drop area hint.

        Args:
            active: ``True`` while a valid file hovers the drop area.
        """
        self.drop_label.setText(DROP_RELEASE_HINT_TEXT if active else DROP_HINT_TEXT)

    def _configure_accessibility(self) -> None:
        """Give the important controls a meaningful accessible identity.

        Bounded baseline only (WP-P12-07-05): controls whose visible text is not
        a complete label get an accessible name (and, for the drop area, a short
        description).  No generalized accessibility framework is built.
        """
        self.drop_zone.setAccessibleName(DROP_ZONE_ACCESSIBLE_NAME)
        self.drop_zone.setAccessibleDescription(DROP_ZONE_ACCESSIBLE_DESCRIPTION)
        self.drop_label.setAccessibleName(DROP_ZONE_ACCESSIBLE_NAME)
        self.select_file_button.setAccessibleName(SELECT_FILE_TEXT)
        self.source_label.setAccessibleName("Selected Markdown file")
        self.source_path_label.setAccessibleName("Selected file folder")
        self.output_value_label.setAccessibleName("Output folder")
        self.change_output_button.setAccessibleName(CHANGE_OUTPUT_ACCESSIBLE_NAME)
        self.convert_button.setAccessibleName(CONVERT_TEXT)
        self.status_label.setAccessibleName(STATUS_ACCESSIBLE_NAME)
        self.notice_label.setAccessibleName("Selection notice")
        self.batch_list.setAccessibleName(BATCH_LIST_ACCESSIBLE_NAME)
        self.batch_remove_button.setAccessibleName(BATCH_REMOVE_TEXT)
        self.batch_clear_button.setAccessibleName(BATCH_CLEAR_TEXT)
        self.batch_summary_label.setAccessibleName("Batch summary")
        self.open_batch_folder_button.setAccessibleName(OPEN_BATCH_FOLDER_TEXT)
        self.view_batch_report_button.setAccessibleName(VIEW_BATCH_REPORT_TEXT)
        self.details_button.setAccessibleName(DETAILS_TEXT)
        self.open_document_button.setAccessibleName(OPEN_DOCUMENT_TEXT)
        self.open_folder_button.setAccessibleName(OPEN_FOLDER_TEXT)
        self.settings_button.setAccessibleName(SETTINGS_TEXT)
        self.about_button.setAccessibleName(ABOUT_TEXT)

    def _configure_shortcuts(self) -> None:
        """Install the two bounded window shortcuts (WP-P12-07-05).

        ``Ctrl+O`` opens the Markdown picker and ``Ctrl+,`` opens Settings.
        Both reuse the existing actions, so nothing about the workflow changes.
        """
        self.select_file_action = QAction(self)
        self.select_file_action.setObjectName("selectFileAction")
        self.select_file_action.setShortcut(QKeySequence(SHORTCUT_SELECT_FILE))
        self.select_file_action.setShortcutContext(Qt.ShortcutContext.WindowShortcut)
        self.select_file_action.setEnabled(True)
        self.select_file_action.triggered.connect(self.choose_source)
        self.addAction(self.select_file_action)

        self.settings_action = QAction(self)
        self.settings_action.setObjectName("settingsAction")
        self.settings_action.setShortcut(QKeySequence(SHORTCUT_SETTINGS))
        self.settings_action.setShortcutContext(Qt.ShortcutContext.WindowShortcut)
        self.settings_action.setEnabled(True)
        self.settings_action.triggered.connect(self.open_settings)
        self.addAction(self.settings_action)

    def _configure_tab_order(self) -> None:
        """Set the logical Tab order of the window (WP-P12-07-05).

        The order follows the workflow - choose a file, choose the output
        folder, convert, inspect the result, then the product surfaces - instead
        of the widget creation order.
        """
        chain = (
            self.select_file_button,
            self.batch_list,
            self.batch_remove_button,
            self.batch_clear_button,
            self.change_output_button,
            self.convert_button,
            self.details_button,
            self.open_document_button,
            self.open_folder_button,
            self.open_batch_folder_button,
            self.view_batch_report_button,
            self.settings_button,
            self.about_button,
        )
        for index, current in enumerate(chain[:-1]):
            self.setTabOrder(current, chain[index + 1])

    def open_settings(self) -> bool:
        """Open the compact Settings surface (WP-P12-07-02).

        The dialog edits the GUI-local preferences only.  Opening or saving it
        never starts a conversion and never changes the current selections; the
        effects of a saved change (the remembered folders) apply to the next
        dialog the user opens.

        Returns:
            bool: ``True`` when the user saved, ``False`` when the edits were
            discarded (Cancel or ``Esc``).
        """
        dialog = SettingsDialog(self.preferences, self)
        return dialog.exec() == QDialog.DialogCode.Accepted

    def show_about(self) -> None:
        """Open the read-only About / product-information surface (WP-P12-07-03).

        The surface is informational: it starts no conversion, reads no
        document and makes no network request.
        """
        AboutDialog(self).exec()

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

        Flow (WP-P12-05-03 §3, SBC-03/04): ``READY`` -> ``CONVERTING`` -> one
        serial :class:`~md_converter.gui.batch.BatchRun` whose items are each
        converted by exactly the accepted single-file path - one
        ``ConversionRequest`` from the shared request builder, one worker job
        running ``ConversionService.convert`` outside the GUI thread, and the
        next source only after the previous job is terminal and the boundary is
        idle again.

        A one-file selection is a batch of one and keeps the accepted
        single-file completion surface.

        Returns:
            GuiState: The state after the request.  The state is unchanged when
            the action is unavailable (no source, not ``READY``, or a job is
            already running).
        """
        if self.state is not GuiState.READY or self.worker.is_running:
            return self.state

        sources = self._selection.sources
        if not sources:
            return self.state

        run = BatchRun(sources)
        first = run.begin()
        if first is None:
            return self.state

        request = build_conversion_request(str(first), self.output_directory)
        if request is None:
            # A validated source always yields a request; never fabricate one.
            return self.state

        # Start the job first: a refused start must not leave the GUI stuck in
        # CONVERTING.  The transition below happens synchronously, before any
        # queued completion signal can be delivered by the event loop.
        if not self.worker.start(partial(self.service.convert, request)):
            return self.state

        self._batch = run
        self._notice_text = ""
        return self.request_convert()

    def _on_conversion_result(self, result: ConversionResult) -> None:
        """Retain and map one application-layer result, then leave ``CONVERTING``.

        The status -> state interpretation lives in
        :func:`md_converter.gui.result_mapping.gui_state_for_result`; this
        callback only stores the evidence and applies the mapped state.
        The failure presentation (WP-P12-06-02) is derived from the retained
        result by the presentation model.

        In a serial batch the result is recorded against the item that was
        converting; the next source is started from
        :meth:`_on_worker_idle` once the boundary is reusable (SBC-04).

        Args:
            result: Conversion outcome returned by the application service.
        """
        self._latest_result = result
        run = self._batch
        if run is not None and run.is_running:
            run.record_result(result)
            self._apply_state()
            return

        # Defensive path: a result without an active batch is still retained,
        # mapped and reported through the accepted single-file semantics.
        self._presentation = present_result(result)
        self.state_model.complete(gui_state_for_result(result))
        self._apply_state()

    def _on_conversion_failure(self, failure: JobFailure) -> None:
        """Retain worker failure evidence and leave ``CONVERTING``.

        An item-level worker failure keeps its own semantics: it is recorded as
        a failed item and the batch continues, because the boundary itself is
        proven reusable (the next source is started from
        :meth:`_on_worker_idle`).

        Args:
            failure: Structured evidence from the worker boundary.
        """
        self._latest_job_failure = failure
        run = self._batch
        if run is not None and run.is_running:
            run.record_failure(failure)
            self._apply_state()
            return

        self._presentation = present_job_failure(failure)
        self.state_model.complete_failure()
        self._apply_state()

    def _on_worker_idle(self) -> None:
        """Advance the serial batch once the worker boundary is reusable.

        The worker emits ``idle`` after the job's thread has exited and its
        references were released, so this is the only place where the next
        source may be started.  Together with :meth:`BatchRun.next_source` this
        keeps the invariant ``active conversions <= 1``.
        """
        run = self._batch
        if run is None or not run.is_running:
            return

        try:
            run.next_source()  # marks the next pending item as converting
        except BatchRunError:
            # The serial invariant was violated by a caller: fail closed by
            # stopping the queue instead of starting an overlapping job.
            run.abort("the next conversion could not be started")
            self._notice_text = BATCH_STOPPED_NOTICE_TEXT
            self._finish_batch(run)
            return
        current = run.current_source
        if current is None:
            self._finish_batch(run)
            return

        if not self._start_batch_job(current):
            run.abort("the next conversion could not be started")
            self._notice_text = BATCH_STOPPED_NOTICE_TEXT
            self._finish_batch(run)
            return

        self._apply_state()

    def _start_batch_job(self, source: Path) -> bool:
        """Start exactly one worker job for ``source``.

        Args:
            source: The batch item the job belongs to.

        Returns:
            bool: ``True`` when the job started.
        """
        request = build_conversion_request(str(source), self.output_directory)
        if request is None:
            return False
        return bool(self.worker.start(partial(self.service.convert, request)))

    def _finish_batch(self, run: BatchRun) -> None:
        """Apply the terminal presentation of a finished or stopped batch.

        A one-file batch keeps the accepted single-file completion semantics
        (``SUCCESS`` / ``SUCCESS_WITH_WARNING`` / ``FAILED``) and its result
        surface.  A multi-file batch returns the workflow to ``READY`` and
        presents the derived batch summary instead, so no single item is
        presented as if it were the whole result.

        Args:
            run: The batch that just stopped running.
        """
        self._batch = run
        if run.total == 1 and not run.aborted:
            item = run.items[0]
            if item.failure is not None:
                self._latest_job_failure = item.failure
                self._presentation = present_job_failure(item.failure)
                self.state_model.complete_failure()
            elif item.result is not None:
                self._latest_result = item.result
                self._presentation = present_result(item.result)
                self.state_model.complete(gui_state_for_result(item.result))
            else:
                self._presentation = None
                self.state_model.complete_batch()
        else:
            # The batch summary is the terminal presentation; no single item
            # presentation is exposed as the batch outcome.
            self._presentation = None
            self.state_model.complete_batch()
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

    def open_batch_output_folder(self) -> bool:
        """Open the authoritative output folder of the last batch (SBC-05).

        The folder is the one retained by
        :attr:`md_converter.gui.batch.BatchRun.output_directory`, which is
        derived from the first produced document - never guessed from a source
        name or from the folder preference.  A batch that produced nothing
        fails closed and never triggers another conversion.

        Returns:
            bool: ``True`` when the platform accepted the request.
        """
        run = self._batch
        if run is None:
            return False
        directory = run.output_directory
        if directory is None:
            return False
        if open_directory(directory):
            return True
        notify_missing_artifact(self, directory)
        return False

    def show_batch_report(self) -> bool:
        """Open the lightweight batch report of the last batch (SBC-05).

        Returns:
            bool: ``True`` when the report surface was shown.
        """
        run = self._batch
        if run is None:
            return False
        show_batch_report(self, run)
        return True

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
        outcome presentation (WP-P12-06-02/03).  The batch surfaces (SBC-02/05)
        are applied here as well: the selection list, the bounded notice, the
        progress line and the batch summary are all derived from the retained
        selection and batch state, never patched from elsewhere.

        Returns:
            GuiState: The current GUI state.
        """
        effect = self.state_model.effect
        self.convert_button.setEnabled(effect.convert_enabled)
        self.select_file_button.setEnabled(effect.select_enabled)
        self.drop_zone.setEnabled(effect.drop_enabled)
        self.drop_zone.setAcceptDrops(effect.drop_enabled)
        self.change_output_button.setEnabled(effect.change_output_enabled)
        self._apply_selection_surface(effect.select_enabled)
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
        self.status_label.setText(self._status_text(effect.status_text))
        self.notice_label.setText(self._notice_text)
        self.notice_label.setVisible(bool(self._notice_text))
        self._apply_batch_summary()
        self._apply_result_state()
        self._apply_output_actions()
        return self.state_model.state

    def _status_text(self, state_text: str) -> str:
        """Return the status line, preferring live batch information.

        The batch layer supplies the progress line while a serial batch runs and
        the derived summary line when it finished, because a batch aggregates
        several independent results and has no single completion state.  Every
        other state keeps the accepted state-model wording.

        Args:
            state_text: Status wording of the current GUI state.

        Returns:
            str: The status line to display.
        """
        run = self._batch
        if run is None:
            return state_text
        if run.is_running:
            return run.progress_text()
        if run.total > 1 and (run.processed or run.aborted):
            return run.status_line()
        return state_text

    def _apply_selection_surface(self, input_enabled: bool) -> None:
        """Apply the batch selection surface (SBC-02).

        Part of the single :meth:`_apply_state` write path.  The surface appears
        once the workflow is a batch (two or more files), so a one-file
        selection keeps the accepted single-file surface.  Mutation is gated by
        the shared state effect ``select_enabled``, which is exactly the flag
        that already protects source changes during ``CONVERTING``.

        Args:
            input_enabled: Whether source input may be changed right now.
        """
        total = self._selection.total
        visible = total >= 2
        self.batch_area.setVisible(visible)
        self.batch_count_label.setText(BATCH_COUNT_TEMPLATE.format(count=total))
        self._render_batch_list()
        self.batch_list.setEnabled(input_enabled)
        self.batch_remove_button.setEnabled(input_enabled and bool(self.batch_list.selectedItems()))
        self.batch_clear_button.setEnabled(input_enabled and total > 0)
        self.convert_button.setText(
            CONVERT_TEXT if total <= 1 else CONVERT_MANY_TEMPLATE.format(count=total)
        )

    def _render_batch_list(self) -> None:
        """Render the selection list with the per-file batch status.

        The rows come from the ordered selection; when a batch exists, the
        matching item supplies the marker and the status word.  The highlight is
        preserved across a refresh by source identity, so a rebuild cannot move
        the user's place in the list.
        """
        highlighted = {
            source_identity(row.data(Qt.ItemDataRole.UserRole))
            for row in self.batch_list.selectedItems()
        }
        labels = self.source_display_labels()
        run = self._batch
        items_by_identity = (
            {source_identity(item.source_path): item for item in run.items}
            if run is not None
            else {}
        )
        show_status = run is not None and (run.is_running or bool(run.processed))

        self.batch_list.clear()
        sources = self._selection.sources
        for index, source in enumerate(sources):
            label = labels[index]
            item = items_by_identity.get(source_identity(source))
            if show_status and item is not None:
                text = f"{item.marker} {label} \u2014 {item.state_word}"
            else:
                text = label
            row = QListWidgetItem(text)
            row.setData(Qt.ItemDataRole.UserRole, str(source))
            row.setToolTip(str(source))
            self.batch_list.addItem(row)
            if source_identity(source) in highlighted:
                row.setSelected(True)

    def _apply_batch_summary(self) -> None:
        """Apply the batch completion summary (SBC-05).

        Part of the single :meth:`_apply_state` write path.  The summary counts
        are read from the batch run, which derives every count from the recorded
        per-file statuses.  A one-file batch keeps the accepted single-file
        completion surface and shows no summary.
        """
        run = self._batch
        visible = bool(
            run is not None
            and run.total > 1
            and not run.is_running
            and (run.is_complete or run.aborted)
        )
        self.batch_summary_area.setVisible(visible)
        self.batch_summary_label.setText(run.summary_text() if visible and run else "")
        folder_available = bool(visible and run is not None and run.output_directory is not None)
        for button, available in (
            (self.open_batch_folder_button, folder_available),
            (self.view_batch_report_button, visible),
        ):
            button.setVisible(visible)
            button.setEnabled(available)

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
        zone.setToolTip(DROP_ZONE_TOOLTIP)
        zone.sources_dropped.connect(self.add_source_files)
        zone.hover_changed.connect(self._set_drop_hover)

        zone_layout = QVBoxLayout(zone)
        zone_layout.setObjectName("dropZoneLayout")
        zone_layout.setSpacing(10)
        zone_layout.setContentsMargins(16, 16, 16, 16)
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

        # Secondary empty-state wording (WP-P12-07-04).  It stays visible with a
        # selection as well, where it describes what the drop area accepts.
        self.drop_sub_label = QLabel(DROP_SUB_HINT_TEXT, zone)
        self.drop_sub_label.setObjectName("dropSubLabel")
        self.drop_sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_sub_label.setWordWrap(True)
        zone_layout.addWidget(self.drop_sub_label)

        # File-picker behavior is implemented by WP-P12-04-04; button
        # enablement is applied from the GUI state by _apply_state().
        self.select_file_button = QPushButton(SELECT_FILE_TEXT, zone)
        self.select_file_button.setObjectName("selectFileButton")
        self.select_file_button.setMinimumWidth(SECONDARY_BUTTON_MINIMUM_WIDTH)
        self.select_file_button.setToolTip(SELECT_FILE_TOOLTIP)
        self.select_file_button.clicked.connect(self.choose_source)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        button_row.addWidget(self.select_file_button)
        button_row.addStretch(1)
        zone_layout.addLayout(button_row)
        zone_layout.addStretch(1)
        return zone

    def _create_batch_area(self, parent: QWidget) -> QWidget:
        """Create the multi-file selection surface (SBC-02).

        The surface lists the selected Markdown files in execution order and
        offers the two bounded list operations (Remove / Clear).  It is hidden
        for an empty or single-file selection, so the accepted single-file
        workflow keeps its simple surface (product specification §33).

        Args:
            parent: Parent widget for the container.

        Returns:
            QWidget: The batch selection container.
        """
        area = QWidget(parent)
        area.setObjectName("batchArea")
        layout = QVBoxLayout(area)
        layout.setObjectName("batchAreaLayout")
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        caption_row = QHBoxLayout()
        caption_row.setObjectName("batchCaptionRow")
        self.batch_caption_label = QLabel(BATCH_CAPTION_TEXT, area)
        self.batch_caption_label.setObjectName("batchCaptionLabel")
        self.batch_count_label = QLabel("", area)
        self.batch_count_label.setObjectName("batchCountLabel")
        caption_row.addWidget(self.batch_caption_label)
        caption_row.addStretch(1)
        caption_row.addWidget(self.batch_count_label)
        layout.addLayout(caption_row)

        self.batch_list = QListWidget(area)
        self.batch_list.setObjectName("batchList")
        self.batch_list.setMinimumHeight(BATCH_LIST_MINIMUM_HEIGHT)
        self.batch_list.setToolTip(BATCH_LIST_TOOLTIP)
        self.batch_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.batch_list.itemSelectionChanged.connect(self._on_batch_selection_changed)
        layout.addWidget(self.batch_list)

        button_row = QHBoxLayout()
        button_row.setObjectName("batchButtonRow")
        self.batch_remove_button = QPushButton(BATCH_REMOVE_TEXT, area)
        self.batch_remove_button.setObjectName("batchRemoveButton")
        self.batch_remove_button.setMinimumWidth(SECONDARY_BUTTON_MINIMUM_WIDTH)
        self.batch_remove_button.clicked.connect(self.remove_selected_sources)
        self.batch_clear_button = QPushButton(BATCH_CLEAR_TEXT, area)
        self.batch_clear_button.setObjectName("batchClearButton")
        self.batch_clear_button.setMinimumWidth(SECONDARY_BUTTON_MINIMUM_WIDTH)
        self.batch_clear_button.clicked.connect(self.clear_sources)
        button_row.addStretch(1)
        button_row.addWidget(self.batch_remove_button)
        button_row.addWidget(self.batch_clear_button)
        layout.addLayout(button_row)
        return area

    def _create_notice_label(self, parent: QWidget) -> QLabel:
        """Create the bounded notice line (SBC-02).

        The line reports what a selection attempt did with skipped or duplicate
        items.  It stays hidden while there is nothing to say, so it never
        becomes a second status area.

        Args:
            parent: Parent widget for the label.

        Returns:
            QLabel: The notice label.
        """
        label = QLabel("", parent)
        label.setObjectName("noticeLabel")
        label.setWordWrap(True)
        label.setVisible(False)
        return label

    def _create_batch_summary_area(self, parent: QWidget) -> QWidget:
        """Create the batch completion summary (SBC-05).

        The area shows the derived counts and the two batch-level actions from
        the product specification §8.4.  It deliberately offers no single
        batch-level "Open Document" action, because a batch has several
        documents.

        Args:
            parent: Parent widget for the container.

        Returns:
            QWidget: The batch summary container.
        """
        area = QWidget(parent)
        area.setObjectName("batchSummaryArea")
        layout = QVBoxLayout(area)
        layout.setObjectName("batchSummaryLayout")
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.batch_summary_label = QLabel("", area)
        self.batch_summary_label.setObjectName("batchSummaryLabel")
        self.batch_summary_label.setWordWrap(True)
        layout.addWidget(self.batch_summary_label)

        button_row = QHBoxLayout()
        button_row.setObjectName("batchSummaryButtonRow")
        self.open_batch_folder_button = QPushButton(OPEN_BATCH_FOLDER_TEXT, area)
        self.open_batch_folder_button.setObjectName("openBatchFolderButton")
        self.open_batch_folder_button.setToolTip(OPEN_BATCH_FOLDER_TOOLTIP)
        self.open_batch_folder_button.clicked.connect(self.open_batch_output_folder)
        self.view_batch_report_button = QPushButton(VIEW_BATCH_REPORT_TEXT, area)
        self.view_batch_report_button.setObjectName("viewBatchReportButton")
        self.view_batch_report_button.setToolTip(VIEW_BATCH_REPORT_TOOLTIP)
        self.view_batch_report_button.clicked.connect(self.show_batch_report)
        button_row.addStretch(1)
        button_row.addWidget(self.open_batch_folder_button)
        button_row.addWidget(self.view_batch_report_button)
        button_row.addStretch(1)
        layout.addLayout(button_row)
        return area

    def _on_batch_selection_changed(self) -> None:
        """Refresh the Remove affordance when the highlighted entries change."""
        self.batch_remove_button.setEnabled(
            self.state_model.effect.select_enabled and bool(self.batch_list.selectedItems())
        )

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
        self.change_output_button.setMinimumWidth(SECONDARY_BUTTON_MINIMUM_WIDTH)
        self.change_output_button.setToolTip(CHANGE_OUTPUT_TOOLTIP)
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
        self.convert_button.setToolTip(CONVERT_TOOLTIP)
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
        self.details_button.setToolTip(DETAILS_TOOLTIP)
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
        self.open_document_button.setToolTip(OPEN_DOCUMENT_TOOLTIP)
        self.open_document_button.clicked.connect(self.open_output_document)
        self.open_folder_button = QPushButton(OPEN_FOLDER_TEXT, area)
        self.open_folder_button.setObjectName("openFolderButton")
        self.open_folder_button.setToolTip(OPEN_FOLDER_TOOLTIP)
        self.open_folder_button.clicked.connect(self.open_output_folder)

        row.addStretch(1)
        row.addWidget(self.open_document_button)
        row.addWidget(self.open_folder_button)
        row.addStretch(1)
        return area

    def _create_footer_row(self, parent: QWidget) -> QHBoxLayout:
        """Create the secondary entry-point row (WP-P12-07-02/03).

        The footer keeps product-level entry points out of the primary
        workflow: the Markdown -> DOCX job stays the centre of the window.

        Args:
            parent: Parent widget for the buttons.

        Returns:
            QHBoxLayout: The footer row.
        """
        row = QHBoxLayout()
        row.setObjectName("footerRow")
        row.setSpacing(8)

        self.settings_button = QPushButton(SETTINGS_TEXT, parent)
        self.settings_button.setObjectName("settingsButton")
        self.settings_button.setMinimumWidth(FOOTER_BUTTON_MINIMUM_WIDTH)
        self.settings_button.setToolTip(SETTINGS_TOOLTIP)
        self.settings_button.clicked.connect(self.open_settings)
        self.about_button = QPushButton(ABOUT_TEXT, parent)
        self.about_button.setObjectName("aboutButton")
        self.about_button.setMinimumWidth(FOOTER_BUTTON_MINIMUM_WIDTH)
        self.about_button.setToolTip(ABOUT_TOOLTIP)
        self.about_button.clicked.connect(self.show_about)

        row.addStretch(1)
        row.addWidget(self.settings_button)
        row.addWidget(self.about_button)
        return row
