# P11-MNT-004 — Reproduction

## Activation Conditions

```text
P11-MNT-003: CLOSED / ACCEPTED
HEAD: a5efdfcced0221edaaa34adf5f164464be7d9b2d
Working tree: CLEAN
P11-MNT-004 ID: not previously occupied
```

## Reproduction A — Pipeline.run Swallows Pass Execution Failure

Minimal `BoomPass` raises during `run`; a later `SentinelPass` records execution.

Observed before fix:

```text
sentinel_executed=True
diagnostic_codes=['PIPE001']
```

The failure is swallowed and the later pass executes.

## Reproduction B — PassRegistry.get_passes Swallows Construction Failure

An enabled `BrokenInitPass` raises in its constructor; a later `SentinelPass`
is registered after it.

Observed before fix:

```text
returned_passes=['SentinelPass']
partial_list=True
```

The enabled pass is silently omitted and a partial list is returned.

## Reproduction C — Compiler Integration Observation

A `BoomIntegrationPass` was registered into `CompilerContext.pass_registry`
and compilation was attempted.

Observed before fix:

```text
compile_raised=False
error=None
docx_exists=True
diagnostic_codes=['PIPE001']
```

The compiler continued after the required pass failure and produced a DOCX.

## Expected After Fix

```text
Pipeline.run:
  pass execution failure -> diagnostic PIPE001 + re-raise

PassRegistry.get_passes:
  enabled construction failure -> re-raise

CompilerContext.compile:
  required pass failure -> raise
  no final DOCX

Disabled pass:
  skip behavior unchanged

Successful enabled pass:
  continue behavior unchanged
```
