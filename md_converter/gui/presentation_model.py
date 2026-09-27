"""Thin, Qt-free presentation model for conversion outcomes (WP-P12-06-01).

The model is the single GUI boundary that turns *retained* evidence into
presentation-ready values:

    ConversionResult / JobFailure  ->  Presentation  ->  GUI surfaces

It formats, summarises and counts what already exists.  It never reinterprets
product semantics:

* the retained application result stays authoritative and untouched - the
  caller keeps the complete object (warnings, errors, diagnostics,
  ``diagnostic_summary``, ``quality_gate_report``, ``technical_detail``,
  ``output_path``) for the report view;
* the raw application status enum is not re-read here: the model consumes the
  application-level status predicates (``is_success`` /
  ``is_success_with_warning`` / ``is_failed``), so status interpretation stays
  centralized in :mod:`md_converter.gui.result_mapping`;
* worker infrastructure evidence is presented as its own outcome and is never
  turned into a fabricated application result;
* ``output_path`` is used verbatim as the sole path authority - no path is
  derived, reconstructed, renamed or guessed.

The module imports no GUI framework and nothing from the Core compiler stages;
its only dependency is the application-layer result model.  It can therefore be
unit-tested without a GUI runtime (WP-P12-06-01 "Qt-free; no Core imports").
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Protocol, Tuple

from ..application.conversion_result import ConversionResult

__all__ = [
    "FailureEvidence",
    "Presentation",
    "PresentationOutcome",
    "SEVERITY_BY_OUTCOME",
    "SUMMARY_FAILED",
    "SUMMARY_INFRASTRUCTURE_FAILURE",
    "SUMMARY_SUCCESS",
    "TITLE_FAILED",
    "TITLE_INFRASTRUCTURE_FAILURE",
    "TITLE_SUCCESS",
    "TITLE_SUCCESS_WITH_WARNING",
    "present_job_failure",
    "present_result",
]


class PresentationOutcome(str, Enum):
    """Presentation outcome of one finished job (WP-P12-06-01).

    The values mirror the accepted semantics one-to-one; they do not redefine
    them and they never move a warning into a failure.

    Attributes:
        SUCCESS: The artifact was produced without warnings.
        SUCCESS_WITH_WARNING: The artifact was produced and warnings must be
            surfaced.  This is still a successful outcome.
        FAILED: The application reported a failed conversion.
        INFRASTRUCTURE_FAILURE: The worker boundary retained a failure that is
            distinct from an application conversion result.
    """

    SUCCESS = "SUCCESS"
    SUCCESS_WITH_WARNING = "SUCCESS_WITH_WARNING"
    FAILED = "FAILED"
    INFRASTRUCTURE_FAILURE = "INFRASTRUCTURE_FAILURE"

    def __str__(self) -> str:
        """Return the stable outcome value (independent of Python version)."""
        return self.value


#: Presentation severity used for styling/status decisions.  It is a 1:1
#: projection of the outcome and is not a second error taxonomy.
SEVERITY_BY_OUTCOME: Dict[PresentationOutcome, str] = {
    PresentationOutcome.SUCCESS: "success",
    PresentationOutcome.SUCCESS_WITH_WARNING: "warning",
    PresentationOutcome.FAILED: "error",
    PresentationOutcome.INFRASTRUCTURE_FAILURE: "error",
}

#: Concise status line per outcome (plain product language).
TITLE_SUCCESS = "Conversion completed."
TITLE_SUCCESS_WITH_WARNING = "Conversion completed with warnings."
TITLE_FAILED = "Conversion failed."
TITLE_INFRASTRUCTURE_FAILURE = "Conversion could not be completed."

#: Fallback summary used when the retained evidence carries no wording.
SUMMARY_SUCCESS = "The document was generated successfully."
SUMMARY_FAILED = "The document could not be generated."
SUMMARY_INFRASTRUCTURE_FAILURE = (
    "An internal error stopped the conversion before a document was produced."
)

_TITLE_BY_OUTCOME: Dict[PresentationOutcome, str] = {
    PresentationOutcome.SUCCESS: TITLE_SUCCESS,
    PresentationOutcome.SUCCESS_WITH_WARNING: TITLE_SUCCESS_WITH_WARNING,
    PresentationOutcome.FAILED: TITLE_FAILED,
    PresentationOutcome.INFRASTRUCTURE_FAILURE: TITLE_INFRASTRUCTURE_FAILURE,
}

#: Outcomes whose artifact may be offered to the user (WP-P12-06-05 rule).
_OUTPUT_ACTIONABLE_OUTCOMES = (
    PresentationOutcome.SUCCESS,
    PresentationOutcome.SUCCESS_WITH_WARNING,
)


class FailureEvidence(Protocol):
    """Structural view of the retained worker-failure evidence.

    The concrete class lives in the Qt-bearing worker module; declaring the
    fields structurally keeps this module free of that import while still
    typing the boundary.  Only retained evidence fields are named, and the
    presentation model never converts this evidence into an application result.

    Attributes:
        error_type: Exception class name.
        message: Exception message.
        traceback: Formatted traceback text, kept as technical evidence.
    """

    error_type: str
    message: str
    traceback: str


@dataclass(frozen=True)
class Presentation:
    """Presentation-ready view of one retained outcome.

    The view is derived data only: the original ``ConversionResult`` or
    ``JobFailure`` remains the authoritative evidence and is retained
    separately by the caller.

    Attributes:
        outcome: Presentation outcome for the retained job.
        title: Concise status line.
        summary: Concise plain-language sentence.
        details_available: Whether a bounded details affordance is meaningful.
        output_actionable: Whether Open Document / Open Folder are eligible.
            ``output_path`` is used verbatim; nothing is derived.
        output_path: Retained output path, or ``None`` when the result has none.
        warning_count: Warning records reported by the retained evidence.
        error_count: Error records reported by the retained evidence.
    """

    outcome: PresentationOutcome
    title: str
    summary: str
    details_available: bool
    output_actionable: bool
    output_path: Optional[Path]
    warning_count: int
    error_count: int

    @property
    def severity(self) -> str:
        """Return the presentation severity for :attr:`outcome`."""
        return SEVERITY_BY_OUTCOME[self.outcome]

    @property
    def is_success(self) -> bool:
        """Whether the presented job produced an artifact."""
        return self.outcome in _OUTPUT_ACTIONABLE_OUTCOMES

    @property
    def is_failure(self) -> bool:
        """Whether the presented job did not produce an artifact."""
        return not self.is_success

    @property
    def is_infrastructure_failure(self) -> bool:
        """Whether the presented job failed outside the application contract."""
        return self.outcome is PresentationOutcome.INFRASTRUCTURE_FAILURE


def present_result(result: ConversionResult) -> Presentation:
    """Return the presentation view of one retained application result.

    Args:
        result: Application-layer conversion outcome.  It is only read: the
            caller keeps the complete object for the report view.

    Returns:
        Presentation: Title, summary, counts, detail availability and output
        actionability for ``result``.
    """
    outcome = _outcome_for_result(result)
    warning_count, error_count = _diagnostic_counts(result)
    return Presentation(
        outcome=outcome,
        title=_TITLE_BY_OUTCOME[outcome],
        summary=_summary_for_result(result, outcome, warning_count),
        details_available=_details_available(result),
        output_actionable=_output_actionable(result, outcome),
        output_path=result.output_path,
        warning_count=warning_count,
        error_count=error_count,
    )


def present_job_failure(failure: FailureEvidence) -> Presentation:
    """Return the presentation view of one retained worker failure.

    Infrastructure failure keeps its own semantics: it is never presented as a
    document failure, it never fabricates a successful outcome, and no output
    action is offered because no application result exists.

    Args:
        failure: Retained worker-failure evidence.

    Returns:
        Presentation: Infrastructure-failure presentation with details
        available and output actions disabled.
    """
    return Presentation(
        outcome=PresentationOutcome.INFRASTRUCTURE_FAILURE,
        title=TITLE_INFRASTRUCTURE_FAILURE,
        summary=_infrastructure_summary(failure),
        details_available=True,
        output_actionable=False,
        output_path=None,
        warning_count=0,
        error_count=0,
    )


def _outcome_for_result(result: ConversionResult) -> PresentationOutcome:
    """Map one application result to its presentation outcome.

    The application status predicates are consumed instead of the raw status
    enum, so status interpretation stays centralized.  The check is ordered
    fail-closed: anything that is not recognisably successful is presented as a
    failure, never as a success.
    """
    if result.is_failed:
        return PresentationOutcome.FAILED
    if result.is_success_with_warning:
        return PresentationOutcome.SUCCESS_WITH_WARNING
    if result.is_success:
        return PresentationOutcome.SUCCESS
    return PresentationOutcome.FAILED


def _diagnostic_counts(result: ConversionResult) -> Tuple[int, int]:
    """Return ``(warning_count, error_count)`` from retained evidence.

    The adapted diagnostic summary is preferred when present: it already counts
    the complete adapted record set.  Otherwise the retained warning and error
    records are counted directly.  Nothing is recomputed from the source
    document or from QA.
    """
    summary = result.diagnostic_summary
    if summary is not None:
        return summary.warnings, summary.errors
    return len(result.warnings), len(result.errors)


def _summary_for_result(
    result: ConversionResult,
    outcome: PresentationOutcome,
    warning_count: int,
) -> str:
    """Return the concise summary sentence for ``result``."""
    if outcome is PresentationOutcome.FAILED:
        message = (result.error_message or "").strip()
        return message or SUMMARY_FAILED

    summary = result.diagnostic_summary
    if summary is not None and summary.user_message:
        return summary.user_message

    if outcome is PresentationOutcome.SUCCESS_WITH_WARNING:
        return f"Conversion reported {_plural(warning_count, 'warning')}."
    return SUMMARY_SUCCESS


def _infrastructure_summary(failure: FailureEvidence) -> str:
    """Return the summary sentence for a retained worker failure.

    Only the bounded exception category is added; the retained message and
    traceback stay in the details view.
    """
    error_type = (getattr(failure, "error_type", "") or "").strip()
    if error_type:
        return (
            f"An internal error ({error_type}) stopped the conversion "
            "before a document was produced."
        )
    return SUMMARY_INFRASTRUCTURE_FAILURE


def _details_available(result: ConversionResult) -> bool:
    """Return whether the report view has retained evidence to show.

    Failures always offer the details affordance.  Successful outcomes offer it
    when the retained result carries evidence to inspect or an artifact path to
    display.
    """
    if result.is_failed:
        return True
    return bool(
        result.diagnostics
        or result.warnings
        or result.errors
        or result.quality_gate_report is not None
        or result.technical_detail
        or result.output_path is not None
    )


def _output_actionable(result: ConversionResult, outcome: PresentationOutcome) -> bool:
    """Return whether the output actions are eligible for ``result``.

    ``ConversionResult.output_path`` is the sole path authority: it is used
    verbatim and never derived from the source, the configuration or a title.
    Actions are eligible only for successful outcomes whose artifact is present
    on disk; a missing or unreadable path simply disables them.
    """
    if outcome not in _OUTPUT_ACTIONABLE_OUTCOMES:
        return False
    path = result.output_path
    if path is None:
        return False
    try:
        return Path(path).exists()
    except OSError:
        return False


def _plural(count: int, noun: str) -> str:
    """Return ``"<count> <noun>"`` with a pluralised noun when needed."""
    return f"{count} {noun}" + ("" if count == 1 else "s")
