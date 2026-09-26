"""Focused verification for the real conversion vertical slice (WP-P12-05-03).

Proves: READY -> Convert -> CONVERTING -> one worker job -> real
``ConversionService.convert`` off the GUI thread -> real DOCX artifact ->
result delivered on the GUI thread -> GUI leaves CONVERTING.  One deterministic
failure slice is covered too.

The window runs a deterministic service configuration (``word_com: False``) so
the slice does not depend on optional Word automation being available.
"""

from __future__ import annotations

import importlib
import os
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING, Callable, List, Optional

import pytest

from md_converter.application.conversion_request import ConversionRequest
from md_converter.application.conversion_result import ConversionResult, ConversionStatus

if TYPE_CHECKING:  # pragma: no cover - typing only
    from md_converter.gui.main_window import MainWindow

pytest.importorskip("PySide6", reason="PySide6 (GUI dev dependency) is not installed")

#: Qt needs a platform plugin even when a test only constructs widgets.  Set
#: here (not in a directory ``conftest.py``) because the test tree is not a
#: package and a second ``conftest`` would shadow ``md_converter/tests/conftest.py``.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from md_converter.gui.state import GuiState  # noqa: E402 - the Qt guard must run first

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MAIN_WINDOW_MODULE = "md_converter.gui.main_window"


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
    """Provide a window with a deterministic service, idle again at teardown.

    The working directory is the test's temp directory so the service's default
    output location resolves inside it.  Waiting for the worker to go idle before
    teardown keeps Qt thread teardown away from pytest's capture teardown.
    """
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


def _spy_on_service(
    window: "MainWindow",
    monkeypatch: pytest.MonkeyPatch,
    block: Optional[threading.Event] = None,
) -> List[dict]:
    """Record real ``service.convert`` calls (thread id and request)."""
    calls: List[dict] = []
    original = window.service.convert

    def recording(request: ConversionRequest) -> ConversionResult:
        calls.append({"thread": threading.get_ident(), "request": request})
        if block is not None:
            block.wait(10)
        return original(request)

    monkeypatch.setattr(window.service, "convert", recording)
    return calls


def _spy_on_request_builder(monkeypatch: pytest.MonkeyPatch) -> List[tuple]:
    """Record calls to the shared request builder used by MainWindow."""
    module = importlib.import_module(MAIN_WINDOW_MODULE)
    built: List[tuple] = []
    original = module.build_conversion_request

    def recording(*args, **kwargs):
        built.append((args, kwargs))
        return original(*args, **kwargs)

    monkeypatch.setattr(module, "build_conversion_request", recording)
    return built


# ============================================================
# Success slice
# ============================================================


def test_real_conversion_vertical_slice(
    window: "MainWindow", monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """WP §7: real DOCX through worker + service, completion back on the GUI."""
    source = _write_markdown(tmp_path / "notes.md")
    calls = _spy_on_service(window, monkeypatch)
    built = _spy_on_request_builder(monkeypatch)
    results: List[tuple] = []
    window.worker.succeeded.connect(lambda result: results.append((result, threading.get_ident())))

    window.show()
    assert window.set_source_file(str(source)) is GuiState.READY

    window.convert_button.click()
    assert window.state is GuiState.CONVERTING
    assert _wait_until(
        lambda: window.state is not GuiState.CONVERTING and not window.worker.is_running
    )

    # Exactly one service call, executed outside the GUI thread.
    assert len(calls) == 1
    assert calls[0]["thread"] != _gui_thread_id()
    assert isinstance(calls[0]["request"], ConversionRequest)

    # The shared request builder was reused (no duplicated request logic).
    assert built and built[0][0][0] == str(source)

    # The result came back to the GUI thread and the GUI left CONVERTING.
    assert results and results[0][1] == _gui_thread_id()
    result = results[0][0]
    assert isinstance(result, ConversionResult)
    assert result.status is ConversionStatus.SUCCESS
    assert window.state is GuiState.SUCCESS

    # A real DOCX artifact exists on disk.
    assert result.output_path is not None
    assert result.output_path.exists()
    assert result.output_path.stat().st_size > 0
    assert result.output_path.read_bytes().startswith(b"PK")


def test_output_folder_intent_reaches_the_service_request(
    window: "MainWindow", monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The GUI folder preference reaches the service as configuration intent."""
    from md_converter.gui.request_builder import OUTPUT_DIR_CONFIG_KEY

    source = _write_markdown(tmp_path / "notes.md")
    output_dir = tmp_path / "exports"
    output_dir.mkdir()
    calls = _spy_on_service(window, monkeypatch)
    results: List[ConversionResult] = []
    window.worker.succeeded.connect(lambda result: results.append(result))

    window.set_source_file(str(source))
    window.set_output_directory(output_dir)
    window.start_conversion()
    assert _wait_until(lambda: not window.worker.is_running)

    assert len(calls) == 1
    request = calls[0]["request"]
    assert request.config_overrides == {OUTPUT_DIR_CONFIG_KEY: str(output_dir)}
    assert request.output_path is None

    result = results[0]
    assert result.status is ConversionStatus.SUCCESS
    assert result.output_path is not None
    assert result.output_path.parent == output_dir


# ============================================================
# Failure slice
# ============================================================


def test_service_failure_leaves_converting(
    window: "MainWindow", monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """WP §8: a real service failure still leaves CONVERTING safely."""
    source = _write_markdown(tmp_path / "empty.md", body="")
    calls = _spy_on_service(window, monkeypatch)
    results: List[ConversionResult] = []
    window.worker.succeeded.connect(lambda result: results.append(result))

    window.set_source_file(str(source))
    window.start_conversion()
    assert window.state is GuiState.CONVERTING
    assert _wait_until(lambda: window.state is not GuiState.CONVERTING)

    assert len(calls) == 1
    assert calls[0]["thread"] != _gui_thread_id()
    assert results and results[0].status is ConversionStatus.FAILED
    assert results[0].output_path is None
    assert window.state is GuiState.FAILED


def test_worker_level_failure_leaves_converting(
    window: "MainWindow", monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A raised service exception is transported as worker failure evidence."""
    source = _write_markdown(tmp_path / "notes.md")
    failures: List[tuple] = []
    window.worker.failed.connect(lambda failure: failures.append((failure, threading.get_ident())))

    def exploding(request: ConversionRequest) -> ConversionResult:
        raise RuntimeError("service exploded")

    monkeypatch.setattr(window.service, "convert", exploding)

    window.set_source_file(str(source))
    window.start_conversion()
    assert window.state is GuiState.CONVERTING
    assert _wait_until(lambda: window.state is not GuiState.CONVERTING)

    assert failures and failures[0][1] == _gui_thread_id()
    assert failures[0][0].error_type == "RuntimeError"
    assert window.state is GuiState.FAILED


# ============================================================
# Deterministic activation rules
# ============================================================


def test_second_activation_is_ignored_while_converting(
    window: "MainWindow", monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """WP §12: one Convert action cannot start two jobs."""
    source = _write_markdown(tmp_path / "notes.md")
    release = threading.Event()
    calls = _spy_on_service(window, monkeypatch, block=release)

    window.set_source_file(str(source))
    assert window.start_conversion() is GuiState.CONVERTING
    assert _wait_until(lambda: bool(calls))

    # A second activation while CONVERTING is refused (button is disabled too).
    assert window.start_conversion() is GuiState.CONVERTING
    assert window.convert_button.isEnabled() is False
    window.convert_button.click()
    assert len(calls) == 1

    release.set()
    assert _wait_until(lambda: window.state is not GuiState.CONVERTING)
    assert len(calls) == 1
    assert window.state is GuiState.SUCCESS


def test_start_conversion_requires_a_source(
    window: "MainWindow", monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without a source the action does nothing and starts no job."""
    calls = _spy_on_service(window, monkeypatch)

    assert window.state is GuiState.EMPTY
    assert window.start_conversion() is GuiState.EMPTY
    assert calls == []
    assert window.worker.is_running is False


def test_start_conversion_recovers_when_worker_refuses(
    window: "MainWindow", monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A refused worker job never leaves the GUI stuck in CONVERTING."""
    source = _write_markdown(tmp_path / "notes.md")
    calls = _spy_on_service(window, monkeypatch)
    monkeypatch.setattr(window.worker, "start", lambda job: False)

    window.set_source_file(str(source))

    assert window.start_conversion() is GuiState.READY
    assert calls == []
    assert window.state_model.source == str(source)
