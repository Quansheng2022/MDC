"""Qt-free document-quality (preflight) presentation model (WP-DI-02).

Document Preflight answers one product question without adding a second quality
system:

    Which quality findings does the *existing* conversion authority already
    report for this document?

The model is therefore a presentation-only view over retained evidence:

    authoritative diagnostics (DiagnosticCollector -> DiagnosticsAdapter)
        v
    preflight_model   (this module - group / order / count / label)
        v
    preflight panel + conversion report

Boundary rules frozen by ``DOCUMENT_INTELLIGENCE_ARCHITECTURE_BASELINE.md``
(WP-DI-01):

* the model creates **no** findings: every item comes from one retained
  :class:`~md_converter.application.diagnostics_adapter.ApplicationDiagnostic`;
* it runs no QA stage, parses no Markdown, reads no document and touches no
  renderer/Word object, so it stays importable and testable without a GUI and
  without the Core compiler stages;
* per-finding wording is never composed here: the display-safe ``title`` is the
  adapter's ``user_message`` (the single wording authority, ``_USER_MESSAGE_MAP``),
  and the technical ``message`` stays as secondary ``detail``;
* counts are derived from the items, so a count can never drift from the
  presented record set.  No duplicate suppression is applied, so the presented
  counts equal the authoritative diagnostic counts;
* deterministic ordering: errors first, then warnings, then informational
  items, and the authoritative record order is preserved inside each group.

Severity semantics are not redefined: ``ERROR``/``FATAL`` are errors, ``WARNING``
is a warning, and any other value is presented as an informational item that
keeps its original severity text (fail-soft presentation of unexpected input).
"""

from __future__ import annotations

from collections.abc import Mapping as MappingABC
from dataclasses import dataclass
from typing import Any, List, Optional, Sequence, Tuple

from ..application.conversion_result import ConversionResult

__all__ = [
    "DEGRADED_CODES",
    "MARKER_BY_SEVERITY",
    "PREFLIGHT_CLEAN_TEXT",
    "PreflightItem",
    "PreflightSummary",
    "SEVERITY_RANK",
    "preflight_from_diagnostics",
    "preflight_from_result",
]

#: Severity names that mean "error" (canonical semantics, not redefined here).
ERROR_SEVERITIES: Tuple[str, ...] = ("ERROR", "FATAL")

#: Severity name that means "warning".
WARNING_SEVERITY = "WARNING"

#: Presentation rank per canonical severity.  ``FATAL`` and ``ERROR`` share a
#: rank, so the authoritative record order decides between them (stable sort).
SEVERITY_RANK = {"FATAL": 0, "ERROR": 0, "WARNING": 1, "INFO": 2}

#: Rank used for a severity value outside the canonical set (shown last).
_UNKNOWN_SEVERITY_RANK = 3

#: Per-severity marker.  A marker is always accompanied by the severity word, so
#: no finding is conveyed by colour or glyph alone.
MARKER_BY_SEVERITY = {
    "FATAL": "\u2717",
    "ERROR": "\u2717",
    "WARNING": "\u26a0",
    "INFO": "\u2139",
}

#: Marker used for a severity value outside the canonical set.
_FALLBACK_MARKER = "\u2139"

#: Codes whose existing wording reports a degraded / unsupported outcome
#: (``POST002`` Word post-processing unavailable, ``MD001`` referenced image
#: missing, ``MD004`` diagram fallback, ``DIAG001``/``DIAG002`` diagram text
#: fallback, ``DIAG003`` diagram could not be saved).  The set only *groups*
#: retained findings; it never creates one and it changes no severity.
DEGRADED_CODES = frozenset({"POST002", "MD001", "MD004", "DIAG001", "DIAG002", "DIAG003"})

#: Wording used when no authoritative summary wording was retained and nothing
#: was reported.
PREFLIGHT_CLEAN_TEXT = "No quality findings were reported."


def _plural(count: int, noun: str) -> str:
    """Return ``"<count> <noun>"`` with a pluralised noun when needed."""
    return f"{count} {noun}" + ("" if count == 1 else "s")


def _join(parts: Sequence[str]) -> str:
    """Join parts with commas and a final ``"and"``."""
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return f"{parts[0]} and {parts[1]}"
    return ", ".join(parts[:-1]) + f", and {parts[-1]}"


def _field(record: Any, name: str, default: Any = None) -> Any:
    """Return ``record.name`` for an object or a mapping, else ``default``.

    Presentation input is expected to be an
    :class:`~md_converter.application.diagnostics_adapter.ApplicationDiagnostic`,
    but a mapping or a partially-populated object is tolerated so that an
    unexpected record never breaks the surface (WP-DI-06).
    """
    if isinstance(record, MappingABC):
        return record.get(name, default)
    return getattr(record, name, default)


def _text(value: Any) -> str:
    """Return ``value`` as trimmed text (empty for ``None``)."""
    if value is None:
        return ""
    return str(value).strip()


def _severity_of(record: Any) -> str:
    """Return the canonical severity name of ``record`` (``INFO`` as fallback)."""
    severity = _text(_field(record, "severity")).upper()
    return severity or "INFO"


def _location_text(location: Any) -> Optional[str]:
    """Return a concise display location for a retained location value."""
    if location is None:
        return None
    if isinstance(location, MappingABC):
        start_line = location.get("start_line")
        if start_line is not None and str(start_line).strip():
            return f"line {start_line}"
        return None
    text = _text(location)
    return text or None


@dataclass(frozen=True)
class PreflightItem:
    """One presentation-ready quality finding (never a new finding).

    Attributes:
        severity: Canonical severity name (``INFO`` / ``WARNING`` / ``ERROR``
            / ``FATAL``); the meaning is unchanged from the authoritative
            diagnostic.
        code: Canonical diagnostic code, preserved for traceability.
        title: Display-safe one-line summary - the adapter's ``user_message``.
        detail: Retained technical message (secondary evidence).
        source: Canonical source/stage of the diagnostic, when known.
        location: Concise location text (for example ``"line 12"``), when known.
    """

    severity: str
    code: str
    title: str
    detail: str = ""
    source: Optional[str] = None
    location: Optional[str] = None

    @property
    def is_error(self) -> bool:
        """Whether this finding is an error (``ERROR`` or ``FATAL``)."""
        return self.severity in ERROR_SEVERITIES

    @property
    def is_warning(self) -> bool:
        """Whether this finding is a warning."""
        return self.severity == WARNING_SEVERITY

    @property
    def is_info(self) -> bool:
        """Whether this finding is informational."""
        return not self.is_error and not self.is_warning

    @property
    def is_degradation(self) -> bool:
        """Whether the finding reports a degraded / unsupported outcome."""
        return self.code in DEGRADED_CODES

    @property
    def marker(self) -> str:
        """Return the presentation marker for this finding's severity."""
        return MARKER_BY_SEVERITY.get(self.severity, _FALLBACK_MARKER)

    @property
    def display_title(self) -> str:
        """Return the finding wording, falling back to the code when empty."""
        return self.title or self.code

    def row_text(self) -> str:
        """Return the one-line row text, always carrying the severity word."""
        row = f"{self.marker} {self.severity} \u2014 {self.display_title}"
        if self.code and self.code != self.display_title:
            row = f"{row} ({self.code})"
        return row

    def to_dict(self) -> dict:
        """Return a JSON-serialisable representation of the finding."""
        return {
            "severity": self.severity,
            "code": self.code,
            "title": self.title,
            "detail": self.detail,
            "source": self.source,
            "location": self.location,
        }


@dataclass(frozen=True)
class PreflightSummary:
    """Counts plus the ordered findings of one document.

    Attributes:
        items: Ordered findings (errors, then warnings, then informational
            items; authoritative order preserved inside each group).
        retained_wording: Optional display-safe sentence retained from the
            authoritative diagnostic summary.  When present it is used verbatim
            so the preflight view and the conversion report cannot phrase the
            same evidence differently.
    """

    items: Tuple[PreflightItem, ...] = ()
    retained_wording: Optional[str] = None

    def __post_init__(self) -> None:
        """Coerce ``items`` to an immutable tuple."""
        if not isinstance(self.items, tuple):
            object.__setattr__(self, "items", tuple(self.items))

    @property
    def total(self) -> int:
        """Return the number of presented findings."""
        return len(self.items)

    @property
    def error_count(self) -> int:
        """Return the number of error-level findings."""
        return sum(1 for item in self.items if item.is_error)

    @property
    def warning_count(self) -> int:
        """Return the number of warning-level findings."""
        return sum(1 for item in self.items if item.is_warning)

    @property
    def info_count(self) -> int:
        """Return the number of informational findings."""
        return sum(1 for item in self.items if item.is_info)

    @property
    def is_clean(self) -> bool:
        """Whether no finding was reported at all."""
        return not self.items

    @property
    def has_errors(self) -> bool:
        """Whether any error-level finding was reported."""
        return self.error_count > 0

    @property
    def has_warnings(self) -> bool:
        """Whether any warning-level finding was reported."""
        return self.warning_count > 0

    def counts_text(self) -> str:
        """Return the bounded counts sentence body, for example
        ``"2 warnings and 1 information item"``; empty when nothing was
        reported.
        """
        parts: List[str] = []
        if self.error_count:
            parts.append(_plural(self.error_count, "error"))
        if self.warning_count:
            parts.append(_plural(self.warning_count, "warning"))
        if self.info_count:
            parts.append(_plural(self.info_count, "information item"))
        return _join(parts)

    def summary_text(self) -> str:
        """Return the display sentence for this summary.

        The retained authoritative wording wins when it exists, so no second
        wording authority is created; otherwise the counts are rendered.
        """
        wording = _text(self.retained_wording)
        if wording:
            return wording
        if self.is_clean:
            return PREFLIGHT_CLEAN_TEXT
        return f"{self.counts_text()}."

    def rows(self) -> Tuple[str, ...]:
        """Return the one-line row text of every finding, in order."""
        return tuple(item.row_text() for item in self.items)

    def degradations(self) -> Tuple[PreflightItem, ...]:
        """Return the findings that report a degraded / unsupported outcome."""
        return tuple(item for item in self.items if item.is_degradation)

    def to_dict(self) -> dict:
        """Return a JSON-serialisable representation of the summary."""
        return {
            "items": [item.to_dict() for item in self.items],
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "summary_text": self.summary_text(),
        }


def preflight_from_diagnostics(
    records: Optional[Sequence[Any]],
    *,
    retained_wording: Optional[str] = None,
) -> PreflightSummary:
    """Build the preflight summary for retained diagnostic records.

    Args:
        records: Adapted application diagnostics (or equivalent mappings).
            ``None`` and empty input produce an empty, clean summary.
        retained_wording: Optional display-safe sentence retained from the
            authoritative diagnostic summary.

    Returns:
        PreflightSummary: The ordered findings with derived counts.  Every
        usable input record produces exactly one item, so the counts match the
        authoritative record set.
    """
    items: List[PreflightItem] = []
    for record in records or ():
        if record is None:
            continue
        code = _text(_field(record, "code"))
        detail = _text(_field(record, "message"))
        title = _text(_field(record, "user_message")) or detail or code
        source = _text(_field(record, "source")) or _text(_field(record, "stage")) or None
        items.append(
            PreflightItem(
                severity=_severity_of(record),
                code=code,
                title=title,
                detail=detail,
                source=source,
                location=_location_text(_field(record, "location")),
            )
        )
    ordered = tuple(sorted(items, key=_rank_of))
    return PreflightSummary(items=ordered, retained_wording=retained_wording)


def preflight_from_result(result: ConversionResult) -> PreflightSummary:
    """Build the preflight summary for one retained application result.

    The retained result is only read: the caller keeps the complete object, and
    the authoritative ``DiagnosticSummary`` wording is passed through so both
    surfaces phrase the same evidence identically.

    Args:
        result: Application-layer conversion outcome.

    Returns:
        PreflightSummary: The ordered findings of ``result``.
    """
    if result is None:
        return PreflightSummary()
    summary = getattr(result, "diagnostic_summary", None)
    wording = _text(getattr(summary, "user_message", None))
    return preflight_from_diagnostics(
        getattr(result, "diagnostics", None) or (),
        retained_wording=wording or None,
    )


def _rank_of(item: PreflightItem) -> int:
    """Return the presentation rank of one finding's severity."""
    return SEVERITY_RANK.get(item.severity, _UNKNOWN_SEVERITY_RANK)
