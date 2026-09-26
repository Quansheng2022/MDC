"""Focused verification for ConversionResult -> GuiState mapping (WP-P12-05-04).

Covers the centralized mapping, result retention (complete evidence kept for
P12-06), worker-failure semantics, GUI-thread completion, and the rule that the
production path never depends on the P12-04 ``simulate_*`` mock helpers.
"""

from __future__ import annotations

import ast
import importlib
import os
import threading
import time
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Callable, List, Tuple

import pytest

from md_converter.application.conversion_result import (
    ConversionErrorCategory,
    ConversionResult,
    ConversionStatus,
)
from md_converter.application.diagnostics_adapter import ApplicationDiagnostic

if TYPE_CHECKING:  # pragma: no cover - typing only
    from md_converter.gui.main_window import MainWindow

pytest.importorskip("PySide6", reason="PySide6 (GUI dev dependency) is not installed")

#: Qt needs a platform plugin even when a test only constructs widgets.  Set
#: here (not in a directory ``conftest.py``) because the test tree is not a
#: package and a second ``conftest`` would shadow ``md_converter/tests/conftest.py``.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from md_converter.gui.result_mapping import (  # noqa: E402 - the Qt guard must run first
    RESULT_STATE_MAP,
    UNMAPPED_RESULT_STATE,
    gui_state_for_result,
)
from md_converter.gui.state import GuiState  # noqa: E402 - the Qt guard must run first

PROJECT_ROOT = Path(__file__).resolve().parents[3]
GUI_DIR = PROJECT_ROOT / "md_converter" / "gui"
MAIN_WINDOW_MODULE = "md_converter.gui.main_window"

#: Application status -> expected GUI state (WP §3).
EXPECTED_MAPPING = (
    (ConversionStatus.SUCCESS, GuiState.SUCCESS),
    (ConversionStatus.SUCCESS_WITH_WARNING, GuiState.SUCCESS_WITH_WARNING),
    (ConversionStatus.FAILED, GuiState.FAILED),
)

#: Mock helpers the production path must not call (WP §4).
MOCK_HELPER_PREFIX = "simulate_"


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


def _module_names(path: Path) -> set:
    """Return identifier and attribute names referenced in ``path``."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    names |= {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    return names


def _result_for(status: ConversionStatus) -> ConversionResult:
    """Return a minimal valid result for ``status``."""
    if status is ConversionStatus.SUCCESS_WITH_WARNING:
        return ConversionResult(
            status=status,
            warnings=(
                ApplicationDiagnostic(
                    severity="WARNING",
                    code="QA_STATIC_WARN",
                    message="empty heading",
                    user_message="A document quality warning was reported.",
                ),
            ),
        )
    if status is ConversionStatus.FAILED:
        return ConversionResult(
            status=status,
            error_category=ConversionErrorCategory.CONVERSION_ERROR,
        )
    return ConversionResult(status=status)


# ============================================================
# The mapping itself
# ============================================================


@pytest.mark.parametrize(("status", "expected"), EXPECTED_MAPPING)
def test_status_maps_to_gui_state(status: ConversionStatus, expected: GuiState) -> None:
    """WP §3: each application status maps to its GUI state."""
    assert gui_state_for_result(_result_for(status)) is expected


def test_mapping_covers_every_application_status() -> None:
    """No application status is left unmapped."""
    assert set(RESULT_STATE_MAP) == set(ConversionStatus)
    assert set(RESULT_STATE_MAP.values()) == {
        GuiState.SUCCESS,
        GuiState.SUCCESS_WITH_WARNING,
        GuiState.FAILED,
    }


def test_unrecognised_status_fails_closed() -> None:
    """An outcome the GUI cannot interpret never reports success."""
    foreign = SimpleNamespace(status="NOT_A_STATUS")

    assert gui_state_for_result(foreign) is UNMAPPED_RESULT_STATE
    assert UNMAPPED_RESULT_STATE is GuiState.FAILED


def test_mapping_preserves_result_evidence() -> None:
    """WP §5: the mapping never mutates or flattens result evidence."""
    result = ConversionResult(
        status=ConversionStatus.FAILED,
        error_category=ConversionErrorCategory.CONVERSION_ERROR,
        error_message="boom",
        technical_detail="traceback text",
        quality_gate_report={"static_qa": {"status": "FAIL"}},
    )
    before = result.to_dict()

    assert gui_state_for_result(result) is GuiState.FAILED
    assert result.to_dict() == before


# ============================================================
# Production path
# ============================================================


def test_production_completion_uses_the_central_mapping(
    window: "MainWindow", monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """WP §3/§7: the window maps results through the single centralized path."""
    module = importlib.import_module(MAIN_WINDOW_MODULE)
    original = module.gui_state_for_result
    calls: List[Tuple[ConversionResult, int]] = []

    def recording(result: ConversionResult) -> GuiState:
        calls.append((result, threading.get_ident()))
        return original(result)

    monkeypatch.setattr(module, "gui_state_for_result", recording)
    source = _write_markdown(tmp_path / "notes.md")

    _run_conversion(window, source)

    assert len(calls) == 1
    asserted_result, thread_id = calls[0]
    assert thread_id == _gui_thread_id()
    assert asserted_result is window.latest_result
    assert window.state is original(asserted_result)


def test_success_result_maps_to_success_state(window: "MainWindow", tmp_path: Path) -> None:
    """READY -> CONVERTING -> SUCCESS with the result retained."""
    source = _write_markdown(tmp_path / "notes.md")

    _run_conversion(window, source)

    assert window.state is GuiState.SUCCESS
    assert window.worker.is_running is False
    assert window.latest_result is not None
    assert window.latest_result.status is ConversionStatus.SUCCESS


def test_warning_result_maps_to_warning_state(window: "MainWindow", tmp_path: Path) -> None:
    """A warning outcome maps to SUCCESS_WITH_WARNING, not to SUCCESS."""
    source = _write_markdown(tmp_path / "warn.md", body="#\n\nSome body text.\n")

    _run_conversion(window, source)

    assert window.state is GuiState.SUCCESS_WITH_WARNING
    assert window.latest_result is not None
    assert window.latest_result.status is ConversionStatus.SUCCESS_WITH_WARNING
    assert window.latest_result.warnings


def test_failed_result_maps_to_failed_state(window: "MainWindow", tmp_path: Path) -> None:
    """A failed outcome maps to FAILED and keeps its technical evidence."""
    source = _write_markdown(tmp_path / "empty.md", body="")

    _run_conversion(window, source)

    assert window.state is GuiState.FAILED
    assert window.latest_result is not None
    assert window.latest_result.status is ConversionStatus.FAILED
    assert window.latest_result.technical_detail
    assert window.latest_job_failure is None


def test_latest_result_retains_complete_evidence(window: "MainWindow", tmp_path: Path) -> None:
    """WP §5: diagnostics, QA evidence and output path survive retention."""
    source = _write_markdown(tmp_path / "notes.md")
    delivered: List[ConversionResult] = []
    window.worker.succeeded.connect(lambda result: delivered.append(result))

    _run_conversion(window, source)

    retained = window.latest_result
    assert retained is not None and delivered and retained is delivered[0]
    assert retained.to_dict() == delivered[0].to_dict()
    assert retained.output_path is not None and retained.output_path.exists()
    assert retained.quality_gate_report
    assert retained.diagnostic_summary is not None


def test_worker_failure_leaves_failed_without_fabricated_result(
    window: "MainWindow", monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """WP §3/§5: infrastructure failure keeps its own semantics."""
    source = _write_markdown(tmp_path / "notes.md")

    def exploding(request):
        raise RuntimeError("service exploded")

    monkeypatch.setattr(window.service, "convert", exploding)

    _run_conversion(window, source)

    assert window.state is GuiState.FAILED
    assert window.latest_job_failure is not None
    assert window.latest_job_failure.error_type == "RuntimeError"
    assert window.latest_result is None


def test_new_source_after_completion_returns_to_ready(window: "MainWindow", tmp_path: Path) -> None:
    """WP §6: the workflow recovers to READY after completion."""
    first = _write_markdown(tmp_path / "first.md")
    second = _write_markdown(tmp_path / "second.md")

    _run_conversion(window, first)
    assert window.state is GuiState.SUCCESS

    assert window.set_source_file(str(second)) is GuiState.READY
    assert window.worker.is_running is False
    assert window.latest_result is not None


# ============================================================
# Centralization and mock-hook guards
# ============================================================


def test_status_interpretation_is_centralized() -> None:
    """WP §3: only the mapping module interprets ``ConversionStatus``."""
    modules_with_status = set()

    for module in sorted(GUI_DIR.glob("*.py")):
        if "ConversionStatus" in _module_names(module):
            modules_with_status.add(module.name)

    assert modules_with_status == {"result_mapping.py"}


def test_production_path_does_not_call_mock_helpers() -> None:
    """WP §4: the real conversion path never depends on ``simulate_*``."""
    guarded = {"start_conversion", "_on_conversion_result", "_on_conversion_failure"}
    tree = ast.parse((GUI_DIR / "main_window.py").read_text(encoding="utf-8"))

    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or node.name not in guarded:
            continue
        for call in (n for n in ast.walk(node) if isinstance(n, ast.Call)):
            target = call.func
            name = target.attr if isinstance(target, ast.Attribute) else getattr(target, "id", "")
            assert not name.startswith(MOCK_HELPER_PREFIX), f"{node.name} calls {name}"
