# WP-R2V01-04 — Application / CLI / GUI / Serial Batch Integration

**Program:** R2-V01 — Competitive Foundation Integrated Verification (P12-19)
**Work package:** R2V01-04
**Change classification:** G1 — verification only (real entry-point execution)
**Governing SPEC:** `CANONICAL_SPEC.md` (FROZEN 1.1) — SPEC-GOAL-002,
SPEC-GOAL-003, SPEC-GOAL-009 / SPEC-INV-012
**Baseline:** `7330b1e` (`master`)
**Status:** PASS — serial-batch invariant violations = 0, introduced failures = 0

## 1. Objective

Prove the application boundary, CLI, GUI worker/application and multi-file
Serial Batch still behave as accepted: single-file service, strict serial
(`active_conversion_count <= 1`), failure isolation, per-file state and
summary, profile captured for the batch, no state leakage, stable output
naming, thread/worker cleanup, and cross-entry consistency.

## 2. Method

`Verification/verify_application_batch.py` drives the **real** entry points:

* GUI: `MainWindow` (offscreen Qt) → `GuiWorker` → `ConversionService.convert`
  → Canonical Core, with a recording wrapper around the real service to
  measure start order, thread identity and peak concurrency.
* CLI: the installed `md-converter.exe` console script (single-file and
  directory modes) in a subprocess.
* Cross-entry: identical source + config through the service and the CLI.

## 3. Results

```text
R2-V01 WP-04 APPLICATION / CLI / GUI / SERIAL BATCH
checks=16 failed=0
```

### GUI single-file + serial batch

Four-file batch `a.md`(ok) · `b.md`(empty → failed) · `c.md`(warn) · `d.md`(ok):

| Check | Measurement |
|---|---|
| G1 execution order | `['a.md', 'b.md', 'c.md', 'd.md']` (list order) |
| G2 serial invariant | peak `active_conversion_count = 1` |
| G3 threading | every conversion on a non-GUI thread; one QThread per job |
| G4 per-file state | `succeeded=2, warnings=1, failed=1` |
| G5 failure isolation | `b.md=FAILED`, yet `d.md=SUCCESS` and its document exists |
| G6 outputs | one document per successful source, named after the source stem; the failed item has no output |
| G7 batch completion | window returns to `READY` |
| G8 cleanup | `worker.is_running=False`, `worker.thread=None`, `is_conversion_active=False` |
| G9 no state leakage | a later single-file conversion succeeds (`concurrency=1`, `state=SUCCESS`) |
| G10 single-file surface | exactly one document in the chosen output folder |
| G11 profile capture | selected `academic` captured on **every** batch request (`['academic','academic']`) |
| G12 profile reaches geometry | rendered left margin 3.0 cm == academic profile |

### CLI entry point

| Check | Measurement |
|---|---|
| H1 directory mode | exit code 0 |
| H2 naming | an explicit frontmatter title `A/B Report` → `A_B_Report.docx`; a title-less source → `alpha.docx` |
| H3 single-file mode | `--output <path>.docx` honoured exactly; exit code 0 |

### Cross-entry consistency

| Check | Measurement |
|---|---|
| I1 | same source + equivalent config through `ConversionService` and through the CLI → identical `word/document.xml` (`sha256=30c1a2379722f096…`) |

## 4. Entry-point path observation (informational)

```text
GUI single-file / serial batch -> ConversionService : YES
CLI -> ConversionService : NO ; CLI -> CompilerContext (canonical core) : YES
```

The CLI currently enters the **canonical core** directly
(`CompilerContext.create` + `ctx.compile`) instead of `ConversionService`. This
is the documented deferred convergence **"Step C"** of
`Doc/V2/Review/P12-02_ARCHITECTURE_INSPECTION.md` (§11) and is recorded as
deferred in the P12-03 closure evidence. Properties that follow:

* no compiler stage is bypassed — the CLI still runs Parser → AST → Pipeline →
  Renderer → QA/PostProcessor → DOCX through the canonical context;
* the CLI output naming rule is byte-identical to
  `application.sanitize_output_title` (WP-R2V01-02 A7);
* converging the CLI onto `ConversionService` would change CLI/architecture
  semantics and is therefore a **G2-class** change, explicitly outside R2-V01
  authority.

**Classification:** `PRE_EXISTING_KNOWN_FAILURE` → documented architecture
deferral (`LATER_RELEASE_GATE_DEBT`, separate CLI-convergence authority).
Not introduced by R2-V01; drift = 0; not repaired.

## 5. WP conclusion

**PASS.** 16/16 checks. The serial-batch invariant holds strictly
(`active_conversion_count = 1`), failure isolation is preserved, per-file state
and summary are correct, the profile is captured for the batch and reaches the
rendered geometry, no state leaks between conversions, worker/thread cleanup is
clean, output naming is stable, and CLI/service agree on the canonical
document. No G2 condition and no BLOCKED condition was encountered. Pipeline
continues to R2V01-05.
