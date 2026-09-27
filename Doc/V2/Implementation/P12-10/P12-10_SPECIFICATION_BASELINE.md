# P12-10 — Release Candidate
## Specification Baseline

**Project:** MD_Converter v2.0  
**Phase:** P12-10 — Release Candidate  
**Product Baseline:** `4c02734` (P12-09 Closure)  
**Character:** RC freeze / release-readiness packaging  
**Governance:** freeze-first; no feature expansion

## Objective
Turn the P12-09 verified product into one exact Release Candidate (RC) with frozen source/artifact identity, release documentation, integrity evidence, and an explicit acceptance gate.

## Frozen Boundary
Runtime architecture remains:
```text
GUI → GuiWorker → ConversionService → Canonical Core
```
P12-10 must not add product features, Settings, conversion/output/diagnostics semantics, installer behavior, updater, telemetry, cloud/account capability, or architecture.

## Work Packages
1. WP-P12-10-01 — RC Baseline & Identity
2. WP-P12-10-02 — Release Documentation
3. WP-P12-10-03 — RC Artifact Assembly
4. WP-P12-10-04 — Signing / Distribution Readiness
5. WP-P12-10-05 — RC Smoke & Integrity
6. WP-P12-10-06 — RC Acceptance Gate
7. WP-P12-10-07 — RC Closure

## RC Principles
- Freeze one exact source/artifact identity.
- Any release-affecting post-freeze change invalidates the RC identity.
- Do not repeat P12-09 full verification; perform only minimal RC integrity/smoke checks.
- Release documentation describes accepted behavior; it does not create new requirements.

## Version Policy
Do not automatically increment version. Existing authoritative version remains in force unless Human authority explicitly approves a change such as an RC suffix.

## Filename Policy
Windows release filenames must not contain:
```text
\ / : * ? " < > |
```

## Signing Boundary
Record whether installer/executable are signed, signer identity if present, and expected trust behavior if unsigned. Do not procure certificates or build signing infrastructure in this phase.

## Distribution Boundary
P12-10 may assemble a local/final release payload. Do not add Store publishing, CDN, updater, CI/CD release automation, or artifact registry.

## Change Classification
- R0: documentation/evidence only — allowed.
- R1: release metadata only — allowed if semantics unchanged.
- R2: release-affecting artifact change — STOP; new RC identity required.
- R3: product semantic change — STOP immediately.

## Exit Criteria
```text
RC source identity frozen
RC installer identity frozen
RC executable identity frozen where applicable
version consistency PASS
release notes PASS
known issues PASS
artifact manifest/checksums PASS
signing/trust status explicit
distribution payload PASS
minimal RC smoke PASS
post-freeze drift = 0
open RC blockers = 0
```

Next: **P12-11 — Human Acceptance**
