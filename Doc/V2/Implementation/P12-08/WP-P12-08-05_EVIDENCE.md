# WP-P12-08-05 — Packaged Runtime Verification — Completion Evidence

**Product Baseline SHA:** `1b040c5d0d19f16be127cf3060fb573005a69c81`
**Specification Baseline SHA:** `f6a12779303816ad4f9f1cfebce700cbc8f76ace`
**Input commit:** `1602b2d` (WP-P12-08-04 package metadata notices and resources)
**Authority:** G1 verification; bounded packaging/runtime corrections allowed

## Report record

| Field | Value |
|---|---|
| WP | WP-P12-08-05 — Packaged Runtime Verification |
| Status | PASS |
| Input baseline SHA | `1602b2d` |
| Output commit SHA | recorded by the committing run (`P12-08-05 verify packaged Windows runtime`) |
| Files added | `tools/packaging/gui_automation.ps1`, `tools/packaging/windows_runtime_matrix.ps1`, this evidence file |
| Files modified | none (no packaging/config correction was required) |
| Verified product | installed `%LOCALAPPDATA%\Programs\MD_Converter\MD_Converter.exe` (version 1.1.0) |
| Tests/checks | runtime matrix 16 checks + cp1252 evidence set |
| Passed / Failed | 16 / 0 |
| cp1252 | CASE A — not reproducible in the packaged GUI (evidence below) |
| Open Document actual Word open | PASS (Word document window + exclusive file lock) |
| Open Folder | PASS (new Explorer window for the artifact folder) |
| Install / Uninstall | PASS (WP-P12-08-03) |
| Direct GUI → Core | none |
| Conversion semantic change | none |
| Core change | none |
| Golden change | none |
| CLI/public API change | none |
| Scope deviation | none |
| Stop condition | none |

## How the runtime was driven

New verification tooling (packaging helpers only, no product change):

* `tools/packaging/gui_automation.ps1` — shared primitives: Win32 window
  discovery (UI Automation does not list owned Qt dialogs under the desktop
  root), message-based user actions (Qt widgets ignore the UIA
  `InvokePattern` here), native file-dialog input, artifact validation.
* `tools/packaging/windows_runtime_matrix.ps1` — the A/C/D/E/F/G/H matrix.

The product was exercised only through real user actions; the conversion path
under test is `GUI → GuiWorker → ConversionService → Canonical Core → DOCX`.

## Matrix results

| # | Check | Evidence |
|---|---|---|
| A1 | `startup` | window "MD Converter" visible |
| A2 | `worker-active-close-protection` | window close during an active conversion did **not** terminate the application |
| A3 | `close-protection-conversion-completes` | that conversion then completed: SUCCESS |
| A4 | `clean-close` | application exits when closed while idle |
| C1 | `preference-written-on-conversion` | `HKCU\...\folders\last_source_directory` = `…\MDC smoke ü 测试 205320` |
| C2 | `settings-saved` | Settings dialog "Remember the last folders I used" = On, saved |
| C3 | `settings-persist-across-restart` | after closing and restarting the app the setting still reads On |
| C4 | `remembered-folders-restored` | restarted app showed `C:\Users\Quansheng\AppData\Local\Temp\mdc_runtime\MDC smoke ü 测试 205320` |
| D1 | `open-document-word-opens` | Word document window `Runtime_Matrix_205320 [Compatibility Mode] - Word` |
| D2 | `open-document-word-reads-file` | the artifact was exclusively held open while Word displayed it |
| D3 | `artifact-persists-after-open` | artifact present before and after opening |
| D4 | `word-document-closed-lock-released` | closing that Word window released the file lock |
| E1 | `open-folder` | new Explorer window `output - File Explorer` for the artifact folder |
| F1 | `missing-artifact-fails-closed` | dialog `File not available - MD Converter`; no Word window; artifact **not** recreated; app still running; no retry conversion |
| G1 | `conversion-non-ascii-path` | SUCCESS in 4.9 s for `…\MDC smoke ü 测试 205320\runtime smoke ü 205320.md` |
| H1 | `high-dpi-controls-in-bounds` | at the machine's real scaling (900×600 logical → 1350×900 physical = 150%) every button lies inside the window rectangle |

Evidence record: `%TEMP%\mdc_runtime_evidence.json` (status PASS, 0 failing checks).

## cp1252 / console encoding — decisive verification (CASE A)

The known risk: `DocxPostProcessor` prints emoji diagnostics
(`📄 TOC 已插入…`, `⚠️ …`) which raise `UnicodeEncodeError` on a cp1252
console.

1. **The risk is real in the Core print path** —
   `md_converter/renderer/post_processor.py` lines 94, 115, 125, 260, 611, 625,
   636, 714 print such characters, and writing one of them to a cp1252 stream
   raises:
   `UnicodeEncodeError: character maps to <undefined>`.
2. **The packaged product has no cp1252 console stream.** The windowed build
   (`console=False`, WP-P12-08-02) starts without a console window, and
   launching the installed executable with redirected handles captured
   **0 bytes** on both stdout and stderr.
3. **`print()` cannot raise there.** With `sys.stdout = None` — what a windowed
   packaged process has — `print()` returns silently; verified directly in the
   interpreter used to build the payload.
4. **The emoji-printing code path really executes in the packaged conversion.**
   A packaged conversion reached SUCCESS in 4.9 s and its artifact contains the
   native TOC field (`TOC \o`), which is produced by exactly the
   post-processing block that performs those prints.
5. **No developer workaround was used.** `PYTHONIOENCODING` was empty for every
   verification run (`python_io_encoding_env: ""` in the evidence record); no
   environment variable was set to hide the issue.

Result: **CASE A — the packaged GUI does not reproduce the failure**, because
the accepted windowed packaging removes the problematic console stream
entirely. No Core/Application semantic change was needed and none was made.

## Observed behaviour recorded (not changed)

* Word COM post-processing (`DocxPostProcessor`) starts a WINWORD
  `/Automation -Embedding` process during conversion; conversion time varied
  between ~5 s and >4 min depending on Microsoft Word availability on this
  machine.
* The "Open Document" action hands the file to the user's existing Word
  instance: the document loads in Word's own document window, which stays hidden
  while another document is the active window — hence the runtime matrix matches
  hidden `OpusApp` windows by document title.
* `DEFAULT_REMEMBER_FOLDERS` is `True`, so "Remember the last folders I used" is
  enabled unless the user turns it off.
* Verification restored the product's own settings (`folders\last_source_directory`,
  `folders\remember`, window geometry) to their pre-verification values and
  closed the Word document window / Explorer window it opened.

## Conclusion

Every WP-P12-08-05 required outcome passes on the real packaged product:
startup, clean close, worker-active close protection, real conversion through
the accepted application path, settings persistence, Open Document with
Microsoft Word actually reading the file, Open Folder, fail-closed handling of
a missing artifact, path robustness (spaces + non-ASCII), high-DPI smoke, and
cp1252 CASE A.
