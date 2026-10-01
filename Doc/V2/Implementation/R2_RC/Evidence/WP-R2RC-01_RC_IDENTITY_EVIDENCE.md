# WP-R2RC-01 — RC Identity Evidence

**Work package:** WP-R2RC-01 — Create and verify canonical RC identity
**Program:** R2-RC (P12-23) — Release Candidate freeze
**Change classification:** `G2_OR_RELEASE` — release identity/freeze gate
**Governing SPEC:** `CANONICAL_SPEC.md` (FROZEN 1.1) — `SPEC-GOAL-003`, `SPEC-INV-001`,
`SPEC-INV-006`, `SPEC-INV-010`, `SPEC-INV-012`, `SPEC-QA-002`
**Upstream gates:** R2-V01 / R2-V02 / R2-V03 / R2-V04 / R2-PRE-RC-01 all CLOSED / ACCEPTED
**Result:** `PASS`

Scope of this WP: bind and verify one candidate identity. No product source change, no installer
rebuild, no duplicated V01/V02/V03/V04/PRE-RC testing.

## 1. Freeze context

| Item | Value |
|---|---|
| Branch | `master` |
| Freeze-time HEAD | `286fdd6b61a5b1603a3a00d9508f44564f6a1635` (`R2PRERC01-03 verify final installer lifecycle and close gate`) |
| HEAD = R2-PRE-RC-01 closure commit | yes |
| Last product-source commit | `bd1a818` (`IC-04 guard image width configuration contract`) |
| Golden baseline | `md_converter/tests/golden/sample.expected.json` |

## 2. Recomputed release-critical identities

Recomputation used the same deterministic algorithm as the accepted gate
(`Verification/r2rc_identity_check.ps1`, mirroring
`Doc/V2/Implementation/R2_PRE_RC_01/Verification/r2prerc01_payload_identity.ps1`; the payload tree
digest is SHA-256 over the sorted `"<relative path> <size> <sha256>"` lines of the payload tree).

| Identity | Expected (accepted evidence) | Recomputed 2026-10-01 | Match |
|---|---|---|---|
| Installer SHA-256 | `4B56FC989BAB7FF7E648CC29DFE5A6D944B2B8EFC420F11DE8D0ECF8294FFDE9` (PRE-RC-02) | `4B56FC989BAB7FF7E648CC29DFE5A6D944B2B8EFC420F11DE8D0ECF8294FFDE9` | PASS |
| Installer bytes | `51186717` (PRE-RC-02) | `51186717` | PASS |
| Packaged EXE SHA-256 | `68524527CDC5718CE31A1F0454EAFB0FF64C52D5C838716AC1277445DE0E3021` (V02-01 / PRE-RC-01/02/03) | `68524527CDC5718CE31A1F0454EAFB0FF64C52D5C838716AC1277445DE0E3021` | PASS |
| Packaged EXE bytes | `6926650` (PRE-RC-01) | `6926650` | PASS |
| Payload tree digest | `ecb6a4453f342af51cbc2b26b175489cb4ad963bc987a7407ff10ff0f8efa96c` (PRE-RC-01) | `ecb6a4453f342af51cbc2b26b175489cb4ad963bc987a7407ff10ff0f8efa96c` | PASS |
| Payload file count | `268` (PRE-RC-01) | `268` | PASS |
| Payload total bytes | `166231301` (PRE-RC-01) | `166231301` | PASS |
| Golden baseline SHA-256 | `6D589013B8024C158DE5D29B93BDFEF68F2F406045C805DAB61F8E513725829A` (V04 §1 / PRE-RC-03) | `6D589013B8024C158DE5D29B93BDFEF68F2F406045C805DAB61F8E513725829A` | PASS |
| Installer script SHA-256 | `EBB0979972348ECA2926BC3095049BDB047B36F206E9D66E2A1C7E468B91CE03` (PRE-RC-01) | `EBB0979972348ECA2926BC3095049BDB047B36F206E9D66E2A1C7E468B91CE03` | PASS |

Release-critical identity mismatches: **0**. Artifact mismatches: **0**.

## 3. Authoritative product / version identity

| Source | Value |
|---|---|
| `pyproject.toml` `[project].version` | `1.1.0` |
| `md_converter/__init__.py` `__version__` | `1.1.0` |
| Packaged EXE version resource (FileVersion / ProductVersion / ProductName / CompanyName) | `1.1.0` / `1.1.0` / `MD Converter` / `Quansheng2022` |
| `.iss` `MyAppId` / `MyAppName` / `MyAppVersion` / `MyAppPublisher` | `MDConverter.Quansheng2022` / `MD Converter` / `1.1.0` / `Quansheng2022` |

All authorities agree. No release-version decision was required or made (`G2` if it were).
Observation for the Human reviewer: the version string `1.1.0` is shared with the earlier, already
tagged `v1.1.0` production release (annotated tag at `e025a36`); the RC is distinguished by
manifest + closure commit + hashes. No re-versioning was performed or is authorized here.

## 4. Upstream gate chain resolution

| Gate | Closure commit | Status resolved from |
|---|---|---|
| R2-V01 | `1e1cfc7062736a687147e642442677d24144204f` | R2_V01_CLOSURE_EVIDENCE §1/§14 |
| R2-V02 | `93d7cbde1302c60b25206cba1288f4b751e77860` | R2_V02_CLOSURE_EVIDENCE §2/§12 |
| R2-V03 | `39c5f53eefef9592da5f5a62bb98d235c7025aca` | R2_V03_CLOSURE_EVIDENCE §3/§13 |
| R2-V04 | `1ff46215f17c068b7f8b79a0ee75faf25bbaf595` | R2_V04_CLOSURE_EVIDENCE §1/§11 |
| R2-PRE-RC-01 | `286fdd6b61a5b1603a3a00d9508f44564f6a1635` | R2_PRE_RC_01_CLOSURE_EVIDENCE §5/§12 |

All five gates are CLOSED / ACCEPTED. No upstream inconsistency was found; no gate was re-run.

## 5. Protected-input drift check

| Protected input | Drift caused by R2-RC | Evidence |
|---|---|---|
| Product runtime source | `0` | `git status --porcelain -- md_converter packaging pyproject.toml tools` → only the inherited `md_converter/cli.py` docstring-only hunk (`git diff --numstat` = `2 2`), untouched by this task |
| Packaged payload bytes | `0` | payload tree digest recomputed identical |
| Packaged EXE bytes | `0` | EXE SHA-256 recomputed identical |
| Installer bytes | `0` | installer SHA-256 and size recomputed identical |
| Product / version metadata | `0` | `pyproject.toml`, `__init__.py`, EXE resource and `.iss` all `1.1.0`, unchanged |
| Golden baseline | `0` | baseline SHA-256 recomputed identical |
| Accepted gate results | `0` | no gate re-run, no gate evidence modified |

Inherited pre-existing working-tree state, disclosed for auditability and preserved untouched:
`.gitignore`, `README.md`, `md_converter/cli.py` (docstring-only, 2/2), plus an unstaged relocation
of the R2-V01 / R2-V02 evidence trees. Relocated closure-evidence files were hash-compared against
their committed blobs: `R2_V01_CLOSURE_EVIDENCE.md` and `R2_V02_CLOSURE_EVIDENCE.md` are
byte-identical; the relocated `WP-R2V02-01_RESULT.json` harness output is not byte-identical to its
committed blob. Reported only (`SPEC-INV-012`); the authoritative records remain the Git blobs at
the closure commits in §4.

## 6. Limitations extracted (no expansion)

The accepted limitations and deferred debt were extracted in substance from R2-V01 §11, R2-V02 §9,
R2-V03 §8/§12, R2-V04 §5/§7/§9 and R2-PRE-RC-01 §11 and are recorded in `R2_RC_MANIFEST.md` §7
(L1–L14). No limitation was reclassified, reopened, promoted or invented.

## 7. Artifacts created by this WP

```text
Doc/V2/Implementation/R2_RC/R2_RC_MANIFEST.md
Doc/V2/Implementation/R2_RC/Evidence/WP-R2RC-01_RC_IDENTITY_EVIDENCE.md
Doc/V2/Implementation/R2_RC/Verification/r2rc_identity_check.ps1
```

## 8. Required PASS values

```text
release-critical identity mismatches : 0
artifact mismatches                  : 0
product source drift (task-caused)   : 0
installer drift                      : 0
Golden drift                         : 0
manifest internally consistent       : yes
product source changes               : 0
installer rebuilds                   : 0
gate re-runs                         : 0
```

Failure classification per the product specification: `PASS`.

## 9. Commit

`R2RC-01 freeze release candidate identity` — exact-file staging of the three files in §7 only.

Green → continue automatically to WP-R2RC-02.
