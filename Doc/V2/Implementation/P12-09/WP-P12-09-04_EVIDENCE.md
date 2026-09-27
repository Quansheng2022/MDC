# WP-P12-09-04 — Installed / Packaged Verification — Completion Evidence

**Product Baseline SHA:** `38614c7bb555f96685c301bc4b6abd71138c2642`
**Specification Baseline SHA:** `08b198043ad107cdcd9293152acfa756fd6fa410`
**Input commit:** `bf3270c` (WP-P12-09-03)
**Authority:** verification only; no production code change

## Report record

| Field | Value |
|---|---|
| WP | WP-P12-09-04 — Installed / Packaged Verification |
| Status | PASS |
| Input baseline SHA | `bf3270c` |
| Output commit SHA | recorded by the committing run (`P12-09-04 verify installed release candidate`) |
| Candidate installer | `dist_installer\MD_Converter_v1.1.0_Setup.exe` |
| Installer SHA-256 | `EFEC378F11B00A53791158199B4DC98AA09F44F5B1F013363FF744A92B91B9BF` (51,109,717 bytes, version 1.1.0) |
| Files added | this evidence file, `evidence/wp04_install_uninstall.json`, `evidence/wp04_runtime_matrix_installed.json`, `evidence/wp04_cp1252_reconfirm.json` |
| Files modified | none |
| Checks executed | install, installed runtime matrix (16 checks), cp1252 reconfirmation, Start Menu launch, uninstall |
| Passed / Failed | all PASS / 0 |
| Scope deviation | none |
| Stop condition | none |

## Pre-install state

The product was not installed: no install directory, no uninstall registry key,
no Start Menu folder, and no service matching the product. The installer hash
was re-read immediately before installation and matched the frozen candidate.

## Installation

| Check | Observed | Result |
|---|---|---|
| Installer launches and completes | silent install exit code 0 | PASS |
| Install path correct | `%LOCALAPPDATA%\Programs\MD_Converter` | PASS |
| Installed payload | `MD_Converter.exe`, `EULA.txt`, `THIRD_PARTY_NOTICES.txt`, `unins000.exe`, `unins000.dat` | PASS |
| Installed executable identity | 6,845,458 bytes, SHA-256 `F5AB9881…0F7E04`, version 1.1.0 — byte-identical to the packaged candidate | PASS |
| No unexpected elevation | `PrivilegesRequired=lowest`, `DefaultDirName={localappdata}\…`; install wrote only under the user profile, no per-machine key | PASS |
| Version metadata correct | `DisplayName=MD Converter 1.1.0`, `DisplayVersion=1.1.0`, `Publisher=Quansheng2022` | PASS |
| Start Menu | `MD Converter.lnk`, input/output folder shortcuts, uninstall shortcut | PASS |
| No background service / updater | no product service, no autostart entry | PASS |
| No required network setup | installer completed from the local archive; no download step | PASS |

Registry entry: `HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\MDConverter.Quansheng2022_is1`
(the `_is1` suffix is added by Inno Setup; the published `AppId` is unchanged).

## Start Menu launch

`MD Converter.lnk` resolves to
`%LOCALAPPDATA%\Programs\MD_Converter\MD_Converter.exe`; launching the shortcut
started that executable and a real `MD Converter` main window appeared and then
closed cleanly.

## Installed runtime (matrix)

Run against the installed executable with a foreign working directory
(`%TEMP%\mdc_p1209_wp04_matrix`), so the result does not depend on the repository
or the current directory.

| # | Check | Evidence | Result |
|---|---|---|---|
| 1 | startup | main window visible | PASS |
| 2 | high-dpi-controls-in-bounds | window 1350×900 (150 %), no clipped controls | PASS |
| 3 | conversion-non-ascii-path | SUCCESS in 4.7 s for a spaces + non-ASCII input path | PASS |
| 4 | artifact-created | valid DOCX produced | PASS |
| 5 | preference-written-on-conversion | remembered folder written to the product's own store | PASS |
| 6 | open-document-word-opens | Word document window `runtime_smoke_ü_225144 [Compatibility Mode] - Word` | PASS |
| 7 | open-document-word-reads-file | artifact held under an exclusive lock while Word displayed it | PASS |
| 8 | artifact-persists-after-open | artifact present before and after | PASS |
| 9 | word-document-closed-lock-released | lock released when the Word window closed | PASS |
| 10 | open-folder | new Explorer window `output - File Explorer` | PASS |
| 11 | missing-artifact-fails-closed | notice shown, no Word window, artifact not recreated, app alive | PASS |
| 12 | settings-saved | remember-folders saved | PASS |
| 13 | settings-persist-across-restart | setting still On after a restart | PASS |
| 14 | remembered-folders-restored | restarted app showed the remembered folder | PASS |
| 15 | worker-active-close-protection | close during conversion did not terminate the app; conversion completed | PASS |
| 16 | clean-close | app exits when closed while idle | PASS |

Raw evidence: `evidence/wp04_runtime_matrix_installed.json` (status PASS, 0
failing checks).

## Paths and independence

The matrix ran the installed product with a working directory of
`%TEMP%\mdc_p1209_wp04_matrix` and an input path containing both spaces and
non-ASCII characters (`MDC smoke ü 测试 …`). Conversion succeeded, proving the
installed product is independent of the repository working directory and
handles spaces / non-ASCII paths.

## cp1252 — independent reconfirmation (CASE A)

| Step | Observed | Result |
|---|---|---|
| Packaged process has no console | PE subsystem = 2 (Windows GUI) | PASS |
| No console stream exists | launching the installed exe with redirected stdout/stderr captured 0 bytes on both | PASS |
| No developer workaround | `PYTHONIOENCODING` empty for the run | PASS |
| The emoji-printing post-processing block really executes | the DOCX produced by the installed app contains the native TOC field written by that block | PASS |

The installed candidate is windowed, so `print()` of emoji diagnostics returns
silently instead of raising `UnicodeEncodeError`. Result: **CASE A — the
installed runtime does not reproduce the cp1252 failure.** No
`PYTHONIOENCODING=utf-8` (or any other) workaround was used as proof.

Raw evidence: `evidence/wp04_cp1252_reconfirm.json`.

## Uninstall

| Check | Observed | Result |
|---|---|---|
| Uninstall succeeds | silent uninstall exit code 0 | PASS |
| Installed payload removed | install directory gone (executable and uninstaller removed) | PASS |
| Uninstall registry entry removed | `MDConverter.Quansheng2022_is1` gone | PASS |
| Start Menu entries removed | `MD Converter` start-menu folder gone | PASS |
| User documents preserved | sentinel in `Documents\MD_Converter\input` and `…\output` preserved | PASS |
| Unrelated files not deleted | sentinel next to the install directory preserved | PASS |
| GUI settings preserved | `HKCU:\Software\MD Converter` untouched by uninstall | PASS |

The uninstall/install cycle was performed twice (the second time to verify
Start Menu launch) and left the machine in the same clean state.

## Defects

| Class | Count | Detail |
|---|---|---|
| V0 observations | 0 | — |
| V1 corrections | 0 | — |
| V2 blockers | 0 | — |
| V3 blockers | 0 | — |

## Acceptance

| Criterion | Result |
|---|---|
| Installer install / path / metadata / Start Menu | PASS |
| Installed launch (direct and via Start Menu) | PASS |
| Real conversion from the installed app | PASS |
| DOCX artifact produced | PASS |
| Clean close and worker-active close protection | PASS |
| Settings save / restart / restore | PASS |
| Path robustness (spaces, non-ASCII, foreign CWD) | PASS |
| Open Document — Word actually opened the file | PASS |
| Open Folder | PASS |
| Missing artifact fails closed | PASS |
| cp1252 installed-runtime reconfirmation | PASS (CASE A) |
| Uninstall removes payload, preserves user data | PASS |
| Release blockers | 0 |

## Conclusion

WP-P12-09-04 passes. The frozen release candidate installs per-user without
elevation, launches from the Start Menu and directly, performs real conversions
on path-robust inputs, opens the artifact in Microsoft Word, persists settings,
fails closed on a missing artifact, does not reproduce the cp1252 failure, and
uninstalls cleanly while preserving user documents.
