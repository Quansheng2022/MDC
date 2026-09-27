# WP-P12-10-05 — RC Smoke & Integrity — Evidence

**Product Baseline:** `4c02734` (P12-09 Closure)
**Input HEAD:** `eb5b6dad3108c8549c46c29637cd6f9701b91882` (WP-P12-10-04)
**Status:** PASS (34/34 checks)

## 1. Precheck — binary identity unchanged

| Item | Value |
|---|---|
| Installer used | `release\MD_Converter_v1.1.0_RC1\MD_Converter_v1.1.0_Setup.exe` |
| Installer size | 51,109,717 bytes |
| Installer SHA-256 | `EFEC378F11B00A53791158199B4DC98AA09F44F5B1F013363FF744A92B91B9BF` |
| Installer file version | 1.1.0.0 |
| Equals WP-01 frozen hash | YES |

No hash drift. The smoke proceeded.

## 2. Minimal RC smoke

Executed with the verification harness `tools/packaging/p12_10_rc_smoke.ps1`
(new in this work package; reuses `tools/packaging/gui_automation.ps1`). Every
step is a real user action against the **installed** product; no source-tree
import and no conversion logic of the harness's own.

| # | Required step | Result | Detail |
|---|---|---|---|
| 1 | install the frozen installer | PASS | silent per-user install, exit 0 |
| 2 | launch the installed application | PASS | window `MD Converter` visible from `%LOCALAPPDATA%\Programs\MD_Converter\MD_Converter.exe` |
| 3 | verify About version = 1.1.0 | PASS | About text: `Version 1.1.0` |
| 4 | convert one representative Markdown | PASS | `SUCCESS` after 9.6 s, `Open Document` / `Open Folder` enabled |
| 5 | verify the DOCX exists | PASS | `…\output\01_simple.docx`, contains `word/document.xml` |
| 6 | Open Document → Word actually opens/reads it | PASS | Word window `01_simple [Compatibility Mode] - Word` (Word 16.0.20326.20158) plus an exclusive file lock held while displayed, released on close |
| 7 | quick Settings persistence check | PASS | toggle `On → Off`, saved, restart → `Off` restored (store `folders/remember = false`) |
| 8 | close the app cleanly | PASS | process exited, twice (before restart and after the conversion) |
| 9 | uninstall | PASS | `unins000.exe /VERYSILENT`, exit 0; program dir, uninstall entry and Start Menu entries removed |
| 10 | confirm the user document is preserved | PASS | sentinel `user_note.txt` and the converted DOCX both survive |

Installed binary identity: the installed executable is byte-identical to the
frozen packaged executable (`F5AB9881…0F7E04`, version 1.1.0). EULA.txt and
THIRD_PARTY_NOTICES.txt are installed next to it.

## 3. Post-freeze drift

| Check | Result |
|---|---|
| Installer SHA-256 re-read after the whole smoke | `EFEC378F…B91B9BF` |
| Equals the WP-01 frozen hash | YES |
| Post-freeze binary drift | **0** |
| Product source / spec / installer script modified during the smoke | NO |

## 4. cp1252

Binary identity is unchanged, so (per the work package) a single normal
conversion on the accepted Windows environment is sufficient: the packaged GUI
conversion reached `SUCCESS` on the cp1252 (en-SG) machine with
`PYTHONIOENCODING` unset, and the produced DOCX contains the native TOC field
written by the emoji-printing post-processing block. The full cp1252
investigation was not repeated; P12-09 remains authoritative for it.

## 5. Scope discipline

Deliberately **not** re-run (P12-09 remains authoritative):

```text
full regression / full Canonical / full Golden / full accessibility matrix /
full failure-recovery matrix
```

## 6. Checks executed

```text
34 checks executed, 34 PASS, 0 FAIL
```

| Group | Checks |
|---|---|
| installer precheck | hash, size, version (3) |
| install | exit code, install directory, installed exe identity, installed exe version, EULA/notices, uninstall entry, no service/autostart (7) |
| launch + About | installed-app launch, About version (2) |
| settings | save persists, clean close, restored after restart (3) |
| conversion | conversion success, artifact created, artifact valid (3) |
| Open Document / Word | Open Document enabled, artifact present before open, Word actually opened, Word exclusive lock, Word closed, artifact present after, lock released (7) |
| close / uninstall / user data | clean close, uninstall exit code, install dir removed, uninstall entry removed, Start Menu removed, user document preserved, converted document preserved, settings key preserved (8) |
| drift | post-smoke installer hash unchanged (1) |

## 7. Side effects cleaned up

* The application was uninstalled; no `MD_Converter` process and no `WINWORD`
  process remain.
* The GUI preference store was restored to its pre-smoke values
  (`folders/remember = true`, remembered source/output folders as found), so the
  phase leaves no user-visible settings change.
* The smoke worked in a fresh temp folder
  (`%TEMP%\mdc_p1210_rc_smoke_20260927_234638`); the produced DOCX and sentinel
  are intentionally left in place as the preserved user documents.

Evidence record: `Doc/V2/Implementation/P12-10/evidence/wp05_rc_smoke.json`

## 8. Acceptance

Binary identity unchanged and minimal install/launch/convert/open/uninstall
smoke PASS. **WP-P12-10-05 = PASS.**
