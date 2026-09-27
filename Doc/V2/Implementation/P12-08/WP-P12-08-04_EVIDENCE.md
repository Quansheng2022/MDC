# WP-P12-08-04 — Product Metadata / Notices / Resources — Completion Evidence

**Product Baseline SHA:** `1b040c5d0d19f16be127cf3060fb573005a69c81`
**Specification Baseline SHA:** `f6a12779303816ad4f9f1cfebce700cbc8f76ace`
**Input commit:** `21f8d7b` (WP-P12-08-03 add Windows installer)
**Authority:** G1 bounded packaging work

## Report record

| Field | Value |
|---|---|
| WP | WP-P12-08-04 — Product Metadata / Notices / Resources |
| Status | PASS |
| Input baseline SHA | `21f8d7b` |
| Output commit SHA | recorded by the committing run (`P12-08-04 package metadata notices and resources`) |
| Files added | `packaging/windows/pyi_support.py`, this evidence file |
| Files modified | `MD_Converter.spec`, `MD_Converter_Lite.spec`, `packaging/windows/MD_Converter.iss` |
| Generated artifacts | `dist/MD_Converter_Lite/` (268 files, 158.5 MB), `dist_installer/MD_Converter_v1.1.0_Setup.exe` (51,112,465 bytes), `build/*/version_info.txt` |
| Tests/checks | version consistency, notices/EULA payload, resource presence, payload hygiene, launch |
| Passed / Failed | 6 / 0 |
| Version | `1.1.0` (authoritative, mirrored everywhere) |
| Direct GUI → Core | none |
| Conversion semantic change | none |
| Core change | none |
| Golden change | none |
| CLI/public API change | none |
| Scope deviation | none |
| Stop condition | none |

## Version authority — single source, no drift

`pyproject.toml [project].version` remains the only version authority. The
executable resource is **generated at build time** from that value by
`packaging/windows/pyi_support.py`, so no second version constant exists.

| Authority | Value |
|---|---|
| `pyproject.toml [project].version` | `1.1.0` |
| `md_converter.__version__` | `1.1.0` |
| GUI `product_identity.product_version()` / `product_title()` | `1.1.0` / `MD Converter 1.1.0` |
| Packaged executable `ProductVersion` / `FileVersion` | `1.1.0` / `1.1.0` |
| Installer `MyAppVersion` / `VersionInfoProductVersion` / `OutputBaseFilename` | `1.1.0` / `1.1.0` / `MD_Converter_v1.1.0_Setup` |
| Installed executable metadata | `ProductName=MD Converter`, `ProductVersion=1.1.0`, `CompanyName=Quansheng2022` |
| Installed uninstall registration | `MD Converter 1.1.0` / `1.1.0` |

## Executable metadata wiring (new)

Both specs now pass a generated `version=` resource to `EXE(...)`:

```text
ProductName      MD Converter
FileDescription  Markdown to Microsoft Word DOCX Converter
FileVersion      1.1.0
ProductVersion   1.1.0
CompanyName      Quansheng2022
LegalCopyright   Copyright (C) 2026 Quansheng2022
OriginalFilename MD_Converter_Lite.exe / MD_Converter.exe
```

Before this WP the packaged executable carried no version resource
(`ProductVersion`/`FileDescription` empty), so Windows showed no product
identity in file properties.

## Notices and EULA payload (new)

`packaging/windows/MD_Converter.iss` now installs the authoritative
repository-root documents next to the application:

```text
{app}\THIRD_PARTY_NOTICES.txt   (10,759 bytes, authoritative notices file)
{app}\EULA.txt                  (713 bytes, authoritative EULA)
```

No second notices or EULA source was created; the installer also continues to
display `EULA.txt` through `LicenseFile`.

## Payload hygiene (new)

`collect_data_files('md_converter')` was pulling development material into the
payload. `pyi_support.strip_development_material()` now removes it:

| Removed from payload | Count |
|---|---|
| `md_converter/tests/**` (acceptance corpus, golden samples, fixtures) | 23 files |
| `md_converter/.gitignore` | 1 file |

Remaining `md_converter` package data - the only runtime resources:

```text
md_converter/py.typed
md_converter/renderer/themes/default_v1_5.yaml
```

Payload total: 268 files / 158.5 MB (was 292 files / 158.6 MB).

Qt plugins/resources required at runtime remain present, and the packaged GUI
was re-verified to start after the change.

## Icon

`WP-P12-08-01` found no authoritative custom icon, and this WP did not create
one: **custom icon = deferred / unavailable (non-blocking)**. The executable and
installer therefore use the default platform/toolchain icons. No branding was
invented.

## Verification

| # | Check | Result |
|---|---|---|
| 1 | Version consistency across pyproject / `__version__` / About / executable resource / installer / uninstall registry | PASS (all `1.1.0`) |
| 2 | Notices included in the installed payload | PASS (`{app}\THIRD_PARTY_NOTICES.txt`, byte size 10,759) |
| 3 | EULA included as specified (installer `LicenseFile` + installed copy) | PASS (`{app}\EULA.txt`, byte size 713) |
| 4 | Required runtime assets present (`py.typed`, theme YAML, Qt platform plugins) | PASS (see payload listing) |
| 5 | Unnecessary development material reduced | PASS (23 test data files + `.gitignore` removed; no `.git`, `.venv`, caches, review packages or historical builds in the payload) |
| 6 | No developer absolute-path dependency / installed app still launches | PASS (no repository path in payload text files; installed `MD_Converter.exe` launched with window title "MD Converter") |

## Notes for later work packages

* The version resource file is regenerated on every build under
  `build/<profile>/version_info.txt`; it is a build artifact, not a source of
  authority.
* WP-P12-08-06 rebuilds `build/`, `dist/` and `dist_installer/` from clean and
  records the final hashes.
