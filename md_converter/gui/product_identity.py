"""Product identity and privacy wording for the GUI (WP-P12-07-03).

The About surface is a presentation of facts the product can actually stand
behind (``V2_PRODUCT_SPEC`` §1/§5, ``V2_GUI_UX_SPEC`` §15):

* the frozen product positioning;
* the authoritative product version - read from ``md_converter.__version__``,
  the same metadata ``pyproject.toml`` and the release evidence use, so no
  second version constant is maintained here;
* the product name declared by :mod:`md_converter.gui.app`;
* the copyright / licence wording that mirrors ``EULA.txt``.

Privacy wording is deliberately bounded.  The GUI states what the normal
product workflow does (local processing, no account, no document upload) and
makes no claim about network access under all circumstances, because such a
claim is not proven here.

The module is text and metadata only: it imports no Qt module, opens no file and
starts no process.
"""

from __future__ import annotations

__all__ = [
    "COPYRIGHT_TEXT",
    "FACT_ACCOUNT_TEXT",
    "FACT_PROCESSING_TEXT",
    "FACT_UPLOAD_TEXT",
    "LICENSE_TEXT",
    "PRODUCT_NAME",
    "PRODUCT_TAGLINE",
    "PRODUCT_TITLE_TEXT",
    "product_title",
    "product_version",
    "version_text",
]

#: Product name.  Matches the Qt application identity declared by
#: :mod:`md_converter.gui.app` (asserted by the focused tests).
PRODUCT_NAME = "MD Converter"

#: Frozen product positioning (``V2_PRODUCT_SPEC`` §1).
PRODUCT_TAGLINE = (
    "Turn Markdown into polished Word documents \u2014 locally, privately, "
    "and without a subscription."
)

#: Bounded privacy/behaviour facts (``V2_GUI_UX_SPEC`` §15 example).
FACT_PROCESSING_TEXT = "Processing: Local, on this computer"
FACT_ACCOUNT_TEXT = "Account required: No"
FACT_UPLOAD_TEXT = "Document upload: Not required for normal conversion"

#: Authoritative copyright/licence wording, mirroring ``EULA.txt``.
COPYRIGHT_TEXT = "Copyright \u00a9 2026 Quansheng2022. All rights reserved."
LICENSE_TEXT = "Licensed under the Proprietary Single-User License (see EULA.txt)."

#: Label prefix used in front of the product name in the About surface.
PRODUCT_TITLE_TEXT = PRODUCT_NAME


def product_version() -> str:
    """Return the authoritative product version.

    The value comes from the installed project metadata
    (``md_converter.__version__``), which is the single version authority the
    packaging metadata and the release evidence already agree on.  No second
    version constant exists.

    Returns:
        str: Version string such as ``"1.1.0"``.
    """
    from md_converter import __version__

    return __version__


def version_text() -> str:
    """Return the version wording shown on the About surface.

    Returns:
        str: The version line.
    """
    return f"Version {product_version()}"


def product_title() -> str:
    """Return the product name with its authoritative version.

    Returns:
        str: Title such as ``"MD Converter 1.1.0"``.
    """
    return f"{PRODUCT_NAME} {product_version()}"
