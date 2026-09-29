# MD Converter - TOC Heading Localization Closure Evidence

**Document Type:** Closure Evidence
**Task:** TOC Heading Localization Fix (THL)
**Change classification:** G1 - bounded presentation / localization change (no G2 trigger opened)
**Starting HEAD:** `ed965f80cee552cbc8f646616349d80fa92c997d` (`master`, "Program C close professional output profiles")
**Implementation commit:** `22462cb0a657d9a8012c013d1b766ba8f12c97ab` - "fix localize TOC heading by document language"
**Canonical impact:** none (`CANONICAL_SPEC.md` frozen 1.0 unchanged; no ADR, no `SPEC_CHANGELOG.md` entry)
**Final status:** **CLOSED / ACCEPTED** (§15)

---

## 1. Baseline (frozen before any edit)

```text
git rev-parse HEAD    ed965f80cee552cbc8f646616349d80fa92c997d
git log -1            Program C close professional output profiles
git status --short (tracked modifications at the start of THL)
  M .gitignore                                  (unrelated, pre-existing)
  M README.md                                   (unrelated, pre-existing)
  M md_converter/cli.py                         (unrelated, pre-existing)
git diff --name-status
  M .gitignore  M README.md  M md_converter/cli.py
```

No THL file was modified before this baseline was recorded. The unrelated dirty
files were preserved and never staged (see §5 and §14).

---

## 2. Architecture inspection conclusion

Traced before writing code: the TOC heading text, the TOC heading paragraph and
style, the TOC field, the cached entries, the post-TOC page break and the Word
COM refresh path.

| Inspection item | Finding |
|---|---|
| Current TOC heading authority | `DocxPostProcessor._insert_toc_native` (`md_converter/renderer/post_processor.py`) |
| Current default / hardcoded title | `title_p.add_run("目录")` - always Chinese, independent of the document |
| Existing document-language signal | `md_converter/renderer/layout/language_detection.py`: `classify_char` / `TextScript.CJK` / `detect_language`. Its `_CJK_RE` also covers Kana, Hangul and CJK punctuation, so it is **not** by itself a "meaningful Chinese" predicate |
| Proposed integration point | select the localized heading text inside `_insert_toc_native`, immediately before the title paragraph is created, using the visible text of the document object the post-processor already holds |
| TOC field semantics changed? | **NO** - the field instruction `' TOC \o "1-3" \h \z \u '`, field char sequence, `w:dirty` absence and `updateFields` absence are untouched |
| PostProcessor structural semantics changed? | **NO** - same anchor, same paragraph order, same `TOC Heading` style, same bold/18pt/Microsoft YaHei title run formatting, same bookmarks, same entry paragraphs, same page break |
| G1 implementation possible? | **YES** - no Core/Canonical/QA/ConversionService change and no new dependency required |

Related surfaces inspected and left unchanged: the Word COM refresh
(`_update_toc_with_word`, which already accepted both heading texts), the TOC
entry builder (`_append_toc_entry`), `_ensure_toc_styles`, the theme/config TOC
block, the Golden/Canonical guards and the Presentation Profile layer.

---

## 3. Localization rule (frozen)

```text
English-only document            -> "Table of Contents"   PASS
Chinese-only document            -> "目录"                PASS
Chinese + English mixed document -> "目录"                PASS
unknown / unreliable language    -> "Table of Contents"   PASS
```

Governing rule, implemented exactly as specified:

```text
if meaningful Chinese content is positively detected:  TOC heading = "目录"
else:                                                  TOC heading = "Table of Contents"
```

"Positively detected Chinese content" is implemented as **at least one Han
ideograph** (CJK Unified Ideographs U+4E00-U+9FFF, plus Extension A
U+3400-U+4DBF) in the visible document text:

* English prose, digits, symbols, Latin text -> no Han -> English title;
* full-width punctuation (`。、；：！？`) alone -> no Han -> English title
  (mandated by the "numbers / punctuation only" requirement);
* any real Chinese content anywhere (heading or body, short or long) -> Chinese
  title, which is what makes "English heading + Chinese body" and "Chinese
  heading + English body" both resolve to "目录".

No ratio/threshold heuristic was used: a dominance ratio would fail the mandated
"mostly-English document with a Chinese section" case. No `langdetect`,
fastText, NLP framework, LLM call, locale guess, Windows locale lookup or
network access is involved - the rule is a deterministic Unicode predicate.

---

## 4. Implementation point (single authority)

```text
_insert_toc_native(doc)
    -> toc_heading_for_document_text(_visible_document_text(doc))   [single authority]
    -> title_p.add_run(toc_heading)                                  [existing insertion]
    -> existing TOC field / entries / page break / COM refresh       [unchanged]
```

New authority module: `md_converter/renderer/layout/toc_localization.py`

```text
DEFAULT_TOC_HEADING = "Table of Contents"
CHINESE_TOC_HEADING = "目录"
toc_heading_for_document_text(text: Optional[str]) -> str
```

* pure function: no Qt, no IO, no network, no mutable global state, no
  third-party import (a guard test asserts the module's only imports are
  `__future__`, `typing` and the sibling `language_detection`);
* reuse, not duplication: the Han predicate lives once, in the existing
  language utility (`language_detection.contains_han_ideograph`);
* the two heading texts exist as literals in exactly one production module; a
  guard test scans every other production module's *code* string constants
  (docstrings excluded) and fails if either text reappears;
* the COM refresh whitelist now references the same two constants instead of its
  own copies.

Language input: the lowest-cost authoritative representation already available
at the integration point - the python-docx document the post-processor is
holding (paragraph text + table cell text). No Markdown re-parse, no parser
change, no new document model.

---

## 5. Files changed

```text
md_converter/renderer/layout/language_detection.py    + contains_han_ideograph() and its Han-only regex
md_converter/renderer/layout/toc_localization.py      + new single localization authority
md_converter/renderer/post_processor.py               + localized heading selection, visible-text helper,
                                                        COM whitelist single-sourced (no structural change)
md_converter/tests/test_toc_heading_localization.py   + new focused coverage (29 tests)
Doc/V2/Implementation/TOC_Heading_Localization/TOC_HEADING_LOCALIZATION_CLOSURE_EVIDENCE.md   (this file)
Doc/V2/Implementation/TOC_Heading_Localization/evidence/thl_localization_matrix.json          (measured evidence)
Doc/V2/Implementation/TOC_Heading_Localization/evidence/samples/{english,chinese,mixed,unknown}.docx
```

Not touched (preserved, and deliberately not staged): `.gitignore`, `README.md`,
`md_converter/cli.py` (pre-existing unrelated modifications) and every unrelated
untracked path.

No Golden baseline was modified: `md_converter/tests/golden/sample.expected.json`
already expects `"目录"` for a sample that contains Han characters
(`中文 日本語 ...`), so the frozen product rule leaves that expectation intact -
it was never a semantic invariant being rewritten.

---

## 6. Tests added

`md_converter/tests/test_toc_heading_localization.py` - 29 tests:

| Area | Coverage |
|---|---|
| Frozen matrix (authority) | English -> English; Chinese -> 目录; mixed -> 目录; empty/whitespace/`None` -> English; numbers + full-width punctuation -> English; English heading + Chinese body -> 目录; Chinese heading + English body -> 目录; determinism |
| Script predicate | Han detected; kana-only, hangul-only, CJK-punctuation-only, Latin-only, numeric-only, empty -> not Han |
| Real DOCX | six documents: localized title text, `TOC Heading` style, centered, bold, 18pt |
| Field / entries / break | field instruction present, no `w:dirty`, no `updateFields`, bookmarks + hyperlinks + anchors, entries equal the document headings, page break after the last entry, artifact opens |
| TOC disabled | `toc=False` leaves no TOC heading and no field in either language |
| Orthogonality | three Presentation Profiles x two languages -> localization unchanged |
| Batch | one service instance, four languages, per-file correct title and `SUCCESS` (proves per-document derivation, no cross-document state) |
| Authority guards | localization module is dependency-free; no other production module hardcodes either heading text |

---

## 7. Verification results

```text
Focused pass (THL module + existing post-processor tests)      33 passed, 0 failed
THL module alone                                               29 passed

Bounded regression pass (golden, acceptance, THL, post-processor, empty-heading,
renderer v1.5, theme v1.5, layout plan, page geometry, heading font sizes,
quality gate, figure sizing, adjacent tables, simple table pass, public API,
Program C profile tests, full GUI suite, application suite)     844 passed, 0 failed

Full suite near closure                                        1040 collected
                                                               1038 passed
                                                                  2 failed (pre-existing, see §8)

Lint (touched files only):
  ruff           PASS (0 findings in THL files; no unrelated lint debt touched)
  black --check  PASS
  isort          PASS
```

Golden tests passed unchanged, confirming the frozen rule is presentation-
compatible with the existing baseline.

---

## 8. Known pre-existing failures

```text
md_converter/tests/test_packaging_metadata.py
  ::test_pkg_documented_extras_exist_in_metadata
  ::test_pkg_readme_has_no_legacy_packaging_references

Cause: the working tree's already-modified README.md no longer documents the
pyproject extras / entry points these tests assert. Present before Program C,
before THL, and intentionally not repaired here.

Known pre-existing failures: 2
Introduced THL failures: 0
```

---

## 9. Real DOCX evidence

Measured from artifacts produced by the accepted conversion path
(`evidence/thl_localization_matrix.json`, `evidence/samples/*.docx`):

| Case | Source content | TOC title | Expected | Entries | Field | Break after TOC |
|---|---|---|---|---|---|---|
| `english` | English only | `Table of Contents` | `Table of Contents` | `Guide` | present | yes |
| `chinese` | Chinese only | `目录` | `目录` | `使用手册` | present | yes |
| `mixed` | Chinese + English | `目录` | `目录` | `Guide 使用手册` | present | yes |
| `unknown` | numbers, symbols, full-width punctuation only | `Table of Contents` | `Table of Contents` | `2026` | present | yes |

All four artifacts: `TOC Heading` style, centered, bold, 18pt, opens
successfully, entries match the document headings, page numbering unaffected
(no page-number change was introduced; the Word field still owns page numbers).

Profile orthogonality (same source compiled under all five profiles): the
localization-relevant TOC block is byte-identical across profiles and the title
is unchanged (English -> `Table of Contents`, Chinese -> `目录`). The only
cross-profile difference is the TOC page-number tab stop, which the
post-processor derives from the effective content width and which therefore
follows the profile's page margins - pre-existing behaviour, with the tab code
untouched by THL.

Batch (one `ConversionService`, four languages, four files): each artifact got
its own correct title and reported `SUCCESS` - localization is derived per
document, so Serial Batch behavior is unaffected.

---

## 10. TOC field / update drift result

```text
TOC field instruction (TOC \o "1-3" \h \z \u)      unchanged
field character sequence (begin/separate/end)      unchanged
w:dirty flag                                       absent (unchanged)
settings.xml updateFields                          absent (unchanged)
Word COM refresh path (_update_toc_with_word)      unchanged (already accepted both titles)
TOC entry paragraphs, styles, bookmarks, anchors   unchanged
post-TOC page break                                unchanged
TOC heading style (TOC Heading) and run formatting unchanged
```

Only the title run's text differs, and only when the document language requires
the English title.

---

## 11. Drift matrix

```text
Core semantic drift                     = 0   (parser / AST / pipeline / renderer untouched)
Canonical decision drift                = 0   (CANONICAL_SPEC.md, ADRs, SPEC_CHANGELOG.md untouched)
QA semantic drift                       = 0   (StaticQA / RenderedQA / FinalArtifactQA untouched; gates pass)
ConversionService semantic drift        = 0   (no change to the application layer)
CLI / public API breaking drift         = 0   (no signature or behaviour change for callers)
output naming / path semantic drift     = 0   (naming code untouched)
TOC field-generation semantic drift     = 0   (§10)
Word COM / TOC refresh semantic drift   = 0   (§10)
Golden semantic drift                   = 0   (no baseline modified; golden tests pass)
profile authority duplication           = 0   (one localization authority; guard test)
introduced failures                     = 0   (2 failures are the pre-existing packaging ones)
open blockers                           = 0
```

---

## 12. Sandbox / execution environment observation

```text
Sandbox status: UNAVAILABLE ("windows sandbox failed ... setup refresh had errors")
Execution path: Human-approved host/escalated execution using the project .venv
Dependency changes: NONE (nothing installed, upgraded or configured)
System configuration changes: NONE
Product impact: NONE OBSERVED
Verification impact: NONE OBSERVED
```

The sandbox was not repaired as part of this task (separate maintenance item).
Sandbox unavailability alone was not treated as a reason to stop this bounded
fix.

---

## 13. Known limitations

1. **Script-based, not language-identification-based.** The rule detects Han
   ideographs; therefore a Japanese document that contains kanji yields `目录`.
   This follows the frozen product rule (Chinese vs. non-Chinese only) and
   deliberately avoids building a document-language classification subsystem.
2. **Visible text includes code blocks and metadata.** The signal is the
   document's rendered text (paragraphs + table cells) using the representation
   the post-processor already holds; a document whose only Han characters appear
   inside a code block or the cover metadata would be treated as Chinese. The
   accepted architecture exposes whole-document text cheaply, and the task
   explicitly discourages redesigning the parser to exclude such content.
3. **Selected before the TOC is inserted**, so the heading itself never
   influences the decision.
4. **No user-selectable TOC language** - explicitly out of scope (no general
   i18n framework, no translation system).

---

## 14. Commits

```text
implementation   22462cb0a657d9a8012c013d1b766ba8f12c97ab
                 fix localize TOC heading by document language
                 4 files changed, 466 insertions(+), 3 deletions(-)
                 parent: ed965f80cee552cbc8f646616349d80fa92c997d

closure          <created after this document is written; see the closure report>
                 close TOC heading localization fix
                 (this evidence document + measured evidence artifacts)
```

Staging was performed one exact path at a time; `git diff --cached
--name-status` was inspected before each commit. No `git add .` / `git add -A` /
`git clean` / `git reset --hard` / `git restore` was used. No retrospective
per-WP commits were fabricated.

---

## 15. Definition of Done

```text
English-only -> "Table of Contents"        PASS
Chinese-only -> "目录"                     PASS
Chinese-English mixed -> "目录"            PASS
Unknown / unreliable -> "Table of Contents" PASS
TOC entries unchanged                      PASS
TOC field semantics unchanged              PASS
Word update behavior unchanged             PASS
TOC style unchanged                        PASS
Profiles unaffected                        PASS
Serial Batch unaffected                    PASS
Core drift                                 = 0
Canonical drift                            = 0
QA semantic drift                          = 0
ConversionService semantic drift           = 0
CLI / public API breaking drift            = 0
output naming / path drift                 = 0
introduced failures                        = 0
open blockers                              = 0
```

**Recommendation: accept and close.**

```text
TOC Heading Localization Fix (THL)
Status: CLOSED / ACCEPTED
```
