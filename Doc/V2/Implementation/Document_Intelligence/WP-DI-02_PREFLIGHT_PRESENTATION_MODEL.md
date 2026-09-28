# WP-DI-02 — Preflight Presentation Model

**Program:** Document Intelligence Upgrade
**Baseline:** `DOCUMENT_INTELLIGENCE_ARCHITECTURE_BASELINE.md` (WP-DI-01)
**Change classification:** G1 — additive presentation layer

## Scope

Create one Qt-free presentation model that turns retained authoritative
diagnostics into a grouped, ordered, counted quality view.  The model is the
single presentation authority for the preflight panel and the report's quality
sections.

## Implementation

| Artifact | Purpose |
|---|---|
| `md_converter/gui/preflight_model.py` | `PreflightItem` / `PreflightSummary` plus `preflight_from_diagnostics()` and `preflight_from_result()`. |
| `md_converter/tests/gui/test_preflight_model.py` | 21 focused tests. |

Rules implemented (plan §6):

* counts are **derived from the items** (`total` / `error_count` /
  `warning_count` / `info_count` are properties), so presented counts always
  equal the authoritative counts;
* diagnostic identity is preserved (`severity`, `code`, technical `detail`,
  `source`, `location`);
* no QA logic: the module imports the application boundary only and never a
  compiler stage or Qt;
* deterministic ordering: errors (`ERROR`/`FATAL`) first, then `WARNING`, then
  informational items, with the authoritative order preserved inside a group
  (stable sort);
* wording: per-finding wording is the adapter's `user_message`; only
  counts-only wording is composed here, and the retained
  `DiagnosticSummary.user_message` is passed through verbatim when present;
* degradation grouping (`POST002`, `MD001`, `MD004`, `DIAG001`–`DIAG003`) only
  *selects* existing findings that already report a degraded outcome;
* no duplicate suppression: one retained record produces exactly one finding.

## Verification

```text
pytest md_converter/tests/gui/test_preflight_model.py  -> 21 passed
ruff check md_converter/gui                           -> clean
black --check / isort --check-only                    -> clean
```

Covered: no issues; info-only; warning-only; mixed severities; count
correctness against `DiagnosticSummary`; derived counts; stable and
deterministic ordering; row text; technical evidence secondary; degradation
grouping; result adapter; retained wording; failed results; missing
diagnostics; evidence not mutated; malformed / unexpected presentation input;
unknown severity; Qt-free and Core-free imports.

## Drift

No production module outside `md_converter/gui/preflight_model.py` is touched
by this work package.  No Core, Canonical, QA, Golden, CLI or public API
semantic changes.
