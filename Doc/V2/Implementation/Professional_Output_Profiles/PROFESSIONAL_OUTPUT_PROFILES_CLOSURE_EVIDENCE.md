# MD Converter - Professional Output Profiles Closure Evidence

**Document Type:** Closure Evidence (WP-POP-07)
**Program:** Program C - Professional Output Profiles
**Product Specification baseline:** `Doc/V2/Product/Professional_Output_Profiles_Product_Specification.md` (unchanged; an untracked planning input, see §3)
**Architecture baseline:** `Doc/V2/Implementation/Professional_Output_Profiles/PROFESSIONAL_OUTPUT_PROFILES_ARCHITECTURE_BASELINE.md` (FROZEN)
**Change classification:** G1 - controlled feature work (no G2 item opened)
**Canonical impact:** none (`CANONICAL_SPEC.md` FROZEN 1.0 unchanged; no ADR, no `SPEC_CHANGELOG.md` entry)
**Starting HEAD (closure baseline):** `70a63981707f8d041ca8e5d55d49fdd3d66f8c61` (`master`, "DI-07 close document intelligence upgrade")
**Implementation commit:** see §11
**Final status:** Program C - Professional Output Profiles: **CLOSED / ACCEPTED** (see §12)

---

## 1. Work Package chain

| WP | Deliverable | Status |
|---|---|---|
| POP-01 | `PROFESSIONAL_OUTPUT_PROFILES_ARCHITECTURE_BASELINE.md` (freeze: registry location, id format, initial set, default, in/out-of-scope properties, renderer + GUI integration points, batch locking, Golden policy, G2 triggers) | DONE |
| POP-02 | `md_converter/profiles/{model,registry,theme_overrides,__init__}.py` - single profile authority, bounded immutable configuration, deterministic lookup, safe fallback | DONE |
| POP-03 | Output-profile selector beside the conversion controls, persisted through the existing GUI-local store only | DONE |
| POP-04 | One renderer integration point (`V15Theme.with_presentation_overrides`) driven by the compiler; no renderer branching | DONE |
| POP-05 | One profile captured per conversion/batch; selector locked while converting; no cross-run leakage | DONE |
| POP-06 | Presentation matrix evidence + representative DOCX samples for visual review | DONE (human review PASS, see §7) |
| POP-07 | This closure evidence | DONE |

**No retrospective WP commits were fabricated.** POP-01..POP-07 were implemented
without commits (a single working-tree implementation), so the truthful history
is one bounded implementation commit plus one closure-evidence commit
(§11 / §12):

```text
Program C implement professional output profiles     (code + tests + baseline + evidence)
Program C close professional output profiles         (this closure evidence)
```

---

## 2. Implementation summary (what was frozen)

### 2.1 Single profile authority

`md_converter/profiles/registry.py` is the only profile authority in the
product: stable identifiers, deterministic declaration order, one default, safe
fallback, no duplicate definitions. The GUI reads only identifiers and display
names from it; the compiler resolves configuration against it. There is no
second profile definition anywhere (no duplicated table in the GUI, the
settings store holds an identifier only, and the renderer knows nothing about
profiles).

### 2.2 The five frozen profiles

| Order | Identifier | Display name | Bounded divergence from the accepted baseline |
|---|---|---|---|
| 1 | `professional_report` | Professional Report | none - this is the default and equals the frozen V1.5 baseline |
| 2 | `business_report` | Business Report | 2.0 cm margins, 10 pt body, smaller headings, Light Grid, 9 pt table text |
| 3 | `academic` | Academic | 3.0 cm side margins, Times New Roman / SimSun 11.5 pt, 1.5 line spacing, 0 pt paragraph spacing |
| 4 | `technical` | Technical | 2.2 cm margins, 18/15/13/11.5 pt headings, 1.2 line spacing, Light Grid Accent 1 |
| 5 | `clean_minimal` | Clean / Minimal | 15/13/11.5/10.5 pt headings, 1.25 line spacing, 8 pt paragraph spacing, Light Grid |

Profile-controllable properties are frozen to: page margins; body/heading font
families (all four Word font slots); body size; H1-H4 sizes; heading spacing;
line spacing; paragraph spacing; code font/size/line spacing; table style and
table font size.

### 2.3 Default profile behaviour (compatibility rule)

The default `professional_report` profile applies **no presentation overlay**:
the compiler leaves the theme object untouched. This is the strongest
backward-compatibility guarantee, it preserves caller-supplied/customised
themes, and it makes the default artifact content-identical to the accepted
baseline (§4). No silent output-wide restyling occurs.

### 2.4 Renderer integration boundary

```text
config["output_profile"]
    -> md_converter.profiles.registry.resolve_profile()      (safe fallback)
    -> md_converter.profiles.theme_overrides (data only)
    -> V15Theme.with_presentation_overrides()                 (renderer-owned merge)
    -> existing StyleResolver / WordRenderer / DocxPostProcessor path
```

`CompilerContext.create` is the only caller. The renderer contains no
`if profile == ...` branch, and a guard test asserts that no module under
`md_converter/renderer/` mentions `output_profile`, the overlay function or the
profile package.

### 2.5 GUI selection / settings behaviour

One `Output Profile:` combo box beside the existing output-folder row (the
Settings dialog stays frozen to GUI-local folder preferences and contains no
combo box). Default selected on a fresh install; the last-used identifier is
stored through the existing GUI-local store only (`output/profile`); blank,
unknown or deprecated stored identifiers fall back to the default
deterministically; opening the window writes nothing; the default profile is
not sent as an override, so the accepted request shape is unchanged. Keyboard
reachable, in the workflow tab order, accessible name + plain-language tooltip.

### 2.6 Batch profile behaviour

One profile is captured at batch start and reused for every item of that run;
there is no per-file profile configuration; the selector and
`set_output_profile` are refused while the run is active; a failing/warning item
does not change the profile or stop the queue; the captured value is released
when the run finishes, so the next batch uses the newly selected profile and no
profile leaks across runs.

---

## 3. Files changed

Added:

```text
md_converter/profiles/__init__.py
md_converter/profiles/model.py
md_converter/profiles/registry.py
md_converter/profiles/theme_overrides.py
md_converter/tests/test_output_profiles.py                       (56 tests)
md_converter/tests/test_output_profile_rendering.py              (12 tests)
md_converter/tests/gui/test_output_profile_selection.py          (23 tests)
Doc/V2/Implementation/Professional_Output_Profiles/PROFESSIONAL_OUTPUT_PROFILES_ARCHITECTURE_BASELINE.md
Doc/V2/Implementation/Professional_Output_Profiles/PROFESSIONAL_OUTPUT_PROFILES_CLOSURE_EVIDENCE.md
Doc/V2/Implementation/Professional_Output_Profiles/evidence/pop_presentation_matrix.json
Doc/V2/Implementation/Professional_Output_Profiles/evidence/source.md              (sample input)
Doc/V2/Implementation/Professional_Output_Profiles/evidence/samples/*.docx       (visual-review artifacts)
```

Modified (all inside the frozen Allowed Scope):

```text
md_converter/config.py                        + output_profile key, type validation, CompilerConfig field
md_converter/compiler.py                      + single profile resolution/overlay integration point
md_converter/renderer/themes/v15_theme.py     + with_presentation_overrides + private deep merge
md_converter/gui/main_window.py               + selector row, capture, locking, request intent, a11y, tab order
md_converter/gui/preferences.py               + output/profile key (GUI-local, identifier only)
md_converter/gui/request_builder.py           + optional output_profile intent (default omitted)
md_converter/gui/state.py                     + StateEffect.profile_enabled
md_converter/tests/gui/test_accessibility_window.py   tab-order expectation extended by the authorized control
```

Untouched by design: `CANONICAL_SPEC.md`, `SPEC_CHANGELOG.md`, ADRs,
`renderer/themes/default_v1_5.yaml`, `renderer/layout/**`, `quality_gate.py`,
`application/conversion_service.py`, `parser/**`, `pipeline/**`, `ast/**`,
`tests/golden/**`, `README.md`, `pyproject.toml`, `packaging/**`.

Staging boundary (see §10): the staged implementation commit contains exactly
the Program C files listed above. The Program C **Product Specification**
(`Doc/V2/Product/Professional_Output_Profiles_Product_Specification.md`) is an
untracked planning input that lives in an otherwise untracked `Doc/V2/Product/`
tree; the previous programs (`Doc/V2/Implementation/Document_Intelligence`,
Serial Batch Conversion) likewise committed their *implementation* documents
only, so the product specification is deliberately **not** staged and remains
an untracked input. The unrelated dirty files present at the starting HEAD
(`.gitignore`, `README.md`, `md_converter/cli.py`) are likewise not staged.

---

## 4. Test evidence

```text
Full suite (md_converter/tests, QT_QPA_PLATFORM=offscreen), re-run on the final
delivered tree:
  collected        1011
  passed           1009
  failed              2   <- identical to the pre-change baseline

  7% -> 100% progression with no error, no skip and no xfail introduced.
  The only failures are the two pre-existing packaging-metadata tests below.

Pre-change baseline (same command): 2 failures, both
  md_converter/tests/test_packaging_metadata.py
    ::test_pkg_documented_extras_exist_in_metadata
    ::test_pkg_readme_has_no_legacy_packaging_references
  Cause: the working tree's modified README.md no longer documents the
  pyproject extras / entry points these tests assert. Unrelated to Program C
  (README.md was already modified before this work started).

New focused tests: 91, all passing
  test_output_profiles.py                    56
  test_output_profile_rendering.py           12
  gui/test_output_profile_selection.py       23

Bounded closure verification pass (shortly before the implementation commit;
the implementation tree was unchanged since the full-suite run above):
  scope   focused profile tests, GUI profile tests, renderer/profile
          integration, batch/profile tests, GUI workflow regression,
          application layer, config/compiler-context/quality-gate regression
  result  405 tests, 405 passed, 0 failed, 0 skipped

Linters (final pass, exact Program C file list):
  ruff            PASS for every Program C file
                  (one pre-existing B904 remains in md_converter/config.py at the
                   untouched load_config YAML handler - proven present at
                   70a6398 and outside every Program C diff hunk)
  black --check   PASS (15 files unchanged)
  isort           PASS
  (The wider repository is not lint-clean independently of this program.)

Test hygiene: the GUI profile tests move the working directory to the pytest
temporary directory, so a test run never writes conversion artifacts into the
repository's gitignored `output/` scratch folder.
```

---

## 5. Presentation matrix evidence

Measured from real compiled artifacts
(`evidence/pop_presentation_matrix.json`, `evidence/samples/*.docx`); the
representative document covers headings, paragraphs, both list kinds, a table,
an inline-formatted paragraph and a code block.

| Profile | Presentation facts differing from baseline | FinalArtifactQA | Document meaning |
|---|---|---|---|
| `professional_report` (default) | **0** (content-identical artifact) | PASS | unchanged |
| `business_report` | 9 (margins, body/code size, heading font+sizes, line spacing, paragraph spacing, table style+size) | PASS | unchanged |
| `academic` | 10 (margins, body+heading fonts, body/code size, heading sizes, line spacing, paragraph spacing, table size) | PASS | unchanged |
| `technical` | 6 (margins, heading sizes, code size, line spacing, table style+size) | PASS | unchanged |
| `clean_minimal` | 6 (heading font+sizes, code size, line spacing, paragraph spacing, table style) | PASS | unchanged |

Key assertions:

* every profile: StaticQA = PASS, RenderedQA = PASS, PostProcessor = PASS, FinalArtifactQA = PASS, diagnostics = none;
* every profile: paragraph/table/shape meaning identical to the baseline;
* every profile: no rendered text below the 8pt floor, body ≥ 10pt, table ≥ 8.5pt (SPEC-INV-002);
* default profile: **identical package content** to the accepted baseline, i.e. introducing profiles restyles nothing (product specification §7).

Note on byte comparison: a DOCX raw file hash is *not* stable across saves
because the ZIP container records the local write time per entry. Content
identity is therefore asserted over the package parts. `ConversionResult`
quality-gate artifact hashes keep their canonical meaning (SPEC-QA-004).

---

## 6. Functional evidence

Single-file (WP-POP-03/04)

* the selector lists exactly the five supported profiles in the frozen order, with plain display names and descriptions;
* the default profile is selected on a fresh install; opening the window writes no preference;
* a user selection is persisted through the existing GUI-local store (`output/profile`) and restored on the next launch; blank or unknown stored identifiers fall back to the default deterministically;
* the default profile is not sent as a configuration override, so the accepted request shape is unchanged; a non-default profile is carried as `config_overrides["output_profile"]`;
* a real GUI conversion with `technical` produced a DOCX with 2.2cm margins and its declared typography.

Batch (WP-POP-05)

* one profile is captured at batch start and reused for every item (3-file batch: identical profile identifier on all three requests, in selection order);
* the selector and `set_output_profile` are refused while the run is active, so a mid-run change cannot affect the active batch;
* a failing item neither changes the profile nor stops the queue (failure in the middle: profile unchanged for the remaining item);
* after the run the captured profile is released and the next batch uses the newly selected profile (no leakage).

Settings / accessibility (WP-POP-06)

* the identifier is one of the declared GUI-owned keys, so `GuiPreferences.reset()` clears it;
* the selector is keyboard reachable, is in the workflow tab order, carries an accessible name and a plain-language tooltip, exposes item descriptions as item tooltips, and is never the only signal for any state;
* no colour-only styling was introduced.

Privacy / locality (unchanged)

* the profile is a local constant table: no account, no upload, no network, no telemetry, no file-system dependency.

---

## 7. Human visual review

**Human Visual Review: PASS.** The Human reviewed the generated profile DOCX
files and reported the conclusions below. This review was performed by the
Human; it is recorded here verbatim and was not machine-verified.

Reviewed artifacts:

```text
Doc/V2/Implementation/Professional_Output_Profiles/evidence/samples/
  baseline.docx  professional_report.docx  business_report.docx
  academic.docx  technical.docx  clean_minimal.docx
```

| Artifact | Human conclusion |
|---|---|
| `baseline.docx` vs `professional_report.docx` | no unintended visual regression (default profile preserves the accepted presentation) |
| `business_report.docx` | intentionally more compact |
| `academic.docx` | formal academic typography / spacing acceptable |
| `clean_minimal.docx` | appropriately restrained and readable |
| `technical.docx` | technical heading / table presentation acceptable |

Review dimensions covered: page layout and margins; body typography; heading
hierarchy; paragraph spacing; table appearance; code block appearance.

Regenerate any time with the converter (cover page, TOC and table styling are
the frozen product defaults and are profile-independent):

```powershell
python -c "from md_converter.compiler import compile_file; compile_file('Doc/V2/Implementation/Professional_Output_Profiles/evidence/source.md', config={'output_profile': 'academic', 'word_com': False}, output_path='out.docx')"
```

### 7.1 Separate observation: TOC heading localization

The review surfaced one presentation observation that is **not** a Program C
profile failure:

```text
TOC Heading Localization:
  English-only document            -> expected "Table of Contents"
  Chinese / mixed Chinese-English  -> expected "目录"
  Unknown / unreliable language    -> expected "Table of Contents"

Classification: separate bounded presentation fix
  NOT introduced by Program C
  NOT a Program C blocker
```

The TOC heading wording is owned by the frozen post-processor path
(`DocxPostProcessor._insert_toc_native`), which Program C does not touch; no
profile can influence it (cover/TOC presentation is an explicit deferred item,
§9). Per the closure instruction this fix is **not** implemented here; it is
recorded as the first post-closure action in §12.

---

## 8. Drift results

```text
ConversionService semantic drift = 0     (no change to conversion_service.py)
Core drift = 0                           (parser/AST/pipeline/renderer unchanged except the theme merge point)
Canonical drift = 0                       (CANONICAL_SPEC.md, SPEC_CHANGELOG.md, ADRs untouched)
QA semantic drift = 0                     (quality_gate.py and renderer/layout/** untouched; all QA stages pass)
Golden semantic drift = 0                 (no golden file changed; golden tests pass unchanged)
Golden baseline updates = 0               (SPEC-INV-011 respected)
CLI/public API breaking drift = 0         (config key is additive; CLI untouched)
output naming/path drift = 0              (no naming code touched)
default profile output drift = 0          (content-identical artifact)
profile authority duplication = 0         (one registry; the GUI and the settings store hold identifiers only)
renderer profile branching = 0            (no renderer module mentions profiles; guard test)
introduced failures = 0                   (2 failures are the pre-existing baseline failures)
open blockers = 0
```

---

## 9. Deferred items (explicitly out of scope, no work started)

| Item | Why deferred |
|---|---|
| Per-profile colours (heading/body/table-header/code background) | Colour is not theme data today: constants in `V15Theme` plus hardcoded post-processor values. Enabling it needs a renderer/post-processor change (G2-adjacent). |
| List spacing / list indentation | Hardcoded in `StyleResolver.list_item_style` and `WordRenderer.visit_ListItem`. |
| Figure sizing defaults per profile | `figure_sizing` reads the frozen `figure` block plus real section geometry; `image_width` remains the canonical key. |
| Cover-page and TOC presentation | Hardcoded in `DocxPostProcessor`; product specification §5 lists TOC presentation as future work. This is also where the TOC heading localization observation of §7.1 belongs. |
| Caption styling, page-break policy, table-fitting / figure-fitting policy | Not implemented in the current product at all. |
| Profile editing UI, user-defined profiles, profile DSL, Word template support | Explicit product non-goals (product specification §6). |
| `heading bold/italic` as a profile property | The renderer forces bold heading runs, so the property would be a silent no-op. |

---

## 10. Closure baseline, staging boundary and environment

### 10.1 Starting baseline (frozen before any closure action)

```text
git rev-parse HEAD   70a63981707f8d041ca8e5d55d49fdd3d66f8c61   (master)
git log -1           DI-07 close document intelligence upgrade
git status --short   see the classification below
git diff --name-status
  M .gitignore                                   (C: unrelated, pre-existing)
  M README.md                                    (C: unrelated, pre-existing)
  M md_converter/cli.py                          (C: unrelated, pre-existing)
  M md_converter/compiler.py                     (A: Program C)
  M md_converter/config.py                       (A: Program C)
  M md_converter/gui/main_window.py              (A: Program C)
  M md_converter/gui/preferences.py              (A: Program C)
  M md_converter/gui/request_builder.py          (A: Program C)
  M md_converter/gui/state.py                    (A: Program C)
  M md_converter/renderer/themes/v15_theme.py    (A: Program C)
  M md_converter/tests/gui/test_accessibility_window.py   (A: Program C, authorized tab-order expectation)
untracked
  md_converter/profiles/                                   (A: Program C, new)
  md_converter/tests/test_output_profiles.py               (A: Program C, new)
  md_converter/tests/test_output_profile_rendering.py      (A: Program C, new)
  md_converter/tests/gui/test_output_profile_selection.py  (A: Program C, new)
  Doc/V2/Implementation/Professional_Output_Profiles/      (A: Program C docs + evidence)
  ... plus a large body of unrelated untracked content (B/C: preserved
      review packages, dist/, release/, input_test/, packaging/, Doc/ trees, ...)
```

Classification: **A** = Program C, **B/C** = unrelated pre-existing dirty or
untracked content. Every staged file was verified against `git diff` to belong
to Program C; the file list was taken from the actual repository state, not
from the plan.

### 10.2 Git safety

No `git add .` / `git add -A` / `git clean` / `git reset --hard` / `git restore`
was used. Files were staged one exact path at a time, and
`git diff --cached --name-status` was inspected before each commit; the closure
commit stages the closure evidence document only.

### 10.3 Sandbox observation

```text
Sandbox status: UNAVAILABLE during Program C implementation
  (the Windows sandbox helper failed with
   "windows sandbox failed: helper_unknown_error: setup refresh had errors")
Execution path: Human-approved host/escalated execution using the project .venv
Product impact: NONE OBSERVED
Verification impact: NONE OBSERVED
                 (the same test suite, linters and evidence generation ran
                  successfully on the host; no dependency was installed,
                  changed or upgraded)
```

Sandbox recovery is deliberately **not** attempted in this closure; it is a
separate environment-maintenance task (§12). The sandbox was unavailable for
the whole program, including this closure session.

### 10.4 Open blockers

None. The feature has no open blocker; the two failing tests are the known
pre-existing `test_packaging_metadata.py` failures described in §4, and the TOC
heading localization observation (§7.1) is a separate bounded fix, not a
Program C blocker.

---

## 11. Commits

Truthful history: the implementation was completed in one working tree without
commits, so no retrospective POP-01..POP-07 commits were fabricated.

| # | Commit message | Contents |
|---|---|---|
| 1 | `Program C implement professional output profiles` | Program C code, tests, architecture baseline, evidence matrix + samples |
| 2 | `Program C close professional output profiles` | this closure evidence document |

Implementation commit SHA (verified after commit 1 was created):

```text
4acb978d66ed6b8522d66634eb9aa4832276228d
Program C implement professional output profiles
24 files changed, 3585 insertions(+), 7 deletions(-)
parent: 70a63981707f8d041ca8e5d55d49fdd3d66f8c61
```

Closure commit SHA is recorded in the closure report (a commit cannot contain
its own hash).

---

## 12. Definition of Done and final program status

```text
initial profile set frozen                PASS
profile registry implemented              PASS
single profile authority                  PASS
default profile no-overlay preservation   PASS
GUI selection                             PASS
settings integration                      PASS
renderer integration                      PASS
batch consistency                         PASS
safe invalid-ID fallback                  PASS
representative outputs                    PASS
document meaning preservation            PASS
visual Word review                        PASS (Human, §7)
accessibility                             PASS
high-DPI                                  PASS (no new layout primitive; bounded smoke test unchanged)
privacy/locality unchanged                PASS
focused regression                        PASS (405/405)
lint / black / isort                      PASS (§4)
full-suite evidence retained              1009 / 1011 PASS; 2 known pre-existing failures
ConversionService semantic drift          = 0
Core drift                                = 0
Canonical drift                           = 0
QA semantic drift                         = 0
output naming/path drift                  = 0
CLI/public API breaking drift             = 0
profile authority duplication             = 0
renderer profile branching                = 0
introduced failures                       = 0
open blockers                             = 0
implementation commit created             PASS (§11)
closure commit created                    PASS (§11)
```

```text
Program C - Professional Output Profiles
Status: CLOSED / ACCEPTED
```

Post-closure actions (separate tasks, deliberately not started here):

```text
1. TOC Heading Localization bounded fix (§7.1) - if not already authorized/completed
2. Codex Windows sandbox recovery (§10.3)
3. Program D - Advanced Table Fitting / Advanced Figure Fitting
```
