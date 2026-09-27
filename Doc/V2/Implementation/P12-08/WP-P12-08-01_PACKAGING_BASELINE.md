# WP-P12-08-01 — Packaging Baseline

**Product Baseline SHA:** `1b040c5d0d19f16be127cf3060fb573005a69c81`  
**Authority:** G1 bounded  
**Purpose:** inspect, normalize and freeze the packaging contract before changing build outputs.

## Objective

Identify the existing packaging assets and define the exact Windows packaging path that will be used for P12-08.

## Required Inspection

Inspect only packaging-relevant assets, including where present:

- `MD_Converter.spec`
- `MD_Converter_Lite.spec`
- `packaging/`
- installer scripts/config
- `pyproject.toml`
- GUI entry point
- product icon/resources
- `EULA.txt`
- `THIRD_PARTY_NOTICES.txt`
- existing `dist/` / `dist_installer/` only as historical evidence, not as authority
- build helper scripts

## Required Decisions

Record:

- accepted GUI entry point;
- accepted bundler;
- accepted installer technology already present in repository, if usable;
- expected executable name;
- expected install directory strategy;
- authoritative product version source;
- icon/resource source;
- required licence/notices payload;
- expected build output directories;
- excluded developer/test assets.

## Rules

Do not modify product semantics.

Do not make generated `dist/` artifacts authoritative.

Do not rely on the stale non-editable package copy in `.venv`.

Do not add a second packaging stack if the existing one is fit for purpose.

## Deliverable

Create/update a concise packaging baseline section in the WP completion evidence.

Production packaging code/config changes should be minimal and only if inspection proves a baseline correction is required.

## Verification

Focused checks only:

- entry point imports;
- version metadata resolves;
- resource paths exist;
- spec/config parses;
- installer source config is identifiable;
- no direct GUI → Core packaging bypass.

## Stop Conditions

STOP if:

- no viable Windows packaging path exists without architectural changes;
- accepted GUI entry point cannot be packaged without semantic changes;
- installer choice would require new privileged/network services.

## Completion

Return files inspected/changed, accepted packaging stack, entry point, metadata authority, artifact layout, focused checks and blockers.
