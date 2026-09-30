# WP-R2V01-07 — Release Readiness Classification

**Program:** R2-V01 — Competitive Foundation Integrated Verification (P12-19)
**Work package:** R2V01-07
**Change classification:** G1 — classification only (no product change)
**Baseline:** `7330b1e` (`master`) · verified through `1bbf686`
**Status:** PASS for the source-level release gate — 0 unresolved source blockers

## 1. Objective

Classify the current source baseline against the R2-V01 release matrix and mark
the later gates explicitly, so the pipeline can decide whether the source is
eligible to proceed to packaged-runtime, native-Word/visual, Golden-environment,
RC, Human Acceptance and Production Release gates.

## 2. Release matrix (source level)

| # | Capability | Status | Evidence |
|---|---|---|---|
| 1 | Core / Canonical (`CompilerContext.compile()` single authority) | **PASS** | WP-02 A2/A4; WP-05 Q1/Q2 |
| 2 | Application / CLI (service boundary, naming, single-file) | **PASS** | WP-04 H1–H3, I1; WP-02 A7/A9 |
| 3 | GUI (worker/application, single-file surface, cleanup) | **PASS** | WP-04 G7–G10 |
| 4 | Serial Batch (strict serial, failure isolation, summary) | **PASS** | WP-04 G1–G6, G11–G12 (peak concurrency = 1) |
| 5 | Document Intelligence / Conversion Report | **PASS** | WP-05 Q3–Q5 |
| 6 | Professional Output Profiles (five profiles, resolved geometry) | **PASS** | WP-03 C; WP-02 A6; WP-04 G11–G12 |
| 7 | TOC Heading Localization (single authority) | **PASS** | WP-03 A2–A4, B2–B4; WP-02 A5 |
| 8 | Advanced Table Fitting (floor, no mutation, fixed layout) | **PASS** | WP-03 A5–A10, D1–D4, D8–D9; WP-02 A5 |
| 9 | Advanced Figure Fitting (aspect ratio, content box) | **PASS** | WP-03 A11–A14, D5–D7; WP-02 A5 |
| 10 | `image_width` (IMG-CFG-01, narrow propagation, capped) | **PASS** | WP-03 A12/A14, C; WP-02 A8 |
| 11 | QA (single authority, real diagnostics, fail-closed) | **PASS** | WP-05 Q1–Q5; WP-03 D10–D11 |
| 12 | Failure recovery (per-file; no poisoning) | **PASS** | WP-04 G5, G9; WP-05 R1–R3 |
| 13 | Determinism (decisions stable) | **PASS** | WP-03 E1–E3; WP-05 S |
| 14 | Privacy (approved source-level check) | **PASS** | WP-05 P1–P3 |
| 15 | Source regression (introduced failures = 0) | **PASS** | WP-06 grouped + full suite |

```text
protected-contract drift            = 0   (WP-02)
authority duplication               = 0   (WP-02, WP-05)
SPEC-FUNC-023 drift                 = 0   (WP-02 A8, WP-03 A12/D6)
serial-batch invariant violations   = 0   (WP-04 G2)
introduced source failures          = 0   (WP-06)
unresolved product-owned source blockers = 0
```

## 3. Later-release gates — explicitly PENDING

```text
Packaged runtime / multi-file runtime verification   = PENDING R2-V02
Native Word / human visual acceptance                = PENDING R2-V03
Chromium / Golden-environment retest                 = PENDING R2-V04
```

R2-V01 does **not** close V02/V03/V04 and makes no claim about them.

## 4. Known conditions carried forward (classified, not blockers)

| Condition | Classification | Rationale |
|---|---|---|
| 2 × README packaging test failures | `PRE_EXISTING_KNOWN_FAILURE` | function of the pre-existing modified `README.md`; unrelated to source authority |
| 2 × Chromium/Golden test failures (`spawn EPERM`) | `ENVIRONMENT_FAILURE` → `LATER_RELEASE_GATE_DEBT` (R2-V04) | sandbox cannot launch Chromium; no source defect |
| CLI does not yet enter via `ConversionService` | documented architecture deferral (`PRE_EXISTING_KNOWN_FAILURE`) | P12-02 §11 "Step C"; CLI still uses the canonical core; convergence is a G2-class change |
| data-URI picture `name` is a per-run temp stem | `PRE_EXISTING_KNOWN_FAILURE` (format-level) | decisions (TOC/geometry/widths/profile/diagnostics) remain deterministic; real file-image path is byte-identical |
| twips quantization of DOCX lengths | format property, not a defect | ≤ ~0.002 cm; repository guards use the same 1e-3 cm tolerance |

None of the above is a product-owned **source** blocker, and none is repaired
here (each would require unrelated history, a G2 semantic change, or an
environment outside this sandbox).

## 5. Stop-condition audit

```text
G2 AUTHORITY REQUIRED : not triggered
  - no Canonical/Core semantic change required
  - no QA semantic contract change required
  - no ConversionService redesign required
  - no API/CLI/output-naming semantic change required
  - no SPEC-FUNC-023 change required
  - no profile/TOC semantic redefinition required
  - no parser/AST or renderer/page/section architecture rewrite required
  - no Golden semantic re-freeze, new dependency, new user-facing setting, or
    destructive transformation required

BLOCKED : not triggered
  - exact staging was safe and separated (three pre-existing dirty tracked files
    were never staged)
  - required source-level verification was possible
  - no bounded correction was needed (zero introduced failures)
  - required evidence was produced for every WP
```

## 6. WP conclusion

**PASS (source-level release gate).** Every row of the release matrix is PASS,
all protected-contract drift is zero, there are no unresolved product-owned
source blockers, and the later gates are explicitly pending. The source baseline
is eligible to proceed to the R2-V02 packaged-runtime gate. No G2 condition and
no BLOCKED condition was encountered. Pipeline continues to R2V01-08 (closure).
