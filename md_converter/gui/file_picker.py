"""Markdown file picker for the MD_Converter GUI (WP-P12-04-04).

Implements user-driven Markdown selection and nothing else: the standard Qt
file dialog plus GUI-boundary validation.  The picker decides *which file the
user selected*; it does not parse frontmatter, inspect the AST, or call the
conversion core (WP-P12-04-04 §8).

The validated path is handed to ``MainWindow.set_source`` so that source
selection always flows through the single GUI state-model path
(WP-P12-04-03 §7).  Drag & drop (WP-P12-04-05) reuses
:func:`validate_markdown_source` instead of duplicating validation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from PySide6.QtWidgets import QFileDialog, QWidget

__all__ = [
    "DIALOG_TITLE",
    "MARKDOWN_EXTENSIONS",
    "MARKDOWN_FILTER",
    "ask_for_markdown_source",
    "validate_markdown_source",
]

#: Supported source extensions.  The v2.0 GUI contract covers ``.md``; other
#: formats are neither added nor advertised (WP-P12-04-04 §4).
MARKDOWN_EXTENSIONS = (".md",)

#: File-dialog filter, prioritizing Markdown files (WP-P12-04-04 §4).
MARKDOWN_FILTER = "Markdown Files (*.md)"

#: File-dialog caption (plain product language).
DIALOG_TITLE = "Select Markdown file"


def validate_markdown_source(path: Optional[Union[str, Path]]) -> Optional[Path]:
    """Return ``path`` as a selectable Markdown source, or ``None``.

    Validation is limited to the GUI boundary (WP-P12-04-04 §6): the path must
    be present, must be a file, and must use a supported Markdown extension.
    No frontmatter, AST or conversion inspection happens here.

    Args:
        path: Candidate path from a dialog or drop event.

    Returns:
        Optional[Path]: The validated path, or ``None`` when the candidate is
        not selectable.
    """
    if path is None:
        return None
    text = str(path).strip()
    if not text:
        return None
    candidate = Path(text)
    if not candidate.is_file():
        return None
    if candidate.suffix.lower() not in MARKDOWN_EXTENSIONS:
        return None
    return candidate


def ask_for_markdown_source(
    parent: Optional[QWidget] = None,
    directory: Optional[Union[str, Path]] = None,
) -> Optional[str]:
    """Open the standard file dialog and return the chosen path.

    Args:
        parent: Optional parent widget for the dialog.
        directory: Optional directory the dialog starts in.  Defaults to the
            user's home directory; no directory is remembered (settings are out
            of scope for P12-04).

    Returns:
        Optional[str]: The selected path, or ``None`` when the user cancelled.
        Cancelling is not an error (WP-P12-04-04 §5).
    """
    start_dir = str(directory) if directory is not None else str(Path.home())
    return _open_dialog(parent, DIALOG_TITLE, start_dir, MARKDOWN_FILTER) or None


def _open_dialog(
    parent: Optional[QWidget],
    title: str,
    directory: str,
    file_filter: str,
) -> str:
    """Call Qt's standard open dialog and return its raw selection.

    Args:
        parent: Optional parent widget for the dialog.
        title: Dialog caption.
        directory: Initial directory.
        file_filter: File filter string.

    Returns:
        str: Selected path, or ``""`` when the dialog was cancelled.  The
        public :func:`ask_for_markdown_source` normalizes that to ``None``.
    """
    selected, _ = QFileDialog.getOpenFileName(parent, title, directory, file_filter)
    return selected
