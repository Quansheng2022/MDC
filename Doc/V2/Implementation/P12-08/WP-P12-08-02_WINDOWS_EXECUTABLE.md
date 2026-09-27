# WP-P12-08-02 — Windows Executable Packaging

**Product Baseline SHA:** `1b040c5d0d19f16be127cf3060fb573005a69c81`  
**Prerequisite:** WP-P12-08-01 CLOSED  
**Authority:** G1 bounded

## Objective

Build a standalone Windows GUI application from the accepted source baseline.

## Required Behavior

The packaged executable must:

- start without requiring a developer Python environment;
- enter the accepted GUI application;
- preserve P12-07 Settings/About/diagnostics/output behavior;
- locate all required runtime resources;
- perform a real Markdown → DOCX conversion;
- exit cleanly.

## Packaging Rules

Prefer the repository's accepted bundler configuration.

Allowed changes:

- `.spec` file;
- runtime hooks;
- hidden-import/resource declarations;
- icon/version resource wiring;
- packaging helper script;
- packaging-only environment setup.

Forbidden:

- source semantic workarounds;
- direct-Core GUI path;
- rewriting conversion defaults;
- bundling test/source-development directories unnecessarily.

## Required Focused Verification

From a newly built package:

1. executable exists;
2. executable launches;
3. main window appears;
4. About/version opens;
5. Settings opens;
6. real small conversion succeeds;
7. output DOCX exists;
8. Details/report works where applicable;
9. process closes cleanly.

Capture package size and main artifact path.

## Console/Encoding Observation

Record whether the packaged GUI has a console and what stdout/stderr behavior exists.

Do not declare the cp1252 issue solved here; WP-05 owns decisive verification.

## Stop Conditions

STOP if packaging requires Core/Application semantic changes or if the packaged executable cannot complete a minimal real conversion after one bounded packaging correction cycle.
