# R2-PR-01 — Human Production Release Decision

**Program:** R2-PR-01 — Production Release Decision & Execution
**Governance:** `G2_OR_RELEASE` — mandatory Human Authority gate
**Recorded at:** 2026-10-01T16:45:00+08:00
**Authority:** Human Authority (release decision owner) — the Agent does not approve its own release

## 1. Human directive (verbatim)

```text
DECISION=RELEASE_EXACT_RC
VERSION=1.1.0
TAG_POLICY=NEW_IMMUTABLE_TAG
TAG_NAME=r2-prod-1.1.0
TAG_TARGET=R2_RC_02_FREEZE
PUBLICATION=LOCAL_ARCHIVE_ONLY
```

Issued by Human Authority together with the R2-PR-01 post-Human-Gate execution plan
(`R2_PR_01_Post_Human_Gate_AI_Agent_Master_Instruction.md` §1 and the
`R2_PR_01_Post_Human_Gate_Minimum_Sufficient_Execution_Plan.md` "Required Human Directive" block).
The directive matches the required directive of that plan exactly; execution is authorized.

## 2. Accepted release candidate

| Item | Value |
|---|---|
| Product / version | `MD Converter` `1.1.0` |
| R2-RC-02 freeze commit | `ec06977debdbd2dd747e14ad2f27a9a4f9b74c3a` |
| Targeted Human Acceptance commit | `a8533a6e416c004b9a51a0a43d0ec50df3b77982` |
| R2-PRR-01 canonicalization commit | `d12ba44aa7c64976d015e39b50d93e6898e11abe` |
| HA-02 closure commit | `f851b64c3b65afe4c4d960346a9b19a9e2f3afd5` |
| R2-PRE-RC-02 closure commit | `196079ef2efa7ca5e86b5e8c2b744a710e4ae530` |

## 3. Release-critical identities (frozen)

| Artifact | Path | Size | SHA-256 |
|---|---|---|---|
| Installer | `dist_installer\MD_Converter_v1.1.0_Setup.exe` | 77,296,967 B | `C54ADF6225689F06886B6C326E897BEB294EBA13EFD7897328DD738F6CF3CA42` |
| Packaged EXE | `dist\MD_Converter_Lite\MD_Converter_Lite.exe` | 7,671,725 B | `C368DFEBBC3660020CB20119E4952D83E2791B5D231D6BE62A6D0E552C871270` |
| Payload tree | `dist\MD_Converter_Lite` | 461 files / 279,011,814 B | `92daa5ea8c7031e0046ccd2d875990cfebbca9ba8767f9d4c00e9d1a316cf370` (tree digest) |
| Third-party notices | `THIRD_PARTY_NOTICES.txt` | 11,890 B | `E4B8D7223F085357DF923226FECD5AA189206B65448C26D1AD772C7116229696` |

Authoritative release evidence: `RC_EVIDENCE/CURRENT_RELEASE_EVIDENCE_POINTER.md` and
`RC_EVIDENCE/current_release_evidence_pointer.json` (pointer consistency verified, 0 mismatches).

## 4. Release policy decided by Human Authority

| Policy | Decision |
|---|---|
| Release vs hold | `RELEASE_EXACT_RC` — release the exact accepted candidate, no rebuild |
| Version | `1.1.0` (unchanged) |
| Tag policy | `NEW_IMMUTABLE_TAG` |
| New tag name | `r2-prod-1.1.0` |
| Tag target | `R2_RC_02_FREEZE` → `ec06977debdbd2dd747e14ad2f27a9a4f9b74c3a` |
| Publication | `LOCAL_ARCHIVE_ONLY` — no remote publication, no network mutation |
| Production archive | `release/R2_PRODUCTION_RELEASE/` |

## 5. Historical tag preservation

The existing historical tag `v1.1.0`
(annotated tag object `9f32090d2b756b16b43f7f556116cdec918cdadd`, peeled commit
`e025a36c645039acb1bb38208db73e8550a76156`) is **immutable** under this release. It is not moved,
deleted, recreated, retargeted or force-updated, and `v1.0.0` / `v1.0.1` are likewise untouched.
The new audit tag `r2-prod-1.1.0` is separate and additionally identifies the R2 production
baseline.

## 6. Pre-mutation guards confirmed

```text
canonical pointer resolves to this candidate : YES (0 mismatches, 0 ambiguity)
installer / EXE / notice hashes match frozen : YES
payload digest matches frozen manifest       : YES (92daa5ea…16cf370, 461 files / 279,011,814 B)
new tag r2-prod-1.1.0 absent                 : YES
archive target release/R2_PRODUCTION_RELEASE absent : YES
historical v1.1.0 unchanged from preflight   : YES
shipped-content drift since accepted RC      : NONE
```

## 7. Authorization

```text
authority source        : Human Authority
execution authorized    : YES (WP-R2PR-02 local production release)
remote publication      : PROHIBITED
rebuild / retest        : NOT AUTHORIZED (and not performed)
```

This record is the auditable Human authorization for the R2 production release of the exact
R2-RC-02 candidate identified in §2/§3.
