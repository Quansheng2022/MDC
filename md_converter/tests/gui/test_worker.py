"""Focused verification for the GUI worker boundary (WP-P12-05-01 §10).

Covered: execution outside the GUI thread, success payload transport, failure
evidence transport, completion exactly once, thread exit and reference release,
deterministic second-start behavior, and the worker's own boundary rules
(no widgets, no Core/Markdown semantics).

The job callable is always a fake; real ``ConversionService`` execution belongs
to WP-P12-05-03.
"""

from __future__ import annotations

import ast
import os
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING, Callable, List, Set

import pytest

if TYPE_CHECKING:  # pragma: no cover - typing only
    from md_converter.gui.worker import GuiWorker

pytest.importorskip("PySide6", reason="PySide6 (GUI dev dependency) is not installed")

#: Qt needs a platform plugin even when a test only constructs widgets.  Set
#: here (not in a directory ``conftest.py``) because the test tree is not a
#: package and a second ``conftest`` would shadow ``md_converter/tests/conftest.py``.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from md_converter.gui.worker import GuiWorker, JobFailure  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[3]
GUI_DIR = PROJECT_ROOT / "md_converter" / "gui"
WORKER_PATH = GUI_DIR / "worker.py"


def _make_worker() -> "GuiWorker":
    """Return a fresh worker, ensuring a QApplication exists."""
    from md_converter.gui.app import create_application

    create_application([])
    return GuiWorker()


def _gui_thread_id() -> int:
    """Return the id of the calling (GUI) thread."""
    return threading.get_ident()


def _pump() -> None:
    """Deliver pending Qt events (queued cross-thread signals)."""
    from PySide6.QtWidgets import QApplication

    QApplication.processEvents()


def _wait_until(predicate: Callable[[], bool], timeout_ms: int = 5000) -> bool:
    """Process GUI events until ``predicate`` holds, or the timeout expires."""
    deadline = time.monotonic() + timeout_ms / 1000.0
    while time.monotonic() < deadline:
        _pump()
        if predicate():
            return True
        time.sleep(0.005)
    return predicate()


def _wait_idle(worker: "GuiWorker", timeout_ms: int = 5000) -> bool:
    """Wait until ``worker`` has finished and released its thread."""
    return _wait_until(lambda: not worker.is_running, timeout_ms)


@pytest.fixture
def worker() -> "GuiWorker":
    """Provide a fresh worker and guarantee it is idle again at teardown.

    Qt thread teardown (``QThread.finished`` -> ``deleteLater``) is delivered
    through the GUI event loop.  A test that returned while that was still
    pending would run pytest's capture teardown underneath a live Qt thread,
    which reproducibly crashed the process (native fail-fast).  Waiting for the
    boundary to go idle keeps the Qt object lifetime deterministic.
    """
    instance = _make_worker()
    yield instance
    assert _wait_idle(instance), "worker thread did not stop"
    _pump()


def _imported_modules(path: Path) -> Set[str]:
    """Return the module names imported by ``path``."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module:
                names.add(module)
            names.update(f"{module}.{alias.name}".lstrip(".") for alias in node.names)
    return names


def _code_string_constants(path: Path) -> List[str]:
    """Return string literals used in code, excluding docstrings."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings = {
        ast.get_docstring(node, clean=False)
        for node in ast.walk(tree)
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef))
    }
    docstrings.discard(None)
    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value not in docstrings
    ]


# ============================================================
# Execution boundary
# ============================================================


def test_job_executes_outside_the_gui_thread(worker: "GuiWorker") -> None:
    """WP §6: the job runs on a thread other than the GUI thread."""
    seen: List[int] = []

    assert worker.start(lambda: seen.append(threading.get_ident())) is True
    assert _wait_idle(worker)

    assert seen, "job did not run"
    assert seen[0] != _gui_thread_id()


def test_success_payload_is_delivered_on_the_gui_thread(worker: "GuiWorker") -> None:
    """WP §5: the success payload arrives on the GUI side, before completion."""
    deliveries: List[tuple] = []
    worker.succeeded.connect(
        lambda payload: deliveries.append(("payload", payload, threading.get_ident()))
    )
    worker.finished.connect(lambda: deliveries.append(("finished", None, threading.get_ident())))

    assert worker.start(lambda: "job-result") is True
    assert _wait_until(lambda: len(deliveries) >= 2 and not worker.is_running)

    assert deliveries[0] == ("payload", "job-result", _gui_thread_id())
    assert deliveries[1] == ("finished", None, _gui_thread_id())


def test_failure_evidence_is_delivered_on_the_gui_thread(worker: "GuiWorker") -> None:
    """WP §7: failures arrive as structured evidence on the GUI side."""
    failures: List[tuple] = []
    successes: List[object] = []
    worker.succeeded.connect(lambda payload: successes.append(payload))
    worker.failed.connect(lambda failure: failures.append((failure, threading.get_ident())))

    def failing_job() -> None:
        raise ValueError("job exploded")

    assert worker.start(failing_job) is True
    assert _wait_until(lambda: bool(failures) and not worker.is_running)

    failure, delivered_on = failures[0]
    assert isinstance(failure, JobFailure)
    assert failure.error_type == "ValueError"
    assert failure.message == "job exploded"
    assert "ValueError" in failure.traceback
    assert delivered_on == _gui_thread_id()
    assert successes == []


# ============================================================
# Lifecycle
# ============================================================


@pytest.mark.parametrize("failing", [False, True])
def test_completion_is_emitted_exactly_once(worker: "GuiWorker", failing: bool) -> None:
    """WP §8: exactly one outcome and one completion per job."""
    outcomes: List[str] = []
    completions: List[int] = []
    worker.succeeded.connect(lambda payload: outcomes.append("success"))
    worker.failed.connect(lambda failure: outcomes.append("failure"))
    worker.finished.connect(lambda: completions.append(1))

    def job() -> str:
        if failing:
            raise RuntimeError("boom")
        return "ok"

    assert worker.start(job) is True
    assert _wait_until(lambda: bool(completions) and not worker.is_running)

    assert completions == [1]
    assert outcomes == (["failure"] if failing else ["success"])

    _pump()
    _pump()
    assert completions == [1]


def test_thread_is_stopped_and_references_released(worker: "GuiWorker") -> None:
    """WP §8: the job thread exits and the worker releases its references."""
    release = threading.Event()

    assert worker.thread is None
    assert worker.start(lambda: release.wait(5)) is True
    assert worker.is_running is True
    assert worker.thread is not None
    assert worker.thread.isRunning() is True

    release.set()
    assert _wait_idle(worker)

    assert worker.thread is None
    assert worker.is_running is False


def test_second_start_is_rejected_while_running(worker: "GuiWorker") -> None:
    """WP §8: a second start is deterministic and does not overlap."""
    release = threading.Event()
    second_ran: List[int] = []

    assert worker.start(lambda: release.wait(5)) is True
    assert worker.start(lambda: second_ran.append(threading.get_ident())) is False

    release.set()
    assert _wait_idle(worker)
    assert second_ran == []


def test_worker_is_reusable_after_completion(worker: "GuiWorker") -> None:
    """WP §8: after completion the boundary can run another job safely."""
    results: List[int] = []
    worker.succeeded.connect(lambda payload: results.append(payload))

    for index in range(3):
        assert worker.start(lambda index=index: index * 2) is True
        assert _wait_idle(worker)

    assert results == [0, 2, 4]
    assert worker.thread is None


def test_repeated_jobs_release_every_thread(worker: "GuiWorker") -> None:
    """WP §8: repeated job cycles release each thread and its references.

    Regression guard for a native heap-corruption race in the cleanup path:
    the deferred thread deletion must be scheduled before the Python references
    are released, otherwise the wrapper release deletes a QThread that Qt is
    still finishing.
    """
    results: List[int] = []
    worker.succeeded.connect(lambda payload: results.append(payload))

    for index in range(25):
        assert worker.start(lambda index=index: index) is True
        assert _wait_idle(worker)
        assert worker.thread is None
        _pump()

    assert results == list(range(25))


def test_start_rejects_non_callable_job(worker: "GuiWorker") -> None:
    """A programming error fails loudly instead of starting an empty job."""
    with pytest.raises(TypeError, match="callable"):
        worker.start("not-a-callable")  # type: ignore[arg-type]


# ============================================================
# Worker boundary rules
# ============================================================


def test_worker_imports_qtcore_only() -> None:
    """WP §5: the worker never touches widgets or other Qt modules."""
    imported = _imported_modules(WORKER_PATH)

    assert not [
        name for name in imported if name.startswith(("PySide6.QtWidgets", "PySide6.QtGui"))
    ]
    assert [name for name in imported if name.startswith("PySide6.QtCore")]


def test_worker_has_no_core_or_application_dependency() -> None:
    """WP §5/§11: no Core, application-service or conversion imports."""
    imported = _imported_modules(WORKER_PATH)
    forbidden = (
        "md_converter.application",
        "md_converter.compiler",
        "md_converter.parser",
        "md_converter.pipeline",
        "md_converter.renderer",
        "md_converter.services",
    )

    assert not [name for name in imported if name.startswith(forbidden)]


def test_worker_code_has_no_markdown_or_conversion_terms() -> None:
    """WP §5: the worker carries no Markdown/Core semantics."""
    strings = _code_string_constants(WORKER_PATH)
    for token in ("markdown", "frontmatter", "docx"):
        assert not [text for text in strings if token in text.lower()], token

    tree = ast.parse(WORKER_PATH.read_text(encoding="utf-8"))
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    names |= {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    assert not names & {"CompilerContext", "ConversionService", "sanitize_output_title"}
