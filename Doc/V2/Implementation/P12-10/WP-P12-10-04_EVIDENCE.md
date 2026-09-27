# WP-P12-10-04 — Signing / Distribution Readiness — Evidence

**Product Baseline:** `4c02734` (P12-09 Closure)
**Input HEAD:** `e954a680cf29f050278661cd78c9ac1d04cbf446` (WP-P12-10-03)
**Status:** PASS

## 1. Authenticode inspection

| Artifact | Signed | Authenticode status | Signer / certificate |
|---|---|---|---|
| `dist_installer\MD_Converter_v1.1.0_Setup.exe` | NO | `NotSigned` | none |
| `dist\MD_Converter_Lite\MD_Converter_Lite.exe` | NO | `NotSigned` | none |
| `release\MD_Converter_v1.1.0_RC1\MD_Converter_v1.1.0_Setup.exe` (payload copy) | NO | `NotSigned` | none |

No signer certificate, no timestamp certificate and no signature validity can be
recorded because no signature exists. This was an inspection only: no
certificate was bought or generated and no signing infrastructure was built.

## 2. Classification of the unsigned state

The RC installer and executable are **unsigned**. Per the P12-10 specification,
unsigned is not automatically BLOCKED, so the existing frozen requirements were
reviewed:

| Source | Statement |
|---|---|
| `Doc/V2/V2_RELEASE_PLAN.md` section 15 | code signing is a high-priority distribution requirement for commercial/public Windows distribution; if signing is not ready for the first RC, the *release approval* must explicitly decide between mandatory signing, limited/private distribution, or an approved temporary release path — owned by Human Release Authority |
| `Doc/V2/V2_IMPLEMENTATION_PLAN.md` section 12 | code signing recommended for commercial release, may be managed as a release/distribution work item when certificate procurement is external |
| `P12-08_SPECIFICATION_BASELINE.md` | code-signing procurement declared out of scope for the packaging phase |
| P12-09 closure | `E7 installer not code-signed` recorded as an approved exception; open blockers = 0 |

No frozen requirement makes signing a hard gate for this RC. The classification
is therefore:

```text
Signing / trust classification = KNOWN RELEASE CONDITION (not a blocker)
```

Expected Windows trust behaviour (recorded, not hidden): because the binaries
are unsigned, Microsoft Defender SmartScreen may show an Unknown Publisher /
"Windows protected your PC" prompt on first run; the user can continue through
"More info" then "Run anyway". This is mirrored in user-facing
`KNOWN_ISSUES_v1.1.0.md` section 6 and `INSTALLATION_GUIDE_v1.1.0.md`.

The underlying release-authority decision (mandatory signing before public
v2.0.0 / limited distribution / approved temporary release path) is carried to
**P12-11 Human Acceptance**; P12-10 does not and must not make it.

## 3. Distribution readiness

The assembled RC folder was copied to a separate location to simulate
controlled transfer:

```text
source : release\MD_Converter_v1.1.0_RC1\
target : %TEMP%\mdc_rc_transfer_20260927_234054\MD_Converter_v1.1.0_RC1\
```

| Check | Result |
|---|---|
| RC folder copies/transfers intact | PASS (9 files) |
| Installer size after transfer | 51,109,717 bytes (unchanged) |
| Installer SHA-256 after transfer | `EFEC378F…B91B9BF` (equals frozen WP-01 hash) |
| All `SHA256SUMS.txt` entries re-verified in the transferred copy | PASS (7 entries, 0 mismatches) |
| Documentation transferred with the payload | PASS |
| Installer remains self-contained | PASS |
| Python installation or source tree required | NO |
| Installer hash verifies after copy and transfer | PASS |

## 4. Infrastructure boundary

Deliberately **not** created or procured in this phase:

```text
updater / CDN / Store publishing / artifact registry / CI-CD release pipeline /
signing infrastructure / code-signing certificate
```

No change was made to the installer to fake trust, and no binary was rebuilt,
patched or re-signed.

## 5. Checks

| Check | Result |
|---|---|
| Installer signing status explicit | PASS (unsigned, `NotSigned`) |
| Executable signing status explicit | PASS (unsigned, `NotSigned`) |
| Existing release requirements reviewed before classifying | PASS |
| Signing classification recorded as known release condition | PASS |
| Expected SmartScreen behaviour recorded | PASS |
| RC payload transferable without breaking documentation | PASS |
| Checksums verify after transfer | PASS |
| Installer self-contained, no Python/source required | PASS |
| New infrastructure created | NONE (forbidden) |
| R2/R3 action required | NONE |

Evidence record: `Doc/V2/Implementation/P12-10/evidence/wp04_signing_distribution.json`

## 6. Acceptance

Signing/trust status is explicit and the RC payload is ready for controlled
distribution. **WP-P12-10-04 = PASS.**
