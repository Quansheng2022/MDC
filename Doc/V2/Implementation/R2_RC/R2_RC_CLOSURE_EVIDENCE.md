# R2-RC — Release Candidate Freeze
## Closure & Human-Acceptance Handoff Evidence

**Program:** R2-RC (P12-23) — Release Candidate freeze, release train R2
**Change classification:** `G2_OR_RELEASE` — release identity/freeze gate
**Governing SPEC:** `CANONICAL_SPEC.md` (FROZEN 1.1) — `SPEC-GOAL-003`, `SPEC-INV-001`,
`SPEC-INV-006`, `SPEC-INV-010`, `SPEC-INV-012`, `SPEC-QA-002`
**Work packages:** 2 / 2 PASS
**Upstream gates:** R2-V01 / R2-V02 / R2-V03 / R2-V04 / R2-PRE-RC-01 all CLOSED / ACCEPTED
**Final status:** `R2-RC — FROZEN / ACCEPTED / READY FOR HUMAN ACCEPTANCE`

## 1. RC manifest and freeze anchor

| Item | Value |
|---|---|
| Canonical RC manifest | `Doc/V2/Implementation/R2_RC/R2_RC_MANIFEST.md` |
| Manifest blob at WP-01 commit | `4b0ef1ecae284c2075f1b902035564323a31d231` |
| RC closure commit | this commit — `R2RC-02 close release candidate freeze and hand off` |
| Viable RC identity anchor | manifest + closure commit + accepted installer/EXE SHA-256 (no Git tag; §11) |

## 2. RC product / version identity

```text
product name / version : MD Converter 1.1.0
publisher              : Quansheng2022
application id         : MDConverter.Quansheng2022
version decision       : none (existing authority used unchanged)
```

All version authorities agree on `1.1.0`: `pyproject.toml` `[project].version`,
`md_converter/__init__.py` `__version__`, the packaged executable version resource, and
`packaging/windows/MD_Converter.iss` `MyAppVersion`.

## 3. Final installer and packaged executable identity

| Artifact | Path | Size | SHA-256 |
|---|---|---|---|
| Final installer | `dist_installer\MD_Converter_v1.1.0_Setup.exe` | `51186717` | `4B56FC989BAB7FF7E648CC29DFE5A6D944B2B8EFC420F11DE8D0ECF8294FFDE9` |
| Packaged executable | `dist\MD_Converter_Lite\MD_Converter_Lite.exe` | `6926650` | `68524527CDC5718CE31A1F0454EAFB0FF64C52D5C838716AC1277445DE0E3021` |

Payload tree digest (268 files, 166231301 bytes):
`ecb6a4453f342af51cbc2b26b175489cb4ad963bc987a7407ff10ff0f8efa96c`.
Golden baseline `md_converter/tests/golden/sample.expected.json`:
`6D589013B8024C158DE5D29B93BDFEF68F2F406045C805DAB61F8E513725829A`.

## 4. Two-commit chain (exact-file staging only)

| # | Commit | Message | Staged files |
|---|---|---|---|
| 1 | `4b0ef1e` | `R2RC-01 freeze release candidate identity` | `R2_RC_MANIFEST.md`, `Evidence/WP-R2RC-01_RC_IDENTITY_EVIDENCE.md`, `Verification/r2rc_identity_check.ps1` |
| 2 | *(this commit)* | `R2RC-02 close release candidate freeze and hand off` | `R2_RC_CLOSURE_EVIDENCE.md` |

`git diff --cached --name-status` for WP-01 showed exactly the three `A` entries above and nothing
else. No `git add .` / `git add -A` / `git clean -fd` / `git reset --hard` / `git restore .` was
used. The inherited dirty/untracked state (`.gitignore`, `README.md`, `md_converter/cli.py`, the
unstaged R2-V01 / R2-V02 evidence relocation and all other untracked trees) was preserved and never
staged.

## 5. Accepted gate chain

| Gate | Closure commit | Status |
|---|---|---|
| R2-V01 Competitive Foundation Integrated Verification | `1e1cfc7062736a687147e642442677d24144204f` | CLOSED / ACCEPTED |
| R2-V02 Packaged Multi-file Runtime Verification | `93d7cbde1302c60b25206cba1288f4b751e77860` | CLOSED / ACCEPTED |
| R2-V03 Native Word Visual Verification | `39c5f53eefef9592da5f5a62bb98d235c7025aca` | CLOSED / ACCEPTED |
| R2-V04 Golden / Browser Environment Retest | `1ff46215f17c068b7f8b79a0ee75faf25bbaf595` | CLOSED / ACCEPTED |
| R2-PRE-RC-01 Final Inno Setup Wrapper Rebuild & Installer Verification | `286fdd6b61a5b1603a3a00d9508f44564f6a1635` | CLOSED / ACCEPTED |

The chain is complete and consistent; no gate was re-run by R2-RC.

## 6. Manifest reference verification (against committed Git content)

The WP-01 manifest was re-read from committed Git content — not from the working tree — and every
referenced evidence/identity path was resolved with `git cat-file -e <ref>:<path>`:

| Referenced path | Resolved at | Result |
|---|---|---|
| `Doc/V2/Implementation/R2_V01/R2_V01_CLOSURE_EVIDENCE.md` | `1e1cfc7` | OK |
| `Doc/V2/Implementation/R2_V02/R2_V02_CLOSURE_EVIDENCE.md` | `93d7cbd` | OK |
| `Doc/V2/Implementation/R2_V03/R2_V03_CLOSURE_EVIDENCE.md` | `39c5f53` | OK |
| `Doc/V2/Implementation/R2_V04/R2_V04_CLOSURE_EVIDENCE.md` | `1ff4621` | OK |
| `Doc/V2/Implementation/R2_PRE_RC_01/R2_PRE_RC_01_CLOSURE_EVIDENCE.md` | `286fdd6` | OK |
| `Doc/V2/Implementation/R2_PRE_RC_01/Evidence/WP-R2PRERC01-01_PAYLOAD_IDENTITY.json` | `286fdd6` | OK |
| `Doc/V2/Implementation/R2_PRE_RC_01/Evidence/WP-R2PRERC01-02_INSTALLER_IDENTITY.json` | `286fdd6` | OK |
| `Doc/V2/Implementation/R2_PRE_RC_01/Evidence/WP-R2PRERC01-03_LIFECYCLE_RESULT.json` | `286fdd6` | OK |
| `Doc/V2/Implementation/P12-10/RC_MANIFEST.md` | `286fdd6` | OK |
| `Doc/V2/Implementation/R2_RC/R2_RC_MANIFEST.md` | `4b0ef1e` | OK |
| `Doc/V2/Implementation/R2_RC/Evidence/WP-R2RC-01_RC_IDENTITY_EVIDENCE.md` | `4b0ef1e` | OK |
| `Doc/V2/Implementation/R2_RC/Verification/r2rc_identity_check.ps1` | `4b0ef1e` | OK |

The R2-V01 / R2-V02 and R2-PRE-RC-01 closure trees were also confirmed byte-identical to their
committed blobs at their relocated (`..._Spec_Plan_Master`) locations where those files exist on
disk. The authoritative records remain the Git blobs at the closure commits above.

## 7. Freeze integrity confirmation

Post-WP-01 re-run of `Doc/V2/Implementation/R2_RC/Verification/r2rc_identity_check.ps1`
(`captured_at 2026-10-01T10:38:03+08:00`, `head 4b0ef1ecae284c2075f1b902035564323a31d231`):

```text
release-critical identity mismatches : 0
artifact mismatches                  : 0
installer identity                   : unchanged  (4B56FC98…4FFDE9 / 51186717 bytes)
packaged EXE identity                : unchanged  (68524527…0E3021 / 6926650 bytes)
payload tree digest                  : unchanged  (ecb6a445…f8efa96c)
Golden baseline                      : unchanged  (6D589013…25829A)
product runtime source change        : none       (git status -- md_converter packaging pyproject.toml → only the inherited, untouched md_converter/cli.py docstring hunk)
packaging semantic change            : none       (packaging/windows/MD_Converter.iss unmodified)
```

## 8. Known limitation reference

Accepted limitations and deferred debt are recorded in `R2_RC_MANIFEST.md` §7 (L1–L14), sourced
verbatim in substance from R2-V01 §11, R2-V02 §9, R2-V03 §8/§12, R2-V04 §5/§7/§9 and
R2-PRE-RC-01 §11. No limitation was discovered, reclassified, reopened or promoted by R2-RC.

Recorded observations (reported, not repaired — `SPEC-INV-012`), full text in `R2_RC_MANIFEST.md`
§12: the `SPEC-FUNC-021` Release Evidence artifact has not been regenerated for R2 (release-process
action, impossible without the reruns this gate is forbidden to perform); the inherited relocation
of the R2-V01 / R2-V02 evidence trees; and the pre-existing dirty tracked files.

## 9. Rollback identity

```text
last accepted pre-RC closure commit : 286fdd6b61a5b1603a3a00d9508f44564f6a1635
accepted final installer SHA-256    : 4B56FC989BAB7FF7E648CC29DFE5A6D944B2B8EFC420F11DE8D0ECF8294FFDE9
accepted packaged EXE SHA-256       : 68524527CDC5718CE31A1F0454EAFB0FF64C52D5C838716AC1277445DE0E3021
accepted payload tree digest         : ecb6a4453f342af51cbc2b26b175489cb4ad963bc987a7407ff10ff0f8efa96c
accepted Golden baseline SHA-256     : 6D589013B8024C158DE5D29B93BDFEF68F2F406045C805DAB61F8E513725829A
```

No rollback was performed.

## 10. Invalidation policy

This candidate is immutable after closure. Any change to a protected release input — product runtime
source, renderer/Core/QA behaviour, configuration semantics, payload bytes, installer bytes,
installer semantics, product/version metadata, or the Golden semantic baseline — invalidates this RC
and requires: classify the change → run only the minimum affected gates → rebuild the installer if
the payload changed → issue a new RC identity. Human-Acceptance documentation that leaves the
protected identities unchanged does not invalidate the RC. Full text in `R2_RC_MANIFEST.md` §10.

## 11. Git tag decision

Tag inventory at closure: `v1.0.0` (`e1e5060`), `v1.0.1` (`146c130`), `v1.1.0` (`9f32090`) — all
annotated release tags; `git tag -l "*rc*"` returns none. No authoritative RC tag naming convention
exists in this repository, and the annotated `v1.1.0` tag already identifies the earlier 1.1.0
production release, so creating any tag here would additionally require a release-version decision.

Decision: **no tag created, closure not blocked.** The canonical freeze anchor is the RC closure
commit plus the manifest and artifact hashes above. No tag was pushed; no remote operation was
performed.

## 12. Counters

| Metric | Required | Actual |
|---|---|---|
| RC identity mismatches | 0 | `0` |
| Artifact mismatches | 0 | `0` |
| Product source drift (task-caused) | 0 | `0` |
| Installer drift | 0 | `0` |
| Golden drift | 0 | `0` |
| Unresolved RC blockers | 0 | `0` |
| Product source changes | 0 | `0` |
| Installer rebuilds | 0 | `0` |
| Source / packaged / Word / Golden / installer-lifecycle reruns | 0 | `0` |
| Truthful commits | 2 | `2` |
| Tags created | 0 (optional) | `0` |

Failure classification per the product specification: `PASS`.

## 13. Human Acceptance

```text
Human Acceptance = PENDING
```

R2-RC does not perform Human Acceptance and does not claim it. The Human is asked to evaluate
installation, launch, the primary conversion workflow, the batch workflow where desired, the
usefulness and aesthetics of the Word output, and overall product readiness — against the exact
candidate identified in §1–§3. Machine-verification gates remain accepted and are not re-run.

## 14. Definition of Done

- 2 cohesive WPs independently verified and committed ✓
- canonical RC manifest created ✓
- release-critical hashes verified against accepted evidence ✓
- upstream gate chain complete and recorded ✓
- accepted features summarized without expansion ✓
- known limitations recorded without reclassification ✓
- rollback identity recorded ✓
- RC invalidation rules explicit ✓
- product source drift = 0 ✓
- installer drift = 0 ✓
- Golden drift = 0 ✓
- unresolved RC blockers = 0 ✓
- Human Acceptance remains PENDING ✓

## 15. Final status

`R2-RC — FROZEN / ACCEPTED / READY FOR HUMAN ACCEPTANCE`

STOP. Human Acceptance is not started by this task.
