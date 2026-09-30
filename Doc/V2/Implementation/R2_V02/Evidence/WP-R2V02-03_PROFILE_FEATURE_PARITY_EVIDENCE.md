# WP-R2V02-03 — Profile & Feature Parity

**Program:** R2-V02 — Packaged Multi-file Runtime Verification (P12-20)
**Work package:** R2V02-03
**Change classification:** G1 — verification only (no product source change)
**Governing SPEC:** `CANONICAL_SPEC.md` (FROZEN 1.1) — `SPEC-FUNC-011`,
`SPEC-FUNC-023`, `SPEC-GOAL-003`, `SPEC-INV-003`, `SPEC-INV-005`
**Raw records:** `WP-R2V02-03_RESULT.json`,
`WP-R2V02-03_PARITY_REPORT.json` (86 measured parity checks)
**Status:** PASS

## 1. Scope

Convert one integrated representative document through the installed packaged
GUI under all five output profiles, plus one localized-TOC control document,
then measure the produced DOCX and compare the semantic measurements with the
frozen R2-V01 evidence. Content exercises the TOC, normal and wide tables,
figure fitting and the `image_width` target/cap rule.

## 2. Artifact / files

| Item | Value |
|---|---|
| Installed executable | `%LOCALAPPDATA%\Programs\MD_Converter\MD_Converter.exe` (SHA-256 `68524527…E3021`) |
| Launch mode | detached windowed GUI launch (no inherited standard handles) + sanitized environment |
| Neutral runtime cwd | `%TEMP%\mdc_r2v02_wp03_20260930_171108\cwd` |
| Integrated document | frontmatter title + `#`/`##`/`###` headings, 3-column table, 8-column table, 400x100 px figure (4:1), 20x200 px figure (1:10) |
| Profile runs | `professional_report`, `business_report`, `academic`, `technical`, `clean_minimal` (one document per profile) |
| TOC control run | Chinese document under `professional_report` (localized heading) |
| Produced documents | `Matrix_Professional_Report.docx`, `Matrix_Business_Report.docx`, `Matrix_Academic.docx`, `Matrix_Technical.docx`, `Matrix_Clean_Minimal.docx`, `竞争基础集成验证.docx` |
| Measurement tooling | `Verification/verify_packaged_parity.py` (imports the accepted R2-V01 measurement module) |

The profile selector was driven through the real packaged control (the combo
popup) and each selection was read back before conversion.

## 3. Verification result

All six packaged conversions reported `SUCCESS` (3.3 s – 4.0 s each), each
after a verified single-file selection state, and each produced exactly the
expected document name.

Measured profile geometry (last section of the produced DOCX):

| Profile | artifact margins (L,R,T,B cm) | content box (cm) | wide table total / min column (cm) | 4:1 figure (cm) | 1:10 figure (cm) |
|---|---|---|---|---|---|
| professional_report | 2.54, 2.54, 2.54, 2.54 | 15.921 × 24.62 | 15.921 / 1.7974 | 12.70 × 3.175 (r = 4.0) | 2.462 × 24.6204 (r = 0.1) |
| business_report | 2.0, 2.0, 2.0, 2.0 | 17.001 × 25.7 | 17.0004 / 1.9209 | 12.70 × 3.175 (r = 4.0) | 2.57 × 25.6999 (r = 0.1) |
| academic | 3.0, 3.0, 2.54, 2.54 | 15.001 × 24.62 | 15.0002 / 1.6951 | 12.70 × 3.175 (r = 4.0) | 2.462 × 24.6204 (r = 0.1) |
| technical | 2.2, 2.2, 2.2, 2.2 | 16.601 × 25.3 | 16.6018 / 1.875 | 12.70 × 3.175 (r = 4.0) | 2.5301 × 25.3012 (r = 0.1) |
| clean_minimal | 2.54, 2.54, 2.54, 2.54 | 15.921 × 24.62 | 15.921 / 1.7974 | 12.70 × 3.175 (r = 4.0) | 2.462 × 24.6204 (r = 0.1) |

Parity checks (86 measured checks, 0 failed):

| Capability | Result |
|---|---|
| profile / effective layout | PASS — every profile matches the frozen R2-V01 geometry and content box |
| TOC heading (English) | PASS — `Table of Contents`, canonical `TOC \o "1-3" \h \z \u` field present in all five profiles |
| TOC heading (localized control) | PASS — `目录` with the same canonical field |
| TOC cached entries | PASS — `Competitive Foundation Report · Architecture · Financial Overview · Projected Growth · Page Capped Figure · Notes` cached in every artifact |
| table fitting | PASS — 8 explicit columns, fixed layout, total ≤ profile content width, column floor ≥ 1.2 cm − twips, no cell mutation |
| figure fitting | PASS — aspect ratio preserved (4:1 and 1:10), figures inside the content box |
| `image_width` target/cap | PASS — delivered width 12.70 cm = `min(5 in default, content width)` in every profile; page-height cap exercised on the 1:10 figure (height == profile content height) |
| document creation | PASS — six documents created by the installed packaged application |

## 4. New failures / classification

No packaged failure. Introduced packaged failures in this work package: **0**.
No `PACKAGED_PRODUCT_REGRESSION` and no `PACKAGING_BUILD_OR_INSTALL_DEFECT`.

Observations (classified, not repaired, no product change):

* The packaged desktop surface exposes no `image_width` control, so the runtime
  target is the frozen configuration default (5 in → 12.70 cm); the explicit
  override and the content-width cap were verified at source level in R2-V01,
  and the same single sizing authority ships in the package
  (`md_converter.renderer.layout.figure_sizing`, verified present in the
  packaged archive). The profile content width cap is therefore not triggered by
  the default target in any profile; the page-height cap is exercised.
* UI Automation's `SelectionItemPattern.Select()` on this Qt combo's popup items
  is accepted but does not change the selection; the harness drives the selector
  with a real mouse click delivered to the combo popup's own window and always
  reads the produced value back.
* Word is present on this machine, so the packaged product refreshes the inserted
  TOC through Word. Word rewrites the cached entries as hyperlinked runs, which
  `python-docx`'s `Paragraph.text` does not expose; the measurement reads the
  entry text from `word/document.xml` (identical content in both forms).

Bounded harness corrections applied while establishing these observations: the
profile selector method above, single-file selection-state verification (the
frozen GUI shows its batch surface only for two or more files), TOC entry
measurement from the document XML, BOM-tolerant parity input, and native-stderr
tolerance in the Python step runner. The run recorded above is the clean re-run
after those corrections.

## 5. Protected drift result

| Protected invariant | Result |
|---|---|
| Product source modified | No (0 files under `md_converter/` changed) |
| Five output profiles | Preserved (all five applied and measured) |
| TOC localization authority | Preserved (English + localized headings from one authority) |
| `plan_table_fit` / `plan_figure_fit` behaviour | Preserved (single authorities; measured widths match) |
| `SPEC-FUNC-023` share of effective width | Preserved (12.70 cm target, height cap honoured) |
| Output naming / path | Unchanged (`<sanitized title|stem>.docx`) |
| Drift | 0 |

## 6. Commit

Commit message: `R2V02-03 verify packaged profile and feature parity`
(exact-file staging: this evidence file, the raw result JSON, the bundled parity
report, and the corrected measurement/harness scripts). The four-commit chain is
listed with SHAs in `R2_V02_CLOSURE_EVIDENCE.md`.

## 7. Status

PASS — all five profiles plus a localized TOC control convert correctly in the
installed packaged application, and TOC, table fitting, figure fitting and the
`image_width` target/cap semantics match the accepted R2-V01 baseline
semantically (86/86 measured checks).
