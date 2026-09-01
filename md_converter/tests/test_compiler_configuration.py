"""Tests for compiler configuration integration."""

from md_converter.compiler import CompilerContext


def test_compiler_context_uses_resolved_configuration() -> None:
    """A compiler context receives complete, safe default settings."""
    context = CompilerContext.create({"toc": True})

    assert context.config["toc"] is True
    assert context.config["enable_cover"] is True
    assert context.config["style_tables"] is True
