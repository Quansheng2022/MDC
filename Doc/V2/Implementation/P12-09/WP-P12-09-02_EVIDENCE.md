# WP-P12-09-02 — Functional Acceptance — Completion Evidence

**Product Baseline SHA:** `38614c7bb555f96685c301bc4b6abd71138c2642`
**Specification Baseline SHA:** `08b198043ad107cdcd9293152acfa756fd6fa410`
**Input commit:** `100c0e7` (WP-P12-09-01)
**Authority:** verification only; no production code change

## Report record

| Field | Value |
|---|---|
| WP | WP-P12-09-02 — Functional Acceptance |
| Status | PASS |
| Input baseline SHA | `100c0e7` |
| Output commit SHA | recorded by the committing run (`P12-09-02 verify functional acceptance`) |
| Candidate under test | `dist\MD_Converter_Lite\MD_Converter_Lite.exe`, SHA-256 `F5AB988168DFA976ED50095A272FB3405CE2CAB395C4A77A34637318D60F7E04` (version 1.1.0) |
| Files added | this evidence file, `corpus/` (7 inputs), `tools/packaging/p12_09_acceptance.ps1`, `tools/packaging/p12_09_probe.ps1`, `evidence/wp02_*.json` |
| Files modified | none (production) |
| Checks executed | 4 smoke runs, 1 focused acceptance matrix (16 checks), 1 packaged runtime matrix (16 checks) |
| Passed / Failed | 36 / 0 (plus 1 recorded V0 observation) |
| Scope deviation | none |
| Stop condition | none |

## Candidate and method

The frozen packaged candidate (WP-09-01) was driven only through real user
actions against the packaged GUI. Conversion runs the accepted path
`GUI → GuiWorker → ConversionService → Canonical Core → DOCX`; every artifact
was validated as a real DOCX (`word/document.xml` present) and Microsoft Word
was used as the actual Open Document target.

Evidence records:

| Run | Evidence file | Result |
|---|---|---|
| Smoke — simple document | `evidence/wp02_smoke_01_simple.json` | PASS 13/13 |
| Smoke — headings/lists/tables | `evidence/wp02_smoke_02_headings_lists_tables.json` | PASS 13/13 |
| Smoke — Unicode / non-ASCII | `evidence/wp02_smoke_03_unicode.json` | PASS 13/13 |
| Smoke — richer rendering case | `evidence/wp02_smoke_04_rich.json` | PASS 13/13 |
| Focused acceptance matrix | `evidence/wp02_acceptance_matrix.json` | PASS 16/16 |
| Packaged runtime matrix | `evidence/wp02_runtime_matrix_packaged.json` | PASS 16/16 |

## Real conversion (representative inputs)

| Input | Content | Outcome | Artifact |
|---|---|---|---|
| `corpus/01_simple.md` | simple paragraphs | SUCCESS (4.8 s) | valid DOCX |
| `corpus/02_headings_lists_tables.md` | H1–H4, ordered/unordered/nested lists, table, quote, horizontal rule | SUCCESS (4.7 s) | valid DOCX |
| `corpus/03_unicode.md` | Chinese headings/body, accented Latin, Greek, Japanese, table | SUCCESS (4.8 s) | valid DOCX |
| `corpus/04_rich.md` | frontmatter (title/date/tags), code block, inline formatting, hyperlink, table, quote | SUCCESS (4.7 s) | valid DOCX |

## Frozen GUI states

Each state was observed through the product's own controls, not inferred:

| State | How it was produced | Observed | Result |
|---|---|---|---|
| `EMPTY` | fresh launch | Convert disabled, no source, no result area | PASS |
| `READY` | select `01_simple.md` | Convert enabled, "Selected Markdown file" shown | PASS |
| `CONVERTING` | click Convert, sample in flight | Convert disabled, Select File **disabled**, drop area **disabled**, no result area | PASS |
| `SUCCESS` | `02_headings_lists_tables.md` | Open Document/Folder enabled, no Details button | PASS |
| `SUCCESS_WITH_WARNING` | `05_warning_empty_heading.md` (empty heading) | summary "Conversion reported 1 warning.", Details enabled, output actions enabled | PASS |
| `FAILED` | `06_empty.md` (empty document) | Details enabled, output actions disabled/hidden | PASS |

Exactly the six frozen states were observed; no hidden or extra state appeared.

## Input handling

| Case | Method | Observed | Result |
|---|---|---|---|
| Select Markdown | native Open dialog via the product's Select File button | source accepted, Convert enabled | PASS |
| Invalid / non-Markdown input | select `invalid_input.txt` through the same dialog | app alive, state stays `READY`, no crash, no conversion | PASS |
| Missing / stale source | select a valid file, delete it, then Convert | app alive, terminal `FAILED`, no crash, no fallback | PASS |
| Drag & drop | probe `WS_EX_ACCEPTFILES` + real `WM_DROPFILES` | not registrable — see observation below | V0 |

**V0 observation — drag & drop.** The main window has
`WS_EX_ACCEPTFILES = False`; Qt registers its drop surface as an OLE
`IDropTarget`, so a `WM_DROPFILES` message cannot exercise it, and scripting an
OLE drag source would require moving the physical cursor and pressing the mouse
button on the user's live desktop. The drop code path is instead verified
directly by the product's own drop-event tests
(`md_converter/tests/gui/test_drag_and_drop.py`), which run in the WP-09-03 GUI
suite against the real widget handler. This is a harness limitation, not a
product failure, and it is carried forward unchanged from P12-08 (whose matrix
also had no OS-level drag check).

## Result UX

| Surface | Evidence | Result |
|---|---|---|
| Success | result area hidden, output actions enabled | PASS |
| Warning | concise summary + Details… enabled, artifact kept actionable (`warning-keeps-artifact-actionable`) | PASS |
| Failure | failure summary + Details… enabled, output actions disabled/hidden | PASS |
| Report / details | `Warning details - MD Converter` and `Failure details - MD Converter` dialogs opened, read-only text, no `Traceback` | PASS |
| Diagnostics retained | details dialogs render the retained result evidence (no second QA interpretation) | PASS |

## Output actions (packaged candidate)

| Check | Evidence | Result |
|---|---|---|
| Artifact exists before launch | `artifact existed before=True` | PASS |
| Open Document launcher accepted | `open-document-word-opens` | PASS |
| Microsoft Word actually opened/read the file | Word document window `runtime_smoke_ü_222826 [Compatibility Mode] - Word`, artifact held under an exclusive lock while displayed, lock released on close | PASS |
| Artifact remains present | `artifact-persists-after-open` | PASS |
| Open Folder targets expected directory | new Explorer window `output - File Explorer` | PASS |
| Missing artifact fails closed | notice shown, no Word window, artifact not recreated, app alive, no fallback/retry | PASS |

`openUrl == True` alone was **not** accepted: the Word document window title and
the exclusive file lock were both required.

## Settings and About

| Check | Evidence | Result |
|---|---|---|
| Save + restart persistence | `settings-saved`, `settings-persist-across-restart`, `remembered-folders-restored` | PASS |
| Cancel discards edits | toggled On→Off, Cancel pressed, reopened dialog shows `On` again | PASS |
| Reset to Defaults | `Reset to Defaults` restores the form default (`On`) without saving | PASS |
| About wording | product name `MD Converter`, `Version 1.1.0`, frozen positioning sentence, `Processing: Local, on this computer`, `Account required: No`, `Document upload: Not required for normal conversion` | PASS |

## Lifecycle (observed during functional acceptance)

| Check | Evidence | Result |
|---|---|---|
| Worker-active close protection | window close during an active conversion did not terminate the app; that conversion then completed SUCCESS | PASS |
| Clean close when idle | application exits when closed while idle | PASS |
| Sequential conversions / recovery | recovery from `FAILED` to `SUCCESS` in one session | PASS |

## Defects

| Class | Count | Detail |
|---|---|---|
| V0 observations | 1 | drag & drop cannot be scripted at the OS/OLE level (above) |
| V1 corrections | 2 | verification-harness only, inside this WP: (a) the source-label accessible name is "Selected Markdown file", not the path — the state classifier was corrected; (b) terminal-state sampling now requires a stable double sample because the outcome controls update over a short window. No product code was touched. |
| V2 blockers | 0 | — |
| V3 blockers | 0 | — |

## Acceptance

| Criterion | Result |
|---|---|
| All required user-visible functional paths PASS | PASS |
| Frozen states only | PASS |
| Open Document (Word actually opened) PASS | PASS |
| Open Folder PASS | PASS |
| Missing artifact fails closed | PASS |
| Settings persistence PASS | PASS |
| Introduced failures | 0 |
| Release blockers | 0 |

## Conclusion

WP-P12-09-02 passes: the frozen packaged release candidate performs real
conversions across simple, structured, Unicode and rich inputs; exposes exactly
the six frozen GUI states; keeps warnings, failures and output actions distinct
and safe; opens the artifact in Microsoft Word; and persists settings. The only
unverified item is OS-level drag & drop, recorded as a V0 harness observation
and covered by the product's own drop-event tests in WP-09-03.
