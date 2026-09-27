# WP-P12-09-02 — Functional Acceptance

**Product Baseline:** `38614c7`  
**Prerequisite:** WP-P12-09-01 CLOSED

## Objective

Independently verify the user-visible v2.0 workflow against the installed/release-candidate product.

## Required Functional Paths

### Input
- Select Markdown file
- Drag/drop Markdown
- Invalid/non-Markdown input fails safely
- Missing/stale source fails safely

### Conversion
Verify:

```text
GUI → GuiWorker → ConversionService → Canonical Core → DOCX
```

Use representative real Markdown inputs including simple content, headings/lists/tables, Unicode/non-ASCII, and one richer rendering case already supported by the product.

### States
Verify only the frozen states:

```text
EMPTY
READY
CONVERTING
SUCCESS
SUCCESS_WITH_WARNING
FAILED
```

### Result UX
Verify success, warning, failure, report/details, retained diagnostics evidence, and no second QA interpretation.

### Output Actions
Verify:

- persistent artifact exists;
- Open Document launcher accepts;
- artifact remains present;
- Microsoft Word actually opens/reads expected file;
- Open Folder targets expected directory;
- missing artifact fails closed;
- retained result path remains authority.

### Settings / About
Verify Save/Cancel/Reset, persistence across restart, About version, frozen product positioning, local/private wording.

## Test Policy

Use the smallest representative matrix covering requirements.
Do not repeat full regression here.

## Acceptance

All required user-visible functional paths PASS and no release blocker remains.
