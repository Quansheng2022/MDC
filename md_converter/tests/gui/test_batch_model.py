"""Focused verification for the Qt-free serial batch model (SBC-03).

Covered at model level, with no GUI runtime:

* ordered, duplicate-free selection (including relative/absolute spellings);
* bounded feedback wording for added, duplicate and rejected candidates;
* the serial invariant ``next job only after a terminal item``;
* continue-after-failure and warning continuation;
* derived summary counts and the aggregate batch report;
* the single mirror between item statuses and the presentation outcomes.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import List, Optional

import pytest

from md_converter.application.conversion_result import (
    ConversionErrorCategory,
    ConversionResult,
    ConversionStatus,
)
from md_converter.application.diagnostics_adapter import ApplicationDiagnostic
from md_converter.gui.batch import (
    MARKER_BY_STATUS,
    STATE_WORD_BY_STATUS,
    BatchItemStatus,
    BatchRun,
    BatchRunError,
    BatchSelection,
    source_identity,
)
from md_converter.gui.presentation_model import PresentationOutcome, present_result


def _warning_record() -> ApplicationDiagnostic:
    """Return one warning-level diagnostic record."""
    return ApplicationDiagnostic(
        severity="WARNING",
        code="QA_STATIC_WARN",
        message="QA_STATIC_WARN technical message",
        user_message="A heading style was adjusted.",
    )


def _success(output: Optional[Path] = None) -> ConversionResult:
    """Return a successful result, optionally with a produced document."""
    return ConversionResult(status=ConversionStatus.SUCCESS, output_path=output)


def _warning(output: Optional[Path] = None) -> ConversionResult:
    """Return a successful-with-warning result."""
    record = _warning_record()
    return ConversionResult(
        status=ConversionStatus.SUCCESS_WITH_WARNING,
        output_path=output,
        warnings=(record,),
        diagnostics=(record,),
    )


def _failure(message: str = "The document could not be generated.") -> ConversionResult:
    """Return a failed result."""
    return ConversionResult(
        status=ConversionStatus.FAILED,
        error_category=ConversionErrorCategory.CONVERSION_ERROR,
        error_message=message,
    )


def _validator(accepted: List[str]):
    """Return a validator that accepts only the named files and records calls."""
    seen: List[str] = []

    def validate(value) -> Optional[Path]:
        text = str(value)
        seen.append(text)
        name = Path(text).name
        return Path(text) if name in accepted else None

    return validate, seen


# ============================================================
# Selection
# ============================================================


def test_selection_keeps_the_order_it_was_given() -> None:
    """§10: the list order is the execution order."""
    selection = BatchSelection()
    result = selection.add(["c.md", "a.md", "b.md"])

    assert [path.name for path in result.added] == ["c.md", "a.md", "b.md"]
    assert [path.name for path in selection.sources] == ["c.md", "a.md", "b.md"]


def test_selection_never_contains_the_same_source_twice(tmp_path: Path) -> None:
    """§9.1: the same absolute source appears exactly once."""
    markdown = tmp_path / "notes.md"
    markdown.write_text("# Notes\n", encoding="utf-8")
    selection = BatchSelection()

    first = selection.add([markdown])
    second = selection.add([str(markdown), markdown.absolute()])

    assert first.added == (markdown,)
    assert second.added == ()
    assert len(second.duplicates) == 2
    assert selection.sources == (markdown,)
    assert selection.total == 1
    assert markdown in selection


def test_selection_identity_is_path_based_not_content_based(tmp_path: Path) -> None:
    """§9.1: duplicates are detected by path, and no content hash is involved."""
    first = tmp_path / "a.md"
    second = tmp_path / "b.md"
    first.write_text("same\n", encoding="utf-8")
    second.write_text("same\n", encoding="utf-8")

    selection = BatchSelection()
    result = selection.add([first, second])

    assert len(result.added) == 2
    assert source_identity(first) != source_identity(second)


def test_selection_reports_rejected_candidates() -> None:
    """§9.2: a rejected candidate never enters the list."""
    validate, seen = _validator(["a.md"])
    selection = BatchSelection(validate)

    result = selection.add(["a.md", "b.txt", ""])

    assert [path.name for path in result.added] == ["a.md"]
    assert len(result.rejected) == 2
    assert seen == ["a.md", "b.txt", ""]
    assert selection.total == 1


def test_rejected_candidate_does_not_disturb_the_selection() -> None:
    """§9.2: a rejected item leaves the existing selection untouched."""
    validate, _ = _validator(["a.md"])
    selection = BatchSelection(validate)
    selection.add(["a.md"])

    result = selection.add(["b.txt"])

    assert result.changed is False
    assert selection.sources == (Path("a.md"),)


def test_notice_text_is_bounded_product_language() -> None:
    """§9.2: feedback names what happened without technical detail."""
    validate, _ = _validator(["a.md"])
    selection = BatchSelection(validate)
    selection.add(["a.md"])

    result = selection.add(["a.md", "b.txt", "c.txt"])
    notice = result.notice_text()

    assert notice is not None
    assert "already in the list" in notice
    assert "Skipped 2 items" in notice
    for token in ("Traceback", "None", "QA_", "0x"):
        assert token not in notice


def test_notice_text_is_absent_when_nothing_happened() -> None:
    """Nothing to report means no notice line at all."""
    validate, _ = _validator([])
    selection = BatchSelection(validate)

    assert selection.add([]).notice_text() is None


def test_remove_and_clear_operate_on_the_ordered_selection() -> None:
    """§9: single entries can be removed and the whole list cleared."""
    selection = BatchSelection()
    selection.add(["a.md", "b.md", "c.md"])

    assert selection.remove_at(1) == Path("b.md")
    assert [path.name for path in selection.sources] == ["a.md", "c.md"]
    assert selection.remove_at(5) is None

    assert selection.remove([Path("a.md")]).added == (Path("a.md"),)
    assert selection.sources == (Path("c.md"),)
    assert selection.remove([Path("c.md")]).added == (Path("c.md"),)
    assert selection.is_empty is True

    selection.add(["a.md"])
    selection.clear()
    assert selection.total == 0
    assert selection.is_empty is True


# ============================================================
# Status mirror
# ============================================================


def test_terminal_statuses_mirror_the_presentation_outcomes() -> None:
    """One taxonomy: a terminal item status is a presentation outcome."""
    for outcome in PresentationOutcome:
        assert BatchItemStatus(outcome.value).value == outcome.value

    assert BatchItemStatus.PENDING.is_terminal is False
    assert BatchItemStatus.CONVERTING.is_terminal is False
    assert BatchItemStatus.SUCCESS.produced_output is True
    assert BatchItemStatus.SUCCESS_WITH_WARNING.produced_output is True
    assert BatchItemStatus.FAILED.produced_output is False
    assert BatchItemStatus.INFRASTRUCTURE_FAILURE.counts_as_failed is True


def test_every_status_has_a_marker_and_a_word() -> None:
    """§31: no outcome is conveyed by colour or glyph alone."""
    assert set(MARKER_BY_STATUS) == set(BatchItemStatus)
    assert set(STATE_WORD_BY_STATUS) == set(BatchItemStatus)
    assert all(marker.strip() for marker in MARKER_BY_STATUS.values())
    assert all(word.strip() for word in STATE_WORD_BY_STATUS.values())


# ============================================================
# Serial run
# ============================================================


def test_run_starts_the_first_source_only() -> None:
    """§11: begin hands out one source and marks it converting."""
    run = BatchRun([Path("a.md"), Path("b.md"), Path("c.md")])

    assert run.begin() == Path("a.md")
    assert run.is_running is True
    assert run.current_position == 1
    assert run.progress_text() == "Converting 1 of 3 \u2014 a.md"
    assert [item.status for item in run.items] == [
        BatchItemStatus.CONVERTING,
        BatchItemStatus.PENDING,
        BatchItemStatus.PENDING,
    ]


def test_next_source_is_refused_before_the_current_item_is_recorded() -> None:
    """§11: the one-active-conversion invariant fails loudly."""
    run = BatchRun([Path("a.md"), Path("b.md")])
    run.begin()

    with pytest.raises(BatchRunError, match="terminal status"):
        run.next_source()

    assert run.current_source == Path("a.md")
    assert [item.status for item in run.items][1] is BatchItemStatus.PENDING


def test_recording_advances_one_item_at_a_time() -> None:
    """§11: exactly one item is converting at any moment."""
    run = BatchRun([Path("a.md"), Path("b.md"), Path("c.md")])
    converting: List[int] = []
    run.begin()

    while run.current_source is not None:
        converting.append(sum(1 for item in run.items if item.status is BatchItemStatus.CONVERTING))
        run.record_result(_success())
        if run.next_source() is None:
            break

    assert converting == [1, 1, 1]
    assert run.is_running is False
    assert run.is_complete is True
    assert run.succeeded == 3
    assert run.output_directory is None


def test_continue_after_failure_and_warning() -> None:
    """§15/§16: failures and warnings both advance to the next source."""
    run = BatchRun([Path("a.md"), Path("b.md"), Path("c.md")])
    run.begin()
    run.record_result(_failure())
    assert run.next_source() == Path("b.md")
    run.record_result(_warning())
    assert run.next_source() == Path("c.md")
    run.record_result(_success())

    assert run.next_source() is None
    assert (run.processed, run.succeeded, run.warnings, run.failed, run.pending) == (3, 1, 1, 1, 0)
    assert run.is_complete is True


def test_item_level_infrastructure_failure_continues_the_batch() -> None:
    """§15: an item-level worker failure is recorded and the batch continues."""

    class Evidence:
        error_type = "RuntimeError"
        message = "service exploded"
        traceback = "Traceback (most recent call last): ..."

    run = BatchRun([Path("a.md"), Path("b.md")])
    run.begin()
    item = run.record_failure(Evidence())

    assert item.status is BatchItemStatus.INFRASTRUCTURE_FAILURE
    assert item.output_path is None
    assert item.summary
    assert run.failed == 1
    assert run.next_source() == Path("b.md")
    run.record_result(_success())
    assert run.is_complete is True


def test_result_and_source_never_mismatch() -> None:
    """§21: every recorded result stays attached to its own source."""
    run = BatchRun([Path("a.md"), Path("b.md")])
    run.begin()
    run.record_result(_success(Path("out/a.docx")))
    run.next_source()
    run.record_result(_failure())

    first, second = run.items
    assert first.source_path == Path("a.md")
    assert first.output_path == Path("out/a.docx")
    assert second.source_path == Path("b.md")
    assert second.result is not None
    assert second.result.is_failed is True
    assert run.output_directory == Path("out")


def test_failed_result_carries_no_invented_output_path() -> None:
    """§17/§18: the batch never invents a produced document."""
    run = BatchRun([Path("a.md")])
    run.begin()
    run.record_result(_failure())
    run.next_source()

    assert run.items[0].output_path is None
    assert run.output_directory is None


def test_run_without_items_completes_immediately() -> None:
    """An empty batch never reports itself as running."""
    run = BatchRun([])

    assert run.begin() is None
    assert run.is_running is False
    assert run.is_complete is False
    assert run.total == 0
    assert run.progress_text() == "Converting 0 of 0 \u2014 "


def test_run_deduplicates_its_sources() -> None:
    """A defensive duplicate cannot create two jobs for one file."""
    run = BatchRun([Path("a.md"), Path("a.md"), Path("b.md")])

    assert run.total == 2
    assert run.sources == (Path("a.md"), Path("b.md"))


def test_abort_preserves_results_and_reports_remaining_files() -> None:
    """§15: only a batch-level problem stops the queue."""
    run = BatchRun([Path("a.md"), Path("b.md"), Path("c.md")])
    run.begin()
    run.record_result(_success(Path("out/a.docx")))
    run.next_source()

    run.abort("the next conversion could not be started")

    assert run.aborted is True
    assert run.is_running is False
    assert (run.processed, run.pending) == (1, 2)
    assert run.succeeded == 1
    assert run.items[1].status is BatchItemStatus.PENDING
    assert run.headline() == "Batch stopped"
    assert "1 of 3 files processed" in run.processed_text()
    assert "NOT PROCESSED" in run.report_text()


# ============================================================
# Summary and report
# ============================================================


def test_summary_counts_derive_from_item_statuses() -> None:
    """§21: the summary is derived, never maintained separately."""
    run = BatchRun([Path("a.md"), Path("b.md"), Path("c.md")])
    run.begin()
    run.record_result(_success())
    run.next_source()
    run.record_result(_warning())
    run.next_source()
    run.record_result(_failure())

    assert run.summary_text() == (
        "Batch complete\n3 files processed\n1 succeeded \u00b7 1 warning \u00b7 1 failed"
    )
    assert run.status_line() == (
        "Batch complete \u2014 3 files processed"
        " \u00b7 1 succeeded \u00b7 1 warning \u00b7 1 failed"
    )
    assert run.counts_text(", ") == "1 succeeded, 1 warning, 1 failed"


def test_report_text_aggregates_retained_evidence_only() -> None:
    """§22: the report shows source, output, status and the retained summary."""
    run = BatchRun([Path("a.md"), Path("b.md")])
    run.begin()
    run.record_result(_warning(Path("out/a.docx")))
    run.next_source()
    run.record_result(_failure("The document could not be generated."))
    run.next_source()

    report = run.report_text()

    assert "Batch complete" in report
    assert "2 files processed" in report
    assert "0 succeeded \u00b7 1 warning \u00b7 1 failed" in report
    assert "[SUCCESS_WITH_WARNING] a.md" in report
    assert "[FAILED] b.md" in report
    assert "Output file: out" in report
    assert f"Summary: {present_result(_warning(Path('out/a.docx'))).summary}" in report
    assert "The document could not be generated." in report


def test_report_does_not_claim_an_output_for_a_failure() -> None:
    """§18/§22: a failed item shows no produced document."""
    run = BatchRun([Path("a.md")])
    run.begin()
    run.record_result(_failure())
    run.next_source()

    report = run.report_text()

    assert "Output file:" not in report
    assert "[FAILED] a.md" in report


def test_batch_model_is_qt_free() -> None:
    """The orchestration model stays unit-testable without a GUI runtime."""
    import ast

    module_path = Path(__file__).resolve().parents[2] / "gui" / "batch.py"
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
            imported.update(f"{node.module}.{alias.name}".lstrip(".") for alias in node.names)

    assert not [name for name in imported if name.startswith(("PySide6", "PyQt5", "PyQt6"))]
    assert not [name for name in imported if name.startswith("md_converter.compiler")]
    # No concurrency machinery is introduced by the model itself.
    source = module_path.read_text(encoding="utf-8")
    for token in ("threading", "QThread", "concurrent.futures"):
        assert token not in source, token


def test_model_does_not_require_a_gui_thread() -> None:
    """The model runs to completion on a plain worker-less interpreter."""
    assert threading.current_thread() is threading.main_thread()
    run = BatchRun([Path("a.md")])
    run.begin()
    run.record_result(_success())
    run.next_source()
    assert run.is_complete is True
