# WP-P12-06-03 — Warning UX

## Objective
Provide clear UX for `SUCCESS_WITH_WARNING` without treating it as failure.

## Required
- Preserve SUCCESS_WITH_WARNING semantics.
- Concise warning summary visible.
- Detailed warning evidence accessible.
- Valid output remains actionable when present.

## Forbidden
No warning→error transformation, warning suppression, warning scoring, QA threshold changes, retry/cancellation, or result mutation.

## Tests
Warning state preserved, summary/details available, artifact eligibility preserved, warning evidence intact, FAILED UX not used.

## Stop
STOP if warning UX requires changing QA or result semantics.
