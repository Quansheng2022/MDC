"""Background job boundary for the MD_Converter GUI (WP-P12-05-01).

Runs exactly one callable outside the Qt GUI main thread and delivers the
outcome back on the GUI thread:

    MainWindow
        v
    GuiWorker (this module)
        v
    application callable  (a fake/mock callable in this WP)

Boundary rules (WP-P12-05-01 §5/§7/§9):

* the worker knows nothing about Markdown, parser, renderer, QA, frontmatter or
  DOCX naming - it only runs an opaque callable;
* it imports ``QtCore`` only and never touches widgets;
* failures are transported as structured evidence; no error UX is built here;
* real ``ConversionService`` execution is deferred to WP-P12-05-03.

Threading model: one dedicated ``QThread`` per job with a private runner
QObject moved onto it (the standard Qt worker-object pattern).  No pool, queue,
retry or cancellation machinery.
"""

from __future__ import annotations

import traceback as traceback_module
from dataclasses import dataclass
from typing import Any, Callable, Optional

from PySide6.QtCore import QObject, QThread, Signal, Slot

__all__ = ["GuiWorker", "JobFailure"]


@dataclass(frozen=True)
class JobFailure:
    """Structured failure evidence from a background job (WP-P12-05-01 §7).

    Attributes:
        error_type: Exception class name.
        message: Exception message.
        traceback: Formatted traceback text, kept as technical evidence.
    """

    error_type: str
    message: str
    traceback: str

    @classmethod
    def from_exception(cls, exc: BaseException) -> "JobFailure":
        """Build failure evidence from ``exc``.

        Args:
            exc: Exception raised by the job.

        Returns:
            JobFailure: Structured evidence describing the failure.
        """
        formatted = "".join(traceback_module.format_exception(type(exc), exc, exc.__traceback__))
        return cls(
            error_type=type(exc).__name__,
            message=str(exc),
            traceback=formatted.rstrip(),
        )


class _JobRunner(QObject):
    """Private runner that executes one job inside the worker thread."""

    succeeded = Signal(object)
    failed = Signal(object)
    finished = Signal()

    def __init__(self, job: Callable[[], Any]) -> None:
        super().__init__()
        self._job = job

    @Slot()
    def run(self) -> None:
        """Execute the job, report exactly one outcome, then completion.

        Application exceptions become failure evidence.  ``finished`` is
        emitted from a ``finally`` block, so the GUI cannot be left waiting even
        if an exception escapes the outcome handling.
        """
        try:
            result = self._job()
        except Exception as exc:
            # Failure evidence is the payload; the GUI decides presentation.
            self.failed.emit(JobFailure.from_exception(exc))
        else:
            self.succeeded.emit(result)
        finally:
            self.finished.emit()


class GuiWorker(QObject):
    """Run one callable outside the GUI thread and report its outcome.

    Signals:
        succeeded: Emitted with the job's return value, on the GUI thread.
        failed: Emitted with :class:`JobFailure` evidence, on the GUI thread.
        finished: Emitted exactly once per started job, on the GUI thread,
            after ``succeeded`` or ``failed``.

    One job runs at a time.  ``is_running`` stays ``True`` until the job's
    thread has exited and the internal references are released, so a second
    start cannot overlap with cleanup (WP-P12-05-01 §8).
    """

    succeeded = Signal(object)
    failed = Signal(object)
    finished = Signal()

    def __init__(self, parent: Optional[QObject] = None) -> None:
        """Create an idle worker.

        Args:
            parent: Optional Qt parent object (GUI thread affinity).
        """
        super().__init__(parent)
        self._thread: Optional[QThread] = None
        self._runner: Optional[_JobRunner] = None
        self._running = False

    @property
    def is_running(self) -> bool:
        """Whether a job is executing or its thread is still cleaning up."""
        return self._running

    @property
    def thread(self) -> Optional[QThread]:
        """Return the job thread, or ``None`` once it has exited."""
        return self._thread

    def start(self, job: Callable[[], Any]) -> bool:
        """Start ``job`` on a dedicated thread.

        Args:
            job: Zero-argument callable executed outside the GUI thread.  Wrap
                arguments at the call site (for example with ``functools.partial``).

        Returns:
            bool: ``True`` when the job started; ``False`` when a previous job
            is still running or cleaning up.

        Raises:
            TypeError: ``job`` is not callable (call-site programming error).
        """
        if not callable(job):
            raise TypeError("job must be callable")
        if self._running:
            return False

        thread = QThread()
        runner = _JobRunner(job)
        runner.moveToThread(thread)

        thread.started.connect(runner.run)
        # Outcome and completion are re-emitted on the GUI thread (queued
        # connections, because this worker lives in the GUI thread).
        runner.succeeded.connect(self.succeeded)
        runner.failed.connect(self.failed)
        runner.finished.connect(self.finished)

        # Graceful shutdown: no terminate(); the thread's event loop is asked to
        # quit once the job reported its completion.
        runner.finished.connect(thread.quit)
        # Qt must own both deletions *before* the Python references are released
        # below: releasing a wrapper whose C++ object still exists deletes the
        # object immediately and can race the pending deferred delete (observed
        # as a native heap-corruption crash inside the cleanup slot).
        thread.finished.connect(runner.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._on_thread_finished)

        self._thread = thread
        self._runner = runner
        self._running = True
        thread.start()
        return True

    @Slot()
    def _on_thread_finished(self) -> None:
        """Release job references after the thread has exited."""
        self._thread = None
        self._runner = None
        self._running = False
