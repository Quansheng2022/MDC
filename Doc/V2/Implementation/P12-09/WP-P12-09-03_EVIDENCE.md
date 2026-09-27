# WP-P12-09-03 — Regression / Canonical / Golden — Completion Evidence

**Product Baseline SHA:** `38614c7bb555f96685c301bc4b6abd71138c2642`
**Specification Baseline SHA:** `08b198043ad107cdcd9293152acfa756fd6fa410`
**Input commit:** `d384800` (WP-P12-09-02)
**Authority:** verification only; no production code change

## Report record

| Field | Value |
|---|---|
| WP | WP-P12-09-03 — Regression / Canonical / Golden |
| Status | PASS |
| Input baseline SHA | `d384800` |
| Output commit SHA | recorded by the committing run (`P12-09-03 verify regression canonical and golden`) |
| Files added | this evidence file, `evidence/wp03_pytest_full.txt`, `evidence/wp03_gui_application.txt`, `evidence/wp03_canonical_golden_qa.txt` |
| Files modified | none |
| Checks executed | one full regression run + two focused area runs over the frozen source |
| Passed / Failed | 787 / 2 (both failures are the pre-existing approved exceptions) |
| Scope deviation | none |
| Stop condition | none |

## Environment

`.venv` CPython 3.12.14 with the project installed editable; `pytest` using the
project `addopts = "-ra -q --strict-markers --tb=short"`. Single mechanism, no
parallel or xdist workers.

## Full regression (run once)

```text
collected 789 tests
787 passed, 2 failed
```

Raw output: `evidence/wp03_pytest_full.txt`. The effective quiet level was
`-qq`, which suppresses pytest's terminal summary line; the counts were
recovered from the complete captured progress output (787 `.` and 2 `F` across
all `[ N%]` progress lines, total 789) and match the P12-08 record
(789 collected / 787 passed / 2 failed).

## Failure classification

| # | Test | Classification | Evidence |
|---|---|---|---|
| 1 | `test_packaging_metadata.py::test_pkg_documented_extras_exist_in_metadata` | PRE-EXISTING / APPROVED (E1) | asserts the working-tree `README.md` documents the `dev`/`mermaid`/`windows` extras; the README is a pre-existing uncommitted rewrite recorded in P12-06/P12-08 |
| 2 | `test_packaging_metadata.py::test_pkg_readme_has_no_legacy_packaging_references` | PRE-EXISTING / APPROVED (E2) | asserts `[project.entry-points` appears in the working-tree `README.md`; same pre-existing uncommitted rewrite |

Both failures are the same assertions that failed in P12-08 and are unchanged:
there is no committed change under `md_converter/` or `pyproject.toml` since the
P12-08 baseline, and the tests read the working-tree `README.md`, which already
carried an uncommitted modification before P12-09 began. No failure was
classified NEW / INTRODUCED, ENVIRONMENTAL / HARNESS or INCONCLUSIVE.

## Focused area runs

| Area | Tests | Result | Evidence |
|---|---|---|---|
| GUI suite (`tests/gui`) + Application suite (`tests/application`) | 437 | 437 passed / 0 failed | `evidence/wp03_gui_application.txt` |
| Canonical / Golden / QA / public API / config / pipeline fail-closed / release evidence | 186 | 186 passed / 0 failed | `evidence/wp03_canonical_golden_qa.txt` |

The second run includes `test_acceptance.py` (Canonical Acceptance Corpus),
`test_golden.py` (Golden regression), `test_quality_gate.py` (Static / Rendered /
FinalArtifact QA), `test_public_api_convert.py` (public API), `test_config.py`,
`test_pipeline_fail_closed.py` and `test_release_evidence.py`. All passed.

## Drift assertions

Evidence: `git diff --name-status 38614c7 HEAD` lists **only** P12-09
documentation, corpus, evidence and verification-tooling files. Nothing under
`md_converter/`, `pyproject.toml`, the packaging scripts or the golden data was
changed by P12-09.

| Drift | Required | Result | Basis |
|---|---|---|---|
| Core semantic drift | 0 | 0 | no committed change under `md_converter/`; regression identical to P12-08 |
| Canonical drift | 0 | 0 | `test_acceptance.py` passes |
| QA semantic drift | 0 | 0 | `test_quality_gate.py` passes |
| Golden drift | 0 | 0 | `test_golden.py` passes; no golden data change |
| ConversionService semantic drift | 0 | 0 | `tests/application/test_conversion_service.py` passes |
| CLI / public API breaking drift | 0 | 0 | `test_public_api_convert.py` passes; `md_converter.cli` imports and runs |

## Pre-existing working-tree change (re-checked)

`md_converter/cli.py` carries a pre-existing uncommitted, docstring-only change
(the two usage examples in `main()`'s docstring, around lines 109-113). It is
not committed, not introduced by P12-09, and non-semantic: no code, signature,
default or behaviour change. It was verified harmless (`from md_converter import
cli` imports cleanly and the public-API tests pass) and is recorded as a V0
observation, not drift.

## Defects

| Class | Count | Detail |
|---|---|---|
| V0 observations | 1 | During `test_public_api_convert.py` the Windows faulthandler reported `code 0x800706be` (`RPC_S_CALL_FAILED`) inside `post_processor._update_toc_with_word` (Word COM automation). The test still passed and the run completed; this is the known Word COM environmental flakiness already documented in P12-08. |
| V1 corrections | 1 | Evidence/harness only: the duplicated `-q` (project `addopts` plus command line) suppressed the pytest summary line, so the counts were recovered from the complete progress output and the fact is recorded rather than hidden. No source or test change. |
| V2 blockers | 0 | none |
| V3 blockers | 0 | none |

## Acceptance

| Criterion | Result |
|---|---|
| Introduced required regression failures | 0 |
| Approved exceptions unchanged | PASS |
| Canonical drift = 0 | PASS |
| Golden drift = 0 | PASS |
| QA semantic drift = 0 | PASS |
| ConversionService drift = 0 | PASS |
| Public contract / CLI breaking drift = 0 | PASS |

## Conclusion

WP-P12-09-03 passes. Packaging and productisation changed no accepted source
behaviour and no canonical document semantics: 787 of 789 tests pass and the
only two failures are the unchanged, approved README-content exceptions.
