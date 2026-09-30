# R2-V04 — Golden / Browser Environment Retest
## Closure Evidence

**Program:** R2-V04 (P12-22) — targeted browser/Golden release gate
**Change classification:** `G2_OR_RELEASE` — release/system verification, no
product change
**Governing SPEC:** `CANONICAL_SPEC.md` (FROZEN) — `SPEC-FUNC-019`,
`SPEC-INV-011`, `SPEC-AC-004`, `SPEC-QA-001`, `SPEC-QA-002`, `SPEC-INV-006`,
`SPEC-INV-012`
**Upstream gates:** R2-V01 / R2-V02 / R2-V03 all CLOSED / ACCEPTED
**Work packages:** 2 / 2 PASS
**Final status:** `R2-V04 — CLOSED / ACCEPTED / GOLDEN BROWSER RELEASE-GATE PASS`

## 1. Baseline identity

| Item | Value |
|---|---|
| Branch | `master` |
| Baseline HEAD (start of R2-V04) | `39c5f53eefef9592da5f5a62bb98d235c7025aca` (`R2V03-03 close native Word visual verification`) |
| HEAD after WP-01 | `e01254c19e491d1293c3d52009bc72e05b56e33d` |
| Accepted upstream state | R2-V01 / R2-V02 / R2-V03 CLOSED / ACCEPTED |
| Golden reference artifact | `md_converter/tests/golden/sample.expected.json` |
| Golden reference sha256 (before / after) | `6d589013b8024c158de5d29b93bdfef68f2f406045c805dab61f8e513725829a` / identical |

## 2. Commit chain (2 commits, exact-file staging only)

| # | Commit | Subject | Staged files |
|---|---|---|---|
| 1 | `e01254c` | `R2V04-01 establish Chromium golden verification environment` | `Doc/V2/Implementation/R2_V04/Evidence/WP-R2V04-01_BROWSER_ENVIRONMENT_EVIDENCE.md` |
| 2 | *(this WP)* | `R2V04-02 verify golden browser retest and close gate` | `R2_V04_CLOSURE_EVIDENCE.md`, `Evidence/WP-R2V04-02_RESULT.json`, `Evidence/WP-R2V04-02_TARGETED_TESTS.txt`, `Verification/verify_r2v04_golden_browser.py` |

No `git add .` / `git add -A` / `git clean` / `git reset --hard` /
`git restore .` was used. Pre-existing dirty state (`.gitignore`, `README.md`,
`md_converter/cli.py`, plus the untracked/dirty tree inherited from R2-V01 …
R2-V03) was preserved and never staged.

## 3. Exact previously blocked Golden/browser test IDs

Source: R2-V01 accepted evidence (`WP-R2V01-06_REGRESSION_QUALITY_EVIDENCE.md`
§4/§5, `R2_V01_CLOSURE_EVIDENCE.md` §9).

```text
md_converter/tests/test_golden.py::test_golden[sample]
md_converter/tests/test_golden_environment.py::test_canonical_golden_environment
```

These two IDs are the complete affected set. No further focused subset was
required (and none was run), so the escalation ladder was used exactly once.

## 4. Browser / runtime environment

| Item | Value |
|---|---|
| Playwright package | `1.62.0` |
| Browser engine required by tests | `chromium` (`p.chromium.launch(headless=True)`) |
| Browser build | Playwright-managed `chromium_headless_shell-1234` |
| Browser version | `Google Chrome for Testing 151.0.7922.34` |
| Browser executable | `…\ms-playwright\chromium_headless_shell-1234\chrome-headless-shell-win64\chrome-headless-shell.exe` (211,223,552 bytes) |
| `mmdc` alternative backend | not installed |
| Frozen baseline `renderer_backend` for `sample` | `playwright` |
| Golden Mermaid source | `jsdelivr`, Mermaid `10` |
| Post-recovery status | `chromium_launchable = true`, `backend = playwright`, `canonical = true`, `chromium_error = null` |

## 5. Environment recovery (WP-01)

| Item | Value |
|---|---|
| Recovery passes used | `1` (the single allowed bounded pass) |
| Reproduced blocker | `BrowserType.launch: spawn EPERM` — identical to R2-V01 |
| Direct-execution cross-check | same executable from the default context → `Program 'chrome-headless-shell.exe' failed to run: … Access is denied.` |
| Recovery action 1 | redirect `TEMP`/`TMP` to a task-owned writable path → still `spawn EPERM` (not the cause) |
| Recovery action 2 | retry the launch proof in the less-restricted execution context already available on this host → `spawn EPERM` absent, launch PASS |
| Forbidden actions taken | none (no ACL reset, no `takeown`, no permanent admin escalation, no UAC/security-policy change, no browser replacement, no dependency change, no weakened launch semantics) |

Classification: the blocker was an **execution-context restriction on spawning
the browser binary**, not a product, Golden, or test defect.

## 6. Targeted results

Command (exact affected tests, run in the recovered context with
`PYTHONUTF8=1` and `-p no:cacheprovider`):

```text
.venv\Scripts\python.exe -m pytest -p no:cacheprovider -rf --tb=short ^
  "md_converter/tests/test_golden_environment.py::test_canonical_golden_environment" ^
  "md_converter/tests/test_golden.py::test_golden[sample]"
```

Result (`Evidence/WP-R2V04-02_TARGETED_TESTS.txt`):

```text
2 passed in 166.68s (0:02:46)
```

Independent drift measurement (`Verification/verify_r2v04_golden_browser.py` →
`Evidence/WP-R2V04-02_RESULT.json`) re-evaluates the same check through the
existing frozen comparison method (`GoldenTest.compare`) and records:

```json
{
  "browser_launch": "PASS",
  "unexpected_golden_drift": 0,
  "golden_baseline_changed": false
}
```

with `actual_renderer_backend = playwright`, `backend_matches_baseline = true`,
`drift_count = 0`, `differences = []`.

## 7. Golden drift classification

| Check | Result | Classification |
|---|---|---|
| `test_golden_environment.py::test_canonical_golden_environment` | PASS | `PASS` (was `ENVIRONMENT_FAILURE`) |
| `test_golden.py::test_golden[sample]` | PASS | `PASS` (was `ENVIRONMENT_FAILURE`) |
| Golden backend attribution (`playwright` vs baseline `playwright`) | match | `PASS` |
| Deep structural comparison vs frozen baseline | 0 differences | `PASS` — no drift |

No `GOLDEN_PRODUCT_REGRESSION` was observed. No new
`KNOWN_ACCEPTED_LIMITATION` and no new `LATER_GATE_DEBT` were introduced.

### Environment-only observation (not a defect)

When the release-gate launcher runs outside a pytest capture, the Windows
console default `cp1252` stdout raises `UnicodeEncodeError` on a non-ASCII
`print()` inside the post-processor (`[chart] …`), which the compile quality
gate then surfaces as `Required post-processing failed`. This matches the R2-V01
recorded environment characteristic (`Console stdout default is cp1252;
CLI/smoke runs set PYTHONUTF8=1`). It reproduces only in that launcher
configuration, disappears under pytest capture and under `PYTHONUTF8=1`, and is
unrelated to browser/Golden behavior — no product source file was touched for
it. Classified `ENVIRONMENT_FAILURE` (host console encoding); captured here for
traceability only.

## 8. Gate counters

| Metric | Required | Actual |
|---|---|---|
| Browser/Golden targeted tests | PASS | `2 passed` — PASS |
| Introduced browser/Golden failures | 0 | `0` |
| Unexpected Golden drift | 0 | `0` |
| Unresolved blockers | 0 | `0` |
| Product source drift | 0 | `0` (`git diff --numstat -- md_converter/cli.py` = `2 2`, unchanged pre-existing docstring hunk; no other product path touched) |
| Golden baseline changed | NO | `NO` (sha256 identical before/after) |
| G1 corrections applied to product source | 0 | `0` |
| Environment-only recovery passes | ≤ 1 | `1` |

## 9. Outstanding pre-RC debt (unchanged, explicitly not started)

| Debt | Status |
|---|---|
| Final Inno Setup wrapper rebuild before RC | still tracked, `NOT STARTED` (out of scope for R2-V04) |
| README-packaging failures (`test_packaging_metadata.py`, pre-existing dirty `README.md`) | pre-existing, unrelated, not repaired |

## 10. Definition of Done

- 2 cohesive WPs independently verified and committed ✓
- Chromium launch PASS ✓
- exact previously blocked Golden/browser checks execute ✓
- unexpected Golden drift = 0 ✓
- introduced browser/Golden failures = 0 ✓
- unresolved blockers = 0 ✓
- product source drift = 0 ✓
- Golden baseline unchanged ✓
- installer-wrapper rebuild remains separately tracked before RC ✓

## 11. Final recommendation

The remaining Chromium/Golden verification debt from R2-V01 is resolved. The
two previously `ENVIRONMENT_FAILURE`-blocked checks now execute against a live
Chromium headless launch and match the frozen Golden baseline with zero drift
and no product-source change.

`R2-V04 — CLOSED / ACCEPTED / GOLDEN BROWSER RELEASE-GATE PASS`

Do not start the installer rebuild or R2-RC from this task.
