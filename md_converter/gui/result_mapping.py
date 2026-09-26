"""Centralized ``ConversionResult`` -> ``GuiState`` mapping (WP-P12-05-04).

One controlled path interprets application-layer result status
(WP-P12-05-04 §3):

    ConversionStatus.SUCCESS               -> GuiState.SUCCESS
    ConversionStatus.SUCCESS_WITH_WARNING  -> GuiState.SUCCESS_WITH_WARNING
    ConversionStatus.FAILED                -> GuiState.FAILED

No other GUI module interprets ``ConversionStatus``: worker callbacks, button
handlers and window methods only store the evidence and apply the mapped state.

An unrecognised status maps to :data:`UNMAPPED_RESULT_STATE` (fail closed: the
GUI never reports success for an outcome it cannot interpret).

The mapping is a pure lookup - it never mutates, flattens or discards result
evidence; the complete ``ConversionResult`` is retained separately for the
P12-06 diagnostics UX.  Worker infrastructure failures (``JobFailure``) are not
mapped here: they keep their own semantics and are never turned into a
fabricated ``ConversionResult``.
"""

from __future__ import annotations

from typing import Dict

from ..application.conversion_result import ConversionResult, ConversionStatus
from .state import GuiState

__all__ = ["RESULT_STATE_MAP", "UNMAPPED_RESULT_STATE", "gui_state_for_result"]

#: Single source of truth for application status -> GUI state.
RESULT_STATE_MAP: Dict[ConversionStatus, GuiState] = {
    ConversionStatus.SUCCESS: GuiState.SUCCESS,
    ConversionStatus.SUCCESS_WITH_WARNING: GuiState.SUCCESS_WITH_WARNING,
    ConversionStatus.FAILED: GuiState.FAILED,
}

#: Fail-closed state for a result the GUI cannot interpret.
UNMAPPED_RESULT_STATE = GuiState.FAILED


def gui_state_for_result(result: ConversionResult) -> GuiState:
    """Return the GUI state for ``result``.

    Args:
        result: Application-layer conversion outcome.

    Returns:
        GuiState: The mapped GUI state, or :data:`UNMAPPED_RESULT_STATE` when
        the status is not part of the application contract.
    """
    return RESULT_STATE_MAP.get(result.status, UNMAPPED_RESULT_STATE)
