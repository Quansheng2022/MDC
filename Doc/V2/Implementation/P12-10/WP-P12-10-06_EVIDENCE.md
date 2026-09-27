# WP-P12-10-06 — RC Acceptance Gate — Evidence

**Product Baseline:** `4c02734` (P12-09 Closure)
**Input HEAD:** `0894442fa18f7061028157bdc247752bd89b4c46` (WP-P12-10-05)
**Status:** PASS

## 1. Gate questions (master instruction, 12)

| # | Question | Answer | Evidence |
|---|---|---|---|
| 1 | Is the RC binary identical to the P12-09 verified candidate? | **YES** | WP-01 §2 (re-hashed), WP-05 precheck + post-smoke re-hash — hash drift 0 |
| 2 | Is source identity frozen? | **YES** | WP-01 §5; `git diff --name-status 38614c7 HEAD -- md_converter pyproject.toml MD_Converter.spec MD_Converter_Lite.spec packaging` is empty |
| 3 | Is version internally consistent? | **YES** | `pyproject.toml` 1.1.0, executable 1.1.0, installer 1.1.0.0, About `Version 1.1.0` (WP-05), uninstall entry `1.1.0` (WP-05) |
| 4 | Is installer identity frozen and hashable? | **YES** | WP-01 §1-2; `RC_MANIFEST.md`; `SHA256SUMS.txt` |
| 5 | Are Release Notes accurate? | **YES** | WP-02; `RELEASE_NOTES_v1.1.0.md` (RC1 section) |
| 6 | Are Known Issues adequate? | **YES** | WP-02; `KNOWN_ISSUES_v1.1.0.md` (user-relevant accepted limitations only) |
| 7 | Is signing/trust status explicit? | **YES** | WP-04: installer and executable `NotSigned`; classified KNOWN RELEASE CONDITION; expected SmartScreen behaviour recorded |
| 8 | Can a user install without developer tooling? | **YES** | WP-05: silent per-user install exit 0; no Python, no admin, no service/autostart |
| 9 | Can a user convert successfully? | **YES** | WP-05: `SUCCESS` in 9.6 s; valid DOCX produced by the installed app |
| 10 | Can uninstall preserve user documents? | **YES** | WP-05: uninstall exit 0; sentinel and converted DOCX preserved |
| 11 | Is post-freeze binary drift = 0? | **YES** | WP-05 §3: installer SHA-256 unchanged after the whole smoke |
| 12 | Are open RC blockers = 0? | **YES** | this gate; `P12-10_CLOSURE_EVIDENCE.md` |

## 2. Gate questions (WP specification, 10)

All ten specification gate questions are answered **YES** by the same evidence
(installer/executable identity, version consistency, release notes, known
issues, explicit signing/trust status, install without developer tooling,
successful conversion, document-preserving uninstall, zero open blockers).

## 3. Block conditions

| Block condition | Triggered |
|---|---|
| Artifact hash drift | NO |
| Source/artifact ambiguity | NO |
| Version mismatch | NO |
| Missing required EULA / notices payload | NO |
| Failed minimal smoke | NO |
| Unresolved release blocker | NO |
| Post-freeze package modification | NO |

## 4. Release payload at gate time

```text
release/MD_Converter_v1.1.0_RC1/   9 files
  MD_Converter_v1.1.0_Setup.exe    frozen, hash-verified twice
  SHA256SUMS.txt                   7 payload entries, 0 mismatches after transfer
  RC_MANIFEST.md                   RC identity + provenance + documentation inventory
  RELEASE_NOTES.md                 present
  KNOWN_ISSUES.md                  present
  INSTALLATION_GUIDE.md            present
  PRIVACY_LOCAL_PROCESSING.md      present
  EULA.txt                         present
  THIRD_PARTY_NOTICES.txt          present
```

## 5. Recorded non-blocking items

These are unchanged from P12-09 and are explicitly **not** RC blockers:

| Item | Status |
|---|---|
| Installer and executable are not code-signed | recorded known release condition; release-authority decision carried to P12-11 (WP-04) |
| No authoritative custom product icon | deferred (unchanged, not release-affecting) |
| Word COM post-processing dominates conversion time | unchanged behaviour (P12-08 E8) |
| Pre-existing uncommitted working-tree changes (`README.md` content rewrite, `.gitignore` rules, `md_converter/cli.py` docstring-only 2-line change) | untouched by P12-10; not staged, not committed, not release-affecting (the same item P12-09 recorded as a non-blocking observation) |

## 6. Decision

```text
All release-critical gate answers = YES
Open RC blockers = 0
RC acceptance gate = PASS
RC may enter P12-11 Human Acceptance
```

Evidence record: `Doc/V2/Implementation/P12-10/evidence/wp06_rc_acceptance_gate.json`

**WP-P12-10-06 = PASS.**
