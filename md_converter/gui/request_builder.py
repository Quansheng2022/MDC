"""GUI-side ConversionRequest construction (WP-P12-05-02).

Target flow (WP-P12-05-02 §3):

    GUI source selection + GUI output-directory preference
        v
    this builder
        v
    ConversionRequest  (application boundary)

Ownership boundary (WP-P12-05-02 §4/§7):

* the GUI owns the selected source file and the output-directory preference;
* the application layer owns the final DOCX name, title/frontmatter precedence,
  filename sanitization and conversion behavior.

The builder therefore never derives a file name.  With an explicit output folder
it passes only the ``output_dir`` configuration intent, which the application
service resolves together with the source's frontmatter title.  It does not
parse frontmatter, sanitize titles, start the worker, or execute conversion.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Union

from ..application.conversion_request import ConversionRequest

__all__ = ["OUTPUT_DIR_CONFIG_KEY", "build_conversion_request"]

#: Canonical configuration key carrying the output-directory intent.
OUTPUT_DIR_CONFIG_KEY = "output_dir"


def build_conversion_request(
    source_path: Optional[Union[str, Path]],
    output_directory: Optional[Union[str, Path]] = None,
) -> Optional[ConversionRequest]:
    """Build one conversion request from the current GUI selections.

    Args:
        source_path: Selected Markdown source.  ``None`` or blank means nothing
            is selected.
        output_directory: Session output-folder preference.  ``None`` or blank
            means "same as source", i.e. the approved service default.

    Returns:
        Optional[ConversionRequest]: The request to convert, or ``None`` when no
        source is selected.  No source path is fabricated (WP-P12-05-02 §6).

    The returned request never carries an ``output_path``: DOCX naming stays
    with the application layer.  An explicit folder is expressed only as the
    ``output_dir`` configuration intent.
    """
    source = _clean(source_path)
    if not source:
        return None

    directory = _clean(output_directory)
    config_overrides: Optional[Dict[str, Any]] = None
    if directory:
        config_overrides = {OUTPUT_DIR_CONFIG_KEY: directory}

    return ConversionRequest(source_path=Path(source), config_overrides=config_overrides)


def _clean(value: Optional[Union[str, Path]]) -> str:
    """Return ``value`` as trimmed text, or an empty string when absent.

    Args:
        value: Candidate path or directory from the GUI session.

    Returns:
        str: Trimmed text (empty when ``value`` is ``None`` or blank).
    """
    if value is None:
        return ""
    return str(value).strip()
