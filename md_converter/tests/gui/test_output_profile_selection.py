"""Focused verification for output-profile selection (Program C, WP-POP-03/05).

Covers the smallest compatible UX (one labelled combo box beside the existing
conversion controls), the existing settings store as the only persistence
mechanism, the safe fallback for a stale stored identifier, the single-file and
batch application of one profile, and the accessibility baseline.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Iterator, List, Optional

import pytest

from md_converter.application.conversion_request import ConversionRequest
from md_converter.application.conversion_result import ConversionResult, ConversionStatus
from md_converter.profiles import DEFAULT_PROFILE_ID, profile_choices, profile_ids

if TYPE_CHECKING:  # pragma: no cover - typing only
    from md_converter.gui.main_window import MainWindow

pytest.importorskip("PySide6", reason="PySide6 (GUI dev dependency) is not installed")

#: Qt needs a platform plugin even when a test only constructs widgets.  Set
#: here (not in a directory ``conftest.py``) because the test tree is not a
#: package and a second ``conftest`` would shadow ``md_converter/tests/conftest.py``.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt  # noqa: E402 - guard runs first
from PySide6.QtWidgets import QApplication, QComboBox, QLabel, QWidget  # noqa: E402

from md_converter.gui.main_window import (  # noqa: E402 - guard runs first
    OUTPUT_PROFILE_ACCESSIBLE_NAME,
    OUTPUT_PROFILE_CAPTION_TEXT,
    OUTPUT_PROFILE_TOOLTIP,
    MainWindow,
)
from md_converter.gui.preferences import (  # noqa: E402 - guard runs first
    GUI_SETTING_KEYS,
    OUTPUT_PROFILE_KEY,
    GuiPreferences,
)
from md_converter.gui.request_builder import (  # noqa: E402 - guard runs first
    OUTPUT_DIR_CONFIG_KEY,
    OUTPUT_PROFILE_CONFIG_KEY,
)
from md_converter.gui.state import GuiState  # noqa: E402 - guard runs first

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MAIN_WINDOW_MODULE = PROJECT_ROOT / "md_converter" / "gui" / "main_window.py"

#: The non-default profile used as the "explicit divergence" under test.
SECOND_PROFILE_ID = profile_ids()[1]
THIRD_PROFILE_ID = profile_ids()[3]


def _store(tmp_path: Path) -> GuiPreferences:
    """Return one isolated file-backed preference store."""
    return GuiPreferences.for_file(tmp_path / "gui_preferences.ini")


def _window(preferences: Optional[GuiPreferences] = None) -> "MainWindow":
    """Return a fresh window, ensuring a QApplication exists."""
    from md_converter.application.conversion_service import ConversionService
    from md_converter.gui.app import create_application

    create_application([])
    instance = MainWindow(preferences=preferences) if preferences is not None else MainWindow()
    # Deterministic configuration: never depend on optional Word automation.
    instance.service = ConversionService({"word_com": False})
    return instance


def _pump() -> None:
    """Deliver pending Qt events."""
    QApplication.instance().processEvents()


def _markdown(tmp_path: Path, name: str = "notes.md") -> Path:
    """Write a minimal Markdown source and return its path."""
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# Notes\n\nBody text.\n", encoding="utf-8")
    return path


def _wait_until(predicate: Callable[[], bool], timeout: float = 60.0) -> bool:
    """Process events until ``predicate`` holds or the timeout expires."""
    import time

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        _pump()
        if predicate():
            return True
        time.sleep(0.005)
    return predicate()


def _profile_key_is_absent(tmp_path: Path) -> bool:
    """Return whether the profile key is absent from the isolated store."""
    from PySide6.QtCore import QSettings

    settings = QSettings(str(tmp_path / "gui_preferences.ini"), QSettings.Format.IniFormat)
    settings.sync()
    return settings.value(OUTPUT_PROFILE_KEY, None) is None


def _spy_on_service(window: "MainWindow", monkeypatch: pytest.MonkeyPatch) -> List[dict]:
    """Record every ``service.convert`` request while still performing it."""
    calls: List[dict] = []
    original = window.service.convert

    def recording(request: ConversionRequest) -> ConversionResult:
        calls.append({"request": request})
        return original(request)

    monkeypatch.setattr(window.service, "convert", recording)
    return calls


@pytest.fixture
def window(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator["MainWindow"]:
    """Provide a window over an isolated store, idle at teardown, in a temp cwd.

    The working directory is moved to the test's temporary directory so the
    service's default output location resolves inside it: a test never writes
    conversion artifacts into the repository (same rule as the accepted real
    conversion slice).
    """
    monkeypatch.chdir(tmp_path)
    instance = _window(_store(tmp_path))
    yield instance
    _wait_until(lambda: not instance.worker.is_running, timeout=30.0)
    instance.close()
    _pump()


# ============================================================
# Selection surface
# ============================================================


def test_selector_is_present_and_plainly_labelled(window: "MainWindow") -> None:
    """The control is visible next to the conversion controls with clear wording."""
    caption = window.findChild(QWidget, "outputProfileCaptionLabel")
    combo = window.findChild(QComboBox, "outputProfileCombo")

    assert caption is not None and isinstance(caption, QLabel)
    assert caption.text() == OUTPUT_PROFILE_CAPTION_TEXT
    assert combo is window.profile_combo
    assert combo.toolTip() == OUTPUT_PROFILE_TOOLTIP
    assert combo.accessibleName() == OUTPUT_PROFILE_ACCESSIBLE_NAME
    assert combo.accessibleName().strip()

    wordings = (
        OUTPUT_PROFILE_CAPTION_TEXT,
        OUTPUT_PROFILE_TOOLTIP,
        OUTPUT_PROFILE_ACCESSIBLE_NAME,
    )
    for text in wordings:
        for jargon in ("--", "AST", "QA", "CompilerContext", "ConversionService"):
            assert jargon not in text


def test_selector_lists_every_supported_profile_in_order(window: "MainWindow") -> None:
    """Only supported profiles appear, in the frozen presentation order."""
    combo = window.profile_combo
    choices = profile_choices()

    assert combo.count() == len(choices)
    for index, (identifier, display_name) in enumerate(choices):
        assert combo.itemText(index) == display_name
        assert combo.itemData(index) == identifier
        assert combo.itemData(index, Qt.ItemDataRole.ToolTipRole)


def test_default_selection_is_the_default_profile(window: "MainWindow") -> None:
    """A fresh window selects the product default (product specification 7)."""
    assert window.output_profile == DEFAULT_PROFILE_ID
    assert window.profile_combo.currentData() == DEFAULT_PROFILE_ID


def test_opening_the_window_writes_no_preference(tmp_path: Path) -> None:
    """Construction is side-effect free; only an explicit choice is stored."""
    preferences = _store(tmp_path)
    instance = _window(preferences)
    try:
        assert preferences.output_profile is None
        assert _profile_key_is_absent(tmp_path)
    finally:
        instance.close()


# ============================================================
# Selection, persistence and safe fallback
# ============================================================


def test_selection_is_remembered_and_restored(tmp_path: Path) -> None:
    """The last-used profile survives a restart through the existing store."""
    preferences = _store(tmp_path)
    instance = _window(preferences)
    try:
        index = instance.profile_combo.findData(SECOND_PROFILE_ID)
        assert instance.set_output_profile(SECOND_PROFILE_ID) == SECOND_PROFILE_ID
        assert instance.profile_combo.currentIndex() == index
    finally:
        instance.close()

    assert preferences.output_profile == SECOND_PROFILE_ID
    reopened = _window(_store(tmp_path))
    try:
        assert reopened.output_profile == SECOND_PROFILE_ID
        assert reopened.profile_combo.currentData() == SECOND_PROFILE_ID
    finally:
        reopened.close()


def test_combo_change_is_what_persists_the_choice(tmp_path: Path) -> None:
    """A user selection in the selector is the writer of the preference."""
    preferences = _store(tmp_path)
    instance = _window(preferences)
    try:
        instance.profile_combo.setCurrentIndex(instance.profile_combo.findData(THIRD_PROFILE_ID))
        assert instance.output_profile == THIRD_PROFILE_ID
    finally:
        instance.close()

    assert preferences.output_profile == THIRD_PROFILE_ID


def test_unknown_stored_identifier_falls_back_safely(tmp_path: Path) -> None:
    """Product specification 10: a stale stored value never breaks the window."""
    preferences = _store(tmp_path)
    preferences.set_output_profile("retired-profile")

    instance = _window(preferences)
    try:
        assert instance.output_profile == DEFAULT_PROFILE_ID
        assert instance.profile_combo.currentData() == DEFAULT_PROFILE_ID
    finally:
        instance.close()


@pytest.mark.parametrize("stored", ["", "   "])
def test_blank_stored_identifier_uses_the_default(tmp_path: Path, stored: str) -> None:
    """A blank stored value is treated as "no preference"."""
    preferences = _store(tmp_path)
    preferences.set_output_profile(stored)

    assert preferences.output_profile is None
    instance = _window(preferences)
    try:
        assert instance.output_profile == DEFAULT_PROFILE_ID
    finally:
        instance.close()


def test_unknown_selection_is_refused(window: "MainWindow") -> None:
    """An unknown identifier never replaces the current selection."""
    assert window.output_profile == DEFAULT_PROFILE_ID

    assert window.set_output_profile("not-a-profile") == DEFAULT_PROFILE_ID
    assert window.set_output_profile(None) == DEFAULT_PROFILE_ID
    assert window.profile_combo.currentData() == DEFAULT_PROFILE_ID


def test_reset_keeps_the_profile_preference(window: "MainWindow") -> None:
    """Clearing the selection is not a preference change."""
    window.set_source("notes.md")
    window.set_output_profile(SECOND_PROFILE_ID)

    assert window.reset() is GuiState.EMPTY
    assert window.output_profile == SECOND_PROFILE_ID
    assert window.profile_combo.currentData() == SECOND_PROFILE_ID


def test_settings_reset_clears_the_profile_preference(tmp_path: Path) -> None:
    """The profile identifier is one of the declared GUI-owned keys."""
    preferences = _store(tmp_path)
    preferences.set_output_profile(SECOND_PROFILE_ID)

    assert OUTPUT_PROFILE_KEY in GUI_SETTING_KEYS
    preferences.reset()

    assert preferences.output_profile is None


# ============================================================
# Locking during a conversion / batch
# ============================================================


def test_selector_is_locked_while_converting(window: "MainWindow") -> None:
    """A running conversion cannot have its presentation changed underneath it."""
    window.set_source("notes.md")
    window.request_convert()

    assert window.state is GuiState.CONVERTING
    assert window.profile_combo.isEnabled() is False
    assert window.set_output_profile(SECOND_PROFILE_ID) == DEFAULT_PROFILE_ID
    assert window.profile_combo.currentData() == DEFAULT_PROFILE_ID


def test_selector_is_available_again_after_a_completion(window: "MainWindow") -> None:
    """The lock is bounded to the conversion."""
    window.set_source("notes.md")
    window.request_convert()
    window.simulate_success()

    assert window.state is GuiState.SUCCESS
    assert window.profile_combo.isEnabled() is True
    assert window.set_output_profile(SECOND_PROFILE_ID) == SECOND_PROFILE_ID


def test_selector_is_available_in_the_empty_state(window: "MainWindow") -> None:
    """The choice can be made before selecting a file."""
    assert window.state is GuiState.EMPTY
    assert window.profile_combo.isEnabled() is True


# ============================================================
# Single-file application
# ============================================================


def test_default_profile_is_not_sent_as_a_configuration_override(
    window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The accepted request shape of the default workflow is unchanged."""
    calls = _spy_on_service(window, monkeypatch)
    window.set_source_file(str(_markdown(tmp_path)))
    window.start_conversion()
    assert _wait_until(lambda: not window.worker.is_running)

    assert len(calls) == 1
    assert calls[0]["request"].config_overrides is None


def test_selected_profile_reaches_the_service_request(
    window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A non-default profile is carried as configuration intent."""
    output_dir = tmp_path / "exports"
    output_dir.mkdir()
    calls = _spy_on_service(window, monkeypatch)

    window.set_source_file(str(_markdown(tmp_path)))
    window.set_output_directory(output_dir)
    window.set_output_profile(SECOND_PROFILE_ID)
    window.start_conversion()
    assert _wait_until(lambda: not window.worker.is_running)

    assert len(calls) == 1
    assert calls[0]["request"].config_overrides == {
        OUTPUT_DIR_CONFIG_KEY: str(output_dir),
        OUTPUT_PROFILE_CONFIG_KEY: SECOND_PROFILE_ID,
    }
    assert calls[0]["request"].output_path is None


def test_real_conversion_uses_the_selected_profile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The selected profile is observable in the produced DOCX."""
    from docx import Document

    monkeypatch.chdir(tmp_path)
    instance = _window(_store(tmp_path))
    results: List[ConversionResult] = []
    instance.worker.succeeded.connect(results.append)
    try:
        instance.set_source_file(str(_markdown(tmp_path)))
        instance.set_output_profile(THIRD_PROFILE_ID)
        instance.start_conversion()
        assert _wait_until(lambda: not instance.worker.is_running)

        assert results and results[0].status is ConversionStatus.SUCCESS
        assert results[0].output_path is not None
        doc = Document(str(results[0].output_path))
        assert doc.sections[0].left_margin.cm == pytest.approx(2.2, abs=0.01)
        assert doc.styles["Normal"].font.size.pt == pytest.approx(10.5)
    finally:
        instance.close()


# ============================================================
# Batch application (WP-POP-05)
# ============================================================


def test_batch_uses_one_profile_for_every_file(
    window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One batch is one profile; there is no per-file profile configuration."""
    sources = [_markdown(tmp_path, name) for name in ("a.md", "b.md", "c.md")]
    calls = _spy_on_service(window, monkeypatch)

    window.set_output_profile(SECOND_PROFILE_ID)
    window.add_source_files(sources)
    window.start_conversion()
    assert _wait_until(lambda: not window.worker.is_running)

    assert len(calls) == 3
    profiles = [
        (call["request"].config_overrides or {}).get(OUTPUT_PROFILE_CONFIG_KEY) for call in calls
    ]
    assert profiles == [SECOND_PROFILE_ID] * 3
    assert [Path(call["request"].source_path).name for call in calls] == [
        "a.md",
        "b.md",
        "c.md",
    ]


def test_batch_profile_is_frozen_at_batch_start(
    window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A mid-run change is refused and the captured profile stays in force."""
    import threading

    sources = [_markdown(tmp_path, name) for name in ("a.md", "b.md")]
    release = threading.Event()
    original = window.service.convert
    calls: List[dict] = []

    def blocking(request: ConversionRequest) -> ConversionResult:
        calls.append({"request": request})
        release.wait(timeout=30)
        return original(request)

    monkeypatch.setattr(window.service, "convert", blocking)

    window.set_output_profile(SECOND_PROFILE_ID)
    window.add_source_files(sources)
    window.start_conversion()
    assert _wait_until(lambda: bool(calls))

    # Locked: neither the widget nor the setter can change the active profile.
    assert window.profile_combo.isEnabled() is False
    assert window.set_output_profile(THIRD_PROFILE_ID) == SECOND_PROFILE_ID
    release.set()
    assert _wait_until(lambda: not window.worker.is_running)

    assert len(calls) == 2
    assert all(
        (call["request"].config_overrides or {}).get(OUTPUT_PROFILE_CONFIG_KEY) == SECOND_PROFILE_ID
        for call in calls
    )


def test_next_batch_uses_the_new_selection_and_releases_the_captured_profile(
    window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A change after the run applies to the next batch only (no leakage)."""
    calls = _spy_on_service(window, monkeypatch)

    window.set_output_profile(SECOND_PROFILE_ID)
    window.set_source_file(str(_markdown(tmp_path, "first.md")))
    window.start_conversion()
    assert _wait_until(lambda: not window.worker.is_running)
    assert window._batch_profile_id is None
    assert window.profile_combo.isEnabled() is True

    window.set_source_file(str(_markdown(tmp_path, "second.md")))
    window.set_output_profile(THIRD_PROFILE_ID)
    window.start_conversion()
    assert _wait_until(lambda: not window.worker.is_running)

    assert len(calls) == 2
    assert (calls[0]["request"].config_overrides or {}).get(
        OUTPUT_PROFILE_CONFIG_KEY
    ) == SECOND_PROFILE_ID
    assert (calls[1]["request"].config_overrides or {}).get(
        OUTPUT_PROFILE_CONFIG_KEY
    ) == THIRD_PROFILE_ID


def test_no_profile_leaks_when_a_batch_item_fails(
    window: "MainWindow", tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failed item neither changes the profile nor stops the batch."""
    sources = [_markdown(tmp_path, "ok.md"), _markdown(tmp_path, "empty.md")]
    (tmp_path / "empty.md").write_text("", encoding="utf-8")
    calls = _spy_on_service(window, monkeypatch)

    window.set_output_profile(SECOND_PROFILE_ID)
    window.add_source_files(sources)
    window.start_conversion()
    assert _wait_until(lambda: not window.worker.is_running)

    assert len(calls) == 2
    assert all(
        (call["request"].config_overrides or {}).get(OUTPUT_PROFILE_CONFIG_KEY) == SECOND_PROFILE_ID
        for call in calls
    )


# ============================================================
# Boundary
# ============================================================


def test_window_contains_no_profile_identifier_literals() -> None:
    """The window knows identifiers only through the single authority."""
    source = MAIN_WINDOW_MODULE.read_text(encoding="utf-8")

    for identifier in profile_ids():
        assert identifier not in source, identifier
