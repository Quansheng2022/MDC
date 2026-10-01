# HA-02 — Mermaid Rendering Failure Remediation
## Closure Evidence

**Program:** HA-02 — Mermaid Rendering Failure Remediation
**Governance:** `STANDARD_G1` — bounded defect remediation (no semantic change)
**Governing SPEC:** `CANONICAL_SPEC.md` (FROZEN 1.1) — `SPEC-FUNC-013`, `SPEC-INV-001`,
`SPEC-INV-006`, `SPEC-FUNC-019`
**Work packages:** 2 / 2 PASS
**Upstream:** R2-RC release candidate freeze (`cd70d86`) + Human Acceptance finding HA-02
**Final status:** `HA-02 — CLOSED / ACCEPTED / MERMAID RENDERING REMEDIATION PASS`

## 1. Root cause

`DiagramPass._render_mermaid` renders through `mmdc`, then Playwright, then a raw-source text
fallback image. In the shipped product neither renderer could run:

1. `MD_Converter_Lite.spec` passed `excludes=['playwright']` to PyInstaller, so the released
   payload contained no Playwright package (`dist\MD_Converter_Lite\_internal` had no `playwright`);
   `import playwright` failed, `_check_playwright()` was `False`.
2. `mmdc` is not part of the product (not on `PATH`, not bundled).

Every `mermaid` block therefore degraded to `_create_text_fallback_image`. The user-visible
evidence matches exactly: the converted DOCX contained three images with the fallback SVG fill
`#f8f9fa` at 600 × 182 / 398 / 524 px, i.e. the fallback geometry for the 9 / 21 / 28-line Mermaid
sources.

Two further defects in the same path are corrected by the same bounded change: the Mermaid runtime
was fetched from `cdn.jsdelivr.net` at conversion time (so an offline machine could not render), and
the screenshot was taken without checking that Mermaid had produced an `<svg>` (so a page that
never initialised Mermaid would have been captured as raw source), with the original failure only
`print()`ed — invisible in the windowed build.

## 2. Changed files

| File | Change |
|---|---|
| `md_converter/renderer/assets/mermaid.min.js` | vendored Mermaid 10.9.8 runtime (3,337,857 bytes, SHA-256 `8D607D7E…E6675D`) — no CDN dependency |
| `md_converter/renderer/assets/mermaid.LICENSE.txt` | Mermaid MIT license text shipped with the asset |
| `md_converter/pipeline/passes/diagram_pass.py` | inline the vendored runtime; wait for a real `.mermaid svg` before screenshotting; surface the original failure reason in `DIAG002`; browser discovery (explicit path → Playwright-managed Chromium → OS Microsoft Edge) |
| `MD_Converter_Lite.spec` | `excludes=['playwright']` removed; `collect_all('playwright')` added (no browser binaries bundled) |
| `.gitattributes` | keeps the vendored third-party assets byte-exact (no EOL conversion) |
| `THIRD_PARTY_NOTICES.txt` | section 13 rewritten for the new distribution content (untracked distribution file, not staged; 11,890 bytes, SHA-256 `E4B8D722…229696`) |
| `Doc/V2/Implementation/HA_02/*` | evidence and verification tooling |

No Canonical/Core/QA/API/CLI/Mermaid-acceptance semantic, renderer layout, table/figure/TOC
behaviour or Golden baseline was changed. Product version/metadata stay `1.1.0`; the installer
script is byte-identical (`EBB0979972348ECA2926BC3095049BDB047B36F206E9D66E2A1C7E468B91CE03`) so
installer semantics are unchanged.

## 3. Focused verification summary

| Check | Result |
|---|---|
| Case A/B/C direct Mermaid runtime, vendored asset, all network blocked | PASS — 3/3 rendered (`svgCount = 1`) |
| Case A/B/C source conversion → DOCX | PASS — `playwright-chromium`, no `DIAG002`, 3 real renders (white background, no fallback) |
| Nearest existing Mermaid-focused Golden checks | PASS — `2 passed` (`renderer_backend` still `playwright`, no Golden drift) |
| Non-Mermaid control (`AC001_simple.md`, source path) | PASS — DOCX produced (37,608 bytes) |

## 4. Rebuilt payload and installer identities

Built with the documented clean-build procedure `tools/packaging/build_windows_release.ps1` on
2026-10-01 13:35:33 +08:00.

| Item | Old (R2-RC, preserved) | New (HA-02) |
|---|---|---|
| Packaged executable | 6,926,650 B / `68524527…0E3021` | **7,671,725 B / `C368DFEBBC3660020CB20119E4952D83E2791B5D231D6BE62A6D0E552C871270`** |
| Payload files / bytes | 268 / 166,231,301 | **461 / 279,011,814** |
| Payload tree digest (release-identity algorithm) | `ecb6a445…f8efa96c` | **`92daa5ea8c7031e0046ccd2d875990cfebbca9ba8767f9d4c00e9d1a316cf370`** |
| Installer | 51,186,717 B / `4B56FC98…4FFDE9` | **77,296,967 B / `C54ADF6225689F06886B6C326E897BEB294EBA13EFD7897328DD738F6CF3CA42`** |
| Installer metadata | FileVersion 1.1.0.0, ProductVersion 1.1.0, `MD Converter`, `Quansheng2022` | unchanged |
| Compiler | ISCC.exe, Inno Setup 7 (`Inno Setup 7.1.0` per R2-PRE-RC-01) | same compiler/path |

The payload grows by ~113 MB because the Playwright runtime now ships; no Chromium binaries are
bundled (the runtime uses the machine's Playwright-managed Chromium when present, otherwise the
OS Chromium/Microsoft Edge). Raw identity: `Evidence/WP-HA02-02_payload_identity.json`.

## 5. Installed-application verification (normal GUI path)

The rebuilt installer was installed silently (exit code `0`) and the untouched fixture was converted
through the **installed application's own GUI** using the existing UI-Automation smoke tool
(`tools/packaging/windows_gui_smoke.ps1`). Raw captures: `Evidence/WP-HA02-02_INSTALLED_RESULT.json`,
`WP-HA02-02_gui_smoke_fixture.json`, `WP-HA02-02_gui_smoke_control.json`,
`WP-HA02-02_installed_docx_check.json`, plus the produced document
`Evidence/WP-HA02-02_installed_render.docx`.

| Check | Result |
|---|---|
| Installed executable identity | `C368DFEB…C871270` — equals the rebuilt payload |
| Playwright present in the install | YES (`_internal\playwright\driver\node.exe`) |
| Vendored Mermaid asset present in the install | YES (`_internal\md_converter\renderer\assets\mermaid.min.js`) |
| Case A rendered | **YES** |
| Case B rendered | **YES** |
| Case C rendered | **YES** |
| Raw Mermaid fallback | **NO** — 3 images, backgrounds `#ffffff`, `fallback_images = []`, no fallback text |
| Conversion | PASS (smoke exit `0`), DOCX 63,685 B / SHA-256 `944FACC4…2408287` |
| DOCX opens | YES (structure parsed: 128 paragraphs, 3 inline images) |
| Non-Mermaid control through the installed GUI | PASS (smoke exit `0`, `AC001_simple.docx` 29,548 B, 0 images, no fallback) |

## 6. Two-path comparison (Case A / B / C)

Exact same Mermaid source; Path A = direct project Mermaid runtime, Path B = installed MD Converter
DOCX. Raw capture: `Evidence/WP-HA02-02_two_path_compare.json`.

| Case | Path A pixels | Path B pixels | Content box | Content aspect | Layout IoU |
|---|---|---|---|---|---|
| A | 1160 × 221 | 1160 × 221 | 512,7 – 649,211 | 0.672 / 0.672 | 0.9912 |
| B | 1160 × 336 | 1160 × 336 | 525,7 – 652,301 | 0.432 / 0.432 | 1.0 |
| C | 1160 × 336 | 1160 × 336 | 361,7 – 763,301 | 1.367 / 1.367 | 1.0 |

Both paths render successfully with materially identical layout (identical pixel size and content
box; IoU 0.99–1.00). The images are not byte-identical because Path A uses the stock Mermaid theme
while the product applies its own `themeVariables` — a colour difference only. Classification per
the remediation contract: **PASS** (no converter-induced rendering difference, no distortion).

Neither Case B nor Case C produces a perfect triangle; that is Mermaid's own automatic-layout
behaviour and is explicitly outside this remediation contract (the triangle geometry is not part of
the fix and the Mermaid source was not modified).

## 7. Old RC rollback identity and supersession

| Item | Value |
|---|---|
| Superseded RC manifest | `Doc/V2/Implementation/R2_RC/R2_RC_MANIFEST.md` (RC closure commit `cd70d86`) |
| Old packaged EXE | 6,926,650 B / `68524527CDC5718CE31A1F0454EAFB0FF64C52D5C838716AC1277445DE0E3021` |
| Old installer | 51,186,717 B / `4B56FC989BAB7FF7E648CC29DFE5A6D944B2B8EFC420F11DE8D0ECF8294FFDE9` |
| Old payload tree digest | `ecb6a4453f342af51cbc2b26b175489cb4ad963bc987a7407ff10ff0f8efa96c` |
| Preserved copy (not deleted, not rebuilt over) | `release/R2RC_pre_HA02_preserved/` with `SHA256SUMS.txt` |
| Old RC status | **SUPERSEDED** — a protected RC input (product source, payload bytes and installer bytes) changed, which invalidates the frozen R2 release candidate per its own invalidation rule. It remains immutable history. |

## 8. Gate counters

```text
Cases rendered without fallback        : 3 / 3  (A, B, C)
installed raw-Mermaid fallback         : NO
non-Mermaid control                    : PASS
direct-vs-installed layout agreement   : IoU 0.9912 / 1.0 / 1.0
Golden baseline drift                  : 0   (2 passed, backend still playwright)
Canonical/Core/QA/API/CLI drift        : 0
new product runtime dependency         : none (playwright is the declared [mermaid] extra; no browser bundled)
new failures                           : 0
unresolved blockers                    : 0
truthful commits                       : 2
```

Failure classification per the remediation contract: `PASS`.

## 9. Next required release step

1. Freeze a **new Release Candidate** over this remediated payload/installer (the previous RC is
   superseded, not eligible).
2. Targeted **Human re-acceptance**: the Mermaid fixture (`test_mermaid_triangle_v2.md`) plus one
   ordinary Markdown conversion through the installed candidate.

The rebuilt candidate is currently installed on this machine and was used for the verification
above. The whole R2 chain was not re-run: the fix does not touch another protected risk domain.

`HA-02 — CLOSED / ACCEPTED / MERMAID RENDERING REMEDIATION PASS`
