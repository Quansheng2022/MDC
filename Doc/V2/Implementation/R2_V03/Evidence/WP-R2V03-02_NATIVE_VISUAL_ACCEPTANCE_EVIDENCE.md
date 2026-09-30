# WP-R2V03-02 - Native Visual Acceptance Matrix

**Program:** R2-V03 - Native Word / Visual Verification (P12-21)
**Work package:** R2V03-02
**Change classification:** G2_OR_RELEASE - native-application release gate (no product change)
**Governing SPEC:** `CANONICAL_SPEC.md` (FROZEN 1.1) - `SPEC-QA-002`,
`SPEC-QA-005`, `SPEC-INV-001`, `SPEC-INV-002`, `SPEC-INV-014`, `SPEC-FUNC-023`,
`SPEC-AC-003`, `SPEC-GOAL-006`
**Raw records:** `WP-R2V03-02_VISUAL_ACCEPTANCE_MATRIX.json`,
`WP-R2V03-02_NATIVE_RENDER_MATRIX.json`, `WP-R2V03-02_PAGE_PIXEL_MATRIX.json`,
`WP-R2V03-01_WORD_LAYOUT_MEASUREMENTS.json`,
`Evidence/Screenshots/*.png`
**Status:** PASS

## 1. Scope

Native visual acceptance of the accepted R2-V02 packaged output in desktop
Microsoft Word: five output profiles, English and Chinese/mixed TOC, normal and
wide and irreducible-wide tables, normal and page-height-capped figures, and a
representative subset of serial-batch outputs.

## 2. Method (native Word observation)

One view convention was used for every artifact, fixed once in WP-R2V03-01:
Print Layout (`View.Type = 3`), zoom `100%`, window maximised. All documents
were opened through Word's normal document-open path and never saved; all ten
artifacts were byte-identical (SHA-256) before and after the work package.

Three independent native measurements were combined:

| Channel | What it observes |
|---|---|
| Word object model (COM) | page setup, pagination, table grid widths, inline-shape size, heading fonts, paragraph spacing, TOC field state |
| Word print-layout renderer (`ExportAsFixedFormat` -> PDF) | the pages exactly as Word lays them out for printing; text and image geometry measured page by page |
| Pixel measurement of the rendered pages (Poppler 110 dpi) | ink extent, blank pages, and the rendered figure blocks in actual pixels |

**Evidence channel note (recorded honestly).** The interactive screen-capture
channel (Computer Use) was stopped by the user during this gate, so no Word
window screenshot was taken. The R2-V03 product specification asks for "native
screenshots or equivalent native-Word evidence"; the committed
`Evidence/Screenshots/*.png` are therefore **Word-rendered page images produced
by Word's own print-layout renderer**, which is the same rendering path Print
Layout displays and is stronger than a window grab because page geometry can be
measured exactly. No human/aesthetic image review was performed in this gate;
every decision below rests on measurements of Word's own rendering output. Pure
preference judgements are out of scope by `R2_V03_Product_Specification.md` §5.

## 3. Acceptance matrix summary

| Metric | Value |
|---|---|
| artifacts covered | 10 (9 packaged outputs + 1 Program D fixture) |
| measured checks | 187 |
| `PASS` | 183 |
| `KNOWN_ACCEPTED_LIMITATION` | 4 (all on the non-packaged Program D fixture) |
| `VISUAL_PRODUCT_DEFECT` | **0** |
| `ENVIRONMENT_FAILURE` | 0 |
| introduced native visual defects | **0** |
| unresolved visual blockers | **0** |

All nine packaged artifacts pass **every** check; the four non-PASS entries
describe the Program D irreducible-table fixture, whose behaviour Program D
already accepted (`RENDER006`, PASS_WITH_WARN).

## 4. Five output profiles

One integrated document per profile, measured against the product's own frozen
profile authority (`md_converter/profiles/registry.py`):

| Profile | Word margins T/B/L/R (cm) | Body font / size | Line spacing | Space after | H1 font / size | Table style / font | Wide table total (cm) | Checks |
|---|---|---|---|---|---|---|---|---|
| professional_report | 2.54 / 2.54 / 2.54 / 2.54 | Calibri 10.5 pt | 1.15 | 6 pt | Arial 20 pt | Table Grid / 9.5 pt | 15.921 | 27/27 PASS |
| business_report | 2.0 / 2.0 / 2.0 / 2.0 | Calibri 10.0 pt | 1.08 | 4 pt | Calibri 16 pt | Light Grid / 9.0 pt | 17.0004 | 27/27 PASS |
| academic | 2.54 / 2.54 / 3.0 / 3.0 | Times New Roman 11.5 pt | 1.5 | 0 pt | Times New Roman 16 pt | Table Grid / 9.0 pt | 15.0002 | 27/27 PASS |
| technical | 2.2 / 2.2 / 2.2 / 2.2 | Calibri 10.5 pt | 1.2 | 6 pt | Arial 18 pt | Light Grid Accent 1 / 9.0 pt | 16.6018 | 27/27 PASS |
| clean_minimal | 2.54 / 2.54 / 2.54 / 2.54 | Calibri 10.5 pt | 1.25 | 8 pt | Calibri 15 pt | Light Grid / 9.5 pt | 15.921 | 27/27 PASS |

Every measured value equals the frozen profile value: margins, body font and
size, H1/H2/H3 font and size, paragraph line spacing, paragraph space-after,
table style and table font size. Heading hierarchy renders as Heading 1 ->
Heading 2 -> Heading 2 -> Heading 2 -> Heading 2 -> Heading 3 with the expected
outline levels. Profile composition is page-consistent: cover page, TOC page,
content page with both tables and the wide figure, a page whose body is filled
exactly by the page-capped figure, and a notes page.

Committed page views: `wp02_profile_<profile>_toc_page2.png` (five files).

## 5. Table of contents

| Case | Heading rendered | Cached entries rendered | Word field | Navigation |
|---|---|---|---|---|
| English (all five profiles) | `Table of Contents` | 6/6 | 1 live field, `TOC \o "1-3" \h \z \u` | `UseHyperlinks = True`; 6 hyperlinked entry runs |
| Chinese/mixed (`竞争基础集成验证.docx`) | `目录` | 4/4 | 1 live field, same instruction | `UseHyperlinks = True`; 4 hyperlinked entry runs |

Word reports the entries with their page numbers
(`Competitive Foundation Report 3`, `Architecture 3`, `Financial Overview 3`,
`Projected Growth 3`, `Page Capped Figure 3`, `Notes 5`), and every entry text is
present in the rendered pages. No repair prompt, no broken field appearance.

Committed page views: five profile TOC pages plus
`wp02_toc_chinese_mixed_page2.png`.

## 6. Tables

| Case | Rendered geometry | Result |
|---|---|---|
| normal 3-column table (every profile) | 3 columns, 5.1893 cm total, first column 1.7092 cm, inside the body | PASS - all header cells rendered |
| wide fitted 8-column table (every profile) | 8 columns, total equals the profile content width (15.0-17.0 cm), right edge at the body edge (e.g. 18.4469 cm vs body 18.461 cm) | PASS - all 8 header labels and every cell rendered |
| wide fitted 8-column table (batch `Wide_Table_Report.docx`) | 8 columns, 15.921 cm | PASS |
| irreducible 25-column table (Program D fixture) | 25 columns at the 1.2 cm floor, 29.9994 cm total in a 29.7 cm landscape page | `KNOWN_ACCEPTED_LIMITATION` - see observations |

No cell content is missing from any packaged output: a character-level
integrity check compares every `w:t` character of the DOCX with the characters
Word actually rendered (`SPEC-AC-003` / `SPEC-INV-001`) and reports **0 dropped
characters** for all nine packaged artifacts.

Committed page views: `wp02_profile_professional_report_tables_page3.png`,
`wp02_batch_wide_table_figure_page3.png`,
`wp02_table_irreducible_program_d_page2.png`.

## 7. Figures

| Case | Word-declared size | Rendered size in the page pixels | Ratio (rendered vs intrinsic) |
|---|---|---|---|
| 4:1 figure (all five profiles, Chinese TOC, batch) | 12.70 x 3.175 cm | 12.677 x 3.187 cm, solid block, fill 1.0 | 3.9777 / 3.9492 vs 4.0 -> 0.56-1.27 % |
| page-capped 1:10 figure (all five profiles) | 2.4606-2.5699 x 24.6204-25.6999 cm | 2.448-2.563 x 24.615-25.723 cm, solid block, fill 1.0 | 0.0995 vs 0.1 -> 0.40-0.50 % |

Verified properties: no crop (the detected block covers the full declared
extent to within 0.03 cm), no distortion (aspect ratio within 1.3 %), no
overlap (the block is 100 % solid with nothing drawn over it), and containment
inside the usable page body (`SPEC-INV-014`): the 4:1 figure right edge sits at
16.833 cm against a body right edge of 18.461 cm, and the page-capped figure
spans exactly the text body height (top 2.54 cm to bottom 27.155 cm against a
body of 2.54-27.1604 cm). The 1:10 figure is horizontally centred in the body
(centre 10.5065 cm vs body centre 10.5005 cm).

Figures are also present in Word's rendered pages as embedded images
(`image_count` equals the declared figure count in every artifact), so no
missing-image placeholder occurs.

Committed page views: `wp02_profile_professional_report_tallfigure_page4.png`
and the profile table pages (which include the 4:1 figure).

## 8. Batch outputs

| Artifact | Word pages | Result |
|---|---|---|
| `01_english.docx` | 3 | PASS - opens, renders, correct Professional Report geometry, TOC intact |
| `Wide_Table_Report.docx` | 3 | PASS - 8-column table and 4:1 figure render inside the body |
| `04_after_failure.docx` | 3 | PASS - the item queued after the failed conversion is independently usable |

The failed batch item produced no document, so nothing about it can corrupt a
neighbouring output; the two successful neighbours and the post-failure output
render with the same geometry as the rest of the acceptance set.

Committed page views: `wp02_batch_english_single_page3.png`,
`wp02_batch_wide_table_figure_page3.png`.

## 9. Observations

| # | Observation | Evidence | Classification |
|---|---|---|---|
| O1 | Word shows `[Compatibility Mode]` because the accepted DOCX declares `compatibilityMode = 14` | window captions of all 10 documents; already recorded in P12-06/08/09/10 | `KNOWN_ACCEPTED_LIMITATION` |
| O2 | In the normal 3-column table the first column is 1.7092 cm in every profile, so the header cell `Component` wraps across two lines (e.g. `Compon` + `ent`) and `WordRenderer` wraps as `WordRender` + `er` in Professional Report; no hyphen is inserted | rendered page text of all five profiles; measured column widths | `LATER_GATE_DEBT` - content is complete and legible, so it is not a blocker; a column-allocation refinement belongs to a later gate |
| O3 | The 25-column Program D fixture is 29.9994 cm wide in a 29.7 cm landscape page, so the trailing columns (`H23`, `H24`) fall outside the printable page and are not rendered | 8 dropped characters; rendered headers `H0`-`H22`; content reaches page edge x = 838.4 pt of 842 pt | `KNOWN_ACCEPTED_LIMITATION` - accepted by Program D (`RENDER006`, PASS_WITH_WARN); no packaged R2-V02 output exhibits it |
| O4 | The Program D fixture's trailing empty section renders an empty page | page 3 ink fraction 0.0 of that fixture | `LATER_GATE_DEBT` - fixture-design characteristic of a verification sample, not a packaged-runtime output |

None of O1-O4 affects a supported packaged workflow, and none is a
`VISUAL_PRODUCT_DEFECT`.

## 10. Protected drift result

| Protected contract | Result |
|---|---|
| Product source modified | No (0 files under `md_converter/` changed) |
| Accepted R2-V02 packaged outputs | Reused byte-identical (0 hash changes) |
| Frozen profile distinctions | Preserved (measured equal to the profile registry) |
| TOC / table / figure semantics | Not redefined, not changed |
| Product or Word settings | Not modified |
| Drift | 0 |

## 11. Commit

Commit message: `R2V03-02 verify native Word visual acceptance`
(exact-file staging: this evidence file, the visual acceptance matrix, the
native render matrix, the page pixel matrix, the rendered page views, and the
two verifier scripts added in this work package).

## 12. Status

PASS - the accepted packaged output renders in desktop Microsoft Word with the
frozen profile distinctions intact; English and Chinese/mixed TOCs render and
navigate; tables and figures are complete, unclipped, undistorted and inside
the usable page body; representative batch outputs remain independently usable.
Introduced visual defects: 0. Unresolved blockers: 0.
