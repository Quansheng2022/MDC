"""Bounded failure-details surface for the MD_Converter GUI (WP-P12-06-02).

WP-P12-06-02 requires failure evidence to be discoverable from the main window,
but the complete read-only diagnostics/report view belongs to WP-P12-06-04.
This module therefore provides the *minimum* bounded surface only:

    Details...  ->  read-only dialog with the retained failure evidence

Properties (WP-P12-06-02 "Details affordance"):

* read-only, on demand, evidence-driven - it renders retained evidence and the
  presentation strings derived from it;
* it never recomputes diagnostics, never calls the Core/QA stages and never
  edits the retained evidence;
* it displays only the failure slice (message, error records, technical detail,
  worker failure text); the full report surface is WP-P12-06-04.
"""

from __future__ import annotations

from typing import List, Optional

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
from .presentation_model import Presentation

__all__ = [
    "CLOSE_TEXT",
    "DETAILS_TITLE",
    "EVIDENCE_CAPTION_TEXT",
    "FailureDetailsDialog",
    "failure_evidence_text",
    "show_failure_details",
]

#: Dialog chrome wording (plain product language).
DETAILS_TITLE = "Failure details"
EVIDENCE_CAPTION_TEXT = "Details:"
CLOSE_TEXT = "Close"

#: Stable dialog size; the surface stays bounded until WP-P12-06-04.
DIALOG_WIDTH = 560
DIALOG_HEIGHT = 360


def failure_evidence_text(presentation: Presentation, evidence: object) -> str:
    """Return the bounded plain-text evidence block for ``evidence``.

    Args:
        presentation: Presentation view of the retained outcome; used to select
            the evidence shape and as a fallback summary.
        evidence: Retained failure evidence - an application
            ``ConversionResult`` or worker-failure evidence.

    Returns:
        str: Read-only text for the details surface; never empty.
    """
    if presentation.is_infrastructure_failure:
        text = _job_failure_text(evidence)
    elif isinstance(evidence, ConversionResult):
        text = _result_failure_text(evidence)
    else:
        text = ""
    return text.strip() or presentation.summary


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


class FailureDetailsDialog(QDialog):
    """Read-only dialog showing the retained failure evidence.

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
                :func:`failure_evidence_text`.
            parent: Optional Qt parent widget.
        """
        super().__init__(parent)
        self.setObjectName("failureDetailsDialog")
        self.setWindowTitle(DETAILS_TITLE)
        self._presentation = presentation
        self._evidence_text = evidence_text

        layout = QVBoxLayout(self)
        layout.setObjectName("failureDetailsLayout")
        layout.setSpacing(10)

        self.summary_label = QLabel(presentation.summary, self)
        self.summary_label.setObjectName("failureDetailsSummaryLabel")
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)

        caption = QLabel(EVIDENCE_CAPTION_TEXT, self)
        caption.setObjectName("failureDetailsEvidenceCaption")
        layout.addWidget(caption)

        self.evidence_view = QPlainTextEdit(self)
        self.evidence_view.setObjectName("failureDetailsEvidenceView")
        self.evidence_view.setPlainText(evidence_text)
        self.evidence_view.setReadOnly(True)
        layout.addWidget(self.evidence_view, 1)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        self.close_button = QPushButton(CLOSE_TEXT, self)
        self.close_button.setObjectName("failureDetailsCloseButton")
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


def show_failure_details(
    parent: Optional[QWidget],
    presentation: Presentation,
    evidence: object,
) -> FailureDetailsDialog:
    """Open the bounded, read-only failure-details surface.

    Args:
        parent: Parent window for the dialog.
        presentation: Presentation view of the retained outcome.
        evidence: Retained failure evidence.

    Returns:
        FailureDetailsDialog: The dialog that was shown (already dismissed).
    """
    dialog = FailureDetailsDialog(
        presentation, failure_evidence_text(presentation, evidence), parent
    )
    dialog.exec()
    return dialog
