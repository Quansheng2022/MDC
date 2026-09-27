"""Focused verification for the GUI-local preferences (WP-P12-07-01).

The preference model must be small, GUI-local, default-safe and test-isolated:

* a first launch, a missing key and a stale value all fall back to defaults;
* saved values round-trip and survive a new instance of the same store;
* a remembered folder is a chooser starting location only - it never becomes an
  output override, so the conversion request is unchanged;
* a stored geometry that is off-screen is rejected in favour of the default;
* ``reset`` touches only the GUI-owned keys;
* a window that was not given a store never reads or writes the real user
  settings.
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

from PySide6.QtCore import QByteArray, QRect, QSettings  # noqa: E402 - guard runs first

from md_converter.gui.preferences import (  # noqa: E402 - guard runs first
    DEFAULT_REMEMBER_FOLDERS,
    GEOMETRY_KEY,
    GUI_SETTING_KEYS,
    LAST_SOURCE_DIRECTORY_KEY,
    REMEMBER_FOLDERS_KEY,
    GuiPreferences,
    geometry_is_usable,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
GUI_DIR = PROJECT_ROOT / "md_converter" / "gui"

#: Conversion-core modules the GUI layer must never import (WP-P12-05-03 §5).
FORBIDDEN_IMPORT_PREFIXES = (
    "md_converter.compiler",
    "md_converter.diagnostics",
    "md_converter.parser",
    "md_converter.pipeline",
    "md_converter.renderer",
    "md_converter.services",
    "md_converter.quality_gate",
)


def _store(tmp_path: Path) -> GuiPreferences:
    """Return one isolated file-backed preference store."""
    return GuiPreferences.for_file(tmp_path / "gui_preferences.ini")


def _markdown(tmp_path: Path, name: str = "notes.md") -> Path:
    """Write a minimal Markdown source and return its path."""
    path = tmp_path / name
    path.write_text("# Notes\n\nBody text.\n", encoding="utf-8")
    return path


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


# ============================================================
# Defaults and first launch
# ============================================================


def test_first_launch_uses_documented_defaults(tmp_path: Path) -> None:
    """WP §"first launch safely uses defaults"."""
    prefs = _store(tmp_path)

    assert prefs.remember_folders is DEFAULT_REMEMBER_FOLDERS is True
    assert prefs.last_source_directory is None
    assert prefs.last_output_directory is None
    assert prefs.window_geometry() is None


def test_missing_and_unreadable_values_fall_back(tmp_path: Path) -> None:
    """A missing key, a blank value or a foreign value never raises."""
    prefs = _store(tmp_path)
    settings = QSettings(str(tmp_path / "gui_preferences.ini"), QSettings.Format.IniFormat)
    settings.setValue(REMEMBER_FOLDERS_KEY, "not-a-boolean")
    settings.setValue(LAST_SOURCE_DIRECTORY_KEY, "   ")
    settings.setValue(GEOMETRY_KEY, "")
    settings.sync()

    assert prefs.remember_folders is DEFAULT_REMEMBER_FOLDERS
    assert prefs.last_source_directory is None
    assert prefs.window_geometry() is None


# ============================================================
# Round-trip and persistence
# ============================================================


def test_remember_folders_toggle_round_trips(tmp_path: Path) -> None:
    """The single toggle round-trips through the store."""
    prefs = _store(tmp_path)

    prefs.set_remember_folders(False)
    assert prefs.remember_folders is False
    prefs.set_remember_folders(True)
    assert prefs.remember_folders is True


def test_folders_round_trip(tmp_path: Path) -> None:
    """Remembered folders round-trip as absolute existing directories."""
    prefs = _store(tmp_path)

    assert prefs.remember_source_directory(tmp_path) == tmp_path
    assert prefs.remember_output_directory(tmp_path) == tmp_path
    assert prefs.last_source_directory == tmp_path
    assert prefs.last_output_directory == tmp_path


def test_values_persist_across_instances(tmp_path: Path) -> None:
    """Saved values survive a new preference instance over the same store."""
    first = _store(tmp_path)
    first.set_remember_folders(False)
    first.set_window_geometry(QByteArray(b"geometry-bytes"))
    first.sync()

    second = _store(tmp_path)
    assert second.remember_folders is False
    assert second.window_geometry() == QByteArray(b"geometry-bytes")


def test_geometry_round_trips_and_clears(tmp_path: Path) -> None:
    """Window geometry round-trips and can be cleared explicitly."""
    prefs = _store(tmp_path)
    geometry = QByteArray(b"stored-window-geometry")

    prefs.set_window_geometry(geometry)
    assert prefs.window_geometry() == geometry

    prefs.clear_window_geometry()
    assert prefs.window_geometry() is None

    prefs.set_window_geometry(geometry)
    prefs.set_window_geometry(None)
    assert prefs.window_geometry() is None


# ============================================================
# Folder behaviour (GUI convenience only)
# ============================================================


def test_remembering_disabled_never_stores_folders(tmp_path: Path) -> None:
    """With remembering off, folders are neither stored nor returned."""
    prefs = _store(tmp_path)
    prefs.set_remember_folders(False)

    assert prefs.remember_source_directory(tmp_path) is None
    assert prefs.last_source_directory is None

    settings = QSettings(str(tmp_path / "gui_preferences.ini"), QSettings.Format.IniFormat)
    assert settings.value(LAST_SOURCE_DIRECTORY_KEY, None) is None


def test_disabling_remembering_hides_already_stored_folders(tmp_path: Path) -> None:
    """Turning the toggle off suppresses previously remembered folders."""
    prefs = _store(tmp_path)
    prefs.remember_source_directory(tmp_path)
    assert prefs.last_source_directory == tmp_path

    prefs.set_remember_folders(False)
    assert prefs.last_source_directory is None
    assert prefs.last_output_directory is None


def test_stale_folder_is_ignored(tmp_path: Path) -> None:
    """A remembered folder that no longer exists is ignored, not returned."""
    gone = tmp_path / "gone"
    gone.mkdir()
    prefs = _store(tmp_path)
    prefs.remember_source_directory(gone)
    gone.rmdir()

    assert prefs.last_source_directory is None


def test_unusable_folder_candidates_are_rejected(tmp_path: Path) -> None:
    """Blank, missing and file candidates are never remembered."""
    prefs = _store(tmp_path)
    candidate_file = _markdown(tmp_path)

    assert prefs.remember_source_directory(None) is None
    assert prefs.remember_source_directory("") is None
    assert prefs.remember_source_directory(tmp_path / "missing") is None
    assert prefs.remember_source_directory(candidate_file) is None
    assert prefs.last_source_directory is None


def test_clear_remembered_folders_keeps_other_preferences(tmp_path: Path) -> None:
    """Clearing folders leaves the toggle and the geometry alone."""
    prefs = _store(tmp_path)
    prefs.set_remember_folders(False)
    prefs.set_window_geometry(QByteArray(b"geometry-bytes"))
    prefs.remember_source_directory(tmp_path)

    prefs.clear_remembered_folders()

    assert prefs.last_source_directory is None
    assert prefs.last_output_directory is None
    assert prefs.remember_folders is False
    assert prefs.window_geometry() == QByteArray(b"geometry-bytes")


# ============================================================
# Reset
# ============================================================


def test_reset_restores_gui_defaults(tmp_path: Path) -> None:
    """Reset returns every GUI-owned preference to its default."""
    prefs = _store(tmp_path)
    prefs.set_remember_folders(False)
    prefs.remember_source_directory(tmp_path)
    prefs.remember_output_directory(tmp_path)
    prefs.set_window_geometry(QByteArray(b"geometry-bytes"))

    prefs.reset()

    assert prefs.remember_folders is DEFAULT_REMEMBER_FOLDERS
    assert prefs.last_source_directory is None
    assert prefs.last_output_directory is None
    assert prefs.window_geometry() is None


def test_reset_removes_only_gui_owned_keys(tmp_path: Path) -> None:
    """Reset is bounded to the declared GUI keys (WP-P12-07-01 "GUI only")."""
    path = tmp_path / "gui_preferences.ini"
    prefs = GuiPreferences.for_file(path)
    prefs.remember_source_directory(tmp_path)
    prefs.set_window_geometry(QByteArray(b"geometry-bytes"))

    foreign = QSettings(str(path), QSettings.Format.IniFormat)
    foreign.setValue("application/unrelated", "kept")
    foreign.sync()

    prefs.reset()
    foreign.sync()

    assert foreign.value("application/unrelated") == "kept"
    for key in GUI_SETTING_KEYS:
        assert foreign.value(key, None) is None, key


# ============================================================
# Store isolation
# ============================================================


def test_session_store_is_process_local_and_isolated() -> None:
    """The session store has no on-disk footprint and no shared state."""
    first = GuiPreferences.session()
    second = GuiPreferences.session()

    first.set_remember_folders(False)
    first.set_window_geometry(QByteArray(b"geometry-bytes"))

    assert second.remember_folders is True
    assert second.window_geometry() is None


def test_file_stores_do_not_share_values(tmp_path: Path) -> None:
    """Two isolated stores keep their own values."""
    first = GuiPreferences.for_file(tmp_path / "a.ini")
    second = GuiPreferences.for_file(tmp_path / "b.ini")

    first.set_remember_folders(False)

    assert second.remember_folders is True


def test_default_window_store_never_touches_user_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A window constructed without a store must not consult the real store."""
    import md_converter.gui.main_window as main_window_module
    from md_converter.gui.app import create_application

    def _forbidden() -> GuiPreferences:
        raise AssertionError("the application preference store must not be used here")

    monkeypatch.setattr(main_window_module.GuiPreferences, "for_application", _forbidden)
    create_application([])

    window = main_window_module.MainWindow()
    try:
        window.preferences.set_remember_folders(False)
        window.close()
    finally:
        window.close()


# ============================================================
# Geometry safety
# ============================================================


def test_geometry_is_usable_accepts_visible_rect() -> None:
    """A window fully inside a screen is usable."""
    screens = [QRect(0, 0, 1920, 1080)]

    assert geometry_is_usable(QRect(100, 100, 900, 600), screens) is True
    assert geometry_is_usable(QRect(1850, 1000, 900, 600), screens) is True


def test_geometry_is_usable_rejects_off_screen_rect() -> None:
    """A window outside every screen is rejected."""
    screens = [QRect(0, 0, 1920, 1080)]

    assert geometry_is_usable(QRect(5000, 5000, 900, 600), screens) is False
    assert geometry_is_usable(QRect(-4000, -4000, 900, 600), screens) is False
    assert geometry_is_usable(QRect(2400, 0, 900, 600), screens) is False


def test_geometry_is_usable_requires_a_meaningful_sliver() -> None:
    """A barely-visible sliver does not count as usable."""
    screens = [QRect(0, 0, 1920, 1080)]

    assert geometry_is_usable(QRect(1910, 1070, 900, 600), screens) is False
    assert geometry_is_usable(QRect(1910, 0, 900, 600), screens, minimum_visible=5) is True


def test_geometry_is_usable_without_screens_accepts() -> None:
    """With no screen information there is nothing to reject against."""
    assert geometry_is_usable(QRect(0, 0, 900, 600), []) is True


# ============================================================
# Main window integration
# ============================================================


@pytest.fixture
def window(tmp_path: Path) -> Iterator["MainWindow"]:
    """Provide a main window over an isolated preference store."""
    from md_converter.gui.app import create_application
    from md_converter.gui.main_window import MainWindow

    create_application([])
    instance = MainWindow(preferences=_store(tmp_path))
    yield instance
    instance.close()


def test_window_uses_isolated_preferences(window: "MainWindow") -> None:
    """The window exposes the store it was given."""
    assert isinstance(window.preferences, GuiPreferences)
    assert window.preferences.window_geometry() is None


def test_window_restores_a_saved_geometry(tmp_path: Path) -> None:
    """A saved, on-screen geometry is restored on the next window."""
    from md_converter.gui.app import create_application
    from md_converter.gui.main_window import MainWindow

    create_application([])
    prefs = _store(tmp_path)
    first = MainWindow(preferences=prefs)
    try:
        # Kept inside the offscreen platform's screen so the platform does not
        # clamp the restored size (a real screen clamps the same way).
        first.resize(720, 520)
        first.close()  # stores the geometry
    finally:
        first.close()

    assert prefs.window_geometry() is not None

    second = MainWindow(preferences=prefs)
    try:
        assert (second.width(), second.height()) == (720, 520)
    finally:
        second.close()


def test_window_rejects_an_off_screen_geometry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A stored geometry placed off every screen falls back to the default."""
    import md_converter.gui.main_window as main_window_module
    from md_converter.gui.app import create_application
    from md_converter.gui.main_window import WINDOW_HEIGHT, WINDOW_WIDTH, MainWindow

    create_application([])
    prefs = _store(tmp_path)
    first = MainWindow(preferences=prefs)
    first.resize(820, 560)
    first.close()

    monkeypatch.setattr(
        main_window_module, "available_screen_rects", lambda: [QRect(0, 0, 1920, 1080)]
    )
    monkeypatch.setattr(main_window_module, "geometry_is_usable", lambda *a, **k: False)

    second = MainWindow(preferences=prefs)
    try:
        assert (second.width(), second.height()) == (WINDOW_WIDTH, WINDOW_HEIGHT)
    finally:
        second.close()


def test_close_does_not_store_geometry_while_converting(
    window: "MainWindow",
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A refused close (active worker) stores no geometry."""
    import threading
    import time

    from md_converter.application.conversion_result import ConversionResult, ConversionStatus

    release = threading.Event()

    def blocking(request) -> ConversionResult:
        release.wait(timeout=30)
        return ConversionResult(status=ConversionStatus.SUCCESS)

    monkeypatch.setattr(window.service, "convert", blocking)
    window.set_source_file(str(_markdown(tmp_path)))
    window.start_conversion()

    try:
        assert window.is_conversion_active is True
        window.close()
        assert window.is_conversion_active is True
        assert window.preferences.window_geometry() is None
    finally:
        release.set()
        deadline = time.monotonic() + 30
        while window.worker.is_running and time.monotonic() < deadline:
            from PySide6.QtWidgets import QApplication

            QApplication.processEvents()
            time.sleep(0.005)


def test_an_accepted_close_stores_the_geometry(window: "MainWindow") -> None:
    """A normal close stores the geometry for the next launch."""
    window.resize(810, 550)
    window.close()

    assert window.preferences.window_geometry() is not None


def test_window_remembers_the_source_folder(window: "MainWindow", tmp_path: Path) -> None:
    """Selecting a source remembers its containing folder."""
    window.set_source_file(str(_markdown(tmp_path, "chosen.md")))

    assert window.preferences.last_source_directory == tmp_path


def test_rejected_source_is_not_remembered(window: "MainWindow", tmp_path: Path) -> None:
    """A rejected candidate changes no preference."""
    window.set_source_file(str(tmp_path / "missing.md"))

    assert window.preferences.last_source_directory is None


def test_window_remembers_the_output_folder(window: "MainWindow", tmp_path: Path) -> None:
    """Choosing an output folder remembers it as GUI convenience."""
    chosen = tmp_path / "out"
    chosen.mkdir()

    assert window.set_output_directory(chosen) == chosen
    assert window.preferences.last_output_directory == chosen


def test_remembered_output_folder_is_not_an_override(tmp_path: Path) -> None:
    """A remembered output folder never becomes a conversion override."""
    from md_converter.gui.app import create_application
    from md_converter.gui.main_window import OUTPUT_VALUE_TEXT, MainWindow
    from md_converter.gui.request_builder import build_conversion_request

    create_application([])
    prefs = _store(tmp_path)
    remembered = tmp_path / "remembered"
    remembered.mkdir()
    prefs.remember_output_directory(remembered)

    window = MainWindow(preferences=prefs)
    try:
        assert window.output_directory is None
        assert window.output_value_label.text() == OUTPUT_VALUE_TEXT
        request = build_conversion_request(str(_markdown(tmp_path)), window.output_directory)
        assert request is not None
        assert request.config_overrides is None
    finally:
        window.close()


def test_choosers_start_in_the_remembered_folders(
    window: "MainWindow",
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Both choosers receive the remembered folder as their start directory."""
    import md_converter.gui.main_window as main_window_module

    remembered_source = tmp_path / "source"
    remembered_output = tmp_path / "destination"
    remembered_source.mkdir()
    remembered_output.mkdir()
    window.preferences.remember_source_directory(remembered_source)
    window.preferences.remember_output_directory(remembered_output)

    seen: List[object] = []
    monkeypatch.setattr(
        main_window_module.file_picker,
        "ask_for_markdown_source",
        lambda parent, directory=None: seen.append(directory) or None,
    )
    monkeypatch.setattr(
        main_window_module.file_picker,
        "ask_for_output_directory",
        lambda parent, directory=None: seen.append(directory) or None,
    )

    window.choose_source()
    window.choose_output_directory()

    assert seen == [remembered_source, remembered_output]


def test_session_output_choice_wins_over_the_remembered_folder(
    window: "MainWindow",
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An explicit session choice is the chooser's start directory."""
    import md_converter.gui.main_window as main_window_module

    remembered = tmp_path / "remembered"
    session = tmp_path / "session"
    remembered.mkdir()
    session.mkdir()
    window.preferences.remember_output_directory(remembered)
    window.set_output_directory(session)

    seen: List[object] = []
    monkeypatch.setattr(
        main_window_module.file_picker,
        "ask_for_output_directory",
        lambda parent, directory=None: seen.append(directory) or None,
    )

    window.choose_output_directory()

    assert seen == [session]


# ============================================================
# Boundary
# ============================================================


def test_preferences_module_imports_no_conversion_core() -> None:
    """The preference model imports no compiler/parser/pipeline/renderer/QA."""
    offenders = {
        name
        for name in _imported_modules(GUI_DIR / "preferences.py")
        if name.startswith(FORBIDDEN_IMPORT_PREFIXES)
    }

    assert not offenders, sorted(offenders)


def test_preferences_module_is_qt_local_only() -> None:
    """The preference model depends on Qt, not on any application-layer type."""
    names = _imported_modules(GUI_DIR / "preferences.py")

    assert "md_converter.application" not in names
    assert "PySide6.QtCore" in names
