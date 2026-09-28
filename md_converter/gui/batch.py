"""Qt-free serial batch selection and orchestration for the MD_Converter GUI.

Serial Batch Conversion turns the single-file workflow into a multi-file one
without introducing a second conversion path (see
``Doc/V2/Product/Serial_Batch_Conversion_Product_Specification.md`` §11/§13):

    MainWindow
        v
    BatchSelection / BatchRun  (this module - ordering, status, summary)
        v
    the existing single-file worker/service execution
        v
    ConversionService -> Canonical Core -> one document per source

Three responsibilities live here, and nothing else:

* :class:`BatchSelection` - the ordered, duplicate-free list of selected
  Markdown sources (the execution order is the list order);
* :class:`BatchItem` / :class:`BatchRun` - the serial job sequence, per-item
  terminal status and the derived batch summary;
* the batch report text, aggregated from retained per-item evidence.

Deliberate limits:

* the module imports no GUI framework and no compiler stage, so the
  orchestration can be unit-tested without a display server;
* it never parses Markdown, renders a document, interprets quality-gate
  diagnostics or decides output naming - every job is executed by the accepted
  single-file authority, and ``ConversionResult.output_path`` stays the only
  path authority;
* per-item outcomes are derived from
  :mod:`md_converter.gui.presentation_model` (``present_result`` /
  ``present_job_failure``), so no second outcome taxonomy and no second
  wording authority is created here;
* no concurrency: exactly one item may be ``CONVERTING`` at a time, the next
  source is only handed out after the current item reached a terminal status,
  and :class:`BatchRun` fails loudly when that invariant is violated.

Failure policy (product specification §15/§16):

* ``SUCCESS``, ``SUCCESS_WITH_WARNING``, ``FAILED`` and an item-level
  infrastructure failure are all recorded and the batch continues with the
  next source;
* only a batch-level infrastructure problem - represented by
  :meth:`BatchRun.abort` - stops the remaining sources, and the remaining
  items are reported as "not processed".
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple, Union

from ..application.conversion_result import ConversionResult
from .presentation_model import (
    FailureEvidence,
    Presentation,
    PresentationOutcome,
    present_job_failure,
    present_result,
)

__all__ = [
    "BATCH_COMPLETE_HEADLINE",
    "BATCH_STOPPED_HEADLINE",
    "COUNTS_SEPARATOR",
    "MARKER_BY_STATUS",
    "STATE_WORD_BY_STATUS",
    "TERMINAL_STATUS_VALUES",
    "BatchAddResult",
    "BatchItem",
    "BatchItemStatus",
    "BatchRun",
    "BatchRunError",
    "BatchSelection",
    "SourceValidator",
    "source_identity",
]

#: Separator used between the per-outcome counts in summary lines.
COUNTS_SEPARATOR = " \u00b7 "

#: Headline shown when every selected source was processed.
BATCH_COMPLETE_HEADLINE = "Batch complete"

#: Headline shown when a batch-level infrastructure problem stopped the queue.
BATCH_STOPPED_HEADLINE = "Batch stopped"


class BatchItemStatus(str, Enum):
    """Terminal/transient status of one source inside a batch.

    ``PENDING`` and ``CONVERTING`` are batch-workflow states; the four terminal
    members mirror :class:`~md_converter.gui.presentation_model.PresentationOutcome`
    one-to-one (the values are identical), so the per-item outcome wording and
    severity stay owned by the presentation model.
    """

    PENDING = "PENDING"
    CONVERTING = "CONVERTING"
    SUCCESS = "SUCCESS"
    SUCCESS_WITH_WARNING = "SUCCESS_WITH_WARNING"
    FAILED = "FAILED"
    INFRASTRUCTURE_FAILURE = "INFRASTRUCTURE_FAILURE"

    def __str__(self) -> str:
        """Return the stable status value (independent of Python version)."""
        return self.value

    @property
    def is_terminal(self) -> bool:
        """Whether the item can no longer change."""
        return self.value in TERMINAL_STATUS_VALUES

    @property
    def produced_output(self) -> bool:
        """Whether the item produced a document.

        A warning is still a produced document (product specification §16);
        failures and item-level infrastructure failures are not.
        """
        return self in (BatchItemStatus.SUCCESS, BatchItemStatus.SUCCESS_WITH_WARNING)

    @property
    def counts_as_failed(self) -> bool:
        """Whether the item contributes to the batch "failed" count."""
        return self in (BatchItemStatus.FAILED, BatchItemStatus.INFRASTRUCTURE_FAILURE)


#: Per-item status marker.  The marker is always accompanied by the status
#: word, so no outcome is conveyed by colour or glyph alone.
MARKER_BY_STATUS: Dict[BatchItemStatus, str] = {
    BatchItemStatus.PENDING: "\u25cb",
    BatchItemStatus.CONVERTING: "\u23f3",
    BatchItemStatus.SUCCESS: "\u2713",
    BatchItemStatus.SUCCESS_WITH_WARNING: "\u26a0",
    BatchItemStatus.FAILED: "\u2717",
    BatchItemStatus.INFRASTRUCTURE_FAILURE: "\u2717",
}

#: Per-item status wording.
STATE_WORD_BY_STATUS: Dict[BatchItemStatus, str] = {
    BatchItemStatus.PENDING: "pending",
    BatchItemStatus.CONVERTING: "converting",
    BatchItemStatus.SUCCESS: "succeeded",
    BatchItemStatus.SUCCESS_WITH_WARNING: "warning",
    BatchItemStatus.FAILED: "failed",
    BatchItemStatus.INFRASTRUCTURE_FAILURE: "failed",
}

#: Values of the four terminal statuses.  They are read from the presentation
#: outcomes, so the mirror between an item outcome and its wording/severity has
#: exactly one definition and cannot drift silently.
TERMINAL_STATUS_VALUES: Tuple[str, ...] = tuple(outcome.value for outcome in PresentationOutcome)

#: Status wording for a source that was never started (an aborted batch).
NOT_PROCESSED_WORD = "not processed"


def source_identity(path: Union[str, Path]) -> str:
    """Return the deterministic identity used for duplicate detection.

    The identity is the absolute, normalised text of the path, so the same
    source cannot enter the batch twice through two spellings or through a
    relative and an absolute path.  No content hashing is introduced
    (product specification §9.1).

    Args:
        path: Candidate source path.

    Returns:
        str: The comparison identity for ``path``.
    """
    candidate = Path(path)
    try:
        resolved = candidate.resolve()
    except OSError:
        resolved = candidate.absolute()
    return os.path.normcase(str(resolved))


SourceValidator = Callable[[Union[str, Path]], "Optional[Path]"]


def _accept_as_source(value: Union[str, Path]) -> Optional[Path]:
    """Default validator: accept any non-blank path without inspection.

    The production GUI injects
    :func:`md_converter.gui.file_picker.validate_markdown_source` instead, so
    this module stays free of file-system policy.  The default keeps the model
    usable - and testable - on its own.
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return Path(text)


@dataclass(frozen=True)
class BatchAddResult:
    """Outcome of adding one group of candidate sources to a selection.

    Attributes:
        added: Sources that entered the selection, in candidate order.
        duplicates: Candidates whose identity was already in the selection.
        rejected: Candidate text that the validator refused.
    """

    added: Tuple[Path, ...] = ()
    duplicates: Tuple[Path, ...] = ()
    rejected: Tuple[str, ...] = ()

    @property
    def changed(self) -> bool:
        """Whether the selection changed."""
        return bool(self.added)

    def notice_text(self) -> Optional[str]:
        """Return the bounded feedback sentence for this result, or ``None``.

        The wording is deliberately short: it names what was added and what was
        skipped, and never includes a traceback or a technical code
        (product specification §9.2, GUI/UX specification GUI-UX-007).
        """
        sentences: List[str] = []
        if self.added:
            sentences.append(f"Added {_plural(len(self.added), 'file')}.")
        if self.duplicates:
            count = len(self.duplicates)
            if count == 1:
                sentences.append("1 file is already in the list.")
            else:
                sentences.append(f"{count} files are already in the list.")
        if self.rejected:
            count = len(self.rejected)
            if count == 1:
                sentences.append("Skipped 1 item that is not a Markdown file.")
            else:
                sentences.append(f"Skipped {count} items that are not Markdown files.")
        return " ".join(sentences) if sentences else None


class BatchSelection:
    """Ordered, duplicate-free list of selected Markdown sources.

    Args:
        validator: Optional path validator.  It receives a candidate and
            returns the usable :class:`~pathlib.Path`, or ``None`` when the
            candidate is not selectable.  Production passes the shared
            GUI-boundary validator; the default accepts every non-blank path.

    The list order is the execution order (product specification §10), and no
    other ordering (sorting, reordering, prioritisation) is introduced.
    """

    def __init__(self, validator: Optional[SourceValidator] = None) -> None:
        self._validator: SourceValidator = validator if validator is not None else _accept_as_source
        self._sources: List[Path] = []
        self._identities: Dict[str, Path] = {}

    # ------------------------------------------------------------------
    # Read-only state
    # ------------------------------------------------------------------

    @property
    def sources(self) -> Tuple[Path, ...]:
        """Return the selected sources in execution order."""
        return tuple(self._sources)

    @property
    def total(self) -> int:
        """Return the number of selected sources."""
        return len(self._sources)

    @property
    def is_empty(self) -> bool:
        """Whether nothing is selected."""
        return not self._sources

    def __contains__(self, candidate: object) -> bool:
        """Return whether ``candidate`` is already selected."""
        if candidate is None:
            return False
        text = str(candidate).strip()
        if not text:
            return False
        return source_identity(text) in self._identities

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add(self, candidates: Iterable[Union[str, Path]]) -> BatchAddResult:
        """Validate and append ``candidates`` that are not already selected.

        Args:
            candidates: Candidate paths, typically a multi-selection or a
                multi-file drop payload.

        Returns:
            BatchAddResult: What was added, what was already present and what
            the validator refused.  A refused or duplicate candidate never
            disturbs the existing selection.
        """
        added: List[Path] = []
        duplicates: List[Path] = []
        rejected: List[str] = []
        for candidate in candidates:
            validated = self._validator(candidate)
            if validated is None:
                rejected.append(str(candidate))
                continue
            identity = source_identity(validated)
            if identity in self._identities:
                duplicates.append(self._identities[identity])
                continue
            self._identities[identity] = validated
            self._sources.append(validated)
            added.append(validated)
        return BatchAddResult(tuple(added), tuple(duplicates), tuple(rejected))

    def remove(self, sources: Iterable[Union[str, Path]]) -> BatchAddResult:
        """Remove ``sources`` from the selection.

        Args:
            sources: Sources to drop from the list.

        Returns:
            BatchAddResult: The removed sources are reported in ``added`` so a
            caller can echo them; unknown or absent paths are ignored.
        """
        removed: List[Path] = []
        for candidate in sources:
            identity = source_identity(candidate)
            path = self._identities.pop(identity, None)
            if path is None:
                continue
            self._sources = [
                source for source in self._sources if source_identity(source) != identity
            ]
            removed.append(path)
        return BatchAddResult(added=tuple(removed))

    def remove_at(self, index: int) -> Optional[Path]:
        """Remove the source at ``index``.

        Args:
            index: Zero-based position in the selection.

        Returns:
            Optional[Path]: The removed source, or ``None`` when ``index`` does
            not address an entry.
        """
        if index < 0 or index >= len(self._sources):
            return None
        return self.remove((self._sources[index],)).added[0]

    def clear(self) -> None:
        """Remove every source from the selection."""
        self._sources = []
        self._identities = {}


@dataclass(frozen=True)
class BatchItem:
    """One source inside a batch and its retained outcome.

    Attributes:
        source_path: The Markdown source of this job.
        status: Current batch status of the item.
        result: Retained application result, when the job completed normally.
        failure: Retained worker failure evidence, when the job failed outside
            the application contract.  It is never converted into a fabricated
            application result.
        presentation: Derived presentation view of the retained evidence
            (``None`` while the item has not reached a terminal status).
    """

    source_path: Path
    status: BatchItemStatus = BatchItemStatus.PENDING
    result: Optional[ConversionResult] = None
    failure: Optional[FailureEvidence] = None
    presentation: Optional[Presentation] = None

    @property
    def name(self) -> str:
        """Return the file name shown for this item."""
        return self.source_path.name or str(self.source_path)

    @property
    def is_terminal(self) -> bool:
        """Whether the item reached a terminal status."""
        return self.status.is_terminal

    @property
    def output_path(self) -> Optional[Path]:
        """Return the retained produced document path, when there is one."""
        if not self.status.produced_output or self.result is None:
            return None
        return self.result.output_path

    @property
    def marker(self) -> str:
        """Return the non-colour status marker for this item."""
        return MARKER_BY_STATUS[self.status]

    @property
    def state_word(self) -> str:
        """Return the status wording for this item."""
        return STATE_WORD_BY_STATUS[self.status]

    @property
    def summary(self) -> str:
        """Return the presentation summary of the retained evidence, if any."""
        return self.presentation.summary if self.presentation is not None else ""

    @property
    def evidence(self) -> Optional[object]:
        """Return the retained evidence the presentation describes."""
        if self.presentation is None:
            return None
        return self.failure if self.presentation.is_infrastructure_failure else self.result


class BatchRunError(RuntimeError):
    """Raised when the serial batch invariant would be violated."""


class BatchRun:
    """Serial orchestration over one ordered list of sources.

    Args:
        sources: Sources to process, in execution order.

    Exactly one item may be converting at a time:

        begin()  -> item 1 converting
        record_* -> item 1 terminal
        next_source() -> item 2 converting (only after item 1 was recorded)

    ``next_source`` raises :class:`BatchRunError` when the previous item has not
    been recorded, so a caller cannot accidentally start two jobs.  All summary
    values are derived from the item statuses, so the counts cannot drift.
    """

    def __init__(self, sources: Sequence[Union[str, Path]]) -> None:
        unique: List[Path] = []
        seen: Dict[str, Path] = {}
        for source in sources:
            path = Path(source)
            identity = source_identity(path)
            if identity in seen:
                continue
            seen[identity] = path
            unique.append(path)
        self._items: List[BatchItem] = [BatchItem(source_path=path) for path in unique]
        self._running = False
        self._aborted = False
        self._abort_reason: Optional[str] = None

    # ------------------------------------------------------------------
    # Read-only state
    # ------------------------------------------------------------------

    @property
    def items(self) -> Tuple[BatchItem, ...]:
        """Return every item in execution order."""
        return tuple(self._items)

    @property
    def sources(self) -> Tuple[Path, ...]:
        """Return every source in execution order."""
        return tuple(item.source_path for item in self._items)

    @property
    def total(self) -> int:
        """Return the number of sources in the batch."""
        return len(self._items)

    @property
    def processed(self) -> int:
        """Return the number of items that reached a terminal status."""
        return sum(1 for item in self._items if item.is_terminal)

    @property
    def succeeded(self) -> int:
        """Return the number of items that produced a document without warnings."""
        return sum(1 for item in self._items if item.status is BatchItemStatus.SUCCESS)

    @property
    def warnings(self) -> int:
        """Return the number of items that produced a document with warnings."""
        return sum(1 for item in self._items if item.status is BatchItemStatus.SUCCESS_WITH_WARNING)

    @property
    def failed(self) -> int:
        """Return the number of items that produced no document."""
        return sum(1 for item in self._items if item.status.counts_as_failed)

    @property
    def pending(self) -> int:
        """Return the number of items that were not started."""
        return sum(1 for item in self._items if item.status is BatchItemStatus.PENDING)

    @property
    def is_running(self) -> bool:
        """Whether the batch is between ``begin`` and its last item."""
        return self._running

    @property
    def is_complete(self) -> bool:
        """Whether every item reached a terminal status."""
        return bool(self._items) and all(item.is_terminal for item in self._items)

    @property
    def aborted(self) -> bool:
        """Whether a batch-level problem stopped the remaining items."""
        return self._aborted

    @property
    def abort_reason(self) -> str:
        """Return the bounded reason recorded by :meth:`abort`."""
        return self._abort_reason or ""

    @property
    def current_index(self) -> Optional[int]:
        """Return the zero-based index of the item being converted, if any."""
        for index, item in enumerate(self._items):
            if item.status is BatchItemStatus.CONVERTING:
                return index
        return None

    @property
    def current_source(self) -> Optional[Path]:
        """Return the source currently being converted, if any."""
        index = self.current_index
        return None if index is None else self._items[index].source_path

    @property
    def current_position(self) -> int:
        """Return the one-based position shown as "2 of 3", or ``0`` when idle."""
        index = self.current_index
        return 0 if index is None else index + 1

    @property
    def output_directory(self) -> Optional[Path]:
        """Return the authoritative output folder of the batch, if any.

        The value is the containing folder of the first retained produced
        document.  Nothing is guessed from names or configuration, so an
        unsatisfied batch reports ``None`` and the folder action stays
        unavailable (product specification §24).
        """
        for item in self._items:
            produced = item.output_path
            if produced is not None:
                return produced.parent
        return None

    # ------------------------------------------------------------------
    # Serial execution
    # ------------------------------------------------------------------

    def begin(self) -> Optional[Path]:
        """Start the batch and return the first source to convert.

        Returns:
            Optional[Path]: The first source, or ``None`` for an empty batch.
        """
        if self._items and not self.is_complete:
            self._running = True
            self._items[0] = _as_converting(self._items[0])
            return self._items[0].source_path
        self._running = False
        return None

    def next_source(self) -> Optional[Path]:
        """Record nothing and return the next source to convert.

        Returns:
            Optional[Path]: The next pending source, or ``None`` when the batch
            is finished.

        Raises:
            BatchRunError: The previously started item has not reached a
                terminal status yet, so starting another job would break the
                one-active-conversion invariant.
        """
        if self.current_index is not None:
            raise BatchRunError("the current item has not reached a terminal status")
        for index, item in enumerate(self._items):
            if item.status is BatchItemStatus.PENDING:
                self._running = True
                self._items[index] = _as_converting(item)
                return item.source_path
        self._running = False
        return None

    def record_result(self, result: ConversionResult) -> BatchItem:
        """Record one application result for the item being converted.

        Args:
            result: Application-layer conversion outcome.

        Returns:
            BatchItem: The updated item.

        Raises:
            BatchRunError: No item is being converted, or more than one is.
        """
        return self._record(result=result, failure=None, presentation=present_result(result))

    def record_failure(self, failure: FailureEvidence) -> BatchItem:
        """Record one worker failure for the item being converted.

        The item keeps its own infrastructure-failure semantics: it is counted
        as failed and the batch continues with the next source.

        Args:
            failure: Retained worker failure evidence.

        Returns:
            BatchItem: The updated item.

        Raises:
            BatchRunError: No item is being converted, or more than one is.
        """
        return self._record(
            result=None,
            failure=failure,
            presentation=present_job_failure(failure),
        )

    def abort(self, reason: str) -> None:
        """Stop the batch after a batch-level infrastructure problem.

        The already recorded results are preserved; every remaining item stays
        ``PENDING`` and is reported as not processed.  Ordinary per-file
        failures never call this (product specification §15).

        Args:
            reason: Bounded, user-facing reason for stopping.
        """
        self._aborted = True
        self._abort_reason = reason
        self._running = False
        self._items = [
            _as_pending(item) if item.status is BatchItemStatus.CONVERTING else item
            for item in self._items
        ]

    def _record(
        self,
        *,
        result: Optional[ConversionResult],
        failure: Optional[FailureEvidence],
        presentation: Presentation,
    ) -> BatchItem:
        """Apply one terminal outcome to the current item."""
        index = self.current_index
        if index is None:
            raise BatchRunError("no item is currently converting")
        item = self._items[index]
        status = _status_for_presentation(presentation)
        updated = BatchItem(
            source_path=item.source_path,
            status=status,
            result=result,
            failure=failure,
            presentation=presentation,
        )
        self._items[index] = updated
        return updated

    # ------------------------------------------------------------------
    # Presentation helpers
    # ------------------------------------------------------------------

    def headline(self) -> str:
        """Return the batch headline ("Batch complete" / "Batch stopped")."""
        return BATCH_STOPPED_HEADLINE if self._aborted else BATCH_COMPLETE_HEADLINE

    def processed_text(self) -> str:
        """Return the "3 files processed" line of the batch summary."""
        if self._aborted:
            return f"{self.processed} of {self.total} files processed"
        return f"{_plural(self.processed, 'file')} processed"

    def counts_text(self, separator: str = COUNTS_SEPARATOR) -> str:
        """Return the per-outcome counts, for example ``2 succeeded · 1 warning``."""
        parts = (
            f"{self.succeeded} succeeded",
            _plural(self.warnings, "warning"),
            f"{self.failed} failed",
        )
        return separator.join(parts)

    def status_line(self) -> str:
        """Return the single-line batch status shown in the status area."""
        return (
            f"{self.headline()} \u2014 "
            f"{self.processed_text()}{COUNTS_SEPARATOR}{self.counts_text()}"
        )

    def summary_text(self) -> str:
        """Return the multi-line batch summary shown in the completion panel."""
        return "\n".join((self.headline(), self.processed_text(), self.counts_text()))

    def progress_text(self) -> str:
        """Return the "Converting 2 of 3 — B.md" progress line."""
        source = self.current_source
        name = source.name if source is not None else ""
        return f"Converting {self.current_position} of {self.total} " f"\u2014 {name}"

    def report_text(self) -> str:
        """Return the lightweight batch report, aggregated from retained evidence.

        The report only assembles what the single-file path already produced:
        the source, the produced document where there is one, the terminal
        status and the presentation summary.  Diagnostics are never
        recomputed and never reinterpreted (product specification §22).
        """
        blocks: List[str] = [self.headline(), self.processed_text() + "\n" + self.counts_text()]
        if self._aborted and self._abort_reason:
            blocks.append(f"Reason: {self._abort_reason}")
        for item in self._items:
            blocks.append(_item_report_block(item, not_processed=self._aborted))
        return "\n\n".join(blocks)


def _as_converting(item: BatchItem) -> BatchItem:
    """Return ``item`` marked as converting."""
    return BatchItem(source_path=item.source_path, status=BatchItemStatus.CONVERTING)


def _as_pending(item: BatchItem) -> BatchItem:
    """Return ``item`` reset to pending."""
    return BatchItem(source_path=item.source_path)


def _status_for_presentation(presentation: Presentation) -> BatchItemStatus:
    """Return the batch status mirroring ``presentation``.

    The four terminal members share the presentation outcome values, so this is
    a lookup rather than a second status interpretation.
    """
    return BatchItemStatus(presentation.outcome.value)


def _item_report_block(item: BatchItem, *, not_processed: bool) -> str:
    """Return one batch-report block for ``item``.

    Args:
        item: The item to describe.
        not_processed: Whether the batch was stopped before this item started,
            in which case a pending item is labelled as not processed.
    """
    if not_processed and item.status is BatchItemStatus.PENDING:
        heading = f"[{NOT_PROCESSED_WORD.upper()}] {item.name}"
    else:
        heading = f"[{item.status.value}] {item.name}"
    fields: List[str] = [f"Source file: {item.source_path}"]
    produced = item.output_path
    if produced is not None:
        fields.append(f"Output file: {produced}")
    if item.summary:
        fields.append(f"Summary: {item.summary}")
    return heading + "\n" + "\n".join(fields)


def _plural(count: int, noun: str) -> str:
    """Return ``"<count> <noun>"`` with a pluralised noun when needed."""
    return f"{count} {noun}" + ("" if count == 1 else "s")
