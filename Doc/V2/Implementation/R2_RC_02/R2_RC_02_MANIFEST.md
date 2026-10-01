# R2 Release Candidate 02 — Post-HA02 Freeze Manifest

**RC identifier:** `MD Converter v1.1.0 R2-RC-02` — evidence-only label (no Git tag; see §11)
**RC build label:** `RC-20261001-R2-02`
**P12 mapping:** P12-23 (release-candidate freeze and handoff)
**Change classification:** `G2_OR_RELEASE` — release identity freeze, no product change
**Governing SPEC:** `CANONICAL_SPEC.md` (FROZEN 1.1) — `SPEC-GOAL-003`, `SPEC-INV-001`,
`SPEC-INV-006`, `SPEC-INV-010`, `SPEC-INV-012`, `SPEC-QA-002`, `SPEC-FUNC-013`
**Created by:** WP-R2RC02-01 · **Closed by:** `R2_RC_02_CLOSURE_EVIDENCE.md`
**Status:** `R2-RC-02 — FROZEN / ACCEPTED / READY FOR TARGETED HUMAN RE-ACCEPTANCE`

This manifest binds the already-accepted post-HA02 payload/installer into one immutable candidate.
It records release-relevant facts only; the full verification narratives remain in the upstream
closure evidence referenced in §7. No artifact was rebuilt, retested or modified by this freeze.

---

## 1. Product / version identity

| Item | Value |
|---|---|
| Product name | `MD Converter` |
| Product version | `1.1.0` — unchanged; no version decision was made by this gate |
| Publisher | `Quansheng2022` |
| Application id (Inno Setup `MyAppId`) | `MDConverter.Quansheng2022` |
| Version authorities | `pyproject.toml` `[project].version`, `md_converter/__init__.py` `__version__`, packaged EXE resource (FileVersion/ProductVersion `1.1.0`), `.iss` `MyAppVersion` — all agree |
| Installer metadata | FileVersion `1.1.0.0`, ProductVersion `1.1.0`, `MD Converter`, `Quansheng2022` |

The version string `1.1.0` is shared with the earlier production release identified by the annotated
`v1.1.0` tag. The post-HA02 candidate is distinguished by this manifest, the R2-RC-02 closure commit
and the exact artifact hashes; no version bump is authorized by this gate.

## 2. Source and freeze anchors

| Item | Value |
|---|---|
| Branch | `master` |
| Freeze-time HEAD | `196079ef2efa7ca5e86b5e8c2b744a710e4ae530` (`R2PRERC02-01 verify post-HA02 installer delta and close gate`) |
| HA-02 closure (product fix) | `26336bd` → HA-02 closure `f851b64` |
| R2-PRE-RC-02 closure | `196079e` |
| RC-02 freeze commit | this commit — `R2RC02-01 freeze post-HA02 release candidate identity` |
| Product-source drift since `196079e` | `0` (only the inherited, untouched `md_converter/cli.py` docstring hunk remains, as recorded by every R2 gate) |

## 3. Packaged executable identity

| Item | Value |
|---|---|
| Path | `dist\MD_Converter_Lite\MD_Converter_Lite.exe` |
| Size | `7671725` bytes |
| SHA-256 | `C368DFEBBC3660020CB20119E4952D83E2791B5D231D6BE62A6D0E552C871270` |
| Version resource | FileVersion `1.1.0`, ProductVersion `1.1.0`, ProductName `MD Converter`, CompanyName `Quansheng2022` |
| Installed as | `%LOCALAPPDATA%\Programs\MD_Converter\MD_Converter.exe` (verified byte-identical during HA-02 and R2-PRE-RC-02) |

## 4. Packaged payload identity

| Item | Value |
|---|---|
| Payload directory | `dist\MD_Converter_Lite` |
| Files | `461` |
| Total bytes | `279011814` |
| Payload tree digest (release-identity algorithm) | `92daa5ea8c7031e0046ccd2d875990cfebbca9ba8767f9d4c00e9d1a316cf370` |
| Mermaid runtime asset | `md_converter\renderer\assets\mermaid.min.js` (SHA-256 `8D607D7EF1D077A8AA202E18E62212BFA992C68BFEABC5CF45D51A128FE6675D`) |
| Playwright runtime | included (`_internal\playwright\driver\node.exe`); no Chromium binaries bundled |

## 5. Installer identity

| Item | Value |
|---|---|
| Filename / path | `MD_Converter_v1.1.0_Setup.exe` — `dist_installer\MD_Converter_v1.1.0_Setup.exe` |
| Size | `77296967` bytes |
| SHA-256 | `C54ADF6225689F06886B6C326E897BEB294EBA13EFD7897328DD738F6CF3CA42` |
| Installer script | `packaging/windows/MD_Converter.iss`, SHA-256 `EBB0979972348ECA2926BC3095049BDB047B36F206E9D66E2A1C7E468B91CE03` (unchanged) |
| Compiler | Inno Setup command-line compiler `ISCC.exe` (`Inno Setup 7.1.0`), per-user install (`PrivilegesRequired=lowest`) |
| Signing | none — recorded release condition, unchanged |

`dist_installer/` is not tracked by this repository's release process; the binary is identified by
path, size and SHA-256.

## 6. Third-party notice identity

| Item | Value |
|---|---|
| Path | `THIRD_PARTY_NOTICES.txt` (repository root; installed to `{app}\THIRD_PARTY_NOTICES.txt`) |
| Size | `11890` bytes |
| SHA-256 | `E4B8D7223F085357DF923226FECD5AA189206B65448C26D1AD772C7116229696` |
| Distribution verification | installed copy byte-identical (verified by R2-PRE-RC-02) |

The notice is an authoritative distribution file that this repository keeps untracked (like
`EULA.txt`); it is therefore identified by size and SHA-256 rather than by a Git blob. Section 13
describes the current distribution content (Playwright runtime bundled, Chromium/Edge discovered,
Mermaid asset redistributed with its MIT license).

## 7. Accepted upstream gate chain

Recorded by identity/reference only; none of these gates was re-run.

| Gate | Closure reference | Status |
|---|---|---|
| R2-V01 Competitive Foundation Integrated Verification | `1e1cfc7062736a687147e642442677d24144204f` | ACCEPTED |
| R2-V02 Packaged Multi-file Runtime Verification | `93d7cbde1302c60b25206cba1288f4b751e77860` | ACCEPTED |
| R2-V03 Native Word Visual Verification | `39c5f53eefef9592da5f5a62bb98d235c7025aca` | ACCEPTED |
| R2-V04 Golden / Browser Environment Retest | `1ff46215f17c068b7f8b79a0ee75faf25bbaf595` | ACCEPTED |
| HA-02 Mermaid Rendering Remediation | `26336bd` (fix) → `f851b64` (closure) | CLOSED / ACCEPTED |
| R2-PRE-RC-02 Post-HA02 Delta Installer Verification | `196079e` | CLOSED / ACCEPTED |

Evidence locations (unchanged):

```text
Doc/V2/Implementation/HA_02/HA_02_CLOSURE_EVIDENCE.md
Doc/V2/Implementation/R2_PRE_RC_02/R2_PRE_RC_02_CLOSURE_EVIDENCE.md
Doc/V2/Implementation/R2_RC/R2_RC_MANIFEST.md            (first RC — superseded, see §8)
Doc/V2/Implementation/R2_PRE_RC_01/R2_PRE_RC_01_CLOSURE_EVIDENCE.md
```

## 8. Previous RC supersession

| Item | Value |
|---|---|
| Previous RC | `Doc/V2/Implementation/R2_RC/R2_RC_MANIFEST.md` (first R2 RC, closure commit `cd70d86`) |
| Previous installer | `4B56FC989BAB7FF7E648CC29DFE5A6D944B2B8EFC420F11DE8D0ECF8294FFDE9` (51,186,717 B) |
| Previous packaged EXE | `68524527CDC5718CE31A1F0454EAFB0FF64C52D5C838716AC1277445DE0E3021` (6,926,650 B) |
| Status | **SUPERSEDED / AUDIT-ONLY** — a protected RC input (product source, payload and installer bytes) changed under HA-02 |
| Preservation | artifacts retained unchanged in `release/R2RC_pre_HA02_preserved/` with `SHA256SUMS.txt`; not modified, moved, renamed or deleted by this gate |

## 9. Rollback identity

Sufficient to return to the last accepted pre-HA02 state; no rollback was performed.

| Item | Value |
|---|---|
| Last accepted pre-HA02 RC closure commit | `cd70d86` |
| Pre-HA02 packaged EXE | `68524527CDC5718CE31A1F0454EAFB0FF64C52D5C838716AC1277445DE0E3021` |
| Pre-HA02 installer | `4B56FC989BAB7FF7E648CC29DFE5A6D944B2B8EFC420F11DE8D0ECF8294FFDE9` |
| Pre-HA02 payload tree digest | `ecb6a4453f342af51cbc2b26b175489cb4ad963bc987a7407ff10ff0f8efa96c` |
| Preserved location | `release/R2RC_pre_HA02_preserved/` |

## 10. RC invalidation rules

R2-RC-02 is immutable once closed and is invalidated by any change to a protected input:

```text
shipped product behaviour / product source
packaged EXE bytes
payload tree
installer bytes
required third-party notice bytes
release version identity
packaging / runtime dependency content
```

A change to any of these requires: classify the change → run only the minimum affected gates →
rebuild the installer if the payload changed → issue a new RC identity. Documentation-only Human
Re-Acceptance evidence added after the freeze does not invalidate this RC while the protected inputs
above remain unchanged.

## 11. Git tag and version guard

```text
Git tag created = NO
```

Tag inventory at freeze: `v1.0.0` (`e1e5060`), `v1.0.1` (`146c130`), `v1.1.0` (`9f32090d2b756b16b43f7f556116cdec918cdadd`) —
all unchanged. The annotated `v1.1.0` tag already identifies an older production release, and
creating, moving or reusing a release tag requires separate Human release-version/tag authority.
The authoritative freeze anchor is the R2-RC-02 closure commit plus this manifest and the artifact
hashes in §3–§6.

## 12. Production-release debt pointer

```text
SPEC-INV-012 — OPEN / PRE-PRODUCTION RELEASE DEBT / NOT AN R2-RC-02 FREEZE BLOCKER
```

The tracked Release Evidence artifact has not been regenerated for the R2 candidate:
`RC_EVIDENCE/RELEASE_EVIDENCE.md` and `RC_EVIDENCE/release_evidence.json` still describe the earlier
**1.0.0** candidate (`build_id 8dfe51eb8df2`, checked `2026-09-01`), while the v1.1.0-era evidence
lives at `RC_EVIDENCE/P12_v1.1.0/RELEASE_CANDIDATE_EVIDENCE.md`. Neither covers the post-HA02
candidate.

- It **must** be resolved before Production Release.
- Acceptable resolution is authoritative regeneration/sync of the release evidence, or an explicit
  canonical supersession/pointer decision. Generated release evidence must **not** be fabricated or
  hand-rewritten.
- It is **not** resolved by this freeze and does not block the RC freeze.

Note on the identifier: the R2-RC-02 task documents label this item `SPEC-INV-012`. In
`CANONICAL_SPEC.md` the release-evidence invariant is `SPEC-INV-010` (with `SPEC-FUNC-021`), while
`SPEC-INV-012` is the "report extra problems, do not modify" invariant. Both mappings are recorded;
the Canonical Spec is the authority for SPEC-ID mapping.

## 13. Human Re-Acceptance handoff

```text
Human Re-Acceptance = PENDING (not started by this gate)
```

Targeted (not the original 18-step acceptance):

1. the unchanged Mermaid fixture `test_mermaid_triangle_v2.md`;
2. one ordinary Markdown conversion;
3. a brief visual usability check.

Machine-verification gates (R2-V01 / V02 / V03 / V04, HA-02, R2-PRE-RC-02) remain accepted and are
not automatically re-run.

## 14. Acceptance criteria and status

| Criterion | Status |
|---|---|
| Accepted post-HA02 artifact identities match | PASS — 0 mismatches |
| Protected product/source drift = 0 | PASS |
| Installer drift = 0 | PASS |
| Previous RC preserved and explicitly superseded | PASS |
| Canonical RC-02 manifest exists | PASS — this file |
| RC-02 closure evidence exists | PASS — `R2_RC_02_CLOSURE_EVIDENCE.md` |
| Production-release debt recorded, not resolved | PASS — §12 |
| No Git tag created | PASS — §11 |
| Unresolved RC-freeze blockers | 0 |

`R2-RC-02 — FROZEN / ACCEPTED / READY FOR TARGETED HUMAN RE-ACCEPTANCE`
