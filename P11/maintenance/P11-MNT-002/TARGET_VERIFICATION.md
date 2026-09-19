# P11-MNT-002 — Target Verification

## Syntax

```text
.\.venv\Scripts\python.exe -m py_compile
    tools/review/merge_project_for_phase11_review.py
    tools/review/collect_project_for_review.py
    md_converter/tests/test_review_tooling.py

Result: PASS
```

## Focused Regression Tests

```text
.\.venv\Scripts\python.exe -m pytest
    md_converter/tests/test_review_tooling.py -q -ra

Result: 4 passed
```

The focused tests cover:

1. Generated snapshot directories are excluded by the merger.
2. Generated snapshot names are excluded outside conventional directories.
3. The maintenance collector includes `md_converter/py.typed` and package
   tests.
4. `--exclude-tests` behavior remains intact while `py.typed` remains included.

## Merger No-Nesting Evidence

Post-fix list-only runs immediately after the tooling change:

```text
Default output:           169 selected files
Alternate output name:    169 selected files
Generated path entries:   0
```

Two full merger generations were then written outside the project tree against
the final Batch A file set:

```text
Run 1: Merged files: 177; generated-path FILE lines: 0; RESULT: PASS
Run 2: Merged files: 177; generated-path FILE lines: 0; RESULT: PASS
File-list delta: 0
Output sizes: both 1,754,060 bytes
SHA256 run 1: 3BBE9BCA91D4C6257705D56B94F71DF44C0EF829978A7DCF530EE3606ECED9CA
SHA256 run 2: C4A3E4FD6EB600C7290B9CB72DF13A9EBD6CFB14F3124C1891A21290C8547D6F
```

The SHA values differ only because the snapshot header contains a generation
timestamp; the selected file sets and sizes are identical.

## Collector Profile Evidence

After the `.typed` fix:

```text
Profile: maintenance
Tests: True
Candidates: 162
md_converter/py.typed candidates: 1
md_converter/tests/test_*.py candidates: 20
tools/review candidates: 2
```

Baseline-to-after delta:

```text
159 baseline
 +1 md_converter/py.typed
 +1 tools/review/collect_project_for_review.py
 +1 md_converter/tests/test_review_tooling.py
= 162 candidates
```

Test collection behavior is preserved: `Tests` remains `True` for the
maintenance profile, and the increase from 19 to 20 package test files is only
the new focused regression test.
