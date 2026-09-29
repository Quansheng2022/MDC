"""Explicit GUI state model for MD_Converter (WP-P12-04-03).

Presentation states for the desktop workflow (``V2_GUI_UX_SPEC`` §4):

    EMPTY -> READY -> CONVERTING -> SUCCESS | SUCCESS_WITH_WARNING | FAILED
                                        |
                                        +-> new source / reset -> READY

These are GUI presentation/workflow states.  They are deliberately distinct
from the P12-03 ``ConversionResult`` statuses and must never be stored in the
application or Core layer (WP-P12-04-03 §11).

The module is Qt-free on purpose: it is a pure Python state machine, so the
workflow can be unit-tested without a GUI runtime, and widget state is applied
from :data:`STATE_EFFECTS` by exactly one path in ``MainWindow``
(WP-P12-04-03 §7).

Real conversion is not authorized in P12-04, so the ``complete_*`` transitions
are reached from the GUI through the ``simulate_*`` verification hooks.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional

__all__ = [
    "STATE_EFFECTS",
    "STATUS_CONVERTING",
    "STATUS_EMPTY",
    "STATUS_FAILED",
    "STATUS_READY",
    "STATUS_SUCCESS",
    "STATUS_SUCCESS_WITH_WARNING",
    "GuiState",
    "GuiStateModel",
    "StateEffect",
]


class GuiState(str, Enum):
    """GUI presentation states (``V2_GUI_UX_SPEC`` §4)."""

    EMPTY = "EMPTY"
    READY = "READY"
    CONVERTING = "CONVERTING"
    SUCCESS = "SUCCESS"
    SUCCESS_WITH_WARNING = "SUCCESS_WITH_WARNING"
    FAILED = "FAILED"

    def __str__(self) -> str:
        """Return the stable state value (independent of Python version)."""
        return self.value


#: Status-area wording per state (WP-P12-04-03 §6).  Plain product language.
STATUS_EMPTY = "Ready"
STATUS_READY = "Ready to convert."
STATUS_CONVERTING = "Converting\u2026"
STATUS_SUCCESS = "Conversion completed."
STATUS_SUCCESS_WITH_WARNING = "Conversion completed with warnings."
STATUS_FAILED = "Conversion failed."

#: States that finish a conversion (WP-P12-04-03 §4).
_COMPLETION_STATES = (
    GuiState.SUCCESS,
    GuiState.SUCCESS_WITH_WARNING,
    GuiState.FAILED,
)


@dataclass(frozen=True)
class StateEffect:
    """Widget effects implied by one GUI state.

    Attributes:
        status_text: Text shown in the status area.
        convert_enabled: Whether the primary Convert action is available.
        select_enabled: Whether the Select File control is available.
        drop_enabled: Whether the input (drop) area is available for input.
        change_output_enabled: Whether the output folder may be changed.
        profile_enabled: Whether the output-profile selection may be changed.
            A profile is captured once per conversion/batch, so the selection is
            locked exactly while a conversion runs and the frozen choice cannot
            be changed underneath the running job (Program C: WP-POP-05).
        source_visible: Whether the selected source is displayed.

    The ``drop_enabled`` flag governs input *availability*.  Drag & drop
    acceptance itself belongs to WP-P12-04-05.
    """

    status_text: str
    convert_enabled: bool
    select_enabled: bool
    drop_enabled: bool
    change_output_enabled: bool
    source_visible: bool
    profile_enabled: bool = True


#: Single source of truth for widget state per GUI state (WP-P12-04-03 §6/§7).
STATE_EFFECTS: Dict[GuiState, StateEffect] = {
    GuiState.EMPTY: StateEffect(
        status_text=STATUS_EMPTY,
        convert_enabled=False,
        select_enabled=True,
        drop_enabled=True,
        change_output_enabled=True,
        source_visible=False,
        profile_enabled=True,
    ),
    GuiState.READY: StateEffect(
        status_text=STATUS_READY,
        convert_enabled=True,
        select_enabled=True,
        drop_enabled=True,
        change_output_enabled=True,
        source_visible=True,
        profile_enabled=True,
    ),
    GuiState.CONVERTING: StateEffect(
        status_text=STATUS_CONVERTING,
        convert_enabled=False,
        select_enabled=False,
        drop_enabled=False,
        change_output_enabled=False,
        source_visible=True,
        profile_enabled=False,
    ),
    GuiState.SUCCESS: StateEffect(
        status_text=STATUS_SUCCESS,
        convert_enabled=False,
        select_enabled=True,
        drop_enabled=True,
        change_output_enabled=True,
        source_visible=True,
        profile_enabled=True,
    ),
    GuiState.SUCCESS_WITH_WARNING: StateEffect(
        status_text=STATUS_SUCCESS_WITH_WARNING,
        convert_enabled=False,
        select_enabled=True,
        drop_enabled=True,
        change_output_enabled=True,
        source_visible=True,
        profile_enabled=True,
    ),
    GuiState.FAILED: StateEffect(
        status_text=STATUS_FAILED,
        convert_enabled=False,
        select_enabled=True,
        drop_enabled=True,
        change_output_enabled=True,
        source_visible=True,
        profile_enabled=True,
    ),
}


class GuiStateModel:
    """Explicit GUI state holder with deterministic, centralized transitions.

    Args:
        source: Optional initial source label.  A non-empty value starts the
            model in ``READY``; otherwise it starts in ``EMPTY``.

    Every transition returns the resulting state, so callers never have to
    guess whether a request was accepted.  Invalid or unavailable transitions
    are rejected by leaving the state unchanged.
    """

    def __init__(self, source: Optional[str] = None) -> None:
        self._source: Optional[str] = None
        self._state: GuiState = GuiState.EMPTY
        if source:
            self.set_source(source)

    @property
    def state(self) -> GuiState:
        """Return the current GUI state."""
        return self._state

    @property
    def source(self) -> Optional[str]:
        """Return the selected source label, or ``None`` when nothing is selected."""
        return self._source

    @property
    def effect(self) -> StateEffect:
        """Return the presentation effects of the current state."""
        return STATE_EFFECTS[self._state]

    def set_source(self, source: Optional[str]) -> GuiState:
        """Select ``source`` and move to ``READY``.

        A blank or ``None`` source clears the selection and returns to
        ``EMPTY``.  Source changes during ``CONVERTING`` are ignored so that an
        in-flight conversion cannot be switched underneath the user
        (``V2_GUI_UX_SPEC`` §4.3).

        Args:
            source: Display label of the selected source (typically a file
                name or path).

        Returns:
            GuiState: The state after the request.
        """
        if self._state is GuiState.CONVERTING:
            return self._state
        text = (source or "").strip()
        if not text:
            return self.reset()
        self._source = text
        self._state = GuiState.READY
        return self._state

    def reset(self) -> GuiState:
        """Clear the selection and return to ``EMPTY``.

        Returns:
            GuiState: The state after the request (unchanged while converting).
        """
        if self._state is GuiState.CONVERTING:
            return self._state
        self._source = None
        self._state = GuiState.EMPTY
        return self._state

    def request_convert(self) -> GuiState:
        """Move ``READY`` -> ``CONVERTING``.

        Requests from any other state are rejected (the request returns the
        unchanged state), which is what prevents duplicate conversion starts.

        Returns:
            GuiState: The state after the request.
        """
        if self._state is GuiState.READY:
            self._state = GuiState.CONVERTING
        return self._state

    def complete_success(self) -> GuiState:
        """Move ``CONVERTING`` -> ``SUCCESS``.

        Returns:
            GuiState: The state after the transition.
        """
        return self.complete(GuiState.SUCCESS)

    def complete_warning(self) -> GuiState:
        """Move ``CONVERTING`` -> ``SUCCESS_WITH_WARNING``.

        Returns:
            GuiState: The state after the transition.
        """
        return self.complete(GuiState.SUCCESS_WITH_WARNING)

    def complete_failure(self) -> GuiState:
        """Move ``CONVERTING`` -> ``FAILED``.

        Returns:
            GuiState: The state after the transition.
        """
        return self.complete(GuiState.FAILED)

    def complete(self, state: GuiState) -> GuiState:
        """Apply a completion transition when the model is ``CONVERTING``.

        This is the generic entry used by the centralized ``ConversionResult``
        -> ``GuiState`` mapping (WP-P12-05-04); the named ``complete_success`` /
        ``complete_warning`` / ``complete_failure`` helpers remain for the
        P12-04 mock hooks and existing callers.

        Args:
            state: Completion state to apply.

        Returns:
            GuiState: The state after the request.

        Raises:
            ValueError: ``state`` is not a completion state.
        """
        if state not in _COMPLETION_STATES:
            raise ValueError(f"{state} is not a completion state")
        if self._state is GuiState.CONVERTING:
            self._state = state
        return self._state

    def complete_batch(self) -> GuiState:
        """Move ``CONVERTING`` -> ``READY`` after a multi-file batch finished.

        A serial batch aggregates several independent results, so no single
        completion state applies to it.  The batch layer keeps its own summary
        presentation, and the workflow returns to ``READY`` with the same
        effects: the selection is still shown, Convert is available again and
        the next batch can start.  No new GUI state is introduced for batch
        mode (``V2_GUI_UX_SPEC`` §4 freezes the state list).

        Returns:
            GuiState: The state after the request (unchanged when the model is
            not ``CONVERTING``).
        """
        if self._state is GuiState.CONVERTING:
            self._state = GuiState.READY
        return self._state
