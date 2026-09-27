# WP-P12-08-02 — Windows Executable Packaging — Completion Evidence

**Product Baseline SHA:** `1b040c5d0d19f16be127cf3060fb573005a69c81`
**Specification Baseline SHA:** `f6a12779303816ad4f9f1cfebce700cbc8f76ace`
**Input commit:** `2135f8b` (WP-P12-08-01 freeze packaging baseline)
**Authority:** G1 bounded packaging work

## Report record

| Field | Value |
|---|---|
| WP | WP-P12-08-02 — Windows Executable Packaging |
| Status | PASS |
| Input baseline SHA | `2135f8b` |
| Output commit SHA | recorded by the committing run (`P12-08-02 package Windows executable`) |
| Files added | `tools/packaging/windows_gui_smoke.ps1`, this evidence file |
| Files modified | `MD_Converter.spec`, `MD_Converter_Lite.spec` |
| Generated artifacts | `dist/MD_Converter_Lite/` (292 files, 158.6 MB), `build/MD_Converter_Lite/` |
| Tests/checks | packaged GUI smoke harness, 11 checks |
| Passed / Failed | 11 / 0 |
| Executable | `dist/MD_Converter_Lite/MD_Converter_Lite.exe` (6,844,946 bytes) |
| Version | `1.1.0` (About dialog reported "Version 1.1.0") |
| SHA-256 | `261B10A704F834F37979C5BC66BAA4D83601C9F34D4743500308BE57D0EFCA90` |
| Console | console build → unwanted console window; final build windowed (`console=False`) |
| Direct GUI → Core | none |
| Conversion semantic change | none |
| Core change | none |
| Golden change | none |
| CLI/public API change | none |
| Scope deviation | none |
| Stop condition | none |

## Accepted build profile

* Bundler: PyInstaller 6.22.3, onedir `COLLECT`.
* Primary target: `MD_Converter_Lite.spec` (Playwright excluded).
* Launcher: `packaging/windows/launcher_main.py` → `md_converter.gui.app.main`.
* Output: `dist/MD_Converter_Lite/MD_Converter_Lite.exe` + `_internal/`.

## Packaging defects found and corrected (packaging-only)

### 1. Shadowed operating-system libraries (WinError 127 at startup)

`PyInstaller` resolves binary dependencies through `PATH` as well as through the
build environment. On a machine whose `PATH` contains portable tool runtimes,
operating-system DLLs were collected into `_internal`, where they are found
**before** `System32` (the application directory is searched first):

| Collected from PATH | Shadowed operating-system library | Verified failure |
|---|---|---|
| `ucrtbase.dll` 10.0.26100.4654 (libheif/jxrlib/poppler `bin`) | UCRT 10.0.26100.9444 | stale copy shipped in `_internal` |
| `api-ms-win-*.dll` stubs (43 files) | Windows API sets | `api-ms-win-core-synch-l1-2-0.dll` did not export `WaitOnAddress` |
| `icuuc.dll` 78.3 + `icudt78.dll` 33 MB (poppler `bin`) | Windows ICU 72.1 | missing unversioned `ucnv_open` / `ucnv_close` exports |

Result before the fix, on the first packaged launch of the accepted GUI entry
point:

```text
File "md_converter\gui\app.py", line 27, in <module>
ImportError: DLL load failed while importing QtCore: The specified procedure could not be found.
```

Both specs now filter those library families out of `a.binaries`, so the
product always uses the operating-system UCRT, API sets and ICU - which the
supported baseline (Windows 10+) provides. Payload shrank from 195.1 MB to
158.6 MB as a side effect.

### 2. Console window for a GUI product

| | Console build (before) | Windowed build (after) |
|---|---|---|
| Visible windows of the process | GUI window + console (`PseudoConsoleWindow`) | GUI window only |
| `stdout` / `stderr` | attached console; tracebacks and Core `print()` output visible | no console streams; redirection captured 0 bytes |
| Core `print()` diagnostics | written to the console | no-op (`print()` with `sys.stdout = None` returns silently) |
| Product character | console window beside the desktop GUI | accepted desktop GUI application |

Both specs now build `console=False`. The Core print-path behaviour itself is
unchanged (no Core edit); WP-P12-08-05 owns the decisive cp1252 verification.

## Focused verification

`tools/packaging/windows_gui_smoke.ps1` launches the **packaged** executable and
drives the real product path with UI Automation plus native window messages
(Qt widgets do not honour the UIA `Invoke` pattern here, and UI Automation does
not list owned Qt dialogs under the desktop root):

```text
launch -> main window -> Settings -> About -> Select File
       -> Convert -> DOCX artifact -> clean close
```

| # | Check | Result |
|---|---|---|
| 1 | `gui-startup` — main window "MD Converter" visible | PASS |
| 2 | `settings-opens` — Settings dialog opens (10 elements) | PASS |
| 3 | `settings-closes` | PASS |
| 4 | `about-opens` | PASS |
| 5 | `about-version` — "Version 1.1.0" matches the authoritative version | PASS |
| 6 | `about-closes` | PASS |
| 7 | `select-file` — native file dialog accepts the Markdown file | PASS |
| 8 | `convert-enabled` — Convert enabled for the selected file | PASS |
| 9 | `conversion` — SUCCESS, 4.8 s, Open Document/Open Folder actionable | PASS |
| 10 | `docx-artifact` + `docx-valid` — real DOCX written, contains `word/document.xml` | PASS |
| 11 | `clean-close` — process exits on window close | PASS |

Conversion path exercised by the packaged product:

```text
GUI -> GuiWorker -> ConversionService -> Canonical Core -> DOCX
```

## Notes for later work packages

* Conversion duration is dominated by the optional Word COM TOC refresh and
  varied between ~5 s and >4 min depending on Microsoft Word availability on
  this machine; the harness default conversion timeout is 900 s.
* A plain successful conversion exposes no report button, so `Details...` is
  only applicable to warning/failure outcomes.
