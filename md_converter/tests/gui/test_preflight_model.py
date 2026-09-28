"""Focused verification for the preflight presentation model (WP-DI-02).

The model is a presentation-only view over retained authoritative diagnostics:
it groups, orders, counts and labels existing findings, and it creates none.
These tests pin that boundary, the deterministic ordering, the derived counts
and the fail-soft behaviour on unexpected presentation input.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Dict, List

from md_converter.application.conversion_result import (
    ConversionErrorCategory,
    ConversionResult,
    ConversionStatus,
)
from md_converter.application.diagnostics_adapter import (
    ApplicationDiagnostic,
    DiagnosticSummary,
)
from md_converter.gui.preflight_model import (
    DEGRADED_CODES,
    MARKER_BY_SEVERITY,
    PREFLIGHT_CLEAN_TEXT,
    PreflightSummary,
    preflight_from_diagnostics,
    preflight_from_result,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
GUI_DIR = PROJECT_ROOT / "md_converter" / "gui"

#: Core modules the presentation layer must never import.
FORBIDDEN_IMPORT_PREFIXES = (
    "md_converter.compiler",
    "md_converter.diagnostics",
    "md_converter.parser",
    "md_converter.pipeline",
    "md_converter.renderer",
    "md_converter.services",
    "md_converter.quality_gate",
    "PySide6",
)


def _record(
    severity: str,
    code: str,
    *,
    user_message: str = "",
    message: str = "",
    source: str = "",
    location: Any = None,
) -> ApplicationDiagnostic:
    """Return one adapted diagnostic record."""
    return ApplicationDiagnostic(
        severity=severity,
        code=code,
        message=message or f"{code} technical message",
        user_message=user_message or f"{code} display message",
        source=source or None,
        location=location,
    )


def _result(records: List[ApplicationDiagnostic], *, status: ConversionStatus) -> ConversionResult:
    """Return a retained result carrying ``records`` as its diagnostics."""
    warnings = tuple(record for record in records if record.is_warning)
    errors = tuple(record for record in records if record.is_error)
    return ConversionResult(
        status=status,
        warnings=warnings,
        errors=errors,
        diagnostics=tuple(records),
        diagnostic_summary=DiagnosticSummary.from_records(records),
    )


# ============================================================
# Counts
# ============================================================


def test_no_findings_is_clean() -> None:
    """No retained diagnostic produces an empty, clean summary."""
    summary = preflight_from_diagnostics(())

    assert isinstance(summary, PreflightSummary)
    assert summary.is_clean is True
    assert (summary.total, summary.error_count, summary.warning_count, summary.info_count) == (
        0,
        0,
        0,
        0,
    )
    assert summary.rows() == ()
    assert summary.summary_text() == PREFLIGHT_CLEAN_TEXT
    assert summary.has_errors is False and summary.has_warnings is False


def test_none_input_is_clean() -> None:
    """``None`` is treated as "no diagnostics" rather than an error."""
    assert preflight_from_diagnostics(None).is_clean is True


def test_info_only_is_counted_as_information() -> None:
    """An information-only document is clean of warnings and errors."""
    summary = preflight_from_diagnostics([_record("INFO", "NORM001")])

    assert summary.info_count == 1
    assert summary.warning_count == 0
    assert summary.error_count == 0
    assert summary.is_clean is False
    assert summary.has_warnings is False and summary.has_errors is False
    assert summary.summary_text() == "1 information item."


def test_warning_only_is_counted_as_warning() -> None:
    """A warning-only document reports exactly one warning."""
    summary = preflight_from_diagnostics([_record("WARNING", "QA_STATIC_WARN")])

    assert (summary.warning_count, summary.error_count, summary.info_count) == (1, 0, 0)
    assert summary.summary_text() == "1 warning."


def test_mixed_severities_are_counted() -> None:
    """Counts follow the canonical severity semantics (FATAL counts as error)."""
    records = [
        _record("INFO", "INFO001"),
        _record("WARNING", "QA_STATIC_WARN"),
        _record("WARNING", "QA_RENDERED_WARN"),
        _record("ERROR", "PIPE001"),
        _record("FATAL", "FATAL001"),
    ]
    summary = preflight_from_diagnostics(records)

    assert summary.error_count == 2
    assert summary.warning_count == 2
    assert summary.info_count == 1
    assert summary.total == 5
    assert summary.counts_text() == "2 errors, 2 warnings, and 1 information item"


def test_counts_match_the_authoritative_summary() -> None:
    """Presented counts equal the authoritative counts: no drift, no invention."""
    records = [
        _record("INFO", "INFO001"),
        _record("WARNING", "QA_STATIC_WARN"),
        _record("ERROR", "PIPE001"),
    ]
    authoritative = DiagnosticSummary.from_records(records)
    summary = preflight_from_diagnostics(records)

    assert summary.total == authoritative.total
    assert summary.error_count == authoritative.errors
    assert summary.warning_count == authoritative.warnings
    assert summary.info_count == authoritative.infos


def test_counts_are_derived_from_the_presented_items() -> None:
    """Counts are properties of the items, so they cannot drift."""
    summary = preflight_from_diagnostics(
        [_record("WARNING", "QA_STATIC_WARN"), _record("INFO", "INFO001")]
    )

    assert summary.total == len(summary.items)
    assert summary.error_count + summary.warning_count + summary.info_count == summary.total


# ============================================================
# Ordering
# ============================================================


def test_ordering_puts_errors_first_then_warnings_then_info() -> None:
    """Grouping is deterministic and severity-ordered."""
    records = [
        _record("INFO", "INFO001"),
        _record("WARNING", "QA_STATIC_WARN"),
        _record("ERROR", "PIPE001"),
    ]
    summary = preflight_from_diagnostics(records)

    assert [item.code for item in summary.items] == [
        "PIPE001",
        "QA_STATIC_WARN",
        "INFO001",
    ]
    assert [item.severity for item in summary.items] == ["ERROR", "WARNING", "INFO"]


def test_ordering_is_stable_inside_a_severity_group() -> None:
    """The authoritative record order survives inside a severity group."""
    records = [
        _record("WARNING", "QA_STATIC_WARN", user_message="first"),
        _record("WARNING", "QA_RENDERED_WARN", user_message="second"),
        _record("WARNING", "QA_FINAL_WARN", user_message="third"),
    ]
    summary = preflight_from_diagnostics(records)

    assert [item.title for item in summary.items] == ["first", "second", "third"]


def test_ordering_is_deterministic() -> None:
    """The same records always produce the same order and rows."""
    records = [
        _record("INFO", "INFO001"),
        _record("ERROR", "PIPE001"),
        _record("WARNING", "QA_STATIC_WARN"),
    ]

    first = preflight_from_diagnostics(records)
    second = preflight_from_diagnostics(records)

    assert first.rows() == second.rows()
    assert [item.to_dict() for item in first.items] == [item.to_dict() for item in second.items]


# ============================================================
# Items and wording
# ============================================================


def test_row_text_carries_the_severity_word_code_and_marker() -> None:
    """A row is readable without colour: severity word plus bounded marker."""
    summary = preflight_from_diagnostics(
        [_record("WARNING", "QA_STATIC_WARN", user_message="A heading was adjusted.")]
    )
    row = summary.rows()[0]

    assert "WARNING" in row
    assert "QA_STATIC_WARN" in row
    assert "A heading was adjusted." in row
    assert row.startswith(MARKER_BY_SEVERITY["WARNING"])


def test_item_keeps_technical_evidence_secondary() -> None:
    """The display wording and the retained technical message stay separate."""
    summary = preflight_from_diagnostics(
        [
            _record(
                "WARNING",
                "QA_STATIC_WARN",
                user_message="Display wording.",
                message="Technical wording.",
                source="static_qa",
                location={"start_line": 12, "start_col": 1, "end_line": 12, "end_col": 4},
            )
        ]
    )
    item = summary.items[0]

    assert item.title == "Display wording."
    assert item.detail == "Technical wording."
    assert item.source == "static_qa"
    assert item.location == "line 12"
    assert item.display_title == "Display wording."


def test_degraded_findings_are_grouped_without_changing_severity() -> None:
    """Degradation grouping selects existing findings; it invents none."""
    records = [
        _record("WARNING", "POST002", user_message="Word post-processing unavailable."),
        _record("WARNING", "MD001", user_message="An image was not found."),
        _record("INFO", "INFO001"),
    ]
    summary = preflight_from_diagnostics(records)

    assert [item.code for item in summary.degradations()] == ["POST002", "MD001"]
    assert all(item.is_warning for item in summary.degradations())
    assert DEGRADED_CODES >= {"POST002", "MD001", "MD004", "DIAG001", "DIAG002", "DIAG003"}
    assert preflight_from_diagnostics([_record("INFO", "INFO001")]).degradations() == ()


# ============================================================
# Result adapter
# ============================================================


def test_preflight_from_result_reads_only_retained_evidence() -> None:
    """The result adapter reads the retained diagnostics, nothing else."""
    records = [_record("WARNING", "QA_STATIC_WARN")]
    result = _result(records, status=ConversionStatus.SUCCESS_WITH_WARNING)
    summary = preflight_from_result(result)

    assert summary.total == 1
    assert summary.warning_count == 1
    assert summary.items[0].code == "QA_STATIC_WARN"


def test_retained_wording_is_used_verbatim() -> None:
    """The authoritative summary wording is passed through, never re-phrased."""
    records = [_record("WARNING", "QA_STATIC_WARN")]
    result = _result(records, status=ConversionStatus.SUCCESS_WITH_WARNING)
    summary = preflight_from_result(result)

    assert result.diagnostic_summary is not None
    assert summary.summary_text() == result.diagnostic_summary.user_message


def test_failed_result_can_still_be_presented() -> None:
    """A failed result presents its retained error findings."""
    records = [_record("ERROR", "PIPE001"), _record("FATAL", "FATAL001")]
    result = ConversionResult(
        status=ConversionStatus.FAILED,
        errors=tuple(records),
        diagnostics=tuple(records),
        diagnostic_summary=DiagnosticSummary.from_records(records),
        error_category=ConversionErrorCategory.CONVERSION_ERROR,
        error_message="The document conversion failed.",
    )
    summary = preflight_from_result(result)

    assert summary.error_count == 2
    assert summary.has_errors is True
    assert summary.rows()[0].startswith(MARKER_BY_SEVERITY["ERROR"])


def test_result_without_diagnostics_is_clean() -> None:
    """A result with no retained diagnostics presents nothing."""
    result = ConversionResult(status=ConversionStatus.SUCCESS)

    assert preflight_from_result(result).is_clean is True


def test_findings_do_not_mutate_the_retained_result() -> None:
    """Presentation leaves the retained evidence completely unchanged."""
    records = [_record("WARNING", "QA_STATIC_WARN"), _record("INFO", "INFO001")]
    result = _result(records, status=ConversionStatus.SUCCESS_WITH_WARNING)
    before = result.to_dict()

    preflight_from_result(result)

    assert result.to_dict() == before


# ============================================================
# Robustness and architecture
# ============================================================


def test_unexpected_record_shapes_are_tolerated() -> None:
    """Malformed presentation input never breaks the surface (fail soft)."""
    mapping: Dict[str, Any] = {
        "severity": "warning",
        "code": "QA_STATIC_WARN",
        "message": "Technical wording.",
        "user_message": "Display wording.",
    }
    summary = preflight_from_diagnostics([None, mapping, object(), "not a record"])  # type: ignore[list-item]

    # ``None`` contributes nothing; the remaining three produce one item each.
    assert summary.total == 3
    assert summary.warning_count == 1
    assert summary.info_count == 2
    assert summary.items[0].severity == "WARNING"
    assert summary.items[0].code == "QA_STATIC_WARN"
    assert summary.items[1].severity == "INFO"
    assert summary.items[1].code == ""
    assert summary.items[1].display_title == ""
    assert summary.items[1].row_text().startswith(MARKER_BY_SEVERITY["INFO"])


def test_unknown_severity_keeps_its_text_and_sorts_last() -> None:
    """An unexpected severity is shown as information without losing its text."""
    records = [_record("NOTICE", "NOTE001"), _record("WARNING", "QA_STATIC_WARN")]
    summary = preflight_from_diagnostics(records)

    assert [item.severity for item in summary.items] == ["WARNING", "NOTICE"]
    assert summary.info_count == 1
    assert summary.warning_count == 1


def test_model_is_qt_free_and_reaches_no_core_stage() -> None:
    """The model imports the application layer only (Qt-free presentation)."""
    path = GUI_DIR / "preflight_model.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    package_parts = ["md_converter", "gui"]
    imported: set = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                keep = len(package_parts) - (node.level - 1)
                base = ".".join(package_parts[:keep]) if keep > 0 else ""
                module = f"{base}.{module}" if module else base
            if module:
                imported.add(module)

    offenders = {name for name in imported if name.startswith(FORBIDDEN_IMPORT_PREFIXES)}
    assert not offenders, sorted(offenders)
    assert "QDialog" not in path.read_text(encoding="utf-8")
