# WP-R2V01-05 — QA / Determinism / Failure Isolation / Privacy

**Program:** R2-V01 — Competitive Foundation Integrated Verification (P12-19)
**Work package:** R2V01-05
**Change classification:** G1 — verification only
**Governing SPEC:** `CANONICAL_SPEC.md` (FROZEN 1.1) — SPEC-GOAL-003,
SPEC-GOAL-005, SPEC-INV-003
**Baseline:** `7330b1e` (`master`)
**Status:** PASS — 17/17 checks

## 1. Objective

Prove there is no second QA authority; the Conversion Report reflects the real
diagnostics; the irreducible-wide-table warning stays surfaced; a failed
conversion does not poison later conversions; repeated identical source/config
preserves table, figure, TOC, profile and diagnostic decisions; and the existing
approved source-level privacy/network check passes.

## 2. Method

`Verification/verify_qa_determinism_privacy.py`:

* instruments the compiler's QA constructors to count instantiations per
  conversion (runtime proof of a single QA authority);
* builds the GUI Conversion Report from a real `ConversionResult` and asserts
  it contains the real diagnostic message;
* runs a failure followed by a valid conversion on **one** service instance;
* repeats an identical mixed document three times per profile and compares the
  observable decisions;
* re-runs the existing approved privacy guard
  (`tests/gui/test_about_dialog.py`) and re-applies its method at package scope.

## 3. Results

```text
R2-V01 WP-05 QA / DETERMINISM / FAILURE ISOLATION / PRIVACY
checks=17 failed=0
```

### QA authority and report fidelity

| Check | Measurement |
|---|---|
| Q1 single QA authority | per conversion `StaticQA=1`, `RenderedQA=1`, `FinalArtifactQA=1` |
| Q2 quality gate | report keys `static_qa · rendered_qa · post_processor · final_artifact_qa (+ policy, repair_evidence, artifact_sha256)` |
| Q3 report reflects real diagnostics | the exact `RENDER006` message appears verbatim in the Conversion Report (`build_report_text`) |
| Q4 wide-table warning surfaced | report shows `⚠ WARNING — Table cannot fit the effective content width … (3 warnings)` |
| Q5 preflight counts | `total=3`, `warnings=3` — derived from the real records, not fabricated |

### Failure isolation

| Check | Measurement |
|---|---|
| R1 | empty source → `FAILED` (`CONVERSION_ERROR`) |
| R2 | the next conversion on the **same** service → `SUCCESS`, no diagnostics, artifact written |
| R3 | later quality gate is `PASS` at every stage (no leaked FAIL) |

### Determinism of decisions (3 repeats each)

| Profile | table widths (cm) | figure (cm) | TOC | margins (L,R) |
|---|---|---|---|---|
| professional_report | `[1.7992 ×5, 2.8487, 1.7992, 2.2789]` | `12.7 × 3.175` (4:1) | `目录` | `2.54, 2.54` |
| academic | `[1.6951 ×5, 2.6829, 1.6951, 2.1467]` | `12.7 × 3.175` | `目录` | `3.0, 3.0` |

All three repeats are identical: table decisions, figure decisions, TOC
localization, profile resolution and the (empty) diagnostic set are preserved.

### Privacy (approved check re-used)

| Check | Measurement |
|---|---|
| P1 | existing approved privacy/network guard `tests/gui/test_about_dialog.py` → 14 passed |
| P2 | no network-client import (`socket`/`http`/`requests`/`httpx`/`aiohttp`/`ftplib`/`smtplib`/`telnetlib`/`webbrowser`) anywhere in the production package |
| P3 | the only process/URL-parsing imports stay at the accepted baseline set: `diagram_pass.py:subprocess` (local `mmdc`), `word_writer.py:urllib.parse` (`unquote_to_bytes` on a data URI), `helpers.py:subprocess` (OS document opener) |

## 4. Observations (pre-existing, not repaired)

1. The determinism statement is about **decisions**, which are byte-stable at
   the decision level. The one byte-level variation observed in WP-R2V01-03 (the
   data-URI picture `name`) persists but does not change TOC, geometry, widths,
   profile resolution or diagnostics. Pre-existing; recorded, not repaired.
2. `subprocess`/`urllib.parse` usages above are documented local behaviours
   (Mermaid CLI, data-URI decode, document opener); no network client exists.
   They are outside the approved privacy guard's scope and are unchanged.

## 5. WP conclusion

**PASS.** 17/17 checks. There is a single QA authority (each stage runs exactly
once per conversion); the Conversion Report carries the real diagnostics and
the wide-table warning remains surfaced; failures do not poison later
conversions; decisions are deterministic across repeats and profiles; and the
approved privacy/network posture is unchanged. No G2 condition and no BLOCKED
condition was encountered. Pipeline continues to R2V01-06.
