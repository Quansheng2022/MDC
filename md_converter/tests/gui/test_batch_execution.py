"""Focused verification for serial batch execution (SBC-04/05/06).

Every test drives the *real* execution path - GUI -> ``GuiWorker`` ->
``ConversionService.convert`` -> Canonical Core -> one document per source -
and asserts the accepted invariants of the product specification:

* the batch is serial (maximum one conversion running at any moment);
* the order is the list order;
* an ordinary failure or a warning never stops the remaining files;
* one document is produced per successful source;
* the progress line, the per-file status, the derived summary and the batch
  report match the recorded results;
* the worker lifecycle, the close policy and the single-file surface are
  unchanged.
"""

from __future__ import annotations

import os
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Dict, List, Optional

import pytest

from md_converter.application.conversion_request import ConversionRequest
from md_converter.application.conversion_result import ConversionResult, ConversionStatus

if TYPE_CHECKING:  # pragma: no cover - typing only
    from md_converter.gui.main_window import MainWindow

pytest.importorskip("PySide6", reason="PySide6 (GUI dev dependency) is not installed")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from md_converter.gui.batch import BatchItemStatus  # noqa: E402 - the Qt guard must run first
from md_converter.gui.state import GuiState  # noqa: E402 - the Qt guard must run first

SUCCESS_BODY = "# Notes\n\nBody text.\n"
WARNING_BODY = "#\n\nSome body text.\n"
FAILURE_BODY = ""


def _pump() -> None:
    """Deliver pending Qt events (queued cross-thread signals)."""
    from PySide6.QtWidgets import QApplication

    QApplication.processEvents()


def _wait_until(predicate: Callable[[], bool], timeout_ms: int = 30000) -> bool:
    """Process GUI events until ``predicate`` holds, or the timeout expires."""
    deadline = time.monotonic() + timeout_ms / 1000.0
    while time.monotonic() < deadline:
        _pump()
        if predicate():
            return True
        time.sleep(0.005)
    return predicate()


def _write_markdown(path: Path, body: str = SUCCESS_BODY) -> Path:
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
    block_after: Optional[int] = None,
) -> Dict[str, object]:
    """Record real service calls, concurrency and the order they started in.

    Args:
        window: Window whose service is observed.
        monkeypatch: Pytest monkeypatch fixture.
        block_after: Optional call number that blocks until ``release`` is set.

    Returns:
        Dict[str, object]: ``calls`` (source names in start order), ``threads``
        (thread ids), ``concurrency`` (peak simultaneous calls) and ``release``
        (the event the blocked call waits on).
    """
    original = window.service.convert
    state: Dict[str, object] = {
        "calls": [],
        "threads": [],
        "active": 0,
        "concurrency": 0,
        "release": threading.Event(),
    }

    def recording(request: ConversionRequest) -> ConversionResult:
        state["calls"].append(Path(str(request.source_path)).name)
        state["threads"].append(threading.get_ident())
        state["active"] = int(state["active"]) + 1
        state["concurrency"] = max(int(state["concurrency"]), int(state["active"]))
        try:
            if block_after is not None and len(state["calls"]) == block_after:
                state["release"].wait(30)
            return original(request)
        finally:
            state["active"] = int(state["active"]) - 1

    monkeypatch.setattr(window.service, "convert", recording)
    return state


def _prepare_batch(
    window: "MainWindow", tmp_path: Path, names: List[str], bodies: Optional[Dict[str, str]] = None
) -> List[Path]:
    """Select ``names`` as a batch and choose an explicit output folder."""
    bodies = bodies or {}
    sources = [_write_markdown(tmp_path / name, bodies.get(name, SUCCESS_BODY)) for name in names]
    output_dir = tmp_path / "out"
    output_dir.mkdir(exist_ok=True)
    window.set_output_directory(output_dir)
    window.set_source_file(str(sources[0]))
    if len(sources) > 1:
        window.add_source_files([str(source) for source in sources[1:]])
    return sources


def _run_batch(window: "MainWindow") -> None:
    """Start the batch and wait until the run and the worker are finished."""
    assert window.start_conversion() is GuiState.CONVERTING
    assert _wait_until(
        lambda: not window.worker.is_running and window.state is not GuiState.CONVERTING
    )


def _assert_clean_boundary(window: "MainWindow") -> None:
    """Assert no worker or thread reference is left behind."""
    assert window.worker.is_running is False
    assert window.worker.thread is None
    assert window.is_conversion_active is False


# ============================================================
# Serial execution
# ============================================================


def test_three_file_batch_produces_one_document_per_source(
    window: "MainWindow", monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """§11/§17: three sources convert serially into three separate documents."""
    sources = _prepare_batch(window, tmp_path, ["a.md", "b.md", "c.md"])
    state = _spy_on_service(window, monkeypatch)

    _run_batch(window)

    assert state["calls"] == ["a.md", "b.md", "c.md"]
    assert state["concurrency"] == 1
    for thread_id in state["threads"]:
        assert thread_id != threading.get_ident()

    run = window.batch_run
    assert run is not None
    assert run.is_complete is True
    assert (run.succeeded, run.warnings, run.failed) == (3, 0, 0)

    outputs = [item.output_path for item in run.items]
    assert all(output is not None for output in outputs)
    assert len(set(outputs)) == 3
    for index, source in enumerate(sources):
        output = outputs[index]
        assert output is not None
        assert output.exists()
        assert output.parent == tmp_path / "out"
        assert output.name.startswith(source.stem)
    assert window.state is GuiState.READY
    _assert_clean_boundary(window)


def test_at_most_one_conversion_is_active(
    window: "MainWindow", monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """§11: the peak number of simultaneous conversions is exactly one."""
    _prepare_batch(window, tmp_path, ["a.md", "b.md", "c.md", "d.md"])
    state = _spy_on_service(window, monkeypatch)

    _run_batch(window)

    assert state["concurrency"] == 1
    assert len(state["calls"]) == 4


def test_order_follows_the_list(
    window: "MainWindow", monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """§10: the list order is the execution order, including after a removal."""
    sources = _prepare_batch(window, tmp_path, ["a.md", "b.md", "c.md"])
    window.batch_list.item(1).setSelected(True)
    window.remove_selected_sources()
    state = _spy_on_service(window, monkeypatch)

    _run_batch(window)

    assert state["calls"] == ["a.md", "c.md"]
    assert sources[1] not in window.batch_run.sources if window.batch_run else True


def test_progress_line_reports_position_and_current_file(
    window: "MainWindow", monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """§8.3: the running batch shows "Converting 2 of 3" and the file name."""
    _prepare_batch(window, tmp_path, ["a.md", "b.md", "c.md"])
    state = _spy_on_service(window, monkeypatch, block_after=2)

    assert window.start_conversion() is GuiState.CONVERTING
    assert _wait_until(lambda: "Converting 1 of 3" in window.status_label.text())
    assert "a.md" in window.status_label.text()

    assert _wait_until(lambda: len(state["calls"]) == 2)
    assert _wait_until(lambda: "Converting 2 of 3" in window.status_label.text())
    assert "b.md" in window.status_label.text()

    state["release"].set()
    _run_batch_completion(window)
    assert window.state is GuiState.READY


def _run_batch_completion(window: "MainWindow") -> None:
    """Wait for the running batch to finish."""
    assert _wait_until(
        lambda: not window.worker.is_running and window.state is not GuiState.CONVERTING
    )


def test_per_file_status_is_shown_in_the_list(
    window: "MainWindow", monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """§8.3/§31: every row carries a marker *and* a status word."""
    _prepare_batch(
        window, tmp_path, ["a.md", "b.md", "c.md"], {"b.md": FAILURE_BODY, "c.md": WARNING_BODY}
    )
    _spy_on_service(window, monkeypatch)

    _run_batch(window)

    rows = [window.batch_list.item(index).text() for index in range(window.batch_list.count())]
    assert rows[0].endswith("succeeded")
    assert rows[1].endswith("failed")
    assert rows[2].endswith("warning")
    assert all(row.strip() for row in rows)


# ============================================================
# Failure and warning continuation
# ============================================================


def test_failure_in_the_middle_continues_and_is_summarised(
    window: "MainWindow", monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """§15: a failed file is recorded, the rest continues, one document each."""
    _prepare_batch(window, tmp_path, ["a.md", "b.md", "c.md"], {"b.md": FAILURE_BODY})
    state = _spy_on_service(window, monkeypatch)

    _run_batch(window)

    assert state["calls"] == ["a.md", "b.md", "c.md"]
    run = window.batch_run
    assert run is not None
    assert (run.succeeded, run.warnings, run.failed) == (2, 0, 1)
    assert run.items[1].status is BatchItemStatus.FAILED
    assert run.items[1].output_path is None
    assert run.items[0].output_path is not None
    assert run.items[2].output_path is not None
    assert window.state is GuiState.READY
    assert "2 succeeded" in window.batch_summary_label.text()
    assert "1 failed" in window.batch_summary_label.text()
    _assert_clean_boundary(window)


def test_warning_continuation(
    window: "MainWindow", monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """§16: warnings never stop the batch and stay successful outcomes."""
    _prepare_batch(window, tmp_path, ["a.md", "b.md"], {"b.md": WARNING_BODY})
    _spy_on_service(window, monkeypatch)

    _run_batch(window)

    run = window.batch_run
    assert run is not None
    assert (run.succeeded, run.warnings, run.failed) == (1, 1, 0)
    assert run.items[1].status is BatchItemStatus.SUCCESS_WITH_WARNING
    assert run.items[1].output_path is not None
    assert window.state is GuiState.READY


def test_worker_level_failure_continues_the_batch(
    window: "MainWindow", monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """§15: an item-level infrastructure failure is still one recorded item."""
    _prepare_batch(window, tmp_path, ["a.md", "b.md", "c.md"])
    original = window.service.convert

    def exploding(request: ConversionRequest) -> ConversionResult:
        if Path(str(request.source_path)).name == "b.md":
            raise RuntimeError("service exploded")
        return original(request)

    monkeypatch.setattr(window.service, "convert", exploding)

    _run_batch(window)

    run = window.batch_run
    assert run is not None
    assert (run.succeeded, run.failed) == (2, 1)
    assert run.items[1].status is BatchItemStatus.INFRASTRUCTURE_FAILURE
    assert run.items[1].output_path is None
    assert run.items[2].output_path is not None
    assert window.state is GuiState.READY
    _assert_clean_boundary(window)


def test_batch_report_lists_every_source(
    window: "MainWindow", monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """§22: the batch report aggregates the retained per-file evidence."""
    _prepare_batch(
        window, tmp_path, ["a.md", "b.md", "c.md"], {"b.md": FAILURE_BODY, "c.md": WARNING_BODY}
    )
    _spy_on_service(window, monkeypatch)
    _run_batch(window)

    run = window.batch_run
    assert run is not None
    report = run.report_text()
    for name in ("a.md", "b.md", "c.md"):
        assert name in report
    assert "1 succeeded" in report
    assert "1 warning" in report
    assert "1 failed" in report
    assert "Output file:" in report


def test_batch_report_action_opens_the_report_surface(
    window: "MainWindow", monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """§23: the completion surface offers View Batch Report, not Open Document."""
    import importlib

    module = importlib.import_module("md_converter.gui.main_window")
    shown: List[object] = []
    monkeypatch.setattr(module, "show_batch_report", lambda parent, run: shown.append(run))

    _prepare_batch(window, tmp_path, ["a.md", "b.md"])
    _spy_on_service(window, monkeypatch)
    _run_batch(window)

    window.show()
    _pump()
    assert window.batch_summary_area.isVisible() is True
    assert window.view_batch_report_button.isVisible() is True
    assert window.show_batch_report() is True
    assert shown == [window.batch_run]


def test_open_output_folder_uses_the_retained_documents(
    window: "MainWindow", monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """§24: the batch folder action uses the retained produced documents."""
    import importlib

    module = importlib.import_module("md_converter.gui.main_window")
    opened: List[Path] = []
    monkeypatch.setattr(module, "open_directory", lambda path: opened.append(Path(path)) or True)

    _prepare_batch(window, tmp_path, ["a.md", "b.md"])
    _spy_on_service(window, monkeypatch)
    _run_batch(window)

    assert window.open_batch_folder_button.isEnabled() is True
    assert window.open_batch_output_folder() is True
    assert opened == [tmp_path / "out"]


def test_open_output_folder_is_unavailable_without_a_document(
    window: "MainWindow", monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A batch that produced nothing never offers a folder action."""
    _prepare_batch(window, tmp_path, ["a.md", "b.md"], {"a.md": FAILURE_BODY, "b.md": FAILURE_BODY})
    _spy_on_service(window, monkeypatch)
    _run_batch(window)

    window.show()
    _pump()
    assert window.batch_summary_area.isVisible() is True
    assert window.open_batch_folder_button.isEnabled() is False
    assert window.open_batch_output_folder() is False


# ============================================================
# Lifecycle
# ============================================================


def test_single_file_selection_keeps_the_single_file_surface(
    window: "MainWindow", monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """§33/§34: one file still behaves exactly like the accepted workflow."""
    _prepare_batch(window, tmp_path, ["only.md"])
    state = _spy_on_service(window, monkeypatch)

    _run_batch(window)

    assert state["calls"] == ["only.md"]
    assert window.state is GuiState.SUCCESS
    assert window.latest_result is not None
    assert window.latest_result.status is ConversionStatus.SUCCESS
    assert window.batch_summary_area.isVisible() is False
    assert window.presentation is not None
    assert window.presentation.is_success is True
    _assert_clean_boundary(window)


def test_convert_is_disabled_while_the_batch_runs(
    window: "MainWindow", monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """§20: a second batch cannot start while one is running."""
    _prepare_batch(window, tmp_path, ["a.md", "b.md"])
    state = _spy_on_service(window, monkeypatch, block_after=1)

    assert window.start_conversion() is GuiState.CONVERTING
    assert _wait_until(lambda: len(state["calls"]) == 1)
    assert window.convert_button.isEnabled() is False
    assert window.start_conversion() is GuiState.CONVERTING
    assert window.select_file_button.isEnabled() is False
    assert window.change_output_button.isEnabled() is False

    state["release"].set()
    _run_batch_completion(window)
    assert len(state["calls"]) == 2


def test_close_is_blocked_during_a_batch_and_allowed_after(
    window: "MainWindow", monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """§20: the frozen close policy covers the whole batch."""
    _prepare_batch(window, tmp_path, ["a.md", "b.md"])
    state = _spy_on_service(window, monkeypatch, block_after=1)
    window.show()

    assert window.start_conversion() is GuiState.CONVERTING
    assert _wait_until(lambda: len(state["calls"]) == 1)
    assert window.is_conversion_active is True
    window.close()
    _pump()
    assert window.isVisible() is True

    state["release"].set()
    _run_batch_completion(window)
    assert window.is_conversion_active is False
    window.close()
    _pump()
    assert window.isVisible() is False


def test_a_second_batch_can_start_after_completion(
    window: "MainWindow", monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """§20: controls are restored and the next batch can start."""
    _prepare_batch(window, tmp_path, ["a.md", "b.md"])
    state = _spy_on_service(window, monkeypatch)

    _run_batch(window)
    assert window.state is GuiState.READY
    assert window.convert_button.isEnabled() is True

    _run_batch(window)
    assert state["calls"] == ["a.md", "b.md", "a.md", "b.md"]
    assert state["concurrency"] == 1
    _assert_clean_boundary(window)


def test_batch_leaves_no_worker_or_thread_reference(
    window: "MainWindow", monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """§20: repeated batches release every worker and thread."""
    _prepare_batch(window, tmp_path, ["a.md", "b.md"])
    _spy_on_service(window, monkeypatch)

    for _ in range(3):
        _run_batch(window)
        _assert_clean_boundary(window)

    run = window.batch_run
    assert run is not None
    assert run.is_complete is True


def test_new_selection_clears_the_previous_batch_summary(
    window: "MainWindow", monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A new workflow replaces the previous batch presentation."""
    _prepare_batch(window, tmp_path, ["a.md", "b.md"])
    _spy_on_service(window, monkeypatch)
    _run_batch(window)
    window.show()
    _pump()
    assert window.batch_summary_area.isVisible() is True

    window.set_source_file(str(_write_markdown(tmp_path / "fresh.md")))

    assert window.batch_run is None
    assert window.batch_summary_area.isVisible() is False
    assert window.status_label.text() == "Ready to convert."
