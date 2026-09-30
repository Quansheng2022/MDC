# R2-V01 — Competitive Foundation Integrated Verification
## Closure Evidence

**P12 mapping:** P12-19
**Change classification:** G1 — verification program (no product change)
**Governing SPEC:** `CANONICAL_SPEC.md` (FROZEN 1.1)
**Final status:** `R2-V01 — CLOSED / ACCEPTED / SOURCE BASELINE RELEASE-GATE PASS`

## 1. Baseline / end SHA

```text
Starting HEAD (frozen baseline) : 7330b1e  (master, "IC-06 close image width configuration propagation")
Ending  HEAD (verified source)  : bd4bdf6  ("R2V01-07 classify competitive foundation release readiness")
Closure documentation commit    : "R2V01-08 close competitive foundation integrated verification" (this file)
Branch                          : master
```

No R2-V01 commit modified product/baseline source; every commit adds
verification evidence (and, for WP-06, mechanical formatting of the new
verification scripts).

## 2. Eight-commit chain

| # | Commit | Message |
|---|---|---|
| 1 | `8c264c5` | `R2V01-01 freeze competitive foundation verification baseline` |
| 2 | `2e1ca2e` | `R2V01-02 verify architecture and authority drift` |
| 3 | `5a4ec8f` | `R2V01-03 verify cross-feature document integration` |
| 4 | `0c75973` | `R2V01-04 verify application and serial batch integration` |
| 5 | `6c7662d` | `R2V01-05 verify QA determinism failure isolation and privacy` |
| 6 | `1bbf686` | `R2V01-06 run integrated regression and quality gate` |
| 7 | `bd4bdf6` | `R2V01-07 classify competitive foundation release readiness` |
| 8 | (this commit) | `R2V01-08 close competitive foundation integrated verification` |

Each work package stopped at its own boundary, verified independently,
classified failures independently, recorded independent evidence, staged exact
files only, and produced a truthful independent commit. No combined or
retrospective WP commit exists.

## 3. Files changed (baseline `7330b1e` → `bd4bdf6`)

```text
A  Doc/V2/Implementation/R2_V01/Evidence/WP-R2V01-01_BASELINE_INVENTORY_EVIDENCE.md
A  Doc/V2/Implementation/R2_V01/Evidence/WP-R2V01-02_ARCHITECTURE_DRIFT_EVIDENCE.md
A  Doc/V2/Implementation/R2_V01/Evidence/WP-R2V01-03_CROSS_FEATURE_DOCUMENT_EVIDENCE.md
A  Doc/V2/Implementation/R2_V01/Evidence/WP-R2V01-04_APPLICATION_BATCH_EVIDENCE.md
A  Doc/V2/Implementation/R2_V01/Evidence/WP-R2V01-05_QA_DETERMINISM_PRIVACY_EVIDENCE.md
A  Doc/V2/Implementation/R2_V01/Evidence/WP-R2V01-06_REGRESSION_QUALITY_EVIDENCE.md
A  Doc/V2/Implementation/R2_V01/Evidence/WP-R2V01-07_RELEASE_READINESS_EVIDENCE.md
A  Doc/V2/Implementation/R2_V01/Verification/verify_architecture_drift.py
A  Doc/V2/Implementation/R2_V01/Verification/verify_cross_feature_documents.py
A  Doc/V2/Implementation/R2_V01/Verification/verify_application_batch.py
A  Doc/V2/Implementation/R2_V01/Verification/verify_qa_determinism_privacy.py
11 files changed, 2753 insertions(+)   (closure evidence adds this file)
```

Product source touched: **none**. The three pre-existing tracked dirty files
(`.gitignore`, `README.md`, `md_converter/cli.py`) were preserved and never
staged.

## 4. Evidence index

| WP | Evidence |
|---|---|
| R2V01-01 | `Evidence/WP-R2V01-01_BASELINE_INVENTORY_EVIDENCE.md` |
| R2V01-02 | `Evidence/WP-R2V01-02_ARCHITECTURE_DRIFT_EVIDENCE.md` |
| R2V01-03 | `Evidence/WP-R2V01-03_CROSS_FEATURE_DOCUMENT_EVIDENCE.md` |
| R2V01-04 | `Evidence/WP-R2V01-04_APPLICATION_BATCH_EVIDENCE.md` |
| R2V01-05 | `Evidence/WP-R2V01-05_QA_DETERMINISM_PRIVACY_EVIDENCE.md` |
| R2V01-06 | `Evidence/WP-R2V01-06_REGRESSION_QUALITY_EVIDENCE.md` |
| R2V01-07 | `Evidence/WP-R2V01-07_RELEASE_READINESS_EVIDENCE.md` |
| R2V01-08 | `R2_V01_CLOSURE_EVIDENCE.md` (this file) |

Reproducible verification scripts: `Verification/verify_architecture_drift.py`
(9 checks), `Verification/verify_cross_feature_documents.py` (53),
`Verification/verify_application_batch.py` (16), and
`Verification/verify_qa_determinism_privacy.py` (17) — 95 scripted checks, all
passing.

## 5. Integrated feature matrix

| Capability | Result | Evidence |
|---|---|---|
| Serial Batch Conversion | PASS (strict serial, `active_conversion_count = 1`, failure isolation, profile captured) | WP-04 |
| Document Intelligence / Conversion Report | PASS (real diagnostics, surfaced warnings, accurate counts) | WP-05 |
| Professional Output Profiles | PASS (five-profile geometry matrix, resolved presentation only) | WP-03 C, WP-04 G11–G12 |
| TOC Heading Localization | PASS (English/Chinese/mixed, single authority, field intact) | WP-03 A/B |
| Advanced Table Fitting | PASS (floor, no mutation, fixed layout, irreducible case) | WP-03 A/D |
| Advanced Figure Fitting | PASS (aspect ratio, content box, page cap, reasons) | WP-03 A/D |
| IMG-CFG-01 `image_width` | PASS (respected and capped by content width) | WP-03 A/C |

## 6. Architecture drift matrix

| Invariant | Result |
|---|---|
| GUI → Worker/Application → ConversionService | PASS |
| Batch → same single-file service path | PASS |
| ConversionService → Canonical Core | PASS |
| `CompilerContext.compile()` canonical authority | PASS |
| Document Intelligence reuses QA | PASS |
| One table fitting authority | PASS |
| One figure fitting authority | PASS |
| One TOC localization authority | PASS |
| No renderer profile-ID branching | PASS |
| IMG-CFG propagation narrow | PASS |
| CLI/API/output naming unchanged | PASS |
| Protected-contract drift = 0 | PASS |

## 7. Regression totals

```text
baseline (WP-01)   : 1150 collected · 1144 passed · 2 skipped · 4 failed
grouped (WP-06)    : 907 passed · 1 skipped · 2 failed (Chromium/Golden only)
full   (WP-06)     : 1150 collected · 1144 passed · 2 skipped · 4 failed
introduced failures: 0
fixed baseline failures: 0 (none selected; unrelated/historical)
quality gate       : isort 0 · black 0 · ruff 0 on new Python files
```

## 8. Known-failure comparison

| Test | Baseline | Now | Classification |
|---|---|---|---|
| `test_packaging_metadata.py::test_pkg_documented_extras_exist_in_metadata` | fail | fail | `PRE_EXISTING_KNOWN_FAILURE` (dirty `README.md`) |
| `test_packaging_metadata.py::test_pkg_readme_has_no_legacy_packaging_references` | fail | fail | `PRE_EXISTING_KNOWN_FAILURE` (dirty `README.md`) |
| `test_golden.py::test_golden[sample]` | fail | fail | `ENVIRONMENT_FAILURE` → R2-V04 |
| `test_golden_environment.py::test_canonical_golden_environment` | fail | fail | `ENVIRONMENT_FAILURE` → R2-V04 |

The failing set is identical to the frozen baseline: no regression, no
opportunistic repair.

## 9. Environment notes

* `.pytest_cache` is ACL-inaccessible → all runs used `-p no:cacheprovider`.
* Console stdout default is `cp1252`; CLI/smoke runs set `PYTHONUTF8=1`.
* Word COM is unavailable in the sandbox; the TOC page-number refresh degrades
  gracefully and the field is still inserted.
* Chromium cannot launch (`spawn EPERM`); the Golden backend resolves to
  `fallback` (R2-V04 debt).
* `black` needed a writable `BLACK_CACHE_DIR`; `black --fast` avoided the
  py3.12-vs-py3.13 safety-check mismatch.

## 10. G1 corrections

```text
bounded G1 correction passes applied to product source : 0
  - no introduced defect was found in any WP, so no correction was required
  - WP-06 applied black/isort formatting to the four new verification scripts
    only (mechanical; the scripts were re-run afterwards and still pass)
```

## 11. Deferred items

* CLI convergence onto `ConversionService` — documented "Step C" (P12-02 §11);
  a G2-class change outside R2-V01 authority.
* Data-URI picture `name` is a per-run temp stem (decisions still deterministic;
  file-image path is byte-identical).
* DOCX twips quantization (≤ ~0.002 cm) — format property, not a fitting defect.
* True Core preflight, no-upscale policy, landscape tables, new
  profiles/config/GUI settings, templates/equations/citations/PDF, installer
  rebuild, README cleanup — out of R2-V01 scope.

## 12. Pending later gates (not closed here)

```text
Packaged runtime / multi-file runtime verification  → PENDING R2-V02
Native Word / human visual acceptance               → PENDING R2-V03
Chromium / Golden-environment retest                → PENDING R2-V04
then R2 RC → Human Acceptance → Production Release
```

## 13. Blocker count

```text
G2 AUTHORITY REQUIRED      : 0
BLOCKED                    : 0
unresolved source blockers : 0
```

## 14. Final status

R2-V01 — CLOSED / ACCEPTED / SOURCE BASELINE RELEASE-GATE PASS

The current integrated source baseline is coherent after combining Serial
Batch, Document Intelligence, Professional Output Profiles, TOC Heading
Localization, Advanced Table Fitting, Advanced Figure Fitting and the
IMG-CFG-01 image-width fix, and is eligible to proceed to the R2-V02
packaged-runtime gate. R2-V01 does not start V02 automatically.
