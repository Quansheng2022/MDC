"""Bounded result-details surface for the MD_Converter GUI (WP-P12-06-02/03).

P12-06 requires failure *and* warning evidence to be discoverable from the main
window, while the complete read-only diagnostics/report view belongs to
WP-P12-06-04.  This module provides the minimum bounded surface for both:

    Details...  ->  read-only dialog with the retained evidence

Properties (WP-P12-06-02 "Details affordance", WP-P12-06-03 "Details surface"):

* read-only, on demand, evidence-driven - it renders retained evidence and the
  presentation strings derived from it;
* it never recomputes diagnostics, never calls the Core/QA stages and never
  edits the retained evidence;
* one surface for every outcome kind, labelled per outcome, so warning evidence
  is never mislabelled as a failure; the full report surface is WP-P12-06-04.

WP-P12-06-03 generalized the WP-P12-06-02 failure-only surface: the dialog is
now titled per outcome ("Failure details" / "Warning details") and renders
warning records as warning evidence.  The former ``failure_details`` module
remains as a thin compatibility alias and contains no implementation.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..application.conversion_result import ConversionResult
from .presentation_model import Presentation, PresentationOutcome

__all__ = [
    "CLOSE_TEXT",
    "DETAILS_TITLES",
    "EVIDENCE_CAPTION_TEXT",
    "ResultDetailsDialog",
    "TITLE_FAILURE_DETAILS",
    "TITLE_GENERIC_DETAILS",
    "TITLE_WARNING_DETAILS",
    "details_title",
    "presentation_evidence_text",
    "show_result_details",
]

#: Dialog chrome wording (plain product language).
TITLE_FAILURE_DETAILS = "Failure details"
TITLE_WARNING_DETAILS = "Warning details"
TITLE_GENERIC_DETAILS = "Conversion details"
EVIDENCE_CAPTION_TEXT = "Details:"
CLOSE_TEXT = "Close"

#: Per-outcome dialog title; the label never mislabels warning evidence.
DETAILS_TITLES: Dict[PresentationOutcome, str] = {
    PresentationOutcome.SUCCESS_WITH_WARNING: TITLE_WARNING_DETAILS,
    PresentationOutcome.FAILED: TITLE_FAILURE_DETAILS,
    PresentationOutcome.INFRASTRUCTURE_FAILURE: TITLE_FAILURE_DETAILS,
    PresentationOutcome.SUCCESS: TITLE_GENERIC_DETAILS,
}

#: Stable dialog size; the surface stays bounded until WP-P12-06-04.
DIALOG_WIDTH = 560
DIALOG_HEIGHT = 360


def details_title(presentation: Presentation) -> str:
    """Return the dialog title for ``presentation``.

    Args:
        presentation: Presentation view of the retained outcome.

    Returns:
        str: Outcome-appropriate dialog title.
    """
    return DETAILS_TITLES.get(presentation.outcome, TITLE_GENERIC_DETAILS)


def presentation_evidence_text(presentation: Presentation, evidence: object) -> str:
    """Return the bounded plain-text evidence block for ``evidence``.

    Args:
        presentation: Presentation view of the retained outcome; used to select
            the evidence shape and as a fallback summary.
        evidence: Retained evidence - an application ``ConversionResult`` or
            worker-failure evidence.

    Returns:
        str: Read-only text for the details surface; never empty.
    """
    if presentation.is_infrastructure_failure:
        text = _job_failure_text(evidence)
    elif isinstance(evidence, ConversionResult):
        if presentation.outcome is PresentationOutcome.SUCCESS_WITH_WARNING:
            text = _warning_text(evidence)
        else:
            text = _result_failure_text(evidence)
    else:
        text = ""
    return text.strip() or presentation.summary


def _warning_text(result: ConversionResult) -> str:
    """Return the retained warning evidence of a successful conversion."""
    return "\n".join(f"{record.code}: {record.user_message}" for record in result.warnings)


def _result_failure_text(result: ConversionResult) -> str:
    """Return the retained failure evidence of an application result."""
    lines: List[str] = []
    message = (result.error_message or "").strip()
    if message:
        lines.append(message)
    for record in result.errors:
        lines.append(f"{record.code}: {record.user_message}")
    detail = (result.technical_detail or "").strip()
    if detail:
        lines.append("")
        lines.append("Technical detail:")
        lines.append(detail)
    return "\n".join(lines)


def _job_failure_text(evidence: object) -> str:
    """Return the retained evidence of a worker infrastructure failure."""
    error_type = str(getattr(evidence, "error_type", "") or "").strip()
    message = str(getattr(evidence, "message", "") or "").strip()
    traceback_text = str(getattr(evidence, "traceback", "") or "").strip()

    lines: List[str] = []
    headline = ": ".join(part for part in (error_type, message) if part)
    if headline:
        lines.append(headline)
    if traceback_text:
        lines.append("")
        lines.append(traceback_text)
    return "\n".join(lines)


class ResultDetailsDialog(QDialog):
    """Read-only dialog showing the retained evidence of one outcome.

    Attributes:
        summary_label: Concise summary from the presentation model.
        evidence_view: Read-only text view of the retained evidence.
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
            evidence_text: Read-only evidence text produced by
                :func:`presentation_evidence_text`.
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
    dialog = ResultDetailsDialog(
        presentation, presentation_evidence_text(presentation, evidence), parent
    )
    dialog.exec()
    return dialog
