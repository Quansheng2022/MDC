# WP-P12-09-05 — Failure / Recovery / Usability

**Product Baseline:** `38614c7`

## Objective

Verify negative paths and desktop usability without expanding behavior.

## Failure / Recovery Matrix

Verify representative cases:

- missing source;
- invalid source selection;
- unavailable/locked output;
- conversion failure;
- warning outcome;
- missing output artifact;
- stale remembered directory;
- invalid/off-screen geometry;
- worker-active close attempt;
- subsequent recovery to usable state.

## Word Lock

A Word-held output may produce `OUTPUT_ERROR`.

Verify fail-closed behavior only.
Do not add rename/retry/overwrite semantics.

## Lifecycle

Verify:

- no duplicate active jobs;
- controls remain safe during conversion;
- close blocked while worker active;
- close succeeds after idle;
- sequential conversions remain usable.

## Keyboard / Accessibility

Verify logical Tab order, `Ctrl+O`, `Ctrl+,`, Esc close, accessible names, report keyboard access, and non-color-only status communication.

## High DPI

Perform bounded real-platform smoke at representative scaling.

## Acceptance

Negative paths fail safely, recovery succeeds, lifecycle remains safe, and desktop usability baseline passes.
