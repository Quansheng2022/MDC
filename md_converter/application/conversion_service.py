"""Application conversion service (WP-P12-03-04).

``ConversionService`` is the first usable implementation of the application
service boundary: it accepts one
:class:`~md_converter.application.conversion_request.ConversionRequest`,
invokes the existing canonical conversion path, and returns one
:class:`~md_converter.application.conversion_result.ConversionResult`
(``Doc/V2/V2_ARCHITECTURE.md`` §5.2, ARCH-INV-001 / ARCH-INV-003).

The service never re-implements the converter.  Every conversion goes through
``CompilerContext.create()`` and ``CompilerContext.compile()`` - the canonical
conversion authority identified by ``DEC-P12-02-01``.  The service performs
only application-level orchestration: input validation, source reading,
frontmatter handling, output path resolution, evidence collection, and
bounded failure translation.

Approved behaviour preserved (WP-P12-03-04 §6, WP-P12-03-05)
-----------------------------------------------------------
The v1.1.0 baseline contains two overlapping file-orchestration paths with
*different* file-name sanitization:

* ``md_converter/cli.py`` (externally visible product behaviour);
* ``CompilerContext.compile_file()`` (context-level convenience helper).

This service deliberately reproduces the **CLI-visible** rule, because that is
the behaviour users observe today and the behaviour a later CLI convergence
(P12-02 §11, step C) must not silently change:

    title -> every Windows-forbidden file-name character and every space
             replaced by "_" -> "<output_dir>/<safe_title>.docx"

``CompilerContext.compile_file()`` keeps a narrower character set and is left
unchanged.  The divergence is recorded as a known legacy inconsistency by the
compatibility characterisation tests (WP-P12-03-05 §7-B); it is *not* unified
here, because unifying it is a product decision that P12-03 is not authorised
to take.

Error policy (WP-P12-03-04 §8, ``V2_ARCHITECTURE.md`` §10)
---------------------------------------------------------
Existing fail-closed behaviour is preserved: the core still raises, and the
service maps the failure to a ``FAILED`` result that retains the full
technical evidence.  Errors are never suppressed into a success outcome.

This module imports no GUI framework.
"""

from __future__ import annotations

import re
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from ..compiler import CompilerContext
from ..quality_gate import QualityGateError
from ..renderer.post_processor import DocxPostProcessor
from ..utils.helpers import parse_frontmatter
from .conversion_request import ConversionRequest
from .conversion_result import (
    ConversionErrorCategory,
    ConversionResult,
    ConversionStatus,
)
from .diagnostics_adapter import ApplicationDiagnostics, DiagnosticsAdapter

__all__ = ["ConversionService", "sanitize_output_title"]

#: Bounded, plain-language description per application error category.
_CATEGORY_MESSAGE: Dict[ConversionErrorCategory, str] = {
    ConversionErrorCategory.INPUT_ERROR: "The source Markdown file could not be used.",
    ConversionErrorCategory.CONFIGURATION_ERROR: "The conversion configuration is invalid.",
    ConversionErrorCategory.DEPENDENCY_ERROR: "A required runtime dependency is unavailable.",
    ConversionErrorCategory.CONVERSION_ERROR: "The document conversion failed.",
    ConversionErrorCategory.OUTPUT_ERROR: "The output document could not be written.",
    ConversionErrorCategory.ENVIRONMENT_ERROR: "The conversion environment is not usable.",
    ConversionErrorCategory.INTERNAL_ERROR: "An unexpected internal error occurred.",
}

#: Quality-gate stages inspected when building failure technical detail.
_GATE_STAGES = ("static_qa", "rendered_qa", "post_processor", "final_artifact_qa")


def sanitize_output_title(title: str) -> str:
    """Return the CLI-equivalent file-name-safe document title.

    Mirrors the existing v1.1.0 CLI rule exactly (``md_converter/cli.py``):
    Windows-forbidden file-name characters and spaces become ``"_"``.

    Args:
        title: Document title (frontmatter ``title`` or the source file stem).

    Returns:
        str: File-name-safe title; non-empty for non-empty input.
    """
    return re.sub(r'[<>:"/\\|?* ]', "_", title)


def _classify_context_error(exc: BaseException) -> ConversionErrorCategory:
    """Classify a compiler-context construction failure."""
    if isinstance(exc, ImportError):
        return ConversionErrorCategory.DEPENDENCY_ERROR
    if isinstance(exc, ValueError):
        # resolve_config() raises ValueError for invalid configuration.
        return ConversionErrorCategory.CONFIGURATION_ERROR
    if isinstance(exc, OSError):
        return ConversionErrorCategory.ENVIRONMENT_ERROR
    return ConversionErrorCategory.INTERNAL_ERROR


def _classify_conversion_error(exc: BaseException) -> ConversionErrorCategory:
    """Classify a canonical conversion failure."""
    if isinstance(exc, QualityGateError):
        return ConversionErrorCategory.CONVERSION_ERROR
    if isinstance(exc, ImportError):
        return ConversionErrorCategory.DEPENDENCY_ERROR
    if isinstance(exc, OSError):
        # The renderer writes the artifact; I/O failures here are output failures.
        return ConversionErrorCategory.OUTPUT_ERROR
    if isinstance(exc, ValueError):
        return ConversionErrorCategory.CONVERSION_ERROR
    return ConversionErrorCategory.INTERNAL_ERROR


class ConversionService:
    """Convert one Markdown file through the canonical compiler path.

    Args:
        config: Baseline configuration for every request served by this
            instance.  It is treated as immutable: per-request
            ``config_overrides`` are applied to a copy.
        context_factory: Callable building the canonical compiler context.
            Defaults to :meth:`CompilerContext.create`.
        adapter: Diagnostics adapter used to normalise evidence.  Defaults to
            :class:`DiagnosticsAdapter`.

    A single instance may serve requests sequentially.  Concurrent use is not
    required to be thread-safe: ``ARCH-THR-002`` places duplicate-execution
    prevention in the GUI layer, and each :meth:`convert` call builds its own
    compiler context.

    Example:
        >>> service = ConversionService({"word_com": False})
        >>> result = service.convert(ConversionRequest("docs/guide.md"))
        >>> result.status.value
        'SUCCESS'
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        *,
        context_factory: Optional[Callable[[Dict[str, Any]], CompilerContext]] = None,
        adapter: Optional[DiagnosticsAdapter] = None,
    ) -> None:
        self._config: Dict[str, Any] = dict(config or {})
        self._context_factory: Callable[[Dict[str, Any]], CompilerContext] = (
            context_factory or CompilerContext.create
        )
        self._adapter = adapter or DiagnosticsAdapter()

    @property
    def config(self) -> Dict[str, Any]:
        """Return a copy of the baseline configuration of this service."""
        return dict(self._config)

    def convert(self, request: ConversionRequest) -> ConversionResult:
        """Convert one Markdown file and return a normalized result.

        Args:
            request: Application-level conversion request.

        Returns:
            ConversionResult: Normalized outcome carrying diagnostics and
            quality-gate evidence.

        Raises:
            TypeError: ``request`` is not a
                :class:`~md_converter.application.conversion_request.ConversionRequest`.
                Call-site programming errors are not conversion failures.
        """
        if not isinstance(request, ConversionRequest):
            raise TypeError("request must be a ConversionRequest instance")

        context: Optional[CompilerContext] = None
        try:
            source_problem = self._source_problem(request.source_path)
            if source_problem is not None:
                return self._failure(
                    request,
                    ConversionErrorCategory.INPUT_ERROR,
                    message=source_problem,
                )

            try:
                raw = request.source_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                return self._failure(request, ConversionErrorCategory.INPUT_ERROR, exc)

            body, metadata = parse_frontmatter(raw)
            if request.metadata_overrides:
                metadata.update(request.metadata_overrides)

            config = self._effective_config(request)
            output_path = self._resolve_output_path(request, metadata, config)

            try:
                context = self._context_factory(config)
            except Exception as exc:
                return self._failure(request, _classify_context_error(exc), exc)

            try:
                context.compile(body, metadata, output_path)
            except Exception as exc:
                category = _classify_conversion_error(exc)
                return self._failure(request, category, exc, context=context)

            if not output_path.exists():
                return self._failure(
                    request,
                    ConversionErrorCategory.OUTPUT_ERROR,
                    message=f"expected output was not produced: {output_path}",
                    context=context,
                )

            self._record_post_processing_evidence(context)
            bundle = self._adapter.build(context)

            if bundle.summary.has_errors:
                first_error = bundle.errors[0]
                return self._failure(
                    request,
                    ConversionErrorCategory.CONVERSION_ERROR,
                    message=first_error.user_message,
                    context=context,
                    bundle=bundle,
                    artifact=output_path,
                )

            return self._success_result(request, output_path, bundle)
        except Exception as exc:
            # Residual application error boundary (V2_ARCHITECTURE.md §10):
            # unmapped conditions become bounded FAILED results carrying the
            # full technical evidence instead of escaping to the adapter layer.
            return self._failure(
                request, ConversionErrorCategory.INTERNAL_ERROR, exc, context=context
            )

    def _effective_config(self, request: ConversionRequest) -> Dict[str, Any]:
        """Return the compiler configuration for ``request``.

        ``config_overrides`` replace matching top-level keys of the baseline
        configuration.  Canonical resolution (product defaults, validation and
        nested merging) then happens inside ``CompilerContext.create()``.
        """
        config = dict(self._config)
        if request.config_overrides:
            config.update(request.config_overrides)
        return config

    @staticmethod
    def _source_problem(source: Path) -> Optional[str]:
        """Return a plain-language problem description when ``source`` is unusable."""
        if not source.exists():
            return f"source file does not exist: {source}"
        if not source.is_file():
            return f"source path is not a file: {source}"
        return None

    @staticmethod
    def _resolve_output_path(
        request: ConversionRequest,
        metadata: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Path:
        """Return the output path for ``request`` using approved behaviour.

        An explicit request ``output_path`` is used verbatim (CLI single-file
        behaviour).  Otherwise the CLI-equivalent default naming rule is
        applied; see :func:`sanitize_output_title`.
        """
        if request.output_path is not None:
            return Path(request.output_path)
        title = metadata.get("title", request.source_path.stem)
        safe_title = sanitize_output_title(title)
        output_dir = Path(config.get("output_dir", "output"))
        return output_dir / f"{safe_title}.docx"

    @staticmethod
    def _record_post_processing_evidence(context: CompilerContext) -> None:
        """Record optional Word COM availability as structured evidence.

        Mirrors the existing CLI behaviour (``cli.py``, P11-MNT-006): when Word
        COM was requested but is unavailable, the degradation is reported as a
        stable warning diagnostic instead of a console-only message, so that
        GUI/CLI surfaces can present it.  Document generation itself is
        unaffected.
        """
        if not context.config.get("word_com", True):
            return
        reason = DocxPostProcessor.com_unavailable_reason()
        if not reason:
            return
        context.diag.warning(
            f"Word COM unavailable ({reason}); "
            "native TOC field kept, page numbers refresh with F9 in Word",
            code=DocxPostProcessor.COM_DIAGNOSTIC_CODE,
            source="post_processor",
        )

    def _success_result(
        self,
        request: ConversionRequest,
        output_path: Path,
        bundle: ApplicationDiagnostics,
    ) -> ConversionResult:
        """Build a successful result from the adapted evidence bundle."""
        status = (
            ConversionStatus.SUCCESS_WITH_WARNING
            if bundle.summary.has_warnings
            else ConversionStatus.SUCCESS
        )
        return ConversionResult(
            status=status,
            source_path=request.source_path,
            output_path=output_path,
            warnings=bundle.warnings,
            errors=bundle.errors,
            diagnostics=bundle.diagnostics,
            diagnostic_summary=bundle.summary,
            quality_gate_report=bundle.quality_gate_report,
        )

    def _failure(
        self,
        request: ConversionRequest,
        category: ConversionErrorCategory,
        exc: Optional[BaseException] = None,
        *,
        message: Optional[str] = None,
        context: Optional[CompilerContext] = None,
        bundle: Optional[ApplicationDiagnostics] = None,
        artifact: Optional[Path] = None,
    ) -> ConversionResult:
        """Build a ``FAILED`` result, keeping all available evidence.

        Args:
            request: Request being converted.
            category: Bounded failure category.
            exc: Underlying exception, when the failure came from one.
            message: Explicit detail message (used instead of ``str(exc)``).
            context: Compiler context, when one exists, for evidence capture.
            bundle: Already adapted diagnostics, when available.
            artifact: Path of an artifact that exists on disk, if any.

        Returns:
            ConversionResult: Failed result with technical detail retained.
        """
        detail_message = message if message is not None else (str(exc) if exc is not None else "")
        error_message = _CATEGORY_MESSAGE[category]
        if detail_message:
            error_message = f"{error_message} ({detail_message})"

        adapter_failure: Optional[str] = None
        evidence = bundle
        if evidence is None:
            evidence, adapter_failure = self._safe_bundle(context)
        if evidence is None:
            evidence = ApplicationDiagnostics.empty()
        technical_detail = self._technical_detail(exc, context, adapter_failure)

        return ConversionResult(
            status=ConversionStatus.FAILED,
            source_path=request.source_path,
            output_path=artifact,
            warnings=evidence.warnings,
            errors=evidence.errors,
            diagnostics=evidence.diagnostics,
            diagnostic_summary=evidence.summary,
            quality_gate_report=evidence.quality_gate_report,
            error_category=category,
            error_message=error_message,
            technical_detail=technical_detail,
        )

    def _safe_bundle(
        self, context: Optional[CompilerContext]
    ) -> Tuple[Optional[ApplicationDiagnostics], Optional[str]]:
        """Adapt ``context`` defensively, keeping adapter failures visible.

        Returns:
            Tuple[Optional[ApplicationDiagnostics], Optional[str]]: The adapted
            bundle (``None`` when adaptation failed) and a description of the
            adapter failure, if any.  The failure text is retained in the
            result's technical detail rather than discarded.
        """
        if context is None:
            return None, None
        try:
            return self._adapter.build(context), None
        except Exception as adapter_exc:
            return None, f"{type(adapter_exc).__name__}: {adapter_exc}"

    def _technical_detail(
        self,
        exc: Optional[BaseException],
        context: Optional[CompilerContext],
        adapter_failure: Optional[str] = None,
    ) -> Optional[str]:
        """Return support/debugging detail for a failed conversion."""
        lines = []
        if exc is not None:
            lines.append(f"{type(exc).__name__}: {exc}")
            if isinstance(exc, QualityGateError):
                lines.append(f"stage: {exc.stage}")
            trace = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            if trace.strip():
                lines.append(trace.rstrip())

        if adapter_failure:
            lines.append(f"diagnostics adapter unavailable: {adapter_failure}")

        if context is not None:
            statuses = self._gate_statuses(context)
            if statuses:
                lines.append("quality gates: " + ", ".join(statuses))

        return "\n".join(lines) if lines else None

    @staticmethod
    def _gate_statuses(context: CompilerContext) -> List[str]:
        """Return ``stage=status`` strings from the canonical gate report."""
        report = getattr(context, "get_quality_gate_report", None)
        if report is None:
            return []
        try:
            data = report()
        except Exception as exc:  # evidence retained as text, never swallowed
            return [f"quality_gate_report unavailable: {type(exc).__name__}: {exc}"]
        if not isinstance(data, dict):
            return []
        statuses = []
        for stage in _GATE_STAGES:
            section = data.get(stage)
            status = section.get("status") if isinstance(section, dict) else None
            if status:
                statuses.append(f"{stage}={status}")
        return statuses
