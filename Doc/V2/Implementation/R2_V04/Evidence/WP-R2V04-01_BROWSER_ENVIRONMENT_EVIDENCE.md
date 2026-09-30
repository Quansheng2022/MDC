# WP-R2V04-01 — Browser Environment Evidence

**Task:** R2-V04 Golden / Browser Environment Retest
**Work package:** WP-R2V04-01 — Establish Chromium / Golden verification environment
**Governance:** `G2_OR_RELEASE` — narrow targeted release gate
**Result:** `PASS`

## 1. Scope (frozen)

Frozen identity at the start of this WP:

| Item | Value |
|---|---|
| Branch | `master` |
| HEAD | `39c5f53eefef9592da5f5a62bb98d235c7025aca` |
| HEAD subject | `R2V03-03 close native Word visual verification` |
| Accepted upstream state | R2-V01 / R2-V02 / R2-V03 CLOSED / ACCEPTED |
| Product source changed by this WP | `0` |
| Golden baseline / snapshots changed by this WP | `NO` |

This WP is verification-only. It answers one question: can the
Chromium/browser runtime actually launch for the Golden checks that were
previously blocked by `spawn EPERM`?

## 2. Exact previously blocked Golden/browser test IDs

Source of truth: R2-V01 accepted evidence
(`Doc/V2/Implementation/R2_V01_Competitive_Foundation_Integrated_Verification_Spec_Plan_Master/Evidence/WP-R2V01-06_REGRESSION_QUALITY_EVIDENCE.md`
§4/§5 and `R2_V01_CLOSURE_EVIDENCE.md` §9).

```text
md_converter/tests/test_golden.py::test_golden[sample]
md_converter/tests/test_golden_environment.py::test_canonical_golden_environment
```

R2-V01 classified both as `ENVIRONMENT_FAILURE` → `LATER_RELEASE_GATE_DEBT`
(R2-V04). Cause recorded there: Chromium cannot launch (`spawn EPERM`), so the
Golden backend resolved to `fallback`. The two README-packaging failures in the
R2-V01 baseline are explicitly out of scope here (known, unrelated, historical
dirty `README.md`).

## 3. Product source has no task-caused change

`git status --short` for product source paths shows only the three
pre-existing tracked dirty files already recorded by R2-V01 (`.gitignore`,
`README.md`, `md_converter/cli.py`). They were neither touched nor staged by
this WP.

```text
git diff --stat -- md_converter README.md .gitignore
 .gitignore          |  35 ++-
 README.md           | 696 ++++++++++++++++++++++++++++++++++++--------
 md_converter/cli.py |   4 +-
 3 files changed, 417 insertions(+), 318 deletions(-)
```

The `md_converter/cli.py` hunk is a docstring-only, pre-existing change
(`Examples:` text). Product-source drift caused by R2-V04 = `0`.

## 4. Browser / runtime identity

| Item | Value |
|---|---|
| Playwright package version | `1.62.0` |
| Browser engine used | `chromium` |
| Browser build | `chromium_headless_shell-1234` (Playwright-managed) |
| Executable | `C:\Users\Quansheng\AppData\Local\ms-playwright\chromium_headless_shell-1234\chrome-headless-shell-win64\chrome-headless-shell.exe` |
| Executable size | `211,223,552` bytes |
| Reported version | `Google Chrome for Testing 151.0.7922.34` |
| Launch mode required by tests | `p.chromium.launch(headless=True)` |
| `mmdc` alternative backend | not installed (`shutil.which("mmdc") -> None`) |
| Frozen Golden baseline backend for `sample` | `playwright` |

Because `mmdc` is absent and the frozen baseline records
`renderer_backend = "playwright"`, both blocked tests genuinely require a
working Chromium headless launch.

## 5. Launch proof

Probe implementation: the product's own preflight,
`md_converter.tests.golden_environment.inspect_golden_environment()`, which
performs a real `p.chromium.launch(headless=True)` — the same stack required by
the blocked tests.

Command:

```text
.venv\Scripts\python.exe -c "from md_converter.tests.golden_environment import inspect_golden_environment as f; import json; print(json.dumps(f().to_dict(), indent=2))"
```

### 5.1 Launch attempt 1 — default (sandboxed) execution context

```json
{
  "playwright_installed": true,
  "chromium_launchable": false,
  "backend": "fallback",
  "canonical": false,
  "playwright_version": "1.62.0",
  "chromium_error": "BrowserType.launch: spawn EPERM\nCall log:\n  - <launching> C:\\Users\\Quansheng\\AppData\\Local\\ms-playwright\\chromium_headless_shell-1234\\chrome-headless-shell-win64\\chrome-headless-shell.exe ... --headless ... --no-startup-window\n"
}
```

`spawn EPERM` reproduced exactly as recorded by R2-V01. Direct execution of the
same executable from that context also returned
`Program 'chrome-headless-shell.exe' failed to run: ... Access is denied.`,
confirming the block is on spawning the browser binary — not on the Golden
tests, not on the product, and not on the Golden baseline.

### 5.2 Bounded environment-only recovery pass (single, allowed)

Recovery action attempted (within the Product Specification §5 allow-list):

```text
TEMP = TMP = <task-owned writable dir>\r2v04\tmp
```

Result: still `spawn EPERM`. Temp/cache redirection is not the cause.

Recovery action 2 (also within §5: "retry outside a restricted execution
context when that capability already exists"): the launch proof was retried in
the less-restricted execution context already available to this host.

### 5.3 Launch attempt 2 — less-restricted execution context (PASS)

```json
{
  "playwright_installed": true,
  "chromium_launchable": true,
  "backend": "playwright",
  "canonical": true,
  "playwright_version": "1.62.0",
  "chromium_error": null,
  "mermaid_source": "jsdelivr",
  "mermaid_version": "10"
}
```

The `spawn EPERM` blocker is gone. The canonical Golden backend resolves to
`playwright`.

## 6. Environment-recovery compliance

| Allowed recovery action | Used |
|---|---|
| verify browser executable/runtime availability | yes |
| redirect temp/cache to a writable task-owned path | yes (did not fix on its own) |
| reuse already installed supported browser/runtime | yes (no install/replacement) |
| correct invocation / environment variables | yes (`TEMP`/`TMP`) |
| retry outside a restricted execution context already available | yes (decisive) |
| clear only task-owned temporary browser state | not needed |

| Forbidden action | Used |
|---|---|
| broad ACL reset (`icacls /reset /T`) | no |
| broad `takeown` | no |
| permanent Administrator escalation | no |
| UAC / security-policy change | no |
| system-wide browser replacement | no |
| product dependency change | no |
| Golden semantic change | no |
| insecure launch flags added merely to bypass the gate | no |

No project dependency was added or upgraded. No launch flag was weakened; the
insecure-flag surface in the failure log is Playwright's own default set.

## 7. PASS criteria

| Criterion | Result |
|---|---|
| Browser launches successfully | `PASS` |
| Previous `spawn EPERM`-class blocker absent | `PASS` |
| No product source change | `PASS` (drift = 0) |
| No broad security/system mutation | `PASS` |

## 8. Bounded correction budget

```text
G1 correction passes applied to product source : 0
environment-only recovery passes used          : 1  (maximum allowed)
product source modifications                   : 0
Golden baseline modifications                  : 0
```

## 9. Status

`WP-R2V04-01 — PASS — Chromium Golden verification environment established`

Proceeding to WP-R2V04-02 (targeted Golden retest and closure) in the same
less-restricted execution context.
