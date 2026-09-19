# P11-MNT-004 — Root Cause Analysis

## Verified Root Cause

Required pass failures are incorrectly classified as recoverable at two
pipeline orchestration layers:

```text
Pipeline.run
    catches Exception
    emits PIPE001
    continues to subsequent passes

PassRegistry.get_passes
    catches enabled-pass construction Exception
    omits the failed pass
    returns a partial pass list
```

The compiler already has a propagation boundary around both operations:

```text
try:
    passes = self.pass_registry.get_passes()
    pipeline = Pipeline(passes=passes)
    ast = pipeline.run(ast, self.diag)
except Exception as e:
    self.diag.error(f"Pipeline error: {e}", code="PIPE001")
    raise
```

Therefore no new exception hierarchy or compiler redesign is required. The
minimal fix is to restore propagation at the two swallow sites.

## Failure Boundary

```text
enabled constructor failure
    -> PassRegistry.get_passes currently swallows
    -> partial pass list

enabled run failure
    -> Pipeline.run currently swallows
    -> later passes execute
    -> compilation may produce DOCX
```

## Required Behavior

```text
disabled pass
    -> skipped by registry, unchanged

successful enabled pass
    -> executes normally, unchanged

enabled constructor failure
    -> raises, no partial list

enabled run failure
    -> raises, later passes do not execute

compiler required-pass failure
    -> raises; no final DOCX
```

## Non-Root Causes Ruled Out

- Parser / AST behavior is not involved.
- Renderer / Writer behavior is not involved.
- QA / FinalArtifactQA behavior is not involved.
- No dependency, Canonical, Architecture, Acceptance, or Golden change is
  required.
