"""Focused fail-closed tests for Pipeline and PassRegistry (P11-MNT-004)."""

from __future__ import annotations

from pathlib import Path

import pytest

from md_converter.ast.nodes import Document
from md_converter.compiler import CompilerContext
from md_converter.diagnostics.collector import DiagnosticCollector
from md_converter.pipeline.pass_registry import PassRegistry
from md_converter.pipeline.passes.base import PassResult, TransformPass
from md_converter.pipeline.pipeline import Pipeline


class RecordingPass(TransformPass):
    """Pass that records whether it executed."""

    def __init__(self, label: str = "recording") -> None:
        super().__init__()
        self.label = label
        self.executed = False

    def run(self, document, diag):
        self.executed = True
        return PassResult(document=document)


class BoomPass(TransformPass):
    """Pass that raises during run."""

    def run(self, document, diag):
        raise RuntimeError("boom during run")


class BrokenInitPass(TransformPass):
    """Enabled pass whose constructor raises."""

    def __init__(self) -> None:
        raise RuntimeError("boom during construction")

    def run(self, document, diag):
        return PassResult(document=document)


class EnabledMarkerPass(TransformPass):
    """Marker pass used for disabled-pass skip verification."""

    def run(self, document, diag):
        return PassResult(document=document)


class DisabledMarkerPass(TransformPass):
    """Disabled marker pass used for skip verification."""

    def run(self, document, diag):
        return PassResult(document=document)


def test_pipeline_runs_successful_enabled_pass() -> None:
    recording = RecordingPass()
    pipeline = Pipeline([recording])

    result = pipeline.run(Document(children=[]), DiagnosticCollector())

    assert result is not None
    assert recording.executed is True


def test_pipeline_run_failure_raises_and_stops_later_pass() -> None:
    later = RecordingPass()
    pipeline = Pipeline([BoomPass(), later])
    diag = DiagnosticCollector()

    with pytest.raises(RuntimeError, match="boom during run"):
        pipeline.run(Document(children=[]), diag)

    assert later.executed is False
    assert "PIPE001" in {d.code for d in diag.diagnostics}


def test_pass_registry_constructor_failure_propagates() -> None:
    registry = PassRegistry()
    registry.register(BrokenInitPass, name="BrokenInitPass", priority=10)
    registry.register(EnabledMarkerPass, name="EnabledMarkerPass", priority=20)

    with pytest.raises(RuntimeError, match="Failed to instantiate Pass 'BrokenInitPass'"):
        registry.get_passes()


def test_disabled_pass_is_skipped() -> None:
    registry = PassRegistry()
    registry.register(EnabledMarkerPass, name="EnabledMarkerPass", priority=10)
    registry.register(DisabledMarkerPass, name="DisabledMarkerPass", priority=20, enabled=False)

    passes = registry.get_passes()

    assert [type(p).__name__ for p in passes] == ["EnabledMarkerPass"]


def test_compiler_pipeline_failure_raises_without_docx(tmp_path: Path) -> None:
    context = CompilerContext.create(
        {
            "diagram": True,
            "output_dir": str(tmp_path),
            "enable_cover": False,
            "toc": False,
        }
    )
    context.pass_registry.register(BoomPass, name="BoomIntegrationPass", priority=5)
    output = tmp_path / "out.docx"

    with pytest.raises(RuntimeError, match="boom during run"):
        context.compile("# Test\n\nHello pipeline.\n", output_path=output)

    assert output.exists() is False
    assert "PIPE001" in {d.code for d in context.diag.diagnostics}
