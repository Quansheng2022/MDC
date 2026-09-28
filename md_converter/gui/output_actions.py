"""Safe post-conversion output actions for the MD_Converter GUI (WP-P12-06-05, SBC-05).

Two convenience actions open the *retained* conversion artifact, and a third
opens the authoritative output folder retained by a batch:

    Open Document  ->  the artifact itself
    Open Folder    ->  the folder that contains the artifact
    Open Directory ->  an already resolved, authoritative folder

Path authority (WP-P12-06-05 §"Path authority"): the only artifact path used
here is the one handed in by the caller, which is
``ConversionResult.output_path``.  Nothing is derived from the source file, the
output-folder preference, configuration, frontmatter, sanitisation rules or a
guessed output name - there is deliberately no filename logic in this module.
The batch folder action receives the folder that
:attr:`md_converter.gui.batch.BatchRun.output_directory` derived from the first
retained produced document, so it does not guess either.

Launching goes through the standard Qt platform facility
(``QDesktopServices.openUrl`` on a local file URL); no shell command string is
built and no process is spawned directly.  A missing or unreadable artifact
fails safely: the helper reports ``False``, never substitutes another path and
never triggers a conversion.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QMessageBox, QWidget

__all__ = [
    "MISSING_ARTIFACT_TEXT",
    "MISSING_ARTIFACT_TITLE",
    "notify_missing_artifact",
    "open_document",
    "open_directory",
    "open_folder",
    "resolve_artifact",
    "resolve_directory",
]

#: Concise local message shown when the retained artifact is gone.
MISSING_ARTIFACT_TITLE = "File not available"
MISSING_ARTIFACT_TEXT = (
    "The generated document could not be found:\n{path}\n\n" "It may have been moved or deleted."
)


def resolve_artifact(path: Optional[Union[str, Path]]) -> Optional[Path]:
    """Return ``path`` as a :class:`Path` when its artifact is present.

    Args:
        path: Retained artifact path (``ConversionResult.output_path``).

    Returns:
        Optional[Path]: The path when a file exists there, otherwise ``None``.
        Missing, unreadable or unexpected paths fail closed.
    """
    if path is None:
        return None
    candidate = Path(path)
    try:
        if candidate.is_file():
            return candidate
    except OSError:
        return None
    return None


def open_document(path: Optional[Union[str, Path]]) -> bool:
    """Open the retained artifact with the standard platform handler.

    Args:
        path: Retained artifact path.

    Returns:
        bool: ``True`` when the platform accepted the request; ``False`` when
        the artifact is missing or could not be opened.  The file itself is
        never modified.
    """
    artifact = resolve_artifact(path)
    if artifact is None:
        return False
    return bool(QDesktopServices.openUrl(QUrl.fromLocalFile(str(artifact))))


def open_folder(path: Optional[Union[str, Path]]) -> bool:
    """Open the folder containing the retained artifact.

    Args:
        path: Retained artifact path.

    Returns:
        bool: ``True`` when the platform accepted the request; ``False`` when
        the artifact or its folder is missing.  Highlighting the file is not
        attempted: opening the containing folder is sufficient and avoids
        platform-specific shell complexity.
    """
    artifact = resolve_artifact(path)
    if artifact is None:
        return False
    folder = artifact.parent
    try:
        if not folder.is_dir():
            return False
    except OSError:
        return False
    return bool(QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder))))


def resolve_directory(path: Optional[Union[str, Path]]) -> Optional[Path]:
    """Return ``path`` as a :class:`Path` when it is an existing directory.

    Args:
        path: Candidate folder (for the batch action, the folder retained by
            :class:`~md_converter.gui.batch.BatchRun`).

    Returns:
        Optional[Path]: The folder when it is usable, otherwise ``None``.
        Missing or unreadable folders fail closed.
    """
    if path is None:
        return None
    candidate = Path(path)
    try:
        if candidate.is_dir():
            return candidate
    except OSError:
        return None
    return None


def open_directory(path: Optional[Union[str, Path]]) -> bool:
    """Open an authoritative folder with the standard platform handler.

    Args:
        path: Folder to open.

    Returns:
        bool: ``True`` when the platform accepted the request; ``False`` when
        the folder is missing or could not be opened.  No path is derived here.
    """
    directory = resolve_directory(path)
    if directory is None:
        return False
    return bool(QDesktopServices.openUrl(QUrl.fromLocalFile(str(directory))))


def notify_missing_artifact(parent: Optional[QWidget], path: object) -> None:
    """Show a concise local message that the retained artifact is gone.

    Args:
        parent: Parent widget for the message.
        path: Retained artifact path that could not be found.
    """
    QMessageBox.warning(
        parent,
        MISSING_ARTIFACT_TITLE,
        MISSING_ARTIFACT_TEXT.format(path=path),
    )
