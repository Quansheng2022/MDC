"""Focused verification for the GUI conversion lifecycle (WP-P12-05-05 §7).

Covers the single-job invariant, source/output immutability while CONVERTING,
worker cleanup for every outcome, sequential reuse, the close policy, and a
bounded repeat run that would expose intermittent Qt teardown defects.

Every test waits for the worker boundary to go idle (thread exited, references
released), not merely for result delivery, so pytest teardown never starts while
Qt thread cleanup is pending.
"""

from __future__ import annotations

import os
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING, Callable, List, Optional, Tuple

import pytest

from md_converter.application.conversion_result import ConversionResult

if TYPE_CHECKING:  # pragma: no cover - typing only
    from md_converter.gui.main_window import MainWindow

pytest.importorskip("PySide6", reason="PySide6 (GUI dev dependency) is not installed")

#: Qt needs a platform plugin even when a test only constructs widgets.  Set
#: here (not in a directory ``conftest.py``) because the test tree is not a
#: package and a second ``conftest`` would shadow ``md_converter/tests/conftest.py``.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from md_converter.gui.state import GuiState  # noqa: E402 - the Qt guard must run first

PROJECT_ROOT = Path(__file__).resolve().parents[3]


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


def _spy_on_service(
    window: "MainWindow",
    monkeypatch: pytest.MonkeyPatch,
    block: Optional[threading.Event] = None,
) -> List[dict]:
    """Record real ``service.convert`` calls (thread id and request)."""
    calls: List[dict] = []
    original = window.service.convert

    def recording(request) -> ConversionResult:
        calls.append({"thread": threading.get_ident(), "request": request})
        if block is not None:
            block.wait(15)
        return original(request)

    monkeypatch.setattr(window.service, "convert", recording)
    return calls


def _run_conversion(window: "MainWindow", source: Path) -> None:
    """Run one real conversion and wait for completion and full cleanup."""
    assert window.set_source_file(str(source)) is GuiState.READY
    window.start_conversion()
    assert _wait_until(
        lambda: window.state is not GuiState.CONVERTING and not window.worker.is_running
    )


def _start_blocked_conversion(
    window: "MainWindow",
    source: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Tuple[threading.Event, List[dict]]:
    """Start a conversion that blocks inside the service until released."""
    release = threading.Event()
    calls = _spy_on_service(window, monkeypatch, block=release)
    window.set_source_file(str(source))
    assert window.start_conversion() is GuiState.CONVERTING
    assert _wait_until(lambda: bool(calls))
    return release, calls


def _drop(zone, paths) -> bool:
    """Send a real Qt drop event carrying ``paths``; return the accept result."""
    from PySide6.QtCore import QMimeData, QPointF, Qt, QUrl
    from PySide6.QtGui import QDropEvent

    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(path)) for path in paths])
    event = QDropEvent(
        QPointF(10.0, 10.0),
        Qt.DropAction.CopyAction,
        mime,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    zone.dropEvent(event)
    return bool(event.isAccepted())


def _assert_clean(window: "MainWindow") -> None:
    """Assert the worker boundary is idle with no references left."""
    assert window.worker.is_running is False
    assert window.worker.thread is None
    assert window.is_conversion_active is False


# ============================================================
# Single-job invariant
# ============================================================


def test_duplicate_convert_starts_exactly_one_job(
    window: "MainWindow", monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """WP §3: a second activation creates no job, thread or service call."""
    source = _write_markdown(tmp_path / "notes.md")
    starts: List[int] = []
    original_start = window.worker.start

    def counting_start(job) -> bool:
        starts.append(1)
        return original_start(job)

    monkeypatch.setattr(window.worker, "start", counting_start)
    release, calls = _start_blocked_conversion(window, source, monkeypatch)
    active_thread = window.worker.thread

    # Second activation via the button is disabled, and the programmatic action
    # is refused before the worker is asked again.
    assert window.convert_button.isEnabled() is False
    window.convert_button.click()
    assert window.start_conversion() is GuiState.CONVERTING

    assert len(starts) == 1
    assert len(calls) == 1
    assert window.worker.thread is active_thread

    release.set()
    assert _wait_until(lambda: window.state is GuiState.SUCCESS)
    assert _wait_until(lambda: not window.worker.is_running)
    assert len(calls) == 1
    _assert_clean(window)


def test_source_cannot_change_while_converting(
    window: "MainWindow", monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """WP §3: picker and forced source changes cannot replace the source."""
    source = _write_markdown(tmp_path / "notes.md")
    other = _write_markdown(tmp_path / "other.md")
    release, _ = _start_blocked_conversion(window, source, monkeypatch)

    assert window.select_file_button.isEnabled() is False
    assert window.set_source_file(str(other)) is GuiState.CONVERTING
    assert window.set_source("forced.md") is GuiState.CONVERTING
    assert window.state_model.source == str(source)
    assert window.source_label.text() == "notes.md"

    release.set()
    assert _wait_until(lambda: not window.worker.is_running)
    assert window.state_model.source == str(source)
    _assert_clean(window)


def test_drag_drop_cannot_change_source_while_converting(
    window: "MainWindow", monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """WP §3: a drop during CONVERTING is rejected by the same state rules."""
    source = _write_markdown(tmp_path / "notes.md")
    other = _write_markdown(tmp_path / "other.md")
    release, _ = _start_blocked_conversion(window, source, monkeypatch)

    assert window.drop_zone.acceptDrops() is False
    assert _drop(window.drop_zone, [other]) is False
    assert window.state_model.source == str(source)

    release.set()
    assert _wait_until(lambda: not window.worker.is_running)
    assert window.state_model.source == str(source)
    _assert_clean(window)


def test_output_cannot_change_while_converting(
    window: "MainWindow", monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """WP §3: Change Output is disabled and the active request stays stable."""
    source = _write_markdown(tmp_path / "notes.md")
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_dir.mkdir()
    second_dir.mkdir()

    window.set_output_directory(first_dir)
    release, calls = _start_blocked_conversion(window, source, monkeypatch)

    assert window.change_output_button.isEnabled() is False
    assert window.set_output_directory(second_dir) == first_dir
    assert window.output_directory == first_dir
    assert calls[0]["request"].config_overrides == {"output_dir": str(first_dir)}

    release.set()
    assert _wait_until(lambda: window.state is GuiState.SUCCESS)
    assert _wait_until(lambda: not window.worker.is_running)
    assert window.output_directory == first_dir
    assert window.latest_result is not None
    assert window.latest_result.output_path is not None
    assert window.latest_result.output_path.parent == first_dir
    _assert_clean(window)


# ============================================================
# Worker cleanup for every outcome
# ============================================================


@pytest.mark.parametrize(
    ("label", "body", "expected"),
    [
        ("success", "# Notes\n\nBody text.\n", GuiState.SUCCESS),
        ("warning", "#\n\nSome body text.\n", GuiState.SUCCESS_WITH_WARNING),
        ("failed", "", GuiState.FAILED),
    ],
)
def test_result_outcome_cleans_up(
    window: "MainWindow", tmp_path: Path, label: str, body: str, expected: GuiState
) -> None:
    """WP §3/§7: every result outcome leaves a clean, idle worker boundary."""
    source = _write_markdown(tmp_path / f"{label}.md", body=body)
    completions: List[int] = []
    window.worker.finished.connect(lambda: completions.append(1))

    _run_conversion(window, source)

    assert window.state is expected
    assert completions == [1]
    _pump()
    assert completions == [1]
    _assert_clean(window)


def test_job_failure_cleans_up(
    window: "MainWindow", monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """WP §3/§7: worker infrastructure failure also cleans up completely."""
    source = _write_markdown(tmp_path / "notes.md")

    def exploding(request):
        raise RuntimeError("service exploded")

    monkeypatch.setattr(window.service, "convert", exploding)

    _run_conversion(window, source)

    assert window.state is GuiState.FAILED
    assert window.latest_job_failure is not None
    assert window.latest_result is None
    _assert_clean(window)


def test_sequential_conversions_reuse_the_window(
    window: "MainWindow", monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """WP §3/§7: a second conversion runs after the first cleaned up."""
    calls = _spy_on_service(window, monkeypatch)
    first = _write_markdown(tmp_path / "first.md")
    second = _write_markdown(tmp_path / "second.md")

    _run_conversion(window, first)
    assert window.state is GuiState.SUCCESS
    _assert_clean(window)

    _run_conversion(window, second)
    assert window.state is GuiState.SUCCESS
    _assert_clean(window)
    assert len(calls) == 2


def test_bounded_repeat_cycles_leave_no_worker(
    window: "MainWindow", monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Bounded repeat run: repeated lifecycles never leave a worker behind."""
    calls = _spy_on_service(window, monkeypatch)

    for index in range(3):
        source = _write_markdown(tmp_path / f"doc{index}.md")
        _run_conversion(window, source)
        assert window.state is GuiState.SUCCESS
        _assert_clean(window)

    assert len(calls) == 3


# ============================================================
# Close policy
# ============================================================


def test_close_is_rejected_during_conversion_then_allowed(
    window: "MainWindow", monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """WP §4: the window refuses to close while a conversion is active."""
    source = _write_markdown(tmp_path / "notes.md")
    release, _ = _start_blocked_conversion(window, source, monkeypatch)
    window.show()

    assert window.is_conversion_active is True
    window.close()
    _pump()
    assert window.isVisible() is True

    release.set()
    assert _wait_until(lambda: window.state is GuiState.SUCCESS)
    assert _wait_until(lambda: not window.worker.is_running)
    assert window.is_conversion_active is False

    window.close()
    _pump()
    assert window.isVisible() is False


def test_close_succeeds_without_active_conversion(window: "MainWindow") -> None:
    """WP §4: without an active conversion the close policy is transparent."""
    window.show()
    assert window.is_conversion_active is False

    window.close()
    _pump()

    assert window.isVisible() is False
