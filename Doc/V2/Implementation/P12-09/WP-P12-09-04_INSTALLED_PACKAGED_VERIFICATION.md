# WP-P12-09-04 — Installed / Packaged Verification

**Product Baseline:** `38614c7`

## Objective

Independently re-verify the release candidate in the actual installed Windows environment.

## Installation

Verify:

- installer launches and completes;
- expected install directory;
- Start Menu launch;
- no unexpected elevation/service/network setup;
- version metadata correct.

## Installed Runtime

Verify:

- clean launch;
- real conversion;
- output artifact;
- clean close;
- worker-active close protection.

## Settings

Verify persistence:

```text
launch → modify/save → close → restart → restore
```

## Paths

Cover normal path, path with spaces, non-ASCII path where practical, and launch independent from repository/current working directory.

## Output Actions

Use a persistent artifact and record separately:

```text
artifact exists before launch
launcher accepted
artifact remains present
Word actual open/read
```

Open Folder must target expected directory.
Missing artifact must fail closed.

## Encoding

Independently reconfirm P12-08 cp1252 CASE A in the installed candidate.

Do not use developer-shell `PYTHONIOENCODING=utf-8` as proof.

## Uninstall

Verify uninstall succeeds, installed payload is removed, user documents are preserved, and unrelated files are not deleted.

## Acceptance

Installed/runtime/install/uninstall behavior PASS with no release blocker.
