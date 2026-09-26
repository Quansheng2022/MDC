# WP-P12-06-06 — Diagnostics UX Verification and Closure

## Objective
Verify and formally close P12-06. No new feature in this WP.

## Verify
### V1 Presentation Model
SUCCESS / SUCCESS_WITH_WARNING / FAILED / JobFailure represented without semantic change.

### V2 Failure UX
Failure clear; infrastructure failure distinct; no false output action; details accessible.

### V3 Warning UX
Warning is still success-with-warning; evidence visible; valid output accessible.

### V4 Diagnostics Report
On-demand, read-only, retained evidence shown without mutation/recomputation.

### V5 Output Actions
Open Document/Folder use `ConversionResult.output_path`; missing artifact safe; no conversion triggered.

### V6 Architecture
GUI direct Core calls = 0; application Qt imports = 0; result/QA semantics changed = 0; second diagnostics pipeline = 0.

### V7 Regression
Run full GUI/P12-06, application, relevant CLI/public/config/QA, full regression, Golden/Acceptance, and real Windows smoke. Existing approved baseline failures may remain pre-existing. Required: P12-06 introduced failures = 0.

### V8 Closure Evidence
Create `Doc/V2/Implementation/P12-06/P12-06_CLOSURE_EVIDENCE.md` with baseline, WP closure SHAs, test results, Windows smoke, evidence preservation, drift, known failures, blockers, decision.

## Exit Criteria
Failure UX PASS; warning UX PASS; report PASS; output actions PASS; evidence preserved; JobFailure distinct; Core/Golden/CLI semantic changes = 0; introduced failures = 0; blockers = 0.

Then P12-06 = CLOSED / ACCEPTED and P12-07 = AUTHORIZED / NEXT.

## Stop
Do not close if result/Core/QA semantics changed, direct GUI→Core exists, required regression remains, Golden changed without authority, or CLI/public regression introduced.
