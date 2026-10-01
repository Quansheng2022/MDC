# WP-HA02-01 — Mermaid Rendering Failure: RCA and Minimum Fix

**Work package:** WP-HA02-01 — Reproduce, root-cause, and apply the minimum fix
**Program:** HA-02 — Mermaid Rendering Failure Remediation
**Governance:** `STANDARD_G1`
**Change classification:** G1 bounded defect remediation (no semantic change)
**Governing SPEC:** `CANONICAL_SPEC.md` (FROZEN 1.1) — `SPEC-FUNC-013`, `SPEC-INV-001`,
`SPEC-INV-006`, `SPEC-FUNC-019`
**Result:** `PASS`

## Scope

Restore Mermaid rendering for valid ```mermaid fenced blocks so the produced DOCX contains a
rendered diagram instead of the raw-source text fallback. No Mermaid layout semantics, triangle
geometry, Canonical/Core/QA semantics, public API/CLI semantics or Golden baseline were changed.
The unchanged triage fixture `test_mermaid_triangle_v2.md` (SHA-256
`D6F512CE05082FFC2B826A5E742FFC9D33537338BAED78798626DB5FE41CA02F`) was used for reproduction and
verification.

## Reproduction (before the fix)

**Path B — installed MD Converter (the failing path).** The user's converted DOCX
`Documents\MD_Converter\output\test_mermaid_triangle_v2.docx` contains three images and no raw
Mermaid text; the images are the product's *text fallback*, not renders:

| Figure | Embedded PNG | Display size | Background | Interpretation |
|---|---|---|---|---|
| Case A | 600 × 182 px | 12.700 × 3.852 cm | `#f8f9fa` | `_create_text_fallback_image` (`max(600, …)` × `lines*18+20`, 9 lines → 182) |
| Case B | 600 × 398 px | 12.700 × 8.424 cm | `#f8f9fa` | same fallback (21 lines → 398) |
| Case C | 600 × 524 px | 12.700 × 11.091 cm | `#f8f9fa` | same fallback (28 lines → 524) |

All three backgrounds equal the fallback SVG fill `#f8f9fa`, and all three heights equal the
fallback height formula for the 9/21/28-line Mermaid sources. Raw capture:
`Evidence/WP-HA02-01_user_docx_check.json`.

**Path A — direct project Mermaid runtime.** Rendering the same three blocks through the
Playwright/Chromium path used by the product produced a real `<svg>` for all three cases
(`svgCount = 1`, node labels as text, no fallback). Raw capture:
`Evidence/WP-HA02-01_direct_mermaid_probe.json`.

Conclusion: the Mermaid source itself renders; the failure is in the packaged product's rendering
capability.

## Root cause

`DiagramPass._render_mermaid` tries `mmdc`, then Playwright, then falls back to the raw-text image.
In the shipped product neither backend can run:

1. **Playwright was excluded from the release payload.** `MD_Converter_Lite.spec` passed
   `excludes=['playwright']` to `Analysis`, and the built payload confirms it:
   `dist\MD_Converter_Lite\_internal` contains no `playwright` package. In a windowed frozen build
   `import playwright` therefore raises `ImportError`, `_check_playwright()` is `False`, and
   `_render_mermaid` jumps straight to `_create_text_fallback_image`.
2. **`mmdc` is not part of the product** (`mmdc` is not on `PATH`, is not bundled, and the frozen
   packaging decision records "Playwright excluded" as the Lite profile).

Two further fragilities in the same code path are part of the proven cause and are corrected with
the same bounded change:

3. **The Mermaid runtime was fetched from a CDN at conversion time** (`cdn.jsdelivr.net/npm/mermaid@10`).
   Any offline or CDN-blocked environment cannot render, regardless of browser availability.
4. **The screenshot path accepted a page where Mermaid never initialised.** `element.screenshot()`
   was taken without checking for a rendered `<svg>`, so a page that still contained the raw
   `<pre class="mermaid">` source was captured as if it were a rendered diagram (raw Mermaid source
   as an image). The fallback's original exception was also only printed, and `print()` is a no-op
   in the windowed build, so the shipped product could not report why rendering failed.

Failure classification per the product specification: `PASS` (bounded defect, single causal cause).

## Files changed

| File | Change |
|---|---|
| `md_converter/renderer/assets/mermaid.min.js` | **new** — vendored Mermaid 10.9.8 runtime (3,337,857 bytes, SHA-256 `8D607D7EF1D077A8AA202E18E62212BFA992C68BFEABC5CF45D51A128FE6675D`) so rendering never depends on the CDN |
| `md_converter/renderer/assets/mermaid.LICENSE.txt` | **new** — Mermaid MIT license text shipped with the asset (1,089 bytes, SHA-256 `EC9FB67DCB25ECCC416ED56E1AAB819222C805A2A4BFE4CB19E7556BF2FFDE80`) |
| `md_converter/pipeline/passes/diagram_pass.py` | inline the vendored runtime (CDN only as last resort); wait for a real `.mermaid svg` before screenshotting; record the original failure reason and surface it in the existing `DIAG002` diagnostic; add browser discovery (explicit path → Playwright-managed Chromium → OS Microsoft Edge) |
| `MD_Converter_Lite.spec` | removed `excludes=['playwright']`; added `collect_all('playwright')` so the declared Mermaid backend ships with the payload. Browser binaries are deliberately not bundled — the runtime uses the Playwright-managed browser when present and otherwise the OS Chromium |
| `THIRD_PARTY_NOTICES.txt` | section 13 rewritten for the new distribution content (Playwright runtime bundled; Chromium/Microsoft Edge discovered, not bundled; Mermaid asset + license) |

`THIRD_PARTY_NOTICES.txt` is an authoritative distribution file that this repository keeps
untracked (it is not in Git; `EULA.txt` is the same). It is therefore not staged by this commit;
its exact content is identified here by size `11890` bytes and SHA-256
`E4B8D7223F085357DF923226FECD5AA189206B65448C26D1AD772C7116229696` so the shipped file is
verifiable. The notice update is required by the file's own instruction to update notices when a
distribution's bundled dependencies change.

Browser discovery keeps the "Lite" profile free of a ~215 MB bundled Chromium while still rendering
on a clean Windows installation: every supported Windows 10/11 machine ships Chromium-based
Microsoft Edge. No new Python runtime dependency was introduced — `playwright` is the product's
existing, declared `[mermaid]` extra (`pyproject.toml`), and it is invoked locally only.

## Verification (focused, per the WP-01 ladder)

| Check | Command / evidence | Result |
|---|---|---|
| Case A/B/C direct Mermaid runtime (vendored asset, **all network blocked**) | `ha02_mermaid_probe.py --runtime md_converter\renderer\assets\mermaid.min.js --offline` | PASS — 3/3 `svgCount = 1`, `mermaidLoaded = true`, no run error |
| Case A/B/C direct Mermaid runtime (CDN reference run, pre-change behaviour) | `ha02_mermaid_probe.py` (CDN) | PASS — 3/3 rendered; identical screenshot byte counts to the vendored run |
| Case A/B/C source conversion → DOCX | `md-converter input_test\mermaid_triangle\test_mermaid_triangle_v2.md -o build\ha02_source\…docx --no-open -v` | PASS — `Mermaid rendered successfully (playwright-chromium)` ×3, no `DIAG002` |
| Converted DOCX figures are real renders | `ha02_docx_check.py build\ha02_source\…docx --json` | PASS — 3 images, background `#ffffff`, 1160×221/336/336 px, `fallback_images = []` |
| Nearest existing Mermaid-focused tests | `pytest "…::test_canonical_golden_environment" "…::test_golden[sample]"` | PASS — `2 passed` (backend still `playwright`, no Golden drift) — raw capture `Evidence/WP-HA02-01_golden_tests.txt` |
| Non-Mermaid control | `md-converter md_converter\tests\acceptance\AC001_simple.md -o build\ha02_control\AC001_simple.docx --no-open` | PASS — DOCX produced (37,608 bytes), no diagram nodes involved |

Word COM TOC refresh was unavailable during the command-line runs (documented environment
limitation, `SPEC-FUNC-011` degradation); the documents were still generated.

## New failures

None. Introduced failures = 0.

## Protected semantic drift

```text
Canonical Specification semantics      : 0
Core / QA semantic contract            : 0
public API / CLI semantics             : 0
Mermaid acceptance semantics           : 0
renderer/table/figure/TOC semantics    : 0
Golden baseline changed                : NO  (sample.expected.json SHA-256 still 6D589013B8024C158DE5D29B93BDFEF68F2F406045C805DAB61F8E513725829A)
product version / metadata             : unchanged (1.1.0)
```

## Commit

`HA02-01 resolve Mermaid rendering failure`

Failure classification: `PASS` → continue automatically to WP-HA02-02.
