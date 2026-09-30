# R2-V02 — Packaged Multi-file Runtime Verification
## Closure Evidence

**Program:** R2-V02 (P12-20) — Packaged/installed Windows runtime release gate
**Change classification:** G2_OR_RELEASE — release verification (no product change)
**Governing SPEC:** `CANONICAL_SPEC.md` (FROZEN 1.1) — `SPEC-GOAL-003`,
`SPEC-GOAL-006`, `SPEC-FUNC-011`, `SPEC-FUNC-023`, `SPEC-INV-001`,
`SPEC-INV-003`, `SPEC-INV-005`, `SPEC-ARCH-007`
**Final status:** `R2-V02 — CLOSED / ACCEPTED / PACKAGED RUNTIME RELEASE-GATE PASS`

## 1. Baseline and package identity

| Item | Value |
|---|---|
| Branch | `master` |
| Accepted source baseline | `1e1cfc7062736a687147e642442677d24144204f` (R2-V01 closure, "R2V01-08 close competitive foundation integrated verification") |
| Last product-source commit | `bd1a818` 2026-09-30 11:34:26 +0800 `IC-04 guard image width configuration contract` |
| Pre-existing release package | `dist_installer/MD_Converter_v1.1.0_Setup.exe`, SHA-256 `EFEC378F11B00A53791158199B4DC98AA09F44F5B1F013363FF744A92B91B9BF`, built 2026-09-27 21:04:45 — **not reused** (built before the product-source commits of 2026-09-29/30) |
| Verification package | built with the frozen packaging pipeline: `MD_Converter_Lite.spec` (PyInstaller 6.22.3, Python 3.12.14) |
| Executable SHA-256 | `68524527CDC5718CE31A1F0454EAFB0FF64C52D5C838716AC1277445DE0E3021` (identical for the built payload and the installed executable) |
| Executable version metadata | FileVersion / ProductVersion `1.1.0`, ProductName `MD Converter`, CompanyName `Quansheng2022` |
| Install path | `%LOCALAPPDATA%\Programs\MD_Converter\MD_Converter.exe` (+ `_internal\`, `EULA.txt`, `THIRD_PARTY_NOTICES.txt`) |
| Launch modes used | primary: detached windowed GUI launch (`CREATE_DETACHED_PROCESS`, `bInheritHandles = FALSE`) with a sanitized environment and a neutral working directory outside the repository; secondary observation: console-attached launch |

`MD_Converter_Lite.exe` is renamed to `MD_Converter.exe` on install, exactly as
the frozen Inno Setup script maps it.

## 2. Four-commit chain

| # | Commit | Message |
|---|---|---|
| 1 | `9c71c88` | `R2V02-01 freeze packaged runtime identity` |
| 2 | `391c691` | `R2V02-02 verify packaged serial batch runtime` |
| 3 | `2be7c11` | `R2V02-03 verify packaged profile and feature parity` |
| 4 | (this commit) | `R2V02-04 close packaged runtime verification` |

Each work package stopped at its own boundary, verified independently,
classified independently, recorded independent evidence, staged exact files
only, and produced one truthful commit. No combined or retrospective commit
exists. The three pre-existing dirty tracked files (`.gitignore`, `README.md`,
`md_converter/cli.py`) were preserved throughout and never staged. No file under
`md_converter/` was modified by any R2-V02 commit.

## 3. Evidence index

| WP | Evidence |
|---|---|
| R2V02-01 | `Evidence/WP-R2V02-01_PACKAGE_IDENTITY_RUNTIME_EVIDENCE.md` (+ `WP-R2V02-01_RESULT.json`) |
| R2V02-02 | `Evidence/WP-R2V02-02_SERIAL_BATCH_RUNTIME_EVIDENCE.md` (+ `WP-R2V02-02_RESULT.json`) |
| R2V02-03 | `Evidence/WP-R2V02-03_PROFILE_FEATURE_PARITY_EVIDENCE.md` (+ `WP-R2V02-03_RESULT.json`, `WP-R2V02-03_PARITY_REPORT.json`) |
| R2V02-04 | `Evidence/WP-R2V02-04_RESULT.json` (+ this closure) |

Reproducible verification tooling (verification only, never imported by the
product): `Verification/mdc_r2v02_verify.ps1` (phases `WP01`–`WP04` plus the
`DIAG03` profile-selector probe), `Verification/make_fixtures.py`,
`Verification/verify_packaged_parity.py`, `Verification/probe_ui_tree.ps1`.

Measured checks: WP-01 7, WP-02 15, WP-03 20 + 86 parity, WP-04 10 — all
passing (`failed_count = 0` for every work package). No R2-V01 source suite was
re-run.

## 4. Runtime independence (WP-01)

* installed executable launches from the installed path with a neutral cwd;
* child environment: `PYTHONPATH` empty, repository not on `PATH`, project
  `.venv\Scripts` not on `PATH`, no inherited standard handles;
* 132 loaded modules, **0** of them from the repository or `.venv` (every module
  comes from the install directory or Windows);
* one minimal packaged conversion through the real GUI path
  (`GUI → GuiWorker → ConversionService → CompilerContext`) succeeded in 3.8 s
  and produced `output\01_english.docx` (29 439 B) with the expected
  stem-derived name.

## 5. Real serial batch (WP-02)

One four-file batch through the packaged GUI (valid English; wide table +
figure; deliberate failing empty source; valid source after the failure):

* queue order preserved: `01_english.md`, `02_wide_table_figure.md`,
  `03_failure.md`, `04_after_failure.md`;
* maximum items observed in the `converting` state in any of the 57 samples = 1,
  and 0 samples showed a later source terminal before an earlier one
  (strict serial prefix order);
* per-file results: `✓ 01_english.md — succeeded`,
  `✓ 02_wide_table_figure.md — succeeded`, `✗ 03_failure.md — failed`,
  `✓ 04_after_failure.md — succeeded` (failure isolation);
* derived summary: `Batch complete — 4 files processed · 3 succeeded ·
  0 warnings · 1 failed`, consistent with the per-file rows;
* output count and naming: `01_english.docx`, `Wide_Table_Report.docx`
  (frontmatter-title naming), `04_after_failure.docx`; the failing source
  produced no document;
* workflow returned to idle (`READY`, primary action enabled again);
* `Open Output Folder` opened a new Explorer window titled
  `output - File Explorer` on the batch output directory.

## 6. Five-profile and feature parity (WP-03)

One integrated document converted once per profile through the packaged GUI
(plus one localized-TOC control), all reporting `SUCCESS`:

| Profile | artifact margins (L,R,T,B cm) | content box (cm) | 8-column table total / min (cm) | 4:1 figure (cm) | 1:10 figure (cm) |
|---|---|---|---|---|---|
| professional_report | 2.54, 2.54, 2.54, 2.54 | 15.921 × 24.62 | 15.921 / 1.7974 | 12.70 × 3.175 | 2.462 × 24.6204 |
| business_report | 2.0, 2.0, 2.0, 2.0 | 17.001 × 25.7 | 17.0004 / 1.9209 | 12.70 × 3.175 | 2.57 × 25.6999 |
| academic | 3.0, 3.0, 2.54, 2.54 | 15.001 × 24.62 | 15.0002 / 1.6951 | 12.70 × 3.175 | 2.462 × 24.6204 |
| technical | 2.2, 2.2, 2.2, 2.2 | 16.601 × 25.3 | 16.6018 / 1.875 | 12.70 × 3.175 | 2.5301 × 25.3012 |
| clean_minimal | 2.54, 2.54, 2.54, 2.54 | 15.921 × 24.62 | 15.921 / 1.7974 | 12.70 × 3.175 | 2.462 × 24.6204 |

* profile geometry matches the frozen R2-V01 matrix exactly;
* TOC heading `Table of Contents` (English) and `目录` (localized control) with
  the canonical `TOC \o "1-3" \h \z \u` field and cached entries
  (`Competitive Foundation Report · Architecture · Financial Overview ·
  Projected Growth · Page Capped Figure · Notes`);
* table fitting: 8 explicit columns, fixed layout, total inside the profile
  content width, column floor ≥ 1.2 cm − twips, no cell mutation;
* figure fitting: aspect ratios 4:1 and 1:10 preserved, figures inside the
  content box; the page-height cap is exercised (the 1:10 figure's height equals
  the profile content height);
* `image_width`: delivered width 12.70 cm = `min(5 in frozen default, content
  width)` in every profile;
* parity measurement: **86 checks, 0 failed** (`WP-R2V02-03_PARITY_REPORT.json`).

## 7. Cold launch (WP-04)

* application fully exited before the cold launch (0 running processes);
* cold launch of the same installed artifact succeeded;
* no stuck previous batch state: no batch summary, no document action, no queued
  rows, primary action disabled (clean `EMPTY`), i.e. the previous batch was not
  resumed;
* runtime independence re-confirmed on the cold process (132 modules, 0 from the
  repository or `.venv`);
* one representative conversion succeeded in 3.1 s, producing
  `output\04_after_failure.docx` with `Open Document` actionable.

## 8. Corrections

`bounded G1 correction passes applied to product source : 0`.

All corrections were confined to the R2-V02 **verification harness** (explicitly
authorized) and are listed for auditability:

1. the packaged product was launched the way its shipped shortcuts launch it —
   a detached windowed process with no inherited standard handles — after the
   console-attached launch produced the environment-sensitive observation in
   §9;
2. `CREATE_UNICODE_ENVIRONMENT` was added to the detached launcher (required for
   a custom Unicode environment block);
3. the output-profile selector is driven with a real mouse click delivered to
   the combo popup's own window (UI Automation's `SelectionItemPattern` is
   accepted by this Qt combo but does not apply the selection);
4. single-file selection state is verified through the frozen GUI's own
   batch-surface rule (the batch list is shown only for two or more files);
5. TOC entry measurement reads the entry text from `word/document.xml`, because
   Word rewrites the cached entries as hyperlinked runs when it refreshes the
   TOC;
6. UI Automation enumerations are retried across transient Qt tree rebuilds,
   and native stderr from `reg.exe`/Python is tolerated instead of aborting a
   run;
7. the product settings store is restored after every run (`reg exit=0` for
   WP-02..WP-04).

The WP-01 raw record predates correction 6 for the settings-restore field and
therefore reports the pre-fix `reg.exe` message; the settings key was verified
absent afterwards by a direct registry query, and nothing was left behind.

## 9. Deferred observations (classified, not repaired)

| Observation | Classification | Note |
|---|---|---|
| Starting the installed product from a console-attached process (child inherits a `cp1252` stdout) makes the Word-COM TOC refresh fail with `UnicodeEncodeError` while `print()`-ing emoji diagnostics in `md_converter/renderer/post_processor.py`; the DOCX is still written, but the conversion is reported as not-clean | `PRE_EXISTING_KNOWN_LIMITATION` | Source-level `print()`-based diagnostics in the accepted baseline; not introduced by packaging and not reproduced by the documented user launch. Product source is out of this gate's authority. |
| The packaged desktop surface exposes no `image_width` control, so the runtime target is the frozen default (5 in → 12.70 cm) and the content-width cap branch is not triggered in any profile | Observation (no defect) | The explicit-override/cap behaviour was verified at source level in R2-V01; the same single sizing authority ships in the package (`md_converter.renderer.layout.figure_sizing` present in the packaged archive). |
| The installer wrapper could not be recompiled on this machine: the Inno Setup compiler (`ISCC.exe`) is not installed and is not reachable offline; the installed layout reproduces the frozen script's `[Files]`/`[Dirs]` mapping and no packaging source was edited | `ENVIRONMENT_FAILURE` (installer wrapper only) | The packaged runtime under test is the frozen-pipeline artifact; rebuilding `MD_Converter_v1.1.0_Setup.exe` remains a release-engineering step, not a runtime property. |

## 10. Introduced packaged failures and blockers

```text
introduced packaged failures : 0   (WP-01 0, WP-02 0, WP-03 0, WP-04 0)
unresolved packaged blockers : 0
G2 AUTHORITY REQUIRED        : 0
BLOCKED                      : 0
```

## 11. Pending later gates (not closed here)

```text
Native Word / human visual acceptance                     -> PENDING R2-V03
Chromium / Golden-environment retest                      -> PENDING R2-V04
Installer rebuild on a machine with the Inno Setup toolchain -> release engineering
then R2 RC -> Human Acceptance -> Production Release
```

R2-V02 does not start R2-V03.

## 12. Final recommendation and status

The accepted R2-V01 source baseline survives packaging and installation: the
installed product runs without the source checkout or `.venv`, proves the real
four-file serial batch with failure isolation, keeps all five output profiles and
the TOC/table/figure/`image_width` semantics, and cold-starts cleanly. With zero
introduced packaged failures and zero unresolved packaged blockers, the
packaged-runtime release gate is satisfied.

**R2-V02 — CLOSED / ACCEPTED / PACKAGED RUNTIME RELEASE-GATE PASS**
