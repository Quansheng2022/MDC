# P12-10 — RC Acceptance Checklist

**RC identifier:** MD Converter v1.1.0 RC1
**Version:** 1.1.0
**Installer:** `MD_Converter_v1.1.0_Setup.exe`, 51,109,717 bytes,
SHA-256 `EFEC378F11B00A53791158199B4DC98AA09F44F5B1F013363FF744A92B91B9BF`

Checklist for P12-11 Human Acceptance. Each item must be answerable YES from
frozen evidence; a NO is a release blocker. The per-item answers are recorded by
WP-P12-10-06 (`WP-P12-10-06_EVIDENCE.md`); this file defines the criteria and
their evidence sources.

| # | Criterion | Evidence source | Answered by |
|---|---|---|---|
| 1 | RC installer is byte-identical to the P12-09 verified candidate | `evidence/wp01_rc_candidate_identity.json` | WP-01 / WP-05 |
| 2 | RC executable identity is frozen and matches P12-09 | `evidence/wp01_rc_candidate_identity.json` | WP-01 / WP-05 |
| 3 | Source identity frozen (no product change since packaging closure) | `WP-P12-10-01_EVIDENCE.md` §5 | WP-01 / WP-06 |
| 4 | Version internally consistent (`1.1.0` in source, exe, installer, About) | `WP-P12-10-01_EVIDENCE.md` §3 | WP-01 / WP-05 |
| 5 | Release notes accurate and free of unverified claims | `RELEASE_NOTES_v1.1.0.md` | WP-02 |
| 6 | Known issues list user-relevant accepted limitations only | `KNOWN_ISSUES_v1.1.0.md` | WP-02 |
| 7 | Install / uninstall documented for the installer | `INSTALLATION_GUIDE_v1.1.0.md` | WP-02 |
| 8 | Privacy / local-processing statement present and accurate | `PRIVACY_LOCAL_PROCESSING_v1.1.0.md` | WP-02 |
| 9 | Signing / trust status explicit (unsigned = known release condition) | `WP-P12-10-04_EVIDENCE.md` | WP-04 |
| 10 | RC payload assembled from the frozen artifact without modification | `WP-P12-10-03_EVIDENCE.md`, `RC_MANIFEST.md` | WP-03 |
| 11 | Checksums re-verified after assembly/transfer | `WP-P12-10-03_EVIDENCE.md`, `WP-P12-10-04_EVIDENCE.md` | WP-03 / WP-04 |
| 12 | Minimal post-freeze smoke PASS (install → convert → Word open → uninstall) | `WP-P12-10-05_EVIDENCE.md` | WP-05 |
| 13 | Post-freeze binary drift = 0 | `WP-P12-10-05_EVIDENCE.md` | WP-05 |
| 14 | Open RC blockers = 0 | `P12-10_CLOSURE_EVIDENCE.md` | WP-06 / WP-07 |

EULA / THIRD_PARTY_NOTICES presence is covered by WP-03 (payload inventory) and
WP-04 (distribution readiness).
