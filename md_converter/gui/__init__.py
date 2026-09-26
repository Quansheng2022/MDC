"""MD_Converter desktop GUI (PySide6).

Layer boundary (``Doc/V2/V2_ARCHITECTURE.md`` ARCH-INV-002, ADR-GUI-001 §5):
PySide6 usage is confined to this package.  ``md_converter.application`` must
stay GUI-independent, and no GUI module may orchestrate conversion internals
directly.

Current scope: GUI runtime bootstrap only
(``Doc/V2/Implementation/P12-04/WP-P12-04-01_GUI_BOOTSTRAP.md``).
"""

from .app import APPLICATION_NAME, create_application, main
from .main_window import MainWindow

__all__ = [
    "APPLICATION_NAME",
    "MainWindow",
    "create_application",
    "main",
]
