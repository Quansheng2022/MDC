# R2 Release Candidate — Freeze Manifest

**RC identifier:** `MD Converter v1.1.0 R2-RC` — evidence-only label (no Git tag; see §11)
**RC build label:** `RC-20261001-R2`
**P12 mapping:** P12-23
**Release train:** R2 — Competitive Foundation
**Change classification:** `G2_OR_RELEASE` — RC identity freeze and handoff gate
**Governing SPEC:** `CANONICAL_SPEC.md` (FROZEN 1.1) — `SPEC-GOAL-003`, `SPEC-INV-001`,
`SPEC-INV-006`, `SPEC-INV-010`, `SPEC-INV-012`, `SPEC-QA-002`
**Created by:** WP-R2RC-01 (`Evidence/WP-R2RC-01_RC_IDENTITY_EVIDENCE.md`)
**Closed by:** WP-R2RC-02 (`R2_RC_CLOSURE_EVIDENCE.md`)
**Freeze-time HEAD:** `286fdd6b61a5b1603a3a00d9508f44564f6a1635`
**Status:** `R2-RC — FROZEN / ACCEPTED / READY FOR HUMAN ACCEPTANCE`

This manifest binds one unambiguous candidate: the accepted R2 product baseline, the
accepted packaged payload, the accepted final installer, the accepted verification chain and
the accepted limitations. It is the canonical RC record; full per-gate evidence is referenced,
not duplicated.

---

## 1. RC product / version identity

| Item | Value |
|---|---|
| Product name | `MD Converter` |
| Product version | `1.1.0` |
| Publisher | `Quansheng2022` |
| Application id (Inno Setup `MyAppId`) | `MDConverter.Quansheng2022` |
| Packaged executable metadata | FileVersion `1.1.0`, ProductVersion `1.1.0`, ProductName `MD Converter`, CompanyName `Quansheng2022` |
| Installer metadata | FileVersion `1.1.0.0`, ProductVersion `1.1.0`, ProductName `MD Converter`, CompanyName `Quansheng2022` |

Authoritative version sources (all agree on `1.1.0`):

| Source | Value |
|---|---|
| `pyproject.toml` `[project].version` | `1.1.0` |
| `md_converter/__init__.py` `__version__` | `1.1.0` |
| Packaged executable version resource | `1.1.0` |
| `packaging/windows/MD_Converter.iss` `MyAppVersion` | `1.1.0` |

Version decision made by this gate: **none**. Existing authority was used unchanged, exactly as
recorded by R2-PRE-RC-01 §1. No release-version decision is authorized by R2-RC (`G2` if pursued).

Note: the version string `1.1.0` is shared with the earlier, already tagged `v1.1.0` production
release (annotated tag at `e025a36`). This RC is therefore distinguished by **manifest +
closure commit + artifact hashes**, not by a new version string. See §11.

## 2. Source / product baseline identity

| Item | Value |
|---|---|
| Branch | `master` |
| Freeze-time HEAD | `286fdd6b61a5b1603a3a00d9508f44564f6a1635` (`R2PRERC01-03 verify final installer lifecycle and close gate`) |
| Last product-source commit | `bd1a818` (`IC-04 guard image width configuration contract`) |
| Accepted source baseline | R2-V01 closure `1e1cfc7062736a687147e642442677d24144204f` |
| Product runtime source drift caused by R2-RC | `0` |
| Golden baseline drift caused by R2-RC | `0` |
| Installer drift | `0` |

Artifact identity is anchored on the frozen payload/installer bytes and the accepted gate chain.
The frozen wrapper replaces an earlier installer built 2026-09-27 from the pre-R2 payload; that
earlier installer was correctly superseded by R2-PRE-RC-01 and is not part of this RC.

Inherited, pre-existing working-tree state — present before this task, preserved untouched, and
**never staged**: `.gitignore`, `README.md`, `md_converter/cli.py` (docstring-only, 2/2 hunk), plus
the unstaged relocation of the R2-V01 / R2-V02 evidence trees under `Doc/V2/Implementation/`. None
of these was produced by R2-RC; see §12.

## 3. Packaged payload identity

| Item | Value |
|---|---|
| Payload directory | `dist\MD_Converter_Lite` |
| Packaged executable | `dist\MD_Converter_Lite\MD_Converter_Lite.exe` |
| Executable bytes | `6926650` |
| Executable SHA-256 | `68524527CDC5718CE31A1F0454EAFB0FF64C52D5C838716AC1277445DE0E3021` |
| Payload files | `268` |
| Payload total bytes | `166231301` |
| Payload tree digest (SHA-256 over sorted `<path> <size> <sha256>` lines) | `ecb6a4453f342af51cbc2b26b175489cb4ad963bc987a7407ff10ff0f8efa96c` |

The executable SHA-256 is identical to the identity frozen by R2-V02 (WP-01) and re-confirmed by
R2-V03 and R2-PRE-RC-01: the final wrapper wraps the accepted R2 payload unchanged. The payload is
retained outside Git and is identified by path, size and SHA-256.

## 4. Final installer identity

| Item | Value |
|---|---|
| Filename | `MD_Converter_v1.1.0_Setup.exe` |
| Absolute path | `C:\Users\Quansheng\Documents\projects\MD_Converter\dist_installer\MD_Converter_v1.1.0_Setup.exe` |
| File size | `51186717` bytes |
| SHA-256 | `4B56FC989BAB7FF7E648CC29DFE5A6D944B2B8EFC420F11DE8D0ECF8294FFDE9` |
| Build timestamp | `2026-09-30T23:25:46+08:00` |
| Compiler | Inno Setup command-line compiler `ISCC.exe`, `Inno Setup 7.1.0` |
| Installer script | `packaging/windows/MD_Converter.iss`, SHA-256 `EBB0979972348ECA2926BC3095049BDB047B36F206E9D66E2A1C7E468B91CE03` |
| Signing | none — recorded P12-10 / R2-PRE-RC-01 release condition, unchanged |

This is the installer already accepted by R2-PRE-RC-01. It was **not** rebuilt, patched or copied
by R2-RC. `dist_installer/` is not tracked by this repository's release process, so the binary
stays out of Git and is identified by path, size and SHA-256.

## 5. Accepted gate chain

| Gate | Closure commit | Status |
|---|---|---|
| R2-V01 Competitive Foundation Integrated Verification | `1e1cfc7062736a687147e642442677d24144204f` | CLOSED / ACCEPTED |
| R2-V02 Packaged Multi-file Runtime Verification | `93d7cbde1302c60b25206cba1288f4b751e77860` | CLOSED / ACCEPTED |
| R2-V03 Native Word Visual Verification | `39c5f53eefef9592da5f5a62bb98d235c7025aca` | CLOSED / ACCEPTED |
| R2-V04 Golden / Browser Environment Retest | `1ff46215f17c068b7f8b79a0ee75faf25bbaf595` | CLOSED / ACCEPTED |
| R2-PRE-RC-01 Final Inno Setup Wrapper Rebuild & Installer Verification | `286fdd6b61a5b1603a3a00d9508f44564f6a1635` | CLOSED / ACCEPTED |

Closure-evidence paths (resolvable in Git at the closure commit above; the R2-V01 / R2-V02 trees
were later relocated in the unstaged working tree — see §12):

```text
Doc/V2/Implementation/R2_V01/R2_V01_CLOSURE_EVIDENCE.md
Doc/V2/Implementation/R2_V02/R2_V02_CLOSURE_EVIDENCE.md
Doc/V2/Implementation/R2_V03/R2_V03_CLOSURE_EVIDENCE.md
Doc/V2/Implementation/R2_V04/R2_V04_CLOSURE_EVIDENCE.md
Doc/V2/Implementation/R2_PRE_RC_01/R2_PRE_RC_01_CLOSURE_EVIDENCE.md
```

Supporting identity records:

```text
Doc/V2/Implementation/R2_PRE_RC_01/Evidence/WP-R2PRERC01-01_PAYLOAD_IDENTITY.json
Doc/V2/Implementation/R2_PRE_RC_01/Evidence/WP-R2PRERC01-02_INSTALLER_IDENTITY.json
Doc/V2/Implementation/R2_PRE_RC_01/Evidence/WP-R2PRERC01-03_LIFECYCLE_RESULT.json
Doc/V2/Implementation/P12-10/RC_MANIFEST.md
```

Gate status is complete and consistent; no upstream gate is treated as open or re-run by R2-RC.

## 6. User-visible R2 feature summary (already accepted — no new claims)

| Capability | Accepted result | Source |
|---|---|---|
| Serial Batch Conversion | PASS — strict serial (`active_conversion_count = 1`), ordered queue, per-file results, failure isolation, derived summary counts | R2-V01 WP-04, R2-V02 WP-02 |
| Document Intelligence / conversion report | PASS — real diagnostics and warnings surfaced with accurate counts | R2-V01 WP-05 |
| Professional Output Profiles | PASS — five profiles (`professional_report`, `business_report`, `academic`, `technical`, `clean_minimal`) verified inside the package | R2-V01 WP-03/04, R2-V02 WP-03 |
| TOC Heading Localization | PASS — English / Chinese / mixed, single localization authority, native TOC field intact | R2-V01 WP-03, R2-V02 WP-03, R2-V03 §7 |
| Advanced Table Fitting | PASS — fixed layout, column floor, total inside the profile content width, no cell mutation, irreducible case classified | R2-V01 WP-03, R2-V02 WP-03 |
| Advanced Figure Fitting | PASS — aspect ratio preserved, contained in the usable page body, page-height cap exercised | R2-V01 WP-03, R2-V02 WP-03, R2-V03 §7 |
| `image_width` configuration propagation (IMG-CFG-01) | PASS — respected and capped by the content width | R2-V01 WP-03, R2-V02 WP-03 |
| Packaged runtime and installer readiness | PASS — install, launch, representative conversion, uninstall, reinstall and post-reinstall smoke on the final installer | R2-V02, R2-PRE-RC-01 §6 |

## 7. Known accepted limitations / deferred debt

Populated only from already recorded, already accepted evidence. Nothing here is reclassified,
reopened or newly discovered.

| # | Limitation / deferred debt | Status as accepted | Source |
|---|---|---|---|
| L1 | CLI reaches the Canonical Core directly instead of through `ConversionService` (documented "Step C") | deferred, `G2`-class, out of R2 scope | R2-V01 §11 |
| L2 | Data-URI picture `name` uses a per-run temporary stem (sizing decisions remain deterministic; file-image path is byte-identical) | accepted observation | R2-V01 §11 |
| L3 | DOCX twips quantization (~0.002 cm) | accepted format property, not a fitting defect | R2-V01 §11 |
| L4 | Console-attached Windows launch under `cp1252` stdout makes the Word-COM TOC refresh fail with `UnicodeEncodeError` while `print()`ing emoji diagnostics in `md_converter/renderer/post_processor.py`; the DOCX is still written but the conversion is reported as not-clean | `PRE_EXISTING_KNOWN_LIMITATION` — reproduced only by that launch mode | R2-V02 §9, R2-V04 §7, R2-PRE-RC-01 §11 |
| L5 | The packaged desktop surface exposes no `image_width` control, so the runtime target is the frozen default (5 in → 12.70 cm) | accepted observation (source-level override/cap behaviour verified in R2-V01) | R2-V02 §9 |
| L6 | Chromium / Golden checks require an execution context that permits spawning the installed browser | execution-context limitation, `CLOSED` by R2-V04, no product defect | R2-V04 §5 |
| L7 | Word displays `[Compatibility Mode]` because the accepted DOCX declares `compatibilityMode = 14` | already recorded; title-bar only, no usability impact | R2-V03 L1 |
| L8 | The 25-column Program D verification fixture is 29.9994 cm wide in a 29.7 cm landscape page, so its trailing columns cannot print on one page | accepted by Program D (`PASS_WITH_WARN`); no packaged R2 output exhibits it | R2-V03 L2 |
| L9 | The Program D fixture's trailing empty section renders an empty page | characteristic of that verification fixture only | R2-V03 L3 |
| L10 | The normal 3-column table's first column is 1.7092 cm, so header/cell words such as `Component` wrap onto two lines | `LATER_GATE_DEBT`; content complete and legible, not a release blocker | R2-V03 L4 |
| L11 | `test_packaging_metadata.py` (2 failures) with the pre-existing dirty `README.md` | `PRE_EXISTING_KNOWN_FAILURE`, unrelated, not repaired | R2-V01 §8, R2-V04 §9, R2-PRE-RC-01 §11 |
| L12 | Installer and executable are not code-signed | pre-existing recorded release condition; not a blocker | P12-10 §5, R2-PRE-RC-01 §11 |
| L13 | Deferred out-of-scope capabilities: true Core preflight, intrinsic no-upscale policy, landscape tables, new profiles/config/GUI settings, templates/equations/citations, PDF backend, README cleanup | out of R2 scope (installer rebuild since completed by R2-PRE-RC-01) | R2-V01 §11 |
| L14 | Release Evidence artifact (`SPEC-FUNC-021` / `SPEC-INV-010`) has not been regenerated for R2 | release-process action outside this freeze gate's authority | see §12 |

## 8. Human Acceptance scope

R2-RC does **not** perform Human Acceptance and does not claim it. The Human is asked to evaluate:

1. installation experience;
2. launch experience;
3. primary (single-file) conversion workflow;
4. batch workflow, where desired;
5. usefulness and aesthetics of the Word output;
6. overall product readiness from a user perspective.

Machine-verification gates (R2-V01 / V02 / V03 / V04 / PRE-RC-01) remain accepted and are **not**
automatically re-run. Human Acceptance is recorded in this RC as `PENDING`.

## 9. Rollback identity

Sufficient to return to the last accepted pre-RC state. No rollback was performed.

| Item | Value |
|---|---|
| Last accepted pre-RC closure commit | `286fdd6b61a5b1603a3a00d9508f44564f6a1635` (`R2-PRE-RC-01`) |
| Accepted final installer SHA-256 | `4B56FC989BAB7FF7E648CC29DFE5A6D944B2B8EFC420F11DE8D0ECF8294FFDE9` |
| Accepted packaged EXE SHA-256 | `68524527CDC5718CE31A1F0454EAFB0FF64C52D5C838716AC1277445DE0E3021` |
| Accepted payload tree digest | `ecb6a4453f342af51cbc2b26b175489cb4ad963bc987a7407ff10ff0f8efa96c` |
| Accepted Golden baseline SHA-256 | `6D589013B8024C158DE5D29B93BDFEF68F2F406045C805DAB61F8E513725829A` |

## 10. RC invalidation rules

After R2-RC closes, this candidate is immutable. It is **invalidated** by any change to a protected
release input:

```text
product runtime source
renderer / Core / QA behaviour
configuration semantics
packaged payload bytes
installer bytes
installer semantics
product / version metadata
Golden semantic baseline
```

A change to any protected input requires: (1) classify the change; (2) execute the minimum
affected verification gates; (3) rebuild the installer if the payload changed; (4) issue a new RC
identity. This RC is then marked superseded/invalidated.

Documentation or evidence produced during Human Acceptance does **not** invalidate the RC provided
the protected identities above and their hashes remain unchanged.

## 11. Git tag policy decision

Tag inventory inspected: `v1.0.0` (`e1e5060`), `v1.0.1` (`146c130`), `v1.1.0` (`9f32090`) — all
annotated release tags. **No RC tag exists in this repository**, and `git tag -l` shows no
RC-suffixed tag convention in use. P12-10 identified its earlier v1.1.0 RC by an evidence-only
label and created no tag. `Doc/V2/V2_RELEASE_PLAN.md` §5 mentions `v2.0.0-rc1` as an RC naming
example, but that is a release-plan versioning statement for version 2.0.0 (not this RC's unchanged
1.1.0 authority) and has never been exercised as a Git tag policy.

Decision: **no tag created.** Creating one would require both an authoritative tag convention and a
release-version decision (the annotated `v1.1.0` tag already identifies the earlier 1.1.0
production release); neither is authorized here. This does not block closure — the canonical freeze
anchor is the RC closure commit plus this manifest and the artifact hashes above.

## 12. Observations recorded without modification

Reported per `SPEC-INV-012` (report extra findings, do not modify outside the change plan):

1. **Release Evidence artifact (`SPEC-FUNC-021`, `SPEC-INV-010`).** The tracked root
   `RC_EVIDENCE/RELEASE_EVIDENCE.md` and `RC_EVIDENCE/release_evidence.json` describe the earlier
   **1.0.0** RC (`RC-20260901-05`); the 1.1.0 RC evidence is
   `RC_EVIDENCE/P12_v1.1.0/RELEASE_CANDIDATE_EVIDENCE.md`. Regenerating Release Evidence requires a
   compiler/QA run plus test-suite and governance inputs — precisely the reruns this freeze gate is
   forbidden to perform — and the artifact is not part of the R2-RC change plan. Recorded here as an
   observation for the release process owner; not repaired, and not treated as a blocker because the
   protected RC identities verified in §3 / §4 are unaffected.
2. **Relocated R2-V01 / R2-V02 evidence trees.** The working tree carries an unstaged relocation of
   those evidence trees into `..._Spec_Plan_Master` folders, inherited from before this task. The
   relocated closure-evidence files are byte-identical to their committed blobs; one relocated
   harness output (`WP-R2V02-01_RESULT.json`) is not byte-identical to its committed blob. The
   authoritative records remain the Git blobs at the gate closure commits listed in §5.
3. **Pre-existing dirty tracked files** (`.gitignore`, `README.md`, `md_converter/cli.py`) — inherited
   from before R2-V01, preserved untouched, never staged by R2-RC.

## 13. Acceptance criteria (`R2_RC_Product_Specification.md` §13)

| Criterion | Status |
|---|---|
| One canonical RC manifest exists | PASS — this file |
| Source / product baseline identity unambiguous | PASS — §2 |
| Packaged EXE identity matches accepted PRE-RC evidence | PASS — §3 |
| Final installer identity matches accepted PRE-RC evidence | PASS — §4 |
| Accepted gate chain complete and consistent | PASS — §5 |
| Known limitations recorded without expansion | PASS — §7 |
| Rollback identity recorded | PASS — §9 |
| Protected-input invalidation rules explicit | PASS — §10 |
| Product source drift = 0 | PASS — no R2-RC change (§2) |
| Installer drift = 0 | PASS — §4 |
| Golden baseline drift = 0 | PASS — §9 / WP-01 evidence |
| Unresolved RC identity mismatches = 0 | PASS — WP-01 evidence |
| Human Acceptance not performed or falsely claimed | PASS — §8, `PENDING` |

**Failure classification:** `PASS`

`R2-RC — FROZEN / ACCEPTED / READY FOR HUMAN ACCEPTANCE`
