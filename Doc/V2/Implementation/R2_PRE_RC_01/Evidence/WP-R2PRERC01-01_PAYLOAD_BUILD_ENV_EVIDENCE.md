# WP-R2PRERC01-01 — Freeze Final Payload & Establish Inno Setup Build Environment

**Program:** R2-PRE-RC-01 (pre-RC release-engineering gate)
**Change classification:** `G2_OR_RELEASE` — release engineering, no product change
**Governing SPEC:** `CANONICAL_SPEC.md` (FROZEN 1.1) — `SPEC-GOAL-003`, `SPEC-ARCH-007`, `SPEC-INV-001`
**Work package:** 1 / 3
**Result:** `PASS`

## 1. Baseline

| Item | Value |
|---|---|
| Branch | `master` |
| HEAD | `1ff46215f17c068b7f8b79a0ee75faf25bbaf595` (`R2V04-02 verify golden browser retest and close gate`) |
| Upstream R2 gates | R2-V01 / R2-V02 / R2-V03 / R2-V04 all CLOSED / ACCEPTED (each closure evidence file is reachable in `HEAD`) |
| Product source drift caused by this WP | `0` |

## 2. Accepted packaged payload identity (frozen)

Reproduced by `Verification/r2prerc01_payload_identity.ps1` →
`Evidence/WP-R2PRERC01-01_PAYLOAD_IDENTITY.json`.

| Item | Value |
|---|---|
| Payload directory | `dist\MD_Converter_Lite` |
| Payload manifest file | `dist\MD_Converter_Lite\MD_Converter_Lite.exe` |
| Executable bytes | `6926650` |
| Executable SHA-256 | `68524527CDC5718CE31A1F0454EAFB0FF64C52D5C838716AC1277445DE0E3021` |
| Payload files / total bytes | `268` / `166231301` |
| Payload tree digest SHA-256 | `ecb6a4453f342af51cbc2b26b175489cb4ad963bc987a7407ff10ff0f8efa96c` |
| Executable version resource | FileVersion `1.1.0`, ProductVersion `1.1.0`, ProductName `MD Converter`, CompanyName `Quansheng2022`, OriginalFilename `MD_Converter_Lite.exe` |

The executable SHA-256 equals the identity frozen and verified by the accepted
R2-V02 gate (`Doc/V2/Implementation/R2_V02/R2_V02_CLOSURE_EVIDENCE.md` §1:
`68524527CDC5718CE31A1F0454EAFB0FF64C52D5C838716AC1277445DE0E3021`). The
payload is therefore the accepted R2 product payload, unmodified.

### Why a rebuild is required

The pre-existing installer `dist_installer\MD_Converter_v1.1.0_Setup.exe`
(SHA-256 `EFEC378F11B00A53791158199B4DC98AA09F44F5B1F013363FF744A92B91B9BF`,
built 2026-09-27) wraps the **older** P12-10 RC1 payload
(`F5AB988168DFA976ED50095A272FB3405CE2CAB395C4A77A34637318D60F7E04`,
6 845 458 bytes) and predates the accepted R2 product source. R2-V02 explicitly
recorded it as *not reused*. The final wrapper must therefore be rebuilt around
the accepted payload frozen above.

## 3. Authoritative product / version metadata

No new version was selected; the existing authoritative metadata is
self-consistent and was used unchanged.

| Authority | Value |
|---|---|
| `pyproject.toml` `[project].version` | `1.1.0` |
| Packaged executable FileVersion / ProductVersion | `1.1.0` |
| `.iss` `MyAppId` / `MyAppName` / `MyAppVersion` / `MyAppPublisher` | `MDConverter.Quansheng2022` / `MD Converter` / `1.1.0` / `Quansheng2022` |
| Published identity (RC manifest, P12-10) | identical (`AppId`, `AppName`, `AppVersion`, publisher) |

## 4. Installer script and input resolution

| Item | Value |
|---|---|
| Installer script | `packaging/windows/MD_Converter.iss` (tracked) |
| Script SHA-256 | `EBB0979972348ECA2926BC3095049BDB047B36F206E9D66E2A1C7E468B91CE03` |
| Payload input | `..\..\dist\MD_Converter_Lite\MD_Converter_Lite.exe` → resolves to the accepted payload |
| Runtime input | `..\..\dist\MD_Converter_Lite\_internal\*` → resolves (268-file payload) |
| Compliance inputs | `..\..\EULA.txt`, `..\..\THIRD_PARTY_NOTICES.txt` → both resolve |
| Output | `..\..\dist_installer` → `MD_Converter_v1.1.0_Setup.exe` |

The script resolves the accepted payload and the existing frozen install
semantics (per-user `{localappdata}\Programs\MD_Converter`,
`PrivilegesRequired=lowest`, unchanged `AppId`, unchanged shortcut/uninstall
contract). **No bounded G1 packaging correction was required or applied.**

## 5. Build tool

| Item | Value |
|---|---|
| Compiler | official Inno Setup command-line compiler `ISCC.exe` |
| Version | `Inno Setup 7.1.0` (registry uninstall entry: DisplayName `Inno Setup 7.1.0`, Publisher `jrsoftware.org`) |
| Path | `C:\Users\Quansheng\AppData\Local\Programs\Inno Setup 7\ISCC.exe` |
| Install scope | per-user (`%LOCALAPPDATA%\Programs\Inno Setup 7`), admin rights not required |
| Action taken | none — the official compiler was already installed on this host |

No build tool was installed, upgraded, replaced, or fetched during this WP.

## 6. PASS criteria

| Criterion | Result |
|---|---|
| Payload identity frozen | PASS |
| Product version metadata resolved from existing authority | PASS (`1.1.0`) |
| Official `ISCC.exe` available | PASS (Inno Setup 7.1.0) |
| `.iss` resolves the accepted payload | PASS |
| Product source drift | `0` (only the pre-existing, untouched `md_converter/cli.py` 2/2 hunk) |
| Broad security/ACL/system mutation | none |

## 7. Result

`WP-R2PRERC01-01 — PASS`

Next: WP-R2PRERC01-02 builds the final installer with this frozen payload and
compiler.
