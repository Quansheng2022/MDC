# P12-07 — Settings / Product Polish
## Specification Baseline

**Product Baseline SHA:** `f3b4e3d5d15d7b95f20fea19515e2e49d8f3e44e`  
**Execution:** One bounded WP at a time.  
**Governance:** G0 cosmetic autonomy; G1 bounded review; G2 stop/escalate.

## Objective
Turn the accepted P12-06 GUI into a polished, predictable desktop product without expanding conversion semantics.

## In Scope
- Minimal GUI settings and local persistence
- Settings UX
- About / Privacy / Product Identity
- Main-window polish
- Keyboard, focus, accessibility, window behavior
- High-DPI smoke
- Verification and closure

## Frozen Architecture
```text
GUI → GuiWorker → ConversionService → Canonical Core
ConversionResult / JobFailure → presentation model → report/output UX
```

## Settings Scope
Authorized:
- Restore window size/geometry
- Remember last-used source directory
- Remember last-used output directory
- Optional single "remember folders" toggle
- Reset GUI preferences to defaults

Out of scope:
- filename rules
- conversion engine options
- QA thresholds/repair settings
- template/profile framework
- diagnostics semantics
- themes
- telemetry/cloud/account/plugin settings
- auto-update
- packaging/installer

## Settings Architecture
Preferred:
```text
GUI → GuiPreferences → QSettings
```
Application layer remains Qt-free. No global/general configuration framework.

Remembered output directory is a GUI convenience only; it must not redefine `ConversionService` default output behavior.

## Product Identity
Preserve:
> **Turn Markdown into polished Word documents — locally, privately, and without a subscription.**

May state local processing, no account required, and no document upload required by the normal product workflow. Reuse authoritative version metadata where practical.

## Product Polish
Allowed: spacing, margins, alignment, button sizing, wording, hierarchy, tooltips, dialog sizing.
Forbidden: new workflow, dashboard, sidebar, home screen, states, conversion features.

## Accessibility / Window Behavior
- logical Tab order
- standard keyboard behavior
- Esc closes dialogs where appropriate
- useful accessible names
- status not conveyed by color alone
- report remains keyboard accessible
- restore geometry safely
- worker-active close protection remains unchanged
- bounded High-DPI smoke

## Governance
G2 stop conditions:
- change ConversionResult/Request/Service
- change Core/QA/Canonical/Golden
- change CLI/public API semantics
- change output naming/path semantics
- introduce conversion config framework
- introduce network/cloud/telemetry
- change privacy or packaging architecture

## Test Strategy
WPs 01–05: focused verification only.
WP-06: full GUI/application/relevant CLI-public API/full regression/Golden-Acceptance/Windows smoke.

## Exit Criteria
P12-07 closes only if settings, persistence, Save/Cancel/Reset, About/Privacy, product polish, keyboard/focus/accessibility/window behavior, and High-DPI all pass; existing conversion/diagnostics/lifecycle semantics remain unchanged; direct GUI→Core=0; application Qt dependency=0; Core/Golden/CLI regressions=0; introduced failures=0; blockers=0.

Next phase: **P12-08 Packaging / Installer**.
