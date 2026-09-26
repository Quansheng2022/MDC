# WP-P12-06-05 — Open Document / Open Folder Actions

## Objective
Add safe post-conversion convenience actions using `ConversionResult.output_path` as the sole authority.

## Required
- Open Document.
- Open Folder.
- Enable for SUCCESS / SUCCESS_WITH_WARNING only when valid output exists.
- Disable for FAILED/JobFailure or missing artifact.
- Missing/deleted file fails safely.

## Platform
Use standard Qt/platform facilities; avoid unsafe shell command construction.

## Forbidden
No path recomputation, regeneration, retry, file-manager abstraction, recent-files history, or settings persistence.

## Tests
Eligibility, missing artifact, failure disabled, no path derivation, no conversion triggered.

## Stop
STOP if this requires output naming changes or unsafe shell invocation.
