"""Application-facing diagnostics adapter (WP-P12-03-03).

The adapter translates *existing* diagnostic and quality-gate evidence into a
plain application structure suitable for CLI/GUI presentation
(``Doc/V2/V2_ARCHITECTURE.md`` §11).

It adapts evidence; it never creates a second QA system:

* the canonical :class:`~md_converter.diagnostics.collector.DiagnosticCollector`
  remains the source of diagnostic records - including QA-stage issues, which
  the QA stages already emit into that collector;
* the canonical quality-gate report is attached verbatim so full technical
  evidence survives.

Two information layers are produced per record (WP-P12-03-03 §5):

* ``user_message`` - display-safe wording for product surfaces;
* ``message`` / ``details`` / ``location`` - the untouched technical evidence.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from ..renderer.post_processor import DocxPostProcessor

__all__ = [
    "ApplicationDiagnostic",
    "ApplicationDiagnostics",
    "DiagnosticSummary",
    "DiagnosticsAdapter",
]

#: Display-safe wording for known diagnostic codes (WP-P12-03-03 §5).
#: Codes that are absent fall back to the original diagnostic message; the
#: technical message is always preserved on the record itself.
_USER_MESSAGE_MAP: Dict[str, str] = {
    DocxPostProcessor.COM_DIAGNOSTIC_CODE: (
        "Word post-processing was unavailable. "
        "The document was generated with limited post-processing."
    ),
    "POST001": "Required Word post-processing failed, so the document was not finalized.",
    "IO001": "The source document could not be read.",
    "IO002": "The output document could not be written.",
    "IO003": "A required file was not found.",
    "CONFIG001": "The conversion configuration could not be loaded.",
    "CONFIG002": "The conversion configuration is invalid.",
    "PARSE001": "Part of the Markdown source could not be parsed.",
    "PARSE002": "Part of the Markdown inline content could not be parsed.",
    "PARSE003": "The Markdown frontmatter could not be parsed.",
    "PIPE001": "A document transformation step failed.",
    "RENDER001": "Part of the document could not be rendered.",
    "MD001": "An image referenced by the document was not found.",
    "MD004": "A diagram could not be rendered; a fallback representation was used.",
}


@dataclass(frozen=True)
class ApplicationDiagnostic:
    """One application-facing diagnostic record.

    Attributes:
        severity: Canonical severity name (``INFO`` / ``WARNING`` / ``ERROR``
            / ``FATAL``); severity semantics are not redefined here.
        code: Canonical diagnostic code.
        message: Original (technical) diagnostic message.
        user_message: Display-safe wording for product surfaces.
        location: Source location as a plain mapping, when known.
        suggestion: Optional remediation hint from the canonical diagnostic.
        source: Canonical diagnostic source, when known.
        stage: Build stage the record belongs to (e.g. ``static_qa``).
        details: Additional structured evidence from the canonical diagnostic.
    """

    severity: str
    code: str
    message: str
    user_message: str
    location: Optional[Dict[str, Any]] = None
    suggestion: Optional[str] = None
    source: Optional[str] = None
    stage: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    @property
    def is_error(self) -> bool:
        """Whether this record is an error (``ERROR`` or ``FATAL``)."""
        return self.severity in ("ERROR", "FATAL")

    @property
    def is_warning(self) -> bool:
        """Whether this record is a warning."""
        return self.severity == "WARNING"

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serialisable representation of the record."""
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "user_message": self.user_message,
            "location": self.location,
            "suggestion": self.suggestion,
            "source": self.source,
            "stage": self.stage,
            "details": self.details,
        }


@dataclass(frozen=True)
class DiagnosticSummary:
    """Aggregate view of the application diagnostics of one conversion."""

    total: int
    errors: int
    warnings: int
    infos: int
    has_errors: bool
    has_warnings: bool
    is_clean: bool
    user_message: str

    @classmethod
    def from_records(cls, records: Sequence[ApplicationDiagnostic]) -> "DiagnosticSummary":
        """Build a summary from adapted diagnostic records.

        Args:
            records: Adapted records for one conversion.

        Returns:
            DiagnosticSummary: Counts and a concise display-safe sentence.
        """
        errors = sum(1 for record in records if record.is_error)
        warnings = sum(1 for record in records if record.is_warning)
        infos = len(records) - errors - warnings
        return cls(
            total=len(records),
            errors=errors,
            warnings=warnings,
            infos=infos,
            has_errors=errors > 0,
            has_warnings=warnings > 0,
            is_clean=len(records) == 0,
            user_message=_summarize_counts(errors, warnings, infos),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serialisable representation of the summary."""
        return {
            "total": self.total,
            "errors": self.errors,
            "warnings": self.warnings,
            "infos": self.infos,
            "has_errors": self.has_errors,
            "has_warnings": self.has_warnings,
            "is_clean": self.is_clean,
            "user_message": self.user_message,
        }


@dataclass(frozen=True)
class ApplicationDiagnostics:
    """Bundle of adapted diagnostics plus the canonical quality-gate report."""

    diagnostics: Tuple[ApplicationDiagnostic, ...] = ()
    summary: DiagnosticSummary = field(default_factory=lambda: DiagnosticSummary.from_records(()))
    quality_gate_report: Optional[Dict[str, Any]] = None

    @property
    def warnings(self) -> Tuple[ApplicationDiagnostic, ...]:
        """All warning-level records."""
        return tuple(record for record in self.diagnostics if record.is_warning)

    @property
    def errors(self) -> Tuple[ApplicationDiagnostic, ...]:
        """All error-level records (``ERROR`` and ``FATAL``)."""
        return tuple(record for record in self.diagnostics if record.is_error)

    @classmethod
    def empty(cls) -> "ApplicationDiagnostics":
        """Return an empty bundle for conversions that produced no evidence."""
        return cls()

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serialisable representation of the bundle."""
        return {
            "diagnostics": [record.to_dict() for record in self.diagnostics],
            "summary": self.summary.to_dict(),
            "quality_gate_report": self.quality_gate_report,
        }


def _plural(count: int, noun: str) -> str:
    """Return ``"<count> <noun>"`` with a pluralised noun when needed."""
    return f"{count} {noun}" + ("" if count == 1 else "s")


def _join_parts(parts: List[str]) -> str:
    """Join sentences parts with commas and a final ``"and"``."""
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return f"{parts[0]} and {parts[1]}"
    return ", ".join(parts[:-1]) + f", and {parts[-1]}"


def _summarize_counts(errors: int, warnings: int, infos: int) -> str:
    """Return a concise display-safe sentence for the given counts."""
    parts: List[str] = []
    if errors:
        parts.append(_plural(errors, "error"))
    if warnings:
        parts.append(_plural(warnings, "warning"))
    if infos:
        parts.append(_plural(infos, "informational note"))

    if not parts:
        return "Conversion completed with no diagnostics."
    if not errors and not warnings:
        return f"Conversion completed with {parts[0]}."
    return f"Conversion reported {_join_parts(parts)}."


class DiagnosticsAdapter:
    """Adapt canonical diagnostics and QA evidence to application structures.

    Args:
        user_message_map: Optional additional/replacement display-safe wording
            keyed by diagnostic code.  The built-in map is not modified.

    Example:
        >>> adapter = DiagnosticsAdapter()
        >>> bundle = adapter.build(context)  # context: CompilerContext
        >>> bundle.summary.total
        0
    """

    def __init__(self, user_message_map: Optional[Mapping[str, str]] = None) -> None:
        self._user_message_map: Dict[str, str] = dict(_USER_MESSAGE_MAP)
        if user_message_map:
            self._user_message_map.update(dict(user_message_map))

    def build(self, context: Any) -> ApplicationDiagnostics:
        """Build the application diagnostics bundle for ``context``.

        Args:
            context: A ``CompilerContext`` (or an equivalent object exposing
                ``diag.diagnostics`` and ``get_quality_gate_report()``).

        Returns:
            ApplicationDiagnostics: Adapted records, summary, and the
            canonical quality-gate report.
        """
        records = tuple(
            self._adapt_record(diagnostic) for diagnostic in self._collect_records(context)
        )
        return ApplicationDiagnostics(
            diagnostics=records,
            summary=DiagnosticSummary.from_records(records),
            quality_gate_report=self._quality_gate_report(context),
        )

    def user_message(self, code: str, message: str) -> str:
        """Return display-safe wording for one diagnostic.

        Args:
            code: Canonical diagnostic code.
            message: Original technical message (used as fallback wording).

        Returns:
            str: Display-safe text; never empty.
        """
        return self._user_message_map.get(code) or message or code

    def _adapt_record(self, diagnostic: Any) -> ApplicationDiagnostic:
        """Adapt one canonical ``Diagnostic`` into an application record."""
        data = diagnostic.to_dict()
        code = str(data.get("code") or "UNKNOWN")
        message = str(data.get("message") or "")
        source = data.get("source")
        return ApplicationDiagnostic(
            severity=str(data.get("severity") or "INFO"),
            code=code,
            message=message,
            user_message=self.user_message(code, message),
            location=data.get("location"),
            suggestion=data.get("suggestion"),
            source=source,
            stage=source,
            details=data.get("data"),
        )

    @staticmethod
    def _collect_records(context: Any) -> List[Any]:
        """Return the canonical diagnostic records held by ``context``."""
        collector = getattr(context, "diag", None)
        records = getattr(collector, "diagnostics", None)
        if not records:
            return []
        return list(records)

    @staticmethod
    def _quality_gate_report(context: Any) -> Optional[Dict[str, Any]]:
        """Return a defensive copy of the canonical quality-gate report."""
        report = getattr(context, "get_quality_gate_report", None)
        if report is None:
            return None
        report = report()
        if report is None:
            return None
        return copy.deepcopy(report)
