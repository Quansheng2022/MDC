# WP-P12-09-06 — Privacy / Locality / Release Integrity — Completion Evidence

**Product Baseline SHA:** `38614c7bb555f96685c301bc4b6abd71138c2642`
**Specification Baseline SHA:** `08b198043ad107cdcd9293152acfa756fd6fa410`
**Input commit:** `e8d9200` (WP-P12-09-05)
**Authority:** verification only; no production code change

## Report record

| Field | Value |
|---|---|
| WP | WP-P12-09-06 — Privacy / Locality / Release Integrity |
| Status | PASS |
| Input baseline SHA | `e8d9200` |
| Output commit SHA | recorded by the committing run (`P12-09-06 verify privacy locality and release integrity`) |
| Candidate installer | `MD_Converter_v1.1.0_Setup.exe`, SHA-256 `EFEC378F…B91B9BF`, 51,109,717 bytes, version 1.1.0 |
| Candidate executable | `MD_Converter_Lite.exe`, SHA-256 `F5AB9881…0F7E04`, 6,845,458 bytes, version 1.1.0 |
| Files added | this evidence file, `tools/packaging/p12_09_release_integrity.ps1`, `evidence/wp06_privacy_locality_integrity.json` |
| Files modified | none |
| Checks executed | 12 integrity/locality checks + 1 static capability scan |
| Passed / Failed | all PASS / 0 |
| Scope deviation | none |
| Stop condition | none |

## Frozen positioning and bounded claims

The About surface (captured live in WP-09-02) states exactly the frozen
positioning and the bounded local/private facts:

> **Turn Markdown into polished Word documents — locally, privately, and without a subscription.**

| Bounded claim | Where it is verified | Result |
|---|---|---|
| Conversion processing is local | About: `Processing: Local, on this computer`; real conversions succeed with no network | PASS |
| No account required | About: `Account required: No`; no login/activation surface exists | PASS |
| No document upload required by the normal workflow | About: `Document upload: Not required for normal conversion`; no upload occurs | PASS |

No broader claim (for example "the process can never access the network") is
made anywhere in this evidence; the verification is limited to "no *required*
network dependency for the normal workflow".

## Required network dependency

The packaged product was launched and then performed a real representative
conversion while its own TCP connections were sampled.

| Check | Observed | Result |
|---|---|---|
| Launch | main window visible | PASS |
| Representative conversion | outcome `SUCCESS` | PASS |
| Established remote connections owned by the product process | 0 (the process owned no TCP connections at all during the run) | PASS |

Because no connection is required, the normal workflow has no required network
dependency. This is a bounded observation, **not** a penetration test and not a
claim that the process can never open a socket.

## Static capability scan (shipped source)

| Finding | Interpretation |
|---|---|
| `md_converter/renderer/word_writer.py` uses `urllib.parse.unquote_to_bytes` | pure percent-decoding of embedded data-URI images — no network access |
| remaining matches are a docstring and a `PassEntry` substring | no HTTP client, socket, telemetry, updater, analytics or credential handling |

No `requests`, `http.client`, `socket`, telemetry, updater or API-key handling
exists in the shipped package.

## Artifact integrity

| Check | Observed | Result |
|---|---|---|
| Installer filename | `MD_Converter_v1.1.0_Setup.exe` | PASS |
| Installer version / size | 1.1.0.0 / 51,109,717 bytes | PASS |
| Installer SHA-256 matches frozen candidate | `EFEC378F11B00A53791158199B4DC98AA09F44F5B1F013363FF744A92B91B9BF` | PASS |
| Executable SHA-256 matches frozen candidate | `F5AB988168DFA976ED50095A272FB3405CE2CAB395C4A77A34637318D60F7E04` | PASS |
| Version consistency | `pyproject.toml` 1.1.0 = executable 1.1.0 = installer 1.1.0 = About "Version 1.1.0" = uninstall `DisplayVersion` 1.1.0 | PASS |
| EULA included | `EULA.txt` bundled and installed (WP-09-04) | PASS |
| THIRD_PARTY_NOTICES included | `THIRD_PARTY_NOTICES.txt` bundled and installed (WP-09-04) | PASS |

## Payload inventory

| Check | Observed | Result |
|---|---|---|
| Payload size | 268 files, 166,150,109 bytes | PASS |
| Development material (`.git`, `.venv`, tests, caches, `review_packages`, credentials, key material) | 0 hits | PASS |
| Developer absolute paths in bundled text files | 0 hits | PASS |

The payload contains no `.git`, `.venv`, `__pycache__`, `.pytest_cache`,
`.mypy_cache`, `.ruff_cache`, `review_packages`, test directories, `.env`,
certificate/key files, credential stores or developer absolute-path
configuration.

## Rebuild traceability

No rebuild was performed (candidate identity was not uncertain). The current
payload maps to the P12-08 clean build:

| Property | P12-08 clean-build record | Current candidate | Match |
|---|---|---|---|
| Payload inventory | 268 files, 158.5 MB | 268 files, 166,150,109 bytes (158.5 MiB) | yes |
| Executable SHA-256 | `F5AB9881…0F7E04` | `F5AB9881…0F7E04` | yes |
| Installer SHA-256 | `EFEC378F…B91B9BF` | `EFEC378F…B91B9BF` | yes |
| Independent clean builds | two builds produced the same inventory hash `108B975A…00E9F7` | payload unchanged | yes |

The P12-08 clean-build evidence therefore still maps to this candidate.

## Defects

| Class | Count | Detail |
|---|---|---|
| V0 observations | 0 | — |
| V1 corrections | 0 | — |
| V2 blockers | 0 | — |
| V3 blockers | 0 | — |

## Acceptance

| Criterion | Result |
|---|---|
| Locality claims remain accurate | PASS |
| No required network dependency in the normal workflow | PASS |
| Artifact identity / integrity consistent | PASS |
| EULA and third-party notices included | PASS |
| Payload free of development-only material | PASS |
| Rebuild traceability to P12-08 | PASS |

## Conclusion

WP-P12-09-06 passes. The candidate keeps the frozen local/private positioning
with bounded wording, needs no network for its normal workflow, carries a
consistent version and identity across source, executable, installer and About,
ships its licence and notices, and contains no development-only payload.
