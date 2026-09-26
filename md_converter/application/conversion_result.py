"""Application-layer conversion result model (WP-P12-03-02).

Defines :class:`ConversionResult`, the normalized outcome of one Markdown ->
DOCX conversion at the application boundary
(``Doc/V2/V2_ARCHITECTURE.md`` §5.3).

The model is deliberately free of GUI concerns: it contains no Qt objects, no
widgets, and no parser/renderer instances.  It preserves both presentation
information (display-safe wording, diagnostic summary) and the full technical
evidence (canonical codes, messages, quality-gate report, technical detail).

Status semantics (WP-P12-03-02 §6)
----------------------------------
``SUCCESS``
    Conversion completed, the artifact was produced, and no user-relevant
    warning was reported.
``SUCCESS_WITH_WARNING``
    The artifact was produced and one or more non-fatal warnings must be
    surfaced.
``FAILED``
    The requested output was not successfully produced according to existing
    product semantics.  A ``FAILED`` result always carries an
    ``error_category``; ``output_path`` is populated only when a partial or
    rejected artifact exists on disk.

GUI presentation states (``EMPTY`` / ``READY`` / ``CONVERTING``) belong to the
GUI state model and are intentionally absent here.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Tuple

from .diagnostics_adapter import ApplicationDiagnostic, DiagnosticSummary

__all__ = ["ConversionStatus", "ConversionErrorCategory", "ConversionResult"]


class ConversionStatus(str, Enum):
    """Application-level outcome of one conversion (WP-P12-03-02 §4)."""

    SUCCESS = "SUCCESS"
    SUCCESS_WITH_WARNING = "SUCCESS_WITH_WARNING"
    FAILED = "FAILED"

    def __str__(self) -> str:
        """Return the stable status value (independent of Python version)."""
        return self.value


class ConversionErrorCategory(str, Enum):
    """Bounded application error taxonomy (``V2_ARCHITECTURE.md`` §10).

    This taxonomy is an application/UI contract.  It does not replace internal
    exception semantics; the original exception is retained in
    :attr:`ConversionResult.technical_detail`.
    """

    INPUT_ERROR = "INPUT_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    DEPENDENCY_ERROR = "DEPENDENCY_ERROR"
    CONVERSION_ERROR = "CONVERSION_ERROR"
    OUTPUT_ERROR = "OUTPUT_ERROR"
    ENVIRONMENT_ERROR = "ENVIRONMENT_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"

    def __str__(self) -> str:
        """Return the stable category value (independent of Python version)."""
        return self.value


@dataclass(frozen=True)
class ConversionResult:
    """Normalized outcome of one conversion (application boundary).

    Attributes:
        status: Application-level outcome.
        source_path: Markdown source of the conversion, when known.
        output_path: Produced DOCX path.  Populated for successful outcomes;
            for ``FAILED`` results it is set only when an artifact is actually
            present on disk (partial or rejected output).
        warnings: Warning-level diagnostic records.
        errors: Error-level diagnostic records (``ERROR`` / ``FATAL``).
        diagnostics: All adapted diagnostic records (info included).
        diagnostic_summary: Counts plus a display-safe summary sentence.
        quality_gate_report: Canonical quality-gate evidence, unmodified.
        error_category: Bounded failure category; required for ``FAILED``.
        error_message: Human-readable failure description.
        technical_detail: Support/debugging detail (exception type, traceback,
            quality-gate statuses).  Never silently discarded.
    """

    status: ConversionStatus
    source_path: Optional[Path] = None
    output_path: Optional[Path] = None
    warnings: Tuple[ApplicationDiagnostic, ...] = ()
    errors: Tuple[ApplicationDiagnostic, ...] = ()
    diagnostics: Tuple[ApplicationDiagnostic, ...] = ()
    diagnostic_summary: Optional[DiagnosticSummary] = None
    quality_gate_report: Optional[Dict[str, Any]] = None
    error_category: Optional[ConversionErrorCategory] = None
    error_message: Optional[str] = None
    technical_detail: Optional[str] = None

    def __post_init__(self) -> None:
        """Coerce record sequences and enforce the status semantics."""
        for name in ("warnings", "errors", "diagnostics"):
            value = getattr(self, name)
            if not isinstance(value, tuple):
                object.__setattr__(
                    self,
                    name,
                    tuple(value) if isinstance(value, Sequence) else (value,),
                )

        if self.status is ConversionStatus.FAILED:
            if self.error_category is None:
                raise ValueError("FAILED results require an error_category")
            if not isinstance(self.error_category, ConversionErrorCategory):
                object.__setattr__(
                    self, "error_category", ConversionErrorCategory(self.error_category)
                )
            return

        if self.errors:
            raise ValueError("Successful results must not carry error diagnostics")
        if self.status is ConversionStatus.SUCCESS and self.warnings:
            raise ValueError("SUCCESS must not carry warning diagnostics")
        if self.status is ConversionStatus.SUCCESS_WITH_WARNING and not self.warnings:
            raise ValueError("SUCCESS_WITH_WARNING requires at least one warning diagnostic")

    __hash__ = None  # type: ignore[assignment]  # quality_gate_report is a mapping

    @property
    def is_success(self) -> bool:
        """Whether the conversion produced its artifact without warnings."""
        return self.status is ConversionStatus.SUCCESS

    @property
    def is_success_with_warning(self) -> bool:
        """Whether the conversion produced its artifact and reported warnings."""
        return self.status is ConversionStatus.SUCCESS_WITH_WARNING

    @property
    def is_failed(self) -> bool:
        """Whether the conversion failed."""
        return self.status is ConversionStatus.FAILED

    @property
    def has_warnings(self) -> bool:
        """Whether warning-level diagnostics were reported."""
        return bool(self.warnings)

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serialisable representation of the result."""
        return {
            "status": self.status.value,
            "source_path": str(self.source_path) if self.source_path is not None else None,
            "output_path": str(self.output_path) if self.output_path is not None else None,
            "warnings": [record.to_dict() for record in self.warnings],
            "errors": [record.to_dict() for record in self.errors],
            "diagnostics": [record.to_dict() for record in self.diagnostics],
            "diagnostic_summary": (
                self.diagnostic_summary.to_dict() if self.diagnostic_summary else None
            ),
            "quality_gate_report": self.quality_gate_report,
            "error_category": (
                self.error_category.value if self.error_category is not None else None
            ),
            "error_message": self.error_message,
            "technical_detail": self.technical_detail,
        }
