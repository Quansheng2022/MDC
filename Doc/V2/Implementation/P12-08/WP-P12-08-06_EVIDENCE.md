# WP-P12-08-06 — Release Artifact Verification — Completion Evidence

**Product Baseline SHA:** `1b040c5d0d19f16be127cf3060fb573005a69c81`
**Specification Baseline SHA:** `f6a12779303816ad4f9f1cfebce700cbc8f76ace`
**Input commit:** `507612a` (WP-P12-08-05 verify packaged Windows runtime)
**Authority:** G1 bounded packaging work

## Report record

| Field | Value |
|---|---|
| WP | WP-P12-08-06 — Release Artifact Verification |
| Status | PASS |
| Input baseline SHA | `507612a` |
| Output commit SHA | recorded by the committing run (`P12-08-06 verify release artifacts`) |
| Files added | `tools/packaging/build_windows_release.ps1`, this evidence file |
| Files modified | none |
| Generated artifacts | `dist/MD_Converter_Lite/` (268 files, 158.5 MB), `dist_installer/MD_Converter_v1.1.0_Setup.exe` |
| Tests/checks | clean rebuild x2, payload hygiene, install/launch/convert/uninstall |
| Passed / Failed | 6 / 0 |
| Version | `1.1.0` |
| Direct GUI → Core | none |
| Core / Canonical / QA / Golden change | none |
| CLI/public API change | none |
| Scope deviation | none (pre-existing `dist/` release bundles could not be deleted; see below) |
| Stop condition | none |

## Clean-build procedure (documented, no manual intervention)

`tools/packaging/build_windows_release.ps1` implements the reproducibility rule
from `P12-08_SPECIFICATION_BASELINE` section 9 and runs end to end:

```text
1. remove generated outputs  (build\, build\MD_Converter, build\MD_Converter_Lite,
                              dist\MD_Converter, dist\MD_Converter_Lite,
                              dist_installer\MD_Converter_v1.1.0_Setup.exe)
2. .venv\Scripts\python.exe -m PyInstaller MD_Converter_Lite.spec --noconfirm
3. ISCC.exe MD_Converter.iss           (working directory packaging\windows)
4. print the release artifact inventory (path, bytes, SHA-256)
```

The version resource, notices/EULA payload and system-DLL filtering all come
from source configuration; nothing inside `dist/` is edited by hand.

## Artifact inventory (final clean build)

| Item | Value |
|---|---|
| Build command | `powershell -File tools/packaging/build_windows_release.ps1` |
| Build timestamp | 2026-09-27 21:04:45 +08:00 |
| Product Baseline | `1b040c5d0d19f16be127cf3060fb573005a69c81` |
| Specification Baseline | `f6a12779303816ad4f9f1cfebce700cbc8f76ace` |
| WP commit chain | 08-01 `2135f8b`, 08-02 `cdb4e59`, 08-03 `21f8d7b`, 08-04 `1602b2d`, 08-05 `507612a`, 08-06 this commit |
| Executable | `dist/MD_Converter_Lite/MD_Converter_Lite.exe` |
| Executable size | 6,845,458 bytes |
| Executable SHA-256 | `F5AB988168DFA976ED50095A272FB3405CE2CAB395C4A77A34637318D60F7E04` |
| Payload | 268 files, 158.5 MB |
| Installer | `dist_installer/MD_Converter_v1.1.0_Setup.exe` |
| Installer size | 51,109,717 bytes |
| Installer SHA-256 | `EFEC378F11B00A53791158199B4DC98AA09F44F5B1F013363FF744A92B91B9BF` |
| Version | 1.1.0 (executable resource, installer metadata, installed product) |

Earlier build in the same verification set (build #1, 2026-09-27 21:01:04):
executable `822EA1DEC5458F0075CEA083592422F6CC118B6000518BACFCCD83F52D0397E5`,
installer `2FE994A34C68BAB694ACB3C0176EF4171234513414F37E437DB321C15638D21D`.

## Determinism

Two independent clean builds produced the **same payload inventory**:

```text
payload inventory digest (sorted relative path | size):
  build #1  108B975AA081228F294AA27EECBFCF9BBFB3E3E2A923BAF53C2CA010CB00E9F7
  build #2  108B975AA081228F294AA27EECBFCF9BBFB3E3E2A923BAF53C2CA010CB00E9F7
identical: True
```

Byte-for-byte identical executables/installers are **not** claimed (embedded
timestamps and toolchain metadata differ, as permitted by the specification);
the required property — a repeatable functional build with no manual
post-build editing — holds.

## Payload hygiene

Checked on the final payload (268 files):

| Check | Result |
|---|---|
| `.git`, `.venv`, `__pycache__`, `tests`, `review_packages`, `node_modules`, `*.pyc` | none present |
| Historical release payloads (`release_bundle_*`, `MDC_p11*`) | none present |
| Developer absolute-path configuration (`C:\Users\Quansheng\…`) in text-like files | 0 hits across 9 scanned files |
| Credential-shaped values (`api_key`/`password`/`secret`/`access_token`) in text-like files | 0 hits |
| Test/dev data under `md_converter/` | only `py.typed` and `renderer/themes/default_v1_5.yaml` remain (WP-P12-08-04) |

## Reinstall check (final candidate)

```text
install   : dist_installer\MD_Converter_v1.1.0_Setup.exe /VERYSILENT  -> exit 0
            %LOCALAPPDATA%\Programs\MD_Converter\MD_Converter.exe present
            THIRD_PARTY_NOTICES.txt + EULA.txt present
launch    : main window "MD Converter" visible
convert   : real conversion SUCCESS in 4.7 s, valid DOCX written
uninstall : unins000.exe /VERYSILENT -> exit 0
            program directory removed, uninstall registry entry gone,
            Documents\MD_Converter user workspace preserved
```

## Notes and constraints recorded

* `dist/` also holds pre-existing release bundles from earlier phases
  (`md_converter-1.1.0-*.whl`, `*.tar.gz`, `release_bundle_v1.0.1/v1.1.0.zip`,
  `MD_Converter_Lite.7z`, `SHA256SUMS_v1.1.0`). Those files are protected
  against deletion in this environment (`Access to the path … is denied`), so the
  clean step removes the packaging outputs this pipeline owns and reports, never
  silently ignores, anything it cannot remove. None of those files are part of
  the packaged payload or the installer.
* `build/MD_Converter` (full profile) is not produced by the release procedure;
  the accepted release payload is the Lite profile, as recorded in
  WP-P12-08-01/02.
