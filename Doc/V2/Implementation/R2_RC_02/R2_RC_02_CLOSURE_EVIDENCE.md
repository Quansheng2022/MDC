# R2-RC-02 — Post-HA02 Release Candidate Freeze
## Closure Evidence

**Program:** R2-RC-02 — post-HA02 Release Candidate identity freeze
**Change classification:** `G2_OR_RELEASE` — identity freeze and handoff, no product change
**Governing SPEC:** `CANONICAL_SPEC.md` (FROZEN 1.1) — `SPEC-GOAL-003`, `SPEC-INV-001`,
`SPEC-INV-006`, `SPEC-INV-010`, `SPEC-INV-012`, `SPEC-QA-002`
**Work packages:** 1 / 1 PASS
**Canonical manifest:** `Doc/V2/Implementation/R2_RC_02/R2_RC_02_MANIFEST.md`
**Freeze anchor:** this commit — `R2RC02-01 freeze post-HA02 release candidate identity`
**Final status:** `R2-RC-02 — FROZEN / ACCEPTED / READY FOR TARGETED HUMAN RE-ACCEPTANCE`

No artifact was rebuilt, no gate was re-run, no shipped content was modified, and no Git tag was
created or moved. Raw recomputation: `Evidence/R2RC02-01_IDENTITY_RECHECK.json`.

## 1. Artifact identity match

Recomputed at freeze-time HEAD `196079ef2efa7ca5e86b5e8c2b744a710e4ae530` and compared with the
accepted HA-02 / R2-PRE-RC-02 evidence:

| Item | Recomputed | Accepted evidence | Match |
|---|---|---|---|
| Packaged EXE | 7,671,725 B / `C368DFEBBC3660020CB20119E4952D83E2791B5D231D6BE62A6D0E552C871270` | HA-02 closure `f851b64`, R2-PRE-RC-02 `196079e` | YES |
| Payload tree | 461 files / 279,011,814 B / `92daa5ea8c7031e0046ccd2d875990cfebbca9ba8767f9d4c00e9d1a316cf370` | R2-PRE-RC-02 closure | YES |
| Installer | 77,296,967 B / `C54ADF6225689F06886B6C326E897BEB294EBA13EFD7897328DD738F6CF3CA42` | R2-PRE-RC-02 closure | YES |
| `THIRD_PARTY_NOTICES.txt` | 11,890 B / `E4B8D7223F085357DF923226FECD5AA189206B65448C26D1AD772C7116229696` | HA-02 closure, R2-PRE-RC-02 distribution check | YES |
| Mermaid runtime asset (in payload) | `8D607D7EF1D077A8AA202E18E62212BFA992C68BFEABC5CF45D51A128FE6675D` | HA-02 closure | YES |
| Installer script | `EBB0979972348ECA2926BC3095049BDB047B36F206E9D66E2A1C7E468B91CE03` | R2-PRE-RC-01 / HA-02 | YES |
| Version authorities | `1.1.0` (pyproject, `__init__`, EXE resource, `.iss`) | unchanged | YES |

Artifact mismatches = **0**. No rebuild was performed for freshness.

## 2. Protected drift

| Protected input | Drift since `196079e` |
|---|---|
| Product source affecting shipped behaviour | `0` — `git status` shows only the inherited, untouched `md_converter/cli.py` docstring hunk; no other product path dirty |
| Packaged EXE bytes | `0` |
| Payload tree | `0` |
| Installer bytes | `0` |
| Required third-party notice bytes | `0` |
| Release version identity | `0` (unchanged `1.1.0`) |

Protected product drift = **0**; installer drift = **0**. The unrelated pre-existing dirty/untracked
working-tree state (`.gitignore`, `README.md`, `md_converter/cli.py`, the unstaged R2-V01/V02 evidence
relocation and other untracked trees) was preserved and never staged.

## 3. Previous RC preservation and supersession

| Item | Value |
|---|---|
| Previous RC | `Doc/V2/Implementation/R2_RC/R2_RC_MANIFEST.md`, closure `cd70d86` |
| Recorded status | **SUPERSEDED / AUDIT-ONLY** |
| Reason | HA-02 changed protected inputs (product source, payload, installer bytes) |
| Preserved artifacts | `release/R2RC_pre_HA02_preserved/` — `MD_Converter_Lite.exe` (6,926,650 B / `68524527…0E3021`), `MD_Converter_v1.1.0_Setup.exe` (51,186,717 B / `4B56FC98…4FFDE9`), `SHA256SUMS.txt` |
| Preservation failures | **0** — files present, sizes and hashes unchanged; nothing modified, deleted, renamed or overwritten |

The previous RC freeze commit `cd70d86` and its manifest were left untouched.

## 4. Production-release debt (`SPEC-INV-012` as labelled by the task documents)

```text
SPEC-INV-012 — OPEN / PRE-PRODUCTION RELEASE DEBT / NOT AN R2-RC-02 FREEZE BLOCKER
```

- The tracked release-evidence artifact was **not** regenerated for the R2 candidate: root
  `RC_EVIDENCE/RELEASE_EVIDENCE.md` + `release_evidence.json` still describe software version
  `1.0.0` (`build_id 8dfe51eb8df2`, checked `2026-09-01`); the v1.1.0-era evidence is
  `RC_EVIDENCE/P12_v1.1.0/RELEASE_CANDIDATE_EVIDENCE.md`. Neither covers the post-HA02 candidate.
- It must be resolved **before Production Release**, by authoritative regeneration/sync or by an
  explicit canonical supersession/pointer decision. Generated release evidence must not be
  fabricated or hand-rewritten.
- It was **not** resolved here and does not block this RC freeze.
- Identifier note: `CANONICAL_SPEC.md` maps the release-evidence invariant to `SPEC-INV-010` /
  `SPEC-FUNC-021`; `SPEC-INV-012` is the "report extra problems, do not modify" invariant. Both are
  recorded and the Canonical Spec is authoritative for the mapping.

## 5. Git tag decision

```text
Git tag created = NO
```

Tag inventory unchanged: `v1.0.0` (`e1e5060`), `v1.0.1` (`146c130`), `v1.1.0`
(`9f32090d2b756b16b43f7f556116cdec918cdadd`). The annotated `v1.1.0` tag already identifies an older
production release, so creating/moving/reusing a release tag needs separate Human authority. No
version change was made.

## 6. Human Re-Acceptance handoff

```text
Human Re-Acceptance = PENDING — not started by this gate
```

Targeted scope (not the original 18-step acceptance):

1. the unchanged Mermaid fixture `test_mermaid_triangle_v2.md`;
2. one ordinary Markdown conversion;
3. a brief visual usability check.

The candidate to evaluate is exactly: packaged EXE `C368DFEB…C871270`, payload digest
`92daa5ea…16cf370`, installer `C54ADF62…F3CA42`, notice `E4B8D722…229696`, anchored at this RC-02
closure commit. The rebuilt candidate is currently installed on this machine and operational.

## 7. Gate counters

```text
artifact mismatches                 : 0
protected product drift             : 0
installer drift                     : 0
old RC preservation failures        : 0
unresolved RC-freeze blockers       : 0
product-code changes                : 0
package / installer rebuilds        : 0
upstream gate re-runs               : 0
Git tags created / moved / reused   : 0
truthful commits                    : 1
```

Failure classification per the gate contract: `PASS`.

## 8. Next step

Hand off to **targeted Human Re-Acceptance** (do not start it automatically). If the Human accepts,
resolve the pre-production release-evidence debt before Production Release, then execute Production
Release readiness.

`R2-RC-02 — FROZEN / ACCEPTED / READY FOR TARGETED HUMAN RE-ACCEPTANCE`
