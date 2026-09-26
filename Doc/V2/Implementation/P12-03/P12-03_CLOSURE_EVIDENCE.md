# P12-03 — Application Service Extraction: Closure Evidence

**Phase:** P12-03  
**Status:** CLOSED / ACCEPTED  
**Authority:** G1 (no G2 trigger hit)  
**Core semantic change authority:** NONE — not used  
**Golden change authority:** NONE — not used  
**Base revision:** `e025a36c645039acb1bb38208db73e8550a76156` (working tree, not committed)

---

## 1. Work package status

| WP | Scope | Status |
|---|---|---|
| WP-P12-03-01 | `ConversionRequest` | CLOSED |
| WP-P12-03-02 | `ConversionResult` | CLOSED |
| WP-P12-03-03 | `DiagnosticsAdapter` | CLOSED |
| WP-P12-03-04 | `ConversionService` | CLOSED |
| WP-P12-03-05 | Compatibility baseline | CLOSED |
| WP-P12-03-06 | Verification and closure | CLOSED |

Final decision: **P12-03 complete. P12-04 GUI Foundation may be authorised.**

---

## 2. Changed files

Added (application layer):

```text
md_converter/application/__init__.py
md_converter/application/conversion_request.py
md_converter/application/conversion_result.py
md_converter/application/diagnostics_adapter.py
md_converter/application/conversion_service.py
```

Added (application-focused tests):

```text
md_converter/tests/application/test_conversion_request.py
md_converter/tests/application/test_conversion_result.py
md_converter/tests/application/test_diagnostics_adapter.py
md_converter/tests/application/test_conversion_service.py
md_converter/tests/application/test_conversion_compatibility.py
```

Modified: **none.** No change to `cli.py`, `compiler.py`, `config.py`, `quality_gate.py`,
parser, AST, pipeline, renderer, PostProcessor, `__init__.py`, or any Golden fixture.

Pre-existing (acknowledged, not produced by P12-03): worktree modifications to
`.gitignore`, `README.md`, `md_converter/cli.py` (comment text), `pyproject.toml`
(license metadata), plus untracked baseline directories.

---

## 3. Verification layers

### V1 — Static / import

```text
import md_converter.application (+ 4 submodules)      OK
GUI modules loaded (PySide6 / PyQt5 / PyQt6)          0
GUI imports in application source                     0 (asserted by test)
second parser / renderer / QA in application layer    0 (asserted by test)
black --check --fast md_converter/application ...     clean
ruff check md_converter/application ...               clean
circular imports                                      0 (ADR layer direction application -> core)
```

### V2 — Focused application tests

```text
python -m pytest -p no:cacheprovider md_converter/tests/application -q
72 passed, 0 failed
```

Coverage (collected per module):

| Module | Tests |
|---|---|
| `test_conversion_request.py` | 17 |
| `test_conversion_result.py` | 14 |
| `test_diagnostics_adapter.py` | 14 |
| `test_conversion_service.py` | 17 |
| `test_conversion_compatibility.py` | 10 |

### V3 — Public API / CLI focused regression

```text
python -m pytest -p no:cacheprovider \
  md_converter/tests/test_public_api_convert.py md_converter/tests/test_compiler_configuration.py \
  md_converter/tests/test_config.py md_converter/tests/test_quality_gate.py \
  md_converter/tests/test_pipeline_fail_closed.py md_converter/tests/test_post_processor.py -q
47 passed, 0 failed
```

### V4 — Full required regression

```text
python -m pytest -p no:cacheprovider --junitxml=<tmp>/p12_03_full_after.xml --tb=no -q
424 tests, 422 passed, 2 failed, 0 errors, 0 skipped
```

The 2 failures are **pre-existing** and identical to the pre-change baseline
(`test_packaging_metadata::test_pkg_documented_extras_exist_in_metadata`,
`test_packaging_metadata::test_pkg_readme_has_no_legacy_packaging_references`).
Both read `README.md`/`AGENTS.md` and fail because the pre-existing worktree
README rewrite removed the documented `.[windows]`/`.[mermaid]` extras and the
`[project.entry-points` section. No P12-03 file participates in these failures.

```text
new failures introduced by P12-03 = 0
```

Environment note: the full suite must run outside the OS sandbox, because the
Golden environment requires a launchable Chromium (Playwright) and Word COM.
Inside the sandbox the pre-existing failure set grows to 2 environment-caused
failures (`test_golden`, `test_golden_environment`) — reproduced identically
before P12-03.

### V5 — Golden / Acceptance

```text
Golden baseline files modified                0 (git status)
Acceptance baseline files modified            0 (git status)
test_golden.py / test_acceptance.py           PASS (canonical environment)
Canonical semantics changed                   0
```

### V6 — Representative conversion

Source: `Doc/V2/V2_ACCEPTANCE_CRITERIA.md` (258 paragraphs, code fences), external
output directory.

| Path | Result |
|---|---|
| `ConversionService.convert()` | SUCCESS, 45 958 bytes, `artifact_sha256` `46e8527788dcf9cd…`, gates StaticQA/RenderedQA/PostProcessor/FinalArtifactQA all PASS |
| CLI (`--config word_com: false`) | exit 0, 45 957 bytes, same 258 paragraphs, no error output |

---

## 4. Regression Baseline Disposition

```text
Full regression:
424 total
422 passed
2 failed

Known pre-existing failures:
2

P12-03 introduced regression failures:
0

Baseline Exception:
APPROVED
```

The two failures existed before P12-03 implementation and are caused by
pre-existing README / packaging metadata inconsistency
(`test_pkg_documented_extras_exist_in_metadata` and
`test_pkg_readme_has_no_legacy_packaging_references`, both reading the
pre-existing modified `README.md` / `AGENTS.md`).

They are outside P12-03 implementation authority and are not to be repaired as
part of P12-03 closure. The baseline exception is authorized by the P12-03
Formal Closure Master Instruction.

---

## 5. Architecture checks

| Check | Result |
|---|---|
| GUI code added | 0 |
| Qt imports in application layer | 0 |
| Second parser / renderer / QA system | 0 |
| `CompilerContext.compile()` semantic change | 0 |
| Canonical conversion entry used | `CompilerContext.create()` + `CompilerContext.compile()` |
| Golden change | 0 |
| Diff scope | application layer + application tests only |

---

## 6. Recorded decisions and known inconsistency

* **DEC-P12-03-A (naming policy).** The service reproduces the CLI-visible
  sanitization rule (`cli.py`): every Windows-forbidden file-name character and
  every space becomes `"_"`. The CLI is the externally visible v1.1.0 behaviour
  and must not change when the CLI later converges onto the service
  (P12-02 §11 step C).
* **Known legacy inconsistency (recorded, not unified).**
  `CompilerContext.compile_file()` keeps only `[alnum, space, _, -]`. For the
  title `Q1: Draft & Notes` the two rules produce
  `Q1__Draft_&_Notes.docx` (CLI/service) versus `Q1_Draft__Notes.docx`
  (context helper). Locked by
  `test_legacy_inconsistency_between_compile_file_and_cli_naming`.
* **DEC-P12-03-B (COM evidence).** The service records optional Word COM
  degradation as the existing stable `POST002` warning, mirroring the CLI
  path (P11-MNT-006), so GUI/CLI surfaces can present it; document generation
  is unaffected.
* **DEC-P12-03-C (error-bearing outcomes).** Error-class diagnostics are never
  reported as SUCCESS: such a conversion becomes `FAILED` with the error
  evidence retained (conservative, fail-closed application boundary).
* **Out-of-scope observation (reported, not fixed).**
  `DocxPostProcessor` prints emoji via `print()`, which raises
  `UnicodeEncodeError` on a non-UTF-8 console (e.g. cp1252) and then fails
  closed as `POST001`. Pre-existing; unrelated to P12-03; not modified
  (PostProcessor changes are outside this phase's authority).

---

## 7. Closure summary

```text
P12-03 status                     CLOSED / ACCEPTED
Baseline HEAD                     e025a36 (e025a36c645039acb1bb38208db73e8550a76156)
Closure SHA                       recorded in the follow-up closure-record commit
Focused application tests         PASS (72 passed / 0 failed)
Public API + CLI                  PASS (47 passed / 0 failed)
Full regression                   422 passed / 2 known pre-existing failures
P12-03 introduced failures        0
Baseline exception                APPROVED
Golden changes                    0
Acceptance changes                0
Canonical changes                 0
CLI behavior changes              0
Unauthorized drift                0
open blockers                     0
recommended next phase            P12-04 GUI Foundation
```
