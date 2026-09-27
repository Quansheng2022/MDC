"""About / Product Information surface for the GUI (WP-P12-07-03).

One small read-only dialog that communicates the frozen product positioning,
the authoritative version, and the bounded local/no-account/no-upload facts
(see :mod:`md_converter.gui.product_identity`).

Scope limits:

* presentation only - no setting, no control, no update check, no account or
  licence activation, no telemetry toggle and no support upload;
* the surface makes no network request and starts no process;
* ``Esc`` and ``Close`` dismiss it.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .product_identity import (
    COPYRIGHT_TEXT,
    FACT_ACCOUNT_TEXT,
    FACT_PROCESSING_TEXT,
    FACT_UPLOAD_TEXT,
    LICENSE_TEXT,
    PRODUCT_NAME,
    PRODUCT_TAGLINE,
    version_text,
)

__all__ = [
    "CLOSE_TEXT",
    "DIALOG_HEIGHT",
    "DIALOG_WIDTH",
    "TITLE_ABOUT",
    "AboutDialog",
]

#: Dialog chrome wording.
TITLE_ABOUT = f"About {PRODUCT_NAME}"
CLOSE_TEXT = "Close"

#: Stable dialog size for the bounded About surface.
DIALOG_WIDTH = 460
DIALOG_HEIGHT = 320


class AboutDialog(QDialog):
    """Read-only product information surface.

    Attributes:
        name_label: Product name.
        version_label: Authoritative version wording.
        tagline_label: Frozen product positioning.
        processing_label: Local-processing fact.
        account_label: No-account fact.
        upload_label: No-document-upload fact.
        copyright_label: Authoritative copyright line.
        license_label: Authoritative licence line.
        close_button: Dismisses the dialog.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Build the read-only product information surface.

        Args:
            parent: Optional Qt parent widget.
        """
        super().__init__(parent)
        self.setObjectName("aboutDialog")
        self.setWindowTitle(TITLE_ABOUT)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setObjectName("aboutLayout")
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(8)

        self.name_label = self._add_label(layout, "aboutNameLabel", PRODUCT_NAME, emphasis=True)
        self.version_label = self._add_label(layout, "aboutVersionLabel", version_text())
        self.tagline_label = self._add_label(
            layout, "aboutTaglineLabel", PRODUCT_TAGLINE, word_wrap=True
        )

        separator = QFrame(self)
        separator.setObjectName("aboutSeparator")
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        self.processing_label = self._add_label(
            layout, "aboutProcessingLabel", FACT_PROCESSING_TEXT
        )
        self.account_label = self._add_label(layout, "aboutAccountLabel", FACT_ACCOUNT_TEXT)
        self.upload_label = self._add_label(layout, "aboutUploadLabel", FACT_UPLOAD_TEXT)

        layout.addStretch(1)

        self.copyright_label = self._add_label(layout, "aboutCopyrightLabel", COPYRIGHT_TEXT)
        self.license_label = self._add_label(layout, "aboutLicenseLabel", LICENSE_TEXT)

        layout.addLayout(self._create_button_row())
        self.resize(DIALOG_WIDTH, DIALOG_HEIGHT)

    def _add_label(
        self,
        layout: QVBoxLayout,
        object_name: str,
        text: str,
        *,
        emphasis: bool = False,
        word_wrap: bool = False,
    ) -> QLabel:
        """Create, name and add one read-only information label.

        Args:
            layout: Parent layout.
            object_name: Stable object name for tests and assistive tooling.
            text: Label text.
            emphasis: Whether the label carries the product name.
            word_wrap: Whether long text may wrap.

        Returns:
            QLabel: The created label.
        """
        label = QLabel(text, self)
        label.setObjectName(object_name)
        label.setWordWrap(word_wrap)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        if emphasis:
            font = label.font()
            font.setBold(True)
            font.setPointSizeF(font.pointSizeF() + 2)
            label.setFont(font)
        layout.addWidget(label)
        return label

    def _create_button_row(self) -> QHBoxLayout:
        """Create the Close row."""
        row = QHBoxLayout()
        row.setObjectName("aboutButtonRow")

        self.close_button = QPushButton(CLOSE_TEXT, self)
        self.close_button.setObjectName("aboutCloseButton")
        self.close_button.setDefault(True)
        self.close_button.clicked.connect(self.accept)

        row.addStretch(1)
        row.addWidget(self.close_button)
        return row
