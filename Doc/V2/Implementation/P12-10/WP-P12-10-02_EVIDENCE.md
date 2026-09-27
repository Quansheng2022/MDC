# WP-P12-10-02 — Release Documentation — Evidence

**Product Baseline:** `4c02734` (P12-09 Closure)
**Input HEAD:** `49161d129a306ad3e97ecfe094f84ac482fac7ff` (WP-P12-10-01)
**Status:** PASS

## 1. Required minimum vs. delivered

| Required item | Delivered as | Action |
|---|---|---|
| Release Notes | `RELEASE_NOTES_v1.1.0.md` | updated (RC1 section added) |
| Known Issues / Accepted Limitations | `KNOWN_ISSUES_v1.1.0.md` | created |
| Installation Notes | `INSTALLATION_GUIDE_v1.1.0.md` | created (installer scope) |
| Uninstall Notes | `INSTALLATION_GUIDE_v1.1.0.md` §6 | created |
| Privacy / Local Processing statement | `PRIVACY_LOCAL_PROCESSING_v1.1.0.md` | created |
| RC acceptance checklist | `Doc/V2/Implementation/P12-10/RC_ACCEPTANCE_CHECKLIST.md` | created |
| checksum / artifact manifest | `RC_MANIFEST.md` + `SHA256SUMS.txt` | assembled in WP-P12-10-03 |

Existing authoritative documents were reused rather than duplicated:

```text
RELEASE_NOTES_v1.1.0.md      updated in place (only an RC1 pointer section added)
KNOWN_LIMITATIONS_v1.0.0.md  still authoritative for the v1.0.0 base limitations;
                             KNOWN_ISSUES_v1.1.0.md consolidates the v1.1.0
                             accepted limitations and refers to it instead of copying it
INSTALLATION_GUIDE_v1.0.0.md still authoritative for the wheel/sdist install path;
                             INSTALLATION_GUIDE_v1.1.0.md covers the Windows installer
RELEASE_MANIFEST_v1.1.0.json not modified (its content is asserted by
                             md_converter/tests/test_packaging_metadata.py)
```

## 2. Accuracy constraints applied

* Release notes state the product version (`1.1.0`), Windows target, Markdown →
  polished Word conversion, desktop GUI, local processing, no account, no
  subscription, installer availability and the user-visible v1.1.0
  capabilities. `RC1` is declared as an evidence-only label; no version
  metadata was changed for it.
* Known issues contain only user-relevant accepted limitations (conservative
  simple-table recognition, Word-owned pagination, figure minimum-width policy,
  optional Mermaid/CDN dependency, Word COM scope, unsigned installer, default
  icon, declared non-goals, CLI cp1252 redirection). Engineering debt and test
  counts are kept out of the public notes and live in closure evidence.
* No new product requirement was created; every statement describes the frozen
  P12-09-accepted artifact and cites the evidence that supports it.
* Every documented fact is traceable: installer identity from WP-P12-10-01;
  install/uninstall/persistence/privacy behaviour from P12-08 (`WP-P12-08-03`,
  `WP-P12-08-06`) and P12-09 (`WP-P12-09-04`, `WP-P12-09-06`) evidence.

## 3. Files added / modified

```text
modified  RELEASE_NOTES_v1.1.0.md
added     KNOWN_ISSUES_v1.1.0.md
added     INSTALLATION_GUIDE_v1.1.0.md
added     PRIVACY_LOCAL_PROCESSING_v1.1.0.md
added     Doc/V2/Implementation/P12-10/RC_ACCEPTANCE_CHECKLIST.md
added     Doc/V2/Implementation/P12-10/WP-P12-10-02_EVIDENCE.md
```

No file under `md_converter/`, `pyproject.toml`, `*.spec`, `*.iss` or
`packaging/` was touched.

## 4. Checks

| Check | Result |
|---|---|
| All required documentation items delivered | PASS |
| Release notes describe the frozen RC only | PASS |
| Known issues limited to user-relevant accepted limitations | PASS |
| Install and uninstall notes present for the installer | PASS |
| Privacy / local-processing statement present | PASS |
| RC acceptance checklist present with evidence sources | PASS |
| Existing authoritative documents reused, no duplicate created | PASS |
| No new product requirement introduced | PASS |
| R2/R3 action required | NONE |

## 5. Acceptance

Documentation accurately describes the frozen RC and creates no new product
requirements. **WP-P12-10-02 = PASS.**
