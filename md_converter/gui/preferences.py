"""GUI-local preference model and persistence for MD_Converter (WP-P12-07-01).

The desktop GUI owns a very small, user-understandable set of preferences:

    window geometry  ->  restored window size/position
    last source directory / last output directory
    one "remember folders" toggle
    reset to the GUI-owned defaults

Persistence boundary (WP-P12-07-01 "Preferred"):

    MainWindow  ->  GuiPreferences  ->  QSettings

The store stays GUI-local: it never touches the application or Core
configuration, never defines conversion behaviour and never becomes a second
configuration authority.  The remembered *output* directory is GUI convenience
only - it seeds the folder chooser and never redefines the
``ConversionService`` default output semantics (WP-P12-07 "Critical output
directory rule").

Robustness rules:

* a first launch, a missing key or an unreadable value falls back to the
  documented default instead of failing;
* a remembered folder that no longer exists is ignored (never returned);
* a stored geometry that would place the window off-screen is rejected by
  :func:`geometry_is_usable`, so the caller can fall back to the default size;
* tests can construct the model over an isolated store
  (:meth:`GuiPreferences.for_file`) or a process-local one
  (:meth:`GuiPreferences.session`), so no test ever reads or writes the real
  user settings.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Protocol, Union

from PySide6.QtCore import QByteArray, QRect, QSettings
from PySide6.QtGui import QGuiApplication

__all__ = [
    "DEFAULT_REMEMBER_FOLDERS",
    "GEOMETRY_KEY",
    "GUI_SETTING_KEYS",
    "LAST_OUTPUT_DIRECTORY_KEY",
    "LAST_SOURCE_DIRECTORY_KEY",
    "MINIMUM_VISIBLE_PIXELS",
    "REMEMBER_FOLDERS_KEY",
    "GuiPreferences",
    "available_screen_rects",
    "geometry_is_usable",
]

#: Stored window geometry (size and position) of the main window.
GEOMETRY_KEY = "window/geometry"

#: The single "remember folders" toggle.
REMEMBER_FOLDERS_KEY = "folders/remember"

#: Last directories used by the GUI convenience pickers.
LAST_SOURCE_DIRECTORY_KEY = "folders/last_source_directory"
LAST_OUTPUT_DIRECTORY_KEY = "folders/last_output_directory"

#: Every key this GUI owns.  Declaring the set keeps :meth:`GuiPreferences.reset`
#: and the "GUI preferences only" rule explicit and auditable.
GUI_SETTING_KEYS = (
    GEOMETRY_KEY,
    REMEMBER_FOLDERS_KEY,
    LAST_SOURCE_DIRECTORY_KEY,
    LAST_OUTPUT_DIRECTORY_KEY,
)

#: Default of the "remember folders" toggle.  Remembering folders is the
#: expected desktop behaviour; the user can turn it off.
DEFAULT_REMEMBER_FOLDERS = True

#: A restored window must leave at least this many pixels visible on a screen.
MINIMUM_VISIBLE_PIXELS = 48


class PreferenceBackend(Protocol):
    """Minimal key/value store used by :class:`GuiPreferences`.

    The production backend is :class:`QSettings`; tests and direct
    ``MainWindow()`` construction use a process-local in-memory backend so the
    real user settings are never touched.  Only the four operations the
    preference model needs are required.
    """

    def value(self, key: str, default: Any = None, type: Any = None) -> Any:
        """Return the stored value for ``key``, or ``default`` when absent."""

    def setValue(self, key: str, value: Any) -> None:  # noqa: N802 - Qt API name
        """Store ``value`` under ``key``."""

    def remove(self, key: str) -> None:
        """Remove ``key`` if it is present."""

    def clear(self) -> None:
        """Remove every stored key."""


class _SessionBackend:
    """Process-local in-memory backend with no on-disk footprint.

    Used when no explicit store is supplied, so an isolated window (a test, an
    embedded launcher) can never read or write the real user settings.
    """

    def __init__(self) -> None:
        self._values: Dict[str, Any] = {}

    def value(self, key: str, default: Any = None, type: Any = None) -> Any:  # noqa: A002
        return self._values.get(key, default)

    def setValue(self, key: str, value: Any) -> None:  # noqa: N802 - Qt API name
        self._values[key] = value

    def remove(self, key: str) -> None:
        self._values.pop(key, None)

    def clear(self) -> None:
        self._values.clear()


def _usable_directory(value: Union[str, Path, None]) -> Optional[Path]:
    """Return ``value`` as an existing directory, or ``None``.

    A missing value, a blank value and a path that no longer exists all fail
    closed, so a stale remembered folder is simply ignored rather than handed
    to a file dialog.

    Args:
        value: Candidate directory from the preference store or the caller.

    Returns:
        Optional[Path]: The directory when it is usable, otherwise ``None``.
    """
    if value is None:
        return None
    if isinstance(value, Path):
        candidate = value
    else:
        text = str(value).strip()
        if not text:
            return None
        candidate = Path(text)
    try:
        if candidate.is_dir():
            return candidate
    except OSError:
        return None
    return None


def _as_bool(value: Any, default: bool) -> bool:
    """Return ``value`` as a bool, accepting the textual INI encodings.

    Args:
        value: Stored value, a :class:`bool` or a textual representation.
        default: Value used when ``value`` cannot be interpreted.

    Returns:
        bool: The interpreted flag.
    """
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in ("true", "1", "yes", "on"):
        return True
    if text in ("false", "0", "no", "off"):
        return False
    return default


def available_screen_rects() -> List[QRect]:
    """Return the usable geometry of every attached screen.

    Returns:
        List[QRect]: One rectangle per screen; empty when the platform reports
        no screen (for example some headless configurations).
    """
    return [screen.availableGeometry() for screen in QGuiApplication.screens()]


def geometry_is_usable(
    rect: QRect,
    screen_rects: Iterable[QRect],
    *,
    minimum_visible: int = MINIMUM_VISIBLE_PIXELS,
) -> bool:
    """Return whether ``rect`` stays reasonably visible on some screen.

    A stored geometry can be stale: a monitor was unplugged, the resolution
    changed, or the desktop layout moved.  Restoring such a geometry would
    place the window off-screen, so the caller falls back to the default size.

    Args:
        rect: Candidate window rectangle (frame geometry).
        screen_rects: Available screen rectangles.
        minimum_visible: Minimum visible width and height required.

    Returns:
        bool: ``True`` when enough of ``rect`` is visible on at least one
        screen.  When no screen is reported there is nothing to compare
        against, so the geometry is accepted.
    """
    screens = list(screen_rects)
    if not screens:
        return True
    for screen in screens:
        overlap = screen.intersected(rect)
        if overlap.width() >= minimum_visible and overlap.height() >= minimum_visible:
            return True
    return False


class GuiPreferences:
    """The GUI's own preference values over a small key/value store.

    Args:
        backend: Storage backend.  Defaults to a process-local in-memory store
            (:class:`_SessionBackend`), so a window that was not given a store
            cannot touch the real user settings.
    """

    def __init__(self, backend: Optional[PreferenceBackend] = None) -> None:
        self._backend: PreferenceBackend = backend if backend is not None else _SessionBackend()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    @classmethod
    def for_application(cls) -> "GuiPreferences":
        """Return the production store (the platform's native QSettings store).

        Returns:
            GuiPreferences: Preferences persisted for the product identity
            declared by :mod:`md_converter.gui.app`.
        """
        # Imported here on purpose: the bootstrap module imports this module
        # (through the main window), so a module-level import would be cyclic.
        from .app import APPLICATION_NAME, ORGANIZATION_NAME

        settings = QSettings(
            QSettings.Format.NativeFormat,
            QSettings.Scope.UserScope,
            ORGANIZATION_NAME,
            APPLICATION_NAME,
        )
        return cls(settings)

    @classmethod
    def for_file(cls, path: Union[str, Path]) -> "GuiPreferences":
        """Return a store backed by one INI file (used by tests).

        Args:
            path: Location of the INI file.

        Returns:
            GuiPreferences: Preferences stored in ``path``.
        """
        return cls(QSettings(str(path), QSettings.Format.IniFormat))

    @classmethod
    def session(cls) -> "GuiPreferences":
        """Return a process-local store with no on-disk footprint.

        Returns:
            GuiPreferences: Preferences that live for this process only.
        """
        return cls(_SessionBackend())

    def sync(self) -> None:
        """Flush pending writes to the underlying store when it supports it."""
        sync = getattr(self._backend, "sync", None)
        if callable(sync):
            sync()

    # ------------------------------------------------------------------
    # Remember-folders toggle
    # ------------------------------------------------------------------

    @property
    def remember_folders(self) -> bool:
        """Whether the last-used folders are remembered."""
        stored = self._backend.value(REMEMBER_FOLDERS_KEY, DEFAULT_REMEMBER_FOLDERS, bool)
        return _as_bool(stored, DEFAULT_REMEMBER_FOLDERS)

    def set_remember_folders(self, enabled: bool) -> None:
        """Set the "remember folders" toggle.

        Args:
            enabled: New toggle value.
        """
        self._backend.setValue(REMEMBER_FOLDERS_KEY, bool(enabled))

    # ------------------------------------------------------------------
    # Remembered folders (GUI convenience only)
    # ------------------------------------------------------------------

    @property
    def last_source_directory(self) -> Optional[Path]:
        """Return the remembered source folder, or ``None``.

        The value is a picker starting location only: it never changes the
        selected source and never changes conversion behaviour.
        """
        if not self.remember_folders:
            return None
        return _usable_directory(self._backend.value(LAST_SOURCE_DIRECTORY_KEY, ""))

    @property
    def last_output_directory(self) -> Optional[Path]:
        """Return the remembered output folder, or ``None``.

        The value seeds the directory chooser only.  It is deliberately *not*
        restored as an output override: without an explicit user selection the
        existing application default output behaviour stays in force.
        """
        if not self.remember_folders:
            return None
        return _usable_directory(self._backend.value(LAST_OUTPUT_DIRECTORY_KEY, ""))

    def remember_source_directory(self, directory: Union[str, Path, None]) -> Optional[Path]:
        """Remember the folder that contained the selected source.

        Args:
            directory: Candidate folder.

        Returns:
            Optional[Path]: The stored folder, or ``None`` when nothing was
            stored (remembering disabled or the folder is not usable).
        """
        return self._remember_directory(LAST_SOURCE_DIRECTORY_KEY, directory)

    def remember_output_directory(self, directory: Union[str, Path, None]) -> Optional[Path]:
        """Remember the folder selected for output.

        Args:
            directory: Candidate folder.

        Returns:
            Optional[Path]: The stored folder, or ``None`` when nothing was
            stored (remembering disabled or the folder is not usable).
        """
        return self._remember_directory(LAST_OUTPUT_DIRECTORY_KEY, directory)

    def clear_remembered_folders(self) -> None:
        """Forget both remembered folders without touching anything else."""
        self._backend.remove(LAST_SOURCE_DIRECTORY_KEY)
        self._backend.remove(LAST_OUTPUT_DIRECTORY_KEY)

    def _remember_directory(
        self,
        key: str,
        directory: Union[str, Path, None],
    ) -> Optional[Path]:
        """Store one folder under ``key`` when remembering is enabled."""
        if not self.remember_folders:
            return None
        resolved = _usable_directory(directory)
        if resolved is None:
            return None
        self._backend.setValue(key, str(resolved))
        return resolved

    # ------------------------------------------------------------------
    # Window geometry
    # ------------------------------------------------------------------

    def window_geometry(self) -> Optional[QByteArray]:
        """Return the stored window geometry, or ``None`` when absent/invalid."""
        raw = self._backend.value(GEOMETRY_KEY, None)
        if raw is None:
            return None
        if isinstance(raw, QByteArray):
            data = raw
        else:
            text = str(raw).strip()
            if not text:
                return None
            data = QByteArray(text.encode("latin-1", "ignore"))
        return None if data.isEmpty() else data

    def set_window_geometry(self, geometry: Union[QByteArray, bytes, None]) -> None:
        """Store the window geometry.

        Args:
            geometry: Value returned by ``QWidget.saveGeometry()``.  ``None``
                clears the stored geometry.
        """
        if geometry is None:
            self.clear_window_geometry()
            return
        data = geometry if isinstance(geometry, QByteArray) else QByteArray(geometry)
        self._backend.setValue(GEOMETRY_KEY, data)

    def clear_window_geometry(self) -> None:
        """Forget the stored window geometry."""
        self._backend.remove(GEOMETRY_KEY)

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Restore every GUI-owned preference to its default.

        Only the keys declared by :data:`GUI_SETTING_KEYS` are removed; no
        application, Core or packaging setting is touched.
        """
        for key in GUI_SETTING_KEYS:
            self._backend.remove(key)
