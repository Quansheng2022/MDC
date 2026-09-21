# P12 v1.1.0 Release Candidate Evidence

## Artifact Header

| Field | Value |
| --- | --- |
| Product | MD_Converter |
| Release candidate | **v1.1.0**（minor / feature） |
| Authority | P12 Release Readiness instruction（Human, 2026-09-21）：implementation acceptance + RC preparation |
| Release-preparation baseline | `5862edaad3c0d6f39ea6e00a90bd8e383e146b00`（P12 implementation HEAD） |
| Scope freeze | P12-CAND-002 + P12-CAND-001 + P12-CAND-003 + required tests/fixtures/docs/version metadata only |
| Publication status | NOT PUBLISHED — production release approval pending |

---

## 1. Release scope（frozen）

```text
P12-CAND-002  Figure Page-Fit / Figure Size Policy      IMPLEMENTED / VERIFIED / HUMAN ACCEPTED
P12-CAND-001  Simple Table Recognition                  IMPLEMENTED / VERIFIED / HUMAN ACCEPTED
P12-CAND-003  Empty Heading Behaviour（WARN + DROP）     IMPLEMENTED / VERIFIED / HUMAN ACCEPTED
required supporting tests / acceptance fixtures / approved P12 documentation / release metadata
no additional feature entered this candidate
```

## 2. Version decision basis

```text
Resolved version: 1.1.0
Authority: P11/P11_PATCH_RELEASE_GATE.md §2 Version Policy
    Bug / Security / Compatibility fix      -> 1.0.1, 1.0.2, ...
    Backward-compatible feature             -> P12 -> candidate 1.1.0   <== this release
    Canonical semantic change               -> P12
    Breaking change                         -> P12 -> candidate 2.0.0
No conflicting authoritative rule found.
```

## 3. Build artifacts（最终版；`python -m build --no-isolation --outdir dist`，exit code 0）

| Artifact | Size | SHA256 | Embedded version |
| --- | --- | --- | --- |
| `md_converter-1.1.0-py3-none-any.whl` | 337,661 B | `941e09eeee018bd3b256027df4dba822a8da3f129506444f8521bd02671b0f4a` | 1.1.0 |
| `md_converter-1.1.0.tar.gz` | 282,686 B | `f060c7c807c3a6f09fcae2a91fd34f30757a4a183cff93cc2b6add3f66e4c96d` | 1.1.0 |

Final artifacts were rebuilt from the frozen **RC Payload Source SHA
`4b7d5ea3cbfc123750e3ff5551db45cd1d5e1c94`**（canonical incorporation + re-freeze）.
Both hashes differ from the earlier RC-stage build because the packaged canonical-identity constant
`md_converter/release_evidence.py`（`SPEC_VERSION` 1.0 → 1.1）changed；the earlier values are preserved
in `artifact_integrity.json`（labelled as superseded）.

Integrity checks（`final_artifact_integrity.json`）：wheel/sdist identity agreement PASS；
forbidden entries = 0（no `venv` / cache / production-soak corpus / browser binary / temporary Word
file / untracked Human file）；wheel ships the frozen theme YAML, `py.typed`, `SimpleTablePass`,
`figure_sizing` and the AC010–AC018 acceptance fixtures；canonical identity 1.1 present in the wheel.

Local release bundle（regenerated after canonical incorporation，offline hash check PASS）：
`dist/release_bundle_v1.1.0.zip`（637,890 B，SHA256
`e75a559d2eda9e62637220517521a061d57bab5ff0186bf04cc13957273291e8`，16 entries）——
明细见 `final_release_bundle.json`；bundle 哈希不写入 manifest（避免自引用）。

## 3.1 Canonical specification identity（v1.1 re-freeze）

```text
CANONICAL_SPEC.md   spec_version 1.1 / spec_status FROZEN / freeze_date 2026-09-21
Supersedes          spec 1.0（FROZEN 2026-08-30；记录保留于 SPEC_CHANGELOG.md）
Incorporated        SPEC-FUNC-022 / SPEC-FUNC-023 / SPEC-FUNC-024
                    SPEC-INV-013 / SPEC-INV-014 / SPEC-QA-005
Amended（minimal）  Acceptance 基线 AC001–AC015 → AC001–AC018（SPEC-FUNC-020、§4.1、§6）
Clarifications      CLAR-01（识别失败不产生诊断）/ CLAR-02（有效 section 内容区）
Unchanged           SPEC-GOAL / SPEC-ARCH / SPEC-FUNC-001..021 / SPEC-INV-001..012 /
                    SPEC-QA-001..004 / SPEC-AC / SPEC-NON、冻结主题值、架构与依赖方向
ADR                 none required（有界实现面；无新阶段 / 所有权迁移 / LayoutPlan 扩展）
Changelog           SPEC_CHANGELOG.md §1.1（FROZEN，2026-09-21）
```

## 4. Fresh installation（`final_fresh_install_and_smoke.json`）

```text
NEW isolated venv created outside the editable source workflow; FINAL BUILT WHEEL installed
    pip install --no-deps --no-index dist/md_converter-1.1.0-py3-none-any.whl
Import proof: md_converter.__file__ inside the fresh venv site-packages
    module version 1.1.0 / installed metadata version 1.1.0
Environmental limitation: the sandbox has no index access and an empty pip wheel cache, so the four
    runtime dependencies were staged from the verified .venv at identical versions（click 8.4.2,
    python-docx 1.2.0, markdown-it-py 4.2.0, PyYAML 6.0.3）. The wheel's own contents were not altered.
```

## 5. CLI verification（installed wheel）

```text
md-converter --help                 exit 0（usage printed）
md-converter-check --json-output    exit 0（required 4 / optional 2 / ok true）
md-converter <AC017> -o <docx> --no-open
                                    exit 0, DOCX produced, 1 table present
POST002（Word COM unavailable in the agent sandbox）: documented degradation, native TOC field kept
```

最终 wheel 的 CLI 复验见 `final_fresh_install_and_smoke.json`（`--help` / `check` / 转换均 exit 0）。

## 6. Representative P12 verification（installed wheel; `representative_verification.json`）

| Candidate | Evidence | Result |
| --- | --- | --- |
| P12-CAND-002 | content box 15.92 × 24.62 cm; tall figure emitted at 10.552 × 24.620 cm | fits content box；clamped to content height；aspect ratio preserved；no upscale beyond target width；RenderedQA PASS；`figure_overflow = 0`；`figure_below_min_width = 0` |
| P12-CAND-001（positive） | AC017 | 1 table, 3 rows × 2 columns, header `普通软件工程关注 / Governance Engineering 额外关注`, ruler row absent, FinalArtifactQA PASS, content coverage 1.0 |
| P12-CAND-001（conservative rejection） | ruler present but inconsistent columns | 0 tables；block kept as paragraph；**no diagnostic**（CLAR-01） |
| P12-CAND-003 | AC018 | no literal `Heading` paragraph；rendered headings = TOC entries = 2；`semantic_empty_heading` WARNING retained；StaticQA PASS_WITH_WARN |

最终 wheel 的同类复验见 `final_fresh_install_and_smoke.json`（CAND-001 / CAND-002 / CAND-003 全部 PASS）。

## 7. Canonical Golden and Word COM

```text
NON-CANONICAL AGENT EXECUTION ENVIRONMENT — NOT THE RELEASE-GATE RESULT:
    Chromium launch          FAIL — BrowserType.launch: spawn EPERM（backend=fallback）
    Word COM                 UNAVAILABLE — win32com importable but COM dispatch fails
                             （"A specified logon session does not exist"）/ no interactive session
    => these two gates cannot execute here; Golden baseline NOT modified

AUTHORITATIVE RELEASE-GATE EVIDENCE — executed by the Human, not by the Agent
（`human_canonical_verification.json`, Human Product / Release Authority, 2026-09-21）:

    Canonical Golden   python -m pytest md_converter/tests -q -k "canonical_golden_environment or golden"
                       observed: "....."  → PASS
    Word COM           python -m pytest md_converter/tests -q -k "wordcom or word_com"
                       observed: ".." + [100%] → PASS
    Full regression    python -m pytest md_converter/tests -q
                       observed: [100%]；PowerShell $LASTEXITCODE = 0 → PASS / EXIT 0

    The previous "spawn EPERM" is classified EXECUTION-ENVIRONMENT-SPECIFIC LIMITATION, CLOSED,
    not a product defect and not a local canonical-environment defect.
```

## 8. Final full regression（agent environment）

```text
command: python -m pytest md_converter/tests -q
result:  352 tests, 2 failures, 0 errors, 2 skipped（44.2 s）
passed:  348
failed:  test_canonical_golden_environment, test_golden[sample]   -> both environment-contract gates
skipped: test_it_wordcom_001_table_count_survives_word_roundtrip,
         test_word_com_roundtrip_final_artifact_qa_pass          -> documented Word COM gates
artifacts: full_regression_agent_environment.{txt,xml}, full_regression_agent_environment_summary.json
note: the two failures and two skips are the environment gates listed in §7; the Human canonical run
      accepted for those gates is PASS with process exit code 0.
```

## 9. Scope audit and Human-work preservation

```text
changed: P12 status documents（acceptance record）, version surfaces（pyproject.toml,
         md_converter/__init__.py, two version-assertion tests）, RELEASE_MANIFEST_v1.1.0.json,
         RELEASE_NOTES_v1.1.0.md, RC_EVIDENCE/P12_v1.1.0/*
not changed: CANONICAL_SPEC.md, frozen theme YAML, P11 records, package architecture,
         P12 implementation source（no product behaviour change in this phase）
unauthorized change: 0
untracked Human work: unchanged（Doc/MDC_Roadmap_0920.*, Doc/production_soak/, Test/,
         input_test/mermaid_triangle/, input_test/production_soak/）
```

## 10. Known limitations（release-facing）

```text
Simple-table recognition is intentionally conservative（2 columns / plain-text cells / top-level
    paragraphs / ruler required）and emits no diagnostic when it declines a block
Final physical pagination remains Word-owned（no page-number or pagination-determinism promise）
Figure minimum-width handling is bounded by the approved policy（fitted delivery + WARNING）
Extremely wide figures（very small rendered height）are not addressed by the size policy
P12 canonical specification proposal is Human-approved but not yet incorporated into the frozen
    CANONICAL_SPEC.md 1.0 document（spec update + SPEC_CHANGELOG + re-freeze not part of this authority）
```

## 11. Next gate

```text
NEXT HUMAN GATE: PRODUCTION RELEASE APPROVAL
    （tag creation / remote push / publication remain NOT AUTHORIZED）
```
