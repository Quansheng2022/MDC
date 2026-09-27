# WP-P12-08-03 — Windows Installer — Completion Evidence

**Product Baseline SHA:** `1b040c5d0d19f16be127cf3060fb573005a69c81`
**Specification Baseline SHA:** `f6a12779303816ad4f9f1cfebce700cbc8f76ace`
**Input commit:** `cdb4e59` (WP-P12-08-02 package Windows executable)
**Authority:** G1 bounded packaging work

## Report record

| Field | Value |
|---|---|
| WP | WP-P12-08-03 — Windows Installer |
| Status | PASS |
| Input baseline SHA | `cdb4e59` |
| Output commit SHA | recorded by the committing run (`P12-08-03 add Windows installer`) |
| Files added | `packaging/windows/MD_Converter.iss`, this evidence file |
| Files modified | none other |
| Generated artifacts | `dist_installer/MD_Converter_v1.1.0_Setup.exe` |
| Tests/checks | installer compile + silent install + installed launch + silent uninstall |
| Passed / Failed | 10 / 0 |
| Installer | `dist_installer/MD_Converter_v1.1.0_Setup.exe` (51,123,887 bytes) |
| Installer SHA-256 | `04FAA91EBDC8F0334B69BFA8FEF5C902EA57CF2D8B72F752CC2CEE8FEC765F3C` |
| Version | `1.1.0` |
| Install | PASS (silent, exit code 0) |
| Uninstall | PASS (silent, exit code 0, "Removed all? Yes") |
| Direct GUI → Core | none |
| Conversion semantic change | none |
| Core change | none |
| Golden change | none |
| CLI/public API change | none |
| Scope deviation | none (the installer script was a new file for this WP; WP-08-01 committed only the launcher) |
| Stop condition | none |

## Installer stack

* Technology: Inno Setup (compiler engine 7.1.0 present on this machine;
  the script is the accepted Inno Setup 6-era contract).
* Script: `packaging/windows/MD_Converter.iss`.
* Build command:
  `"%LOCALAPPDATA%\Programs\Inno Setup 7\ISCC.exe" MD_Converter.iss`
  executed with `packaging/windows` as the working directory (the script's
  `Source` paths are relative to it).
* Output: `dist_installer/MD_Converter_v1.1.0_Setup.exe`.

## Installer-script defects found and corrected (packaging-only)

The accepted script did not compile at all with the accepted installer
technology:

| Defect | Effect | Correction |
|---|---|---|
| Two `StringSplit(...)` calls split their parameters over several lines, so a line began with `[';'],` | Inno Setup parses a line starting with `[` as a new section tag: `Error on line 384 ... Invalid section tag` | Each call is now a single line: `Parts := StringSplit(PathValue, [';'], stExcludeEmpty);` |
| `; Only remove PATH if THIS installer added it.` inside `[Code]` | Pascal comments in `[Code]` are `//`, not `;`: `Error on line 382 ... Unknown identifier 'The'` | Converted to `//` (and the added explanation comment uses `//`) |
| `IsTaskSelected('addtopath')` | Inno Setup 7 compiles it but reports: *Support function "IsTaskSelected" has been renamed. Use "WizardIsTaskSelected" instead.* | Renamed to `WizardIsTaskSelected('addtopath')` |

No installer behaviour, payload, install location, shortcut, version metadata,
EULA wiring or PATH-ownership logic was changed.

## Accepted installer contract (unchanged)

* Per-user install, no elevation: `PrivilegesRequired=lowest`,
  `DefaultDirName={localappdata}\Programs\MD_Converter`.
* Windows 10+ x64: `MinVersion=10.0`, `SetupArchitecture=x64`,
  `ArchitecturesAllowed=x64compatible`.
* Payload: `dist\MD_Converter_Lite\MD_Converter_Lite.exe` installed as
  `MD_Converter.exe`, plus `_internal\*` beside it.
* User workspace: `{userdocs}\MD_Converter\{input,output}` with
  `uninsneveruninstall`.
* Shortcuts: Start Menu entry, optional (unchecked) desktop shortcut,
  Input/Output folder shortcuts, Uninstall entry.
* PATH: optional `addtopath` task, current user only, marker-based removal.
* EULA: `LicenseFile=..\..\EULA.txt`.
* App identity: `AppId=MDConverter.Quansheng2022`, `AppName=MD Converter`,
  `AppVersion=1.1.0`, publisher `Quansheng2022`.

## Verification

| # | Check | Result |
|---|---|---|
| 1 | Installer compiles (ISCC exit 0, no warnings) | PASS |
| 2 | Silent install runs and completes (`/VERYSILENT`, exit 0) | PASS |
| 3 | Installed payload exists: 294 files (`dist` 292 files + `unins000.exe/.dat`) | PASS |
| 4 | Installed `MD_Converter.exe` byte-identical to the packaged executable (`MD_Converter_Lite.exe` renamed) | PASS |
| 5 | Uninstall registration present: `HKCU\...\Uninstall\MDConverter.Quansheng2022_is1`, `DisplayName = MD Converter 1.1.0`, `DisplayVersion = 1.1.0` | PASS |
| 6 | Start Menu shortcut launches the installed application (`MD Converter.lnk` → `%LOCALAPPDATA%\Programs\MD_Converter\MD_Converter.exe`, window title "MD Converter") | PASS |
| 7 | Installed application starts and performs a real conversion (packaged GUI smoke harness against the installed path: 11/11 checks PASS, conversion SUCCESS in 4.7 s, valid DOCX) | PASS |
| 8 | Uninstall succeeds (`unins000.exe /VERYSILENT`, exit 0, log "Removed all? Yes") | PASS |
| 9 | User documents preserved: `Documents\MD_Converter\{input,output}` and a sentinel file placed before uninstall both survived | PASS |
| 10 | Unrelated settings preserved: `HKCU\Software\MD Converter` (GUI preferences) untouched by uninstall; Start Menu entries and the uninstall registry entry removed | PASS |

## Observed behaviour recorded (not changed)

* The application was already installed before this WP (a historical install),
  so the first install ran as an upgrade over it and the installer reported
  `MD Converter PATH entry already exists`; because the entry was not added by
  that run, no `PathAddedByInstaller` marker was written and the uninstaller
  correctly left the current-user `PATH` untouched
  (`No installer PATH marker found. PATH will not be modified.`).
* Upgrading over an existing installation leaves files from the older payload in
  place (Inno Setup does not remove unknown files); the clean-install payload
  comparison above was taken after an uninstall.
* The installed executable currently carries no version resource
  (`ProductVersion` / `FileDescription` empty) — WP-P12-08-04 owns metadata.

## Notes for later work packages

* The installer is not code-signed (out of scope per the specification).
* WP-P12-08-06 will rebuild build/, dist/ and dist_installer/ from a clean state
  and record the final artifact hashes.
