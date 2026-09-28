"""Standard GUI dialogs for MD_Converter (WP-P12-04-04/06, SBC-02).

Implements the standard Qt dialogs plus GUI-boundary validation:

* Markdown file selection, including the authorized multi-file selection of
  Serial Batch Conversion (WP-P12-04-04 / SBC-02);
* output-folder selection (WP-P12-04-06).

The dialogs decide *what the user selected*; they do not parse frontmatter,
inspect the AST, derive DOCX file names, or call the conversion core
(WP-P12-04-04 §8, WP-P12-04-06 §5).

The chosen paths are handed to ``MainWindow.add_source_files``, which applies
the single validation and state path (WP-P12-04-03 §7): the picker reports the
raw selection and drag & drop (WP-P12-04-05) reuses
:func:`validate_markdown_source`, so the two entry points cannot diverge.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple, Union

from PySide6.QtWidgets import QFileDialog, QWidget

__all__ = [
    "DIALOG_TITLE",
    "DIRECTORY_DIALOG_TITLE",
    "MARKDOWN_EXTENSIONS",
    "MARKDOWN_FILTER",
    "ask_for_markdown_sources",
    "ask_for_output_directory",
    "validate_markdown_source",
    "validate_output_directory",
]

#: Supported source extensions.  The v2.0 GUI contract covers ``.md``; other
#: formats are neither added nor advertised (WP-P12-04-04 §4).
MARKDOWN_EXTENSIONS = (".md",)

#: File-dialog filter, prioritizing Markdown files (WP-P12-04-04 §4).
MARKDOWN_FILTER = "Markdown Files (*.md)"

#: File-dialog caption (plain product language).
DIALOG_TITLE = "Select Markdown file"

#: Directory-dialog caption for the output folder (WP-P12-04-06 §7).
DIRECTORY_DIALOG_TITLE = "Select output folder"


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


def ask_for_markdown_sources(
    parent: Optional[QWidget] = None,
    directory: Optional[Union[str, Path]] = None,
) -> Tuple[str, ...]:
    """Open the standard file dialog and return the chosen paths.

    The dialog supports the authorized multi-file selection (SBC-02), so one
    session can add several Markdown files.  The returned values are raw
    dialog selections: validation, duplicate filtering and the state
    transition happen in the shared selection path.

    Args:
        parent: Optional parent widget for the dialog.
        directory: Optional directory the dialog starts in.  Defaults to the
            user's home directory; no directory is remembered (settings are out
            of scope for P12-04).

    Returns:
        Tuple[str, ...]: The selected paths in dialog order; empty when the
        user cancelled.  Cancelling is not an error (WP-P12-04-04 §5).
    """
    start_dir = str(directory) if directory is not None else str(Path.home())
    return tuple(_open_dialog_many(parent, DIALOG_TITLE, start_dir, MARKDOWN_FILTER))


def validate_output_directory(path: Optional[Union[str, Path]]) -> Optional[Path]:
    """Return ``path`` as a usable output directory, or ``None``.

    Only "the user selected this folder" is validated (WP-P12-04-06 §5): the
    folder must exist and be a directory.  No DOCX file name is derived here.

    Args:
        path: Candidate directory from a dialog.

    Returns:
        Optional[Path]: The validated directory, or ``None`` when the candidate
        is not usable.
    """
    if path is None:
        return None
    text = str(path).strip()
    if not text:
        return None
    candidate = Path(text)
    if not candidate.is_dir():
        return None
    return candidate


def ask_for_output_directory(
    parent: Optional[QWidget] = None,
    directory: Optional[Union[str, Path]] = None,
) -> Optional[str]:
    """Open the standard directory chooser and return the chosen folder.

    Args:
        parent: Optional parent widget for the dialog.
        directory: Optional directory the chooser starts in (the current
            session choice, when there is one).  Nothing is persisted.

    Returns:
        Optional[str]: The selected folder, or ``None`` when the user
        cancelled.  Cancelling keeps the previous choice (WP-P12-04-06 §7).
    """
    start_dir = str(directory) if directory is not None else str(Path.home())
    return _open_directory_dialog(parent, DIRECTORY_DIALOG_TITLE, start_dir) or None


def _open_dialog_many(
    parent: Optional[QWidget],
    title: str,
    directory: str,
    file_filter: str,
) -> List[str]:
    """Call Qt's standard multi-file open dialog and return its raw selection.

    Args:
        parent: Optional parent widget for the dialog.
        title: Dialog caption.
        directory: Initial directory.
        file_filter: File filter string.

    Returns:
        List[str]: Selected paths, or an empty list when the dialog was
        cancelled.
    """
    selected, _ = QFileDialog.getOpenFileNames(parent, title, directory, file_filter)
    return list(selected)


def _open_directory_dialog(
    parent: Optional[QWidget],
    title: str,
    directory: str,
) -> str:
    """Call Qt's standard directory chooser and return its raw selection.

    Args:
        parent: Optional parent widget for the dialog.
        title: Dialog caption.
        directory: Initial directory.

    Returns:
        str: Selected folder, or ``""`` when the dialog was cancelled.  The
        public :func:`ask_for_output_directory` normalizes that to ``None``.
    """
    return QFileDialog.getExistingDirectory(
        parent,
        title,
        directory,
        QFileDialog.Option.ShowDirsOnly,
    )
