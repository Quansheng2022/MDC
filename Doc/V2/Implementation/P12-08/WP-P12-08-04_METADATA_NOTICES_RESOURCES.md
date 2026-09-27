# WP-P12-08-04 — Product Metadata / Notices / Resources

**Product Baseline SHA:** `1b040c5d0d19f16be127cf3060fb573005a69c81`  
**Authority:** G1 bounded

## Objective

Ensure the packaged application and installer carry the correct product identity and required bundled resources without creating duplicate authorities.

## Required Checks

Verify and, where required, package:

- application name;
- version;
- executable/installer icon;
- publisher/company text if authoritative;
- copyright text;
- EULA;
- third-party notices;
- any runtime assets required by GUI or conversion;
- Qt plugins/resources actually required by the packaged app.

## Version Rule

The installed/package version must match the project's authoritative version source.

Do not manually invent a second version number for the installer.

## Resource Rule

Include only resources required for runtime or release compliance.

Do not indiscriminately bundle:

- tests;
- source history;
- review packages;
- developer documentation;
- build caches;
- old release payloads;
- `.venv`;
- unrelated sample files.

## Verification

- compare package/installer displayed version with authoritative source;
- verify icons load;
- verify notices/EULA included where specified;
- verify required runtime resources exist after installation;
- verify no obvious developer-path dependency.

## Stop Conditions

STOP if legal/licensing content is missing or contradictory and cannot be resolved from authoritative repository material.
