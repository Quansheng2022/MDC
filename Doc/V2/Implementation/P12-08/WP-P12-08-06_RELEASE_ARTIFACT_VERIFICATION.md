# WP-P12-08-06 — Release Artifact Verification

**Product Baseline SHA:** `1b040c5d0d19f16be127cf3060fb573005a69c81`  
**Prerequisite:** WP-P12-08-05 CLOSED  
**Authority:** G1 bounded

## Objective

Prove that release artifacts can be produced from a controlled build process and that the resulting payload is complete and reviewable.

## Clean Build

Use a documented build sequence starting from source and packaging configuration, not from manually patched `dist/` contents.

Generated output directories may be removed/recreated if they are dedicated packaging outputs and not authoritative source.

Do not clean unrelated repository files.

## Required Artifact Inventory

Record at minimum:

- packaged executable/application directory or bundle;
- installer file;
- version;
- file size;
- SHA-256 hash for final distributable installer and, where useful, packaged executable;
- build timestamp;
- build command/script;
- source/packaging baseline SHA.

## Rebuild Check

Perform at least one clean rebuild or equivalent reproducibility check sufficient to prove that no manual post-build editing is required.

Byte-for-byte equality is not required unless the existing toolchain is deterministic; explain nondeterminism if hashes differ across builds.

## Install / Uninstall Recheck

Using the candidate artifact:

- install;
- launch;
- minimal conversion smoke;
- uninstall;
- verify no release-blocking residue or broken uninstall registration.

## Artifact Hygiene

Final release package must not accidentally contain obvious development-only material such as:

- tests;
- `.git`;
- `.venv`;
- caches;
- review packages;
- unrelated historical release payloads;
- secrets/credentials;
- local absolute-path configuration.

## Stop Conditions

STOP if the release artifact depends on manual edits, developer-only files, or cannot be rebuilt from documented source/configuration.
