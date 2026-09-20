# MD_Converter v1.0.1 — Human Production Approval & Release Tag Approval

| Field | Value |
| --- | --- |
| Approved Release | **v1.0.1**（P11 Patch Production Release） |
| Approval Date | 2026-09-21 |
| Approved Maintenance Scope | P11-MNT-006, P11-MNT-007, P11-MNT-008, P11-MNT-009 |
| Approved RC Payload Source SHA | `48efc925bfcee0695457168ebcd7c7a0c6d408b5` |
| Approved Release Evidence Archive SHA | `c03b5c55eda1a792b399bdfab133ef9dc9c73e62` |
| Approved Wheel | `md_converter-1.0.1-py3-none-any.whl` |
| Approved Wheel SHA256 | `D535057AE09BD52B1BDE218633F1FC61497C5C4F98C8C20C8259E5C004861F25` |
| Approved Sdist | `md_converter-1.0.1.tar.gz` |
| Approved Sdist SHA256 | `116967BDE5550ED9964A1CF72D0FBF89F89292F8274E7E72F6C4557EAF09B71E` |
| Production Release Approval | **APPROVED** |
| Release Tag Approval | **APPROVED** — annotated tag `v1.0.1` |
| Release Tag Target | this approval-record commit (derived solely from `c03b5c55`; the tag object SHA is recorded externally by the release report) |
| Publication / remote push | NOT AUTHORIZED BY THIS APPROVAL |
| P11 Final Closure / PLAN_D / P12 | NOT AUTHORIZED |

---

## P11 Release Decision Record（`P11/templates/P11_RELEASE_DECISION_TEMPLATE.md`）

```text
Candidate Version:                1.0.1

Included Maintenance Packages:    P11-MNT-006 / P11-MNT-007 / P11-MNT-008 / P11-MNT-009

P1 Open:                          0

Release-Critical P2 Open:         0

Regression:                       PASS — 308/308 collected/passed, 0 failed, 0 errors

Required Skip:                    0

Golden:                           PASS（baseline 未修改）

Acceptance:                       PASS — 35/35

DOCX:                             PASS（代表性文档：MNT-006/007/008/009 各自 PASS）

FinalArtifactQA:                  PASS

COM:                              PASS（Word COM 必需路径实际执行，非 skip）

Build:                            PASS（python -m build，产物位于仓库外）

Wheel:                            md_converter-1.0.1-py3-none-any.whl（318052 bytes）

Sdist:                            md_converter-1.0.1.tar.gz（266885 bytes）

Hashes:                           wheel D535057A…1F25 / sdist 116967BD…B71E（完整值见上表）

Fresh Install:                    PASS（仓库外全新 venv，非 editable，依赖解析成功）

CLI Smoke:                        PASS（--help / md-converter-check / 转换 均 exit 0，无 traceback）

Version Consistency:              PASS（mismatch = 0；CLI 无 --version 选项）

Release Notes:                    COMPLETE（RELEASE_NOTES_v1.0.1.md）

Manifest:                         COMPLETE（RELEASE_MANIFEST_v1.0.1.json）

Known Limitations:                CURRENT（NOT REQUIRED / unchanged）

Git Tree:                         CLEAN（tracked）

Technical Gate:
PASS

Human Production Approval:
APPROVED（2026-09-21）

Final Decision:
APPROVED — v1.0.1 patch production release; annotated tag v1.0.1 authorized
```

---

## Accepted verification basis（Human-approved）

```text
Canonical Regression:   308/308 PASS   Failed: 0   Errors: 0   Required Skip: 0
Acceptance:             35/35 PASS
Golden:                 PASS
FinalArtifactQA:        PASS
Word COM Gate:          PASS
Fresh Install:          PASS
CLI Smoke:              PASS
Version Consistency:    PASS

Open P1 Release Blockers:   0
Release-Critical P2:        0
```

---

## Boundary statement

```text
Product code / tests / version metadata / release artifacts /
Canonical Specification / Architecture / Golden / Acceptance source /
dependencies:  unchanged by this approval record

Release tag:   v1.0.1（annotated，local only）
Publication:   NOT PERFORMED（remote push NOT AUTHORIZED）
P11:           FROZEN / ACTIVE
P11-MNT-010:   NOT CREATED / FREE / UNASSIGNED
Next action:   HUMAN DECISION REQUIRED after tag creation
```
