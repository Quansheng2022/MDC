"""Compact Settings surface for the MD_Converter GUI (WP-P12-07-02).

One small dialog over the accepted GUI-local preferences
(:mod:`md_converter.gui.preferences`):

    Open Settings
        -> the current values are loaded into the controls
    Save
        -> the edited values are persisted and the dialog closes
    Cancel
        -> the edits are discarded and the dialog closes
    Reset to Defaults
        -> the GUI-owned defaults are restored in the form; Save then persists
           them (nothing is written until Save, so Cancel still discards)

Interaction rules (WP-P12-07-02):

* the surface edits GUI preferences only - it never triggers a conversion and
  never touches an application, Core or packaging setting;
* it stays on one page: the setting count does not justify a settings centre;
* ``Esc`` closes the dialog, and both ``Cancel`` and ``Esc`` discard the edits.

The dialog is presentation plus the two bounded write operations above; the
preference semantics themselves stay in :class:`GuiPreferences`.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .preferences import DEFAULT_REMEMBER_FOLDERS, GuiPreferences

__all__ = [
    "CANCEL_TEXT",
    "FOLDERS_SECTION_TEXT",
    "LAST_OUTPUT_CAPTION_TEXT",
    "LAST_SOURCE_CAPTION_TEXT",
    "NOT_REMEMBERED_TEXT",
    "REMEMBER_FOLDERS_HELP_TEXT",
    "REMEMBER_FOLDERS_TEXT",
    "RESET_TEXT",
    "SAVE_TEXT",
    "TITLE_SETTINGS",
    "SettingsDialog",
]

#: Dialog chrome wording (plain product language).
TITLE_SETTINGS = "Settings"
FOLDERS_SECTION_TEXT = "Folders"
REMEMBER_FOLDERS_TEXT = "Remember the last folders I used"
REMEMBER_FOLDERS_HELP_TEXT = (
    "When this is on, the file and folder dialogs open where you last worked. "
    "The folders are remembered on this computer only."
)
LAST_SOURCE_CAPTION_TEXT = "Last source folder:"
LAST_OUTPUT_CAPTION_TEXT = "Last output folder:"
NOT_REMEMBERED_TEXT = "Not remembered"
RESET_TEXT = "Reset to Defaults"
SAVE_TEXT = "Save"
CANCEL_TEXT = "Cancel"

#: Stable dialog size for the single-page surface.
DIALOG_WIDTH = 460
DIALOG_HEIGHT = 240


class SettingsDialog(QDialog):
    """Single-page editor for the GUI-local preferences.

    Attributes:
        preferences: Preference store the dialog edits.
        remember_folders_checkbox: The single "remember folders" toggle.
        remembered_source_value: Read-only preview of the remembered source
            folder.
        remembered_output_value: Read-only preview of the remembered output
            folder.
        reset_button: Restores the GUI-owned defaults in the form.
        save_button: Persists the edited values.
        cancel_button: Discards the edits.
    """

    def __init__(
        self,
        preferences: GuiPreferences,
        parent: Optional[QWidget] = None,
    ) -> None:
        """Build the Settings surface over ``preferences``.

        Args:
            preferences: GUI-local preference store to read and edit.
            parent: Optional Qt parent widget.
        """
        super().__init__(parent)
        self.setObjectName("settingsDialog")
        self.setWindowTitle(TITLE_SETTINGS)
        self.setModal(True)
        self._preferences = preferences
        self._reset_requested = False

        layout = QVBoxLayout(self)
        layout.setObjectName("settingsLayout")
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(10)

        section = QLabel(FOLDERS_SECTION_TEXT, self)
        section.setObjectName("settingsSectionLabel")
        layout.addWidget(section)

        self.remember_folders_checkbox = QCheckBox(REMEMBER_FOLDERS_TEXT, self)
        self.remember_folders_checkbox.setObjectName("rememberFoldersCheckBox")
        self.remember_folders_checkbox.setAccessibleName(REMEMBER_FOLDERS_TEXT)
        self.remember_folders_checkbox.toggled.connect(self._refresh_remembered_summary)
        layout.addWidget(self.remember_folders_checkbox)

        help_label = QLabel(REMEMBER_FOLDERS_HELP_TEXT, self)
        help_label.setObjectName("rememberFoldersHelpLabel")
        help_label.setWordWrap(True)
        layout.addWidget(help_label)

        layout.addLayout(
            self._create_summary_row(
                LAST_SOURCE_CAPTION_TEXT,
                "rememberedSourceValue",
                "remembered_source_value",
            )
        )
        layout.addLayout(
            self._create_summary_row(
                LAST_OUTPUT_CAPTION_TEXT,
                "rememberedOutputValue",
                "remembered_output_value",
            )
        )
        layout.addStretch(1)

        layout.addLayout(self._create_button_row())
        self._load_values()

    # ------------------------------------------------------------------
    # Read-only state
    # ------------------------------------------------------------------

    @property
    def preferences(self) -> GuiPreferences:
        """Return the preference store this dialog edits."""
        return self._preferences

    @property
    def reset_requested(self) -> bool:
        """Whether Reset to Defaults was pressed in this dialog session."""
        return self._reset_requested

    @property
    def remember_folders(self) -> bool:
        """Return the toggle value currently shown in the form."""
        return self.remember_folders_checkbox.isChecked()

    # ------------------------------------------------------------------
    # Interaction
    # ------------------------------------------------------------------

    def _create_summary_row(
        self,
        caption_text: str,
        value_object_name: str,
        value_attribute_name: str,
    ) -> QHBoxLayout:
        """Create one read-only caption/value row."""
        row = QHBoxLayout()
        row.setObjectName(f"{value_object_name}Row")
        row.setSpacing(6)

        caption = QLabel(caption_text, self)
        caption.setObjectName(f"{value_object_name[:-5]}Caption")
        row.addWidget(caption)

        value = QLabel("", self)
        value.setObjectName(value_object_name)
        value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        row.addWidget(value, 1)
        setattr(self, value_attribute_name, value)
        return row

    def _create_button_row(self) -> QHBoxLayout:
        """Create the Reset / Cancel / Save row."""
        row = QHBoxLayout()
        row.setObjectName("settingsButtonRow")
        row.setSpacing(8)

        self.reset_button = QPushButton(RESET_TEXT, self)
        self.reset_button.setObjectName("resetToDefaultsButton")
        self.reset_button.setAutoDefault(False)
        self.reset_button.clicked.connect(self.reset_to_defaults)
        row.addWidget(self.reset_button)
        row.addStretch(1)

        self.cancel_button = QPushButton(CANCEL_TEXT, self)
        self.cancel_button.setObjectName("settingsCancelButton")
        self.cancel_button.setAutoDefault(False)
        self.cancel_button.clicked.connect(self.reject)
        row.addWidget(self.cancel_button)

        self.save_button = QPushButton(SAVE_TEXT, self)
        self.save_button.setObjectName("settingsSaveButton")
        self.save_button.setDefault(True)
        self.save_button.clicked.connect(self.save)
        row.addWidget(self.save_button)
        return row

    # ------------------------------------------------------------------
    # Load / reset / save
    # ------------------------------------------------------------------

    def _load_values(self) -> None:
        """Load the stored values into the controls (temporary editing copy)."""
        self._reset_requested = False
        self.remember_folders_checkbox.setChecked(self._preferences.remember_folders)
        self._refresh_remembered_summary()

    def _refresh_remembered_summary(self) -> None:
        """Refresh the read-only preview of what the store currently holds."""
        remembering = self.remember_folders and not self._reset_requested
        source = self._preferences.last_source_directory if remembering else None
        output = self._preferences.last_output_directory if remembering else None
        self.remembered_source_value.setText(
            str(source) if source is not None else NOT_REMEMBERED_TEXT
        )
        self.remembered_output_value.setText(
            str(output) if output is not None else NOT_REMEMBERED_TEXT
        )

    def reset_to_defaults(self) -> None:
        """Restore the GUI-owned defaults in the form.

        The defaults are applied to the store by :meth:`save`, so ``Cancel``
        still discards the reset - the dialog never writes behind the user.
        """
        self.remember_folders_checkbox.setChecked(DEFAULT_REMEMBER_FOLDERS)
        self._reset_requested = True
        self._refresh_remembered_summary()

    def save(self) -> None:
        """Persist the edited values and close the dialog."""
        if self._reset_requested:
            # Clear every GUI-owned preference (geometry included) before the
            # explicitly chosen toggle value is applied on top.
            self._preferences.reset()
        self._preferences.set_remember_folders(self.remember_folders)
        if not self.remember_folders:
            # Turning the convenience off forgets the stored folders as well.
            self._preferences.clear_remembered_folders()
        self._preferences.sync()
        self.accept()

    def keyPressEvent(self, event) -> None:  # noqa: N802 - Qt API name
        """Treat ``Esc`` as Cancel, discarding the edits.

        Args:
            event: Qt key event.
        """
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)
