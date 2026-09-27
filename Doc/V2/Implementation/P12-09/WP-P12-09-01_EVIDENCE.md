# WP-P12-09-01 — Verification Baseline — Completion Evidence

**Product Baseline SHA:** `38614c7bb555f96685c301bc4b6abd71138c2642` (P12-08 Closure)
**Specification Baseline SHA:** `08b198043ad107cdcd9293152acfa756fd6fa410`
**Input commit:** `08b1980` (Add P12-09 verification specifications)
**Authority:** verification planning only; no production code change

## Report record

| Field | Value |
|---|---|
| WP | WP-P12-09-01 — Verification Baseline |
| Status | PASS |
| Input baseline SHA | `08b1980` |
| Output commit SHA | recorded by the committing run (`P12-09-01 freeze verification baseline`) |
| Files added | this evidence file, `evidence/wp01_candidate_identity.json` |
| Files modified | none |
| Production code touched | none |
| Broad test execution | intentionally deferred to WP-09-03 (per WP rules) |
| Scope deviation | none |
| Stop condition | none |

## Candidate identity (frozen)

The frozen candidate is the P12-08 final release artifact. Both hashes were
recomputed in this WP and match the values recorded in
`Doc/V2/Implementation/P12-08/P12-08_CLOSURE_EVIDENCE.md`, so the candidate is
identical to the accepted P12-08 artifact.

| Item | Value |
|---|---|
| Installer path | `dist_installer\MD_Converter_v1.1.0_Setup.exe` |
| Installer filename | `MD_Converter_v1.1.0_Setup.exe` |
| Installer size | 51,109,717 bytes |
| Installer SHA-256 | `EFEC378F11B00A53791158199B4DC98AA09F44F5B1F013363FF744A92B91B9BF` |
| Installer file version | 1.1.0.0 |
| Installer timestamp | 2026-09-27 21:04:45 (+08:00) |
| Packaged executable path | `dist\MD_Converter_Lite\MD_Converter_Lite.exe` |
| Packaged executable size | 6,845,458 bytes |
| Packaged executable SHA-256 | `F5AB988168DFA976ED50095A272FB3405CE2CAB395C4A77A34637318D60F7E04` |
| Packaged executable version | 1.1.0 |
| Packaged executable timestamp | 2026-09-27 21:04:15 (+08:00) |
| Packaged payload | 268 files, 166,150,109 bytes |
| Product version (`pyproject.toml`) | 1.1.0 |
| Published identity | `AppId=MDConverter.Quansheng2022`, `AppName=MD Converter`, `AppVersion=1.1.0` |

Installer SHA-256 equals the P12-08 closure record
(`EFEC378F…B91B9BF`) and the executable SHA-256 equals the P12-08 closure record
(`F5AB9881…0F7E04`); payload inventory (268 files) is also unchanged. Candidate
identity is therefore **frozen and unchanged**.

Machine-readable copy: `evidence/wp01_candidate_identity.json`.

## Environment record

| Item | Value |
|---|---|
| OS | Windows 11 Home, build 26200 (x64) |
| PowerShell | 7.6.5 (pwsh); harness scripts `#requires -Version 5.1` |
| .NET runtime | 10.0.11 |
| Locale | en-SG |
| ANSI code page | 1252 (cp1252) |
| OEM code page | 1252 |
| Display | Intel UHD Graphics + NVIDIA MX550, 1920×1080, system DPI 144 (150 %) |
| Interactive desktop session | yes (session id 1, `UserInteractive=True`) |
| Microsoft Word | present — `C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE`, version 16.0.20326.20158 |
| Build/verify Python | `.venv\Scripts\python.exe`, CPython 3.12.14 (MSC v.1944, 64-bit) |
| Test workspace | `%TEMP%\mdc_p1209_*` (created per run) |

## Verification matrix

Each release requirement is mapped to exactly one primary verification method.

| Requirement | Primary method | WP | Where evidence is recorded |
|---|---|---|---|
| Candidate identity frozen (installer/exe hash/version) | artifact/static inspection | 01 | this document |
| Each WP refers to the same frozen candidate | artifact/static inspection | 01/07 | this document, closure |
| Select Markdown / Drag & Drop / invalid input / missing source | packaged-app smoke | 02 | WP-09-02 evidence |
| Real conversion `GUI → GuiWorker → ConversionService → Core → DOCX` | packaged-app smoke | 02 | WP-09-02 evidence |
| Frozen GUI states (EMPTY/READY/CONVERTING/SUCCESS/WARNING/FAILED) | packaged-app smoke + source test | 02/03 | WP-09-02/03 |
| Result UX (success/warning/failure/report/diagnostics retained) | packaged-app smoke | 02 | WP-09-02 evidence |
| Open Document — Word actually opens/reads the file | installed-app smoke | 02/04 | WP-09-02/04 evidence |
| Open Folder targets expected directory | installed-app smoke | 02/04 | WP-09-02/04 evidence |
| Missing artifact fails closed | packaged/installed smoke | 02/04/05 | WP-09-02/04/05 |
| Settings save/cancel/reset + restart persistence | installed-app smoke | 02/04 | WP-09-02/04 evidence |
| About version/name/positioning/local wording | installed-app smoke | 02 | WP-09-02 evidence |
| Full source regression + public API/CLI + Canonical + Golden | automated source test | 03 | WP-09-03 evidence |
| Canonical / QA / Golden / ConversionService / CLI drift = 0 | automated source test + diff | 03 | WP-09-03 evidence |
| Installer install/launch/version/Start Menu | installed-app smoke | 04 | WP-09-04 evidence |
| Installed real conversion + output artifact | installed-app smoke | 04 | WP-09-04 evidence |
| Installed paths (normal/spaces/non-ASCII/foreign CWD) | installed-app smoke | 04 | WP-09-04 evidence |
| cp1252 installed-runtime reconfirmation | installed-app smoke + static | 04 | WP-09-04 evidence |
| Uninstall removes payload, preserves user documents | artifact/static + process inspection | 04 | WP-09-04 evidence |
| Failure/recovery matrix (missing/invalid/locked output, recovery) | installed-app smoke | 05 | WP-09-05 evidence |
| Lifecycle (worker-active close protection, sequential reuse) | installed-app smoke | 05 | WP-09-05 evidence |
| Keyboard/accessibility | installed-app smoke + manual/visual | 05 | WP-09-05 evidence |
| High-DPI smoke | manual/visual Windows check | 05 | WP-09-05 evidence |
| Privacy/locality (local processing, no account, no upload) | artifact/static + manual/visual | 06 | WP-09-06 evidence |
| No required network dependency in normal workflow | manual/visual + process/network observation | 06 | WP-09-06 evidence |
| Artifact integrity (filename/version/size/hash/EULA/notices, no dev payload) | artifact/static inspection | 06 | WP-09-06 evidence |
| Rebuild traceability to P12-08 clean build | prior evidence reused | 06 | WP-09-06 evidence |
| Consolidated closure decision | consolidation | 07 | `P12-09_CLOSURE_EVIDENCE.md` |

## Known accepted exceptions (carried forward)

These are carried forward from the P12-08 closure; they must remain **unchanged**.
Any change turns them into new failures to classify.

| # | Exception | Origin |
|---|---|---|
| E1 | `test_packaging_metadata.py::test_pkg_documented_extras_exist_in_metadata` — README-content failure | recorded in P12-06 / P12-08 closure |
| E2 | `test_packaging_metadata.py::test_pkg_readme_has_no_legacy_packaging_references` — README-content failure | recorded in P12-06 / P12-08 closure |
| E3 | Invalid YAML frontmatter behaviour | P12-08 closure |
| E4 | Existing test side effect involving `output\document.docx` | P12-08 closure |
| E5 | Historical repo-wide lint debt outside touched files | P12-08 closure |
| E6 | No authoritative custom product icon (default icons used) | P12-08 closure |
| E7 | Installer is not code-signed | P12-08 closure |
| E8 | Word COM post-processing dominates conversion time (≈5 s to >4 min) | P12-08 closure |

## Pre-existing working-tree state (not part of this phase)

The repository was already dirty before P12-09 started. These changes are
**pre-existing**, unrelated to P12-09, and are left untouched:

| Path | Nature | Release impact on the frozen artifact |
|---|---|---|
| `README.md` | full content rewrite (pre-existing uncommitted modification) | none on the artifact; source of exceptions E1/E2 |
| `.gitignore` | expanded ignore rules | none |
| `md_converter/cli.py` | docstring-only change (CLI usage examples, lines 109–113) | none on the frozen artifact; must be re-checked in WP-09-03 |

Because the release candidate is a frozen, previously built binary artifact, a
working-tree documentation change cannot alter its identity. The `cli.py`
docstring change is a candidate for source-regression classification in
WP-09-03 and is explicitly re-checked there.

## Release-blocker policy (for this phase)

The pipeline must STOP if verification finds any of: installed real conversion
failure; installed app cannot launch reliably; installer/uninstaller risks user
data; worker lifecycle safety regression; output-path authority regression;
persistent Open Document failure; cp1252 runtime regression in normal installed
use; required network dependency; Core/Canonical/QA/Golden semantic drift;
CLI/public API breaking change; or any defect requiring a semantic/product
change (V3/G2).

Defect classes used throughout P12-09: V0 observation (record only), V1 minor
verification defect (one bounded correction cycle per WP allowed), V2
release-blocking product defect (stop), V3 semantic/architecture change required
(stop, escalate to Human authority).

## Acceptance

| Criterion | Result |
|---|---|
| Candidate identity frozen (installer + executable hash/version) | PASS |
| Candidate matches accepted P12-08 artifact | PASS |
| Verification matrix complete | PASS |
| Known exceptions explicit | PASS |
| Environment recorded | PASS |
| Release-blocker policy explicit | PASS |

## Conclusion

WP-P12-09-01 is complete: the release candidate is frozen to installer
`MD_Converter_v1.1.0_Setup.exe`
(`EFEC378F11B00A53791158199B4DC98AA09F44F5B1F013363FF744A92B91B9BF`, 51,109,717
bytes, version 1.1.0), the verification matrix and accepted exceptions are
explicit, and the environment is recorded. Broad regression was intentionally
deferred to WP-09-03.
