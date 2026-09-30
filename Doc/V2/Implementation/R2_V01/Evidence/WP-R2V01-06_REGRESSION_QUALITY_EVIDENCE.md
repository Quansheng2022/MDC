# WP-R2V01-06 — Integrated Regression & Quality Gate

**Program:** R2-V01 — Competitive Foundation Integrated Verification (P12-19)
**Work package:** R2V01-06
**Change classification:** G1 — verification + quality gate (formatting of the
new verification scripts only; no product source change)
**Governing SPEC:** `CANONICAL_SPEC.md` (FROZEN 1.1) — SPEC-GOAL-003,
SPEC-GOAL-005
**Baseline:** `7330b1e` (`master`)
**Status:** PASS — introduced failures = 0

## 1. Objective

Run the integrated regression set once near closure, then the full suite once,
classify the known README and Chromium failures, and run `ruff`, `black
--check` and `isort --check-only` on the touched/new Python files. Required:
`introduced failures = 0`.

## 2. Method

* Grouped run over: Competitive Foundation features (profiles, TOC localization,
  language detection, table/figure fitting, IMG-CFG image width,
  cross-profile), application/GUI/Serial Batch, Document Intelligence, THL,
  table/figure, CLI/public API and acceptance/Golden.
* Full suite once (`-p no:cacheprovider`).
* Quality gate on the R2-V01 verification scripts with a writable
  `BLACK_CACHE_DIR`.

## 3. Grouped regression result

```text
pytest (application + gui + profiles + THL + fitting + IMG-CFG + CLI/API + acceptance/Golden)
2 failed, 907 passed, 1 skipped in 151.31s

FAILED md_converter/tests/test_golden.py::test_golden[sample]
FAILED md_converter/tests/test_golden_environment.py::test_canonical_golden_environment
```

## 4. Full-suite result (run once)

```text
pytest -p no:cacheprovider -rf --tb=no
4 failed, 1144 passed, 2 skipped in 169.84s (1150 collected)

FAILED md_converter/tests/test_golden.py::test_golden[sample]
FAILED md_converter/tests/test_golden_environment.py::test_canonical_golden_environment
FAILED md_converter/tests/test_packaging_metadata.py::test_pkg_documented_extras_exist_in_metadata
FAILED md_converter/tests/test_packaging_metadata.py::test_pkg_readme_has_no_legacy_packaging_references
```

## 5. Failure classification (every baseline failure accounted for)

| Test | Category | Classification | Repair |
|---|---|---|---|
| `test_packaging_metadata.py::test_pkg_documented_extras_exist_in_metadata` | README packaging (dirty working-tree `README.md`) | `PRE_EXISTING_KNOWN_FAILURE` | no (unrelated historical dirty file) |
| `test_packaging_metadata.py::test_pkg_readme_has_no_legacy_packaging_references` | README packaging (dirty working-tree `README.md`) | `PRE_EXISTING_KNOWN_FAILURE` | no |
| `test_golden.py::test_golden[sample]` | Chromium `spawn EPERM` → backend `fallback` | `ENVIRONMENT_FAILURE` → `LATER_RELEASE_GATE_DEBT` (R2-V04) | no |
| `test_golden_environment.py::test_canonical_golden_environment` | Chromium `spawn EPERM` | `ENVIRONMENT_FAILURE` → `LATER_RELEASE_GATE_DEBT` (R2-V04) | no |

```text
baseline failing set (WP-R2V01-01) = 4
current  failing set              = 4
introduced failures               = 0
fixed baseline failures           = 0 (none selected for repair; unrelated/historical)
```

No other test changed status; no test was added to or removed from the suite by
R2-V01 (the verification scripts live outside `testpaths`).

## 6. Quality gate on touched/new Python files

Touched product source: **none** (all 8 R2-V01 work packages are verification
only; the three tracked dirty files `.gitignore`, `README.md`,
`md_converter/cli.py` are pre-existing and untouched). New Python files: the
four R2-V01 verification scripts, which this WP formatted and checked.

```text
$env:BLACK_CACHE_DIR=<writable temp>

isort --check-only <4 verification scripts>   -> rc=0
black --fast --check  <4 verification scripts> -> rc=0 (4 files left unchanged)
ruff check            <4 verification scripts> -> rc=0 (All checks passed!)
```

Formatting changes applied by this WP (mechanical only, no behaviour change):
`verify_application_batch.py`, `verify_architecture_drift.py`,
`verify_cross_feature_documents.py`, `verify_qa_determinism_privacy.py`.
All four scripts were re-run after formatting and still pass
(9 / 16 / 53 / 17 checks respectively; 0 failures).

## 7. WP conclusion

**PASS.** `introduced failures = 0`; the full-suite failing set exactly equals
the frozen baseline of 4 (2 README packaging + 2 Chromium/Golden), all causally
excluded, none repaired opportunistically. Quality gate is clean. No G2
condition and no BLOCKED condition was encountered. Pipeline continues to
R2V01-07.
