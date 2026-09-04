# P11 Maintenance Change Package — P11-MNT-001

## Artifact Header

| Field | Value |
| --- | --- |
| Plan | P11_AGENT_PLAN_B — Maintenance Change Package Execution |
| Change Package | P11-MNT-001 |
| Authority | `Doc/Phase_11_Maintenance_Specification.md` v1.0（§8 Maintenance Change Package / §12） |
| Status | **RATIFIED（HG-B4）/ SCOPE EXPANDED（HG-B2）/ IMPLEMENTED — Verification / Closure 进行中** |
| Date | 2026-09-04 |

---

# 1. B-00 Preflight / B-01 Authority Evidence

```text
Git repository      PASS
Branch              master
HEAD                42394ad3d3541a8a92a7a5790ae2d32af49e6abe
v1.0.0 type         tag
v1.0.0 target       5d2c92a6af662ec8ee392f5a1a4d66f1f022229e
Working Tree        CLEAN（登记文档创建前）

P11_AGENT_PLAN_A       CLOSED / ACCEPTED
P11-MNT-GOV-01         CLOSED / ACCEPTED
P11 Authority          FROZEN / ACTIVE
P11 Program            ACTIVE

Release Baseline:
v1.0.0 -> 5d2c92a6af662ec8ee392f5a1a4d66f1f022229e

P10 Governance Closure:
dab9142f1ece898f7dcd66c2fe53d6106f59230c

P11 Authority Freeze:
bddf36f0ae5667c485aca7cd7132a38d765eb5cc

P11 Governance Foundation:
617463ef0f412211e5bfad98c934d27b1d01895b

P11 Governance Closure:
76a3b52d8f68b970672990045757bd5164d59628
```

---

# 2. Package Definition

```text
Change Package:
P11-MNT-001

Title:
Isolate Word COM Availability Probe from Pytest Collection

Source:
PLAN_A final validation 期间发现的真实 issue（strict merger 检测到
pytest collection 期 Windows fatal signature）

Classification:
TEST_DEFECT

Severity:
P2 Major

Affected Version:
v1.0.0 maintenance line

Affected Component:
md_converter/tests/test_word_com_final_artifact.py

Problem:
Word COM availability probe 在 pytest collection / module import 阶段执行
DispatchEx("Word.Application")，可在 pytest 主进程触发 Windows fatal
exception（0x800706be），而 pytest 仍返回 rc=0，破坏 evidence trust。

Reproduction:
见 REPRODUCTION.md —— CONFIRMED。

Expected:
pytest collection 不启动 Word COM lifecycle；COM integration 仍经真实
生产路径测试；fatal signature = 0。

Actual:
module-level availability detection 在 collection 期启动 Word COM 并可能
输出 Windows fatal RPC signature（pytest rc=0）。

Evidence:
- REPRODUCTION.md / ROOT_CAUSE_ANALYSIS.md
- RC_EVIDENCE\P10_COM01\P10_COM01_before.txt（历史同类 collection 期 fatal）
- Merged_Code\merged_MDC_phase11_foundation_review.txt
  （post-fix：277 passed、fatal=0、PASS）

Root Cause:
verified test design defect —— pytest collection 期 Word COM lifecycle
coupling（详见 ROOT_CAUSE_ANALYSIS.md）。

Potential P12 Boundary:
NO

Product Semantics Change:
NONE

Architecture Change:
NONE
```

---

# 3. Governance Sequence Deviation（Special Condition）

```text
Governance Sequence Deviation:
YES

Reason:
TEST_DEFECT 在 PLAN_A final validation 期间被发现，bounded test correction
先于正式 Change Package 完成并提交：

Package Base SHA:      3eb1b95dac3d2201242a32d7f52f49d248249b56
Existing Patch Commit: 42394ad3d3541a8a92a7a5790ae2d32af49e6abe
                        （md_converter/tests/test_word_com_final_artifact.py）

Historical Approval Before Patch:
NO / NOT RECORDED

Current Action:
Retrospective governance reconciliation。

AI Agent 不得伪造 "P11-MNT-001 was approved before implementation"。
No further implementation changes are authorized until HG-B4。
```

### HG-B4 — Human Decision Required

```text
Human 只有两个合法选择：

A. RATIFY EXISTING BOUNDED PATCH
   -> 保留现有 commit 42394ad
   -> PLAN_B 继续 B-09 Verification / Closure

B. REJECT / REQUIRE PROCEDURAL REPLAY
   -> revert existing patch
   -> Change Package APPROVED
   -> 重新执行 bounded patch
```

Human 决策（2026-09-04）：**A — RATIFY EXISTING BOUNDED PATCH**。
AI Agent 已获授权继续 B-09 之后的 Verification / Closure。

---

# 3a. HG-B2 — Scope Expansion Record

```text
Scope Expansion:
YES

Approval Date:
2026-09-04

Reason:
PLAN_B B-12 / DoD 要求 maintenance merged manifest 包含
md_converter/tests/test_word_com_final_artifact.py；冻结 merger v1.1.0 的
inclusion policy 未覆盖 md_converter 包根（测试位于 md_converter/tests/），
无法在未修改工具的情况下满足验收。Human 选择方案 2，批准在本包内做
有界工具修正。

Authorized Addition to Allowed Scope:
tools/review/merge_project_for_phase11_review.py

Approved Bounded Change:
- SOURCE_ROOT_NAMES 增加 "md_converter"（maintenance/release 模式纳入
  MDC 产品包根，使 bounded patch review 快照包含产品代码与被修改测试）
- TOOL_VERSION: 1.1.0 -> 1.2.0，附变更说明注释

Scope of Change:
- 仅影响 merger 的文件枚举 inclusion policy（maintenance / release 模式）
- foundation 模式行为不变
- 不修改任何 product code / Canonical / Golden / Acceptance
```

---

# 4. Allowed Scope

```text
Allowed Scope（本包）:
P11/P11_MAINTENANCE_REGISTRY.md
P11/maintenance/P11-MNT-001/ISSUE_INTAKE.md
P11/maintenance/P11-MNT-001/REPRODUCTION.md
P11/maintenance/P11-MNT-001/ROOT_CAUSE_ANALYSIS.md
P11/maintenance/P11-MNT-001/CHANGE_PACKAGE.md
P11/maintenance/P11-MNT-001/TARGET_VERIFICATION.md（HG-B4 后填写）
P11/maintenance/P11-MNT-001/REGRESSION_EVIDENCE.md（HG-B4 后填写）
P11/maintenance/P11-MNT-001/SCOPE_AUDIT.md（HG-B4 后填写）
P11/maintenance/P11-MNT-001/GIT_CLOSURE.md（HG-B4 后填写）
P11/maintenance/P11-MNT-001/CLOSURE.md（HG-B4 后填写）
md_converter/tests/test_word_com_final_artifact.py（仅现有 bounded patch；
不再新增代码修改，直到 HG-B4）

tools/review/merge_project_for_phase11_review.py
（HG-B2 于 2026-09-04 批准加入 Allowed Scope：
SOURCE_ROOT_NAMES 增加 "md_converter"；TOOL_VERSION 1.1.0 -> 1.2.0）
```

---

# 5. Forbidden Scope

```text
CANONICAL_SPEC.md
Doc/ARCHITECTURE.md
md_converter/compiler.py
md_converter/renderer/post_processor.py
md_converter/renderer/word_renderer.py
md_converter/renderer/word_writer.py
md_converter/renderer/layout/**
md_converter/parser/**
md_converter/ast/**
md_converter/pipeline/**
md_converter/tests/acceptance/**
md_converter/tests/golden/**
RELEASE_MANIFEST_v1.0.0.json
RELEASE_NOTES_v1.0.0.md
RC_EVIDENCE/**
P10/**
v1.0.0 tag
P10 historical commits
P11 PLAN_A frozen history
```

若修复确实需要修改 Forbidden Scope 文件：

```text
STOP
-> REPORT
-> REQUEST_SCOPE_EXPANSION（HG-B2）
-> WAIT
```

未列入 Allowed Scope 的文件默认禁止修改；禁止以重构 / 整洁 / 技术债等
理由扩大范围。

---

# 6. Required Tests

```text
Dedicated Word COM test（3/3 连续运行）
Full pytest regression（277/277 PASS）
Phase 11 maintenance merger（--mode maintenance --run-pytest --strict）
Golden / Acceptance guard（不修改 baseline）
```

---

# 7. Conditional Gates

```text
COM                            = REQUIRED（dedicated + DOCX）
DOCX / FinalArtifactQA         = REQUIRED（经真实 integration path）
Packaging                      = NOT REQUIRED
Fresh Install                  = NOT REQUIRED
Golden                         = NOT MODIFIED
Acceptance                     = NOT MODIFIED
```

---

# 8. Acceptance Criteria

```text
Targeted COM test:               PASS 3/3
Fatal COM signature:             0
Unexpected Skip:                 0
Full Regression:                 277/277 PASS，New Failure = 0
Maintenance merger strict:       PASS
Golden drift:                    0
Acceptance drift:                0
Canonical drift:                 0
Architecture drift:              0
Release tag drift:               0
P10 history drift:               0
Unauthorized files:              0
git diff --check:                PASS
Working tree:                    CLEAN
```

---

# 9. Rollback

```text
如 Human 选择 B（REJECT / REQUIRE PROCEDURAL REPLAY）：
revert commit 42394ad 对该文件的有界修改后重放；Registry 与包证据按
实际执行顺序重建。Rollback 不触碰 v1.0.0 tag / P10 history / frozen
governance history。
```

---

# 10. Git Closure（HG-B4 后执行）

```text
exact diff
authorized files only
git diff --cached --check PASS
working tree CLEAN
closure commit SHA recorded
（详见 B-17 / GIT_CLOSURE.md）
```

---

# 11. Status

```text
Registry Status:
OPEN（登记 / 分类 / 定级 / Repro / RCA 完成）

Package Lifecycle State:
PACKAGE_DRAFTED
    ↓
WAITING_HUMAN_APPROVAL（HG-B4）

下一步:
Human 决策（RATIFY / REJECT）
```
