# WP-DI-06 — Failure / Accessibility / UX Hardening

**Program:** Document Intelligence Upgrade
**Baseline:** `DOCUMENT_INTELLIGENCE_ARCHITECTURE_BASELINE.md` (WP-DI-01)
**Change classification:** G1 — hardening and verification

## Failure cases covered

| Case | Result |
|---|---|
| Missing source | `FAILED` / `INPUT_ERROR`; bounded report; no leading traceback; no findings invented. |
| Unreadable source (invalid UTF-8) | `FAILED` / `INPUT_ERROR`; retained technical evidence stays last. |
| Directory used as a source | Refused at the GUI boundary; no result, no panel, no crash. |
| No diagnostics at all | Clean summary; no quality section; no review guidance. |
| Malformed / unexpected diagnostic input | Every malformed record degrades to an informational item; counts stay consistent; the report still renders. |
| Missing output artifact | Reported with its retained path; no output action is offered. |
| Report after failure | Status and findings lead; the traceback is last. |
| Batch partial failure | Each file keeps its own report (WP-DI-05). |

## Accessibility and UX guardrails

* keyboard: the visible panel is in the workflow Tab chain, a hidden one is
  skipped, and the list carries a `StrongFocus` policy;
* textual severity: every row names its severity, so no meaning depends on
  colour, and the window sets no stylesheet or palette;
* long text: wording is preserved verbatim in the model (the view wraps or
  elides, the evidence never is);
* layout: the section is placed by the shared layout, never by absolute
  geometry, and stays inside the window rectangle;
* no duplicate flood: a finding appears once inside a presentation group;
* warnings never look fatal; the retained evidence stays secondary.

## Verification

```text
pytest md_converter/tests/gui/test_document_intelligence_hardening.py  -> 10 passed
pytest md_converter/tests/gui/test_accessibility_window.py             -> PASS (unchanged)
```
