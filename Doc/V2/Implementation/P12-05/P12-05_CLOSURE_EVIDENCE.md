# P12-05 — GUI/Core Integration: Closure Evidence

**Phase:** P12-05 — GUI/Core Integration
**Status:** CLOSED / ACCEPTED
**Authority:** G1 (no G2 trigger hit)

---

## 1. Baselines

```text
P12-04 closure baseline (P12-05 starting point)  4356ca7ede841d50e8d255ca9dfd79365f16bec4
WP-P12-05-06 implementation baseline             ac1168588d453c096913d63ac2b450fdb1088373
Specification baseline                            d4c0d3a798f9b0a8918c7aa8b35a4f70f23f9601
```

Work package closure SHAs:

```text
WP-P12-05-01 worker boundary            80e4e76
WP-P12-05-02 request builder            c97d046
WP-P12-05-03 real conversion slice      38c18d0
WP-P12-05-04 result mapping             65d2efd
WP-P12-05-05 lifecycle hardening        ac1168588d453c096913d63ac2b450fdb1088373
WP-P12-05-06 verification and closure   this work package (no production code change)
```

---

## 2. Verification results

```text
GUI / integration tests      175 passed / 0 failed
Application-layer tests       72 passed / 0 failed
Focused regression           299 total / 297 passed / 2 failed
Full regression              599 total / 597 passed / 2 failed / 0 errors / 0 skipped
Known pre-existing failures    2 packaging_metadata README failures (approved baseline exception)
P12-05 introduced failures     0
Qt-lifecycle repeats           3 x clean (worker + lifecycle + slice + mapping modules)
Real Windows GUI smoke         launch -> EMPTY -> READY -> output folder -> CONVERTING -> SUCCESS -> close
```

---

## 3. Real conversion and boundaries

```text
Real GUI conversion        real .docx produced through GUI -> Worker -> ConversionService -> Core
Generated DOCX             pytest: PK container, non-empty; real Windows: notes.docx 37,250 bytes
                           written into the user-selected output folder
ConversionService calls    exactly 1 per Convert activation
Worker-thread evidence     service execution thread id != GUI thread id
GUI-thread completion      result delivered on the GUI thread
Request construction       accepted request builder reused; output intent via
                           config_overrides={"output_dir": ...}; no frontmatter/filename policy in GUI
Result mapping             centralized (only result_mapping.py interprets ConversionStatus);
                           SUCCESS / SUCCESS_WITH_WARNING / FAILED map 1:1
Result retention           complete ConversionResult retained (diagnostics, warnings, errors,
                           QA evidence, output path); JobFailure kept distinct, never fabricated
Duplicate protection       one worker.start, one service call, one QThread per activation
Source immutability        picker, forced set_source and forced drop rejected while CONVERTING
Output immutability        Change disabled; set_output_directory refused; active request stable
Sequential reuse           repeated conversions in one window without restart
Window-close behavior      close blocked while worker.is_running (running and cleanup),
                           succeeds after completion; no force termination
```

---

## 4. Architecture and drift

```text
Direct Core calls from GUI      0
Application-layer Qt dependency 0
Core semantic changes           0
Canonical semantic changes      0
Golden changes                  0
CLI behavior changes            0
Unauthorized drift              0
Open blockers                   0
```

---

## 5. Known deferred issues (outside P12-05)

```text
1. DocxPostProcessor emoji print / cp1252 console UnicodeEncodeError
   (known pre-existing environment-dependent defect; packaged behaviour must be
   re-verified in the P12-08 packaging environment)
2. Invalid YAML frontmatter silently swallowed
3. Existing tests rewriting output\document.docx
4. Approved packaging_metadata README baseline failures (2)
5. Pre-existing unrelated dirty/untracked working-tree files
```

---

## 6. Decision

```text
P12-05 GUI/CORE INTEGRATION = CLOSED / ACCEPTED
Next authorized phase = P12-06 Error / Diagnostics UX
```
