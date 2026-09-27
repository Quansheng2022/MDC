# P12-10 — Release Candidate — Closure Evidence

**Product Baseline SHA:** `4c027344fbd9ca7d05190fe7f689c4edad11dd8d` (P12-09 Closure)
**P12-10 Specification Baseline SHA:** `3a0dfdceae70b709c674d43656cbffed7cd969e8`
**Closure SHA:** recorded by the committing run (`P12-10-07 close release candidate phase`)
**Status:** PASS

## 1. Phase answer

```text
Can one exact P12-09 verified artifact be frozen as a Release Candidate and
handed to P12-11 Human Acceptance without any further product change?

YES.
```

No rebuild, no patch, no product-source change, no packaging change and no
version-metadata change were required or performed. The accepted binaries were
frozen, packaged with release documentation, verified and gated.

## 2. WP commit chain

| WP | Title | Commit | Status |
|---|---|---|---|
| — | P12-10 release candidate specifications | `3a0dfdc` | specification baseline |
| WP-P12-10-01 | RC Baseline & Identity | `49161d1` | PASS |
| WP-P12-10-02 | Release Documentation | `c0d94d8` | PASS |
| WP-P12-10-03 | RC Artifact Assembly | `e954a68` | PASS |
| WP-P12-10-04 | Signing / Distribution Readiness | `eb5b6da` | PASS |
| WP-P12-10-05 | RC Smoke & Integrity | `0894442` | PASS |
| WP-P12-10-06 | RC Acceptance Gate | `7c4dd60` | PASS |
| WP-P12-10-07 | RC Closure | this commit | PASS |

Full SHAs:

```text
specification baseline  3a0dfdceae70b709c674d43656cbffed7cd969e8
WP-P12-10-01            49161d129a306ad3e97ecfe094f84ac482fac7ff
WP-P12-10-02            c0d94d899d24cd26dd1da0f0458e6fafb99e1afe
WP-P12-10-03            e954a680cf29f050278661cd78c9ac1d04cbf446
WP-P12-10-04            eb5b6dad3108c8549c46c29637cd6f9701b91882
WP-P12-10-05            0894442fa18f7061028157bdc247752bd89b4c46
WP-P12-10-06            7c4dd6055e00d5a8dadcadaae7e2ef3fc59f0696
```

## 3. Frozen RC identity

| Item | Value |
|---|---|
| RC identifier | **MD Converter v1.1.0 RC1** (evidence-only label) |
| Product version | `1.1.0` |
| Source SHA (frozen) | `4c027344fbd9ca7d05190fe7f689c4edad11dd8d` |
| P12-09 Closure SHA | `4c027344fbd9ca7d05190fe7f689c4edad11dd8d` |
| P12-10 Specification Baseline SHA | `3a0dfdceae70b709c674d43656cbffed7cd969e8` |
| Installer | `MD_Converter_v1.1.0_Setup.exe` |
| Installer size | 51,109,717 bytes |
| Installer SHA-256 | `EFEC378F11B00A53791158199B4DC98AA09F44F5B1F013363FF744A92B91B9BF` |
| Executable | `dist\MD_Converter_Lite\MD_Converter_Lite.exe` (installed as `MD_Converter.exe`) |
| Executable size | 6,845,458 bytes |
| Executable SHA-256 | `F5AB988168DFA976ED50095A272FB3405CE2CAB395C4A77A34637318D60F7E04` |
| Published identity | `AppId=MDConverter.Quansheng2022`, `AppName=MD Converter`, `AppVersion=1.1.0`, publisher `Quansheng2022` |

Both hashes equal the P12-09 verified candidate exactly (checked in WP-01 and
re-checked after the WP-05 smoke). Post-freeze binary drift = **0**.

## 4. Release payload inventory

Generated folder: `release/MD_Converter_v1.1.0_RC1/` (9 files, 51,142,832 bytes;
the 51 MB installer is intentionally not committed — only the manifest and
checksum definitions are source-controlled).

| Payload file | Present | Role |
|---|---|---|
| `MD_Converter_v1.1.0_Setup.exe` | yes | frozen installer (hash re-verified after copy and transfer) |
| `SHA256SUMS.txt` | yes | checksum manifest (7 payload entries, 0 mismatches) |
| `RC_MANIFEST.md` | yes | RC identity, provenance, documentation inventory |
| `RELEASE_NOTES.md` | yes | release notes (from `RELEASE_NOTES_v1.1.0.md`) |
| `KNOWN_ISSUES.md` | yes | accepted limitations (from `KNOWN_ISSUES_v1.1.0.md`) |
| `INSTALLATION_GUIDE.md` | yes | install / uninstall / troubleshooting |
| `PRIVACY_LOCAL_PROCESSING.md` | yes | local-processing and privacy statement |
| `EULA.txt` | yes | end-user licence (installer `LicenseFile` too) |
| `THIRD_PARTY_NOTICES.txt` | yes | third-party notices (installed copy too) |

Source-controlled definitions: `Doc/V2/Implementation/P12-10/RC_MANIFEST.md`,
`Doc/V2/Implementation/P12-10/SHA256SUMS.txt`,
`Doc/V2/Implementation/P12-10/RC_ACCEPTANCE_CHECKLIST.md`.

## 5. Release documentation identities

```text
Release Notes             RELEASE_NOTES_v1.1.0.md (RC1 section added; no version metadata changed)
Known Issues              KNOWN_ISSUES_v1.1.0.md (user-relevant accepted limitations only)
Install / Uninstall       INSTALLATION_GUIDE_v1.1.0.md
Privacy / Local           PRIVACY_LOCAL_PROCESSING_v1.1.0.md
RC acceptance checklist   Doc/V2/Implementation/P12-10/RC_ACCEPTANCE_CHECKLIST.md
```

Existing authoritative documents were reused rather than duplicated
(`KNOWN_LIMITATIONS_v1.0.0.md`, `INSTALLATION_GUIDE_v1.0.0.md`,
`RELEASE_MANIFEST_v1.1.0.json` was deliberately left untouched because its
content is asserted by `md_converter/tests/test_packaging_metadata.py`).

## 6. Signing state

| Artifact | Signed | Authenticode status |
|---|---|---|
| Installer (source and payload copy) | NO | `NotSigned` |
| Packaged / installed executable | NO | `NotSigned` |

Classification: **KNOWN RELEASE CONDITION** (not a blocker). No frozen
requirement makes signing mandatory for this RC; the release-authority decision
(mandatory signing before public v2.0.0 / limited distribution / approved
temporary release path) is carried to P12-11. No certificate was purchased, no
signing infrastructure was created, and the installer was not modified to fake
trust.

## 7. Distribution readiness

| Check | Result |
|---|---|
| RC folder copies/transfers intact | PASS |
| Installer hash verified after copy and after transfer | PASS (`EFEC378F…B91B9BF`) |
| All checksum entries re-verified after transfer | PASS (7 / 7, 0 mismatches) |
| Installer self-contained, no Python / source tree required | PASS |
| Documentation travels with the payload | PASS |
| New infrastructure (updater / CDN / Store / registry / CI-CD / signing) | NONE |

## 8. Minimal RC smoke (post-freeze)

Executed by `tools/packaging/p12_10_rc_smoke.ps1` against the installed product:

| Step | Result |
|---|---|
| Silent per-user install of the frozen installer | PASS (exit 0) |
| Installed executable identity | PASS (`F5AB9881…0F7E04`, version 1.1.0) |
| Launch installed application | PASS |
| About version | PASS (`Version 1.1.0`) |
| Real conversion (`GUI → GuiWorker → ConversionService → Canonical Core → DOCX`) | PASS (SUCCESS, 9.6 s) |
| DOCX artifact | PASS (contains `word/document.xml`) |
| Open Document — **Word actually opened/read it** | PASS (Word window `01_simple [Compatibility Mode] - Word`, exclusive lock held while displayed, released on close) |
| Settings quick persistence (save → restart → restored) | PASS |
| Clean close | PASS |
| Uninstall | PASS (exit 0; program dir, uninstall entry and Start Menu entries removed) |
| User document preserved | PASS (sentinel and converted DOCX survive) |
| Post-smoke installer hash unchanged | PASS |

```text
34 checks executed, 34 PASS, 0 FAIL
```

Not repeated (P12-09 remains authoritative): full regression, full Canonical,
full Golden, full accessibility matrix, full failure/recovery matrix, and the
full cp1252 investigation (binary identity unchanged; one normal conversion on
the accepted Windows/cp1252 machine sufficed).

## 9. Post-freeze drift

| Property | Result |
|---|---|
| Installer hash drift | 0 |
| Executable hash drift | 0 |
| Version drift | 0 |
| Product source change (`md_converter/`, `pyproject.toml`, `*.spec`, `packaging/`) between `38614c7` and closure | 0 |
| Canonical / Golden / Core semantic drift | 0 (no product change in this phase) |
| Payload modification after freeze | 0 |

## 10. Open blockers

**0.**

Recorded non-blocking items (unchanged from P12-09):

| Item | Status |
|---|---|
| Installer / executable not code-signed | known release condition; P12-11 release-authority decision |
| No authoritative custom product icon | deferred, not release-affecting |
| Word COM post-processing dominates conversion time | unchanged accepted behaviour (E8) |
| Pre-existing uncommitted working-tree changes (`README.md`, `.gitignore`, `md_converter/cli.py` docstring-only) | untouched, unstaged, non-release-affecting |

## 11. Final acceptance criteria

| Criterion | Result |
|---|---|
| RC source identity frozen | PASS |
| RC installer identity frozen | PASS |
| RC executable identity frozen | PASS |
| Version consistency | PASS |
| Release documentation | PASS |
| Artifact manifest | PASS |
| Checksums (after assembly and transfer) | PASS |
| Signing / trust state explicit | PASS |
| Distribution payload | PASS |
| Minimal RC smoke | PASS |
| Post-freeze binary drift = 0 | PASS |
| Open RC blockers = 0 | PASS |

## 12. Decision

```text
P12-10 Release Candidate = CLOSED / ACCEPTED
P12-11 Human Acceptance = AUTHORIZED / NEXT
```
