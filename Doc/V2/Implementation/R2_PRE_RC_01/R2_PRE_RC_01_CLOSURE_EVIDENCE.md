# R2-PRE-RC-01 — Final Inno Setup Wrapper Rebuild & Installer Verification
## Closure Evidence

**Program:** R2-PRE-RC-01 (pre-RC release-engineering gate after P12-22 / R2-V04)
**Release train:** R2 — Competitive Foundation
**Change classification:** `G2_OR_RELEASE` — release engineering and verification only
**Governing SPEC:** `CANONICAL_SPEC.md` (FROZEN 1.1) — `SPEC-GOAL-003`,
`SPEC-ARCH-007`, `SPEC-INV-001`, `SPEC-INV-006`, `SPEC-INV-007`, `SPEC-QA-002`
**Upstream gates:** R2-V01 / R2-V02 / R2-V03 / R2-V04 all CLOSED / ACCEPTED
**Work packages:** 3 / 3 PASS
**Final status:** `R2-PRE-RC-01 — CLOSED / ACCEPTED / FINAL INSTALLER RELEASE-ENGINEERING PASS`

## 1. Accepted product baseline

- Branch: `master`
- HEAD at gate start: `1ff46215f17c068b7f8b79a0ee75faf25bbaf595` (`R2V04-02 verify golden browser retest and close gate`)
- Accepted upstream state: R2-V01 / R2-V02 / R2-V03 / R2-V04 CLOSED / ACCEPTED
- Authoritative product version: `1.1.0` — `pyproject.toml` `[project].version`, the packaged executable version resource, and `.iss` `MyAppVersion` all agree
- Published identity: `AppId=MDConverter.Quansheng2022`, `AppName=MD Converter`, publisher `Quansheng2022`
- Installer script: `packaging/windows/MD_Converter.iss`, SHA-256 `EBB0979972348ECA2926BC3095049BDB047B36F206E9D66E2A1C7E468B91CE03`
- Product version decision made by this gate: none — existing authority was used unchanged

## 2. Final packaged payload identity

- Payload directory: `dist\MD_Converter_Lite`
- Packaged executable: `dist\MD_Converter_Lite\MD_Converter_Lite.exe`
- Executable bytes / SHA-256: `6926650` / `68524527CDC5718CE31A1F0454EAFB0FF64C52D5C838716AC1277445DE0E3021`
- Payload files / total bytes: `268` / `166231301`
- Payload tree digest SHA-256: `ecb6a4453f342af51cbc2b26b175489cb4ad963bc987a7407ff10ff0f8efa96c`
- Executable version resource: FileVersion `1.1.0`, ProductVersion `1.1.0`, ProductName `MD Converter`, CompanyName `Quansheng2022`

The executable SHA-256 equals the identity frozen and verified by the accepted
R2-V02 gate, so the final wrapper wraps the accepted R2 payload unchanged. The
previously existing installer
(`EFEC378F11B00A53791158199B4DC98AA09F44F5B1F013363FF744A92B91B9BF`, built
2026-09-27) wrapped the older P12-10 RC1 payload and was correctly superseded.

## 3. Build tool

- Compiler: official Inno Setup command-line compiler `ISCC.exe`
- Version: `Inno Setup 7.1.0` (`jrsoftware.org`; registry DisplayName `Inno Setup 7.1.0`)
- Path: `C:\Users\Quansheng\AppData\Local\Programs\Inno Setup 7\ISCC.exe`
- Install scope: per-user; already present on the host — nothing was installed, downloaded or upgraded by this gate
- Compiler engine banner: `Compiler engine version: Inno Setup 7.1.0`

No third-party compiler, no installer-technology replacement, no ACL/UAC or
security-policy change, and no new product dependency was introduced.

## 4. Final installer identity

- Installer filename: `MD_Converter_v1.1.0_Setup.exe`
- Absolute path: `C:\Users\Quansheng\Documents\projects\MD_Converter\dist_installer\MD_Converter_v1.1.0_Setup.exe`
- File size: `51186717` bytes
- SHA-256: `4B56FC989BAB7FF7E648CC29DFE5A6D944B2B8EFC420F11DE8D0ECF8294FFDE9`
- Build timestamp: `2026-09-30T23:25:46+08:00`
- Compiler result: `Successful compile (30.578 sec)`, exit code `0`
- Visible metadata: FileVersion `1.1.0.0`, ProductVersion `1.1.0`, ProductName `MD Converter`, CompanyName `Quansheng2022`, FileDescription `Markdown to Microsoft Word DOCX Converter`, LegalCopyright `Copyright © 2026 Quansheng2022`
- Signing: none — matches the recorded P12-10 known release condition; no new signing requirement was invented

Artifact retention: `dist_installer/` is not tracked by this repository's release
process, so the binary stays out of Git and is identified by path, size and
SHA-256 in the evidence instead.

## 5. Commit chain (3 commits, exact-file staging only)

1. `2fc83f2` — `R2PRERC01-01 freeze final installer payload and build environment`
   (WP-01 evidence `.md`, payload identity `.json`, payload identity script)
2. `7ac0a2c` — `R2PRERC01-02 build final Inno Setup installer`
   (WP-02 evidence `.md`, installer identity `.json`, installer identity script)
3. this commit — `R2PRERC01-03 verify final installer lifecycle and close gate`
   (this closure, `Evidence/WP-R2PRERC01-03_LIFECYCLE_RESULT.json`,
   `Evidence/lifecycle/*`, lifecycle script, two fixture documents)

No `git add .` / `git add -A` / `git clean -fd` / `git reset --hard` /
`git restore .` was used. The pre-existing dirty state (`.gitignore`, `README.md`,
`md_converter/cli.py`, plus the untracked/dirty tree inherited from earlier
programs) was preserved and never staged.

## 6. Install lifecycle results

The lifecycle was driven by `Verification/r2prerc01_lifecycle.ps1` against the
**final rebuilt installer**. Raw per-phase observations are in
`Evidence/lifecycle/`; the consolidated record is
`Evidence/WP-R2PRERC01-03_LIFECYCLE_RESULT.json`.

### 6.1 Clean install

- Pre-existing copy-deployed install directory removed for a genuinely clean state: PASS
- Installer exit code: `0`
- Install directory `%LOCALAPPDATA%\Programs\MD_Converter` created: PASS
- `MD_Converter.exe` present and byte-identical to the accepted payload (`68524527…`): PASS
- `_internal\` runtime payload present: PASS (267 files)
- `EULA.txt` and `THIRD_PARTY_NOTICES.txt` installed: PASS
- Start Menu group with four shortcuts — `MD Converter`, `MD Converter - Input Folder`, `MD Converter - Output Folder`, `Uninstall MD Converter`: PASS
- Desktop shortcut absent: PASS (declared `unchecked` in the frozen `.iss`)
- Uninstall registration — `MD Converter 1.1.0`, publisher `Quansheng2022`, correct `DisplayIcon` and `UninstallString`: PASS
- User workspace `Documents\MD_Converter\{input,output}` created: PASS

### 6.2 Launch and conversion

- Installed application launches; main window `MD Converter` visible: PASS
- About dialog reports `Version 1.1.0`: PASS
- Runtime independence — `PYTHONPATH` unset, repository and `.venv` absent from the child `PATH`, and **0** loaded modules from the repository or `.venv`: PASS
- Clean close: PASS
- Representative conversion through the real GUI path (`GUI → GuiWorker → ConversionService → Canonical Core`): PASS — `SUCCESS` in 9.5 s
- Produced artifact: `output\MD_Converter_R2_Pre-RC_Installer_Verification.docx`, 31 396 B, SHA-256 `C3827F128D686DD6EBEB3EABC3848757EA332302795F0CEF2AAB97BB1EE28530`, valid DOCX
- Output location and naming: PASS — written under the neutral working directory's `output\`, named from the frontmatter title

### 6.3 Uninstall

- Uninstaller exit code: `0`
- Installed executable and `_internal` payload removed: PASS
- Start Menu group removed: PASS
- Uninstall registration removed: PASS
- Application PATH entry and installer PATH marker: PASS — see section 7
- User workspace `Documents\MD_Converter` preserved: PASS
- User-generated DOCX artifacts not destructively touched: PASS

### 6.4 Reinstall and post-reinstall smoke

- Same final installer reinstalls (exit code `0`): PASS
- Installed executable again byte-identical to the accepted payload: PASS
- Uninstall registration re-created: PASS
- Post-reinstall launch and short conversion smoke: PASS — `SUCCESS` in 4.8 s, `output\short.docx`, 29 496 B, SHA-256 `629DBBD1DA2A0ED628E61B03CFB24BB40AF7C681E578B43044F62DD0BA4AE6E5`, valid DOCX
- Operational end state: installed, launchable, uninstallable

## 7. PATH semantics observation (correct behaviour, not a defect)

The machine already carried `%LOCALAPPDATA%\Programs\MD_Converter` in the user
`PATH` **before** this gate (left by the earlier P12-10 installer run), and there
was no installer PATH marker. The frozen `.iss` contract is explicit: the
installer adds `{app}` only when absent, and removes it on uninstall **only if
this installer added it**.

Observed behaviour matches that contract exactly:

- Install log line: `MD Converter PATH entry already exists: …\Programs\MD_Converter`
- PATH marker written: no (`PathAddedByInstaller` absent both before and after)
- User `PATH` length before the gate / before uninstall / after uninstall: 933 / 933 / 933 characters, byte-identical
- Uninstall behaviour: no installer PATH marker, so PATH was not modified
- Installer-owned PATH cleanup logic: not exercised in this environment; the guard behaviour observed is the frozen, intended semantics

The install/uninstall cycle is therefore PATH-neutral with respect to whatever
preceded it, which is the stronger guarantee. Classified **not a defect**.

## 8. Corrections applied

- Bounded G1 packaging corrections: `0` — the frozen `.iss` resolved the accepted payload without change
- Product runtime source changes: `0`
- Installer rebuilds beyond the single final build: `0`
- Verification-harness fixes during the gate: `2` — a `PYTHONPATH` guard comparison and the frontmatter-title output-name expectation; both are evidence tooling only and touched no product file

## 9. Gate counters

- Clean install: required PASS, actual `PASS`
- Launch and representative conversion: required PASS, actual `PASS`
- Uninstall: required PASS, actual `PASS`
- Reinstall: required PASS, actual `PASS`
- Post-reinstall smoke: required PASS, actual `PASS`
- Introduced installer failures: required 0, actual `0`
- Unresolved pre-RC installer blockers: required 0, actual `0`
- Product runtime source drift introduced: required 0, actual `0` (only the inherited, untouched `md_converter/cli.py` 2/2 hunk)
- Golden baseline changed: required NO, actual `NO` — `md_converter/tests/golden/sample.expected.json` is `6D589013B8024C158DE5D29B93BDFEF68F2F406045C805DAB61F8E513725829A`
- R2-V01 / R2-V02 / R2-V03 / R2-V04 re-runs: required 0, actual `0`
- Signing requirement introduced: no

Failure classification per the product specification: `PASS`.

## 10. Definition of Done

- accepted payload identity frozen ✓
- official Inno Setup compiler identified (`Inno Setup 7.1.0`) ✓
- final installer built ✓
- installer SHA-256 and build metadata recorded ✓
- product runtime source drift = 0 ✓
- clean install PASS ✓
- installed executable corresponds to the accepted payload ✓
- launch and representative conversion PASS ✓
- uninstall PASS ✓
- reinstall PASS ✓
- post-reinstall smoke PASS ✓
- introduced installer failures = 0 ✓
- unresolved pre-RC installer blockers = 0 ✓
- three truthful commits ✓
- R2-RC not started ✓

## 11. Outstanding items after this gate

- R2 Release Candidate freeze: not started (correctly out of scope)
- README-packaging test failures (`test_packaging_metadata.py`, pre-existing dirty `README.md`): pre-existing, unrelated, unrepaired
- Host console `cp1252` non-ASCII diagnostic observation: pre-existing, recorded by R2-V04, unchanged
- Code signing of installer and executable: still not part of the frozen release process; unchanged

## 12. Final recommendation

The last known release-engineering debt before the R2 Release Candidate is
removed. The final Inno Setup wrapper is built from the accepted R2 payload with
unchanged product and version metadata, and it has proven a complete real-machine
lifecycle: clean install, launch, representative Markdown to DOCX conversion,
uninstall, reinstall and post-reinstall conversion, with zero introduced
failures, zero product-source drift and no Golden-baseline change.

The project is eligible to proceed to the R2 Release Candidate freeze. This gate
does not start it.

`R2-PRE-RC-01 — CLOSED / ACCEPTED / FINAL INSTALLER RELEASE-ENGINEERING PASS`
