"""GUI application bootstrap (WP-P12-04-01).

Runtime boundary for the desktop GUI (WP-P12-04-01 §4):

    entry point -> QApplication -> MainWindow -> show -> Qt event loop -> close

Scope is the bootstrap only.  This module must not call ``ConversionService``
or ``CompilerContext``, must not create worker threads, and must not add file
selection, drag & drop, output selection, diagnostics UX or settings
(WP-P12-04-01 §8).

High-DPI scaling is provided by Qt 6 defaults (``V2_GUI_UX_SPEC`` §17); no
deprecated high-DPI attributes are set here.

A console-script or executable entry point is a packaging decision deferred to
P12-08 (WP-P12-04-01 §3).  The development entry path is
``python -m md_converter.gui``.
"""

from __future__ import annotations

import sys
from typing import Optional, Sequence

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

from .main_window import MainWindow

__all__ = ["APPLICATION_NAME", "ORGANIZATION_NAME", "create_application", "main"]

#: Product identity used by Qt (and by QSettings once settings exist).
APPLICATION_NAME = "MD Converter"
ORGANIZATION_NAME = "MD Converter"


def create_application(argv: Optional[Sequence[str]] = None) -> QApplication:
    """Return the process :class:`QApplication`, creating it when necessary.

    Qt allows only one application object per process, so an existing
    instance is reused.  This keeps the bootstrap usable from tests and from
    embedded launchers.

    Args:
        argv: Argument list passed to Qt.  Defaults to ``sys.argv``.

    Returns:
        QApplication: The single GUI application instance for this process.

    Raises:
        RuntimeError: A non-GUI ``QCoreApplication`` already exists, in which
            case a GUI cannot be started in this process.
    """
    existing = QCoreApplication.instance()
    if isinstance(existing, QApplication):
        return existing
    if existing is not None:
        raise RuntimeError(
            "a non-GUI QCoreApplication already exists; "
            "the GUI bootstrap requires a QApplication"
        )

    app = QApplication(list(argv) if argv is not None else list(sys.argv))
    app.setApplicationName(APPLICATION_NAME)
    app.setApplicationDisplayName(APPLICATION_NAME)
    app.setOrganizationName(ORGANIZATION_NAME)
    return app


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Launch the GUI and return the Qt exit code.

    Args:
        argv: Argument list passed to Qt.  Defaults to ``sys.argv``.

    Returns:
        int: Process exit code returned by the Qt event loop.
    """
    app = create_application(argv)
    window = MainWindow()
    window.show()
    return app.exec()
