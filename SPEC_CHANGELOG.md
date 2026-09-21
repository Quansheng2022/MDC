# Specification Changelog

记录 Canonical Specification 的创建、冻结与变更历史。

## 1.1（FROZEN，2026-09-21）

- **动作**：把 Human 已批准的 P12 canonical delta 并入 `CANONICAL_SPEC.md`，
  并将 Canonical Specification re-freeze 为 1.1。
- **来源**：Human-approved P12 specification（S/N 118 批准 + P12 implementation
  acceptance 2026-09-21）；提案文本 `P12/P12_CANONICAL_SPEC_PROPOSAL.md`；
  需求 `P12/P12_REQUIREMENTS.md`；实现计划 `P12/P12_IMPLEMENTATION_PLAN.md`。
- **Added（Canonical / Frozen）**：
  - `SPEC-FUNC-022` Simple Table Recognition（空白对齐两列简单表格；CLAR-01：
    不满足条件时保留段落且不产生诊断）
  - `SPEC-FUNC-023` Figure Page-Fit / 图形尺寸策略（有效 section 内容区；CLAR-02：
    几何取自实际 section，A4/1in 仅为参考；保持宽高比、永不放大、永不超出内容区；
    低于主题 `figure.min_width` 时交付适配尺寸并 WARNING；物理分页归 Word）
  - `SPEC-FUNC-024` 空标题行为（WARN + DROP：不渲染、不注入 `"Heading"`、
    不产生合成 TOC 条目；AST 保留节点；既有 StaticQA WARNING 保持）
  - `SPEC-INV-013` 歧义输入保持段落，识别不得丢失/重排/改写源文本
  - `SPEC-INV-014` 交付图形不得超出有效内容区，违者不得通过质量门
  - `SPEC-QA-005` RenderedQA 真实测量图形几何（超出 = error → Gate FAIL；
    低于最小宽度 = warning 并计数）
- **Amended（最小冲突文本）**：`SPEC-FUNC-020` 与 §4.1 flow、§6 的 Acceptance
  Corpus 基线从 AC001–AC015 更新为 AC001–AC018（P12 新增 AC016/AC017/AC018）。
- **Unchanged**：`SPEC-GOAL-001..006`、`SPEC-ARCH-001..013`、
  `SPEC-FUNC-001..021`、`SPEC-INV-001..012`、`SPEC-QA-001..004`、
  `SPEC-AC-001..005`、`SPEC-NON-001..004`、冻结主题值、架构与依赖方向。
- **冻结基线**：
  - `spec_version`: 1.1
  - `spec_status`: FROZEN
  - `freeze_date`: 2026-09-21
  - `architecture_version`: 2.0（未修改）
  - `theme_version`: QS-Word-Default-V1.5 (1.5)（未修改）
  - `software_version`: 1.1.0
  - `acceptance_baseline`: AC001–AC018
  - `governance_baseline`: P0-01..P0-08, P1-09, P1-10, P12（S/N 117–118）
- **Superseded**：Spec 1.0（FROZEN 2026-08-30）标记为 SUPERSEDED，记录保留于本文件。
- **ADR**：本 delta 不需要 ADR（CAND-001/002/003 均为有界实现面，无新 pipeline
  阶段、无所有权迁移、无 `LayoutPlan` 契约扩展；见 `P12/P12_REQUIREMENTS.md` §0）。

## 1.0（FROZEN，2026-08-30）

- **动作**：创建 `CANONICAL_SPEC.md`，确立项目唯一 Canonical Authority。
- **来源**：`Doc/ARCHITECTURE.md`、`Doc/MD_Converter_Design_MVP3.0.md`、
  冻结主题 `QS-Word-Default-V1.5`、ADR-001..009、既有测试体系。
- **内容**：
  - System Goals（SPEC-GOAL-001..006）
  - Functional Scope（SPEC-FUNC-001..021）
  - Architecture Contract（SPEC-ARCH-001..013）
  - Quality Gate Contract（SPEC-QA-001..004）
  - Invariants（SPEC-INV-001..012）
  - Acceptance Criteria（SPEC-AC-001..005）
  - Non-Goals（SPEC-NON-001..004）
- **冻结基线**：
  - `spec_version`: 1.0
  - `architecture_version`: 2.0
  - `theme_version`: QS-Word-Default-V1.5 (1.5)
  - `acceptance_baseline`: AC001–AC015
  - `governance_baseline`: P0-01..P0-08, P1-09, P1-10
- **配套交付物**：
  - `REVIEW_TEMPLATE.md`（Change Classification Gate）
  - `IMPLEMENTATION_PLAN.md`（Traceable Implementation Plan 模板）
  - `quality_gate.py`（StaticQA / RenderedQA / FinalArtifactQA Gate）
  - `md_converter/tests/acceptance/`（Canonical Acceptance Corpus）
  - `release_evidence.py` 与 `RELEASE_EVIDENCE.md` / `release_evidence.json`

### 基线刷新记录（2026-08-30，Approved Baseline Refresh）

- **对象**：`md_converter/tests/golden/sample.expected.json`
- **原因**：python-docx 版本行为差异导致 `paragraph.text` 对 `<w:br/>`
  换行语义变化（`\n` 并入文本），以及水平分割线在快照中的呈现差异；
  经 investigate 确认**非实现缺陷**，属于基线过期。
- **流程**：Test failure → investigate（实现缺陷？否）→ 基线刷新获批 →
  regenerate（`--update`，与 mermaid 正常渲染环境一致）。
- **影响**：仅 3 处段落文本快照更新；diagnostics 仍为 11 条，无新增。

### 治理收口记录（2026-08-30，Release Governance Closure）

对 Spec 1.0 既有契约的执行语义进行收口，**不改变 FROZEN 条款**，
属于把“结构正确”升级为“默认拒绝、证据驱动、不可误放行”：

- **Post-Processor Contract Gate**：Post-Processor 基础设施异常从
  `POST001 warning` 升级为 `ERROR / QualityGateError(stage="post_processor")`
  （FAIL CLOSED）；FinalArtifactQA 依据 `ArtifactContract` 判断
  required cover / TOC / table styling，缺失 = ERROR；显式关闭的功能缺失 = PASS。
- **Mandatory Test Evidence Contract**：`REQUIRED_TEST_SUITES`
  （unit / integration / golden / acceptance）缺一不可；
  缺失自动补 `NOT_RUN`；`SKIPPED` 不得等价于 `PASS`；
  `--test-report` 只接受 Canonical Status。
- **Measured Governance Evidence**：治理指标不再默认 0；
  `architecture_frozen` / `unauthorized_spec_changes` / `spec_deviations`
  默认为 `None`（NOT_CHECKED），`regression` 默认
  `{status: NOT_CHECKED, new_failures: None}`；Release Evidence 只读取
  证据、不制造证据；`compute_release_result()` 为 Default Deny，
  UNKNOWN 与 FAIL 同样 BLOCK。新增 `--governance-report` 输入。

对应 IMP：IMP-007 / IMP-008 / IMP-009（见 `IMPLEMENTATION_PLAN.md`）。
完成标准见该轮验收：PostProcessor 故障注入逃逸 = 0、
Required Suite 缺一即 BLOCK、治理未检测即 BLOCK。

### 最终收口记录（2026-08-31，F1–F5 Closure）

在既有治理基础上完成最后 5 项收口，**不改变 FROZEN 条款**：

- **F1（P0）**：修复 Governance 负数绕过 Release Gate。所有治理计数
  （unauthorized_spec_changes / spec_deviations / regression 三个 failures）
  必须为非负整数；`new_failures <= current_failures`；Release Predicate
  从 `> 0` 改为 `!= 0`（Defense-in-Depth，直接构造负数也无法绕过）。
- **F2（P1）**：PostProcessor 状态纳入 Release Evidence。Compiler 记录
  `post_processor_result`（PASS / NOT_REQUIRED / FAIL / NOT_RUN +
  required + features），`REQUIRED_QA_STAGES` 加入 post_processor，
  通过语义为 PASS 或 NOT_REQUIRED。
- **F3（P1）**：Governance Evidence 增加审计来源。`checked_at`（ISO-8601）、
  `checked_by`、`mechanism`（有限集合）为必填；regression 必须带
  baseline / current 标识比较对象；Markdown/JSON 均输出 provenance。
- **F4（P1）**：消除配置 Duplicate Authority。`DEFAULT_CONFIG` 为唯一默认值
  来源；`CompilerConfig` 字段与 `from_dict` 引用 `DEFAULT_CONFIG`；
  `ArtifactContract` 只消费 resolved configuration（缺失键报错）；
  新增一致性测试防回归。
- **F5（Release）**：固定 Golden 环境。`GOLDEN_ENVIRONMENT.md` 定义
  Canonical renderer（playwright，mmdc shim 不可执行）；Golden baseline
  记录 `renderer_backend`，后端不一致时显式失败；恢复 `input/converter2.md`
  fixture，测试 skip 清零（220 collected / 220 passed / 0 skipped）。

对应 IMP：IMP-010 / IMP-011 / IMP-012 / IMP-013 / IMP-014。

### 最终收口（C1–C3，2026-08-31 Closure）

不再扩展架构，仅完成 3 个小项，把状态推进到 CLOSED / ACCEPTED /
RELEASE_ELIGIBLE：

- **C1（P0/P1）**：Governance provenance Defense-in-Depth。提取统一
  `_is_valid_iso8601()`，`validate_governance_evidence()` 与
  `compute_release_result()` 共用；regression.checked_at 成为必填；
  最终 Release Predicate 重新验证 checked_at（ISO-8601）、checked_by
  （非空）、mechanism（Canonical enum）、regression checked_at / baseline /
  current——即使绕过 schema validator 直接构造 ReleaseEvidence 也无法放行。
- **C2（P1）**：Canonical Config Authority 彻底单一化。`ArtifactContract`
  删除字段默认值（`ArtifactContract()` 必须 TypeError）；Compiler 直接
  `self.config[key]` 消费 resolved config（缺键 KeyError = Fail Fast）；
  `DocxPostProcessor` 的 `.get(..., True)` 明确标注为低层 API
  backward-compatible fallback，非权威来源；新增无隐式默认值/匹配/override
  一致性测试。
- **C3（Release）**：Canonical Golden Runtime 固化。`pyproject.toml` 新增
  `[mermaid]` extra 并 pin `playwright>=1.62,<2`；GOLDEN_ENVIRONMENT.md
  补 Setup / Verification 步骤；`converter2.md` fixture 固化到
  `md_converter/tests/fixtures/`，测试不再依赖工作区 `input/`，
  skip 改为 fail（0 unexpected skipped）。

对应 IMP：IMP-015 / IMP-016 / IMP-017。

最终验证：235 collected / 235 passed / 0 failed / 0 skipped；
Golden `renderer_backend=playwright`；Release Evidence = RELEASE_ELIGIBLE。

**本阶段正式关闭 Governance Engineering 扩展**；后续工程重点转向
Markdown→DOCX 实际转换质量与真实文档兼容性。

### 最终修改包 R1–R3（2026-08-31 CP-FINAL Closure）

三个最终修改包，目标是把状态推进到 CLOSED / ACCEPTED / RELEASE_ELIGIBLE：

- **R1 / CP-FINAL-01（P1）**：Regression Evidence 谓词对称。提取统一
  `_is_non_negative_int()`，schema 与最终 Release Predicate 共用；
  `compute_release_result()` 重新校验 baseline/current/new failures
  全部为非负整数、`new_failures <= current_failures`、`new_failures == 0`。
  明确不引入 `current - baseline == new` 的数学约束（旧失败可被修复）。
- **R2 / CP-FINAL-02（P0 Release）**：Canonical Playwright + Chromium
  Runtime 固化。`pyproject.toml` 精确 pin `playwright==1.62.0`；
  新增 `md_converter/tests/golden_environment.py` preflight
  （真实 headless Chromium launch）+ `test_golden_environment.py`
  （环境不满足必须 FAIL，不允许 SKIP）；GOLDEN_ENVIRONMENT.md 记录
  Mermaid 10 CDN 网络依赖（本地化属于后续项，不动 DiagramPass）。
- **R3 / CP-FINAL-03（Release）**：RC Evidence Package。生成
  `RC_EVIDENCE/`：RELEASE_EVIDENCE.md、release_evidence.json、
  governance_evidence.json、test_report.json、golden_environment_report.json、
  full_pytest_summary.txt（来自真实测试运行）。

最终验证：**245 collected / 245 passed / 0 failed / 0 skipped**；
Golden `renderer_backend=playwright`；Release Evidence = RELEASE_ELIGIBLE。

**Governance Engineering：CLOSED / ACCEPTED。** 后续优化预算转向
Markdown 兼容性、复杂表格、图片/Mermaid 稳定性、真实长文档质量与用户体验。

### P7 最终收口（CP-GOV-FINAL-01，2026-08-31）

P7 Governance Engineering 从约 99% 推进到 100% 的唯一剩余修复：

- **Repair Evidence Predicate Fail-Closed**：`compute_release_result()` 对
  `repair.remaining_errors` 复用统一 `_is_non_negative_int()`（int、非 bool、
  >= 0），再要求严格 `== 0`。`-1 / None / True / False / "0" / 0.0 / 1`
  全部 BLOCK，仅 `0` 放行——与 Regression Evidence 完全对称。
- **REPAIR-DI-01..08 攻击矩阵**：全部绕过 validator 直接构造
  `ReleaseEvidence`，验证 schema bypass ≠ Release Gate bypass。
- 完整 Governance Attack Suite（单一入口 `test_release_evidence.py`）：
  schema / GOV / GOV-AUD / GOV-DI / REG-DI / POST-EVID / REPAIR-DI 全绿。

P7 最终状态：

```text
P7 — GOVERNANCE ENGINEERING
Canonical Authority / Spec Freeze / Architecture Freeze / Change Control   PASS
Governance Provenance / Measured Evidence / Regression Integrity           PASS
Repair Evidence Integrity / Required Test Enforcement / QA Stage           PASS
Release Default Deny / CLI Fail Closed                                     PASS
Schema Attack Tests / Direct-object Attack Tests / Positive Eligible Path  PASS
Governance Test Failures 0 / Required Skips 0 / Known Governance Bypasses 0
P7 STATUS: 100% COMPLETE — CLOSED / ACCEPTED
```

核心停止条件已满足：**No Unauthorized Change + No Unmeasured Release
Evidence + No Known Fail-Open Path**。此后明确停止 P7 开发，不新增
Reviewer / Gate / Validator 层级；工程重点转入 P9 RC Closure → v1.0.0
Release（Root snapshot、RC_EVIDENCE 完整包、正式发布包属于 P9，不阻塞 P7）。

### P7 最终补丁（CP-GOV-FINAL-02，2026-08-31）

最后一个 Predicate hardening patch——**顶层 Governance Count 谓词对称**：

- `compute_release_result()` 对 `unauthorized_spec_changes` 与
  `spec_deviations` 复用统一 `_is_non_negative_int()`（int、非 bool、>= 0）
  后再要求 `== 0`，消除 `False == 0` / `0.0 == 0` 的直接构造绕过。
- 新增 GOV-DI-COUNT-01..04（`False` / `0.0` 直接构造 → BLOCK）
  与正向保护测试 `test_zero_governance_counts_remain_eligible`
  （合法零计数保持 ELIGIBLE，防止 Fail Closed → Everything Closed）。
- 至此 Schema 与 Final Predicate 在 Governance Counts / Regression Counts /
  Repair Counts 三层完全对称，统一复用 `_is_non_negative_int()`。

最终验收：`test_release_evidence.py` 99 项 0 failed；完整 Governance
Attack Suite（schema / GOV / GOV-AUD / GOV-DI / GOV-DI-COUNT / REG-DI /
POST-EVID / REPAIR-DI）全绿；Windows Canonical Full Regression
**258 collected / 258 passed / 0 failed / 0 skipped / 0 PytestCacheWarning**；
Golden Environment + Golden PASS；CLI 合法 → RELEASE_ELIGIBLE（exit 0）、
`unauthorized_spec_changes=false` → schema reject（exit 1，compile 前 fail fast）。

```text
P7 — GOVERNANCE ENGINEERING
Canonical Authority / Spec Freeze / Architecture Freeze / Change Control   PASS
Governance Provenance / Measured Evidence / Regression Integrity           PASS
Repair Evidence Integrity / Governance Count Integrity                    PASS
Required Test Enforcement / QA Enforcement / Release Default Deny          PASS
CLI Fail Closed                                                            PASS
Schema Attack Tests / Direct-object Attack Tests / Positive Eligible Path PASS
Known Governance Bypasses 0 / Test Failures 0 / Required Skips 0
STATUS: 100% COMPLETE — CLOSED / ACCEPTED
```

**停止 P7**：不再为 Python 奇异值无限 fuzzing；仅当问题明确违反
CANONICAL_SPEC 已有 Contract 时才重新打开 P7。下一步直接进入
**P9 Release Candidate Closure**。

### 合并器安全与 RC 证据收口（MERGER-SEC-01 / RC-EVID-01，2026-08-31）

P7 保持 CLOSED；本轮为 P0 安全 + P1 RC 一致性 + P2 快照瘦身：

- **P0 MERGER-SEC-01**：合并器升级为“文件名过滤 → 读取 → 内容秘密扫描 →
  BLOCK/MERGE”。新增 `SECRET_PATTERNS`（sk- token / AWS AKIA / GitHub
  token / private key header），命中即跳过整个文件且仅记录 pattern 名称，
  绝不输出秘密值。`Doc/Install_codex.txt` 中一行含 DeepSeek API key 形状
  （`sk-` + 32 位十六进制）的示例值已脱敏为占位符 `<YOUR_DEEPSEEK_API_KEY>`
  （经确认该值并非真实 key，无需轮换）。
- **P2 MERGER-CLEAN-01 / MERGER-TEST-01**：排除 `.egg-info`、`input/`、
  `input_test/`、`output/`、`.env`、`*.min.js` 等；保留
  `md_converter/tests/acceptance/`；合并器自带 9 项自测
  （`tools/project_merger.py --self-test`）。
- **P1 RC-EVID-01**：`RC_EVIDENCE/` 冻结为唯一正式 RC Evidence Package；
  删除 root 证据副本；单一 RC ID **RC-20260831-04**（governance 与 release
  的 regression.current 完全一致）；新增
  `tools/rc_evidence_check.py` 一致性检查（spec_version / spec_status /
  current / new_failures / unauthorized / deviations / result）。
- **MDC(8) 快照**：`merged_code_MDC(8).txt` 由新合并器生成——
  137 文件合并、0 read failures、快照内 secrets=0、`.egg-info/input/`
  排除、acceptance corpus 保留。

验收：merger self-test 9/9 PASS；snapshot secret leak=0；RC package
internal mismatches=0；Full Regression 258/258、0 failed、0 skipped；
Golden canonical；Release Decision RELEASE_ELIGIBLE。

项目阶段推进：P7 Governance CLOSED → P8 Verification PASS → **P9 RC
Closure（RC-20260831-04 READY）** → P10 v1.0.0 RELEASE（正式发布包另行执行）。

---

## 变更流程

1. 提出变更 → 分类（DEFECT / TEST_DEFECT / SPEC_GAP / ARCH_CHANGE /
   OPTIONAL_IMPROVEMENT）。
2. `SPEC_GAP` / `ARCH_CHANGE` → 撰写/更新 ADR → 更新本文件 → 更新
   `CANONICAL_SPEC.md` 头部 → Re-freeze（记录新的 `spec_version`）。
3. 任何 FROZEN 条目的修改不得由普通 Patch 顺便完成。
