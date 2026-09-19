# P11-MNT-005 — Root Cause Analysis

## Verified Root Cause

`md_converter.convert()` duplicates compiler construction manually rather than
delegating to the existing canonical helper:

```text
convert()
    creates DiagnosticCollector / ParserContext / RenderContext
    creates PassRegistry
    registers built-in passes by hand
    calls discover_passes()
    appends to pass_registry._pass_classes   <-- nonexistent attribute
    creates CompilerContext directly
    calls ctx.compile(...)
```

`PassRegistry` exposes `_entries`, `_instances`, `_metadata`,
`_sorted_cache`, and `_cache_dirty`; it has no `_pass_classes` attribute.
When installed entry points are discovered, this path raises
`AttributeError`.

The same stale path also bypasses `resolve_config()` and the canonical theme
construction. After bypassing plugin discovery, the unresolved config reaches
`CompilerContext.compile()` and raises `KeyError: 'enable_cover'`.

## One Issue, Not Multiple

The `_pass_classes` failure and the unresolved-config failure share one root
cause: `convert()` owns a stale parallel compiler-construction path. The fix
must remove that ownership instead of patching individual attributes or
config keys.

## Canonical Fix Strategy

```text
convert(markdown_text, config=None, theme=None)
    ↓
delegate to compile_markdown(markdown_text, config=config, theme=theme)
    ↓
CompilerContext.create(config)
    ↓
resolve_config() + canonical theme/pass construction
```

The existing public signature is preserved. No new API parameters and no new
output/save semantics are introduced.

## Non-Root Causes Ruled Out

- `compiler.py` does not need modification.
- `config.py` does not need modification.
- `PassRegistry` implementation does not need modification.
- Plugin discovery does not need modification.
- Theme implementation does not need modification.
- No Canonical / Architecture / Acceptance / Golden change is required.
