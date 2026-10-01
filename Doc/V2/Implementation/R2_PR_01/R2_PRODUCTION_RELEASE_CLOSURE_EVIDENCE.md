# R2-PR-01 — Production Release Closure Evidence

**Program:** R2-PR-01 — Production Release Decision & Execution
**Governance:** `G2_OR_RELEASE` — Human-authorized local production release
**Release authority:** Human Authority directive (recorded in the decision record)
**Final status:** `R2 PRODUCTION RELEASE — RELEASED / ACCEPTED / PRODUCTION BASELINE ESTABLISHED`

No rebuild, no retest, no product/package/installer change and no remote publication occurred.

## 1. Human decision

```text
DECISION=RELEASE_EXACT_RC
VERSION=1.1.0
TAG_POLICY=NEW_IMMUTABLE_TAG
TAG_NAME=r2-prod-1.1.0
TAG_TARGET=R2_RC_02_FREEZE
PUBLICATION=LOCAL_ARCHIVE_ONLY
```

| Item | Value |
|---|---|
| Decision record | `Doc/V2/Implementation/R2_PR_01/R2_PRODUCTION_RELEASE_DECISION.md` |
| Decision commit | `140b1ab599a66c91075214fc29b657375b9c4935` (`R2PR01-01 record human production release decision`) |

## 2. Released candidate

| Item | Value |
|---|---|
| Product / version | `MD Converter` `1.1.0` |
| R2-RC-02 freeze commit | `ec06977debdbd2dd747e14ad2f27a9a4f9b74c3a` |
| Targeted Human Acceptance commit | `a8533a6e416c004b9a51a0a43d0ec50df3b77982` |
| R2-PRR-01 canonicalization commit | `d12ba44aa7c64976d015e39b50d93e6898e11abe` |
| Installer | `C54ADF6225689F06886B6C326E897BEB294EBA13EFD7897328DD738F6CF3CA42` / 77,296,967 B |
| Packaged EXE | `C368DFEBBC3660020CB20119E4952D83E2791B5D231D6BE62A6D0E552C871270` / 7,671,725 B |
| Payload tree | 461 files / 279,011,814 B / `92daa5ea8c7031e0046ccd2d875990cfebbca9ba8767f9d4c00e9d1a316cf370` |
| `THIRD_PARTY_NOTICES.txt` | `E4B8D7223F085357DF923226FECD5AA189206B65448C26D1AD772C7116229696` / 11,890 B |

All three artifact hashes and the payload digest were recomputed immediately before mutation and
matched the frozen R2-RC-02 identities; the canonical release-evidence pointer resolved to the same
candidate (0 mismatches, 0 ambiguity).

## 3. Production archive

| Item | Value |
|---|---|
| Archive path | `release/R2_PRODUCTION_RELEASE/` (created; did not previously exist) |
| Files | 10 (installer, packaged EXE, notices, canonical pointer MD + JSON, R2-RC-02 manifest, Human Acceptance record, Human decision record, production manifest, checksums) |
| Production manifest | `PRODUCTION_RELEASE_MANIFEST.json` — 2,708 B / `BFE00E2D65357704797ABCE726D883587567C33312F2C39154F7F2AA493B6631` |
| Checksums | `SHA256SUMS.txt` — 873 B / `CAE54F1BC97C2006C7EDD847765A8CAF255D34D2F7904953A6D30F56168DE0EC` |
| Archive integrity | 9/9 checksum entries re-verified against actual bytes — failures 0, missing 0 |
| Git-tracked copies (byte-identical) | `Doc/V2/Implementation/R2_PR_01/PRODUCTION_RELEASE_MANIFEST.json`, `Doc/V2/Implementation/R2_PR_01/SHA256SUMS.txt` |

The full 279 MB payload tree was not archived (no binding release rule requires it). Bytes were
copied only; nothing was rebuilt, patched or transformed.

## 4. Production audit tag

| Item | Value |
|---|---|
| Tag | `r2-prod-1.1.0` (annotated) |
| Tag object | `30692bc9e2b7429185276ad807e8f182148fed60` |
| Peeled commit | `ec06977debdbd2dd747e14ad2f27a9a4f9b74c3a` (R2-RC-02 freeze) |
| Annotation content | MD Converter 1.1.0 · R2 Production Baseline · R2-RC-02 freeze SHA · installer SHA-256 · Human Production Release approval reference (`140b1ab…`) · publication `LOCAL_ARCHIVE_ONLY` |
| Force used | NO |
| Pushed | NO |

Historical tag `v1.1.0` remains exactly `9f32090d2b756b16b43f7f556116cdec918cdadd` → commit
`e025a36c645039acb1bb38208db73e8550a76156`; `v1.0.0` and `v1.0.1` are unchanged.

## 5. Publication

```text
publication policy          : LOCAL_ARCHIVE_ONLY
remote publication actions  : 0
network mutations           : 0
```

The configured remote `origin` (https://github.com/Quansheng2022/MDC) was inspected for reporting
only during preflight; nothing was fetched, pushed or published.

## 6. Rollback

| Item | Value |
|---|---|
| Pre-HA02 superseded RC (exact path) | `release/R2RC_pre_ha02_preserved` (installer 51,186,717 B / `4B56FC98…4FFDE9`, EXE 6,926,650 B / `68524527…0E3021`, `SHA256SUMS.txt`) — preserved, untouched |
| Superseded RC manifest | `Doc/V2/Implementation/R2_RC/R2_RC_MANIFEST.md` (`cd70d86`) — audit-only |
| Rollback rule | Local-only release: revert the R2-PR-01 task commits and remove `release/R2_PRODUCTION_RELEASE/` only under explicit Human cancellation; deleting the new unpublished tag `r2-prod-1.1.0` requires explicit Human cancellation authority; historical tags and superseded RC evidence are never moved or deleted |

## 7. Counters

```text
artifact_identity_mismatches        = 0
archive_checksum_failures           = 0
missing_archive_files               = 0
historical_tag_mutations            = 0
unauthorized_remote_actions         = 0
old_rc_preservation_failures        = 0
unauthorized shipped-byte changes   = 0
unresolved_production_blockers      = 0
product / package / installer staged = 0
truthful commits                    = 2
```

## 8. Final status

`R2 PRODUCTION RELEASE — RELEASED / ACCEPTED / PRODUCTION BASELINE ESTABLISHED`

STOP. No maintenance, repository synchronization or further release work is started by this task.
