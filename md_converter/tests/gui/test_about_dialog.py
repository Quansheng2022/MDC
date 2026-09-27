"""Focused verification for the About / Product Identity surface (WP-P12-07-03).

The About surface must state the frozen positioning, the authoritative version
and bounded local/no-account/no-upload facts, and nothing more:

* the version comes from the project's single version authority
  (``md_converter.__version__``); no second constant exists;
* the copyright/licence wording mirrors ``EULA.txt``;
* the surface is read-only, requests no network resource, starts no process and
  changes no application or Core semantics.
"""

from __future__ import annotations

import ast
import os
from pathlib import Path
from typing import TYPE_CHECKING, Iterator, List, Set

import pytest

if TYPE_CHECKING:  # pragma: no cover - typing only
    from md_converter.gui.main_window import MainWindow

pytest.importorskip("PySide6", reason="PySide6 (GUI dev dependency) is not installed")

#: Qt needs a platform plugin even when a test only constructs widgets.  Set
#: here (not in a directory ``conftest.py``) because the test tree is not a
#: package and a second ``conftest`` would shadow ``md_converter/tests/conftest.py``.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import (  # noqa: E402 - guard runs first
    QComboBox,
    QDialog,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QTextEdit,
)

from md_converter.gui import product_identity  # noqa: E402 - guard runs first
from md_converter.gui.about_dialog import AboutDialog  # noqa: E402 - guard runs first
from md_converter.gui.product_identity import (  # noqa: E402 - guard runs first
    FACT_ACCOUNT_TEXT,
    FACT_PROCESSING_TEXT,
    FACT_UPLOAD_TEXT,
    PRODUCT_NAME,
    PRODUCT_TAGLINE,
    product_title,
    product_version,
    version_text,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
GUI_DIR = PROJECT_ROOT / "md_converter" / "gui"
MAIN_WINDOW_MODULE = "md_converter.gui.main_window"

#: Modules and call targets that would mean a network or process side effect.
FORBIDDEN_IMPORT_PREFIXES = (
    "socket",
    "urllib",
    "http",
    "requests",
    "subprocess",
    "webbrowser",
    "md_converter.compiler",
    "md_converter.parser",
    "md_converter.pipeline",
    "md_converter.renderer",
    "md_converter.services",
    "md_converter.quality_gate",
)

FORBIDDEN_CALL_TARGETS = (
    "Popen",
    "urlopen",
    "openUrl",
    "system",
    "print",
    "open",
    "write_text",
    "start",
)


def _dialog() -> AboutDialog:
    """Return an About dialog with a QApplication guaranteed."""
    from md_converter.gui.app import create_application

    create_application([])
    return AboutDialog()


def _imported_modules(path: Path) -> Set[str]:
    """Return the import targets of ``path``, resolving relative imports."""
    package_parts = list(path.resolve().relative_to(PROJECT_ROOT).with_suffix("").parts)[:-1]
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                keep = len(package_parts) - (node.level - 1)
                base = ".".join(package_parts[:keep]) if keep > 0 else ""
                module = f"{base}.{module}" if module else base
            if module:
                names.add(module)
                names.update(f"{module}.{alias.name}" for alias in node.names)
    return names


def _call_targets(path: Path) -> Set[str]:
    """Return the simple names of every call target in ``path``."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            target = node.func
            if isinstance(target, ast.Name):
                names.add(target.id)
            elif isinstance(target, ast.Attribute):
                names.add(target.attr)
    return names


# ============================================================
# Product identity facts
# ============================================================


def test_version_comes_from_the_single_authority() -> None:
    """WP §"Reuse authoritative version metadata"."""
    import md_converter

    assert product_version() == md_converter.__version__
    assert version_text() == f"Version {md_converter.__version__}"


def test_product_version_matches_the_packaging_metadata() -> None:
    """The version authority agrees with ``pyproject.toml``."""
    import tomllib

    with (PROJECT_ROOT / "pyproject.toml").open("rb") as handle:
        pyproject = tomllib.load(handle)

    assert pyproject["project"]["version"] == product_version()


def test_product_name_matches_the_qt_application_identity() -> None:
    """The displayed name is the identity the GUI actually runs under."""
    from md_converter.gui.app import APPLICATION_NAME

    assert PRODUCT_NAME == APPLICATION_NAME
    assert product_title() == f"{PRODUCT_NAME} {product_version()}"


def test_positioning_matches_the_frozen_product_spec() -> None:
    """WP §"Required Positioning" - the frozen sentence is preserved."""
    spec = (PROJECT_ROOT / "Doc" / "V2" / "V2_PRODUCT_SPEC.md").read_text(encoding="utf-8")
    spec_line = (
        "Turn Markdown into polished Word documents \u2014 locally, privately, "
        "and without a subscription."
    )

    assert PRODUCT_TAGLINE == spec_line
    assert spec_line in spec


def test_privacy_facts_are_bounded() -> None:
    """WP §"Privacy Boundary": only the three provable facts are stated."""
    assert FACT_PROCESSING_TEXT == "Processing: Local, on this computer"
    assert FACT_ACCOUNT_TEXT == "Account required: No"
    assert FACT_UPLOAD_TEXT == "Document upload: Not required for normal conversion"


def test_no_unbounded_network_claim_is_made() -> None:
    """WP §"Privacy Boundary": no absolute no-network claim anywhere.

    The user-visible wording must not mention the network at all, and the source
    must not contain an absolute claim about network access.
    """
    visible = " ".join(
        (PRODUCT_TAGLINE, FACT_PROCESSING_TEXT, FACT_ACCOUNT_TEXT, FACT_UPLOAD_TEXT)
    ).lower()
    for absent in ("network", "internet", "offline", "cloud"):
        assert absent not in visible, absent

    source = "\n".join(
        (GUI_DIR / name).read_text(encoding="utf-8").lower()
        for name in ("product_identity.py", "about_dialog.py")
    )
    for claim in (
        "can never",
        "cannot access",
        "never access",
        "no network access",
        "does not use the internet",
        "never uses the internet",
        "never connects",
    ):
        assert claim not in source, claim


def test_copyright_and_license_mirror_the_eula() -> None:
    """WP §"authoritative copyright/license information"."""
    eula = (PROJECT_ROOT / "EULA.txt").read_text(encoding="utf-8")
    identity = (GUI_DIR / "product_identity.py").read_text(encoding="utf-8")

    assert "Quansheng2022" in eula
    assert "Copyright \u00a9 2026 Quansheng2022" in eula
    assert "Proprietary" in eula

    assert "Quansheng2022" in product_identity.COPYRIGHT_TEXT
    assert "2026" in product_identity.COPYRIGHT_TEXT
    assert "Proprietary" in product_identity.LICENSE_TEXT
    # The wording is declared once, in the identity module.
    assert "Quansheng2022" in identity


# ============================================================
# The dialog
# ============================================================


def test_dialog_shows_the_identity_and_positioning() -> None:
    """WP §Allowed Content: name, version, tagline and bounded facts."""
    dialog = _dialog()
    try:
        assert dialog.windowTitle() == f"About {PRODUCT_NAME}"
        assert dialog.name_label.text() == PRODUCT_NAME
        assert dialog.version_label.text() == version_text()
        assert dialog.tagline_label.text() == PRODUCT_TAGLINE
        assert dialog.processing_label.text() == FACT_PROCESSING_TEXT
        assert dialog.account_label.text() == FACT_ACCOUNT_TEXT
        assert dialog.upload_label.text() == FACT_UPLOAD_TEXT
        assert dialog.copyright_label.text() == product_identity.COPYRIGHT_TEXT
        assert dialog.license_label.text() == product_identity.LICENSE_TEXT
    finally:
        dialog.close()


def test_dialog_is_read_only() -> None:
    """WP §Tests: the surface exposes no editable control."""
    dialog = _dialog()
    try:
        for forbidden in (QComboBox, QLineEdit, QTextEdit, QPlainTextEdit):
            assert not dialog.findChildren(forbidden), forbidden.__name__
    finally:
        dialog.close()


def test_dialog_offers_only_a_close_action() -> None:
    """WP §Forbidden: no update check, licence or support action."""
    dialog = _dialog()
    try:
        buttons: List[QPushButton] = dialog.findChildren(QPushButton)
        assert buttons == [dialog.close_button]
        dialog.close_button.click()
        assert dialog.result() == int(QDialog.DialogCode.Accepted)
    finally:
        dialog.close()


def test_escape_closes_the_dialog() -> None:
    """``Esc`` dismisses the informational surface."""
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    dialog = _dialog()
    try:
        QTest.keyClick(dialog, Qt.Key.Key_Escape)
        assert dialog.result() == int(QDialog.DialogCode.Rejected)
    finally:
        dialog.close()


# ============================================================
# Main window entry point
# ============================================================


@pytest.fixture
def window(tmp_path: Path) -> Iterator["MainWindow"]:
    """Provide a main window over an isolated preference store."""
    from md_converter.gui.app import create_application
    from md_converter.gui.main_window import MainWindow
    from md_converter.gui.preferences import GuiPreferences

    create_application([])
    instance = MainWindow(preferences=GuiPreferences.for_file(tmp_path / "prefs.ini"))
    yield instance
    instance.close()


def test_about_button_opens_the_about_dialog(
    window: "MainWindow",
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The window offers exactly one About entry point."""
    import importlib

    module = importlib.import_module(MAIN_WINDOW_MODULE)
    opened: List[AboutDialog] = []

    class _RecordingAboutDialog(AboutDialog):
        def exec(self) -> int:
            opened.append(self)
            return int(QDialog.DialogCode.Accepted)

    monkeypatch.setattr(module, "AboutDialog", _RecordingAboutDialog)
    window.show()

    window.about_button.click()

    assert len(opened) == 1
    assert opened[0].parent() is window


def test_about_never_triggers_a_conversion(
    window: "MainWindow",
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """WP §Tests: opening About changes no workflow state."""
    import importlib

    module = importlib.import_module(MAIN_WINDOW_MODULE)

    def _forbidden(request) -> None:
        raise AssertionError("About must not trigger a conversion")

    monkeypatch.setattr(window.service, "convert", _forbidden)

    class _ClosableAboutDialog(AboutDialog):
        def exec(self) -> int:
            return int(self.result())

    monkeypatch.setattr(module, "AboutDialog", _ClosableAboutDialog)
    window.show()
    state_before = window.state

    window.about_button.click()

    assert window.state is state_before
    assert window.latest_result is None


# ============================================================
# Boundary
# ============================================================


def test_about_modules_have_no_network_or_process_dependency() -> None:
    """WP §Tests: no network side effect and no process launch."""
    for name in ("about_dialog.py", "product_identity.py"):
        module = GUI_DIR / name
        offenders = {
            imported
            for imported in _imported_modules(module)
            if imported.startswith(FORBIDDEN_IMPORT_PREFIXES)
        }
        assert not offenders, f"{name} imports {sorted(offenders)}"

        calls = _call_targets(module) & set(FORBIDDEN_CALL_TARGETS)
        assert not calls, f"{name} calls {sorted(calls)}"
