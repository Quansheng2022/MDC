"""Development entry point for the GUI: ``python -m md_converter.gui``.

``[project.scripts]`` is a packaging contract owned by the existing
packaging-metadata tests and P12-08; this module provides the development
launch path without changing it (WP-P12-04-01 §3/§7).
"""

from __future__ import annotations

import sys

from .app import main

if __name__ == "__main__":
    sys.exit(main(sys.argv))
