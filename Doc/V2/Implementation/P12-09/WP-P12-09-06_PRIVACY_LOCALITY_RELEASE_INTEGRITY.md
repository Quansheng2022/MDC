# WP-P12-09-06 — Privacy / Locality / Release Integrity

**Product Baseline:** `38614c7`

## Objective

Verify the release candidate remains consistent with the frozen local/private positioning and artifact integrity.

## Product Positioning

Frozen statement:

> **Turn Markdown into polished Word documents — locally, privately, and without a subscription.**

Verify installed behavior is consistent with:

- local conversion processing;
- no account required;
- no document upload required by the normal conversion workflow.

Do not infer broader claims such as guaranteed zero network access under all circumstances.

## Required Network Dependency

During normal launch and representative conversion, verify there is no required network dependency for the core workflow.

This is not a penetration test.

## Artifact Integrity

Verify:

- installer filename;
- version;
- size;
- SHA-256;
- executable/package identity;
- version consistency;
- EULA/notices inclusion;
- no obvious `.git`, `.venv`, tests, caches, review packages, credentials, or developer-only absolute-path configuration in release payload.

## Rebuild Traceability

Confirm P12-08 clean-build evidence still corresponds to the candidate.
Do not rebuild unless candidate identity is uncertain.

## Acceptance

Locality claims remain accurate, no required network dependency appears in normal workflow, and artifact identity/integrity is consistent.
