# WP-P12-08-03 — Windows Installer

**Product Baseline SHA:** `1b040c5d0d19f16be127cf3060fb573005a69c81`  
**Prerequisite:** WP-P12-08-02 CLOSED  
**Authority:** G1 bounded

## Objective

Create a bounded Windows installer for the accepted packaged application.

## Required Installer Capabilities

- install accepted application payload;
- create Start Menu launch entry;
- expose normal uninstall through Windows application management;
- install application icon/resources;
- preserve product version/name/publisher metadata;
- optionally create Desktop shortcut only if already required by current product/release specification;
- present authoritative EULA if the chosen installer flow already supports it and the repository EULA is authoritative.

## Explicitly Out of Scope

Do not add:

- updater service;
- telemetry;
- background process;
- scheduled task;
- shell extension;
- file association;
- autostart;
- system service;
- firewall rule;
- network dependency.

## Install Location

Use a conventional per-user or machine-wide location consistent with the chosen installer technology and existing repository design.

Do not introduce elevation unless genuinely required by the accepted installer design.

## Required Verification

On Windows:

1. installer starts;
2. installation completes;
3. installed files match expected payload;
4. Start Menu launch works;
5. application starts;
6. application can be uninstalled;
7. uninstall removes installed payload owned by the product;
8. user documents/output are not deleted by uninstall;
9. uninstall does not remove unrelated settings/files.

## Stop Conditions

STOP if installer requires privileged services, semantic product changes, or an unapproved licensing/update mechanism.
