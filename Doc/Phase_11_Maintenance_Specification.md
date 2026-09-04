# Phase 11 Maintenance Specification

## MD_Converter v1.x Maintenance Program

| 项目 | 值 |
| --- | --- |
| Project | MD_Converter（Markdown → DOCX Compiler） |
| Phase | **P11 — Maintenance** |
| Spec 版本 | **1.0** |
| 创建日期 | **2026-09-04** |
| 当前状态 | **FROZEN / ACTIVE** |
| Authority Role | **P11 Maintenance Authority** |
| Product Canonical Authority | `CANONICAL_SPEC.md` 1.0 FROZEN |
| P10 Release Baseline | annotated tag `v1.0.0` → `5d2c92a6af662ec8ee392f5a1a4d66f1f022229e` |
| P10 Final Governance Closure | `dab9142f1ece898f7dcd66c2fe53d6106f59230c` |
| Maintenance Version Line | `v1.0.x` patch releases by default |
| Evolution Boundary | Feature / semantic / architecture evolution → **P12 Evolution** |

---

# 1. Authority and Governance Model

## 1.1 Authority Hierarchy

P11 采用以下权威顺序：

```text
CANONICAL_SPEC.md
    ↓
ADR / Frozen Architecture Decisions
    ↓
Phase_11_Maintenance_Specification.md
    ↓
IMPLEMENTATION_PLAN.md
    ↓
Approved P11 Maintenance Change Package
    ↓
Implementation
    ↓
Test / Evidence
```

解释：

1. `CANONICAL_SPEC.md` 继续定义 **产品语义与不可违反的不变量**。
2. ADR / Frozen Architecture Decisions 继续定义 **架构边界与已冻结设计决策**。
3. 本文档定义 **P11 Maintenance 的流程、权限、分类、测试、Release Gate 与 Closure 规则**。
4. `IMPLEMENTATION_PLAN.md` 用于登记已批准的实际实施条目，不得反向修改本 Authority。
5. 单个 Maintenance Change Package 只能在本文档允许的边界内执行。
6. Test / Evidence 用于验证实现，不得替代 Canonical Authority 或人为改写产品语义。

若发生冲突：

```text
Canonical > ADR > P11 Maintenance Authority > Implementation Plan
> Change Package > Implementation > Test Convenience
```

## 1.2 Human Gate

以下事项必须由 Human 明确批准，不得由 AI Agent 自动完成：

- P11 Maintenance Authority Freeze
- SPEC_GAP 的 Canonical clarification
- ARCH_CHANGE 的 ADR / Architecture approval
- Patch Release Approval
- Release Tag Approval / Ratification
- P11 Final Closure

---

# 2. Purpose

P11 的目标是：

> **在不破坏 MD_Converter v1.0.0 Canonical 行为和 Frozen Core 的前提下，对生产使用过程中发现的真实缺陷、稳定性、兼容性、安全性、依赖和文档一致性问题实施可审计、可验证、最小化的维护。**

P11 不是继续开发新功能的阶段。

核心目标：

1. 保持 v1.x 正确性和稳定性。
2. 对真实问题实施最小范围修复。
3. 防止 Maintenance 演变为无边界重构。
4. 防止 Optional Improvement 被包装成 Defect。
5. 防止 Golden / Acceptance baseline 为迁就实现而漂移。
6. 保持每个变更可追溯、可测试、可回滚、可 Git 收口。
7. 需要时产生受控的 `v1.0.x` Patch Release。
8. 将 Feature / Semantic / Architecture Evolution 明确隔离到 P12。

---

# 3. P11 Baseline

## 3.1 Release Baseline

```text
Release:
v1.0.0

Annotated Tag:
v1.0.0

Tag Target:
5d2c92a6af662ec8ee392f5a1a4d66f1f022229e
```

该 tag 是正式 production release baseline，P11 不得移动、删除、重建或强制覆盖该 tag。

## 3.2 Governance Baseline

```text
P10 Final Governance Closure Commit:
dab9142f1ece898f7dcd66c2fe53d6106f59230c
```

P11 从 P10 完整治理收口后的 repository 状态开始。

## 3.3 Baseline Protection

除非有经过批准的 Maintenance Change Package，否则禁止修改：

- `CANONICAL_SPEC.md`
- Frozen Core
- Golden expected structure / semantic meaning
- Acceptance Corpus meaning
- Release tag `v1.0.0`
- 已关闭的 P10 evidence
- 已冻结的 P10 release artifacts / hashes / manifest

---

# 4. Scope

## 4.1 Allowed Maintenance Scope

P11 允许：

| 类型 | 是否允许 | 典型示例 |
| --- | --- | --- |
| Product Defect Fix | ✅ | 错误 DOCX、错误决策、异常 crash |
| Stability Fix | ✅ | 资源泄漏、COM cleanup、retry defect |
| Security Fix | ✅ | path traversal、symlink、外部内容泄漏、fail-open |
| Compatibility Fix | ✅ | Windows / Word / Python patch compatibility |
| Dependency Maintenance | ✅ | Playwright / pywin32 / setuptools / build tooling |
| Test Defect Fix | ✅ | 错误 assertion、fixture、mock、测试边界缺失 |
| Documentation Correction | ✅ | 安装说明、限制、CLI 文档与实际行为不一致 |
| Performance Regression Fix | ✅ | 已证明 regression 且不改变 Canonical 语义 |
| Operational / Diagnostic Fix | ✅ | 明确错误信息、日志、诊断能力 |
| Minimal Refactor Required by Fix | ⚠️ | 仅限缺陷修复不可避免的最小结构调整 |

## 4.2 Forbidden Maintenance Scope

P11 默认禁止：

- 新 Markdown feature
- 新 CLI product feature
- 新 renderer
- 新 output format
- AST schema evolution
- DecisionEngine semantic change
- LayoutPlan schema evolution
- Theme V2 / Canonical theme semantic change
- Acceptance Corpus semantic redefinition
- Golden baseline 仅为迁就新实现而修改
- 大范围“代码清理”
- 无缺陷依据的 architecture refactor
- Optional Improvement 自动进入 implementation
- 通过修改测试掩盖产品缺陷

以上事项原则上转入：

```text
P12 — Evolution
```

---

# 5. Issue Classification

所有 P11 Issue 必须首先分类。

| Classification | 定义 | P11 处理 |
| --- | --- | --- |
| **DEFECT** | 实现违反 Canonical / Approved Behavior | Change Plan → Patch → Evidence |
| **TEST_DEFECT** | 测试错误，产品行为本身无缺陷 | Test Change Review → Test Patch |
| **SPEC_GAP** | Canonical 对真实场景定义不足或矛盾 | 停止产品修改；Human clarification / P12 |
| **ARCH_CHANGE** | 修复需要改变已冻结架构边界 | ADR → Human Approval → 通常进入 P12 |
| **OPTIONAL_IMPROVEMENT** | 非必要改进、可读性、便利性、未来优化 | Backlog；默认不实施 |

## 5.1 Classification Guard

禁止：

```text
OPTIONAL_IMPROVEMENT
    ↓
重新命名为 DEFECT
    ↓
绕过 P12 / Human Gate
```

Reviewer 必须要求：

- 可复现问题；
- Expected Behavior 权威来源；
- Actual Behavior；
- 明确 deviation；
- 可验证 acceptance criteria。

没有这些证据，不得按 DEFECT 执行。

---

# 6. Severity and Priority

| Severity | 定义 | 处理要求 |
| --- | --- | --- |
| **P1 — Critical / Release Blocker** | 数据损坏、严重错误输出、安全问题、核心流程不可用 | 立即建立 Change Package；不得发布存在该 blocker 的 patch |
| **P2 — Major** | 主要功能错误、明显稳定性问题、常见环境失败 | 高优先级处理 |
| **P3 — Normal** | 边缘缺陷、低频兼容问题、非核心错误 | 正常 Maintenance backlog |
| **P4 — Minor** | cosmetic、轻微文档、低影响诊断问题 | 可延后 |
| **Enhancement** | 非缺陷新能力或改进 | 转 P12 / Evolution backlog |

Severity 不得由实现难度决定，而应由用户影响、错误严重性、数据风险、安全风险和发生概率决定。

---

# 7. Maintenance Workflow

标准流程：

```text
Issue Intake
    ↓
Classification
    ↓
Severity
    ↓
Reproduction Evidence
    ↓
Expected vs Actual
    ↓
Root Cause Analysis
    ↓
Change Package
    ↓
Reviewer Approval
    ↓
Bounded Patch
    ↓
Targeted Test
    ↓
Regression Gate
    ↓
Conditional Golden / DOCX / COM / Packaging Gate
    ↓
Git Closure
    ↓
CLOSED / ACCEPTED
```

任何步骤失败，不得跳过后续 Gate 直接 CLOSED。

---

# 8. Maintenance Change Package

每个实际修改必须拥有独立 Change Package。

推荐 ID：

```text
P11-MNT-001
P11-MNT-002
P11-MNT-003
...
```

## 8.1 Mandatory Schema

```text
Change Package:
P11-MNT-XXX

Title:
<short descriptive title>

Source:
<Canonical / ADR / defect evidence / compatibility requirement>

Classification:
DEFECT / TEST_DEFECT / SPEC_GAP / ARCH_CHANGE / OPTIONAL_IMPROVEMENT

Severity:
P1 / P2 / P3 / P4 / Enhancement

Affected Version:
v1.0.0 / v1.0.x

Affected Component:
<component>

Problem:
<verified problem>

Reproduction:
<minimal deterministic reproduction>

Expected:
<expected behavior>

Actual:
<actual behavior>

Evidence:
<logs / output / DOCX / stack trace / failing test>

Root Cause:
<verified root cause; UNKNOWN until verified>

Allowed Scope:
<exact files/modules allowed to change>

Forbidden Scope:
<files/modules explicitly prohibited>

Required Tests:
<targeted tests>

Conditional Gates:
Golden / Acceptance / Real DOCX / COM / Packaging / Fresh Install

Acceptance Criteria:
<measurable pass criteria>

Rollback:
<how to revert if needed>

Git Closure:
exact diff
authorized files only
git diff --check PASS
working tree CLEAN
closure commit SHA

Status:
OPEN / APPROVED / IMPLEMENTED / VERIFIED / CLOSED / REJECTED
```

## 8.2 Scope Rule

Allowed Scope 必须尽量小。

AI Agent 不得因为：

- “顺便重构”
- “代码更优雅”
- “统一风格”
- “消除技术债”
- “未来更易扩展”

而扩大范围。

---

# 9. Root Cause Gate

Patch 前必须区分：

```text
Symptom
≠
Root Cause
```

如果 Root Cause 未验证：

```text
Status:
ROOT CAUSE UNVERIFIED
```

此时允许：

- 增加诊断；
- 增加 reproduction test；
- 增加 evidence；

但不得实施未经证据支持的大范围修复。

---

# 10. Test Matrix

测试按风险触发，不要求每次 Maintenance 都机械运行全部 release tests。

| Change Type | Unit | Targeted | Full Pytest | Golden | Acceptance | Real DOCX | COM | Fresh Install |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Docs only | — | — | — | — | — | — | — | — |
| TEST_DEFECT | ✅ | ✅ | ✅ | 条件 | 条件 | 条件 | 条件 | — |
| Parser / Normalize | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — |
| Diagram | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | 条件 |
| Decision / Layout | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 条件 | — |
| Renderer / Writer | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ 条件 | — |
| PostProcessor / Final QA | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ 条件 | — |
| COM lifecycle | ✅ | ✅ | ✅ | 条件 | 条件 | ✅ | ✅ | — |
| CLI | ✅ | ✅ | ✅ | — | 条件 | 条件 | — | ✅ 条件 |
| Packaging metadata | ✅ | ✅ | ✅ | — | — | — | — | ✅ |
| Dependency update | ✅ | ✅ | ✅ | ✅ 条件 | ✅ 条件 | ✅ | ✅ 条件 | ✅ |
| Security boundary | ✅ | ✅ | ✅ | 按影响 | 按影响 | 按影响 | 按影响 | 条件 |
| Performance regression | ✅ | ✅ | ✅ | 条件 | 条件 | ✅ 条件 | 条件 | — |

## 10.1 Regression Rule

对 product code 的 P11 修复，默认要求：

```text
Targeted Test:
PASS

Full Regression:
PASS

New Failure:
0

Required Skip:
0
```

如果 full regression 不适用，Change Package 必须明确说明原因并由 Reviewer 批准。

## 10.2 Golden / Acceptance Protection

禁止：

```text
Implementation fails Golden
    ↓
Modify Golden expected output
    ↓
Test becomes green
```

Golden / Acceptance baseline 只有在：

1. Canonical Authority 明确允许行为变化；
2. 对应 Spec / ADR 已批准；
3. 不属于简单 P11 defect patch；

时才允许修改。

通常应进入 P12。

---

# 11. Runtime / Word COM Gate

如果变更涉及：

- `WordRenderer`
- `WordWriter`
- PostProcessor
- COM lifecycle
- TOC / Paragraph / Style proxy
- retry / Word process cleanup

则至少要求：

```text
Dedicated COM Tests:
PASS

Representative DOCX:
PASS

FinalArtifactQA:
PASS

Fatal COM Error:
0
```

不得因 COM 环境偶发性而把 required test 改为 silent skip。

---

# 12. Security Maintenance

P11 Security Review 至少覆盖：

- path traversal
- symlink / reparse boundary
- 外部文件读取
- 临时目录
- shell / subprocess boundary
- Mermaid / external renderer
- untrusted Markdown input
- fail-open quality path
- dependency vulnerability
- package integrity
- unsafe cleanup / delete behavior

Security DEFECT 默认至少 P2；存在数据泄漏、任意文件访问、代码执行或严重 integrity 风险时按 P1 处理。

---

# 13. Dependency and Compatibility Maintenance

## 13.1 Permitted

可维护：

- Python patch-level compatibility
- Playwright / Chromium compatibility
- pywin32 / Word compatibility
- setuptools / build compatibility
- packaging metadata correctness
- dependency security patches

## 13.2 Upgrade Rule

Dependency upgrade 必须说明：

```text
Why Upgrade
Affected Behavior
Compatibility Risk
Rollback Version
Required Tests
```

不得为了“追最新版本”自动升级。

如果升级导致：

- Canonical output change
- Architecture change
- Acceptance drift
- major renderer behavior change

则停止 P11 patch，转 P12 evaluation。

---

# 14. Documentation Maintenance

允许修正文档与实际行为的不一致。

文档修复必须判断：

```text
Documentation is wrong
or
Implementation is wrong
```

不得默认以修改文档来掩盖实现缺陷。

文档-only Change Package 可不运行 full regression，但仍要求：

- exact diff
- factual consistency review
- authorized scope
- `git diff --check`
- clean Git closure

---

# 15. AI Agent Governance

P11 继续采用：

```text
              Specification
                   ▲
                   │
            ChatGPT Reviewer
              ▲          ▲
              │          │
         AI Agent ─── Test System
```

## 15.1 Reviewer

Reviewer 可：

- Classification
- Severity Review
- Root Cause Review
- Change Plan
- Allowed / Forbidden Scope
- Test Matrix Selection
- Evidence Review
- Closure Review

Reviewer 不得替代 Human Gate。

## 15.2 AI Agent

AI Agent 只能：

- 执行已批准 Change Package；
- 修改 Allowed Scope 内文件；
- 运行批准的测试；
- 输出 evidence。

AI Agent 禁止：

- 修改 Canonical Authority；
- 扩大 Allowed Scope；
- 自动改变 Golden；
- 自动改变 Acceptance Criteria；
- 把 Optional Improvement 改成 DEFECT；
- 自动批准 Patch Release；
- 自动完成 Human Closure。

---

# 16. Git Closure Gate

每个已实施的 Maintenance Change Package 必须 Git 收口。

最低要求：

```powershell
git status --short
git diff -- <allowed-files>
git add <allowed-files>
git diff --cached --name-status
git diff --cached --check
git diff --cached
git commit -m "<bounded maintenance commit>"
git rev-parse HEAD
git status --short
```

验收：

```text
Changed Files:
exactly authorized

Forbidden Files:
0

git diff --cached --check:
PASS

Working Tree:
CLEAN

Closure SHA:
RECORDED
```

禁止：

- unrelated files 混入；
- `git add .` 在 scope 未审查时直接使用；
- amend 已冻结 release commits；
- 重写 `v1.0.0` tag；
- 为维护提交执行无必要的 rebase / history rewrite。

---

# 17. Patch Release Policy

## 17.1 Version Policy

默认：

| Change | Version Policy |
| --- | --- |
| Bug / Security / Compatibility fix | `1.0.1`, `1.0.2`, ... |
| Backward-compatible feature | P12 → candidate `1.1.0` |
| Canonical semantic change | P12 |
| Breaking change | P12 → candidate `2.0.0` |

P11 默认只生产 **Patch Release**。

## 17.2 Patch Release Trigger

以下任一情况可考虑 patch release：

- 已关闭 P1 / P2 production defect；
- security fix；
- major compatibility fix；
- 多个已验证 P3 修复累积到发布阈值；
- Human 明确要求 patch release。

不是每个 Maintenance Commit 都必须发布。

---

# 18. Patch Release Gate

Patch Release 必须通过：

| Gate | Acceptance |
| --- | --- |
| Maintenance Packages | Release 范围内全部 CLOSED / ACCEPTED |
| Open P1 Blockers | **0** |
| Release-Critical P2 | **0** |
| Targeted Tests | PASS |
| Full Regression | PASS |
| Required Skip | 0 |
| Golden | PASS if affected |
| Acceptance | PASS if affected |
| Representative DOCX | PASS if affected |
| FinalArtifactQA | PASS |
| COM Gate | PASS if affected |
| Packaging | PASS |
| wheel + sdist | Build PASS |
| Artifact Integrity | SHA256 recorded |
| Fresh Install | PASS |
| CLI Smoke | PASS |
| Version Consistency | PASS |
| Release Notes | COMPLETE |
| Patch Manifest | COMPLETE |
| Known Limitations | UPDATED if needed |
| Git Tree | CLEAN |
| Human Production Approval | REQUIRED |

Default decision:

```text
Any Required Gate FAIL
    ↓
PATCH RELEASE DENIED
```

禁止 fail-open。

---

# 19. Patch Release Evidence

Patch release 建议产生独立证据，例如：

```text
RC_EVIDENCE/P11_v1.0.1/
```

或项目既有 Release Evidence Authority 规定的等效结构。

至少记录：

- source commit SHA
- maintenance package IDs
- Python / dependency environment
- regression result
- Golden / Acceptance result（如适用）
- representative DOCX evidence（如适用）
- package filenames
- SHA256
- fresh install result
- CLI smoke result
- release decision
- Human approval

---

# 20. P11 Work Packages

| S/N | Phase# | Task | Work Package | Deliverable / Acceptance | Status |
| ---: | --- | --- | --- | --- | --- |
| 1 | P11-01 | Maintenance Scope Freeze | WP-MNT-01 Scope | Allowed / Forbidden Scope；NO FEATURE DEVELOPMENT；P12 boundary | ⏳ PLANNED |
| 2 | P11-02 | Maintenance Baseline | WP-MNT-02 Baseline | `v1.0.0` tag target；P10 closure SHA；test/environment baseline | ⏳ PLANNED |
| 3 | P11-03 | Issue Classification | WP-MNT-03 Triage | 5-class classification frozen | ⏳ PLANNED |
| 4 | P11-04 | Severity Gate | WP-MNT-04 Priority | P1/P2/P3/P4/Enhancement rules | ⏳ PLANNED |
| 5 | P11-05 | Reproduction Evidence | WP-MNT-05 Repro | deterministic reproduction；Expected vs Actual | ⏳ PLANNED |
| 6 | P11-06 | Change Package Authority | WP-MNT-06 Change Control | Mandatory Change Package schema | ⏳ PLANNED |
| 7 | P11-07 | Bounded Patch | WP-MNT-07 Patch | minimal authorized modification | ⏳ CONTINUOUS |
| 8 | P11-08 | Target Verification | WP-MNT-08 Target Test | failing reproduction → PASS | ⏳ CONTINUOUS |
| 9 | P11-09 | Regression Gate | WP-MNT-09 Regression | full regression PASS；new failure=0 | ⏳ CONTINUOUS |
| 10 | P11-10 | Golden / Acceptance Gate | WP-MNT-10 Golden | affected behavior remains canonical | ⏳ CONDITIONAL |
| 11 | P11-11 | Runtime / COM Gate | WP-MNT-11 Runtime | COM / DOCX / FinalArtifactQA | ⏳ CONDITIONAL |
| 12 | P11-12 | Dependency Maintenance | WP-MNT-12 Dependency | compatibility + rollback + test evidence | ⏳ CONTINUOUS |
| 13 | P11-13 | Security Maintenance | WP-MNT-13 Security | boundary / dependency / fail-open review | ⏳ CONTINUOUS |
| 14 | P11-14 | Documentation Maintenance | WP-MNT-14 Docs | docs == actual approved behavior | ⏳ CONTINUOUS |
| 15 | P11-15 | Git Closure | WP-MNT-15 Git Gate | exact diff；forbidden=0；clean tree；SHA | ⏳ CONTINUOUS |
| 16 | P11-16 | Patch Release Decision | WP-MNT-16 Release Gate | release threshold + blockers + Human decision | ⏳ CONDITIONAL |
| 17 | P11-17 | Patch Build / Verify | WP-MNT-17 Patch Release | wheel/sdist/hash/install/smoke/evidence | ⏳ CONDITIONAL |
| 18 | P11-18 | Governance Review | WP-MNT-18 Governance | no unauthorized drift；all packages classified | ⏳ PLANNED |
| 19 | P11-19 | Final Human Closure | WP-MNT-19 Closure | Human approval；P11 CLOSED / transition decision | ⏳ PLANNED |

---

# 21. Continuous Maintenance Model

P11 与 Development Phase 不同。

P11-07..15 为长期循环：

```text
P11 Foundation
    ↓
P11-MNT-001
    ↓
Closure
    ↓
P11-MNT-002
    ↓
Closure
    ↓
...
    ↓
Patch Release when justified
```

因此：

- 单个 Maintenance Package 可以 CLOSED；
- P11 Program 可以保持 ACTIVE；
- 不要求每个 defect 后立即关闭整个 P11；
- P11 Final Closure 仅在 Human 决定结束该 maintenance line 或进入下一治理阶段时执行。

---

# 22. P11 Definition of Done

P11 Foundation DoD：

```text
[ ] P11 Maintenance Authority Human-Frozen
[ ] Maintenance Scope frozen
[ ] v1.0.0 release baseline recorded
[ ] P10 governance baseline recorded
[ ] Classification rules frozen
[ ] Severity rules frozen
[ ] Change Package template frozen
[ ] Test Matrix frozen
[ ] Git Closure Gate frozen
[ ] Patch Release Gate frozen
[ ] P12 Evolution boundary frozen
```

P11 Program Final Closure DoD：

```text
[ ] All accepted P11 P1 issues CLOSED
[ ] Release-critical P2 issues = 0
[ ] All implemented Maintenance Packages individually Git-closed
[ ] Unauthorized files = 0
[ ] Unauthorized Frozen Core drift = 0
[ ] Canonical semantic drift = 0
[ ] Silent Golden drift = 0
[ ] Silent Acceptance drift = 0
[ ] Patch releases, if any, fully verified
[ ] Patch release tags, if any, Human-approved
[ ] Open backlog fully classified
[ ] P12 candidates separated from P11
[ ] Governance-only Closure Review PASS
[ ] Final Human Closure APPROVED
```

---

# 23. Initial P11 State

在本文档 Freeze 之前：

```text
P11 Status:
DRAFT / NOT YET FROZEN

Product Code Change:
NONE AUTHORIZED

Canonical Change:
NONE AUTHORIZED

Frozen Core Change:
NONE AUTHORIZED

Patch Release:
NONE AUTHORIZED
```

本文档 Human Freeze 后：

```text
P11 Status:
ACTIVE

Initial Work Package:
P11-MNT-GOV-01
Maintenance Governance Foundation

Immediate Scope:
Governance / Baseline / Triage only

Product Code Change:
NONE until an approved Change Package exists
```

---

# 24. Maintenance Governance Principles

P11 最终固定以下原则：

1. **Canonical Authority**
   Maintenance 不得越过 Canonical。

2. **Minimal Change**
   只修复已验证问题，不进行顺带重构。

3. **Evidence Before Patch**
   没有 reproduction / deviation evidence，不实施产品修复。

4. **Classification Before Implementation**
   先判断 DEFECT / TEST_DEFECT / SPEC_GAP / ARCH_CHANGE / OPTIONAL_IMPROVEMENT。

5. **Default Deny Scope**
   未列入 Allowed Scope 的文件默认禁止修改。

6. **No Silent Baseline Drift**
   Golden、Acceptance、Canonical、Release Evidence 不得为迁就实现而静默变化。

7. **Risk-Based Testing**
   测试 Gate 由受影响边界决定，但 required gate 不得静默 skip。

8. **Git Closure Is Mandatory**
   每个已实施 Maintenance Package 必须形成 exact、clean、可追溯 closure。

9. **Patch Release Is Conditional**
   Maintenance commit 不等于必须 release。

10. **Human Release Authority**
    Patch Production Approval、Tag、P11 Final Closure 保留 Human Gate。

11. **Evolution Separation**
    Feature / Semantic / Architecture evolution 属于 P12，不得借 P11 越权实现。

---

# 25. Freeze Gate

本文档成为正式 **P11 Maintenance Authority** 前，应由 Human 明确批准：

```text
APPROVE AND FREEZE
Phase_11_Maintenance_Specification.md
VERSION: 1.0
AS P11 MAINTENANCE AUTHORITY
```

批准后记录：

```text
Spec Version:
1.0

Status:
FROZEN / ACTIVE

Authority:
P11 Maintenance Authority

Human Freeze:
APPROVED

Freeze Date:
<date>

Freeze Commit:
<git SHA>
```

之后对本文档本身的实质性规则修改必须走：

```text
SPEC_GAP / GOVERNANCE CHANGE
    ↓
Review
    ↓
Human Approval
    ↓
Version Update
    ↓
Re-Freeze
```
