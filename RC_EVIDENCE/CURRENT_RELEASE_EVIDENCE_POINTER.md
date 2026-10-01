# Current Release Evidence Pointer — MD Converter v1.1.0 (post-HA02)

**Status:** `CURRENT_CANONICAL_RELEASE_EVIDENCE`
**Pointer schema:** `md-converter/release-evidence-pointer` v1.0
**Generated at:** 2026-10-01T16:30:00+08:00
**Canonical SPEC mapping:** `SPEC-INV-010` / `SPEC-FUNC-021 — Release Evidence`

This pointer resolves which release evidence is authoritative for the accepted post-HA02
MD Converter v1.1.0 release candidate. It exists because the repository carries several generations
of release evidence: the repository-root rule-generated pair describes an earlier 1.0.0 candidate,
and the P12-era v1.1.0 candidate evidence predates both the R2 train and the HA-02 Mermaid
remediation.

The historical generated evidence is **not** modified, regenerated or hand-rewritten by this
pointer, and this pointer does not synthesize a rule-generated `RELEASE_ELIGIBLE` result (no test,
QA, governance, regression or repair fields are invented here). It records authority and exact
artifact identities only. The machine-readable counterpart is
`RC_EVIDENCE/current_release_evidence_pointer.json`; the two files are semantically identical.

## Canonical facts

```text
- pointer_schema: md-converter/release-evidence-pointer
- pointer_version: 1.0
- status: CURRENT_CANONICAL_RELEASE_EVIDENCE
- spec_mapping: SPEC-INV-010 / SPEC-FUNC-021
- product_version: 1.1.0
- r2_rc_02_freeze_commit: ec06977debdbd2dd747e14ad2f27a9a4f9b74c3a
- human_acceptance_commit: a8533a6e416c004b9a51a0a43d0ec50df3b77982
- ha02_closure_commit: f851b64c3b65afe4c4d960346a9b19a9e2f3afd5
- r2_prerc02_closure_commit: 196079ef2efa7ca5e86b5e8c2b744a710e4ae530
- packaged_exe_path: dist/MD_Converter_Lite/MD_Converter_Lite.exe
- packaged_exe_absolute_path: C:\Users\Quansheng\Documents\projects\MD_Converter\dist\MD_Converter_Lite\MD_Converter_Lite.exe
- packaged_exe_bytes: 7671725
- packaged_exe_sha256: C368DFEBBC3660020CB20119E4952D83E2791B5D231D6BE62A6D0E552C871270
- payload_path: dist/MD_Converter_Lite
- payload_absolute_path: C:\Users\Quansheng\Documents\projects\MD_Converter\dist\MD_Converter_Lite
- payload_file_count: 461
- payload_total_bytes: 279011814
- payload_tree_digest_sha256: 92daa5ea8c7031e0046ccd2d875990cfebbca9ba8767f9d4c00e9d1a316cf370
- installer_path: dist_installer/MD_Converter_v1.1.0_Setup.exe
- installer_absolute_path: C:\Users\Quansheng\Documents\projects\MD_Converter\dist_installer\MD_Converter_v1.1.0_Setup.exe
- installer_bytes: 77296967
- installer_sha256: C54ADF6225689F06886B6C326E897BEB294EBA13EFD7897328DD738F6CF3CA42
- third_party_notices_path: THIRD_PARTY_NOTICES.txt
- third_party_notices_absolute_path: C:\Users\Quansheng\Documents\projects\MD_Converter\THIRD_PARTY_NOTICES.txt
- third_party_notices_bytes: 11890
- third_party_notices_sha256: E4B8D7223F085357DF923226FECD5AA189206B65448C26D1AD772C7116229696
```

## Current release authority

| Evidence | Role |
|---|---|
| `Doc/V2/Implementation/R2_RC_02/R2_RC_02_MANIFEST.md` | Canonical RC-02 manifest (freeze identity) |
| `Doc/V2/Implementation/R2_RC_02/R2_RC_02_CLOSURE_EVIDENCE.md` | RC-02 freeze closure |
| `Doc/V2/Implementation/R2_RC_02/Evidence/R2RC02-01_IDENTITY_RECHECK.json` | RC-02 identity recomputation |
| `Doc/V2/Implementation/R2_HUMAN_ACCEPTANCE_02/R2_TARGETED_HUMAN_ACCEPTANCE.md` | Targeted Human Re-Acceptance record — verdict `ACCEPT` |
| `Doc/V2/Implementation/R2_PRE_RC_02/R2_PRE_RC_02_CLOSURE_EVIDENCE.md` | Post-HA02 delta installer verification |
| `Doc/V2/Implementation/HA_02/HA_02_CLOSURE_EVIDENCE.md` | Mermaid rendering remediation closure |

Release chain: R2-RC-02 freeze `ec06977` → targeted Human Re-Acceptance `a8533a6`, over HA-02
closure `f851b64` and R2-PRE-RC-02 closure `196079e`.

## Historical / superseded evidence

| Evidence | Classification | Reason |
|---|---|---|
| `RC_EVIDENCE/RELEASE_EVIDENCE.md` | `HISTORICAL / SUPERSEDED FOR CURRENT P12 RELEASE` | Rule-generated evidence for the earlier 1.0.0 candidate (build_id `8dfe51eb8df2`, checked 2026-09-01) |
| `RC_EVIDENCE/release_evidence.json` | `HISTORICAL / SUPERSEDED FOR CURRENT P12 RELEASE` | Machine counterpart of the same earlier 1.0.0 evidence |
| `RC_EVIDENCE/P12_v1.1.0/RELEASE_CANDIDATE_EVIDENCE.md` | `HISTORICAL / SUPPLEMENTARY / PRE-HA02` | P12-era v1.1.0 candidate evidence, predating the R2 train and HA-02 |
| `Doc/V2/Implementation/R2_RC/R2_RC_MANIFEST.md` | `SUPERSEDED / AUDIT-ONLY` | First R2 RC (closure `cd70d86`); superseded by HA-02. Artifacts preserved in `release/R2RC_pre_ha02_preserved/` |

## Statements

```text
legacy generated evidence rewritten              : NO
frozen R2-RC-02 / R2-RC evidence modified        : NO
synthesized rule-generated RELEASE_ELIGIBLE      : NO
synthesized test/QA/governance/regression fields : NO
```

## SPEC-ID history note

Earlier records (the R2-RC-02 task documents and `R2_RC_02_MANIFEST.md` §12) referred to the
release-evidence requirement as `SPEC-INV-012`. `CANONICAL_SPEC.md` maps that requirement to
`SPEC-INV-010` (`SPEC-FUNC-021`); `SPEC-INV-012` is the "report extra problems, do not modify"
invariant. The historical label is retained here only as a pointer for those older records.
