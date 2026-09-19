# P11-MNT-002 — Reproduction

## Baseline

```text
HEAD: 6db3d39f10e7ac0e05660be0e8c02ba9ee7c30cc3
Command: .\.venv\Scripts\python.exe
         .\tools\review\merge_project_for_phase11_review.py
         --mode maintenance --list-only
```

Before the fix, the default maintenance listing selected 170 files and included
all of the following generated artifacts:

```text
Merged_Code/merged_MDC_phase11_foundation_review.txt
Review_Bundle/MDC_maintenance_review_20260919_155555.manifest.json
Review_Bundle/MDC_maintenance_review_20260919_155555.txt
```

Running the same list-only command with a different output name increased the
selection to 171 files:

```text
Command: --output Merged_Code\batchA_nesting_probe_B.txt

Added generated artifact:
Merged_Code/merged_MDC_phase11_maintenance_review.txt
```

This is the nesting condition: each distinct snapshot name lets the merger
discover and embed the previous snapshot generated under another name.

## Root Trigger

The maintenance inclusion policy treats any path containing `maintenance` or
`review` as governance-relevant. The generated snapshot folders
`Merged_Code/` and `Review_Bundle/` were not in the merger's exclusion sets.

## Collector Companion Observation

Baseline maintenance collector listing:

```text
Profile: maintenance
Tests: True
Candidates: 159
md_converter/py.typed candidates: 0
md_converter/tests/test_*.py candidates: 19
tools/review candidates: 1
```

`md_converter/py.typed` has suffix `.typed`; the maintenance profile traversed
`md_converter` without `allow_all_docs`, so the file was silently omitted.
