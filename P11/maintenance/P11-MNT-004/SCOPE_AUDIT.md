# P11-MNT-004 — Scope Audit

## Authorized Product Files

```text
md_converter/pipeline/pipeline.py
md_converter/pipeline/pass_registry.py
```

## Authorized Test File

```text
md_converter/tests/test_pipeline_fail_closed.py
```

## Authorized Governance Files

```text
P11/P11_MAINTENANCE_REGISTRY.md
P11/maintenance/P11-MNT-004/**
```

## Forbidden Scope Audit

```text
md_converter/compiler.py:             no changes
Parser / AST:                        no changes
Renderer / Writer:                   no changes
QA / FinalArtifactQA:                no changes
Diagnostic framework:                no changes
new exception hierarchy:             not introduced
retry / fallback framework:          not introduced
optional-pass framework:             not introduced
logging / print cleanup:             not performed
general refactor:                    not performed
CANONICAL_SPEC.md:                   no changes
Architecture / ADR:                  no changes
Acceptance / Golden:                 no changes
dependencies:                        no changes
tools/review:                        no changes
P11-MNT-005:                         not started
PLAN_C:                              not started
version / tag / release:             not performed
```

## Registry Consistency Correction

During P11-MNT-004 intake, the Registry's compact issue block was aligned for
already-closed P11-MNT-002 and P11-MNT-003 entries so it matches their existing
CLOSED table rows and recorded closure SHAs. No status was advanced beyond
facts already committed in prior packages.

## Unauthorized Changes

```text
0
```

## Generated Outputs

All strict-merger and collector outputs are written outside `PROJECT_ROOT` and
are not part of the implementation commit.
