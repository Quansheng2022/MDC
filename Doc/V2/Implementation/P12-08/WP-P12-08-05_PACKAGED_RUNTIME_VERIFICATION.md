# WP-P12-08-05 — Packaged Runtime Verification

**Product Baseline SHA:** `1b040c5d0d19f16be127cf3060fb573005a69c81`  
**Prerequisites:** WP-P12-08-02 through 04 CLOSED  
**Authority:** G1 verification; bounded packaging/runtime corrections allowed

## Objective

Verify the real packaged/installed application on Windows, especially behaviors that source-tree tests cannot prove.

## Required Runtime Matrix

### A. Startup / Shutdown

- launch installed app;
- main window usable;
- clean idle close;
- worker-active close protection still works.

### B. Conversion

- real Markdown input;
- real conversion through GUI;
- SUCCESS artifact on disk;
- warning/failure presentation remains correct where practical.

### C. Settings

- Settings save;
- close app;
- restart installed app;
- preferences restored;
- invalid/stale folder preference fails safely.

### D. Output Actions

- Open Document with persistent artifact;
- confirm Microsoft Word actually opens/reads it;
- Open Folder;
- missing artifact fails closed.

Do not use a temporary artifact that is deleted before Word consumes it.

### E. Paths

Verify:

- paths containing spaces;
- non-ASCII user/path names where practical;
- installed location independent from project source directory;
- output paths do not depend on current working directory unexpectedly.

### F. cp1252 / Console Encoding — REQUIRED

This WP owns decisive verification of the known console encoding risk.

Test the actual packaged GUI in a normal Windows environment without relying on the developer shell's `PYTHONIOENCODING=utf-8`.

Verify whether conversion reaches SUCCESS without `UnicodeEncodeError`.

Possible outcomes:

1. **PASS / non-reproducible in packaged GUI**  
   Record why the packaged process does not expose the problematic console path.

2. **FAIL / reproducible**  
   Apply one bounded packaging/runtime-safe correction if it does not alter conversion semantics.

3. **Requires Core semantic change**  
   STOP and escalate.

Do not hide the issue by merely setting a test-shell environment variable.

### G. High DPI

Quick smoke at representative Windows scaling remains usable.

## Evidence

Record exact installed executable path, installer version, test input/output path, Word actual-open confirmation, settings persistence, cp1252 result, and any bounded packaging correction.

## Stop Conditions

STOP on reproducible packaged conversion failure that cannot be fixed without semantic/Core changes.
