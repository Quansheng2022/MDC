"""Application-layer conversion request model (WP-P12-03-01).

Defines :class:`ConversionRequest`, the minimal value object describing one
Markdown -> DOCX conversion at the application boundary
(``Doc/V2/V2_ARCHITECTURE.md`` §5.1).

The model carries application inputs only.  It never embeds compiler, parser,
renderer or GUI objects, contains no mutable global state, and can be
constructed without importing a GUI framework.

Validation policy (WP-P12-03-01 §5)
-----------------------------------
Only structural, application-boundary invariants are validated here:

* ``source_path`` must be supplied as a non-empty ``str``/``pathlib.Path``;
* ``output_path`` is optional, and must be a non-empty path when supplied;
* ``config_overrides`` / ``metadata_overrides`` must be ``str``-keyed mappings
  when supplied.

Deliberately **not** validated here: file existence, source extension, output
naming, and configuration values.  Those belong to the service boundary and
to the canonical core; duplicating them in the value object would invent
product restrictions that the v1.1.0 contract does not have.
"""

from __future__ import annotations

from collections.abc import Mapping as MappingABC
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

__all__ = ["ConversionRequest"]


def _coerce_path(value: Any, *, field_name: str, allow_empty_path_object: bool) -> Path:
    """Return ``value`` as a :class:`~pathlib.Path`.

    Args:
        value: Candidate path supplied by the caller.
        field_name: Field name used in error messages.
        allow_empty_path_object: When ``True`` a ``Path`` instance is accepted
            verbatim (``Path("") == Path(".")`` cannot be distinguished).

    Returns:
        Path: The coerced path.

    Raises:
        TypeError: ``value`` is neither ``str`` nor ``pathlib.Path``.
        ValueError: ``value`` is an empty or whitespace-only string.
    """
    if isinstance(value, Path):
        if not allow_empty_path_object and not str(value):
            raise ValueError(f"{field_name} must be a non-empty path")
        return value
    if isinstance(value, str):
        if not value.strip():
            raise ValueError(f"{field_name} must be a non-empty path")
        return Path(value)
    raise TypeError(f"{field_name} must be a str or pathlib.Path, got {type(value).__name__}")


def _coerce_mapping(value: Any, *, field_name: str) -> Optional[Dict[str, Any]]:
    """Return a shallow copy of ``value`` as a plain ``dict``.

    Args:
        value: Candidate mapping supplied by the caller.
        field_name: Field name used in error messages.

    Returns:
        Optional[Dict[str, Any]]: ``None`` when ``value`` is ``None``, else a
        new ``dict`` with the same items.

    Raises:
        TypeError: ``value`` is neither ``None`` nor a ``str``-keyed mapping.
    """
    if value is None:
        return None
    if not isinstance(value, MappingABC):
        raise TypeError(
            f"{field_name} must be a mapping of str -> value or None, "
            f"got {type(value).__name__}"
        )
    copied: Dict[str, Any] = dict(value)
    for key in copied:
        if not isinstance(key, str):
            raise TypeError(f"{field_name} keys must be str, got {type(key).__name__}")
    return copied


@dataclass(frozen=True)
class ConversionRequest:
    """One Markdown -> DOCX conversion request (application boundary).

    Attributes:
        source_path: Markdown file to convert.
        output_path: Explicit output DOCX path.  When ``None`` the approved
            product default naming behaviour is used by the service.
        config_overrides: Top-level configuration overrides for this request.
            They replace matching top-level keys of the service baseline
            configuration before canonical configuration resolution.
        metadata_overrides: Frontmatter metadata overrides for this request.
            Supplied values take precedence over the file's own frontmatter.

    Example:
        >>> request = ConversionRequest("docs/guide.md")
        >>> request.source_path.name
        'guide.md'
    """

    source_path: Path
    output_path: Optional[Path] = None
    config_overrides: Optional[Dict[str, Any]] = None
    metadata_overrides: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        """Coerce and validate the application-boundary invariants."""
        object.__setattr__(
            self,
            "source_path",
            _coerce_path(self.source_path, field_name="source_path", allow_empty_path_object=True),
        )
        if self.output_path is not None:
            object.__setattr__(
                self,
                "output_path",
                _coerce_path(
                    self.output_path,
                    field_name="output_path",
                    allow_empty_path_object=False,
                ),
            )
        object.__setattr__(
            self,
            "config_overrides",
            _coerce_mapping(self.config_overrides, field_name="config_overrides"),
        )
        object.__setattr__(
            self,
            "metadata_overrides",
            _coerce_mapping(self.metadata_overrides, field_name="metadata_overrides"),
        )

    def __hash__(self) -> int:
        """Hash on the path fields (override mappings are unhashable)."""
        return hash((self.source_path, self.output_path))
