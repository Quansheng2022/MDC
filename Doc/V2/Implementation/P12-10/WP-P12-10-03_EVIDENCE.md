# WP-P12-10-03 — RC Artifact Assembly — Evidence

**Product Baseline:** `4c02734` (P12-09 Closure)
**Input HEAD:** `c0d94d899d24cd26dd1da0f0458e6fafb99e1afe` (WP-P12-10-02)
**Status:** PASS

## 1. Generated RC directory

```text
release/MD_Converter_v1.1.0_RC1/
```

The folder is generated locally and holds the exact accepted binaries plus the
release documentation. Per the phase rule, the 51 MB installer is **not**
committed; the source-controlled RC definitions are this evidence file,
`RC_MANIFEST.md` and `SHA256SUMS.txt`.

## 2. Payload inventory (re-read after assembly)

| File | Size (bytes) | SHA-256 |
|---|---|---|
| `MD_Converter_v1.1.0_Setup.exe` | 51,109,717 | `EFEC378F11B00A53791158199B4DC98AA09F44F5B1F013363FF744A92B91B9BF` |
| `SHA256SUMS.txt` | 1,175 | `8D4A1558E319C4F4F1E8AAD3EF7F5030BAA6AD4BBF8C38495AFD7B30012689DA` |
| `RC_MANIFEST.md` | 4,370 | `5D181DBB0594657484110DD22B3B7AC8AD031B2B705D6995C21017B1EA77E4AB` |
| `RELEASE_NOTES.md` | 6,743 | `DE158647B1DFC4FED71A07B608897FAB4E4880E546546D26D08F4F6E74F66D89` |
| `KNOWN_ISSUES.md` | 3,364 | `E75F19DE886046A2DB3759FF506C5E2F01DCA5AF171F25F276B56B01EFF86E78` |
| `INSTALLATION_GUIDE.md` | 3,778 | `D8F3878F18E7AB29B1E538163EF04E834D9FD5531FFC84ED96F9E5580A269816` |
| `PRIVACY_LOCAL_PROCESSING.md` | 2,213 | `43E92CEF3AAE4839F61AD3A4A83098A25DBC43E549B1BBF72D6E5411DFDB4DD2` |
| `EULA.txt` | 713 | `4D3451765A91B098F727F9C4B077C2F677D1ACC375159BD876EEA63B533F7ABF` |
| `THIRD_PARTY_NOTICES.txt` | 10,759 | `75912F8389836D892A6BD24E0A89A41393D2CBDAEA42E01DBBC1B9957BB2C384` |

```text
payload files = 9
payload bytes = 51,142,832
subdirectories = 0
```

## 3. Post-copy installer hash verification

| Check | Result |
|---|---|
| Installer copied, not rebuilt or patched | PASS |
| Post-copy installer size = 51,109,717 bytes | PASS |
| Post-copy installer SHA-256 = WP-01 frozen hash | PASS |
| Installer bytes changed during assembly | NO |

The copied installer hash equals the WP-P12-10-01 frozen hash and the P12-09
verified candidate hash exactly. No stop condition was triggered.

## 4. Documentation copies

Every documentation hash in the payload equals the hash of its repository
source recorded in `RC_MANIFEST.md` §3, so the published copies are the reviewed
documents and no content drifted during assembly:

```text
RELEASE_NOTES.md            <- RELEASE_NOTES_v1.1.0.md            match YES
KNOWN_ISSUES.md             <- KNOWN_ISSUES_v1.1.0.md             match YES
INSTALLATION_GUIDE.md       <- INSTALLATION_GUIDE_v1.1.0.md       match YES
PRIVACY_LOCAL_PROCESSING.md <- PRIVACY_LOCAL_PROCESSING_v1.1.0.md match YES
EULA.txt                    <- EULA.txt                           match YES
THIRD_PARTY_NOTICES.txt     <- THIRD_PARTY_NOTICES.txt            match YES
RC_MANIFEST.md              <- Doc/V2/Implementation/P12-10/RC_MANIFEST.md   match YES
SHA256SUMS.txt              <- Doc/V2/Implementation/P12-10/SHA256SUMS.txt   match YES
```

## 5. Payload hygiene

The generated folder contains exactly the nine payload files and no
subdirectory. The excluded material is therefore absent by construction:

```text
.git / .venv / tests / caches / review packages / historical releases /
credentials / secrets / developer-only files / Python source tree
```

`SHA256SUMS.txt` lists every payload file except itself and `RC_MANIFEST.md`
(both are declared as not self-hashed); no stale or unlisted payload file
exists.

## 6. Windows filename safety

```text
release folder : MD_Converter_v1.1.0_RC1   (letters, digits, underscore only)
payload files  : no \ / : * ? " < > | characters
```

## 7. Checks

| Check | Result |
|---|---|
| RC payload assembled from frozen artifacts only | PASS |
| Installer bytes unmodified (`hash == WP-01`) | PASS |
| Documentation copies byte-identical to sources | PASS |
| Checksum manifest consistent with payload | PASS |
| Payload hygiene (no development/secret material) | PASS |
| `RC_MANIFEST.md` records RC id, version, source SHA, P12-09 closure SHA, P12-10 spec baseline, installer/executable identity, provenance, documentation inventory, timestamp | PASS |
| Windows filename safety | PASS |
| R2 (artifact-affecting) action required | NONE |

## 8. Acceptance

The RC folder contains only the intended payload and all hashes match
WP-P12-10-01. **WP-P12-10-03 = PASS.**
