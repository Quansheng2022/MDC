# R2 Targeted Human Re-Acceptance — Acceptance Record

**Record:** R2-HA-02 (targeted Human Re-Acceptance of the post-HA02 Release Candidate)
**Authority:** Human Authority Decision — verdict `ACCEPT`
**Recorded at:** 2026-10-01T16:14:34+08:00
**Change classification:** documentation only — the Human Acceptance evidence does not modify any
protected RC input

## 1. Accepted candidate

| Item | Value |
|---|---|
| R2-RC-02 freeze commit | `ec06977` (`R2RC02-01 freeze post-HA02 release candidate identity`) |
| RC manifest | `Doc/V2/Implementation/R2_RC_02/R2_RC_02_MANIFEST.md` |
| Packaged EXE | `C368DFEBBC3660020CB20119E4952D83E2791B5D231D6BE62A6D0E552C871270` |
| Payload tree digest | `92daa5ea8c7031e0046ccd2d875990cfebbca9ba8767f9d4c00e9d1a316cf370` |
| Installer | `C54ADF6225689F06886B6C326E897BEB294EBA13EFD7897328DD738F6CF3CA42` |
| Third-party notice | `E4B8D7223F085357DF923226FECD5AA189206B65448C26D1AD772C7116229696` (11,890 B) |
| Product version | `1.1.0` |

All three release-critical hashes and the tag inventory were re-confirmed unchanged at record time
(HEAD `ec06977`; tags `v1.0.0` / `v1.0.1` / `v1.1.0` untouched). This record is anchored on the
R2-RC-02 freeze commit, the manifest and those artifact hashes; no Git release tag was created.

## 2. Human verification performed

1. Installed application launches normally.
2. `test_mermaid_triangle_v2.md` converts successfully.
3. Mermaid Case A / B / C render correctly in the generated Word document.
4. No raw Mermaid fallback was observed.
5. The Mermaid visual output is acceptable for release.
6. A normal non-Mermaid Markdown conversion succeeds.
7. No new release-blocking usability issue was observed.

## 3. Verdict and status

```text
Human verdict : ACCEPT
Final status  : TARGETED HUMAN RE-ACCEPTANCE — ACCEPTED / READY FOR PRODUCTION RELEASE READINESS
```

The R2-RC-02 candidate is accepted for production-release readiness.

## 4. Constraints honoured

```text
product code / package / installer / RC identity modified : NO
automated gates re-run                                    : NO
Git release tag created or moved                          : NO
R2-RC-02 frozen identity preserved                        : YES (hashes unchanged)
```

This record adds documentation only. Per the R2-RC-02 invalidation rules, Human Acceptance evidence
does not invalidate the frozen RC while the protected inputs (product source, EXE bytes, payload
tree, installer bytes, notice bytes, version identity) remain unchanged — which they do.

## 5. Outstanding pre-production release debt

```text
SPEC-INV-010 / SPEC-FUNC-021 — PRE-PRODUCTION RELEASE DEBT (OPEN)
```

Recorded under the Canonical mapping (`CANONICAL_SPEC.md`: `SPEC-INV-010` "no Release Evidence →
no RC marking", `SPEC-FUNC-021` "Release Evidence (`RELEASE_EVIDENCE.md` + `release_evidence.json`)");
the R2-RC-02 task documents referred to the same item as `SPEC-INV-012`.

- The tracked release evidence has not been regenerated for the R2 candidate: root
  `RC_EVIDENCE/RELEASE_EVIDENCE.md` / `release_evidence.json` still describe software version
  `1.0.0`, and `RC_EVIDENCE/P12_v1.1.0/RELEASE_CANDIDATE_EVIDENCE.md` covers the pre-R2 v1.1.0 work.
- It **must be resolved before Production Release**, by authoritative regeneration/sync of the
  release evidence or by an explicit canonical supersession/pointer decision. Generated release
  evidence must not be fabricated or hand-rewritten.
- It is not resolved by this record and does not affect the accepted RC identity.

## 6. Next step

Production Release readiness — not started by this record.

`TARGETED HUMAN RE-ACCEPTANCE — ACCEPTED / READY FOR PRODUCTION RELEASE READINESS`
