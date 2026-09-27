"""Packaging-only launcher entry shim for the packaged Windows product.

WP-P12-08-01 packaging baseline (``P12-08_SPECIFICATION_BASELINE`` section 5):
the packaged executable must enter the accepted GUI application path

    GUI -> GuiWorker -> ConversionService -> Canonical Core

so this shim dispatches to :func:`md_converter.gui.app.main`.  It deliberately
does not boot the CLI conversion path (``md_converter.cli:main``), which stays a
separate command-line surface with its own console-script entry points.  No
product logic lives here and no ConversionRequest/ConversionResult/
ConversionService, Core, Canonical, QA, golden, CLI/public-API or output
naming/path semantics are touched.
"""

from __future__ import annotations

import sys

from md_converter.gui.app import main

if __name__ == "__main__":
    sys.exit(main(sys.argv))
