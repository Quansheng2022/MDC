# WP-P12-08-07 — Verification & Closure

**Product Baseline SHA:** `1b040c5d0d19f16be127cf3060fb573005a69c81`  
**Authority:** phase closure only; no new feature work

## Objective

Perform the final consolidated verification for P12-08 and create one closure evidence document.

## Preconditions

WP-P12-08-01 through WP-P12-08-06 CLOSED.

## V1 — Packaging

Confirm:

- accepted GUI entry point;
- standalone Windows build succeeds;
- required resources bundled;
- no developer environment required.

## V2 — Installer

Confirm:

- installer runs;
- install completes;
- Start Menu launch works;
- installed app launches;
- uninstall works;
- user-generated documents are preserved.

## V3 — Runtime

Confirm:

- real conversion succeeds;
- Settings persist after restart;
- About/version correct;
- report/diagnostics usable;
- Open Document actual Word open confirmed;
- Open Folder works;
- missing artifact fails closed;
- High-DPI smoke passes.

## V4 — cp1252

Record decisive packaged-environment result.

Closure is blocked if a normal installed Windows run reproduces the known encoding failure and no bounded non-semantic fix exists.

## V5 — Artifact Integrity

Confirm:

- final installer filename/version;
- final size;
- SHA-256;
- packaged executable/app artifact inventory;
- clean build/rebuild evidence;
- no obvious development-only payload.

## V6 — Source Regression

Run once after packaging implementation is frozen:

- relevant packaging tests;
- GUI/application smoke or focused regression as needed;
- full source regression once;
- Golden/Acceptance once if packaging changes touched executable runtime integration.

Existing approved failures may remain only if unchanged and explicitly classified.

## V7 — Drift

Confirm:

```text
Direct GUI → Core calls = 0
Application-layer Qt dependency = 0
Conversion semantics changed = 0
Diagnostics semantics changed = 0
Output semantics changed = 0
Core changes = 0
Canonical semantic changes = 0
QA semantic changes = 0
Golden changes = 0
CLI/public API breaking changes = 0
Network/telemetry/update services introduced = 0
```

## Closure Document

Create exactly:

`Doc/V2/Implementation/P12-08/P12-08_CLOSURE_EVIDENCE.md`

Include:

- Product Baseline SHA
- P12-08 Specification Baseline SHA
- WP closure SHAs
- packaging stack
- executable artifact
- installer artifact
- versions/sizes/hashes
- packaged runtime smoke
- cp1252 result
- install/uninstall evidence
- clean-build evidence
- regressions
- drift
- known deferred issues
- blockers
- closure recommendation

## Exit Criteria

```text
Windows executable build PASS
installed launch PASS
real conversion PASS
installer PASS
uninstall PASS
settings persistence PASS
Open Document actual-open PASS
Open Folder PASS
cp1252 packaged-runtime verification PASS
metadata/resources/notices PASS
clean build/rebuild PASS
artifact inventory PASS
introduced regression failures = 0
open release blockers = 0
```

Then recommend:

```text
P12-08 Packaging / Installer = CLOSED / ACCEPTED
P12-09 Verification          = AUTHORIZED / NEXT
```
