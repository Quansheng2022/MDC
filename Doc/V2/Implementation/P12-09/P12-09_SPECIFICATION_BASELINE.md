# P12-09 — Verification
## Specification Baseline

**Project:** MD_Converter v2.0  
**Phase:** P12-09 — Verification  
**Product Baseline:** `38614c7` (P12-08 Closure)  
**Phase Character:** Independent verification / release-candidate confidence  
**Governance:** verification-first; no feature expansion

## Objective

Independently verify that the packaged and installed MD Converter produced by P12-08 satisfies the frozen v2.0 product, architecture, acceptance, and release expectations.

P12-09 is primarily a verification phase, not an implementation phase.

## Frozen Product Boundary

Accepted runtime architecture:

```text
GUI → GuiWorker → ConversionService → Canonical Core
```

Accepted result path:

```text
ConversionResult / JobFailure → presentation model → result/report/output UX
```

P12-09 must not create new product features, Settings, conversion options, diagnostics semantics, output naming rules, installer behavior, update/network/telemetry capability, or architecture.

## Work Packages

| WP | Title | Responsibility |
|---|---|---|
| WP-P12-09-01 | Verification Baseline | freeze verification matrix, candidate artifacts, environments, accepted exceptions |
| WP-P12-09-02 | Functional Acceptance | user-visible end-to-end product acceptance |
| WP-P12-09-03 | Regression / Canonical / Golden | source regression, public contracts, Canonical/Golden drift |
| WP-P12-09-04 | Installed / Packaged Verification | installer, installed runtime, paths, encoding, output actions |
| WP-P12-09-05 | Failure / Recovery / Usability | negative paths, recovery, lifecycle, keyboard/accessibility/high-DPI |
| WP-P12-09-06 | Privacy / Locality / Release Integrity | local/private claims, required network dependency, artifact integrity |
| WP-P12-09-07 | Verification Closure | consolidate evidence, classify blockers, authorize/block P12-10 |

## Verification Principles

- Prefer verification of the accepted artifact over implementation inference.
- Do not infer PASS solely because an earlier phase passed.
- Reuse prior evidence when still valid; re-check release-critical paths independently.
- WPs 01–06 use focused verification; WP-07 performs closure consolidation.
- Verification does not authorize redesign.

## Defect Classification

- **V0 Observation:** no release impact; record only.
- **V1 Minor verification defect:** harness, stale assertion, evidence/documentation, or non-semantic packaging issue; bounded correction allowed.
- **V2 Release-blocking product defect:** broken launch/conversion/install/uninstall, unsafe lifecycle, data-loss risk, serious privacy/locality failure; stop progression.
- **V3 Semantic/architecture change required:** Core/Canonical/QA/public semantics change; stop immediately and escalate.

## Known Accepted Exceptions

Carry forward unless changed:

- two pre-existing README-content / packaging metadata regression failures;
- invalid YAML frontmatter behavior;
- existing test side effect involving `output\document.docx`;
- historical repo-wide lint debt outside touched files;
- no authoritative custom product icon;
- other explicitly documented deferred items from P12-08 closure.

## Required Environment Record

Record Windows version/build, display scaling, locale/code page where relevant, Microsoft Word availability/version, installed path, installer identity/hash, and test workspace paths.

## Git / Change Policy

P12-09 should produce mostly verification documents/tests.

Any product or packaging change is exceptional.

One WP → verify → bounded commit → next WP.

## Mandatory Stop Conditions

STOP if verification finds:

- packaged app cannot perform normal real conversion;
- installed app cannot launch reliably;
- installer/uninstaller damages user data;
- worker lifecycle safety regression;
- output-path authority regression;
- Open Document fails under persistent-file conditions;
- cp1252/runtime encoding regression in normal installed use;
- unexpected required network dependency;
- Core/Canonical/QA/Golden drift;
- public API/CLI breaking change;
- defect requiring semantic architecture change.

## Exit Criteria

```text
functional acceptance PASS
source regression PASS subject only to unchanged approved exceptions
Canonical / Golden drift = 0
installed-app verification PASS
installer/uninstaller verification PASS
failure/recovery PASS
settings persistence PASS
Open Document actual-open PASS
Open Folder PASS
privacy/locality verification PASS
release artifact integrity PASS
introduced failures = 0
open release blockers = 0
```

Next phase: **P12-10 — Release Candidate**
