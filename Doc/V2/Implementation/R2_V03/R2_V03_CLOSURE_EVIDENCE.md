# R2-V03 - Native Word / Visual Verification
## Closure Evidence

**Program:** R2-V03 (P12-21) - native Word / visual release gate
**Change classification:** G2_OR_RELEASE - native-application release
verification (no product change)
**Governing SPEC:** `CANONICAL_SPEC.md` (FROZEN 1.1) - `SPEC-QA-002`,
`SPEC-QA-005`, `SPEC-INV-001`, `SPEC-INV-002`, `SPEC-INV-014`, `SPEC-FUNC-023`,
`SPEC-AC-003`, `SPEC-GOAL-006`
**Upstream gate:** R2-V02 - CLOSED / ACCEPTED / PACKAGED RUNTIME RELEASE-GATE PASS
**Final status:** `R2-V03 — CLOSED / ACCEPTED / NATIVE WORD VISUAL RELEASE-GATE PASS`

## 1. Accepted packaged runtime identity (inherited from R2-V02, not rebuilt)

| Item | Value |
|---|---|
| Installed executable | `%LOCALAPPDATA%\Programs\MD_Converter\MD_Converter.exe` |
| SHA-256 | `68524527CDC5718CE31A1F0454EAFB0FF64C52D5C838716AC1277445DE0E3021` |
| Built payload | `dist\MD_Converter_Lite\MD_Converter_Lite.exe`, identical SHA-256 |
| Version metadata | FileVersion / ProductVersion `1.1.0`, ProductName `MD Converter` |
| R2-V02 accepted identity | `68524527...E3021` (R2_V02_CLOSURE_EVIDENCE section 1) |

The exact artifact accepted by R2-V02 was used. No package was rebuilt and no
product source file was modified by any R2-V03 work package.

## 2. Native Word environment

| Item | Value |
|---|---|
| Word | desktop `WINWORD.EXE` `16.0.20430.20092` (Office Click-to-Run x64, `VersionToReport 16.0.20430.20092`) |
| Windows | Windows 10 Home `25H2`, build `26200.9457`, AMD64 |
| Display | single `1280x720` primary display, no explicit DPI override |
| View convention | Print Layout (`View.Type = 3`), zoom `100%`, window maximised - fixed once and reused |
| Document association | `HKCR\.docx` -> `Word.Document.12` -> `WINWORD.EXE /n "%1" /o "%u"` |
| Word exit/relaunch | fully exited (0 `WINWORD` processes) and relaunched for the WP-03 restart smoke |

## 3. Three-commit chain

| # | Commit | Message |
|---|---|---|
| 1 | `9617646` | `R2V03-01 establish native Word visual acceptance set` |
| 2 | `a71e0e0` | `R2V03-02 verify native Word visual acceptance` |
| 3 | (this commit) | `R2V03-03 close native Word visual verification` |

Each work package verified independently, classified independently, recorded its
own evidence, staged exact files only, and produced one truthful commit. No
combined or retrospective commit exists. The pre-existing dirty worktree state
(`.gitignore`, `README.md`, `md_converter/cli.py` and the unrelated untracked
directories) was preserved and never staged, and no file under `md_converter/`
was touched.

## 4. Evidence index

| WP | Evidence |
|---|---|
| R2V03-01 | `Evidence/WP-R2V03-01_NATIVE_WORD_OPENABILITY_EVIDENCE.md`, `Evidence/R2_V03_ENVIRONMENT.json`, `Evidence/WP-R2V03-01_ACCEPTANCE_SET_INDEX.json`, `Evidence/WP-R2V03-01_WORD_LAYOUT_MEASUREMENTS.json` |
| R2V03-02 | `Evidence/WP-R2V03-02_NATIVE_VISUAL_ACCEPTANCE_EVIDENCE.md`, `Evidence/WP-R2V03-02_VISUAL_ACCEPTANCE_MATRIX.json`, `Evidence/WP-R2V03-02_NATIVE_RENDER_MATRIX.json`, `Evidence/WP-R2V03-02_PAGE_PIXEL_MATRIX.json`, `Evidence/Screenshots/wp02_*.png` |
| R2V03-03 | `Evidence/WP-R2V03-03_WORD_RESTART_COMPARISON.json`, `Evidence/WP-R2V03-03_NATIVE_RENDER_MATRIX_AFTER_RESTART.json`, `Evidence/WP-R2V03-03_PAGE_PIXEL_MATRIX_AFTER_RESTART.json`, `Evidence/Screenshots/wp03_*.png`, this closure |

Reproducible verification tooling (verification only, never imported by the
product): `Verification/r2v03_env_record.ps1`,
`Verification/r2v03_acceptance_set.py`, `Verification/r2v03_word_probe.py`,
`Verification/r2v03_pdf_render_check.py`,
`Verification/r2v03_page_image_check.py`,
`Verification/r2v03_visual_matrix.py`,
`Verification/r2v03_restart_compare.py`.

## 5. Acceptance set

Ten native-Word targets: the five profile documents and the localized TOC
control produced by the accepted package in WP-R2V02-03, the three serial-batch
outputs produced in WP-R2V02-02, and the Program D irreducible-table fixture.
Full structural index (margins, TOC field and cached entries, table grids,
figure sizes) in `Evidence/WP-R2V03-01_ACCEPTANCE_SET_INDEX.json`.

All ten artifacts were byte-identical before and after the gate
(`sha256` compared at four points, including after the Word restart): Word never
modified an accepted artifact.

## 6. Five-profile native visual matrix

Each row was measured from Word's own layout and compared with the product's
frozen profile authority (`md_converter/profiles/registry.py`). 27 of 27 checks
pass per profile.

| Profile | Margins T/B/L/R (cm) | Body font / size | Spacing / after | H1 | Table style / font | Wide table | Checks |
|---|---|---|---|---|---|---|---|
| professional_report | 2.54 / 2.54 / 2.54 / 2.54 | Calibri 10.5 pt | 1.15 / 6 pt | Arial 20 pt | Table Grid / 9.5 pt | 15.921 cm | 27/27 |
| business_report | 2.0 / 2.0 / 2.0 / 2.0 | Calibri 10.0 pt | 1.08 / 4 pt | Calibri 16 pt | Light Grid / 9.0 pt | 17.0004 cm | 27/27 |
| academic | 2.54 / 2.54 / 3.0 / 3.0 | Times New Roman 11.5 pt | 1.5 / 0 pt | Times New Roman 16 pt | Table Grid / 9.0 pt | 15.0002 cm | 27/27 |
| technical | 2.2 / 2.2 / 2.2 / 2.2 | Calibri 10.5 pt | 1.2 / 6 pt | Arial 18 pt | Light Grid Accent 1 / 9.0 pt | 16.6018 cm | 27/27 |
| clean_minimal | 2.54 / 2.54 / 2.54 / 2.54 | Calibri 10.5 pt | 1.25 / 8 pt | Calibri 15 pt | Light Grid / 9.5 pt | 15.921 cm | 27/27 |

Heading hierarchy, cover page, TOC page, content page, page-capped figure page
and notes page compose consistently in every profile.

## 7. TOC, table, figure and batch results

| Area | Result |
|---|---|
| TOC (English) | PASS - `Table of Contents`, 6/6 cached entries rendered, one live `TOC \o "1-3" \h \z \u` field, `UseHyperlinks = True`, page numbers present |
| TOC (Chinese/mixed) | PASS - `目录`, 4/4 entries rendered, same field, hyperlinks present |
| Normal 3-column table | PASS - content complete, inside the body in every profile |
| Wide fitted 8-column table | PASS - total equals the profile content width, right edge inside the body (18.4469 cm vs 18.461 cm in professional_report), all header labels and cells rendered |
| Irreducible 25-column table | `KNOWN_ACCEPTED_LIMITATION` - see section 8 |
| Figures 4:1 (all profiles, TOC, batch) | PASS - rendered 12.677 x 3.187 cm, ratio 3.9777-3.9492 vs 4.0, solid fill 1.0 |
| Figures 1:10 page-capped (all profiles) | PASS - rendered 2.448-2.563 x 24.615-25.723 cm, ratio 0.0995 vs 0.1, solid fill 1.0, contained in the text body (`SPEC-INV-014`) |
| Batch outputs | PASS - `01_english.docx`, `Wide_Table_Report.docx`, `04_after_failure.docx` each open and render coherently; the failed item produced no document |
| Content integrity | PASS - 0 dropped characters across all nine packaged artifacts (`SPEC-INV-001`, `SPEC-AC-003`) |

Measured checks overall: **187** (183 `PASS`, 4
`KNOWN_ACCEPTED_LIMITATION`, 0 `VISUAL_PRODUCT_DEFECT`, 0
`ENVIRONMENT_FAILURE`).

## 8. Accepted limitations

| # | Limitation | Status |
|---|---|---|
| L1 | Word shows `[Compatibility Mode]` because the accepted DOCX declares `compatibilityMode = 14` | already recorded in P12-06/08/09/10; user-visible only in the title bar, no usability impact |
| L2 | The 25-column Program D fixture is 29.9994 cm wide in a 29.7 cm landscape page, so the trailing columns (`H23`, `H24`) cannot be printed on one page | accepted by Program D (`RENDER006`, PASS_WITH_WARN); no packaged R2-V02 output exhibits it |
| L3 | The Program D fixture's trailing empty section renders an empty page | characteristic of that verification fixture, not a packaged output |
| L4 | The normal 3-column table's first column is 1.7092 cm in every profile, so header/cell words such as `Component` and `WordRenderer` wrap across two lines | `LATER_GATE_DEBT`: content is complete and legible; a column-allocation refinement belongs to a later gate and is not a release blocker |

L2-L4 were kept visible in the evidence and were not silently repaired, because
R2-V03 does not authorise product-source changes.

## 9. Word restart / reopen result

All verification documents were closed, Word was fully exited (0 `WINWORD`
processes), relaunched, and three documents were reopened: one profile document
(`Matrix_Professional_Report.docx`), one TOC document
(`竞争基础集成验证.docx`) and one integrated table/figure document
(`Wide_Table_Report.docx`).

| Check | Result |
|---|---|
| no repair/recovery prompt on reopen | PASS |
| pagination unchanged | PASS - 5 / 3 / 3 pages before and after |
| page setup, table geometry, figure sizes unchanged | PASS - 0 material differences |
| TOC remains present, hyperlinked and complete | PASS - 0 material differences |
| rendered content and figure blocks unchanged | PASS - 0 material differences |
| artifacts modified by the restart cycle | No - 0 SHA-256 mismatches |

The only differences recorded anywhere in the comparison are two Word-generated
TOC dot-leader characters in one document (1410 -> 1408 rendered characters,
0 content characters dropped in both runs). They are reported explicitly as
non-material in `WP-R2V03-03_WORD_RESTART_COMPARISON.json`.

## 10. Evidence-channel note

The interactive screen-capture channel (Computer Use) was stopped by the user
during the gate, so no Word window screenshot was taken. Word's own
print-layout renderer was used instead: every page was exported to PDF by
`Document.ExportAsFixedFormat`, rasterised, and measured pixel by pixel. This is
the "equivalent native-Word evidence" the R2-V03 product specification allows,
and it is stronger than a window grab because page geometry is measurable. No
human/aesthetic image review was performed; every decision rests on measurements
of Word's own rendering output, and pure preference judgements are explicitly
out of scope.

## 11. Defect and blocker count

| Metric | Value |
|---|---|
| introduced native visual defects | **0** |
| unresolved native visual blockers | **0** |
| product source files changed | 0 |
| accepted artifacts changed | 0 |

## 12. Remaining debt

* **R2-V04 = PENDING** (not started; R2-V03 does not open the next gate).
* **Installer-wrapper rebuild = release-engineering debt before RC.** The frozen
  Inno Setup script still cannot be compiled on this machine (no `ISCC.exe`), so
  the installed layout was materialised by reproducing the script's own mapping
  (recorded in `WP-R2V02-01`). This remains outstanding before a release
  candidate.
* **L4** (narrow first column of the normal 3-column table) is carried as
  `LATER_GATE_DEBT`.

## 13. Final recommendation

Accept R2-V03. The exact packaged runtime accepted by R2-V02 produces DOCX
documents that open and render natively in desktop Microsoft Word with the
frozen profile distinctions intact, complete and unclipped tables, complete and
undistorted figures inside the usable page body, working English and
Chinese/mixed tables of contents, and independently usable batch outputs. The
result is repeatable across a full Word restart. Zero introduced visual defects
and zero unresolved blockers remain. Proceed to plan R2-V04 separately, carrying
the installer-wrapper rebuild as release-engineering debt.

`R2-V03 — CLOSED / ACCEPTED / NATIVE WORD VISUAL RELEASE-GATE PASS`
