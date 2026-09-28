"""Focused verification for the unified report surface (WP-P12-06-04).

The report surface must be one read-only, on-demand view over retained evidence:
warnings, failures and worker infrastructure failures all render through
:mod:`md_converter.gui.result_details`, with the presentation model supplying
title/summary/outcome and no recomputation of diagnostics anywhere.
"""

from __future__ import annotations

import ast
import dataclasses
import importlib
import os
import time
from pathlib import Path
from typing import TYPE_CHECKING, Callable, List, Optional, Set, Tuple

import pytest

from md_converter.application.conversion_result import (
    ConversionErrorCategory,
    ConversionResult,
    ConversionStatus,
)
from md_converter.application.diagnostics_adapter import (
    ApplicationDiagnostic,
    DiagnosticSummary,
)

if TYPE_CHECKING:  # pragma: no cover - typing only
    from md_converter.gui.main_window import MainWindow

pytest.importorskip("PySide6", reason="PySide6 (GUI dev dependency) is not installed")

#: Qt needs a platform plugin even when a test only constructs widgets.  Set
#: here (not in a directory ``conftest.py``) because the test tree is not a
#: package and a second ``conftest`` would shadow ``md_converter/tests/conftest.py``.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from md_converter.gui.presentation_model import (  # noqa: E402 - the guard runs first
    present_job_failure,
    present_result,
)
from md_converter.gui.state import GuiState  # noqa: E402 - the guard runs first

PROJECT_ROOT = Path(__file__).resolve().parents[3]
GUI_DIR = PROJECT_ROOT / "md_converter" / "gui"
MAIN_WINDOW_MODULE = "md_converter.gui.main_window"

#: Core modules the GUI must never import directly (WP-P12-05-03 boundary).
FORBIDDEN_IMPORT_PREFIXES = (
    "md_converter.compiler",
    "md_converter.diagnostics",
    "md_converter.parser",
    "md_converter.pipeline",
    "md_converter.renderer",
    "md_converter.services",
    "md_converter.quality_gate",
)

#: Core/QA entry points the report surface must never call.
FORBIDDEN_CALL_TARGETS = (
    "CompilerContext",
    "DiagnosticCollector",
    "MarkdownParser",
    "WordRenderer",
    "compile_file",
    "get_quality_gate_report",
)

#: Evidence fields the window must never read (no GUI-side interpretation).
FORBIDDEN_WINDOW_ATTRIBUTES = (
    "diagnostics",
    "diagnostic_summary",
    "errors",
    "quality_gate_report",
    "technical_detail",
    "warnings",
)


def _record(
    severity: str,
    code: str,
    user_message: Optional[str] = None,
) -> ApplicationDiagnostic:
    """Return one adapted diagnostic record."""
    return ApplicationDiagnostic(
        severity=severity,
        code=code,
        message=f"{code} technical message",
        user_message=user_message or f"{code} display message",
    )


def _rich_result() -> ConversionResult:
    """Return a failed result carrying every kind of retained evidence."""
    records = (
        _record("INFO", "INFO001"),
        _record("WARNING", "QA_STATIC_WARN"),
        _record("ERROR", "PIPE001"),
        _record("FATAL", "FATAL001"),
    )
    return ConversionResult(
        status=ConversionStatus.FAILED,
        source_path=Path("notes.md"),
        output_path=Path("out") / "partial.docx",
        warnings=tuple(record for record in records if record.is_warning),
        errors=tuple(record for record in records if record.is_error),
        diagnostics=records,
        diagnostic_summary=DiagnosticSummary.from_records(records),
        quality_gate_report={
            "policy": {
                "fail_on_error": True,
                "fail_on_warning": False,
                "max_repair_iterations": 0,
            },
            "static_qa": {"status": "FAIL", "errors": 1, "warnings": 1},
            "post_processor": None,
            "rendered_qa": {"status": "SKIPPED"},
            "final_artifact_qa": None,
            "repair_evidence": [],
            "artifact_sha256": "abc123",
        },
        error_category=ConversionErrorCategory.CONVERSION_ERROR,
        error_message="The document conversion failed. (pipeline step failed)",
        technical_detail="ValueError: pipeline step failed\nTraceback (most recent call last): ...",
    )


def _warning_result() -> ConversionResult:
    """Return a successful result carrying warning evidence."""
    records = (_record("WARNING", "QA_STATIC_WARN"),)
    return ConversionResult(
        status=ConversionStatus.SUCCESS_WITH_WARNING,
        output_path=Path("out") / "warned.docx",
        warnings=records,
        diagnostics=records,
        diagnostic_summary=DiagnosticSummary.from_records(records),
    )


def _minimal_success() -> ConversionResult:
    """Return a clean result with no optional evidence at all."""
    return ConversionResult(status=ConversionStatus.SUCCESS)


@dataclasses.dataclass(frozen=True)
class _StubFailure:
    """Structural stand-in for retained worker-failure evidence."""

    error_type: str = "RuntimeError"
    message: str = "service exploded"
    traceback: str = (
        'Traceback (most recent call last):\n  File "x.py", line 1\nRuntimeError: service exploded'
    )


def _pump() -> None:
    """Deliver pending Qt events."""
    from PySide6.QtWidgets import QApplication

    QApplication.processEvents()


def _wait_until(predicate: Callable[[], bool], timeout_ms: int = 20000) -> bool:
    """Process GUI events until ``predicate`` holds, or the timeout expires."""
    deadline = time.monotonic() + timeout_ms / 1000.0
    while time.monotonic() < deadline:
        _pump()
        if predicate():
            return True
        time.sleep(0.005)
    return predicate()


def _write_markdown(path: Path, body: str = "# Notes\n\nBody text.\n") -> Path:
    """Write ``body`` as UTF-8 Markdown and return the path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


@pytest.fixture
def window(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> "MainWindow":
    """Provide a window with a deterministic service, idle again at teardown."""
    from md_converter.application.conversion_service import ConversionService
    from md_converter.gui.app import create_application
    from md_converter.gui.main_window import MainWindow

    monkeypatch.chdir(tmp_path)
    create_application([])

    instance = MainWindow()
    instance.service = ConversionService({"word_com": False})
    yield instance

    assert _wait_until(lambda: not instance.worker.is_running), "worker did not stop"
    instance.close()
    _pump()


def _run_conversion(window: "MainWindow", source: Path) -> None:
    """Run one real conversion through the window and wait for completion."""
    assert window.set_source_file(str(source)) is GuiState.READY
    window.start_conversion()
    assert _wait_until(
        lambda: window.state is not GuiState.CONVERTING and not window.worker.is_running
    )


def _spy_on_details(monkeypatch: pytest.MonkeyPatch) -> List[Tuple[object, object, object]]:
    """Record calls to the unified report surface."""
    module = importlib.import_module(MAIN_WINDOW_MODULE)
    calls: List[Tuple[object, object, object]] = []

    def recording(parent, presentation, evidence):
        calls.append((parent, presentation, evidence))

    monkeypatch.setattr(module, "show_result_details", recording)
    return calls


def _imported_modules(path: Path) -> Set[str]:
    """Return the import targets of ``path``, resolving relative imports."""
    package_parts = list(path.resolve().relative_to(PROJECT_ROOT).with_suffix("").parts)[:-1]
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                keep = len(package_parts) - (node.level - 1)
                base = ".".join(package_parts[:keep]) if keep > 0 else ""
                module = f"{base}.{module}" if module else base
            if module:
                names.add(module)
                names.update(f"{module}.{alias.name}" for alias in node.names)
    return names


def _call_targets(path: Path) -> Set[str]:
    """Return the simple names of every call target in ``path``."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            target = node.func
            if isinstance(target, ast.Name):
                names.add(target.id)
            elif isinstance(target, ast.Attribute):
                names.add(target.attr)
    return names


def _report(evidence: object) -> str:
    """Return the report text for ``evidence``."""
    from md_converter.gui.result_details import build_report_text

    if isinstance(evidence, _StubFailure):
        return build_report_text(present_job_failure(evidence), evidence)
    return build_report_text(present_result(evidence), evidence)


# ============================================================
# One unified surface
# ============================================================


def test_only_one_report_surface_exists() -> None:
    """WP §17: no second diagnostics/report dialog module exists.

    WP-P12-07 adds two further bounded user-facing dialogs (Settings and
    About).  Neither renders retained conversion evidence, so the guard pins the
    complete set of dialog modules: a new unbounded dialog still fails it, and
    the report surface itself stays exactly one module.

    SBC-05 adds one further bounded surface, ``batch_report.py``, which renders
    the *aggregate* batch summary (and opens the single report surface for a
    selected row).  It builds no second result taxonomy and no second wording:
    it reuses :mod:`md_converter.gui.batch` and
    :func:`md_converter.gui.result_details.show_result_details`.
    """
    from PySide6.QtWidgets import QDialog

    from md_converter.gui import result_details

    dialog_modules = set()
    for module in sorted(GUI_DIR.glob("*.py")):
        tree = ast.parse(module.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            bases = {base.id for base in node.bases if isinstance(base, ast.Name)}
            bases |= {base.attr for base in node.bases if isinstance(base, ast.Attribute)}
            if "QDialog" in bases:
                dialog_modules.add(module.name)

    assert dialog_modules == {
        "about_dialog.py",
        "batch_report.py",
        "result_details.py",
        "settings_dialog.py",
    }
    assert result_details.ResultDetailsDialog.__mro__[1] is QDialog
    # The WP-P12-06-02 module is a pure alias: no implementation, no classes.
    alias_tree = ast.parse((GUI_DIR / "failure_details.py").read_text(encoding="utf-8"))
    assert not [n for n in ast.walk(alias_tree) if isinstance(n, ast.ClassDef)]


def test_all_presented_outcomes_route_to_the_single_surface(
    window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WP §1/§2/§3: warning, failure and JobFailure share one surface."""
    from md_converter.gui.result_details import show_result_details

    module = importlib.import_module(MAIN_WINDOW_MODULE)
    assert module.show_result_details is show_result_details

    calls = _spy_on_details(monkeypatch)
    window.show()

    warning_source = _write_markdown(tmp_path / "warn.md", body="#\n\nBody text.\n")
    _run_conversion(window, warning_source)
    assert window.state is GuiState.SUCCESS_WITH_WARNING
    window.details_button.click()

    failed_source = _write_markdown(tmp_path / "empty.md", body="")
    _run_conversion(window, failed_source)
    assert window.state is GuiState.FAILED
    window.details_button.click()
    failed_evidence = window.latest_result

    def exploding(request) -> ConversionResult:
        raise RuntimeError("service exploded")

    monkeypatch.setattr(window.service, "convert", exploding)
    crash_source = _write_markdown(tmp_path / "notes.md")
    _run_conversion(window, crash_source)
    assert window.state is GuiState.FAILED
    window.details_button.click()

    assert len(calls) == 3
    assert [call[1].outcome.value for call in calls] == [
        "SUCCESS_WITH_WARNING",
        "FAILED",
        "INFRASTRUCTURE_FAILURE",
    ]
    assert calls[1][2] is failed_evidence
    assert calls[2][2] is window.latest_job_failure
    assert all(call[0] is window for call in calls)


# ============================================================
# Report content
# ============================================================


def test_warning_report_is_warning_oriented() -> None:
    """WP §5: warning evidence renders in the unified surface."""
    from md_converter.gui.result_details import details_title

    result = _warning_result()
    presentation = present_result(result)
    text = _report(result)

    assert details_title(presentation) == "Warning details"
    assert "Status: SUCCESS_WITH_WARNING" in text
    assert "Warnings (1)" in text
    assert "QA_STATIC_WARN: QA_STATIC_WARN display message" in text
    assert "Traceback" not in text


def test_failure_report_renders_errors_and_output_path() -> None:
    """WP §6/§11: error and output-path evidence render."""
    result = _rich_result()
    presentation = present_result(result)
    text = _report(result)

    assert presentation.title in text
    assert "Status: FAILED" in text
    assert f"Output path: {result.output_path}" in text
    assert "Errors (2)" in text
    assert "PIPE001: PIPE001 display message" in text
    assert "FATAL001: FATAL001 display message" in text


def test_all_diagnostics_render_with_severity() -> None:
    """WP §7: every retained diagnostic record renders."""
    result = _rich_result()
    text = _report(result)

    assert "Diagnostics (4)" in text
    for record in result.diagnostics:
        assert f"[{record.severity}] {record.code}: {record.user_message}" in text


def test_diagnostic_summary_renders() -> None:
    """WP §8: the retained summary counts and wording render."""
    result = _rich_result()
    summary = result.diagnostic_summary
    assert summary is not None
    text = _report(result)

    assert "Diagnostic summary" in text
    assert f"Total: {summary.total}" in text
    assert f"Errors: {summary.errors}" in text
    assert f"Warnings: {summary.warnings}" in text
    assert f"Info: {summary.infos}" in text
    assert summary.user_message in text


def test_quality_gate_report_renders() -> None:
    """WP §9: meaningful gate entries render; empty ones are skipped."""
    text = _report(_rich_result())

    assert "Quality gate report" in text
    assert "static_qa: FAIL (errors=1, warnings=1)" in text
    assert "rendered_qa: SKIPPED" in text
    assert "artifact_sha256: abc123" in text
    assert "policy: fail_on_error=True, fail_on_warning=False, max_repair_iterations=0" in text
    assert "post_processor" not in text
    assert "final_artifact_qa" not in text
    assert "repair_evidence" not in text


def test_technical_detail_renders() -> None:
    """WP §10: retained technical detail renders verbatim."""
    result = _rich_result()
    text = _report(result)

    assert "Technical detail" in text
    assert result.technical_detail is not None
    assert result.technical_detail in text


def test_job_failure_report_is_separate_but_same_surface() -> None:
    """WP §3: infrastructure evidence renders distinctly, never merged."""
    from md_converter.gui.result_details import details_title

    failure = _StubFailure()
    presentation = present_job_failure(failure)
    text = _report(failure)

    assert details_title(presentation) == "Failure details"
    assert "Status: INFRASTRUCTURE_FAILURE" in text
    assert "Exception type: RuntimeError" in text
    assert "Exception message: service exploded" in text
    assert failure.traceback in text
    assert "Warnings (" not in text
    assert "Diagnostics (" not in text


def test_missing_optional_evidence_produces_no_empty_sections() -> None:
    """WP §12: a minimal result renders without noisy empty sections."""
    result = _minimal_success()
    presentation = present_result(result)
    text = _report(result)

    assert presentation.title in text
    assert "Status: SUCCESS" in text
    assert "Summary: " in text
    for absent in (
        "Output path:",
        "Warnings (",
        "Errors (",
        "Diagnostics (",
        "Diagnostic summary",
        "Quality gate report",
        "Technical detail",
    ):
        assert absent not in text, absent

    # The dialog itself must build cleanly for such a result.
    from PySide6.QtWidgets import QApplication

    QApplication.instance() or QApplication([])
    from md_converter.gui.result_details import ResultDetailsDialog

    dialog = ResultDetailsDialog(presentation, text)
    try:
        assert dialog.evidence_view.toPlainText() == text
    finally:
        dialog.close()


def test_report_is_deterministic() -> None:
    """The same evidence always renders the same text."""
    result = _rich_result()

    assert _report(result) == _report(result)
    assert _report(_StubFailure()) == _report(_StubFailure())


# ============================================================
# Read-only behaviour
# ============================================================


def test_report_surface_is_read_only() -> None:
    """WP §4: the unified surface exposes no editable widget."""
    from PySide6.QtWidgets import QApplication, QLineEdit, QPlainTextEdit, QTextEdit

    QApplication.instance() or QApplication([])
    from md_converter.gui.result_details import ResultDetailsDialog

    presentation = present_result(_rich_result())
    dialog = ResultDetailsDialog(presentation, _report(_rich_result()))
    try:
        widgets = (
            list(dialog.findChildren(QPlainTextEdit))
            + list(dialog.findChildren(QTextEdit))
            + list(dialog.findChildren(QLineEdit))
        )
        assert widgets
        for widget in widgets:
            assert widget.isReadOnly() is True
        assert dialog.evidence_view.toPlainText() == _report(_rich_result())
    finally:
        dialog.close()


def test_copy_action_copies_the_report_text() -> None:
    """WP §"Copy action": the optional copy action copies the report verbatim."""
    from PySide6.QtWidgets import QApplication

    application = QApplication.instance() or QApplication([])
    from md_converter.gui.result_details import ResultDetailsDialog

    text = _report(_rich_result())
    dialog = ResultDetailsDialog(present_result(_rich_result()), text)
    try:
        dialog.copy_button.click()
        _pump()
        assert application.clipboard().text() == text
    finally:
        dialog.close()


# ============================================================
# Evidence preservation and architecture
# ============================================================


def test_report_never_mutates_retained_evidence() -> None:
    """WP §13: rendering leaves the retained result completely unchanged."""
    from PySide6.QtWidgets import QApplication

    QApplication.instance() or QApplication([])
    from md_converter.gui.result_details import ResultDetailsDialog

    result = _rich_result()
    before = result.to_dict()
    warnings_before = [record.to_dict() for record in result.warnings]
    diagnostics_before = [record.to_dict() for record in result.diagnostics]

    presentation = present_result(result)
    text = _report(result)
    dialog = ResultDetailsDialog(presentation, text)
    dialog.close()
    assert _report(result) == text

    assert result.to_dict() == before
    assert [record.to_dict() for record in result.warnings] == warnings_before
    assert [record.to_dict() for record in result.diagnostics] == diagnostics_before


def test_retained_counts_are_displayed_not_recomputed() -> None:
    """WP §"no recomputation": retained summary numbers win over a recount."""
    records = (_record("WARNING", "QA_STATIC_WARN"),)
    retained = DiagnosticSummary(
        total=7,
        errors=1,
        warnings=5,
        infos=1,
        has_errors=True,
        has_warnings=True,
        is_clean=False,
        user_message="Retained summary wording.",
    )
    result = ConversionResult(
        status=ConversionStatus.SUCCESS_WITH_WARNING,
        warnings=records,
        diagnostics=records,
        diagnostic_summary=retained,
    )

    text = _report(result)

    assert "Total: 7" in text
    assert "Warnings: 5" in text
    assert "Retained summary wording." in text
    # The record list still shows exactly the retained record.
    assert "Warnings (1)" in text


def test_main_window_stays_insulated_from_raw_diagnostics() -> None:
    """WP §14: the window never interprets raw diagnostic fields."""
    tree = ast.parse((GUI_DIR / "main_window.py").read_text(encoding="utf-8"))
    attributes = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}

    offenders = attributes & set(FORBIDDEN_WINDOW_ATTRIBUTES)
    assert not offenders, sorted(offenders)


def test_report_surface_calls_no_core_or_qa_entry_point() -> None:
    """WP §15: the report imports and calls nothing from the Core/QA stages."""
    for module in (GUI_DIR / "result_details.py", GUI_DIR / "main_window.py"):
        offenders = {
            name for name in _imported_modules(module) if name.startswith(FORBIDDEN_IMPORT_PREFIXES)
        }
        assert not offenders, f"{module.name} imports {sorted(offenders)}"

        calls = _call_targets(module) & set(FORBIDDEN_CALL_TARGETS)
        assert not calls, f"{module.name} calls {sorted(calls)}"


def test_report_module_has_no_output_side_effects() -> None:
    """WP §4: the surface neither prints nor writes anything."""
    calls = _call_targets(GUI_DIR / "result_details.py")

    assert "print" not in calls
    assert "open" not in calls
    assert "write_text" not in calls
