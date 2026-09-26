"""Focused tests for the application diagnostics adapter (WP-P12-03-03)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from md_converter.application import DiagnosticsAdapter
from md_converter.ast.nodes import SourceSpan
from md_converter.diagnostics.collector import DiagnosticCollector
from md_converter.diagnostics.diagnostic import Severity
from md_converter.renderer.post_processor import DocxPostProcessor


class _StubContext:
    """Minimal stand-in for the evidence surface the adapter consumes."""

    def __init__(
        self,
        collector: DiagnosticCollector,
        report: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.diag = collector
        self._report = report

    def get_quality_gate_report(self) -> Optional[Dict[str, Any]]:
        return self._report


def _collector() -> DiagnosticCollector:
    return DiagnosticCollector()


# ============================================================
# Summary counts
# ============================================================


def test_zero_diagnostics() -> None:
    """A clean conversion reports an empty, clean summary."""
    bundle = DiagnosticsAdapter().build(_StubContext(_collector()))

    assert bundle.diagnostics == ()
    assert bundle.summary.total == 0
    assert bundle.summary.is_clean is True
    assert bundle.summary.has_errors is False
    assert bundle.summary.has_warnings is False
    assert bundle.summary.user_message == "Conversion completed with no diagnostics."


def test_warnings_only() -> None:
    """Warnings are counted and summarised without errors."""
    collector = _collector()
    collector.warning("empty heading", code="QA_STATIC_WARN", source="static_qa")
    collector.warning("table clipped", code="QA_RENDER_WARN", source="rendered_qa")

    bundle = DiagnosticsAdapter().build(_StubContext(collector))

    assert bundle.summary.total == 2
    assert bundle.summary.warnings == 2
    assert bundle.summary.errors == 0
    assert bundle.summary.has_warnings is True
    assert bundle.summary.user_message == "Conversion reported 2 warnings."
    assert [record.code for record in bundle.warnings] == ["QA_STATIC_WARN", "QA_RENDER_WARN"]


def test_informational_notes_only() -> None:
    """Informational records are reported without claiming a silent run."""
    collector = _collector()
    collector.info("diagram pass skipped", code="INFO000")

    bundle = DiagnosticsAdapter().build(_StubContext(collector))

    assert bundle.summary.total == 1
    assert bundle.summary.infos == 1
    assert bundle.summary.has_warnings is False
    assert bundle.summary.is_clean is False
    assert bundle.summary.user_message == "Conversion completed with 1 informational note."


def test_errors_present_including_fatal() -> None:
    """FATAL counts as an error without redefining severity semantics."""
    collector = _collector()
    collector.error("build gate failed", code="QA_STATIC_ERR", source="static_qa")
    collector.fatal("cannot continue", code="PIPE001")

    bundle = DiagnosticsAdapter().build(_StubContext(collector))

    assert bundle.summary.errors == 2
    assert bundle.summary.has_errors is True
    assert bundle.summary.total == 2
    assert bundle.summary.user_message == "Conversion reported 2 errors."
    assert bundle.diagnostics[1].severity == "FATAL"


def test_mixed_severity_counts() -> None:
    """Info, warning and error severities are counted independently."""
    collector = _collector()
    collector.info("diagram pass skipped", code="INFO000")
    collector.warning("empty heading", code="QA_STATIC_WARN")
    collector.error("image missing", code="MD001")

    bundle = DiagnosticsAdapter().build(_StubContext(collector))

    assert bundle.summary.total == 3
    assert bundle.summary.infos == 1
    assert bundle.summary.warnings == 1
    assert bundle.summary.errors == 1
    assert bundle.summary.user_message == (
        "Conversion reported 1 error, 1 warning, and 1 informational note."
    )


# ============================================================
# Evidence retention
# ============================================================


def test_code_message_location_and_details_retained() -> None:
    """Technical evidence is preserved next to the display-safe wording."""
    collector = _collector()
    collector.warning(
        "Table 1: width exceeds content width",
        code="QA_RENDER_WARN",
        location=SourceSpan(3, 1, 3, 20),
        suggestion="Consider landscape orientation.",
        source="rendered_qa",
        data={"table_index": 1},
    )

    bundle = DiagnosticsAdapter().build(_StubContext(collector))
    record = bundle.diagnostics[0]

    assert record.code == "QA_RENDER_WARN"
    assert record.message == "Table 1: width exceeds content width"
    assert record.severity == Severity.WARNING.name
    assert record.location == {
        "start_line": 3,
        "start_col": 1,
        "end_line": 3,
        "end_col": 20,
    }
    assert record.suggestion == "Consider landscape orientation."
    assert record.source == "rendered_qa"
    assert record.stage == "rendered_qa"
    assert record.details == {"table_index": 1}


def test_known_com_warning_is_mapped_to_user_wording() -> None:
    """The existing COM degradation warning maps to display-safe text."""
    collector = _collector()
    collector.warning(
        "Word COM unavailable (win32com.client unavailable); "
        "native TOC field kept, page numbers refresh with F9 in Word",
        code=DocxPostProcessor.COM_DIAGNOSTIC_CODE,
        source="post_processor",
    )

    bundle = DiagnosticsAdapter().build(_StubContext(collector))
    record = bundle.diagnostics[0]

    assert record.code == "POST002"
    assert record.user_message == (
        "Word post-processing was unavailable. "
        "The document was generated with limited post-processing."
    )
    assert "Word COM unavailable" in record.message
    assert record.stage == "post_processor"


def test_unknown_code_falls_back_to_original_message() -> None:
    """Unmapped codes keep their canonical message as display text."""
    collector = _collector()
    collector.warning("something new happened", code="XX999")

    bundle = DiagnosticsAdapter().build(_StubContext(collector))

    assert bundle.diagnostics[0].user_message == "something new happened"


def test_custom_user_message_map_can_be_extended() -> None:
    """Callers may extend display wording without redefining QA semantics."""
    collector = _collector()
    collector.warning("internal text", code="XX999")
    adapter = DiagnosticsAdapter(user_message_map={"XX999": "Friendly text."})

    bundle = adapter.build(_StubContext(collector))

    assert bundle.diagnostics[0].user_message == "Friendly text."
    assert bundle.diagnostics[0].message == "internal text"


# ============================================================
# Quality-gate evidence
# ============================================================


def test_quality_gate_report_passed_through_unmodified() -> None:
    """The canonical quality-gate report is attached verbatim."""
    report: Dict[str, Any] = {
        "static_qa": {"status": "PASS", "errors": [], "warnings": []},
        "artifact_sha256": "abc123",
    }

    bundle = DiagnosticsAdapter().build(_StubContext(_collector(), report))

    assert bundle.quality_gate_report == report


def test_quality_gate_report_is_copied_not_aliased() -> None:
    """Adapting evidence does not hand out a mutable internal reference."""
    report: Dict[str, Any] = {"static_qa": {"status": "PASS"}}

    bundle = DiagnosticsAdapter().build(_StubContext(_collector(), report))
    bundle.quality_gate_report["static_qa"]["status"] = "MUTATED"  # type: ignore[index]

    assert report["static_qa"]["status"] == "PASS"


def test_missing_quality_gate_report_is_none() -> None:
    """Absent QA evidence is ``None``, not an invented score."""
    bundle = DiagnosticsAdapter().build(_StubContext(_collector()))

    assert bundle.quality_gate_report is None


def test_bundle_serialises_for_logging() -> None:
    """The bundle has a JSON-serialisable representation."""
    collector = _collector()
    collector.warning("empty heading", code="QA_STATIC_WARN")

    data = DiagnosticsAdapter().build(_StubContext(collector)).to_dict()

    assert data["summary"]["warnings"] == 1
    assert data["diagnostics"][0]["code"] == "QA_STATIC_WARN"


def test_adapter_source_contains_no_gui_framework(tmp_path: Path) -> None:
    """The adapter stays usable without a GUI framework."""
    import md_converter.application.diagnostics_adapter as module

    text = Path(module.__file__).read_text(encoding="utf-8")

    assert "PySide6" not in text
    assert "PyQt" not in text
