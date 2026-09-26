"""Focused verification for the GUI state model (WP-P12-04-03 §9).

Two layers are verified:

* the state machine itself (``md_converter.gui.state``, Qt-free): initial state,
  every required transition, and deterministic rejection of invalid ones;
* the window binding: widget enablement, source visibility and status text are
  derived from the state through the single ``_apply_state`` path.

``CONVERTING`` completions are driven by the mocked ``simulate_*`` hooks; real
conversion integration is not authorized in P12-04.
"""

from __future__ import annotations

import ast
import os
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Set, Tuple

import pytest

if TYPE_CHECKING:  # pragma: no cover - typing only
    from md_converter.gui.main_window import MainWindow

pytest.importorskip("PySide6", reason="PySide6 (GUI dev dependency) is not installed")

#: Qt needs a platform plugin even when a test only constructs widgets.  Set
#: here (not in a directory ``conftest.py``) because the test tree is not a
#: package and a second ``conftest`` would shadow ``md_converter/tests/conftest.py``.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from md_converter.gui.state import (  # noqa: E402 - the Qt guard must run first
    STATE_EFFECTS,
    STATUS_CONVERTING,
    STATUS_EMPTY,
    GuiState,
    GuiStateModel,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
GUI_DIR = PROJECT_ROOT / "md_converter" / "gui"

#: Completion state -> (state-model method, window mock hook).
_COMPLETIONS: Dict[GuiState, Tuple[str, str]] = {
    GuiState.SUCCESS: ("complete_success", "simulate_success"),
    GuiState.SUCCESS_WITH_WARNING: ("complete_warning", "simulate_warning"),
    GuiState.FAILED: ("complete_failure", "simulate_failure"),
}

#: Worker/threading machinery must not appear in P12-04 GUI code.
_THREAD_TOKENS = (
    "QThread",
    "QThreadPool",
    "QtConcurrent",
    "QRunnable",
    "concurrent.futures",
    "threading",
)


def _make_window() -> "MainWindow":
    """Return a fresh ``MainWindow``, ensuring a QApplication exists."""
    from md_converter.gui.app import create_application
    from md_converter.gui.main_window import MainWindow

    create_application([])
    return MainWindow()


def _process_events() -> None:
    """Deliver pending Qt events (layout/visibility) without entering the loop."""
    from PySide6.QtWidgets import QApplication

    QApplication.instance().processEvents()


def _drive(window: "MainWindow", state: GuiState) -> None:
    """Drive ``window`` into ``state`` through the public transitions."""
    if state is GuiState.EMPTY:
        return
    window.set_source("notes.md")
    if state is GuiState.READY:
        return
    window.request_convert()
    if state is GuiState.CONVERTING:
        return
    getattr(window, _COMPLETIONS[state][1])()


def _imported_modules(path: Path) -> Set[str]:
    """Return the module names imported by ``path``."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module:
                names.add(module)
            names.update(f"{module}.{alias.name}".lstrip(".") for alias in node.names)
    return names


# ============================================================
# State machine
# ============================================================


def test_initial_state_is_empty() -> None:
    """§9: a fresh model starts in EMPTY with no source selected."""
    model = GuiStateModel()

    assert model.state is GuiState.EMPTY
    assert model.source is None
    assert model.effect is STATE_EFFECTS[GuiState.EMPTY]


def test_valid_source_moves_to_ready() -> None:
    """§4: EMPTY -> READY when a valid source is available."""
    model = GuiStateModel()

    assert model.set_source("notes.md") is GuiState.READY
    assert model.source == "notes.md"


def test_model_may_start_ready_with_source() -> None:
    """An explicit initial source starts the model in READY."""
    assert GuiStateModel("notes.md").state is GuiState.READY


def test_blank_source_clears_selection() -> None:
    """A blank source is not a valid selection."""
    model = GuiStateModel("notes.md")

    assert model.set_source("   ") is GuiState.EMPTY
    assert model.source is None


def test_reset_returns_to_empty() -> None:
    """READY -> EMPTY on reset."""
    model = GuiStateModel("notes.md")

    assert model.reset() is GuiState.EMPTY
    assert model.source is None


def test_ready_to_converting() -> None:
    """§4: READY -> CONVERTING when conversion is requested."""
    model = GuiStateModel("notes.md")

    assert model.request_convert() is GuiState.CONVERTING


def test_convert_request_is_rejected_when_not_ready() -> None:
    """An invalid transition leaves the state unchanged."""
    model = GuiStateModel()

    assert model.request_convert() is GuiState.EMPTY


def test_duplicate_convert_is_rejected_while_converting() -> None:
    """§9: duplicate convert starts are prevented."""
    model = GuiStateModel("notes.md")
    model.request_convert()

    assert model.request_convert() is GuiState.CONVERTING


@pytest.mark.parametrize("completion", list(_COMPLETIONS))
def test_converting_completions(completion: GuiState) -> None:
    """§4: CONVERTING -> SUCCESS / SUCCESS_WITH_WARNING / FAILED."""
    model = GuiStateModel("notes.md")
    model.request_convert()

    assert getattr(model, _COMPLETIONS[completion][0])() is completion


@pytest.mark.parametrize("completion", list(_COMPLETIONS))
def test_completion_requires_converting(completion: GuiState) -> None:
    """Completion transitions from a non-CONVERTING state are rejected."""
    model = GuiStateModel("notes.md")

    assert getattr(model, _COMPLETIONS[completion][0])() is GuiState.READY


@pytest.mark.parametrize("completion", list(_COMPLETIONS))
def test_new_source_after_completion_returns_to_ready(completion: GuiState) -> None:
    """§4: completion + new valid source -> READY."""
    model = GuiStateModel("notes.md")
    model.request_convert()
    getattr(model, _COMPLETIONS[completion][0])()

    assert model.set_source("other.md") is GuiState.READY
    assert model.source == "other.md"


@pytest.mark.parametrize("completion", list(_COMPLETIONS))
def test_reset_after_completion_returns_to_empty(completion: GuiState) -> None:
    """§4: completion + reset -> EMPTY."""
    model = GuiStateModel("notes.md")
    model.request_convert()
    getattr(model, _COMPLETIONS[completion][0])()

    assert model.reset() is GuiState.EMPTY
    assert model.source is None


def test_source_change_during_converting_is_ignored() -> None:
    """An in-flight conversion cannot be switched underneath the user."""
    model = GuiStateModel("notes.md")
    model.request_convert()

    assert model.set_source("other.md") is GuiState.CONVERTING
    assert model.source == "notes.md"


def test_reset_during_converting_is_ignored() -> None:
    """Resetting during conversion is rejected deterministically."""
    model = GuiStateModel("notes.md")
    model.request_convert()

    assert model.reset() is GuiState.CONVERTING
    assert model.source == "notes.md"


# ============================================================
# State effects (§6)
# ============================================================


def test_effects_cover_every_state() -> None:
    """Every GUI state has exactly one declared effect."""
    assert set(STATE_EFFECTS) == set(GuiState)


def test_required_state_effects() -> None:
    """§6: EMPTY and READY effects match the required behavior."""
    empty = STATE_EFFECTS[GuiState.EMPTY]
    assert (empty.convert_enabled, empty.select_enabled, empty.drop_enabled) == (
        False,
        True,
        True,
    )
    assert empty.source_visible is False

    ready = STATE_EFFECTS[GuiState.READY]
    assert ready.convert_enabled is True
    assert ready.source_visible is True

    converting = STATE_EFFECTS[GuiState.CONVERTING]
    assert converting.convert_enabled is False
    assert converting.status_text == STATUS_CONVERTING

    statuses = {state: STATE_EFFECTS[state].status_text for state in GuiState}
    assert all(text.strip() for text in statuses.values())
    assert len(set(statuses.values())) == len(GuiState)
    assert statuses[GuiState.EMPTY] == STATUS_EMPTY
    assert statuses[GuiState.SUCCESS] != statuses[GuiState.SUCCESS_WITH_WARNING]


# ============================================================
# Window binding
# ============================================================


def test_window_starts_in_empty_state() -> None:
    """§9: the window starts EMPTY with Convert unavailable."""
    window = _make_window()
    try:
        assert window.state is GuiState.EMPTY
        assert window.convert_button.isEnabled() is False
        assert window.select_file_button.isEnabled() is True
        assert window.drop_zone.isEnabled() is True
        assert window.status_label.text() == STATUS_EMPTY

        window.show()
        _process_events()
        assert window.source_label.isVisible() is False
    finally:
        window.close()


def test_window_ready_state_shows_source_and_enables_convert() -> None:
    """§6: READY enables Convert and makes the source visible."""
    window = _make_window()
    try:
        assert window.set_source("notes.md") is GuiState.READY
        window.show()
        _process_events()

        assert window.convert_button.isEnabled() is True
        assert window.source_label.isVisible() is True
        assert window.source_label.text() == "notes.md"
        assert window.status_label.text() == STATE_EFFECTS[GuiState.READY].status_text
    finally:
        window.close()


def test_window_converting_disables_convert_and_input() -> None:
    """§6: CONVERTING disables Convert, restricts input and shows progress."""
    window = _make_window()
    try:
        window.set_source("notes.md")
        assert window.request_convert() is GuiState.CONVERTING

        assert window.convert_button.isEnabled() is False
        assert window.select_file_button.isEnabled() is False
        assert window.drop_zone.isEnabled() is False
        assert window.status_label.text() == STATUS_CONVERTING
    finally:
        window.close()


def test_window_duplicate_convert_is_prevented() -> None:
    """§9: repeated Convert requests during CONVERTING are ignored."""
    window = _make_window()
    try:
        window.set_source("notes.md")
        window.request_convert()

        assert window.request_convert() is GuiState.CONVERTING
        assert window.state is GuiState.CONVERTING
    finally:
        window.close()


@pytest.mark.parametrize("state", list(GuiState))
def test_widget_state_derives_from_gui_state(state: GuiState) -> None:
    """§7/§10: widget state is derived from the state model, not patched ad hoc."""
    window = _make_window()
    try:
        window.show()
        _process_events()
        _drive(window, state)

        effect = STATE_EFFECTS[state]
        assert window.state is state
        assert window.convert_button.isEnabled() is effect.convert_enabled
        assert window.select_file_button.isEnabled() is effect.select_enabled
        assert window.drop_zone.isEnabled() is effect.drop_enabled
        assert window.source_label.isVisible() is effect.source_visible
        assert window.status_label.text() == effect.status_text
    finally:
        window.close()


@pytest.mark.parametrize("completion", list(_COMPLETIONS))
def test_window_completion_then_new_source_returns_to_ready(completion: GuiState) -> None:
    """§4: after a completion state, a new source returns the window to READY."""
    window = _make_window()
    try:
        window.set_source("notes.md")
        window.request_convert()
        assert getattr(window, _COMPLETIONS[completion][1])() is completion

        assert window.set_source("other.md") is GuiState.READY
        assert window.source_label.text() == "other.md"
        assert window.convert_button.isEnabled() is True
    finally:
        window.close()


def test_window_reset_returns_to_empty() -> None:
    """Reset clears the source and returns the window to EMPTY."""
    window = _make_window()
    try:
        window.set_source("notes.md")

        assert window.reset() is GuiState.EMPTY
        assert window.source_label.text() == ""
        assert window.convert_button.isEnabled() is False
        assert window.status_label.text() == STATUS_EMPTY
    finally:
        window.close()


# ============================================================
# Scope guards
# ============================================================


def test_gui_layer_has_no_threading_or_worker_code() -> None:
    """No worker/thread machinery is introduced (P12-04 scope)."""
    modules = sorted(GUI_DIR.glob("*.py"))

    assert modules
    for module in modules:
        text = module.read_text(encoding="utf-8")
        for token in _THREAD_TOKENS:
            assert token not in text, f"{module.name}: {token}"


def test_state_module_is_qt_free() -> None:
    """The GUI state model is pure Python and stays out of the Core layer."""
    imported = _imported_modules(GUI_DIR / "state.py")
    gui_prefixes = ("PySide6", "PyQt5", "PyQt6")

    assert not [name for name in imported if name.startswith(gui_prefixes)]
