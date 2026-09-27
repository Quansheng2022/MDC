"""Focused verification for the post-conversion output actions (WP-P12-06-05).

``Open Document`` and ``Open Folder`` must act on the retained
``ConversionResult.output_path`` verbatim, be offered only for a successful
outcome whose artifact exists, fail safely when the artifact is gone, and never
trigger another conversion.

External OS launching is mocked in every automated test; a bounded real Windows
smoke is performed separately (see the WP report).
"""

from __future__ import annotations

import ast
import importlib
import os
import time
from pathlib import Path
from typing import TYPE_CHECKING, Callable, List, Set

import pytest

from md_converter.application.conversion_result import (
    ConversionErrorCategory,
    ConversionResult,
    ConversionStatus,
)

if TYPE_CHECKING:  # pragma: no cover - typing only
    from md_converter.gui.main_window import MainWindow

pytest.importorskip("PySide6", reason="PySide6 (GUI dev dependency) is not installed")

#: Qt needs a platform plugin even when a test only constructs widgets.  Set
#: here (not in a directory ``conftest.py``) because the test tree is not a
#: package and a second ``conftest`` would shadow ``md_converter/tests/conftest.py``.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from md_converter.gui.state import GuiState  # noqa: E402 - the guard runs first

PROJECT_ROOT = Path(__file__).resolve().parents[3]
GUI_DIR = PROJECT_ROOT / "md_converter" / "gui"
MAIN_WINDOW_MODULE = "md_converter.gui.main_window"
OUTPUT_ACTIONS_MODULE = "md_converter.gui.output_actions"

#: Core modules the GUI must never import directly (WP-P12-05-03 boundary).
FORBIDDEN_IMPORT_PREFIXES = (
    "md_converter.compiler",
    "md_converter.diagnostics",
    "md_converter.parser",
    "md_converter.pipeline",
    "md_converter.renderer",
    "md_converter.services",
    "md_converter.quality_gate",
)

#: Tokens that would indicate GUI-side output naming or path derivation.
FORBIDDEN_PATH_TOKENS = (
    ".docx",
    "sanitize",
    "with_suffix",
    "with_name",
    ".stem",
    "subprocess",
    "shell",
)


def _pump() -> None:
    """Deliver pending Qt events."""
    from PySide6.QtWidgets import QApplication

    QApplication.processEvents()


def _wait_until(predicate: Callable[[], bool], timeout_ms: int = 20000) -> bool:
    """Process GUI events until ``predicate`` holds, or the timeout expires."""
    deadline = time.monotonic() + timeout_ms / 1000.0
    while time.monotonic() < deadline:
        _pump()
        if predicate():
            return True
        time.sleep(0.005)
    return predicate()


def _write_markdown(path: Path, body: str = "# Notes\n\nBody text.\n") -> Path:
    """Write ``body`` as UTF-8 Markdown and return the path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


@pytest.fixture
def window(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> "MainWindow":
    """Provide a window with a deterministic service, idle again at teardown."""
    from md_converter.application.conversion_service import ConversionService
    from md_converter.gui.app import create_application
    from md_converter.gui.main_window import MainWindow

    monkeypatch.chdir(tmp_path)
    create_application([])

    instance = MainWindow()
    instance.service = ConversionService({"word_com": False})
    yield instance

    assert _wait_until(lambda: not instance.worker.is_running), "worker did not stop"
    instance.close()
    _pump()


def _run_conversion(window: "MainWindow", source: Path) -> None:
    """Run one real conversion through the window and wait for completion."""
    assert window.set_source_file(str(source)) is GuiState.READY
    window.start_conversion()
    assert _wait_until(
        lambda: window.state is not GuiState.CONVERTING and not window.worker.is_running
    )


def _success_conversion(window: "MainWindow", tmp_path: Path) -> Path:
    """Run a successful conversion and return the produced artifact path."""
    source = _write_markdown(tmp_path / "notes.md")
    _run_conversion(window, source)
    assert window.state is GuiState.SUCCESS
    assert window.latest_result is not None
    artifact = window.latest_result.output_path
    assert artifact is not None and artifact.exists()
    return artifact


def _spy_on_launcher(monkeypatch: pytest.MonkeyPatch, name: str) -> List[Path]:
    """Record calls to one launcher used by ``MainWindow``."""
    module = importlib.import_module(MAIN_WINDOW_MODULE)
    calls: List[Path] = []

    def recording(path: Path) -> bool:
        calls.append(path)
        return True

    monkeypatch.setattr(module, name, recording)
    return calls


def _spy_on_notify(monkeypatch: pytest.MonkeyPatch) -> List[object]:
    """Record missing-artifact notifications instead of showing a modal box."""
    module = importlib.import_module(MAIN_WINDOW_MODULE)
    calls: List[object] = []

    def recording(parent, path):
        calls.append(path)

    monkeypatch.setattr(module, "notify_missing_artifact", recording)
    return calls


def _spy_on_service(window: "MainWindow", monkeypatch: pytest.MonkeyPatch) -> List[object]:
    """Record real ``service.convert`` calls."""
    calls: List[object] = []
    original = window.service.convert

    def recording(request):
        calls.append(request)
        return original(request)

    monkeypatch.setattr(window.service, "convert", recording)
    return calls


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


def _code_tokens(path: Path) -> Set[str]:
    """Return the identifiers and non-docstring string literals of ``path``."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)):
            docstring = ast.get_docstring(node, clean=False)
            if docstring:
                docstrings.add(docstring)

    tokens: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            tokens.add(node.id)
        elif isinstance(node, ast.Attribute):
            tokens.add(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value not in docstrings:
                tokens.add(node.value)
    return tokens


def _buttons(window: "MainWindow") -> tuple:
    """Return the two output-action buttons."""
    return (window.open_document_button, window.open_folder_button)


# ============================================================
# Eligibility
# ============================================================


def test_success_with_artifact_enables_both_actions(window: "MainWindow", tmp_path: Path) -> None:
    """WP §1: SUCCESS with an existing artifact offers both actions."""
    _success_conversion(window, tmp_path)
    window.show()
    _pump()

    assert window.presentation is not None
    assert window.presentation.output_actionable is True
    for button in _buttons(window):
        assert button.isVisible() is True
        assert button.isEnabled() is True


def test_success_with_warning_enables_both_actions(window: "MainWindow", tmp_path: Path) -> None:
    """WP §2/§11: warnings keep the artifact actionable and the outcome successful."""
    source = _write_markdown(tmp_path / "warn.md", body="#\n\nSome body text.\n")
    _run_conversion(window, source)
    window.show()
    _pump()

    assert window.state is GuiState.SUCCESS_WITH_WARNING
    assert window.presentation is not None
    assert window.presentation.is_success is True
    assert window.presentation.output_actionable is True
    for button in _buttons(window):
        assert button.isVisible() is True
        assert button.isEnabled() is True


def test_failed_result_disables_actions(window: "MainWindow", tmp_path: Path) -> None:
    """WP §3: a failure without a valid artifact disables both actions."""
    source = _write_markdown(tmp_path / "empty.md", body="")
    _run_conversion(window, source)
    window.show()
    _pump()

    assert window.state is GuiState.FAILED
    assert window.presentation is not None
    assert window.presentation.output_actionable is False
    for button in _buttons(window):
        assert button.isVisible() is False
        assert button.isEnabled() is False
    assert window.open_output_document() is False
    assert window.open_output_folder() is False


def test_failed_result_with_an_artifact_still_disables_actions(
    window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WP §"Failed/JobFailure": a FAILED artifact is never assumed valid."""
    artifact = tmp_path / "partial.docx"
    artifact.write_bytes(b"placeholder")
    failed = ConversionResult(
        status=ConversionStatus.FAILED,
        output_path=artifact,
        error_category=ConversionErrorCategory.CONVERSION_ERROR,
        error_message="The document conversion failed.",
    )
    monkeypatch.setattr(window.service, "convert", lambda request: failed)
    source = _write_markdown(tmp_path / "notes.md")
    document_calls = _spy_on_launcher(monkeypatch, "open_document")
    folder_calls = _spy_on_launcher(monkeypatch, "open_folder")

    _run_conversion(window, source)
    window.show()
    _pump()

    assert window.state is GuiState.FAILED
    assert window.presentation is not None
    assert window.presentation.output_path == artifact
    assert window.presentation.output_actionable is False
    for button in _buttons(window):
        assert button.isVisible() is False
        assert button.isEnabled() is False
    assert window.open_output_document() is False
    assert window.open_output_folder() is False
    assert document_calls == [] and folder_calls == []


def test_job_failure_disables_actions(
    window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WP §4: worker infrastructure failure disables both actions."""
    source = _write_markdown(tmp_path / "notes.md")

    def exploding(request) -> ConversionResult:
        raise RuntimeError("service exploded")

    monkeypatch.setattr(window.service, "convert", exploding)
    _run_conversion(window, source)
    window.show()
    _pump()

    assert window.state is GuiState.FAILED
    assert window.presentation is not None
    assert window.presentation.is_infrastructure_failure is True
    assert window.presentation.output_actionable is False
    for button in _buttons(window):
        assert button.isVisible() is False
        assert button.isEnabled() is False
    assert window.open_output_document() is False
    assert window.open_output_folder() is False


# ============================================================
# Path authority
# ============================================================


def test_open_document_uses_the_retained_path_exactly(
    window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WP §5: Open Document receives the retained ``output_path`` unchanged."""
    artifact = _success_conversion(window, tmp_path)
    calls = _spy_on_launcher(monkeypatch, "open_document")
    window.show()
    _pump()

    window.open_document_button.click()
    _pump()

    assert window.latest_result is not None
    assert calls and calls[0] is window.latest_result.output_path
    assert calls[0] == artifact


def test_open_folder_uses_the_retained_path_exactly(
    window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WP §6: Open Folder receives the retained ``output_path`` unchanged."""
    artifact = _success_conversion(window, tmp_path)
    calls = _spy_on_launcher(monkeypatch, "open_folder")
    window.show()
    _pump()

    window.open_folder_button.click()
    _pump()

    assert window.latest_result is not None
    assert calls and calls[0] is window.latest_result.output_path
    assert calls[0].parent == artifact.parent


def test_no_filename_or_path_recomputation() -> None:
    """WP §7: no GUI-side output naming or path construction exists."""
    for module in (GUI_DIR / "main_window.py", GUI_DIR / "output_actions.py"):
        for token in _code_tokens(module):
            for forbidden in FORBIDDEN_PATH_TOKENS:
                assert forbidden not in token, f"{module.name}: {forbidden} in {token!r}"

    # The single path source is the retained result field.
    main_window_text = (GUI_DIR / "main_window.py").read_text(encoding="utf-8")
    assert "return result.output_path" in main_window_text


def test_launchers_receive_the_retained_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WP §5/§6: the platform helpers use the artifact and its folder verbatim."""
    from md_converter.gui import output_actions

    opened: List[str] = []

    class _DesktopServices:
        @staticmethod
        def openUrl(url) -> bool:  # noqa: N802 - Qt API name
            opened.append(url.toLocalFile())
            return True

    monkeypatch.setattr(output_actions, "QDesktopServices", _DesktopServices)
    artifact = tmp_path / "exported.docx"
    artifact.write_bytes(b"placeholder")

    assert output_actions.open_document(artifact) is True
    assert output_actions.open_folder(artifact) is True
    assert [Path(item) for item in opened] == [artifact, tmp_path]


def test_launchers_fail_closed_for_missing_targets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WP §8: missing paths fail safely without opening anything."""
    from md_converter.gui import output_actions

    opened: List[str] = []

    class _DesktopServices:
        @staticmethod
        def openUrl(url) -> bool:  # noqa: N802 - Qt API name
            opened.append(url.toLocalFile())
            return True

    monkeypatch.setattr(output_actions, "QDesktopServices", _DesktopServices)
    missing = tmp_path / "gone.docx"

    assert output_actions.resolve_artifact(None) is None
    assert output_actions.resolve_artifact(missing) is None
    assert output_actions.open_document(None) is False
    assert output_actions.open_document(missing) is False
    assert output_actions.open_folder(missing) is False
    assert opened == []


# ============================================================
# Missing artifact at click time
# ============================================================


def test_missing_artifact_at_click_time_is_safe(
    window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WP §8: a deleted artifact fails safely with a concise message.

    The real launchers run here (the artifact is gone, so they must fail
    closed); only the OS launch call and the modal message are stubbed.
    """
    from md_converter.gui import output_actions

    artifact = _success_conversion(window, tmp_path)
    notifications = _spy_on_notify(monkeypatch)
    opened: List[str] = []

    class _DesktopServices:
        @staticmethod
        def openUrl(url) -> bool:  # noqa: N802 - Qt API name
            opened.append(url.toLocalFile())
            return True

    monkeypatch.setattr(output_actions, "QDesktopServices", _DesktopServices)
    window.show()
    _pump()

    artifact.unlink()

    assert window.open_output_document() is False
    assert window.open_output_folder() is False
    assert opened == []
    assert notifications == [artifact, artifact]
    # No path substitution: the retained evidence still names the same artifact.
    assert window.latest_result is not None
    assert window.latest_result.output_path == artifact


def test_actions_never_trigger_a_conversion(
    window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WP §9: the actions never start another conversion."""
    calls = _spy_on_service(window, monkeypatch)
    _success_conversion(window, tmp_path)
    assert len(calls) == 1
    _spy_on_launcher(monkeypatch, "open_document")
    _spy_on_launcher(monkeypatch, "open_folder")
    window.show()
    _pump()

    window.open_document_button.click()
    window.open_folder_button.click()
    window.open_output_document()
    window.open_output_folder()
    _pump()

    assert len(calls) == 1
    assert window.worker.is_running is False
    assert window.state is GuiState.SUCCESS


def test_actions_do_not_mutate_the_retained_result(
    window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WP §10: the retained result is byte-for-byte unchanged after acting."""
    _success_conversion(window, tmp_path)
    result = window.latest_result
    assert result is not None
    before = result.to_dict()
    _spy_on_launcher(monkeypatch, "open_document")
    _spy_on_launcher(monkeypatch, "open_folder")

    window.open_output_document()
    window.open_output_folder()
    _pump()

    assert window.latest_result is result
    assert result.to_dict() == before


def test_actions_are_unavailable_before_any_conversion(window: "MainWindow") -> None:
    """No artifact means no action, in the initial workflow state."""
    assert window.presentation is None
    assert window.open_output_document() is False
    assert window.open_output_folder() is False
    for button in _buttons(window):
        assert button.isVisible() is False
        assert button.isEnabled() is False


def test_new_workflow_clears_the_actions(window: "MainWindow", tmp_path: Path) -> None:
    """The actions follow the existing state flow: a new source clears them."""
    _success_conversion(window, tmp_path)
    window.show()
    _pump()
    assert window.open_document_button.isVisible() is True

    other = _write_markdown(tmp_path / "other.md")
    assert window.set_source_file(str(other)) is GuiState.READY
    _pump()

    assert window.open_document_button.isVisible() is False
    assert window.open_document_button.isEnabled() is False


# ============================================================
# Architecture guards
# ============================================================


def test_output_actions_add_no_core_import() -> None:
    """WP §12: the GUI still reaches the Core only through the application layer."""
    for module in (GUI_DIR / "main_window.py", GUI_DIR / "output_actions.py"):
        offenders = {
            name for name in _imported_modules(module) if name.startswith(FORBIDDEN_IMPORT_PREFIXES)
        }
        assert not offenders, f"{module.name} imports {sorted(offenders)}"
