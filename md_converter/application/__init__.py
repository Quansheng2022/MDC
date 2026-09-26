"""Application layer for MD_Converter v2.0 (P12-03).

The application layer is the shared, GUI-independent boundary between product
adapters (CLI, GUI worker) and the canonical conversion core:

    adapter -> ConversionService -> CompilerContext (canonical core)

Boundaries are defined by ``Doc/V2/V2_ARCHITECTURE.md``:

* §5  Application Service Boundary (``ConversionRequest`` / ``ConversionService``
      / ``ConversionResult``);
* §10 Error Boundary (bounded application error taxonomy);
* §11 Diagnostics Boundary (adapt existing evidence, never replace it);
* ARCH-INV-002 / ARCH-INV-004 (no duplicated conversion logic, no GUI state in
  the canonical AST).

Nothing in this package may import a GUI framework.
"""

from .conversion_request import ConversionRequest
from .conversion_result import (
    ConversionErrorCategory,
    ConversionResult,
    ConversionStatus,
)
from .conversion_service import ConversionService, sanitize_output_title
from .diagnostics_adapter import (
    ApplicationDiagnostic,
    ApplicationDiagnostics,
    DiagnosticsAdapter,
    DiagnosticSummary,
)

__all__ = [
    "ApplicationDiagnostic",
    "ApplicationDiagnostics",
    "ConversionErrorCategory",
    "ConversionRequest",
    "ConversionResult",
    "ConversionService",
    "ConversionStatus",
    "DiagnosticSummary",
    "DiagnosticsAdapter",
    "sanitize_output_title",
]
