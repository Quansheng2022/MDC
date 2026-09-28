"""Lightweight batch report surface for the MD_Converter GUI (SBC-05).

One read-only surface presents what the serial batch already recorded:

    BatchRun.items (retained ConversionResult / worker evidence)
            v
    batch report text + per-item rows (this module)
            v
    "View Batch Report" affordance

The aggregate text comes from :meth:`md_converter.gui.batch.BatchRun.report_text`,
which only assembles retained evidence: the source, the produced document where
there is one, the terminal status and the presentation summary.  Nothing is
recomputed, no quality gate runs again and no second result taxonomy is built.

A per-row ``Details...`` action is offered when the selected item retained
evidence; it opens the existing single-file report surface
(:func:`md_converter.gui.result_details.show_result_details`), so warning and
failure wording keeps exactly one authority.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .batch import BatchItem, BatchRun
from .result_details import show_result_details

__all__ = [
    "BATCH_ITEMS_ACCESSIBLE_NAME",
    "BATCH_REPORT_ACCESSIBLE_NAME",
    "BATCH_REPORT_TITLE",
    "CLOSE_TEXT",
    "COPY_TEXT",
    "DETAILS_TEXT",
    "ITEMS_CAPTION_TEXT",
    "REPORT_CAPTION_TEXT",
    "BatchReportDialog",
    "batch_item_row_text",
    "show_batch_report",
]

#: Dialog chrome wording (plain product language).
BATCH_REPORT_TITLE = "Batch report"
ITEMS_CAPTION_TEXT = "Files:"
REPORT_CAPTION_TEXT = "Report:"
DETAILS_TEXT = "Details..."
COPY_TEXT = "Copy"
CLOSE_TEXT = "Close"

#: Accessible names for the read-only report surfaces.
BATCH_ITEMS_ACCESSIBLE_NAME = "Batch files"
BATCH_REPORT_ACCESSIBLE_NAME = "Batch report"

#: Stable dialog size.
DIALOG_WIDTH = 760
DIALOG_HEIGHT = 560


def batch_item_row_text(item: BatchItem) -> str:
    """Return the one-line row text for ``item``.

    The status word always accompanies the marker, so the row is readable
    without colour perception (product specification §31).

    Args:
        item: Batch item to describe.

    Returns:
        str: Row text such as ``"✓ A.md — succeeded"``.
    """
    return f"{item.marker} {item.name} \u2014 {item.state_word}"


def batch_item_tooltip(item: BatchItem) -> str:
    """Return the tooltip for ``item``: the full source and output paths."""
    produced = item.output_path
    if produced is None:
        return str(item.source_path)
    return f"{item.source_path}\n{produced}"


class BatchReportDialog(QDialog):
    """Read-only batch report over one completed (or stopped) batch.

    Attributes:
        run: The batch whose retained evidence is presented.
        summary_label: Aggregate batch status line.
        items_view: Per-item rows (keyboard reachable, selectable).
        details_button: Opens the retained evidence of the selected item.
        report_view: Read-only aggregate report text.
        copy_button: Copies the report text to the clipboard.
        close_button: Dismisses the dialog.
    """

    def __init__(self, run: BatchRun, parent: Optional[QWidget] = None) -> None:
        """Build the report surface for ``run``.

        Args:
            run: The batch to present.
            parent: Optional Qt parent widget.
        """
        super().__init__(parent)
        self.setObjectName("batchReportDialog")
        self.setWindowTitle(BATCH_REPORT_TITLE)
        self._run = run
        self._report_text = run.report_text()

        layout = QVBoxLayout(self)
        layout.setObjectName("batchReportLayout")
        layout.setSpacing(10)

        self.summary_label = QLabel(run.status_line(), self)
        self.summary_label.setObjectName("batchReportSummaryLabel")
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)

        items_caption = QLabel(ITEMS_CAPTION_TEXT, self)
        items_caption.setObjectName("batchReportItemsCaption")
        layout.addWidget(items_caption)

        self.items_view = QListWidget(self)
        self.items_view.setObjectName("batchReportItemsView")
        self.items_view.setAccessibleName(BATCH_ITEMS_ACCESSIBLE_NAME)
        self.items_view.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        for item in run.items:
            row = QListWidgetItem(batch_item_row_text(item))
            row.setToolTip(batch_item_tooltip(item))
            self.items_view.addItem(row)
        self.items_view.setCurrentRow(0)
        self.items_view.itemSelectionChanged.connect(self._refresh_details)
        layout.addWidget(self.items_view)

        report_caption = QLabel(REPORT_CAPTION_TEXT, self)
        report_caption.setObjectName("batchReportTextCaption")
        layout.addWidget(report_caption)

        self.report_view = QPlainTextEdit(self)
        self.report_view.setObjectName("batchReportTextView")
        self.report_view.setPlainText(self._report_text)
        self.report_view.setReadOnly(True)
        self.report_view.setAccessibleName(BATCH_REPORT_ACCESSIBLE_NAME)
        self.report_view.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        layout.addWidget(self.report_view, 1)

        button_row = QHBoxLayout()
        self.details_button = QPushButton(DETAILS_TEXT, self)
        self.details_button.setObjectName("batchReportDetailsButton")
        self.details_button.setAccessibleName(DETAILS_TEXT)
        self.details_button.clicked.connect(self.show_selected_details)
        button_row.addWidget(self.details_button)
        button_row.addStretch(1)
        self.copy_button = QPushButton(COPY_TEXT, self)
        self.copy_button.setObjectName("batchReportCopyButton")
        self.copy_button.setAccessibleName(COPY_TEXT)
        self.copy_button.clicked.connect(self._copy_report)
        button_row.addWidget(self.copy_button)
        self.close_button = QPushButton(CLOSE_TEXT, self)
        self.close_button.setObjectName("batchReportCloseButton")
        self.close_button.setAccessibleName(CLOSE_TEXT)
        self.close_button.clicked.connect(self.accept)
        button_row.addWidget(self.close_button)
        layout.addLayout(button_row)

        self.setTabOrder(self.items_view, self.report_view)
        self.setTabOrder(self.report_view, self.details_button)
        self.setTabOrder(self.details_button, self.copy_button)
        self.setTabOrder(self.copy_button, self.close_button)
        self._refresh_details()
        self.resize(DIALOG_WIDTH, DIALOG_HEIGHT)

    @property
    def run(self) -> BatchRun:
        """Return the batch presented by this surface."""
        return self._run

    @property
    def report_text(self) -> str:
        """Return the read-only aggregate report text."""
        return self._report_text

    def selected_item(self) -> Optional[BatchItem]:
        """Return the currently selected batch item, if any."""
        row = self.items_view.currentRow()
        items = self._run.items
        if row < 0 or row >= len(items):
            return None
        return items[row]

    def _refresh_details(self) -> None:
        """Enable the details action only when the selection retained evidence."""
        item = self.selected_item()
        available = bool(item is not None and item.presentation is not None and item.evidence)
        self.details_button.setEnabled(available)

    def show_selected_details(self) -> bool:
        """Open the retained evidence of the selected item.

        Returns:
            bool: ``True`` when the details surface was shown.
        """
        item = self.selected_item()
        if item is None or item.presentation is None or item.evidence is None:
            return False
        show_result_details(self, item.presentation, item.evidence)
        return True

    def _copy_report(self) -> None:
        """Copy the report text to the system clipboard (no export, no upload)."""
        clipboard = QApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(self._report_text)


def show_batch_report(parent: Optional[QWidget], run: BatchRun) -> BatchReportDialog:
    """Open the read-only batch report surface.

    Args:
        parent: Parent window for the dialog.
        run: The batch to present.

    Returns:
        BatchReportDialog: The dialog that was shown (already dismissed).
    """
    dialog = BatchReportDialog(run, parent)
    dialog.exec()
    return dialog
