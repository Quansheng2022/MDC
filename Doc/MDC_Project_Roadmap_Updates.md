下面按**截至当前实际状态**整理项目 Roadmap。需要说明一点：早期 `MPC_Roadmap.md` 中仍把 P10 标为 “CURRENT TARGET”，这是历史快照；后续 P10 evidence 已证明 P10 已完成，因此下表按**最新证据状态**归一化，不沿用该陈旧标记。早期阶段顺序与状态见项目 Roadmap。

## MD_Converter Project Roadmap

| S/N | Phase#                          | 任务                                                                 | Work Package / Plan                   | 交付 / 验收清单                                                                                            | 完成状态                          | 当前说明 / 下一步                           |
| --: | ------------------------------- | ------------------------------------------------------------------ | ------------------------------------- | ---------------------------------------------------------------------------------------------------- | ----------------------------- | ------------------------------------ |
|   1 | **P0**                          | Product Definition                                                 | Product Definition Baseline           | 产品目标、范围、核心能力、约束边界明确                                                                                  | ✅ **COMPLETE**                | 已完成，后续不重新打开                          |
|   2 | **P1**                          | Canonical Specification                                            | `CANONICAL_SPEC.md` v1.0              | Canonical Authority；SPEC-ID；功能、架构、QA、Acceptance 不变量                                                  | ✅ **FROZEN**                  | Canonical 1.0 已冻结，普通维护不得修改           |
|   3 | **P2**                          | Architecture Design                                                | `Doc/ARCHITECTURE.md` + ADR-001..009  | Compiler architecture；职责边界；ADR；dependency direction                                                  | ✅ **FROZEN**                  | 架构已冻结；Architecture Evolution → P12   |
|   4 | **P3**                          | Implementation Specification                                       | Implementation Specification / Plan   | Spec → Implementation mapping；模块职责；实施约束                                                              | ✅ **COMPLETE**                | 实现规范已完成                              |
|   5 | **P4**                          | Foundation Development                                             | Foundation Development WP             | Parser / AST / Pipeline / Config 等基础能力实现与测试                                                          | ✅ **COMPLETE**                | Foundation 已完成                       |
|   6 | **P5**                          | Rendering Development                                              | Rendering Development WP              | Renderer、WordWriter、PostProcessor、Theme、DOCX 渲染能力                                                    | ✅ **COMPLETE**                | Rendering 已完成                        |
|   7 | **P6**                          | Quality Engineering                                                | QA / Golden / Acceptance WP           | StaticQA、RenderedQA、FinalArtifactQA、Golden、Acceptance                                                | ✅ **COMPLETE**                | QA 强制门已建立                            |
|   8 | **P7**                          | Governance Engineering                                             | Governance Closure                    | Canonical governance、Release Evidence、Default-Deny、审计链                                               | ✅ **CLOSED / ACCEPTED**       | 冻结，不再反复优化                            |
|   9 | **P8**                          | Verification & Acceptance                                          | Verification / Acceptance             | Full regression、Golden、Acceptance、representative DOCX                                                | ✅ **PASS / CLOSED**           | 验证验收通过                               |
|  10 | **P9**                          | Release Candidate Closure                                          | RC Closure                            | RC evidence、regression、artifact consistency、Governance closure                                       | ✅ **CLOSED / ACCEPTED**       | RC 已正式收口                             |
|  11 | **P10**                         | v1.0.0 Production Release                                          | `WP-REL-*` / P10 Release Plan         | wheel/sdist、SHA256、fresh install、CLI smoke、DOCX、277/277、release docs、tag、archive                     | ✅ **CLOSED / ACCEPTED**       | `v1.0.0` 已正式发布                       |
|  12 | **P10-18**                      | Final Release Regression                                           | WP-REL-18                             | Full regression；Failed=0；Required Skip=0；Fatal COM=0                                                 | ✅ **277/277 PASS**            | Release regression 已通过               |
|  13 | **P10-19**                      | Production Tag                                                     | WP-REL-19                             | annotated `v1.0.0`；target SHA 固定                                                                     | ✅ **CLOSED / ACCEPTED**       | tag → `5d2c92a...`，不可移动              |
|  14 | **P10-20..23**                  | Distribution / Production Approval / Archive / Post-release Verify | WP-REL-20..23                         | 分发、Human Approval、归档、正式包重装、CLI/DOCX 验证                                                               | ✅ **PASS / CLOSED**           | 全部完成                                 |
|  15 | **P10-24**                      | Final Phase Closure                                                | WP-REL-24                             | blockers=0；Governance review；Final Human Closure                                                     | ✅ **CLOSED / ACCEPTED**       | P10 完全关闭                             |
|  16 | **P10-GIT-FINAL**               | Final Git Closure                                                  | Governance Closure                    | exact diff；clean tree；tag 不移动；closure SHA                                                            | ✅ **CLOSED / ACCEPTED**       | P10 closure SHA `dab9142...`         |
|  17 | **P11**                         | Maintenance Program                                                | P11 Maintenance Authority             | v1.0.x maintenance；defect/stability/security/compatibility；P12 boundary                              | 🟢 **FROZEN / ACTIVE**        | 当前阶段；P11 Program 不因单包关闭而关闭           |
|  18 | **P11 / PLAN_A**                | Maintenance Governance Foundation                                  | `P11_AGENT_PLAN_A` / `P11-MNT-GOV-01` | Scope、Baseline、Classification、Severity、Change Package、Test Matrix、Git Gate、Release Gate、P12 Boundary | ✅ **CLOSED / ACCEPTED**       | PLAN_A 已完成；Authority FROZEN / ACTIVE |
|  19 | **P11 / PLAN_B**                | Maintenance Change Package Lifecycle                               | `P11_AGENT_PLAN_B`                    | Issue → Repro → RCA → Change Package → Patch → Verify → Regression → Git Closure                     | 🟡 **ACTIVE / FINAL CLOSURE** | 当前处理首个真实 maintenance package         |
|  20 | **P11-MNT-001**                 | Word COM collection-time probe defect                              | `P11-MNT-001` / TEST_DEFECT P2        | COM probe 移出 collection；subprocess isolation；fail-closed；真实 COM 路径保留                                 | ✅ **TECHNICAL PASS**          | 技术修改已验收                              |
|  21 | **P11-MNT-001 / B-10**          | Target Verification                                                | WP-MNT-08 / COM Gate                  | Dedicated COM 连续 3 次；Fatal=0；Unexpected Skip=0                                                       | ✅ **3/3 PASS**                | 已完成                                  |
|  22 | **P11-MNT-001 / B-11**          | Full Regression                                                    | WP-MNT-09                             | 277/277；Failed=0；Required Skip=0；Fatal COM=0                                                         | ✅ **PASS**                    | 已完成                                  |
|  23 | **P11-MNT-001 / B-12**          | Maintenance Review Gate                                            | Maintenance merger 1.2.0              | `--mode maintenance --run-pytest --strict`；目标测试、Registry、证据全部进入 snapshot                             | ✅ **PASS on closure state**   | 已有 `277/277 + RESULT: PASS` 证据       |
|  24 | **P11-MNT-001 / Final**         | Governance-State Reconciliation                                    | PLAN_B Final Reconciliation           | Registry / Change Package / Closure 状态一致；Reviewer Acceptance                                         | 🟡 **IN PROGRESS**            | **当前正在做**                            |
|  25 | **P11-MNT-001 / Final Gate**    | Final HEAD Strict Validation                                       | PLAN_B Final Gate                     | CLEAN tree；最新 HEAD；277/277；fatal=0；strict `RESULT: PASS`                                             | ⏳ **NEXT**                    | reconciliation commit 后执行            |
|  26 | **P11-MNT-001 / Reviewer Gate** | Final Reviewer / Human Acceptance                                  | PLAN_B Final Acceptance               | Reviewer approve；Human Gate；记录 CLOSED / ACCEPTED                                                     | ⏳ **NEXT**                    | AI Agent 不得自批准                       |
|  27 | **P11-MNT-002**                 | Merger generated-snapshot nesting defect                           | Future Maintenance Package            | `Merged_Code` 不应嵌套旧 review snapshot；独立 Repro/RCA/Change Package                                      | ⚪ **CANDIDATE / NOT STARTED** | 已发现，但**不得混入 P11-MNT-001**            |
|  28 | **P11 / PLAN_C**                | Conditional Patch Release                                          | `P11_AGENT_PLAN_C`                    | package threshold、build、wheel/sdist、SHA、fresh install、CLI、release evidence、Human approval            | ⏳ **CONDITIONAL**             | 只有决定发布 v1.0.x patch 时启动              |
|  29 | **P11 / PLAN_D**                | Governance Audit / Final P11 Closure                               | `P11_AGENT_PLAN_D`                    | 全包审计；open blocker=0；authority consistency；Final Human Closure                                        | ⏳ **FUTURE**                  | 只有结束 maintenance line 时执行            |
|  30 | **P12**                         | Product Evolution                                                  | P12 Evolution Program                 | 新 feature、新 Markdown 语义、新 renderer/output、AST/LayoutPlan/Architecture evolution                      | ⏳ **PLANNED**                 | 与 P11 Maintenance 严格隔离               |

P10 的正式发布链已经覆盖 build、fresh install、CLI/DOCX、277/277 final regression、annotated tag、distribution/archive 和 Final Closure。 P11 Authority 当前明确为 **FROZEN / ACTIVE**，默认维护 `v1.0.x`，任何 feature、semantic 或 architecture evolution 都转 P12。

### 当前项目位置

```text id="fqw7rm"
P0   Product Definition             ✅
 ↓
P1   Canonical Specification        ✅ FROZEN
 ↓
P2   Architecture Design            ✅ FROZEN
 ↓
P3   Implementation Specification   ✅
 ↓
P4   Foundation Development         ✅
 ↓
P5   Rendering Development          ✅
 ↓
P6   Quality Engineering            ✅
 ↓
P7   Governance Engineering         ✅ CLOSED / ACCEPTED
 ↓
P8   Verification & Acceptance      ✅ PASS
 ↓
P9   RC Closure                     ✅ CLOSED / ACCEPTED
 ↓
P10  v1.0.0 Production Release      ✅ CLOSED / ACCEPTED
 ↓
P11  Maintenance                    🟢 ACTIVE
      │
      ├─ PLAN_A                     ✅ CLOSED / ACCEPTED
      │
      ├─ P11-MNT-001 / PLAN_B       🟡 FINAL CLOSURE
      │    ├─ Technical Fix         ✅
      │    ├─ COM 3/3               ✅
      │    ├─ Regression 277/277    ✅
      │    ├─ Maintenance Strict    ✅
      │    └─ Governance Reconcile  ◀ CURRENT
      │
      ├─ P11-MNT-002                ⚪ Candidate
      │
      ├─ PLAN_C Patch Release       ⏳ Conditional
      │
      └─ PLAN_D Final Audit         ⏳ Future
 ↓
P12  Product Evolution              ⏳ PLANNED
```

这里最重要的是：**P11 不是传统 development phase。** 它采用连续维护模式，单个 `P11-MNT-xxx` 可以关闭，而 P11 Program 继续 `ACTIVE`；只有 Human 决定结束 maintenance line 时才执行 P11 Final Closure。

### 当前下一步

目前唯一应该推进的是：

```text id="woqi57"
P11-MNT-001
Governance-State Reconciliation
        ↓
Reconciliation Commit
        ↓
Final HEAD maintenance strict + 277/277
        ↓
ChatGPT Reviewer / Human Acceptance
        ↓
Final Acceptance Record Commit
        ↓
Final immutable strict PASS
        ↓
P11-MNT-001 CLOSED / ACCEPTED
        ↓
P11 Program remains ACTIVE
```

**不需要再回到 P0–P10，也不应该在此时进入 PLAN_C。** Patch Release 并非每个 maintenance commit 都必须触发；正式 Patch Release 还要求全部 release-scope maintenance packages CLOSED、regression/COM/packaging/fresh install/CLI 等 Gate 通过并取得 Human Production Approval。
