# WP-P12-09-05 — Failure / Recovery / Usability — Completion Evidence

**Product Baseline SHA:** `38614c7bb555f96685c301bc4b6abd71138c2642`
**Specification Baseline SHA:** `08b198043ad107cdcd9293152acfa756fd6fa410`
**Input commit:** `5249e46` (WP-P12-09-04)
**Authority:** verification only; no production code change

## Report record

| Field | Value |
|---|---|
| WP | WP-P12-09-05 — Failure / Recovery / Usability |
| Status | PASS |
| Input baseline SHA | `5249e46` |
| Output commit SHA | recorded by the committing run (`P12-09-05 verify failure recovery and usability`) |
| Candidate under test | packaged `MD_Converter_Lite.exe`, SHA-256 `F5AB988168DFA976ED50095A272FB3405CE2CAB395C4A77A34637318D60F7E04` |
| Files added | this evidence file, `tools/packaging/p12_09_failure_usability.ps1`, `evidence/wp05_failure_recovery_usability.json` |
| Files modified | none |
| Checks executed | 15 real-platform checks (negative paths, lifecycle, accessibility, geometry) |
| Passed / Failed | 15 / 0 |
| Scope deviation | none |
| Stop condition | none |

## Negative-path matrix

| Case | Method | Observed outcome | Result |
|---|---|---|---|
| Missing source | select a valid file, delete it, convert | terminal `FAILED`, app alive (WP-09-02) | PASS |
| Invalid source selection | select a non-Markdown file | rejected safely, state stays `READY` (WP-09-02) | PASS |
| Word-locked output | open the artifact in Word, convert the same source again | terminal `FAILED` with `[Errno 13] Permission denied: 'output\usability_source.docx'`; app alive; output file set unchanged (no rename/retry) | PASS |
| Unavailable output | pre-create a **directory** named `blocked_output.docx` in the output folder | terminal `FAILED` with `[Errno 13] Permission denied`; app alive | PASS |
| Conversion failure | empty document | terminal `FAILED` with a bounded failure report (WP-09-02) | PASS |
| Warning outcome | empty heading | `SUCCESS_WITH_WARNING` with a retained report (WP-09-02) | PASS |
| Missing output artifact | delete the artifact, click Open Document | fails closed: notice shown, no Word window, artifact not recreated (WP-09-02/04) | PASS |
| Stale remembered directory | store `Z:\definitely\missing\p1209` as the remembered source and output folder, restart | app starts normally; Settings shows `Not remembered` for both; the stale path is never surfaced | PASS |
| Invalid / off-screen geometry | move the window to (5000, 5000), close (product saves geometry), restart | restored to `558,134,1930,1090` — fully on a 1920×1080 screen (1362×946 visible) | PASS |
| Worker-active close attempt | close during an active conversion | close blocked, conversion completed (WP-09-02/04) | PASS |
| Recovery | convert again after `FAILED` | back to `READY`, then `SUCCESS` | PASS |
| No data loss | release the Word lock after the failed locked-output conversion | original artifact still a valid DOCX | PASS |

The Word-locked case exercised the accepted `OUTPUT_ERROR` behaviour only:
there is no rename, retry or overwrite, and the existing file set is unchanged
(`files_before == files_after`).

## Lifecycle

| Check | Evidence | Result |
|---|---|---|
| Active jobs ≤ 1 / duplicate Convert rejected | three rapid activation attempts on `Convert` produced exactly one artifact and one `SUCCESS` | PASS |
| Unsafe controls protected while converting | in-flight `CONVERTING` disables Select File and the drop area (WP-09-02) | PASS |
| Close blocked while a worker is active | window close during conversion did not exit; conversion completed (WP-09-02/04) | PASS |
| Close succeeds when idle | clean close verified | PASS |
| Sequential conversions usable | multiple conversions in one session, including after failures | PASS |

## Keyboard and accessibility

Real-window (packaged app, UI Automation) checks:

| Check | Observed | Result |
|---|---|---|
| Important controls have accessible names | `Select File`, `Change output folder`, `Convert`, `Settings`, `About`, `Markdown file drop area` all present, none missing | PASS |
| Logical Tab order | keyboard-focusable order `Select File → Change output folder → Convert → Settings → About` | PASS |
| Status is textual, not colour-only | status area exposes the accessible name `Status` and every state has distinct wording | PASS |
| Report is keyboard reachable | `Warning details` dialog exposes 8 elements, 3 keyboard-focusable | PASS |

Product-code level (already verified by the WP-09-03 GUI suite, 437/437):
`test_accessibility_window.py` proves the two standard shortcuts (`Ctrl+O`,
`Ctrl+,`), `Enter`/`Space` activation, hidden actions skipped by Tab,
accessible names matching visible wording, textual status, no colour-only
styling, the textual warning summary and a keyboard-accessible report surface.
`test_lifecycle.py` and `test_gui_state.py` cover duplicate-convert rejection
and close protection at the state-model level.

## High-DPI

Real-platform smoke at the machine's actual scaling (1920×1080, 150 %): every
button lies inside the window rectangle and no control is clipped (WP-09-02 and
WP-09-04 matrices, check `high-dpi-controls-in-bounds`).

## Defects

| Class | Count | Detail |
|---|---|---|
| V0 observations | 0 | — |
| V1 corrections | 1 | verification-harness only: the first draft of the new script inserted the blocked-output section at the wrong anchor and it became unreachable; the layout was corrected and the matrix re-run. No product code touched. |
| V2 blockers | 0 | — |
| V3 blockers | 0 | — |

## Acceptance

| Criterion | Result |
|---|---|
| Negative paths fail safely | PASS |
| Locked / unavailable output fails closed (no rename/retry/overwrite) | PASS |
| No data loss | PASS |
| Recovery to a usable state | PASS |
| Lifecycle safety (≤ 1 job, protected controls, close protection) | PASS |
| Keyboard / accessibility baseline | PASS |
| High-DPI smoke | PASS |

## Conclusion

WP-P12-09-05 passes. The release candidate fails closed on every negative path
it was given (missing/invalid source, Word-locked output, unavailable output,
missing artifact, stale remembered folder, off-screen geometry), recovers to a
usable state, keeps one active job with protected controls, and meets the
bounded keyboard/accessibility and high-DPI baseline.
