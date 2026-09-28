# WP-DI-04 — Conversion Report Strengthening

**Program:** Document Intelligence Upgrade
**Baseline:** `DOCUMENT_INTELLIGENCE_ARCHITECTURE_BASELINE.md` (WP-DI-01)
**Change classification:** G1 — additive report structure

## Scope

Make the conversion report answer the product questions of the specification §7
in a deterministic order, using the preflight model as the only finding source.

## Report structure

```text
<outcome title>

Status: <outcome>
Summary: <retained wording>
Output path: <authoritative output_path>        (only when an artifact exists)

Quality findings (N)                            (grouped, severity-ordered)
Warnings (N)                                    (retained severity list)
Errors (N)                                      (retained severity list)
Diagnostics (N)                                 (traceability list, [SEV] CODE: wording)
Degraded or unsupported items (N)               (only when present)
Diagnostic summary                              (retained counts + wording)
Suggested review                                (only when findings warrant it)
Quality gate report                             (retained canonical evidence)
Technical detail                                (retained raw evidence, last)
```

Mapping to the implementation plan: `Status` → Status; `Output path` → Output
Artifact; `Summary` → Summary; `Warnings` → Warnings; `Quality findings` →
Quality / Preflight Findings; `Degraded or unsupported items` → Degraded /
Unsupported Items; `Suggested review` → Suggested Review; `Diagnostics`,
`Diagnostic summary`, `Quality gate report`, `Technical detail` → Technical
Details (secondary).

## Rules implemented

* the authoritative output path is used verbatim (no path is derived);
* counts are derived from the retained evidence and equal the authoritative
  counts;
* grouping is deterministic and severity-ordered;
* the diagnostics traceability list is rendered from the normalised preflight
  items, so an unexpected presentation record cannot break the report;
* review guidance only points at findings the report already renders — it adds
  no finding, severity or quality judgement;
* the technical detail (including any traceback) is always the last block;
* existing output actions and their path authority are untouched.

## Verification

```text
pytest md_converter/tests/gui/test_document_intelligence_report.py  -> 9 passed
pytest md_converter/tests/gui/test_report_view.py                   -> PASS (unchanged guards)
pytest md_converter/tests/gui                                      -> PASS
ruff / black / isort                                               -> clean
```

Covered: leading status/summary/output block; grouping and order of findings;
degraded section; bounded review guidance (and its absence when clean);
technical detail last; preserved traceability layers; counts matching the
authoritative summary; determinism and non-mutation; warning presentation stays
successful.

## Compatibility

Every accepted P12-06 report assertion still passes: the layered structure
(overview → severity lists → raw traceability) is inherited, not replaced, and
the layered rendering is deliberate — the overview is product-facing, the raw
list is support-facing.  No wording authority is duplicated.
