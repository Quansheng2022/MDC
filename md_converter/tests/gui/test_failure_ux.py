"""Focused verification for the bounded failure UX (WP-P12-06-02).

Covers the two failure kinds (``ConversionResult.FAILED`` and worker
``JobFailure``), the presentation-model reuse, the bounded ``Details...``
affordance, evidence preservation, output-action safety and workflow recovery.
"""

from __future__ import annotations

import ast
import dataclasses
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
    PresentationOutcome,
    present_job_failure,
    present_result,
)
from md_converter.gui.state import GuiState  # noqa: E402 - the guard runs first

PROJECT_ROOT = Path(__file__).resolve().parents[3]
GUI_DIR = PROJECT_ROOT / "md_converter" / "gui"
MAIN_WINDOW_MODULE = "md_converter.gui.main_window"

#: Wording that would duplicate presentation-model semantics in the window.
FORBIDDEN_WINDOW_WORDING = (
    "Conversion failed",
    "An internal error",
    "The document could not be generated",
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


def _fail_conversion(window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Drive the window into the ``FAILED`` state through a real conversion."""
    source = _write_markdown(tmp_path / "empty.md", body="")
    _run_conversion(window, source)
    assert window.state is GuiState.FAILED
    assert window.latest_result is not None


def _crash_worker(window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Drive the window into the ``FAILED`` state through a worker failure."""
    source = _write_markdown(tmp_path / "notes.md")

    def exploding(request) -> ConversionResult:
        raise RuntimeError("service exploded")

    monkeypatch.setattr(window.service, "convert", exploding)
    _run_conversion(window, source)
    assert window.state is GuiState.FAILED
    assert window.latest_job_failure is not None
    assert window.latest_result is None


def _spy_on_details(monkeypatch: pytest.MonkeyPatch) -> List[Tuple[object, object, object]]:
    """Record calls to the bounded details surface."""
    module = importlib.import_module(MAIN_WINDOW_MODULE)
    calls: List[Tuple[object, object, object]] = []

    def recording(parent, presentation, evidence):
        calls.append((parent, presentation, evidence))

    monkeypatch.setattr(module, "show_result_details", recording)
    return calls


def _spy_on_service(window: "MainWindow", monkeypatch: pytest.MonkeyPatch) -> List[dict]:
    """Record real ``service.convert`` calls."""
    calls: List[dict] = []
    original = window.service.convert

    def recording(request) -> ConversionResult:
        calls.append({"thread": threading.get_ident(), "request": request})
        return original(request)

    monkeypatch.setattr(window.service, "convert", recording)
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


# ============================================================
# FAILED result UX
# ============================================================


def test_failed_result_shows_failure_presentation(
    window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WP §1: a failed conversion presents a clear failure state."""
    _fail_conversion(window, tmp_path, monkeypatch)
    window.show()
    _pump()

    presentation = window.presentation
    assert presentation is not None
    assert presentation.outcome is PresentationOutcome.FAILED
    assert presentation.is_failure is True
    assert window.status_label.text().startswith("Conversion failed")
    assert window.result_area.isVisible() is True
    assert window.result_summary_label.text() == presentation.summary
    assert window.details_button.isVisible() is True
    assert window.details_button.isEnabled() is True


def test_failed_summary_is_concise_and_plain(
    window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WP §1: the summary is short, user-facing and traceback-free."""
    _fail_conversion(window, tmp_path, monkeypatch)

    summary = window.result_summary_label.text()

    assert summary
    assert summary == window.presentation.summary
    assert "\n" not in summary
    assert "Traceback" not in summary
    assert len(summary) < 200
    # The technical evidence is retained for the details surface instead.
    assert window.latest_result is not None
    assert window.latest_result.technical_detail


def test_failed_result_details_show_retained_evidence(
    window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WP §1: the details surface carries the retained failure evidence."""
    _fail_conversion(window, tmp_path, monkeypatch)
    result = window.latest_result
    assert result is not None

    calls = _spy_on_details(monkeypatch)
    window.show()
    _pump()
    window.details_button.click()

    assert len(calls) == 1
    parent, shown, evidence = calls[0]
    assert parent is window
    assert shown is window.presentation
    assert evidence is result


# ============================================================
# JobFailure UX
# ============================================================


def test_job_failure_shows_distinct_infrastructure_presentation(
    window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WP §2: worker failure is presented as an infrastructure failure."""
    _crash_worker(window, tmp_path, monkeypatch)
    window.show()
    _pump()

    presentation = window.presentation
    assert presentation is not None
    assert presentation.outcome is PresentationOutcome.INFRASTRUCTURE_FAILURE
    assert presentation.is_infrastructure_failure is True
    assert presentation.summary != window.status_label.text()
    assert "RuntimeError" in presentation.summary
    assert window.result_area.isVisible() is True
    assert window.result_summary_label.text() == presentation.summary
    assert window.details_button.isVisible() is True
    # No fabricated application result was produced.
    assert window.latest_result is None
    assert window.latest_job_failure is not None


def test_failed_and_infrastructure_presentations_differ(
    window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WP §2: the two failure kinds never share one presentation."""
    _fail_conversion(window, tmp_path, monkeypatch)
    failed_presentation = window.presentation
    assert failed_presentation is not None

    source = _write_markdown(tmp_path / "other.md")

    def exploding(request) -> ConversionResult:
        raise RuntimeError("service exploded")

    monkeypatch.setattr(window.service, "convert", exploding)
    _run_conversion(window, source)
    infrastructure_presentation = window.presentation
    assert infrastructure_presentation is not None

    assert failed_presentation.outcome is not infrastructure_presentation.outcome
    assert failed_presentation.title != infrastructure_presentation.title
    assert failed_presentation.summary != infrastructure_presentation.summary
    assert failed_presentation.is_infrastructure_failure is False
    assert infrastructure_presentation.is_infrastructure_failure is True


# ============================================================
# Details affordance
# ============================================================


def test_details_affordance_follows_presentation_evidence(
    window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WP §4: the affordance follows the presentation's evidence flag."""
    module = importlib.import_module(MAIN_WINDOW_MODULE)
    original = module.present_result

    def without_details(result: ConversionResult):
        return dataclasses.replace(original(result), details_available=False)

    monkeypatch.setattr(module, "present_result", without_details)
    calls = _spy_on_details(monkeypatch)

    _fail_conversion(window, tmp_path, monkeypatch)
    window.show()
    _pump()

    assert window.presentation is not None
    assert window.presentation.details_available is False
    assert window.details_button.isVisible() is False
    assert window.details_button.isEnabled() is False
    assert window.show_details() is False
    assert calls == []


def test_details_is_unavailable_without_a_failure(window: "MainWindow") -> None:
    """No failure presentation means no details surface."""
    assert window.presentation is None
    assert window.show_details() is False
    assert window.result_area.isVisible() is False
    assert window.details_button.isVisible() is False


def test_details_dialog_is_read_only_and_evidence_driven(
    window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WP §1/§2: the bounded surface is read-only and shows retained evidence."""
    from md_converter.gui.result_details import (
        CLOSE_TEXT,
        TITLE_FAILURE_DETAILS,
        ResultDetailsDialog,
        presentation_evidence_text,
    )
    from md_converter.gui.worker import JobFailure

    _fail_conversion(window, tmp_path, monkeypatch)
    result = window.latest_result
    assert result is not None
    presentation = present_result(result)

    dialog = ResultDetailsDialog(
        presentation, presentation_evidence_text(presentation, result), window
    )
    try:
        assert dialog.windowTitle() == TITLE_FAILURE_DETAILS
        assert dialog.summary_label.text() == presentation.summary
        assert dialog.evidence_view.isReadOnly() is True
        assert dialog.evidence_view.toPlainText() == presentation_evidence_text(
            presentation, result
        )
        assert result.technical_detail.splitlines()[0] in dialog.evidence_view.toPlainText()
        assert dialog.close_button.text() == CLOSE_TEXT
    finally:
        dialog.close()

    failure = JobFailure.from_exception(RuntimeError("service exploded"))
    failure_presentation = present_job_failure(failure)
    failure_dialog = ResultDetailsDialog(
        failure_presentation, presentation_evidence_text(failure_presentation, failure), window
    )
    try:
        text = failure_dialog.evidence_view.toPlainText()
        assert "RuntimeError: service exploded" in text
        assert failure.traceback.strip() in text
        assert failure_dialog.evidence_view.isReadOnly() is True
    finally:
        failure_dialog.close()


# ============================================================
# Output action safety
# ============================================================


def test_no_output_action_is_offered_after_failure(
    window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WP §5: failures never expose an actionable output artifact.

    WP-P12-06-05 added the output controls; for a failure they stay hidden and
    disabled, so no misleading action is offered.
    """
    _fail_conversion(window, tmp_path, monkeypatch)
    window.show()
    _pump()

    assert window.presentation is not None
    assert window.presentation.output_actionable is False
    for button in (window.open_document_button, window.open_folder_button):
        assert button.isEnabled() is False
        assert button.isVisible() is False
    assert window.open_output_document() is False
    assert window.open_output_folder() is False


# ============================================================
# Evidence preservation
# ============================================================


def test_latest_result_is_retained_unchanged(
    window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WP §6: presenting a failure never mutates the retained result."""
    _fail_conversion(window, tmp_path, monkeypatch)
    result = window.latest_result
    assert result is not None
    before = result.to_dict()

    _spy_on_details(monkeypatch)
    window.show_details()
    window.set_source("other.md")
    _pump()

    assert window.latest_result is result
    assert result.to_dict() == before


def test_latest_job_failure_is_retained_unchanged(
    window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WP §7: presenting an infrastructure failure never mutates its evidence."""
    _crash_worker(window, tmp_path, monkeypatch)
    failure = window.latest_job_failure
    assert failure is not None
    before = dataclasses.asdict(failure)

    _spy_on_details(monkeypatch)
    window.show_details()
    window.set_source("other.md")
    _pump()

    assert window.latest_job_failure is failure
    assert dataclasses.asdict(failure) == before


# ============================================================
# Workflow recovery
# ============================================================


def test_new_valid_source_recovers_and_clears_failure_ux(
    window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WP §9/§10: a new source returns to READY and clears the failure UX."""
    _fail_conversion(window, tmp_path, monkeypatch)
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


def test_reset_clears_failure_ux(
    window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WP §10: resetting clears the failure presentation."""
    _fail_conversion(window, tmp_path, monkeypatch)
    window.show()
    _pump()
    assert window.result_area.isVisible() is True

    assert window.reset() is GuiState.EMPTY
    _pump()

    assert window.result_area.isVisible() is False
    assert window.presentation is None


def test_recovery_then_failure_presents_the_new_failure(
    window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WP §10: the failure UX updates for a later failure."""
    _fail_conversion(window, tmp_path, monkeypatch)
    first = window.presentation

    second_source = _write_markdown(tmp_path / "second.md", body="")
    _run_conversion(window, second_source)

    assert window.state is GuiState.FAILED
    assert window.presentation is not None
    assert window.presentation is not first
    assert window.result_summary_label.text() == window.presentation.summary


def test_showing_details_does_not_re_execute_conversion(
    window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WP §11: the failure UX never starts another conversion."""
    calls = _spy_on_service(window, monkeypatch)
    source = _write_markdown(tmp_path / "empty.md", body="")
    _run_conversion(window, source)
    assert len(calls) == 1

    _spy_on_details(monkeypatch)
    window.show_details()
    window.set_source("other.md")
    window.request_convert()
    _pump()

    assert len(calls) == 1
    assert window.worker.is_running is False


# ============================================================
# Presentation-model authority and architecture
# ============================================================


def test_production_ux_reuses_the_presentation_model(
    window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WP §8: the window consumes the model instead of building wording."""
    module = importlib.import_module(MAIN_WINDOW_MODULE)
    original = module.present_result
    calls: List[Tuple[ConversionResult, int]] = []

    def recording(result: ConversionResult):
        calls.append((result, threading.get_ident()))
        return original(result)

    monkeypatch.setattr(module, "present_result", recording)

    _fail_conversion(window, tmp_path, monkeypatch)

    assert len(calls) == 1
    result, thread_id = calls[0]
    assert thread_id == _gui_thread_id()
    assert result is window.latest_result
    assert window.result_summary_label.text() == original(result).summary


def test_window_contains_no_duplicated_presentation_wording() -> None:
    """WP §8: title/summary wording lives in the presentation model only."""
    text = (GUI_DIR / "main_window.py").read_text(encoding="utf-8")

    for wording in FORBIDDEN_WINDOW_WORDING:
        assert wording not in text, wording


def test_failure_ux_adds_no_conversion_core_import() -> None:
    """WP §12: the GUI still reaches the Core only through the application layer."""
    for module in (GUI_DIR / "main_window.py", GUI_DIR / "result_details.py"):
        offenders = {
            name for name in _imported_modules(module) if name.startswith(FORBIDDEN_IMPORT_PREFIXES)
        }
        assert not offenders, f"{module.name} imports {sorted(offenders)}"
