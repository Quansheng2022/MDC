# R2-PRR-01 — Release Evidence Canonicalization
## Closure Evidence

**Program:** R2-PRR-01 — release evidence canonicalization (pre-production)
**Change classification:** `G2_OR_RELEASE` — release-evidence authority record, no product change
**Governing SPEC:** `CANONICAL_SPEC.md` (FROZEN 1.1) — `SPEC-INV-010`, `SPEC-FUNC-021`
**Work packages:** 1 / 1 PASS
**Inputs:** R2-RC-02 freeze `ec06977`, targeted Human Re-Acceptance `a8533a6`, HA-02 `f851b64`,
R2-PRE-RC-02 `196079e`, version `1.1.0`
**Final status:** `R2-PRR-01 — CLOSED / ACCEPTED / RELEASE EVIDENCE CANONICALIZED / READY FOR PRODUCTION RELEASE DECISION`

Only documentation and one read-only consistency script were produced. No product source, package,
installer, generated legacy release evidence or frozen RC evidence was modified, and no Git tag was
created or moved. Existing `r2prerc01_payload_identity.ps1` and `ha02_docx_check.py` were used
where already available; only the pointer consistency script is new.

## 1. Canonical mapping used

```text
SPEC-INV-010   no Release Evidence -> the build must not be marked RC
SPEC-FUNC-021  Release Evidence (RELEASE_EVIDENCE.md + release_evidence.json)
```

`SPEC-INV-012` is the "report extra problems, do not modify" invariant. Earlier records (the
R2-RC-02 task documents and `R2_RC_02_MANIFEST.md` §12) used `SPEC-INV-012` as a label for the
release-evidence requirement; that label is treated as historical only and is noted as such inside
the pointer.

## 2. Historical evidence classification (baseline inspection)

| Evidence | Classification |
|---|---|
| `RC_EVIDENCE/RELEASE_EVIDENCE.md` + `RC_EVIDENCE/release_evidence.json` | `HISTORICAL / SUPERSEDED FOR CURRENT P12 RELEASE` — rule-generated pair for the earlier **1.0.0** candidate (`build_id 8dfe51eb8df2`, checked 2026-09-01) |
| `RC_EVIDENCE/P12_v1.1.0/RELEASE_CANDIDATE_EVIDENCE.md` | `HISTORICAL / SUPPLEMENTARY / PRE-HA02` — P12-era v1.1.0 candidate evidence, predating the R2 train and the HA-02 Mermaid remediation |
| `Doc/V2/Implementation/R2_RC/R2_RC_MANIFEST.md` | `SUPERSEDED / AUDIT-ONLY` — first R2 RC (closure `cd70d86`); artifacts preserved in `release/R2RC_pre_ha02_preserved/` |

Baseline assumptions confirmed: the root generated pair is not the current candidate; the P12
v1.1.0 evidence predates the accepted post-HA02 candidate; R2-RC-02 + targeted Human Re-Acceptance
identify the current accepted candidate; and no shipped-content change has occurred since Human
Acceptance (frozen hashes recomputed unchanged).

## 3. Current canonical release authority

```text
R2-RC-02 freeze commit               : ec06977debdbd2dd747e14ad2f27a9a4f9b74c3a
Targeted Human Re-Acceptance commit  : a8533a6e416c004b9a51a0a43d0ec50df3b77982
HA-02 closure commit                 : f851b64c3b65afe4c4d960346a9b19a9e2f3afd5
R2-PRE-RC-02 closure commit          : 196079ef2efa7ca5e86b5e8c2b744a710e4ae530
product version                      : 1.1.0
```

The pointer binds the full artifact identities from the frozen R2-RC-02 evidence:

| Artifact | Size | SHA-256 |
|---|---|---|
| Packaged EXE (`dist/MD_Converter_Lite/MD_Converter_Lite.exe`) | 7,671,725 B | `C368DFEBBC3660020CB20119E4952D83E2791B5D231D6BE62A6D0E552C871270` |
| Payload tree (`dist/MD_Converter_Lite`) | 461 files / 279,011,814 B | `92daa5ea8c7031e0046ccd2d875990cfebbca9ba8767f9d4c00e9d1a316cf370` (tree digest) |
| Installer (`dist_installer/MD_Converter_v1.1.0_Setup.exe`) | 77,296,967 B | `C54ADF6225689F06886B6C326E897BEB294EBA13EFD7897328DD738F6CF3CA42` |
| `THIRD_PARTY_NOTICES.txt` | 11,890 B | `E4B8D7223F085357DF923226FECD5AA189206B65448C26D1AD772C7116229696` |

## 4. Created pointer pair

| File | Size | SHA-256 |
|---|---|---|
| `RC_EVIDENCE/CURRENT_RELEASE_EVIDENCE_POINTER.md` | 5,154 B | `5BEF0E16D98EFF22D282C0C948BFF9D0371843F7E44E3159255AF18169E40202` |
| `RC_EVIDENCE/current_release_evidence_pointer.json` | 5,396 B | `A37072F5E7D860787974B685ADBE24746B3506E2754BCB337E67F241B6302F6E` |

Status recorded in both: `CURRENT_CANONICAL_RELEASE_EVIDENCE`, mapped to
`SPEC-INV-010 / SPEC-FUNC-021`. Both files state that no legacy generated evidence was rewritten,
that no frozen RC evidence was modified, and that the pointer does not synthesize a rule-generated
`RELEASE_ELIGIBLE` result or any test/QA/governance/regression/repair fields.

## 5. Consistency verification

Command: `.venv\Scripts\python.exe Doc\V2\Implementation\R2_PRR_01\Verification\r2prr01_pointer_consistency.py --json`

```text
fact_keys                                  : 26
pointer_md_json_mismatch                   : 0
missing_referenced_evidence                : 0
artifact_identity_mismatch                 : 0
frozen_manifest_mismatch                   : 0
legacy_generated_evidence_modifications    : 0
frozen_rc_modifications                    : 0
release_evidence_authority_ambiguity       : 0
result                                     : PASS
```

The check re-read the pointer pair, resolved every referenced current-authority evidence path,
recomputed the packaged EXE / installer / `THIRD_PARTY_NOTICES.txt` SHA-256 values, confirmed the
payload tree digest appears exactly in the frozen R2-RC-02 manifest, and compared the historical
generated evidence plus the frozen R2-RC-02 files against the pre-task byte baseline:

```text
RC_EVIDENCE/RELEASE_EVIDENCE.md                       6D0108A9…63DC1   unchanged
RC_EVIDENCE/release_evidence.json                     EB571654…82512   unchanged
RC_EVIDENCE/P12_v1.1.0/RELEASE_CANDIDATE_EVIDENCE.md  B9861045…17964F  unchanged
Doc/…/R2_RC_02/R2_RC_02_MANIFEST.md                   2C646B67…F0687   unchanged
Doc/…/R2_RC_02/R2_RC_02_CLOSURE_EVIDENCE.md           8C66BB2E…1F672   unchanged
Doc/…/R2_RC_02/Evidence/R2RC02-01_IDENTITY_RECHECK.json  C915EE7D…42704 unchanged
```

## 6. Counters

```text
artifact identity mismatch                    : 0
pointer MD/JSON mismatch                      : 0
missing referenced evidence                   : 0
legacy generated evidence modifications       : 0
frozen RC modifications                       : 0
release-evidence authority ambiguity          : 0
product / package / installer files staged    : 0
Git tags created / moved / reused             : 0
truthful commits                              : 1
```

Failure classification per the gate contract: `PASS`.

## 7. Production-release debt status

```text
SPEC-INV-010 / SPEC-FUNC-021 release-evidence authority
  -> RESOLVED by canonical supersession pointer (this WP)
  -> resolution method: explicit pointer + classification, NOT regeneration
  -> legacy generated evidence: preserved unchanged (no manual rewrite, no fabricated fields)
```

Remaining production blockers attributable to release-evidence canon: **none**. The next handoff
owns the final Human production authority, version/tag policy decision, and publication/archive
actions.

## 8. Next handoff

`Production Release Decision / Production Release` — not started by this gate.

`R2-PRR-01 — CLOSED / ACCEPTED / RELEASE EVIDENCE CANONICALIZED / READY FOR PRODUCTION RELEASE DECISION`
