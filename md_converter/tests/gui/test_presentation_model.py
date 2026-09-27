"""Focused verification for the GUI presentation model (WP-P12-06-01).

The presentation model is the single GUI boundary between retained evidence
(``ConversionResult`` / ``JobFailure``) and presentation data.  These tests
verify the required properties:

* SUCCESS / SUCCESS_WITH_WARNING / FAILED / JobFailure mappings;
* evidence immutability - the retained result is only read, never rebuilt;
* deterministic counts derived directly from retained evidence;
* output actionability derived from ``result.output_path`` alone;
* the Qt-free and Core-free module boundary.
"""

from __future__ import annotations

import ast
import dataclasses
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import pytest

pytest.importorskip("PySide6", reason="PySide6 (GUI dev dependency) is not installed")

from md_converter.application.conversion_result import (  # noqa: E402 - the guard runs first
    ConversionErrorCategory,
    ConversionResult,
    ConversionStatus,
)
from md_converter.application.diagnostics_adapter import (  # noqa: E402 - the guard runs first
    ApplicationDiagnostic,
    DiagnosticSummary,
)
from md_converter.gui.presentation_model import (  # noqa: E402 - the guard runs first
    SEVERITY_BY_OUTCOME,
    SUMMARY_FAILED,
    SUMMARY_INFRASTRUCTURE_FAILURE,
    TITLE_FAILED,
    TITLE_INFRASTRUCTURE_FAILURE,
    TITLE_SUCCESS,
    TITLE_SUCCESS_WITH_WARNING,
    PresentationOutcome,
    present_job_failure,
    present_result,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
GUI_DIR = PROJECT_ROOT / "md_converter" / "gui"
SOURCE = GUI_DIR / "presentation_model.py"

#: Core compiler stages the presentation model must not import directly.
_CORE_PACKAGES = (
    "compiler",
    "parser",
    "pipeline",
    "renderer",
    "diagnostics",
    "quality_gate",
    "services",
    "utils",
    "constants",
)

#: Only the standard library and the application layer may be imported.
_ALLOWED_ABSOLUTE_IMPORTS = ("__future__", "dataclasses", "enum", "pathlib", "typing")

_PROBE_SENTINEL = "GUI_MODULES="


@dataclass(frozen=True)
class _StubFailure:
    """Minimal structural stand-in for the retained worker-failure evidence."""

    error_type: str = "RuntimeError"
    message: str = "worker exploded"
    traceback: str = "Traceback (most recent call last):\nRuntimeError: worker exploded"


def _warning_record(code: str = "QA_STATIC_WARN") -> ApplicationDiagnostic:
    """Return one warning-level application diagnostic."""
    return ApplicationDiagnostic(
        severity="WARNING",
        code=code,
        message="document heading is empty",
        user_message="A document quality warning was reported.",
    )


def _error_record(code: str = "PIPE001") -> ApplicationDiagnostic:
    """Return one error-level application diagnostic."""
    return ApplicationDiagnostic(
        severity="ERROR",
        code=code,
        message="pipeline step failed",
        user_message="A document transformation step failed.",
    )


def _success_result(output: Optional[Path] = None) -> ConversionResult:
    """Return a minimal clean successful result."""
    return ConversionResult(
        status=ConversionStatus.SUCCESS,
        source_path=Path("notes.md"),
        output_path=output,
        diagnostic_summary=DiagnosticSummary.from_records(()),
    )


def _warning_result(
    output: Optional[Path] = None,
    records: Tuple[ApplicationDiagnostic, ...] = (),
) -> ConversionResult:
    """Return a successful result carrying warning evidence."""
    evidence = records or (_warning_record(),)
    return ConversionResult(
        status=ConversionStatus.SUCCESS_WITH_WARNING,
        source_path=Path("warn.md"),
        output_path=output,
        warnings=evidence,
        diagnostics=evidence,
        diagnostic_summary=DiagnosticSummary.from_records(evidence),
    )


def _failed_result(**overrides: object) -> ConversionResult:
    """Return a failed result carrying retained technical evidence."""
    fields: dict = {
        "status": ConversionStatus.FAILED,
        "source_path": Path("empty.md"),
        "error_category": ConversionErrorCategory.CONVERSION_ERROR,
        "error_message": "The document conversion failed. (empty document)",
        "technical_detail": "ValueError: empty document",
    }
    fields.update(overrides)
    return ConversionResult(**fields)


def _artifact(tmp_path: Path) -> Path:
    """Create a placeholder artifact and return its path."""
    path = tmp_path / "report.docx"
    path.write_bytes(b"placeholder")
    return path


def _imported_modules(path: Path) -> set:
    """Return the module names imported by ``path``."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module:
                names.add(module)
            names.update(f"{module}.{alias.name}".lstrip(".") for alias in node.names)
    return names


def _relative_imports(path: Path) -> List[Tuple[int, str]]:
    """Return the ``(level, module)`` pairs of the relative imports in ``path``."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [
        (node.level, node.module or "")
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    ]


# ============================================================
# Outcome mapping
# ============================================================


def test_success_maps_to_success_presentation(tmp_path: Path) -> None:
    """SUCCESS presents as a completed conversion with an actionable artifact."""
    output = _artifact(tmp_path)

    presentation = present_result(_success_result(output))

    assert presentation.outcome is PresentationOutcome.SUCCESS
    assert presentation.title == TITLE_SUCCESS
    assert presentation.severity == "success"
    assert presentation.summary == "Conversion completed with no diagnostics."
    assert presentation.warning_count == 0
    assert presentation.error_count == 0
    assert presentation.is_success is True
    assert presentation.is_failure is False
    assert presentation.output_path == output
    assert presentation.output_actionable is True


def test_success_with_warning_stays_a_success(tmp_path: Path) -> None:
    """SUCCESS_WITH_WARNING is never presented as a failure."""
    output = _artifact(tmp_path)

    presentation = present_result(_warning_result(output))

    assert presentation.outcome is PresentationOutcome.SUCCESS_WITH_WARNING
    assert presentation.outcome is not PresentationOutcome.FAILED
    assert presentation.title == TITLE_SUCCESS_WITH_WARNING
    assert presentation.severity == "warning"
    assert presentation.summary == "Conversion reported 1 warning."
    assert presentation.warning_count == 1
    assert presentation.error_count == 0
    assert presentation.is_success is True
    assert presentation.is_failure is False
    assert presentation.output_actionable is True


def test_warning_summary_is_derived_when_no_summary_is_retained() -> None:
    """A count-based warning summary is used when no summary object exists."""
    records = (_warning_record("W1"), _warning_record("W2"))
    result = ConversionResult(
        status=ConversionStatus.SUCCESS_WITH_WARNING,
        warnings=records,
    )

    presentation = present_result(result)

    assert presentation.summary == "Conversion reported 2 warnings."
    assert presentation.warning_count == 2


def test_failed_maps_to_failure_presentation() -> None:
    """FAILED presents as a failure carrying the retained plain-language text."""
    result = _failed_result()

    presentation = present_result(result)

    assert presentation.outcome is PresentationOutcome.FAILED
    assert presentation.title == TITLE_FAILED
    assert presentation.severity == "error"
    assert presentation.summary == result.error_message
    assert presentation.details_available is True
    assert presentation.is_failure is True
    assert presentation.is_success is False
    assert presentation.output_actionable is False


def test_failed_summary_falls_back_to_plain_language() -> None:
    """A failure without a message still presents a plain-language summary."""
    presentation = present_result(_failed_result(error_message=None, technical_detail=None))

    assert presentation.summary == SUMMARY_FAILED


def test_failed_never_offers_output_actions(tmp_path: Path) -> None:
    """A failed conversion disables output actions even if an artifact exists."""
    artifact = _artifact(tmp_path)

    presentation = present_result(_failed_result(output_path=artifact))

    assert presentation.output_actionable is False
    # The retained evidence is still exposed untouched.
    assert presentation.output_path == artifact


def test_job_failure_maps_to_infrastructure_failure() -> None:
    """Worker failure stays distinct from an application failure."""
    failure = _StubFailure()

    presentation = present_job_failure(failure)

    assert presentation.outcome is PresentationOutcome.INFRASTRUCTURE_FAILURE
    assert presentation.is_infrastructure_failure is True
    assert presentation.title == TITLE_INFRASTRUCTURE_FAILURE
    assert presentation.title != TITLE_FAILED
    assert presentation.severity == "error"
    assert presentation.summary != SUMMARY_FAILED
    assert failure.error_type in presentation.summary
    assert presentation.details_available is True
    assert presentation.is_failure is True
    assert presentation.output_actionable is False
    assert presentation.output_path is None
    assert (presentation.warning_count, presentation.error_count) == (0, 0)


def test_job_failure_summary_is_plain_without_a_type() -> None:
    """Missing failure details still produce bounded plain-language wording."""
    presentation = present_job_failure(_StubFailure(error_type=""))

    assert presentation.summary == SUMMARY_INFRASTRUCTURE_FAILURE


def test_real_job_failure_satisfies_the_boundary() -> None:
    """The retained worker evidence maps through the structural boundary."""
    from md_converter.gui.worker import JobFailure

    failure = JobFailure.from_exception(RuntimeError("service exploded"))
    before = dataclasses.asdict(failure)

    presentation = present_job_failure(failure)

    assert presentation.outcome is PresentationOutcome.INFRASTRUCTURE_FAILURE
    assert "RuntimeError" in presentation.summary
    assert dataclasses.asdict(failure) == before


def test_every_outcome_is_reachable() -> None:
    """The four retained evidence kinds cover the presentation outcomes."""
    outcomes = {
        present_result(_success_result()).outcome,
        present_result(_warning_result()).outcome,
        present_result(_failed_result()).outcome,
        present_job_failure(_StubFailure()).outcome,
    }

    assert outcomes == set(PresentationOutcome)
    assert set(SEVERITY_BY_OUTCOME) == set(PresentationOutcome)


# ============================================================
# Evidence preservation and counts
# ============================================================


@pytest.mark.parametrize(
    "builder",
    (_success_result, _warning_result, _failed_result),
)
def test_evidence_is_preserved_unchanged(builder) -> None:
    """The retained result is only read - presentation never mutates it."""
    result = builder()
    before = result.to_dict()

    first = present_result(result)
    second = present_result(result)

    assert result.to_dict() == before
    assert first == second


def test_counts_prefer_the_retained_summary() -> None:
    """Adapted summary counts are used verbatim when they are retained."""
    records = (_warning_record(), _error_record(), _error_record("PIPE002"))
    summary = DiagnosticSummary.from_records(records)
    result = _failed_result(
        warnings=records[:1],
        errors=records[1:],
        diagnostics=records,
        diagnostic_summary=summary,
    )

    presentation = present_result(result)

    assert (presentation.warning_count, presentation.error_count) == (
        summary.warnings,
        summary.errors,
    )
    assert (presentation.warning_count, presentation.error_count) == (1, 2)


def test_counts_fall_back_to_retained_records() -> None:
    """Without a summary the retained records are counted directly."""
    result = _failed_result(
        warnings=(_warning_record(),),
        errors=(_error_record(),),
    )

    presentation = present_result(result)

    assert (presentation.warning_count, presentation.error_count) == (1, 1)


def test_presentation_is_immutable() -> None:
    """Presentation data is a frozen value object."""
    presentation = present_result(_success_result())

    with pytest.raises(dataclasses.FrozenInstanceError):
        presentation.summary = "changed"  # type: ignore[misc]


def test_output_actionability_requires_an_existing_artifact(tmp_path: Path) -> None:
    """Eligibility follows the retained output path and its presence on disk."""
    existing = _artifact(tmp_path)
    missing = tmp_path / "deleted.docx"

    assert present_result(_success_result(existing)).output_actionable is True
    assert present_result(_warning_result(existing)).output_actionable is True
    assert present_result(_success_result(missing)).output_actionable is False
    assert present_result(_success_result(None)).output_actionable is False


def test_output_path_is_never_derived() -> None:
    """The retained output path is exposed verbatim."""
    retained = Path("somewhere") / "custom-name.docx"

    presentation = present_result(_success_result(retained))

    assert presentation.output_path == retained


# ============================================================
# Module boundary
# ============================================================


def test_module_is_qt_free_and_core_free() -> None:
    """The presentation model imports no GUI framework and no Core stage."""
    text = SOURCE.read_text(encoding="utf-8")
    imported = _imported_modules(SOURCE)

    assert not [name for name in imported if name.startswith(("PySide6", "PyQt5", "PyQt6"))]
    assert "PySide6" not in text
    assert "PyQt" not in text

    for level, module in _relative_imports(SOURCE):
        if level == 0:
            assert module in _ALLOWED_ABSOLUTE_IMPORTS, module
            continue
        assert level == 2, (level, module)
        assert module.split(".")[0] not in _CORE_PACKAGES, module


def test_module_does_not_reinterpret_or_rebuild_evidence() -> None:
    """Status interpretation stays centralized and no result is fabricated."""
    text = SOURCE.read_text(encoding="utf-8")

    assert "ConversionStatus" not in text
    assert "ConversionResult(" not in text
    assert "JobFailure(" not in text


def test_importing_the_module_pulls_no_gui_framework() -> None:
    """Importing the presentation model alone must not load Qt."""
    code = "\n".join(
        [
            "import importlib, sys, types",
            "import md_converter",
            "package = types.ModuleType('md_converter.gui')",
            f"package.__path__ = [{str(GUI_DIR)!r}]",
            "sys.modules['md_converter.gui'] = package",
            "importlib.import_module('md_converter.gui.presentation_model')",
            "names = {'PySide6', 'PyQt5', 'PyQt6'}",
            "loaded = sorted(n for n in sys.modules if n.split('.')[0] in names)",
            f"print('{_PROBE_SENTINEL}' + ','.join(loaded))",
        ]
    )

    proc = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )

    assert proc.returncode == 0, proc.stderr
    lines = [line for line in proc.stdout.splitlines() if line.startswith(_PROBE_SENTINEL)]
    assert lines == [_PROBE_SENTINEL]
