# WP-R2V01-03 — Cross-Feature Document Integration

**Program:** R2-V01 — Competitive Foundation Integrated Verification (P12-19)
**Work package:** R2V01-03
**Change classification:** G1 — verification only (measured DOCX evidence)
**Governing SPEC:** `CANONICAL_SPEC.md` (FROZEN 1.1) — SPEC-GOAL-004,
SPEC-GOAL-003, SPEC-FUNC-023, SPEC-INV-003
**Baseline:** `7330b1e` (`master`)
**Status:** PASS — 53/53 measured checks

## 1. Objective

Prove the accepted capabilities still compose inside one document, measured
from the produced artifact, not inferred from module unit tests:

* **A** English professional report — TOC + normal/wide tables + figure +
  explicit `image_width` + diagnostics.
* **B** Chinese / mixed report — localized TOC + table/figure fitting.
* **C** the same representative document across all five output profiles.
* **D** boundary case — irreducible wide table (fit floor) + page-capped figure
  (height limit), with fit-reason evidence.

Asserted: no content/cell mutation, correct TOC heading + field, table floor
preserved, aspect ratio preserved, effective profile geometry respected,
`image_width` respected/capped, diagnostics QA-derived, deterministic repeat,
no profile-name branches.

## 2. Method

`Verification/verify_cross_feature_documents.py` converts each fixture through
the accepted **application entry point** (`ConversionService.convert`), then
measures the produced DOCX (`python-docx` + `word/document.xml`): TOC heading
and field, TOC cached entries, table cell matrix, `w:tblGrid` column widths,
`w:tblLayout`, section geometry, inline-shape geometry. Fit *reasons* are read
from the single authorities (`plan_table_fit`, `plan_figure_fit`). Figures use
a deterministic in-script PNG (no new dependency). `word_com` is disabled
because the sandbox has no Word (the TOC field is still inserted).

## 3. Results (measured)

```text
R2-V01 WP-03 CROSS-FEATURE DOCUMENT INTEGRATION
checks=53 failed=0
```

### A — English professional report

| Check | Measurement |
|---|---|
| status | `SUCCESS` (no warnings) |
| TOC heading | `'Table of Contents'` (style `TOC Heading`) |
| TOC field | `TOC \o "1-3" \h \z \u` present |
| TOC entries | `Competitive Foundation Report · Architecture · Financial Overview · Projected Growth · Notes` |
| normal table cells | unchanged (`Component/Authority/Status`, `Parser/markdown-it/frozen`, …) |
| wide table | 8 explicit columns, `autofit=False`, fixed layout |
| wide table widths (cm) | `[1.799, 1.799, 1.799, 1.799, 1.799, 2.849, 1.799, 2.279]`, total ≈ 15.923 ≤ content 15.921 (twips rounding) |
| column floor | min 1.799 ≥ 1.2 cm |
| figure | width 10.16 cm == `min(image_width 4in, content 15.921)`, height 2.54 cm, ratio 4.0 (4:1 preserved) |
| diagnostics | none (clean document) |

### B — Chinese / mixed report

| Check | Measurement |
|---|---|
| status | `SUCCESS` |
| TOC heading | `'目录'` (THL single authority) |
| TOC entries | `竞争基础集成验证 · 架构 · 图形 · 备注` |
| table cells | unchanged (`组件/权威/状态`, …) |
| table fit | total 4.680 ≤ content 15.921, min column 1.1994 (floor 1.2 − twips) |
| figure | ratio 2.0 (2:1 preserved), inside the content box |

### C — five-profile matrix

The same English document converted once per profile; declared geometry
reaches the artifact with no renderer profile-ID branch:

| Profile | artifact margins (L,R,T,B cm) | declared | content box (cm) |
|---|---|---|---|
| professional_report | 2.54, 2.54, 2.54, 2.54 | 2.54, 2.54, 2.54, 2.54 | 15.921 × 24.62 |
| business_report | 2.0, 2.0, 2.0, 2.0 | 2.0, 2.0, 2.0, 2.0 | 17.0 × 25.7 |
| academic | 3.0, 3.0, 2.54, 2.54 | 3.0, 3.0, 2.54, 2.54 | 15.0 × 24.62 |
| technical | 2.2, 2.2, 2.2, 2.2 | 2.2, 2.2, 2.2, 2.2 | 16.602 × 25.301 |
| clean_minimal | 2.54, 2.54, 2.54, 2.54 | 2.54, 2.54, 2.54, 2.54 | 15.921 × 24.62 |

For every profile, all tables fit inside that profile's content width, the
figure respects `min(image_width, content width)`, and the TOC heading is
unchanged (`'Table of Contents'`, status `SUCCESS`).

### D — boundary case

| Check | Measurement |
|---|---|
| irreducible table | 25 columns retained, every cell kept, first cell `'H0'` |
| column floor | all columns 1.1994 cm (floor 1.2 − twips) |
| table fit reason | `squeezed=True`, total 30.0 cm > content 15.921, font step 9.0 pt ≥ 8.5 pt floor |
| figure fit reason | `height_limited=True`, `width_limited=False`; delivered 2.462 × 24.62 cm == content height, ratio 0.1 preserved |
| wide-table warning | `RENDER006` surfaced with the fit plan in `details` (`squeezed`, `min_column_width_cm=1.2`) |
| QA-derived diagnostics | `QA_RENDERED_WARN` (`stage=rendered_qa`) + `QA_FINAL_WARN` (`stage=final_artifact_qa`) |
| quality-gate report | `static_qa=PASS`, `rendered_qa=PASS_WITH_WARN`, `post_processor=PASS`, `final_artifact_qa=PASS_WITH_WARN` |

### E — determinism

| Check | Result |
|---|---|
| file-image report, repeated conversion | `word/document.xml` byte-identical (`sha256=2fe28ca8…`) |
| data-URI report, repeated conversion | identical after masking the picture `name` attribute |
| boundary report, repeated conversion | identical after masking the picture `name` attribute |

### F — no profile-name branching

No module under `md_converter/renderer/` imports `md_converter.profiles`
(`offenders=[]`), consistent with WP-R2V01-02 A6.

## 4. Observations (classified, not repaired)

1. **Twips quantization.** DOCX stores lengths in twips, so a column written as
   exactly 1.2 cm reads back as ≈ 1.1994 cm and a fitted table total can read
   back ~0.002 cm above the computed content width. This is a format
   quantization, not a fitting fault; the repository's own guards use a 1e-3 cm
   tolerance. `PRE_EXISTING_KNOWN_FAILURE`-class (format property, no repair).
2. **Data-URI picture name.** When an image is supplied as a `data:` URI, the
   embedded picture's internal `pic:cNvPr/@name` is a per-run temp stem, so the
   document XML is not byte-identical across runs. All *decisions* (TOC,
   geometry, widths, diagnostics) are identical, and the real product path
   (a filesystem image reference) is byte-identical. Not introduced by R2-V01;
   recorded for WP-R2V01-05 determinism and flagged as a bounded observation.

## 5. WP conclusion

**PASS.** Cross-feature document integration is green: 53/53 measured checks
across English, Chinese/mixed, five-profile, boundary, determinism and
no-profile-branch scenarios. No content/cell mutation, aspect-ratio or
geometry regression; `image_width` respected/capped; diagnostics QA-derived.
No G2 condition and no BLOCKED condition was encountered. Pipeline continues to
R2V01-04.
