"""Unified read-only result report surface for the MD_Converter GUI.

P12-06 requires retained failure, warning and diagnostics evidence to be
discoverable from the main window, with the presentation model as the only
presentation-semantic authority:

    ConversionResult / JobFailure
            v
    presentation_model   (title / summary / outcome / counts)
            v
    result_details       (this module - read-only report rendering)
            v
    MainWindow "Details..." affordance

The module is the *single* report surface for every outcome kind
(WP-P12-06-04 §"Primary rule"): it is read-only, on demand, deterministic and
local-only, and it renders retained evidence exactly as it was recorded.

It never recomputes diagnostics, never calls the Core/QA stages, never edits the
retained evidence and never builds a second result taxonomy.  Optional or empty
evidence produces no section at all, so the surface stays free of noise.

History: WP-P12-06-02 introduced a bounded failure-only details surface;
WP-P12-06-03 generalized it to warnings; WP-P12-06-04 completed it into the
unified diagnostics/report view.  The former ``failure_details`` module remains
as a thin compatibility alias and contains no implementation.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..application.conversion_result import ConversionResult
from ..application.diagnostics_adapter import ApplicationDiagnostic, DiagnosticSummary
from .presentation_model import Presentation, PresentationOutcome

__all__ = [
    "CLOSE_TEXT",
    "COPY_TEXT",
    "DETAILS_TITLES",
    "EVIDENCE_CAPTION_TEXT",
    "ResultDetailsDialog",
    "TITLE_FAILURE_DETAILS",
    "TITLE_GENERIC_DETAILS",
    "TITLE_WARNING_DETAILS",
    "build_report_text",
    "details_title",
    "presentation_evidence_text",
    "show_result_details",
]

#: Dialog chrome wording (plain product language).
TITLE_FAILURE_DETAILS = "Failure details"
TITLE_WARNING_DETAILS = "Warning details"
TITLE_GENERIC_DETAILS = "Conversion details"
EVIDENCE_CAPTION_TEXT = "Report:"
CLOSE_TEXT = "Close"
COPY_TEXT = "Copy"

#: Per-outcome dialog title; the label never mislabels warning evidence.
DETAILS_TITLES: Dict[PresentationOutcome, str] = {
    PresentationOutcome.SUCCESS_WITH_WARNING: TITLE_WARNING_DETAILS,
    PresentationOutcome.FAILED: TITLE_FAILURE_DETAILS,
    PresentationOutcome.INFRASTRUCTURE_FAILURE: TITLE_FAILURE_DETAILS,
    PresentationOutcome.SUCCESS: TITLE_GENERIC_DETAILS,
}

#: Stable dialog size for the full report.
DIALOG_WIDTH = 720
DIALOG_HEIGHT = 520


def details_title(presentation: Presentation) -> str:
    """Return the dialog title for ``presentation``.

    Args:
        presentation: Presentation view of the retained outcome.

    Returns:
        str: Outcome-appropriate dialog title.
    """
    return DETAILS_TITLES.get(presentation.outcome, TITLE_GENERIC_DETAILS)


def build_report_text(presentation: Presentation, evidence: object) -> str:
    """Return the read-only report text for one retained outcome.

    The text is derived only from ``presentation`` and the retained evidence
    handed in - no Core/QA stage is consulted and nothing is recomputed.  Empty
    or missing optional evidence contributes no section.

    Args:
        presentation: Presentation view of the retained outcome.
        evidence: Retained evidence - an application ``ConversionResult`` or
            worker-failure evidence.

    Returns:
        str: Deterministic report text; never empty.
    """
    if presentation.is_infrastructure_failure:
        return _job_failure_report(presentation, evidence)
    if isinstance(evidence, ConversionResult):
        return _result_report(presentation, evidence)
    return _render_report(presentation.title, _outcome_fields(presentation), [])


#: WP-P12-06-02/03 name for :func:`build_report_text`.
presentation_evidence_text = build_report_text


def _outcome_fields(presentation: Presentation) -> List[str]:
    """Return the headline fields shared by every report kind."""
    return [f"Status: {presentation.outcome}", f"Summary: {presentation.summary}"]


def _result_report(presentation: Presentation, result: ConversionResult) -> str:
    """Return the report text for a retained application result."""
    fields = _outcome_fields(presentation)
    if result.output_path is not None:
        fields.append(f"Output path: {result.output_path}")

    sections: List[Tuple[str, List[str]]] = []
    if result.warnings:
        sections.append(
            (f"Warnings ({len(result.warnings)})", _record_lines(result.warnings, severity=False))
        )
    if result.errors:
        sections.append(
            (f"Errors ({len(result.errors)})", _record_lines(result.errors, severity=False))
        )
    if result.diagnostics:
        sections.append(
            (
                f"Diagnostics ({len(result.diagnostics)})",
                _record_lines(result.diagnostics, severity=True),
            )
        )
    if result.diagnostic_summary is not None:
        sections.append(("Diagnostic summary", _summary_lines(result.diagnostic_summary)))
    if result.quality_gate_report:
        sections.append(("Quality gate report", _quality_gate_lines(result.quality_gate_report)))
    detail = (result.technical_detail or "").strip()
    if detail:
        sections.append(("Technical detail", [detail]))
    return _render_report(presentation.title, fields, sections)


def _job_failure_report(presentation: Presentation, evidence: object) -> str:
    """Return the report text for retained worker infrastructure evidence."""
    error_type = str(getattr(evidence, "error_type", "") or "").strip()
    message = str(getattr(evidence, "message", "") or "").strip()
    traceback_text = str(getattr(evidence, "traceback", "") or "").strip()

    fields = _outcome_fields(presentation)
    if error_type:
        fields.append(f"Exception type: {error_type}")
    if message:
        fields.append(f"Exception message: {message}")

    sections: List[Tuple[str, List[str]]] = []
    if traceback_text:
        sections.append(("Technical detail", [traceback_text]))
    return _render_report(presentation.title, fields, sections)


def _render_report(
    title: str,
    fields: Sequence[str],
    sections: Sequence[Tuple[str, List[str]]],
) -> str:
    """Join the report blocks in a deterministic order."""
    blocks: List[str] = []
    if title:
        blocks.append(title)
    blocks.append("\n".join(fields))
    for heading, lines in sections:
        blocks.append(f"{heading}\n" + "\n".join(lines))
    return "\n\n".join(blocks)


def _record_lines(
    records: Sequence[ApplicationDiagnostic],
    *,
    severity: bool,
) -> List[str]:
    """Return one display line per retained diagnostic record."""
    lines: List[str] = []
    for record in records:
        prefix = f"[{record.severity}] " if severity else ""
        lines.append(f"{prefix}{record.code}: {record.user_message}")
    return lines


def _summary_lines(summary: DiagnosticSummary) -> List[str]:
    """Return the retained diagnostic-summary counts and wording."""
    lines = [
        f"Total: {summary.total}",
        f"Errors: {summary.errors}",
        f"Warnings: {summary.warnings}",
        f"Info: {summary.infos}",
    ]
    if summary.user_message:
        lines.append(summary.user_message)
    return lines


def _quality_gate_lines(report: Mapping[str, Any]) -> List[str]:
    """Return one display line per meaningful quality-gate entry.

    Empty entries are skipped entirely.  A stage that records a status is shown
    as ``stage: STATUS`` (plus its scalar extras); other mappings are shown as
    their scalar key/value pairs.  Nothing is interpreted or scored here.
    """
    lines: List[str] = []
    for name, value in report.items():
        if value is None or value == "" or value == [] or value == {}:
            continue
        if isinstance(value, Mapping):
            status = value.get("status")
            extras = _scalar_pairs(value, skip=("status",))
            if status:
                lines.append(f"{name}: {status}" + (f" ({extras})" if extras else ""))
            else:
                lines.append(f"{name}: {extras}" if extras else f"{name}: present")
        elif isinstance(value, (list, tuple)):
            lines.append(f"{name}: {len(value)} item(s)")
        else:
            lines.append(f"{name}: {value}")
    return lines


def _scalar_pairs(value: Mapping[str, Any], *, skip: Sequence[str] = ()) -> str:
    """Return deterministic ``key=value`` text for the scalar mapping entries."""
    pairs = [
        f"{key}={item}"
        for key, item in sorted(value.items())
        if key not in skip and not isinstance(item, (Mapping, list, tuple))
    ]
    return ", ".join(pairs)


class ResultDetailsDialog(QDialog):
    """Read-only dialog showing the retained evidence of one outcome.

    Attributes:
        summary_label: Concise summary from the presentation model.
        evidence_view: Read-only text view of the full report.
        copy_button: Copies the report text to the clipboard (optional action).
        close_button: Dismisses the dialog.
    """

    def __init__(
        self,
        presentation: Presentation,
        evidence_text: str,
        parent: Optional[QWidget] = None,
    ) -> None:
        """Build the bounded details surface.

        Args:
            presentation: Presentation view of the retained outcome.
            evidence_text: Read-only report text produced by
                :func:`build_report_text`.
            parent: Optional Qt parent widget.
        """
        super().__init__(parent)
        self.setObjectName("resultDetailsDialog")
        self.setWindowTitle(details_title(presentation))
        self._presentation = presentation
        self._evidence_text = evidence_text

        layout = QVBoxLayout(self)
        layout.setObjectName("resultDetailsLayout")
        layout.setSpacing(10)

        self.summary_label = QLabel(presentation.summary, self)
        self.summary_label.setObjectName("resultDetailsSummaryLabel")
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)

        caption = QLabel(EVIDENCE_CAPTION_TEXT, self)
        caption.setObjectName("resultDetailsEvidenceCaption")
        layout.addWidget(caption)

        self.evidence_view = QPlainTextEdit(self)
        self.evidence_view.setObjectName("resultDetailsEvidenceView")
        self.evidence_view.setPlainText(evidence_text)
        self.evidence_view.setReadOnly(True)
        layout.addWidget(self.evidence_view, 1)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        self.copy_button = QPushButton(COPY_TEXT, self)
        self.copy_button.setObjectName("resultDetailsCopyButton")
        self.copy_button.clicked.connect(self._copy_report)
        button_row.addWidget(self.copy_button)
        self.close_button = QPushButton(CLOSE_TEXT, self)
        self.close_button.setObjectName("resultDetailsCloseButton")
        self.close_button.clicked.connect(self.accept)
        button_row.addWidget(self.close_button)
        layout.addLayout(button_row)

        self.resize(DIALOG_WIDTH, DIALOG_HEIGHT)

    @property
    def presentation(self) -> Presentation:
        """Return the presentation view shown by this surface."""
        return self._presentation

    @property
    def evidence_text(self) -> str:
        """Return the read-only evidence text shown by this surface."""
        return self._evidence_text

    def _copy_report(self) -> None:
        """Copy the report text to the system clipboard (no export, no upload)."""
        clipboard = QApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(self._evidence_text)


def show_result_details(
    parent: Optional[QWidget],
    presentation: Presentation,
    evidence: object,
) -> ResultDetailsDialog:
    """Open the bounded, read-only result-details surface.

    Args:
        parent: Parent window for the dialog.
        presentation: Presentation view of the retained outcome.
        evidence: Retained evidence.

    Returns:
        ResultDetailsDialog: The dialog that was shown (already dismissed).
    """
    dialog = ResultDetailsDialog(presentation, build_report_text(presentation, evidence), parent)
    dialog.exec()
    return dialog
