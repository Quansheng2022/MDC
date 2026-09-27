# WP-P12-10-03 — RC Artifact Assembly

**Product Baseline:** `4c02734`

## Objective
Assemble the exact RC payload without rebuilding or modifying accepted binaries.

## Suggested Payload
```text
MD_Converter_v<version>_Setup.exe
SHA256SUMS.txt
RELEASE_NOTES.md
KNOWN_ISSUES.md
EULA.txt
THIRD_PARTY_NOTICES.txt
RC_MANIFEST.md
```

## Rules
- Copy accepted artifacts; do not patch binaries.
- Preserve binary hashes.
- Exclude `.git`, `.venv`, tests, caches, review packages, old releases, credentials, and local-only paths.

## RC Manifest
Record RC identifier, version, source SHA, P12-09 closure SHA, installer identity, executable identity where useful, documentation inventory, build provenance, and creation timestamp.

## Acceptance
RC folder contains only intended payload and all hashes match WP-01.
