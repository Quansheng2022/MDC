"""Compatibility alias for the WP-P12-06-02 failure-details surface.

WP-P12-06-03 generalized that bounded surface into
:mod:`md_converter.gui.result_details`, so warning evidence can be shown without
being mislabelled as a failure.  This module is a re-export alias only - it holds
no implementation of its own, so there is still exactly one details surface.

Kept for backward compatibility with the WP-P12-06-02 call sites and tests;
WP-P12-06-04 (the full diagnostics/report view) is expected to retire it.
"""

from __future__ import annotations

from .result_details import (
    CLOSE_TEXT,
    EVIDENCE_CAPTION_TEXT,
    TITLE_FAILURE_DETAILS,
    ResultDetailsDialog,
    presentation_evidence_text,
    show_result_details,
)

#: Failure dialog title (WP-P12-06-02 name for the failure-specific label).
DETAILS_TITLE = TITLE_FAILURE_DETAILS

#: WP-P12-06-02 names for the generalized surface.
FailureDetailsDialog = ResultDetailsDialog
failure_evidence_text = presentation_evidence_text
show_failure_details = show_result_details

__all__ = [
    "CLOSE_TEXT",
    "DETAILS_TITLE",
    "EVIDENCE_CAPTION_TEXT",
    "FailureDetailsDialog",
    "failure_evidence_text",
    "show_failure_details",
]
