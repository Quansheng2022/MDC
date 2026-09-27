"""Shared packaging helpers for the MD Converter PyInstaller specs (P12-08).

The two ``.spec`` files at the project root stay thin by delegating the
packaging rules that must be identical in both build profiles to this module:

* the operating-system libraries that must never be bundled (WP-P12-08-02);
* the developer/test material that must never be shipped (WP-P12-08-04);
* the Windows version resource, generated from the authoritative project
  version so the executable cannot drift from ``pyproject.toml``
  (WP-P12-08-04).

Nothing here changes product behaviour: these helpers only decide which files
end up inside the packaged payload and which metadata the executable carries.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Iterable, Sequence, Tuple

__all__ = [
    "read_project_version",
    "strip_shadowed_system_dlls",
    "strip_development_material",
    "write_version_resource",
]

#: DLL families that must come from the operating system, never from the
#: bundle.  A developer-machine ``PATH`` (portable tool runtimes) can otherwise
#: leak copies into ``_internal``, where they shadow the system libraries and
#: make Qt 6 fail with WinError 127.  Windows 10+ - the supported baseline -
#: provides all of them.
_SHADOWED_SYSTEM_DLLS: Tuple[str, ...] = ("ucrtbase.dll",)
_SHADOWED_SYSTEM_DLL_PREFIXES: Tuple[str, ...] = ("api-ms-win-", "icu")

#: Package data that is developer/test material rather than runtime resource.
_DEVELOPMENT_DATA_PREFIXES: Tuple[str, ...] = ("md_converter/tests/",)
_DEVELOPMENT_DATA_FILES: Tuple[str, ...] = ("md_converter/.gitignore",)


def _is_shadowed_system_dll(name: str) -> bool:
    """Return whether ``name`` is an operating-system DLL that must not ship."""
    lower = os.path.basename(name).lower()
    if not lower.endswith(".dll"):
        return False
    if lower in _SHADOWED_SYSTEM_DLLS:
        return True
    return lower.startswith(_SHADOWED_SYSTEM_DLL_PREFIXES)


def strip_shadowed_system_dlls(binaries: Sequence) -> list:
    """Drop collected copies of operating-system DLLs from ``binaries``.

    Args:
        binaries: PyInstaller ``Analysis.binaries`` entries.

    Returns:
        list: The entries that may be bundled.
    """
    return [entry for entry in binaries if not _is_shadowed_system_dll(entry[0])]


def _is_development_material(destination: str) -> bool:
    """Return whether a collected data file is developer/test material."""
    normalized = destination.replace("\\", "/")
    if normalized in _DEVELOPMENT_DATA_FILES:
        return True
    return normalized.startswith(_DEVELOPMENT_DATA_PREFIXES)


def strip_development_material(datas: Sequence) -> list:
    """Drop test/dev data files from ``datas``.

    ``collect_data_files('md_converter')`` also picks up the acceptance
    corpus, golden samples and fixtures, which are development material and
    must not reach the packaged payload.

    Args:
        datas: PyInstaller ``Analysis.datas`` entries.

    Returns:
        list: The entries that may be bundled.
    """
    return [entry for entry in datas if not _is_development_material(entry[0])]


def read_project_version(project_root: str | os.PathLike) -> str:
    """Return ``[project].version`` from ``pyproject.toml``.

    ``pyproject.toml`` is the single version authority (WP-P12-08-04); the
    executable resource and the installer both mirror this value.

    Args:
        project_root: Repository root that contains ``pyproject.toml``.

    Returns:
        str: The authoritative version string.

    Raises:
        FileNotFoundError: ``pyproject.toml`` is missing.
        ValueError: No project version could be read.
    """
    pyproject = Path(project_root) / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    try:  # Python 3.11+
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover - build-time fallback
        match = re.search(r'(?m)^\s*version\s*=\s*"([^"]+)"', text)
        if not match:
            raise ValueError(f"no [project].version found in {pyproject}") from None
        return match.group(1)

    data = tomllib.loads(text)
    version = data.get("project", {}).get("version")
    if not version:
        raise ValueError(f"no [project].version found in {pyproject}")
    return str(version)


def _version_tuple(version: str) -> Tuple[int, int, int, int]:
    """Return a four-element Windows version tuple for ``version``."""
    numbers = [int(part) for part in re.findall(r"\d+", version)[:4]]
    while len(numbers) < 4:
        numbers.append(0)
    return tuple(numbers)  # type: ignore[return-value]


def write_version_resource(
    destination: str | os.PathLike,
    version: str,
    *,
    product_name: str,
    original_filename: str,
    file_description: str,
    company_name: str,
    copyright_text: str,
) -> Path:
    """Write a PyInstaller version resource file and return its path.

    The values mirror the authoritative product metadata (product name from
    the GUI product identity, publisher/copyright from the installer script)
    while the version itself comes from ``pyproject.toml``.

    Args:
        destination: Path of the version resource to write.
        version: Authoritative project version, e.g. ``"1.1.0"``.
        product_name: Product name shown by Windows.
        original_filename: Name of the packaged executable.
        file_description: Short description shown by Windows.
        company_name: Publisher shown by Windows.
        copyright_text: Copyright shown by Windows.

    Returns:
        pathlib.Path: The written file.
    """
    numbers = _version_tuple(version)
    version_tuple = "({0}, {1}, {2}, {3})".format(*numbers)
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """# Generated by packaging/windows/pyi_support.py (WP-P12-08-04).
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={version_tuple},
    prodvers={version_tuple},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [
          StringStruct('CompanyName', {company_name!r}),
          StringStruct('FileDescription', {file_description!r}),
          StringStruct('FileVersion', {version!r}),
          StringStruct('InternalName', {product_name!r}),
          StringStruct('LegalCopyright', {copyright_text!r}),
          StringStruct('OriginalFilename', {original_filename!r}),
          StringStruct('ProductName', {product_name!r}),
          StringStruct('ProductVersion', {version!r})
        ]
      )
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
""".format(
            version_tuple=version_tuple,
            company_name=company_name,
            file_description=file_description,
            version=version,
            product_name=product_name,
            copyright_text=copyright_text,
            original_filename=original_filename,
        ),
        encoding="utf-8",
    )
    return path
