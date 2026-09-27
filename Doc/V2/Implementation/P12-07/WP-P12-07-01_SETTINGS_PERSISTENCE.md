# WP-P12-07-01 — Settings / Persistence

**Product Baseline SHA:** `f3b4e3d5d15d7b95f20fea19515e2e49d8f3e44e`  
**Authority:** G1 bounded.

## Objective
Create the smallest GUI-local preference model and persistence boundary.

Preferred:
```text
GUI → GuiPreferences → QSettings
```

## Authorized Preferences
- window geometry/size
- last source directory
- last output directory
- optional remember-folders toggle
- reset to defaults

## Rules
- first launch safely uses defaults
- saved values persist across GUI instances
- remembered folders only affect GUI convenience
- no change to `ConversionService` defaults
- invalid/off-screen geometry fails safely
- reset affects GUI preferences only

## Preferred Files
- `md_converter/gui/preferences.py`
- `md_converter/tests/gui/test_preferences.py`

MainWindow changes only as necessary.

## Forbidden
No global ConfigManager, YAML/JSON settings framework, conversion options, filename rules, QA settings, theme system, cloud/account settings, packaging work.

## Tests
Defaults, round-trip, persistence, reset, folder behavior, geometry behavior, test isolation, application Qt-free, no conversion semantic changes.

## Acceptance
Focused tests PASS; Application Qt dependency=0; Core/Golden/CLI changes=0.

## Stop
Stop if persistence requires Application/Core semantic change or generalized configuration architecture.
