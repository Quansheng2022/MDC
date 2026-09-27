# WP-P12-10-01 — RC Baseline & Identity — Evidence

**Product Baseline:** `4c02734` (P12-09 Closure)
**P12-10 Specification Baseline SHA:** `3a0dfdceae70b709c674d43656cbffed7cd969e8`
**Input HEAD:** `3a0dfdceae70b709c674d43656cbffed7cd969e8`
**Status:** PASS

## 1. Frozen identity

| Item | Value |
|---|---|
| RC identifier (evidence-only label) | **MD Converter v1.1.0 RC1** |
| Product version | `1.1.0` |
| P12-09 Closure SHA (full) | `4c027344fbd9ca7d05190fe7f689c4edad11dd8d` |
| P12-10 Specification Baseline SHA | `3a0dfdceae70b709c674d43656cbffed7cd969e8` |
| Frozen source SHA | `4c027344fbd9ca7d05190fe7f689c4edad11dd8d` |
| Installer path | `dist_installer\MD_Converter_v1.1.0_Setup.exe` |
| Installer size | 51,109,717 bytes |
| Installer SHA-256 | `EFEC378F11B00A53791158199B4DC98AA09F44F5B1F013363FF744A92B91B9BF` |
| Installer file version | `1.1.0.0` |
| Executable path | `dist\MD_Converter_Lite\MD_Converter_Lite.exe` |
| Executable size | 6,845,458 bytes |
| Executable SHA-256 | `F5AB988168DFA976ED50095A272FB3405CE2CAB395C4A77A34637318D60F7E04` |
| Executable file version | `1.1.0` |
| Payload | 268 files, 166,150,109 bytes |
| RC freeze timestamp | 2026-09-27T23:33:00+08:00 |

## 2. Hash identity verification

Both artifacts were re-hashed in this work package and compared with the
P12-09 frozen candidate (`Doc/V2/Implementation/P12-09/evidence/wp01_candidate_identity.json`):

| Artifact | Re-computed | P12-09 candidate | Match |
|---|---|---|---|
| Installer | `EFEC378F…B91B9BF` | `EFEC378F…B91B9BF` | YES |
| Executable | `F5AB9881…0F7E04` | `F5AB9881…0F7E04` | YES |

Sizes match exactly (51,109,717 / 6,845,458 bytes). Candidate drift = 0; no stop
condition was triggered.

## 3. Version consistency

| Authority | Value |
|---|---|
| `pyproject.toml [project].version` | `1.1.0` |
| Executable file version | `1.1.0` |
| Installer file version | `1.1.0.0` |
| About dialog (P12-09 WP-09-02 `about-wording` PASS) | `Version 1.1.0` |
| Published identity | `AppId=MDConverter.Quansheng2022`, `AppName=MD Converter`, `AppVersion=1.1.0` |

`RC1` is an evidence-only label. No application, package, installer or resource
version metadata was changed to encode it.

## 4. Provenance

**P12-08 build provenance:** PyInstaller 6.22.3 onedir `COLLECT` from
`MD_Converter_Lite.spec`, entry point `packaging/windows/launcher_main.py` →
`md_converter.gui.app.main`, windowed build; installer produced by Inno Setup
from `packaging/windows/MD_Converter.iss`, per-user
`{localappdata}\Programs\MD_Converter`, `PrivilegesRequired=lowest`;
clean-build procedure `tools/packaging/build_windows_release.ps1`
(P12-08 Closure `38614c7`).

**P12-09 verification provenance:** `Doc/V2/Implementation/P12-09/P12-09_CLOSURE_EVIDENCE.md`
— functional acceptance, installed runtime, regression/canonical/golden,
failure/recovery, privacy/locality/integrity all PASS; candidate unchanged for
every work package; introduced failures = 0; open blockers = 0.

## 5. Frozen source identity

No change occurred under `md_converter/`, `pyproject.toml`, `*.spec` or
`packaging/` between the P12-08 packaging closure (`38614c7`) and the P12-09
verification closure (`4c02734`); P12-09 and the P12-10 specification baseline
added documentation, corpus, evidence and verification tooling only.

The frozen source identity for this RC is therefore
`4c027344fbd9ca7d05190fe7f689c4edad11dd8d`.

## 6. RC identifier and filename safety

`MD Converter v1.1.0 RC1` contains no Windows-invalid filename character
(`\ / : * ? " < > |`). The filename-safe form used for the release folder is
`MD_Converter_v1.1.0_RC1`.

## 7. Checks

| Check | Result |
|---|---|
| Installer hash matches frozen candidate | PASS |
| Executable hash matches frozen candidate | PASS |
| Installer size matches frozen candidate | PASS |
| Executable size matches frozen candidate | PASS |
| Version internally consistent | PASS |
| P12-08 build provenance recorded | PASS |
| P12-09 verification provenance recorded | PASS |
| RC identifier assigned and filename-safe | PASS |
| Repair/rebuild performed | NO (not required, not authorized) |
| Product source modified | NO |

Evidence record: `Doc/V2/Implementation/P12-10/evidence/wp01_rc_candidate_identity.json`

## 8. Acceptance

Source, installer, executable, version and RC identifier are frozen;
candidate drift = 0. **WP-P12-10-01 = PASS.**
