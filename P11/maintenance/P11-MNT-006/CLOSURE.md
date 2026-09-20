# P11-MNT-006 Closure Record

## Artifact Header

| Field | Value |
| --- | --- |
| Plan | Master Instruction — P11 ISSUE-008 → Conditional P11-MNT-006 (Bounded Maintenance Execution) |
| Work Package | P11-MNT-006 |
| Issue Source | ISSUE-008 — Production Usage Validation Cycle 01 (`Doc/production_soak/cycle_01/CLASSIFIED_ISSUES_CYCLE_01.md`) |
| Title | Optional Word COM Import Must Degrade Gracefully |
| Classification | DEFECT |
| Severity | P2 |
| Authority | `CANONICAL_SPEC.md` 1.0 FROZEN (SPEC-INV-006), `KNOWN_LIMITATIONS_v1.0.0.md` §3, `P11_CLASSIFICATION_RULES.md`, `P11_SEVERITY_RULES.md` |
| Status | CLOSED / ACCEPTED |

---

## 1. Objective

Ensure that optional Word COM availability/import failures neither terminate
MD_Converter package/CLI initialization nor prevent DOCX generation, while the
documented graceful-degradation contract (`KNOWN_LIMITATIONS_v1.0.0.md` §3:
no COM → native TOC field kept, page numbers refreshed with F9) is preserved.

## 2. Batch A — Triage Result

```text
Triage Result:      CONFIRMED_DEFECT
Reproduction:       Control A (normal env, MPC_Roadmap.md): exit 0, DOCX produced (5.0 s)
                    Control B (Cycle-01 minimal env: PATH + UTF-8 only):
                        exit 1, no DOCX, raw traceback
                        PermissionError: [WinError 5] Access is denied: 'C:\WINDOWS\gen_py'
                    Also reproduced at package level: `import md_converter` and
                    `from md_converter.renderer.post_processor import DocxPostProcessor`
                    both fail with the same PermissionError.
Root Cause:         `win32com.client` (an OPTIONAL enhancement) is imported at module
                    scope in md_converter/renderer/post_processor.py, with only
                    `except ImportError`. The pywin32 gencache initialisation failure
                    (PermissionError/OSError, e.g. when APPDATA/USERPROFILE/TEMP are
                    unavailable so the generate path resolves to C:\WINDOWS\gen_py)
                    escapes that guard during package import, so the CLI never regains
                    control. Failures outside the optional COM boundary were already
                    fail-closed and remain so.
```

## 3. Batch B — Bounded Patch

```text
Files Modified:     md_converter/renderer/post_processor.py   (optional COM boundary)
                    md_converter/cli.py                        (diagnostic presentation only)
                    md_converter/tests/test_com_optional_import.py  (new, 4 focused tests)

Patch Summary:      - COM import guard now catches the optional-dependency failure,
                      records WIN32_UNAVAILABLE_REASON ("<ExcType>: <message>") and marks
                      the capability unavailable instead of aborting the package.
                    - Post-processing reports a skipped COM refresh with the stable code
                      POST002 when the capability was requested but unavailable; the
                      intentional/not-applicable case keeps the previous informational line.
                    - The CLI surfaces the same reason once per run as a structured
                      diagnostic (POST002) in the existing diagnostics block.
                    - Native TOC insertion, Word COM call path, Word COM lifecycle and
                      the fail-closed behaviour outside the optional boundary are unchanged.
```

## 4. Batch C — Verification

```text
Focused Tests:      pytest md_converter/tests/test_com_optional_import.py -q → 4 passed
                    UT-COM-001  PermissionError during optional import → COM unavailable,
                                reason recorded, document still generated, POST002 emitted
                    IT-ENV-001  CLI in the Cycle-01 minimal environment → exit 0, DOCX
                                exists, no raw traceback
                    IT-ENV-002  CLI with injected failing win32com → exit 0, DOCX exists,
                                no traceback, [POST002] + diagnostics block present
                    NORMAL-COM-SMOKE  with COM available the Word refresh is still invoked
                                (dispatch-level; real COM round trip stays covered by
                                test_word_com_final_artifact.py)

Minimal-env Smoke:  exit=0 | DOCX=44715 bytes | traceback=no | POST002=yes | diagnostics block=yes
                    ⚠️ [POST002] Word COM 不可用（PermissionError: [WinError 5] Access is
                    denied: 'C:\WINDOWS\gen_py'）；已保留原生 TOC 域，页码可在 Word 中按 F9 刷新
                    ⚠️ [POST002] Word COM unavailable (...); native TOC field kept ...
                    (same document that previously produced exit 1 and no artifact)

Normal-env Smoke:   exit=0 | DOCX produced (44710 bytes) | no traceback
                    (COM call-time failure in this sandbox still degrades as documented)

Full Regression:    296 tests | 293 passed | 2 failed | 0 errors | 1 skipped
                    Failures (both Golden-environment gates, unrelated to this patch —
                    `test_golden.py` / `test_golden_environment.py` do not reference the
                    changed modules):
                      test_golden[sample]                          renderer_backend
                          baseline 'playwright' vs actual 'fallback'
                      test_canonical_golden_environment            Chromium cannot launch:
                          BrowserType.launch: spawn EPERM
                    Environment probe: playwright_installed=true,
                    chromium_launchable=false, backend=fallback, canonical=false
                    (sandbox blocks the Chromium process; GOLDEN_ENVIRONMENT.md declares
                    that a non-canonical environment MUST fail rather than pass).
                    Skip: test_word_com_roundtrip_final_artifact_qa_pass — existing
                    Windows release-gate skip (no interactive Word COM session).

Golden:             ENV_BLOCKED (not PASS, not modified). No Golden/baseline file was
                    touched; the failure is the documented canonical-environment gate.
```

## 5. Scope Audit

```text
Changed by P11-MNT-006:
    md_converter/renderer/post_processor.py
    md_converter/cli.py
    md_converter/tests/test_com_optional_import.py
    P11/maintenance/P11-MNT-006/CLOSURE.md
    P11/P11_MAINTENANCE_REGISTRY.md

Unauthorized product changes:        0
Unrelated issue changes:             0   (ISSUE-001..007, 009, 010, OBS-01..04 untouched)
Canonical Spec changes:              0
Architecture changes:                0
Golden baseline changes:             0
Acceptance Corpus source changes:    0
P12 implementation changes:          0
Theme YAML / parser / AST / pass-order changes: 0

Pre-existing (not part of P11-MNT-006), recorded before the task started:
    untracked: Doc/production_soak/ (Cycle 01 soak + audit evidence), Doc/MDC_Roadmap_0920.md|.docx,
               Test/, input_test/mermaid_triangle/, input_test/production_soak/
    tracked:   none (working tree had no tracked modifications)

Pre-existing condition found (report-only, NOT fixed — out of scope):
    `isort --check-only md_converter/cli.py` fails at HEAD as well as after this patch
    (verified by removing the P11-MNT-006 import line and re-running the check:
    both versions fail identically). Reformatting that import block is unrelated churn.
    black/ruff are clean on all three changed files.
```

## 6. Git

```text
Starting HEAD:               9ad1ce41985da812940e4bda8e2b2843e4026f91
Product Implementation SHA:  d6be63e3cdb1ace80f01caafb3c37497c0315a81
                             (fix(p11): guard optional Word COM import so conversion
                              always succeeds (P11-MNT-006))
Closure SHA:                 recorded in the post-commit final report
                             (P11_AGENT_PLAN_B §22: a commit cannot reference its own SHA)
Final git status:            tracked working tree clean; pre-existing untracked Cycle-01
                             evidence remains untracked by design
```

## 7. Closure Acceptance Checklist

```text
[x] ISSUE-008 reproduced before patch
[x] root cause confirmed
[x] change remained inside authorized scope
[x] PermissionError no longer aborts import/CLI
[x] COM unavailable path produces DOCX
[x] structured diagnostic/warning exists (POST002, warning + CLI diagnostics block)
[x] normal COM path still works (dispatch-level + normal-env CLI smoke)
[x] focused tests PASS (4/4)
[x] minimal-env smoke PASS
[x] normal-env smoke PASS
[x] full regression — no new failures attributable to this patch (2 Golden-environment
    failures and 1 release-gate skip are environment gates, verified independent of the
    changed modules; Golden baseline unchanged)
[x] Golden unchanged
[x] Canonical Spec unchanged
[x] Architecture unchanged
[x] Acceptance source unchanged
[x] unrelated ISSUEs untouched
[x] unauthorized changes = 0
```

## 8. Result

```text
P11-MNT-006: CLOSED / ACCEPTED
Patch Release: NOT AUTHORIZED (unchanged by this package)
Next Action: HUMAN REVIEW ONLY
```
