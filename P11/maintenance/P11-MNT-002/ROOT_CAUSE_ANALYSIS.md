# P11-MNT-002 — Root Cause Analysis

## Verified Root Cause

`enumerate_files()` pruned only the merger's existing excluded directory/path
sets. Those sets did not contain `Merged_Code/` or `Review_Bundle/`.

When the merger walked a previous snapshot, `include_for_mode()` evaluated the
generated path as maintenance/release content because the path or filename
contains governance keywords such as `maintenance` and `review`. The exact
current output path was filtered after enumeration, but any prior snapshot with
a different output name remained eligible.

## Failure Chain

```text
prior snapshot generated
    ↓
next merger run scans project tree
    ↓
generated folder not excluded
    ↓
generated filename contains "maintenance" / "review"
    ↓
include_for_mode(mode=maintenance|release) returns True
    ↓
prior snapshot embedded into new snapshot
```

## Collector Companion Root Cause

The collector's `is_supported_text_file()` accepts known text extensions or
extensionless files. `md_converter/py.typed` has the suffix `.typed`, which was
not in `TEXT_EXTENSIONS`. The maintenance profile therefore omitted it even
though it is part of the approved package-data contract.

## Fix Strategy

- Exclude the conventional generated review directories from merger traversal.
- Exclude generated review artifact names even if produced outside those
  conventional directories.
- Treat `.typed` as a supported review text extension.
- Preserve all approved profile defaults and test-inclusion behavior.

## Non-Root Causes Ruled Out

- No product parser / AST / pipeline / renderer / post-processor involvement.
- No Canonical, Architecture, Acceptance, or Golden semantic change.
- No dependency or packaging change.
