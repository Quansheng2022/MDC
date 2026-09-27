# P12-09 — Verification — Closure Evidence

**Product Baseline SHA:** `38614c7bb555f96685c301bc4b6abd71138c2642` (P12-08 Closure)
**P12-09 Specification Baseline SHA:** `08b198043ad107cdcd9293152acfa756fd6fa410`
**Closure SHA:** recorded by the committing run (`P12-09-07 close verification phase`)

## WP commit chain

| WP | Title | Commit | Status |
|---|---|---|---|
| — | P12-09 verification specifications | `08b1980` | baseline |
| WP-P12-09-01 | Verification Baseline | `100c0e7` | PASS |
| WP-P12-09-02 | Functional Acceptance | `d384800` | PASS |
| WP-P12-09-03 | Regression / Canonical / Golden | `bf3270c` | PASS |
| WP-P12-09-04 | Installed / Packaged Verification | `5249e46` | PASS |
| WP-P12-09-05 | Failure / Recovery / Usability | `e8d9200` | PASS |
| WP-P12-09-06 | Privacy / Locality / Release Integrity | `f083008` | PASS |
| WP-P12-09-07 | Verification Closure | this commit | PASS |

## Candidate

| Item | Value |
|---|---|
| Installer filename | `MD_Converter_v1.1.0_Setup.exe` |
| Installer size | 51,109,717 bytes |
| Installer SHA-256 | `EFEC378F11B00A53791158199B4DC98AA09F44F5B1F013363FF744A92B91B9BF` |
| Packaged executable | `dist\MD_Converter_Lite\MD_Converter_Lite.exe`, 6,845,458 bytes |
| Executable SHA-256 | `F5AB988168DFA976ED50095A272FB3405CE2CAB395C4A77A34637318D60F7E04` |
| Version | 1.1.0 (source, executable, installer, About and uninstall metadata agree) |
| Payload | 268 files, 166,150,109 bytes |

Both hashes were re-read at the end of the phase and are unchanged from
WP-09-01: the candidate was identical for every WP, and no release-affecting
change appeared during verification.

## Environment

| Item | Value |
|---|---|
| OS | Windows 11 Home, build 26200 (x64) |
| Locale / code page | en-SG, ANSI cp1252 |
| Display | 1920×1080 at 150 % (system DPI 144) |
| Microsoft Word | 16.0.20326.20158 (actually opened the produced DOCX) |
| Python (build/verify) | CPython 3.12.14 in `.venv` |
| Install scope | per-user `%LOCALAPPDATA%\Programs\MD_Converter`, `PrivilegesRequired=lowest` |

## Functional acceptance (WP-09-02)

Four representative inputs (simple; headings/lists/tables; Unicode/non-ASCII;
richer rendering) each converted to a valid DOCX in ~4.8 s through
`GUI → GuiWorker → ConversionService → Canonical Core → DOCX`. The six frozen
states (`EMPTY`, `READY`, `CONVERTING`, `SUCCESS`, `SUCCESS_WITH_WARNING`,
`FAILED`) were all observed with no extra state. Invalid input, missing source
and stale source fail safely; success/warning/failure remain distinct and the
report surface retains the original evidence.

Smoke 4×13/13 PASS; focused acceptance matrix 16/16 PASS; packaged runtime
matrix 16/16 PASS.

## Regression (WP-09-03)

```text
collected 789 tests
787 passed, 2 failed
```

Both failures are the unchanged, approved README-content exceptions (E1, E2).
Focused runs: GUI + Application suites 437/437 PASS; Canonical/Golden/QA/public
API/config/pipeline/release-evidence 186/186 PASS. The full suite was run once;
it was not repeated for closure.

## Canonical and Golden drift

| Drift | Result |
|---|---|
| Core semantic drift | 0 |
| Canonical drift | 0 |
| QA semantic drift | 0 |
| Golden drift | 0 |
| ConversionService semantic drift | 0 |
| CLI / public API breaking drift | 0 |

Evidence: `git diff --name-status 38614c7 HEAD` lists only P12-09 documentation,
corpus, evidence and verification tooling; nothing under `md_converter/`,
`pyproject.toml`, the packaging scripts or the golden data changed.

## Installed runtime (WP-09-04)

Silent per-user install (exit 0) produced a byte-identical executable
(`F5AB9881…0F7E04`), correct metadata and Start Menu entries, with no service,
autostart entry, elevation or network setup. The installed runtime matrix passed
16/16 against a foreign working directory with spaces and non-ASCII paths.
Uninstall (exit 0) removed the payload, uninstall entry and Start Menu entries
while preserving user documents, unrelated files and GUI settings.

## Output actions

| Check | Result |
|---|---|
| Open Document — artifact exists before launch | PASS |
| Open Document — launcher accepted | PASS |
| Open Document — artifact remains present | PASS |
| Open Document — **Microsoft Word actually opened/read the file** (Word document window plus an exclusive file lock held while displayed, released on close) | PASS |
| Open Folder — expected directory opened | PASS |
| Missing artifact — fails closed (notice, no Word window, artifact not recreated) | PASS |

## Failure / recovery / usability (WP-09-05)

15/15 PASS. Missing/invalid source, Word-locked output
(`[Errno 13] Permission denied`), output path blocked by a same-named
directory, conversion failure, warning, missing artifact, stale remembered
folder, off-screen stored geometry and worker-active close all fail closed or
recover safely. No rename, retry or overwrite was introduced; the artifact was
intact after the Word lock was released.

## Accessibility and High-DPI

Real-window checks: accessible names present for every key control; Tab order
`Select File → Change output folder → Convert → Settings → About`; textual
status (never colour-only); the warning report dialog is keyboard reachable.
The product-code level checks (`Ctrl+O`, `Ctrl+,`, Enter/Space activation,
keyboard-accessible report surface) pass in the WP-09-03 GUI suite.

High-DPI smoke at 150 %: no clipped controls at either candidate form.

## cp1252

**CASE A — no regression.** The installed candidate is a windowed build
(PE subsystem 2); launching it with redirected stdout/stderr captured 0 bytes;
`PYTHONIOENCODING` was empty; and the produced DOCX contains the native TOC
field written by the emoji-printing post-processing block, so that path really
executes. No environment workaround was used as proof.

## Privacy / locality / artifact integrity (WP-09-06)

Frozen positioning and bounded facts verified live:
`Processing: Local, on this computer`, `Account required: No`,
`Document upload: Not required for normal conversion`. During launch and a real
conversion the product process owned **no** TCP connections, so the normal
workflow has no required network dependency (bounded observation, not a
penetration test). Installer/executable hashes and version 1.1.0 agree with the
P12-08 clean build; EULA and THIRD_PARTY_NOTICES are shipped; the 268-file
payload contains no `.git`, `.venv`, tests, caches, review packages, credentials
or developer absolute paths.

## Approved exceptions (unchanged)

| # | Exception |
|---|---|
| E1 | `test_pkg_documented_extras_exist_in_metadata` — README-content failure |
| E2 | `test_pkg_readme_has_no_legacy_packaging_references` — README-content failure |
| E3 | invalid YAML frontmatter behaviour |
| E4 | `output\document.docx` test side effect |
| E5 | historical repo-wide lint debt outside touched files |
| E6 | no authoritative custom product icon |
| E7 | installer not code-signed |
| E8 | Word COM post-processing dominates conversion time |

## Open blockers

**0.**

Recorded non-blocking items:

* **V0:** OS-level drag & drop cannot be scripted (Qt uses an OLE drop target,
  `WS_EX_ACCEPTFILES = False`); the drop path is verified by the product's own
  drop-event tests in the WP-09-03 GUI suite. Unchanged from P12-08.
* **V0:** Word COM occasionally reports `RPC_S_CALL_FAILED` via faulthandler
  during a public-API conversion; the test still passes. Environmental.
* **V0:** `md_converter/cli.py` carries a pre-existing uncommitted
  docstring-only change; non-semantic and not release-affecting.

## Accept criteria

| Criterion | Result |
|---|---|
| Functional acceptance PASS | PASS |
| Introduced required failures = 0 | PASS |
| Canonical drift = 0 | PASS |
| Golden drift = 0 | PASS |
| Installed runtime PASS | PASS |
| Install / uninstall PASS | PASS |
| Failure / recovery PASS | PASS |
| Settings persistence PASS | PASS |
| Open Document actual-open PASS | PASS |
| Open Folder PASS | PASS |
| cp1252 PASS | PASS |
| Privacy / locality PASS | PASS |
| Artifact integrity PASS | PASS |
| Open release blockers = 0 | PASS |

## Decision

```text
P12-09 Verification = CLOSED / ACCEPTED
P12-10 Release Candidate = AUTHORIZED / NEXT
```
