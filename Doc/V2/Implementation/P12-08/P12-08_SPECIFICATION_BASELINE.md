# P12-08 — Packaging / Installer
## Specification Baseline

**Project:** MD_Converter v2.0  
**Phase:** P12-08 — Packaging / Installer  
**Product Baseline SHA:** `1b040c5d0d19f16be127cf3060fb573005a69c81`  
**Governance:** bounded G1 packaging work; G2 stop/escalate  
**Execution rule:** one Work Package at a time, focused verification, bounded commit, then next WP.

## 1. Objective

Turn the accepted P12-07 Windows desktop application into a reproducible, installable Windows product artifact without changing product semantics.

P12-08 owns:

- Windows executable packaging;
- bundled runtime/resource completeness;
- Windows installer;
- installed/uninstalled application behavior;
- packaged-environment verification;
- version/product metadata used by package/installer;
- licence/third-party notice inclusion where already authoritative;
- packaging artifact integrity;
- packaging/installer closure evidence.

P12-08 does **not** own:

- conversion semantics;
- Core / Canonical / QA behavior;
- new GUI features;
- new Settings features;
- auto-update;
- cloud/account/telemetry;
- code-signing procurement;
- Microsoft Store publication;
- macOS/Linux packaging;
- file-association features unless already explicitly required;
- new licensing/activation system.

## 2. Frozen Product Baseline

P12-07 is CLOSED / ACCEPTED.

Accepted P12-07 closure:

`1b040c5d0d19f16be127cf3060fb573005a69c81`

Frozen runtime architecture:

```text
GUI
→ GuiWorker
→ ConversionService
→ Canonical Core
```

Packaging must wrap this application; it must not introduce another execution path.

## 3. Work Packages

| WP | Title | Responsibility |
|---|---|---|
| WP-P12-08-01 | Packaging Baseline | inspect existing packaging assets; freeze entry point, metadata, artifact layout |
| WP-P12-08-02 | Windows Executable | build standalone Windows application and verify packaged startup/runtime |
| WP-P12-08-03 | Windows Installer | build bounded installer/uninstaller around accepted packaged app |
| WP-P12-08-04 | Product Metadata / Notices | version, icon/resource, EULA/notices integration without creating new authorities |
| WP-P12-08-05 | Packaged Runtime Verification | real installed-app smoke, cp1252 environment, paths, settings, output actions |
| WP-P12-08-06 | Release Artifact Verification | clean-build reproducibility, artifact inventory, hashes/sizes, install/uninstall checks |
| WP-P12-08-07 | Verification & Closure | final regression evidence and phase closure |

## 4. Packaging Principles

1. **Packaging ≠ product semantics.**
2. Existing Python application behavior is authoritative.
3. Packaging-only fixes must remain packaging-only whenever possible.
4. Do not alter Core or Application semantics to make a bundler happy unless there is a proven packaging blocker and Human authority is obtained.
5. Prefer the smallest stable Windows packaging stack already present in the repository.
6. Reuse existing `.spec`, installer scripts, icons, version metadata, notices and release assets where valid instead of creating duplicate systems.

## 5. Runtime Entry Point

The packaged GUI entry point must resolve to the accepted GUI application path.

Do not package an alternate CLI-driven or direct-Core GUI path.

No new direct GUI → Core dependency is allowed.

## 6. Known Packaging-Risk Item — cp1252

P12-08 explicitly owns verification of the known Windows console encoding issue involving `DocxPostProcessor` emoji output and cp1252.

Required result is one of:

```text
A. packaged GUI environment does not expose the failure → verified non-blocker

B. packaged GUI reproduces the failure → bounded packaging/runtime fix required

C. fix would require semantic/Core change → STOP and escalate
```

Do not assume `PYTHONIOENCODING=utf-8` is an acceptable production solution unless the final packaged runtime explicitly and safely establishes equivalent behavior.

## 7. Installer Boundary

Installer may own:

- install directory;
- Start Menu shortcut;
- optional Desktop shortcut if already required;
- uninstall registration;
- application icon;
- version/publisher metadata;
- EULA display if an authoritative EULA already exists;
- bundled notices;
- deterministic file payload.

Installer must not add:

- auto-update service;
- telemetry;
- background service;
- scheduled tasks;
- shell extensions;
- file association;
- privileged service;
- network dependency,

unless separately authorized.

## 8. Metadata Authority

Do not create competing version/product-name authorities.

Prefer existing authoritative sources such as project package/version metadata.

Any installer-specific metadata may mirror authoritative values but must be verified against them.

## 9. Reproducibility

A release build must be runnable from a documented clean-build procedure.

The build process should not depend on:

- untracked personal files;
- stale `.venv` package copies;
- developer-specific absolute paths;
- manual edits inside generated `dist/`;
- previously generated binaries.

## 10. Governance

### G0 — autonomous

- generated-file cleanup inside dedicated build output directories;
- bundler flag tuning;
- installer text spacing;
- harmless icon/resource path correction;
- test harness adjustments;
- packaging-only metadata formatting.

### G1 — bounded WP

- `.spec` changes;
- packaging scripts;
- installer scripts;
- runtime hooks;
- resource collection;
- installer payload layout;
- packaged-runtime fixes that do not alter product semantics.

### G2 — mandatory stop

STOP if work requires:

- changing ConversionRequest/Result/Service semantics;
- changing Core/Canonical/QA/Golden;
- changing CLI/public API semantics;
- changing output naming/path semantics;
- adding network/telemetry/update behavior;
- adding privileged services;
- changing privacy architecture;
- changing licensing model;
- weakening accepted GUI lifecycle behavior.

## 11. Testing Strategy

WPs 01–04 use focused packaging tests only.

WP-05 performs real packaged/installed Windows runtime smoke.

WP-06 performs clean-build/reproducibility/artifact checks.

WP-07 performs the final consolidated verification once.

Do not run full source-tree regression after every installer or bundler edit.

## 12. Exit Criteria

P12-08 closes only when:

```text
packaged Windows executable builds PASS
packaged GUI startup PASS
real conversion from packaged app PASS
installer install PASS
installed launch PASS
uninstall PASS
settings persistence PASS
Open Document/Open Folder PASS
cp1252 packaged-environment verification PASS
resource/version metadata PASS
clean-build/rebuild PASS
artifact inventory PASS
introduced source regression failures = 0
Core/Canonical/QA/Golden semantic drift = 0
CLI/public API breaking changes = 0
open release blockers = 0
```

Next phase after closure:

**P12-09 — Verification**
