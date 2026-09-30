# WP-R2PRERC01-02 — Build & Identify the Final Inno Setup Installer

**Program:** R2-PRE-RC-01 (pre-RC release-engineering gate)
**Change classification:** `G2_OR_RELEASE` — release engineering, no product change
**Governing SPEC:** `CANONICAL_SPEC.md` (FROZEN 1.1) — `SPEC-GOAL-003`, `SPEC-ARCH-007`, `SPEC-INV-001`
**Work package:** 2 / 3
**Result:** `PASS`

## 1. Build invocation

```text
cd packaging\windows
"C:\Users\Quansheng\AppData\Local\Programs\Inno Setup 7\ISCC.exe" MD_Converter.iss
```

| Item | Value |
|---|---|
| Compiler | `ISCC.exe` — Inno Setup 7.1.0 (`jrsoftware.org`, per-user install) |
| Compiler engine banner | `Compiler engine version: Inno Setup 7.1.0` |
| Script | `packaging/windows/MD_Converter.iss` (unchanged; SHA-256 `EBB0979972348ECA2926BC3095049BDB047B36F206E9D66E2A1C7E468B91CE03`) |
| Compiler exit code | `0` — `Successful compile (30.578 sec)` |
| Builds performed | `1` (no bounded G1 packaging correction was needed, so no rebuild) |

The compiler log confirms every payload member was taken from the frozen
accepted payload (`dist\MD_Converter_Lite\MD_Converter_Lite.exe` plus 267
`_internal` / compliance files) and that no other source tree was folded in.

## 2. Final installer identity

Recorded by `Verification/r2prerc01_installer_identity.ps1` →
`Evidence/WP-R2PRERC01-02_INSTALLER_IDENTITY.json`.

| Item | Value |
|---|---|
| Installer filename | `MD_Converter_v1.1.0_Setup.exe` |
| Absolute path | `C:\Users\Quansheng\Documents\projects\MD_Converter\dist_installer\MD_Converter_v1.1.0_Setup.exe` |
| File size | `51186717` bytes |
| SHA-256 | `4B56FC989BAB7FF7E648CC29DFE5A6D944B2B8EFC420F11DE8D0ECF8294FFDE9` |
| Build timestamp | `2026-09-30T23:25:46+08:00` |
| Compiler version | `Inno Setup 7.1.0` |
| Product/source baseline | `master` @ `2fc83f2` (WP-01), product source = accepted R2 baseline |
| Packaged executable SHA-256 | `68524527CDC5718CE31A1F0454EAFB0FF64C52D5C838716AC1277445DE0E3021` |

### Installer file metadata (visible product/installer version)

| Field | Value |
|---|---|
| FileVersion | `1.1.0.0` |
| ProductVersion | `1.1.0` |
| ProductName | `MD Converter` |
| CompanyName | `Quansheng2022` |
| FileDescription | `Markdown to Microsoft Word DOCX Converter` |
| LegalCopyright | `Copyright © 2026 Quansheng2022` |

The visible metadata is exactly what the frozen `.iss` declares — no new
signing requirement and no release-semantic change was introduced. The
installer remains unsigned, matching the recorded P12-10 known release
condition.

## 3. Superseded artifact

| Item | Value |
|---|---|
| Previous wrapper (now replaced) | SHA-256 `EFEC378F11B00A53791158199B4DC98AA09F44F5B1F013363FF744A92B91B9BF`, 51 109 717 bytes, built 2026-09-27, wrapping the pre-R2 payload `F5AB9881…` |
| Byte-identical copy | `release\MD_Converter_v1.1.0_RC1\MD_Converter_v1.1.0_Setup.exe` (same hash) — the superseded bytes remain recoverable |

## 4. Invariance checks (the build changed nothing else)

| Check | Result |
|---|---|
| Accepted packaged payload executable unchanged | `PASS` — `68524527…` re-verified after the build |
| Payload tree digest unchanged | `PASS` — `ecb6a4453f342af51cbc2b26b175489cb4ad963bc987a7407ff10ff0f8efa96c` |
| Frozen Golden baseline unchanged | `PASS` — `md_converter/tests/golden/sample.expected.json` = `6D589013B8024C158DE5D29B93BDFEF68F2F406045C805DAB61F8E513725829A` |
| Product runtime source drift | `0` — only the pre-existing, untouched `md_converter/cli.py` 2/2 hunk |
| Product source file modified by this WP | none |

## 5. PASS criteria

| Criterion | Result |
|---|---|
| Final installer builds successfully | PASS |
| Installer identity recorded (name/path/size/SHA-256/time/compiler/baseline/payload) | PASS |
| Accepted payload unchanged | PASS |
| Product source drift | `0` |
| New signing requirement introduced | no |
| Bounded G1 packaging correction used | none |

## 6. Result

`WP-R2PRERC01-02 — PASS`

Next: WP-R2PRERC01-03 verifies the install / launch+conversion / uninstall /
reinstall lifecycle with this exact installer.

Artifact retention: `dist_installer/` is not tracked by the repository's release
process (it is untracked), so the executable itself stays out of Git; its exact
path, size and SHA-256 are recorded here instead.
