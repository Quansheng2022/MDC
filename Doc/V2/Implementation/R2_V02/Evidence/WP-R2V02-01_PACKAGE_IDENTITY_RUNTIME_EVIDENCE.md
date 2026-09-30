# WP-R2V02-01 — Package Identity & Runtime Independence

**Program:** R2-V02 — Packaged Multi-file Runtime Verification (P12-20)
**Work package:** R2V02-01
**Change classification:** G1 — verification only (no product source change)
**Governing SPEC:** `CANONICAL_SPEC.md` (FROZEN 1.1) — `SPEC-GOAL-006`,
`SPEC-INV-003`, `SPEC-INV-005`, `SPEC-ARCH-007`
**Raw machine record:** `WP-R2V02-01_RESULT.json`
**Status:** PASS

## 1. Scope

Freeze the packaged runtime identity against the accepted R2-V01 source
baseline, build/reuse exactly one verification package, install it at the
product's documented per-user install location, and prove the installed
executable runs and converts a document with no source-checkout or `.venv`
runtime involvement.

## 2. Artifact / files

| Item | Value |
|---|---|
| Branch / HEAD | `master` / `1e1cfc7062736a687147e642442677d24144204f` (R2-V01 closure) |
| Last product-source commit | `bd1a818` 2026-09-30 11:34:26 +0800 `IC-04 guard image width configuration contract` |
| Existing release-target package | `dist_installer/MD_Converter_v1.1.0_Setup.exe`, SHA-256 `EFEC378F11B00A53791158199B4DC98AA09F44F5B1F013363FF744A92B91B9BF`, built 2026-09-27 21:04:45 |
| Verification package built | `dist/MD_Converter_Lite/MD_Converter_Lite.exe` (+ `_internal/`), frozen `MD_Converter_Lite.spec`, PyInstaller 6.22.3, Python 3.12.14 |
| Executable SHA-256 | `68524527CDC5718CE31A1F0454EAFB0FF64C52D5C838716AC1277445DE0E3021` |
| Executable version metadata | FileVersion/ProductVersion `1.1.0`, ProductName `MD Converter` |
| Installed path | `%LOCALAPPDATA%\Programs\MD_Converter\MD_Converter.exe` (installed executable hash identical to the built payload) |
| Neutral runtime cwd | `%TEMP%\mdc_r2v02_wp01_20260930_154016\cwd` (outside the repository) |
| Verification tooling | `Verification/mdc_r2v02_verify.ps1`, `Verification/make_fixtures.py`, `Verification/verify_packaged_parity.py`, `Verification/probe_ui_tree.ps1` |

**Identity decision (no reuse).** The only pre-existing release-target package
predates the accepted product baseline: it was built 2026-09-27 21:04:45, while
the accepted product source changed afterwards in commits `4acb978`
(professional output profiles, 2026-09-29), `39dd391`/`DI-*` (serial batch and
document intelligence), `0239c3f`…`0884fbe` (table/figure fitting), `22462cb`
(TOC localization), `0baba62`/`bd1a818` (`image_width` propagation). A
PyInstaller artifact built on 2026-09-27 cannot contain code committed on
2026-09-29/30, so the existing package was **not** reused; exactly one
verification package was built with the frozen packaging pipeline.

**Installer wrapper limitation.** The frozen Inno Setup script
(`packaging/windows/MD_Converter.iss`) could not be compiled on this machine:
the Inno Setup compiler (`ISCC.exe`) is not installed and is not reachable
offline. The installed layout was therefore materialised by reproducing the
script's own `[Files]`/`[Dirs]` mapping exactly (executable renamed to
`MD_Converter.exe`, `_internal\` payload, `EULA.txt`,
`THIRD_PARTY_NOTICES.txt`, per-user program directory). No packaging script,
spec, or product source was modified. Classification:
`ENVIRONMENT_FAILURE` — installer wrapper only; the packaged runtime itself is
the frozen-pipeline artifact.

## 3. Verification result

Launch mode used for the functional checks: **documented user launch** — a
detached windowed GUI process (`CREATE_DETACHED_PROCESS`,
`bInheritHandles = FALSE`), i.e. the same runtime condition the shipped
shortcuts produce (no console, no inherited standard handles), started from a
neutral working directory with a sanitized environment.

| Check | Result | Measurement |
|---|---|---|
| installed exe hash == built payload hash | PASS | `68524527…E3021` on both sides |
| child environment sanitized | PASS | `PYTHONPATH=''`; repository on child `PATH` = False; `.venv` on child `PATH` = False |
| installed executable launches | PASS | main window `MD Converter` visible (pid 4572) |
| no source / `.venv` module loaded | PASS | 132 loaded modules; repository/`.venv` module hits = 0 (all modules come from the install directory or Windows) |
| Convert action available for one selected file | PASS | `Convert` enabled after the real file dialog accepted `01_english.md` |
| minimal packaged conversion succeeds | PASS | ui outcome `SUCCESS` after 3.8 s through GUI → worker → `ConversionService` → canonical core |
| default output location and naming | PASS | `output\01_english.docx` (29 439 bytes, SHA-256 `ECD6A6AC…6306`) in the neutral cwd, named from the source stem |

## 4. New failures / classification

No packaged failure. One bounded observation was recorded and deliberately not
repaired:

* **Console-inherited launch (`PRE_EXISTING_KNOWN_LIMITATION`).** The same
  installed executable, started by a console-attached process so that the child
  inherits a `cp1252` standard output, fails its Word-COM TOC refresh with
  `UnicodeEncodeError` while `print()`-ing emoji diagnostics in
  `md_converter/renderer/post_processor.py` (`_update_toc_with_word`). The DOCX
  is still written; the conversion is only reported as not-clean. The
  behaviour is source-level (`print()`-based diagnostics in the accepted
  baseline, unchanged by packaging) and does not reproduce in the documented
  user launch, where the windowed process has no usable stdout. No product
  source was changed in this gate; carried as a deferred observation for a
  later gate.

No `PACKAGED_PRODUCT_REGRESSION` and no `PACKAGING_BUILD_OR_INSTALL_DEFECT`
were observed in this work package.

## 5. Protected drift result

| Protected contract | Result |
|---|---|
| Product source modified by this gate | No (0 files under `md_converter/` changed) |
| Canonical pipeline stages bypassed | No (`GUI → GuiWorker → ConversionService → CompilerContext`) |
| Packaged GUI entry point | `packaging/windows/launcher_main.py` → `md_converter.gui.app.main` (unchanged) |
| Dist/baseline artifacts rewritten | One verification package built from the frozen spec; no packaging source edited |
| Pre-existing dirty worktree files (`.gitignore`, `README.md`, `md_converter/cli.py`) | Preserved, never staged |
| Drift | 0 |

## 6. Commit

Commit message: `R2V02-01 freeze packaged runtime identity`
(exact-file staging: this evidence file, the raw result JSON, and the
verification tooling added in this work package). The four-commit chain is
listed with SHAs in `R2_V02_CLOSURE_EVIDENCE.md`.

## 7. Status

PASS — installed packaged runtime is traceable to the accepted R2-V01 source
baseline, runs outside the repository without source/`.venv` involvement, and
completes a minimal packaged conversion with correct output naming.
