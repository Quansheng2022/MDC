# MD Converter v1.1.0 RC1 — Release Candidate Manifest

**RC identifier:** MD Converter v1.1.0 RC1 (evidence-only label)
**Product version:** 1.1.0
**Phase:** P12-10 — Release Candidate
**Created:** 2026-09-27T23:40:00+08:00

## 1. Frozen identity

| Item | Value |
|---|---|
| Source SHA (frozen product source) | `4c027344fbd9ca7d05190fe7f689c4edad11dd8d` |
| P12-09 Closure SHA | `4c027344fbd9ca7d05190fe7f689c4edad11dd8d` |
| P12-10 Specification Baseline SHA | `3a0dfdceae70b709c674d43656cbffed7cd969e8` |
| Installer filename | `MD_Converter_v1.1.0_Setup.exe` |
| Installer size | 51,109,717 bytes |
| Installer SHA-256 | `EFEC378F11B00A53791158199B4DC98AA09F44F5B1F013363FF744A92B91B9BF` |
| Executable (packaged payload) | `dist\MD_Converter_Lite\MD_Converter_Lite.exe` |
| Executable size | 6,845,458 bytes |
| Executable SHA-256 | `F5AB988168DFA976ED50095A272FB3405CE2CAB395C4A77A34637318D60F7E04` |
| Published identity | `AppId=MDConverter.Quansheng2022`, `AppName=MD Converter`, `AppVersion=1.1.0`, publisher `Quansheng2022` |

The installer is byte-identical to the P12-09 verified candidate
(`Doc/V2/Implementation/P12-09/evidence/wp01_candidate_identity.json`); the
executable is the exact payload this installer deploys.

## 2. Build provenance

```text
P12-08 packaging closure     38614c7bb555f96685c301bc4b6abd71138c2642
bundler                      PyInstaller 6.22.3, onedir COLLECT
release spec                 MD_Converter_Lite.spec
entry point                  packaging/windows/launcher_main.py -> md_converter.gui.app.main
executable mode              windowed (console=False)
installer technology         Inno Setup, packaging/windows/MD_Converter.iss (compiler engine 7.1.0)
clean-build procedure        tools/packaging/build_windows_release.ps1
install strategy             per-user {localappdata}\Programs\MD_Converter, PrivilegesRequired=lowest
verification provenance      P12-08 closure 38614c7, P12-09 closure 4c02734
```

## 3. Payload inventory

Assembled folder: `release/MD_Converter_v1.1.0_RC1/` (generated locally; the
large installer binary is intentionally not committed — only this manifest and
`SHA256SUMS.txt` are source-controlled).

```text
MD_Converter_v1.1.0_Setup.exe
SHA256SUMS.txt
RC_MANIFEST.md
RELEASE_NOTES.md
KNOWN_ISSUES.md
INSTALLATION_GUIDE.md
PRIVACY_LOCAL_PROCESSING.md
EULA.txt
THIRD_PARTY_NOTICES.txt
```

Documentation inventory and provenance:

| Payload file | Source (repository) |
|---|---|
| `RELEASE_NOTES.md` | `RELEASE_NOTES_v1.1.0.md` (RC1 section) |
| `KNOWN_ISSUES.md` | `KNOWN_ISSUES_v1.1.0.md` |
| `INSTALLATION_GUIDE.md` | `INSTALLATION_GUIDE_v1.1.0.md` |
| `PRIVACY_LOCAL_PROCESSING.md` | `PRIVACY_LOCAL_PROCESSING_v1.1.0.md` |
| `EULA.txt` | `EULA.txt` |
| `THIRD_PARTY_NOTICES.txt` | `THIRD_PARTY_NOTICES.txt` |
| `RC_MANIFEST.md` | `Doc/V2/Implementation/P12-10/RC_MANIFEST.md` |
| `SHA256SUMS.txt` | `Doc/V2/Implementation/P12-10/SHA256SUMS.txt` |

Documentation hashes (source-controlled definitions):

| File | SHA-256 |
|---|---|
| `RELEASE_NOTES.md` | `DE158647B1DFC4FED71A07B608897FAB4E4880E546546D26D08F4F6E74F66D89` |
| `KNOWN_ISSUES.md` | `E75F19DE886046A2DB3759FF506C5E2F01DCA5AF171F25F276B56B01EFF86E78` |
| `INSTALLATION_GUIDE.md` | `D8F3878F18E7AB29B1E538163EF04E834D9FD5531FFC84ED96F9E5580A269816` |
| `PRIVACY_LOCAL_PROCESSING.md` | `43E92CEF3AAE4839F61AD3A4A83098A25DBC43E549B1BBF72D6E5411DFDB4DD2` |
| `EULA.txt` | `4D3451765A91B098F727F9C4B077C2F677D1ACC375159BD876EEA63B533F7ABF` |
| `THIRD_PARTY_NOTICES.txt` | `75912F8389836D892A6BD24E0A89A41393D2CBDAEA42E01DBBC1B9957BB2C384` |

## 4. Assembly rules applied

```text
installer bytes copied, never rebuilt or patched
post-copy installer SHA-256 re-verified against the WP-01 frozen hash
payload contains no .git, .venv, tests, caches, review packages, historical
    releases, credentials or developer-only files
no Python installation or source tree is required by the payload
```

## 5. Signing / trust status

Installation of the payload does not require developer tooling. The installer
and executable are not code-signed; this is a recorded known release condition,
not a blocker (see `WP-P12-10-04_EVIDENCE.md`).

## 6. Verification of the assembled payload

See `WP-P12-10-03_EVIDENCE.md` (assembly) and `WP-P12-10-04_EVIDENCE.md`
(distribution readiness, checksum re-verification after copy/transfer).
