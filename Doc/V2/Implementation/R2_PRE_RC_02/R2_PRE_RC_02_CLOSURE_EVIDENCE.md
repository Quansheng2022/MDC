# R2-PRE-RC-02 — Post-HA02 Delta Installer Verification
## Closure Evidence

**Program:** R2-PRE-RC-02 — post-HA02 release/distribution delta verification
**Change classification:** `G2_OR_RELEASE` — release engineering verification, no product change
**Governing SPEC:** `CANONICAL_SPEC.md` (FROZEN 1.1) — `SPEC-GOAL-003`, `SPEC-INV-001`,
`SPEC-INV-006`, `SPEC-FUNC-013`
**Work packages:** 1 / 1 PASS
**Upstream:** HA-02 closure `f851b64` (product fix `26336bd`), superseded RC `cd70d86`
**Final status:** `R2-PRE-RC-02 — CLOSED / ACCEPTED / POST-HA02 DELTA INSTALLER PASS`

This gate verifies only the installer/distribution risk introduced by HA-02. No R2-V01/V02/V03/V04
gate, no full source suite, no batch/profile matrix, no native-Word matrix and no full Golden run
were re-executed. No artifact was rebuilt: the accepted HA-02 payload and installer were installed
exactly as frozen.

## 1. Frozen input identities (recomputed, no rebuild)

| Input | Value | Matches HA-02 closure |
|---|---|---|
| HA-02 closure commit | `f851b64` | — |
| HA-02 product-fix commit | `26336bd` | — |
| Packaged EXE | 7,671,725 B / `C368DFEBBC3660020CB20119E4952D83E2791B5D231D6BE62A6D0E552C871270` | YES |
| Payload tree digest | `92daa5ea8c7031e0046ccd2d875990cfebbca9ba8767f9d4c00e9d1a316cf370` (461 files / 279,011,814 B) | YES |
| Installer | 77,296,967 B / `C54ADF6225689F06886B6C326E897BEB294EBA13EFD7897328DD738F6CF3CA42` | YES |
| `THIRD_PARTY_NOTICES.txt` | 11,890 B / `E4B8D7223F085357DF923226FECD5AA189206B65448C26D1AD772C7116229696` | YES |
| Mermaid runtime asset | `8D607D7EF1D077A8AA202E18E62212BFA992C68BFEABC5CF45D51A128FE6675D` | YES |
| Reproduction fixture | `D6F512CE05082FFC2B826A5E742FFC9D33537338BAED78798626DB5FE41CA02F` (unchanged) | YES |
| Installer script | `EBB0979972348ECA2926BC3095049BDB047B36F206E9D66E2A1C7E468B91CE03` (unchanged) | YES |

Raw: `Evidence/R2PRERC02-01_LIFECYCLE_RESULT.json` (`identities`), `Evidence/R2PRERC02-01_payload_identity.json`.
Artifact mismatch count = **0**.

## 2. Clean uninstall

| Check | Result |
|---|---|
| Normal uninstaller present (`unins000.exe`) | YES |
| Uninstall exit code | `0` |
| Installer-owned application files removed (`MD_Converter.exe`, `_internal`) | PASS |
| Distributed notice removed with the application | PASS |
| User workspace preserved (`Documents\MD_Converter\input`, `...\output`) | PASS — directories present, 6 files, 0 missing / 0 changed |

A pre-uninstall backup of the workspace was taken for auditability
(`build/r2prerc02/workspace_backup`); it was not needed.

## 3. Install of the accepted post-HA02 installer

| Check | Result |
|---|---|
| Install exit code | `0` |
| Install directory exists (`%LOCALAPPDATA%\Programs\MD_Converter`) | PASS |
| Installed EXE exists | PASS |
| Installed EXE identity equals the accepted HA-02 payload | PASS (`C368DFEB…C871270`) |
| Playwright runtime distributed (`_internal\playwright\driver\node.exe`) | PASS |
| Mermaid runtime asset distributed (`_internal\md_converter\renderer\assets\mermaid.min.js`) | PASS (`8D607D7E…E6675D`) |
| `THIRD_PARTY_NOTICES.txt` distributed to `{app}` per the frozen `.iss` contract | PASS (11,890 B, hash equals the authoritative repository file) |
| `EULA.txt` distributed | PASS |

## 4. Targeted installed verification (normal GUI path)

Both conversions were driven through the installed application's own GUI using the existing
UI-Automation smoke tool; raw captures `Evidence/R2PRERC02-01_gui_smoke_fixture.json` and
`…gui_smoke_control.json`.

| Check | Result |
|---|---|
| Case A rendered | YES |
| Case B rendered | YES |
| Case C rendered | YES |
| Raw Mermaid fallback | NO — 3 images, backgrounds `#ffffff`, `fallback_images = []` |
| DOCX opens | YES (128 paragraphs parsed) |
| Fixture conversion | PASS (smoke exit `0`), 63,641 B / SHA-256 `1114DDCE…5BC68D` |
| Non-Mermaid control (`AC001_simple.md`) | PASS (smoke exit `0`), 29,553 B, 0 images, no fallback |

## 5. Reinstall confirmation

| Check | Result |
|---|---|
| Uninstall exit code | `0` |
| Installed EXE removed | PASS |
| User workspace preserved again | PASS — 0 missing / 0 changed |
| Reinstall exit code | `0` |
| Reinstalled EXE identity | `C368DFEB…C871270` (equals the accepted payload) |
| Short Mermaid smoke (Case A control, `Verification/fixtures/case_a_smoke.md`) | PASS — 1 image, background `#ffffff`, no fallback, DOCX 37,804 B (`Evidence/R2PRERC02-01_reinstall_smoke.docx`) |
| Application operational after reinstall | YES (left installed) |

## 6. Gate counters

```text
artifact mismatch                     : 0
installed Mermaid fallback            : 0
non-Mermaid control failures          : 0
user-workspace destructive changes    : 0
notice/runtime distribution failures  : 0
product source drift                  : 0   (only the inherited, untouched md_converter/cli.py hunk)
payload drift                         : 0   (digest and file count unchanged after the lifecycle)
installer drift                       : 0   (C54ADF62…F3CA42 unchanged)
introduced failures                   : 0
unresolved blockers                   : 0
bounded packaging corrections used    : 0   (none needed)
truthful commits                      : 1
```

Failure classification per the gate contract: `PASS`.

## 7. Old RC rollback identity

| Item | Value |
|---|---|
| Superseded RC | `Doc/V2/Implementation/R2_RC/R2_RC_MANIFEST.md` (closure `cd70d86`), superseded by HA-02 |
| Old installer | 51,186,717 B / `4B56FC989BAB7FF7E648CC29DFE5A6D944B2B8EFC420F11DE8D0ECF8294FFDE9` |
| Old packaged EXE | 6,926,650 B / `68524527CDC5718CE31A1F0454EAFB0FF64C52D5C838716AC1277445DE0E3021` |
| Preserved copies | `release/R2RC_pre_HA02_preserved/` + `SHA256SUMS.txt` (untouched by this gate) |

The accepted HA-02 artifacts (payload `dist/`, installer `dist_installer/`, preserved as well) were
not overwritten or deleted.

## 8. Recommendation

The post-HA02 installer is installable, complete, uninstallable and reinstallable without touching
user data, and it distributes the Playwright/Mermaid runtime assets and the third-party notice
required by the frozen packaging contract. Its installed GUI renders the unchanged Mermaid fixture
with no raw fallback and converts an ordinary document normally.

Recommended next steps:

1. freeze a new R2 Release Candidate over this post-HA02 payload/installer
   (`C368DFEB…C871270` / `C54ADF62…F3CA42`);
2. run targeted Human re-acceptance: the Mermaid fixture, one normal conversion and a brief visual
   usability check.

No new RC was frozen by this gate, and Human Acceptance was not performed or claimed here.

`R2-PRE-RC-02 — CLOSED / ACCEPTED / POST-HA02 DELTA INSTALLER PASS`
