# WP-R2V03-01 - Native Word Openability & Acceptance Set

**Program:** R2-V03 - Native Word / Visual Verification (P12-21)
**Work package:** R2V03-01
**Change classification:** G2_OR_RELEASE - native-application release gate (no product change)
**Governing SPEC:** `CANONICAL_SPEC.md` (FROZEN 1.1) - `SPEC-QA-002`,
`SPEC-QA-005`, `SPEC-INV-001`, `SPEC-INV-002`, `SPEC-INV-014`, `SPEC-FUNC-023`,
`SPEC-GOAL-006`
**Raw records:** `R2_V03_ENVIRONMENT.json`,
`WP-R2V03-01_ACCEPTANCE_SET_INDEX.json`,
`WP-R2V03-01_WORD_LAYOUT_MEASUREMENTS.json`
**Status:** PASS

## 1. Scope

Confirm the exact R2-V02 packaged runtime identity, record the native Word
environment once, assemble the native-word acceptance set, and prove every
member opens and renders in desktop Microsoft Word without repair/recovery
behaviour. Detailed visual scoring belongs to WP-R2V03-02.

## 2. Accepted runtime identity (inherited, not rebuilt)

| Item | Value |
|---|---|
| Installed executable | `%LOCALAPPDATA%\Programs\MD_Converter\MD_Converter.exe` |
| SHA-256 (installed) | `68524527CDC5718CE31A1F0454EAFB0FF64C52D5C838716AC1277445DE0E3021` |
| SHA-256 (built payload `dist\MD_Converter_Lite\MD_Converter_Lite.exe`) | identical |
| Version metadata | FileVersion / ProductVersion `1.1.0`, ProductName `MD Converter` |
| R2-V02 accepted identity | `68524527...E3021` (R2_V02_CLOSURE_EVIDENCE section 1) |

The installed runtime is byte-identical to the artifact accepted by R2-V02. No
package was rebuilt and no product source file was touched by this work package.

## 3. Native environment record

| Item | Value |
|---|---|
| Word | desktop `WINWORD.EXE`, version `16.0.20430.20092`, Office Click-to-Run x64, `VersionToReport 16.0.20430.20092` |
| Windows | Windows 10 Home `25H2`, build `26200.9457`, AMD64 |
| Display | single `1280x720` primary display; no explicit DPI override in `HKCU\Control Panel\Desktop` (`LogPixels` absent) |
| View convention | Print Layout (`View.Type = 3`), zoom `100%`, window maximised; standardised once for every artifact |
| `.docx` association | `HKCR\.docx` -> `Word.Document.12` -> `"C:\Program Files\Microsoft Office\Root\Office16\WINWORD.EXE" /n "%1" /o "%u"` |

Rendered documents carry Word's `[Compatibility Mode]` window-title suffix
because the accepted DOCX declares `w:compatSetting compatibilityMode = 14`
(Word 2010). The same condition was already recorded and accepted in P12-06,
P12-08, P12-09 and P12-10; it is classified `KNOWN_ACCEPTED_LIMITATION` and does
not affect readability, content integrity, navigation or usability.

## 4. Acceptance set

The set reuses the accepted R2-V02 packaged outputs; only the Program D
irreducible-table fixture is added, because the product specification asks for
that case "if a fixture is available". Full structural index (margins, TOC
field, entries, table grids, figure sizes) is in
`WP-R2V03-01_ACCEPTANCE_SET_INDEX.json`.

| Role | Artifact | Bytes | SHA-256 (head) | Word pages |
|---|---|---|---|---|
| profile:professional_report | `Matrix_Professional_Report.docx` | 32 407 | `5F50F483...61AE7E` | 5 |
| profile:business_report | `Matrix_Business_Report.docx` | 33 008 | `8C8FF306...A557D7` | 5 |
| profile:academic | `Matrix_Academic.docx` | 32 400 | `F7CA44E8...931EAC1` | 5 |
| profile:technical | `Matrix_Technical.docx` | 33 007 | `4D95AC76...494E456C` | 5 |
| profile:clean_minimal | `Matrix_Clean_Minimal.docx` | 33 003 | `E112BD25...D86EB8DA` | 5 |
| toc:chinese_mixed | `竞争基础集成验证.docx` | 31 211 | `2EC1D03D...2FB564351` | 3 |
| batch:english_single | `01_english.docx` | 29 442 | `8E19BA0A...6EA7D7E0` | 3 |
| batch:wide_table_figure | `Wide_Table_Report.docx` | 31 433 | `D45FC667...B9053BDB` | 3 |
| batch:after_failure | `04_after_failure.docx` | 29 352 | `366331D8...CEE7EB54C` | 3 |
| table:irreducible_wide_program_d | `irreducible_table.docx` | 37 370 | `A49EB6FE...B94FF1A1B` | 3 |

Sources: `%TEMP%\mdc_r2v02_wp03_20260930_171108\collected` (five profiles and
the localized TOC control) and `%TEMP%\mdc_r2v02_wp02_20260930_155602\collected`
(the serial-batch outputs), plus
`Doc/V2/Implementation/Program_D_Advanced_Table_Figure_Fitting/Evidence/samples/irreducible_table.docx`.
The set was copied into one neutral work directory
(`%TEMP%\mdc_r2v03_wp01_20260930_201727\acceptance_set`) so that all inspection
targets share one location.

## 5. Openability result

Every artifact was opened through Word's normal document-open path, set to the
standard view, and measured (10 of 10):

| Check | Result |
|---|---|
| opens in desktop Word without an error or recovery event | PASS - 10 of 10 |
| repair/recovery prompt displayed | none observed |
| renders in Print Layout at 100% zoom | PASS - `View.Type = 3`, `Zoom = 100` for all 10 |
| Word-visible structure present (pages, tables, figures, TOC links) | PASS - matches the acceptance-set index per artifact |
| `.docx` association path resolves to desktop Word | PASS - `Word.Document.12` -> `WINWORD.EXE` |
| artifact modified by Word | No - all 10 SHA-256 values identical before and after open/measure/export/close (0 mismatches) |

Word-reported page counts: five-profile documents 5 pages each
(cover / TOC / content / page-capped figure / notes); localized TOC control and
the three batch outputs 3 pages each; the Program D irreducible fixture 3 pages.

## 6. New failures / classification

Introduced failures in this work package: **0**. No
`VISUAL_PRODUCT_DEFECT`, no `ENVIRONMENT_FAILURE`.

Observations (classified, not repaired, no product change):

* `[Compatibility Mode]` window-title indicator -
  `KNOWN_ACCEPTED_LIMITATION` (see section 3).

## 7. Protected drift result

| Protected contract | Result |
|---|---|
| Product source modified | No (0 files under `md_converter/` changed) |
| Accepted R2-V02 runtime identity | Preserved (identical executable SHA-256) |
| R2-V02 packaged outputs | Reused unchanged; byte-identical after Word inspection |
| Product settings / Word settings | Not modified |
| Pre-existing dirty worktree state | Preserved, never staged |
| Drift | 0 |

## 8. Reproducible tooling

| Tool | Purpose |
|---|---|
| `Verification/r2v03_env_record.ps1` | records packaged identity, Word/Windows/display environment |
| `Verification/r2v03_acceptance_set.py` | assembles the acceptance set and writes the structural index |
| `Verification/r2v03_word_probe.py` | native Word COM measurement, print-layout standardisation, native PDF export |

## 9. Commit

Commit message: `R2V03-01 establish native Word visual acceptance set`
(exact-file staging: this evidence file, the environment record, the acceptance
set index, the Word layout measurements, and the three verification tools).

## 10. Status

PASS - the exact R2-V02 packaged runtime and its accepted outputs open in
desktop Microsoft Word without repair/recovery behaviour, render in Print
Layout, and are provably unmodified by the inspection.
