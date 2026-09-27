"""Focused verification for the bounded warning UX (WP-P12-06-03).

``SUCCESS_WITH_WARNING`` is a successful conversion that carries warnings.  The
GUI must keep it distinct from both plain ``SUCCESS`` and ``FAILED``, present a
concise warning summary from the presentation model, keep the warning evidence
discoverable, and keep a valid artifact presentation-actionable.
"""

from __future__ import annotations

import ast
import importlib
import os
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING, Callable, List, Set, Tuple

import pytest

from md_converter.application.conversion_result import ConversionResult

if TYPE_CHECKING:  # pragma: no cover - typing only
    from md_converter.gui.main_window import MainWindow

pytest.importorskip("PySide6", reason="PySide6 (GUI dev dependency) is not installed")

#: Qt needs a platform plugin even when a test only constructs widgets.  Set
#: here (not in a directory ``conftest.py``) because the test tree is not a
#: package and a second ``conftest`` would shadow ``md_converter/tests/conftest.py``.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from md_converter.gui.presentation_model import (  # noqa: E402 - the guard runs first
    SUMMARY_FAILED,
    TITLE_FAILED,
    PresentationOutcome,
)
from md_converter.gui.state import STATE_EFFECTS, GuiState  # noqa: E402 - the guard runs first

PROJECT_ROOT = Path(__file__).resolve().parents[3]
GUI_DIR = PROJECT_ROOT / "md_converter" / "gui"
MAIN_WINDOW_MODULE = "md_converter.gui.main_window"

#: Markdown that produces a warning diagnostic in the canonical pipeline.
WARNING_BODY = "#\n\nSome body text.\n"

#: Evidence fields the window must never read (no GUI-side recomputation).
FORBIDDEN_EVIDENCE_ATTRIBUTES = (
    "diagnostics",
    "diagnostic_summary",
    "errors",
    "quality_gate_report",
    "technical_detail",
    "warnings",
)

#: Core modules the GUI must never import directly (WP-P12-05-03 boundary).
FORBIDDEN_IMPORT_PREFIXES = (
    "md_converter.compiler",
    "md_converter.parser",
    "md_converter.pipeline",
    "md_converter.renderer",
    "md_converter.services",
    "md_converter.quality_gate",
)


def _gui_thread_id() -> int:
    """Return the id of the calling (GUI) thread."""
    return threading.get_ident()


def _pump() -> None:
    """Deliver pending Qt events (queued cross-thread signals)."""
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


def _warning_conversion(window: "MainWindow", tmp_path: Path, name: str = "warn.md") -> Path:
    """Drive the window into ``SUCCESS_WITH_WARNING`` through a real conversion."""
    source = _write_markdown(tmp_path / name, body=WARNING_BODY)
    _run_conversion(window, source)
    assert window.state is GuiState.SUCCESS_WITH_WARNING
    assert window.latest_result is not None
    return source


def _spy_on_details(monkeypatch: pytest.MonkeyPatch) -> List[Tuple[object, object, object]]:
    """Record calls to the bounded details surface."""
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


def _attribute_names(path: Path) -> Set[str]:
    """Return every attribute name accessed in ``path``."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}


# ============================================================
# Warning presentation
# ============================================================


def test_warning_result_shows_warning_presentation(window: "MainWindow", tmp_path: Path) -> None:
    """WP §3: a warning outcome presents a concise warning summary."""
    _warning_conversion(window, tmp_path)
    window.show()
    _pump()

    presentation = window.presentation
    assert presentation is not None
    assert presentation.outcome is PresentationOutcome.SUCCESS_WITH_WARNING
    assert presentation.is_success is True
    assert window.status_label.text() == STATE_EFFECTS[GuiState.SUCCESS_WITH_WARNING].status_text
    assert window.result_area.isVisible() is True
    assert window.result_summary_label.text() == presentation.summary
    assert window.details_button.isVisible() is True
    assert window.details_button.isEnabled() is True


def test_state_remains_success_with_warning(window: "MainWindow", tmp_path: Path) -> None:
    """WP §2: the GUI state stays ``SUCCESS_WITH_WARNING``, never ``FAILED``."""
    _warning_conversion(window, tmp_path)

    assert window.state is GuiState.SUCCESS_WITH_WARNING
    assert window.state is not GuiState.SUCCESS
    assert window.state is not GuiState.FAILED
    assert window.presentation is not None
    assert window.presentation.is_failure is False


def test_warning_summary_comes_from_the_presentation_model(
    window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WP §3: the visible summary is the presentation model's wording."""
    module = importlib.import_module(MAIN_WINDOW_MODULE)
    original = module.present_result
    calls: List[Tuple[ConversionResult, int]] = []

    def recording(result: ConversionResult):
        calls.append((result, threading.get_ident()))
        return original(result)

    monkeypatch.setattr(module, "present_result", recording)

    _warning_conversion(window, tmp_path)

    assert len(calls) == 1
    result, thread_id = calls[0]
    assert thread_id == _gui_thread_id()
    assert result is window.latest_result
    assert result.diagnostic_summary is not None
    assert window.result_summary_label.text() == result.diagnostic_summary.user_message
    assert window.result_summary_label.text() == original(result).summary


def test_warning_evidence_is_not_recomputed_in_main_window() -> None:
    """WP §4: the window never reads raw diagnostic evidence or counts."""
    attributes = _attribute_names(GUI_DIR / "main_window.py")

    offenders = attributes & set(FORBIDDEN_EVIDENCE_ATTRIBUTES)
    assert not offenders, sorted(offenders)


# ============================================================
# Warning evidence and details
# ============================================================


def test_warning_evidence_remains_intact(
    window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WP §5: presenting warnings never mutates the retained result."""
    _warning_conversion(window, tmp_path)
    result = window.latest_result
    assert result is not None
    assert result.warnings
    before = result.to_dict()
    before_warnings = [record.to_dict() for record in result.warnings]

    _spy_on_details(monkeypatch)
    window.show_details()
    other = _write_markdown(tmp_path / "other.md")
    window.set_source_file(str(other))
    _pump()

    assert window.latest_result is result
    assert result.to_dict() == before
    assert [record.to_dict() for record in result.warnings] == before_warnings


def test_warning_details_open_the_retained_evidence(
    window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WP §5/§6: the details affordance shows the retained warning evidence."""
    _warning_conversion(window, tmp_path)
    result = window.latest_result
    assert result is not None

    calls = _spy_on_details(monkeypatch)
    window.show()
    _pump()
    window.details_button.click()

    assert len(calls) == 1
    parent, presentation, evidence = calls[0]
    assert parent is window
    assert presentation is window.presentation
    assert evidence is result


def test_warning_details_follow_the_presentation_flag(
    window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WP §6: the affordance follows the presentation's evidence flag."""
    import dataclasses

    module = importlib.import_module(MAIN_WINDOW_MODULE)
    original = module.present_result

    def without_details(result: ConversionResult):
        return dataclasses.replace(original(result), details_available=False)

    monkeypatch.setattr(module, "present_result", without_details)
    calls = _spy_on_details(monkeypatch)

    _warning_conversion(window, tmp_path)
    window.show()
    _pump()

    assert window.presentation is not None
    assert window.presentation.details_available is False
    assert window.details_button.isVisible() is False
    assert window.details_button.isEnabled() is False
    assert window.show_details() is False
    assert calls == []
    # The warning summary stays visible even when details are unavailable.
    assert window.result_area.isVisible() is True
    assert window.result_summary_label.text() == window.presentation.summary


def test_warning_details_surface_is_read_only_and_lists_warnings(
    window: "MainWindow", tmp_path: Path
) -> None:
    """WP §5/§6: the shared surface renders warning evidence, not failures."""
    from md_converter.gui.result_details import (
        TITLE_WARNING_DETAILS,
        ResultDetailsDialog,
        presentation_evidence_text,
    )

    _warning_conversion(window, tmp_path)
    result = window.latest_result
    presentation = window.presentation
    assert result is not None and presentation is not None

    text = presentation_evidence_text(presentation, result)
    dialog = ResultDetailsDialog(presentation, text, window)
    try:
        assert dialog.windowTitle() == TITLE_WARNING_DETAILS
        assert dialog.summary_label.text() == presentation.summary
        assert dialog.evidence_view.isReadOnly() is True
        assert dialog.evidence_view.toPlainText() == text
        assert "Traceback" not in text
        for record in result.warnings:
            assert record.code in text
            assert record.user_message in text
    finally:
        dialog.close()


def test_compatibility_alias_matches_the_generalized_surface() -> None:
    """WP §"Details implementation rule": one implementation, one alias."""
    from md_converter.gui import failure_details, result_details

    assert failure_details.FailureDetailsDialog is result_details.ResultDetailsDialog
    assert failure_details.show_failure_details is result_details.show_result_details
    assert failure_details.failure_evidence_text is result_details.presentation_evidence_text
    assert failure_details.DETAILS_TITLE == result_details.TITLE_FAILURE_DETAILS


# ============================================================
# Output eligibility and failure separation
# ============================================================


def test_valid_output_remains_actionable(window: "MainWindow", tmp_path: Path) -> None:
    """WP §7: warnings never suppress artifact eligibility."""
    from PySide6.QtWidgets import QPushButton

    _warning_conversion(window, tmp_path)
    presentation = window.presentation
    assert presentation is not None

    assert presentation.output_path is not None
    assert presentation.output_path.exists()
    assert presentation.output_actionable is True

    # WP-P12-06-05 owns the Open Document / Open Folder controls.
    assert not hasattr(window, "open_document_button")
    assert not hasattr(window, "open_folder_button")
    object_names = [button.objectName().lower() for button in window.findChildren(QPushButton)]
    assert not [name for name in object_names if "open" in name]


def test_failed_ux_is_not_used_for_warnings(window: "MainWindow", tmp_path: Path) -> None:
    """WP §8: warning presentation never routes through failure semantics."""
    from md_converter.gui.result_details import TITLE_WARNING_DETAILS, details_title

    _warning_conversion(window, tmp_path)
    presentation = window.presentation
    assert presentation is not None

    assert presentation.outcome is not PresentationOutcome.FAILED
    assert presentation.is_infrastructure_failure is False
    assert presentation.summary != SUMMARY_FAILED
    assert window.result_summary_label.text() != SUMMARY_FAILED
    assert window.result_summary_label.text() != TITLE_FAILED
    assert "fail" not in window.result_summary_label.text().lower()
    assert details_title(presentation) == TITLE_WARNING_DETAILS


def test_success_warning_and_failed_stay_distinct(window: "MainWindow", tmp_path: Path) -> None:
    """WP §"SUCCESS UX boundary": SUCCESS != SUCCESS_WITH_WARNING != FAILED."""
    window.show()

    success_source = _write_markdown(tmp_path / "ok.md")
    _run_conversion(window, success_source)
    assert window.state is GuiState.SUCCESS
    _pump()
    assert window.result_area.isVisible() is False
    success_summary = window.presentation.summary if window.presentation else ""

    _warning_conversion(window, tmp_path)
    _pump()
    assert window.result_area.isVisible() is True
    warning_summary = window.result_summary_label.text()

    failed_source = _write_markdown(tmp_path / "empty.md", body="")
    _run_conversion(window, failed_source)
    _pump()
    assert window.state is GuiState.FAILED
    assert window.result_area.isVisible() is True
    failed_summary = window.result_summary_label.text()

    assert warning_summary and failed_summary
    assert warning_summary != failed_summary
    assert warning_summary != success_summary
    assert window.status_label.text() == STATE_EFFECTS[GuiState.FAILED].status_text


# ============================================================
# Evidence identity and workflow recovery
# ============================================================


def test_latest_result_remains_the_original_object(
    window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WP §9: the retained ``ConversionResult`` object is never replaced."""
    delivered: List[ConversionResult] = []
    window.worker.succeeded.connect(lambda result: delivered.append(result))

    _warning_conversion(window, tmp_path)

    assert delivered
    assert window.latest_result is delivered[0]
    assert window.presentation is not None
    before = window.latest_result.to_dict()

    # The bounded surface is stubbed: a real dialog would block on ``exec()``.
    _spy_on_details(monkeypatch)
    window.show_details()
    _pump()

    assert window.latest_result is delivered[0]
    assert window.latest_result.to_dict() == before


def test_new_source_recovers_to_ready_and_clears_warning_ux(
    window: "MainWindow", tmp_path: Path
) -> None:
    """WP §10: a new valid source returns to READY and clears the presentation."""
    _warning_conversion(window, tmp_path)
    retained = window.latest_result
    window.show()
    _pump()
    assert window.result_area.isVisible() is True

    recovered = _write_markdown(tmp_path / "recovered.md")
    assert window.set_source_file(str(recovered)) is GuiState.READY
    _pump()

    assert window.state is GuiState.READY
    assert window.result_area.isVisible() is False
    assert window.result_summary_label.text() == ""
    assert window.presentation is None
    assert window.latest_result is retained


def test_reset_recovers_to_empty_and_clears_warning_ux(
    window: "MainWindow", tmp_path: Path
) -> None:
    """WP §11: reset returns to EMPTY and clears the presentation."""
    _warning_conversion(window, tmp_path)
    window.show()
    _pump()
    assert window.result_area.isVisible() is True

    assert window.reset() is GuiState.EMPTY
    _pump()

    assert window.result_area.isVisible() is False
    assert window.presentation is None
    assert window.latest_result is not None


# ============================================================
# Presentation-model authority and architecture
# ============================================================


def test_warnings_do_not_use_the_failure_presentation_path(
    window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WP §12: the warning path never fabricates a failure presentation."""
    module = importlib.import_module(MAIN_WINDOW_MODULE)
    original = module.present_job_failure
    calls: List[object] = []

    def recording(failure):
        calls.append(failure)
        return original(failure)

    monkeypatch.setattr(module, "present_job_failure", recording)

    _warning_conversion(window, tmp_path)

    assert calls == []
    assert window.presentation is not None
    assert window.presentation.outcome is PresentationOutcome.SUCCESS_WITH_WARNING


def test_warning_ux_adds_no_conversion_core_import() -> None:
    """WP §13: the GUI still reaches the Core only through the application layer."""
    for module in (
        GUI_DIR / "main_window.py",
        GUI_DIR / "result_details.py",
        GUI_DIR / "failure_details.py",
    ):
        offenders = {
            name for name in _imported_modules(module) if name.startswith(FORBIDDEN_IMPORT_PREFIXES)
        }
        assert not offenders, f"{module.name} imports {sorted(offenders)}"
