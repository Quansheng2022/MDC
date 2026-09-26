# WP-P12-06-02 — Failure UX

## Objective
Provide bounded GUI UX for failed conversion and worker/infrastructure failure.

## Required
- FAILED: clear failure status + concise summary + details affordance.
- JobFailure: distinguish infrastructure/internal failure; preserve original JobFailure.
- No false output actions if no valid artifact exists.
- Recovery via selecting a new valid source remains intact.

## Preferred UX
Simple main-window status/summary plus `Details...` or equivalent bounded surface.

## Forbidden
No retry/cancellation, taxonomy rewrite, raw traceback as sole UX, support-upload flow, Core diagnostic changes.

## Tests
FAILED UX, JobFailure UX, output-action gating, evidence retention, recovery, no conversion re-execution.

## Stop
STOP if usable failure UX requires changing result/Core/CLI semantics.
