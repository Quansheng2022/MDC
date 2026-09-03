# Traceable Implementation Plan（模板）

本模板用于把 Review 输出转换为可追踪、有边界的实施计划，解决 LLM 常见的
“局部合理、全局漂移”问题。

## 1. 追踪链

```text
SPEC → IMP → Code → Test
```

要求：

- 每个 implementation item 必须包含 `IMP-ID`，并引用 `SPEC-ID` / `ADR-ID`。
- 必须显式声明 **Allowed Scope** 与 **Forbidden Scope**。
- Patch Prompt 中必须包含：

> 不得修改未列入 Change Plan 的模块；如发现额外问题，仅报告，不修改。

- `SPEC → IMP → Code → Test` 必须可以双向追踪。

## 2. 条目格式

```text
IMP-<NNN>

Source:
  SPEC-<XXX>-<NNN>
  SPEC-<XXX>-<NNN>
  ADR-<NNN>

Modify:
  <module 1>
  <module 2>

Do not modify:
  <module A>
  <module B>

Required Evidence:
  UT-<XXX>-<NNN>
  IT-<XXX>-<NNN>
  GOLDEN-<NNN>
  AC-<NNN>

Acceptance Criteria:
  <可验证的行为标准>
```

### 示例

```text
IMP-023

Source:
  SPEC-INV-014
  SPEC-AC-031
  ADR-009

Modify:
  compiler.py
  renderer/layout/rendered_qa.py

Do not modify:
  AST node schema
  Parser behavior
  Pass ordering
  Frozen Theme YAML

Required Evidence:
  UT-QA-003
  IT-COMPILER-007
  GOLDEN-012
  AC-010

Acceptance Criteria:
  RenderedQA FAIL 时编译器抛出 QualityGateError，
  且输出目录不存在最终 DOCX Release artifact。
```

## 3. 实施清单

> 新增实施条目时复制 §2 的格式追加到此处，并按 IMP-ID 递增。

---

### IMP-001：StaticQA 升级为 Build Gate（P0-05）

```text
Source:
  SPEC-QA-001
  SPEC-INV-007
  ADR-009

Modify:
  md_converter/quality_gate.py（新建：QualityGateError / QualityGatePolicy）
  md_converter/compiler.py

Do not modify:
  Parser 行为、AST schema、Pass 顺序、冻结 Theme YAML

Required Evidence:
  UT-QA-001（空 AST → build rejected）
  UT-QA-002（非法 heading level → build rejected）
  UT-QA-003（body_font < minimum → build rejected）
  UT-QA-004（warning-only issue → build allowed）

Acceptance Criteria:
  StaticQA FAIL 时编译抛 QualityGateError，不产生 Release artifact。
```

### IMP-002：RenderedQA Gate + QualityGatePolicy（P0-06）

```text
Source:
  SPEC-QA-002
  SPEC-INV-008

Modify:
  md_converter/quality_gate.py
  md_converter/compiler.py
  md_converter/config.py（quality_gate 默认策略）

Do not modify:
  Parser 行为、AST schema、Pass 顺序

Required Evidence:
  UT-QA-005（QualityGatePolicy.from_config 默认值）
  UT-QA-006（decide_qa 决策表）
  IT-COMPILER-002（RenderedQA FAIL → QualityGateError）

Acceptance Criteria:
  配置里的 fail_on_error / fail_on_warning 真正控制程序行为；
  RenderedQA FAIL 无法静默进入 Release Candidate。
```

### IMP-003：Repair 有限闭环（P0-07）

```text
Source:
  SPEC-QA-003
  SPEC-INV-009

Modify:
  md_converter/compiler.py
  md_converter/quality_gate.py（RepairRecord / 修复证据）

Do not modify:
  AST semantic content、Parser 行为、冻结 Theme YAML

Required Evidence:
  UT-QA-007（RepairRecord 记录修复证据）
  IT-COMPILER-003（Repair → Re-render → Re-inspect，最多 max_repair_iterations 次）

Acceptance Criteria:
  Render → Inspect → Repair → Re-render → Re-inspect 有限闭环；
  任何被 Repair 的 DOCX 至少再经过一次 RenderedQA。
```

### IMP-004：Final Artifact QA（P0-08）

```text
Source:
  SPEC-QA-004
  SPEC-INV-010

Modify:
  md_converter/renderer/layout/final_artifact_qa.py（新建）
  md_converter/compiler.py

Do not modify:
  Parser 行为、AST schema、Pass 顺序

Required Evidence:
  UT-QA-008（FinalArtifactQA 检查清单）
  IT-COMPILER-004（最终发布文件 sha256 == Final QA 检查文件 sha256）

Acceptance Criteria:
  测试对象 == 发布对象；Post-Processor 后的最终文件必须经过 Final QA。
```

### IMP-005：Canonical Acceptance Corpus（P1-09）

```text
Source:
  SPEC-AC-001..005
  SPEC-INV-001

Modify:
  md_converter/tests/acceptance/（AC001..AC015 + manifest.json）
  md_converter/tests/test_acceptance.py

Do not modify:
  现有 Golden Test 机制（在其基础上扩展）

Required Evidence:
  AC-001..AC-015 全部通过

Acceptance Criteria:
  每个 RC 必须通过完整 corpus；Golden baseline 更新必须走
  investigate → ADR/Spec approval → approve baseline 流程。
```

### IMP-006：Release Evidence（P1-10）

```text
Source:
  SPEC-INV-010
  SPEC-AC-005

Modify:
  md_converter/release_evidence.py（新建）
  md_converter/cli.py（release-evidence 命令 / --release-evidence 选项）
  pyproject.toml（entry point）

Do not modify:
  Parser 行为、AST schema、Pass 顺序

Required Evidence:
  UT-EVIDENCE-001（决策规则：RELEASE_ELIGIBLE / RELEASE_BLOCKED）
  UT-EVIDENCE-002（RELEASE_EVIDENCE.md + release_evidence.json 生成）

Acceptance Criteria:
  没有 Release Evidence 的 build 不得标记为 RC；
  Release Decision 由规则生成，不由模型口头判断。
```

### IMP-007：Post-Processor Contract Gate（治理收口 1）

```text
Source:
  SPEC-QA-004
  SPEC-INV-010
  ADR-007

Modify:
  md_converter/renderer/layout/artifact_contract.py（新建：ArtifactContract）
  md_converter/compiler.py（POST001 warning -> QualityGateError fail closed）
  md_converter/renderer/layout/final_artifact_qa.py（required feature -> ERROR）
  md_converter/quality_gate.py（post_processor stage / GATE_SEQUENCE）

Do not modify:
  Parser、AST、Pipeline、DecisionEngine、Renderer core、Theme V1.5

Required Evidence:
  POST-01..POST-07（test_quality_gate.py）

Acceptance Criteria:
  PostProcessor infrastructure failure 无法逃逸（逃逸 = 0）；
  required TOC/Cover/table styling 缺失 = BLOCK；
  显式关闭的功能缺失 = PASS。
```

### IMP-008：Mandatory Test Evidence Contract（治理收口 2）

```text
Source:
  SPEC-AC-004
  SPEC-INV-010

Modify:
  md_converter/release_evidence.py（REQUIRED_TEST_SUITES / normalize /
    validate / compute 显式判断）
  md_converter/cli.py（--test-report schema 校验）
  md_converter/tests/test_release_evidence.py（测试证据矩阵）

Do not modify:
  Parser、AST、Pipeline、Renderer core、Theme V1.5

Required Evidence:
  test_release_tests_evidence_matrix（8 例）

Acceptance Criteria:
  unit / integration / golden / acceptance 缺一不可；
  SKIPPED / NOT_RUN Required Suite -> RELEASE_BLOCKED；
  optional suite 不阻断。
```

### IMP-009：Measured Governance Evidence（治理收口 3）

```text
Source:
  SPEC-AC-005
  SPEC-INV-010

Modify:
  md_converter/release_evidence.py（None / NOT_CHECKED 默认值，
    Default Deny compute）
  md_converter/cli.py（--governance-report 输入与校验）
  governance_evidence.json（示例治理证据）
  md_converter/tests/test_release_evidence.py（GOV-01..12 矩阵）

Do not modify:
  Parser、AST、Pipeline、Renderer core、Theme V1.5

Required Evidence:
  test_governance_decision_matrix（13 例）+ test_build_release_evidence_missing_governance_blocked

Acceptance Criteria:
  治理指标不允许默认 0；未检测（None / NOT_CHECKED）-> BLOCK；
  Regression 0 必须来自 CHECKED evidence；
  Release Evidence 只读取/汇总证据，不制造证据。
```

### IMP-010：Governance 负数绕过修复（F1，P0）

```text
Source:
  SPEC-AC-005（Release Gate Default Deny）

Modify:
  md_converter/release_evidence.py（非负校验 + new<=current + !=0 predicate）
  md_converter/tests/test_release_evidence.py（GOV-NEG-01..06 + defense-in-depth）

Do not modify:
  Compiler / Renderer / Parser / AST / Pipeline

Required Evidence:
  test_governance_negative_schema_rejected（6 例）
  test_direct_negative_governance_cannot_bypass_gate（3 例）

Acceptance Criteria:
  negative governance input: schema escaped = 0；
  direct negative Release bypass: escaped = 0。
```

### IMP-011：PostProcessor 证据纳入 Release（F2，P1）

```text
Source:
  SPEC-QA-004（actual decision path == reported decision path）

Modify:
  md_converter/compiler.py（post_processor_result 记录与 reset）
  md_converter/release_evidence.py（REQUIRED_QA_STAGES + PASS/NOT_REQUIRED）
  md_converter/tests/test_release_evidence.py（POST-EVID-01..07）

Do not modify:
  Parser / AST / Pipeline / Renderer core / Theme V1.5

Required Evidence:
  test_post_processor_evidence_pass / not_required
  test_post_processor_stage_decision（4 例）+ missing stage

Acceptance Criteria:
  Gate actually ran == Evidence proves gate ran；
  post_processor PASS / NOT_REQUIRED 放行，其余 BLOCK。
```

### IMP-012：Governance 审计元数据（F3，P1）

```text
Source:
  SPEC-AC-005（evidence provenance recorded）

Modify:
  md_converter/release_evidence.py（checked_at/checked_by/mechanism/
    regression baseline/current + schema 校验 + 输出）
  md_converter/cli.py（--governance-report 校验）
  governance_evidence.json
  md_converter/tests/test_release_evidence.py（GOV-AUD-01..07）

Do not modify:
  Parser / AST / Pipeline / Renderer core

Required Evidence:
  test_governance_audit_schema_rejected（6 例）+ complete accepted

Acceptance Criteria:
  checked_at / checked_by / mechanism 必填；
  regression baseline / current 必填；非法 provenance -> schema reject。
```

### IMP-013：配置唯一权威（F4，P1）

```text
Source:
  SPEC-ARCH（Configuration belongs in config.yaml / 单一来源）

Modify:
  md_converter/config.py（CompilerConfig 引用 DEFAULT_CONFIG）
  md_converter/compiler.py（docstring 指向 DEFAULT_CONFIG）
  md_converter/renderer/layout/artifact_contract.py（只消费 resolved config）
  md_converter/tests/test_config.py（一致性测试）

Do not modify:
  Parser / AST / Pipeline / Renderer core / Theme V1.5

Required Evidence:
  test_canonical_configuration_defaults_are_consistent

Acceptance Criteria:
  DEFAULT_CONFIG 为唯一默认值来源；CompilerConfig / ArtifactContract
  与 resolved config 完全一致；任意单点改动 -> 测试失败。
```

### IMP-014：Golden 环境收口（F5，Release）

```text
Source:
  SPEC-AC-004（Golden 必须在 Canonical renderer 环境验收）

Modify:
  GOLDEN_ENVIRONMENT.md（新建：环境契约 + CI 顺序）
  md_converter/tests/test_golden.py（renderer_backend 记录 + 环境契约守卫）
  input/converter2.md（恢复 fixture，关闭测试 skip）

Do not modify:
  Parser / AST / Pipeline / DiagramPass 逻辑 / Renderer core / Theme V1.5

Required Evidence:
  test_golden（renderer_backend=playwright 环境）
  全量 pytest：220 collected / 220 passed / 0 skipped

Acceptance Criteria:
  Golden baseline 记录 renderer_backend；
  后端不一致时显式失败（不得拿同一条 baseline 跨环境假装通过）；
  required test skip = 0。
```

### IMP-015：Governance Provenance Defense-in-Depth（C1）

```text
Source:
  SPEC-AC-005（Final Release Predicate 自身也必须拒绝非法 provenance）

Modify:
  md_converter/release_evidence.py（_is_valid_iso8601 统一校验；
    regression.checked_at 必填；compute 重新验证 provenance）
  md_converter/tests/test_release_evidence.py（GOV-DI-01..08 绕过攻击测试）

Do not modify:
  Compiler / Renderer / Parser / Pipeline

Required Evidence:
  test_final_predicate_rejects_bypassed_provenance（8 例）
  test_governance_provenance_schema_rejected（4 例）

Acceptance Criteria:
  schema invalid provenance escaped = 0；
  direct ReleaseEvidence provenance bypass escaped = 0；
  regression provenance 缺失 -> BLOCK；valid governance -> Eligible。
```

### IMP-016：Canonical Config Authority 单一化（C2）

```text
Source:
  SPEC-ARCH（DEFAULT_CONFIG 是唯一默认值来源）

Modify:
  md_converter/renderer/layout/artifact_contract.py（删除字段默认值）
  md_converter/compiler.py（post_features 直接消费 resolved keys）
  md_converter/renderer/post_processor.py（注释：低层兼容 fallback 非权威）
  md_converter/tests/test_config.py（无隐式默认值/匹配/override 测试）

Do not modify:
  实际默认值（toc/cover/style_tables 仍为 True）

Required Evidence:
  test_artifact_contract_has_no_implicit_defaults
  test_artifact_contract_matches_resolved_config
  test_artifact_contract_respects_explicit_overrides

Acceptance Criteria:
  ArtifactContract() -> TypeError；from_config(unresolved) -> ValueError；
  from_config(resolve_config(...)) -> PASS；Compiler 缺 key -> KeyError（Fail Fast）。
```

### IMP-017：Canonical Golden Runtime 固化（C3）

```text
Source:
  SPEC-AC-004（Golden 为 Required Release Suite，环境必须固定）

Modify:
  pyproject.toml（[mermaid] extra，playwright>=1.62,<2）
  GOLDEN_ENVIRONMENT.md（Setup / Verification / preflight）
  md_converter/tests/fixtures/converter2.md（固化 fixture）
  md_converter/tests/test_ascii_mermaid_service.py（依赖自身 fixture，
    skip 改 fail）

Do not modify:
  Golden expected 结构 / DiagramPass 语义 / Renderer core

Required Evidence:
  Golden PASS（renderer_backend=playwright）
  Full pytest 235/235，0 skipped

Acceptance Criteria:
  Canonical backend = Playwright；Chromium 安装为环境准备步骤；
  后端不一致 -> FAIL 不 skip；fixture 不依赖工作区 input/。
```

### CP-FINAL-01：Regression Evidence Predicate Symmetry（R1）

```text
Source:
  SPEC-AC-005（Input Validation + Decision Validation 对称）

Modify:
  md_converter/release_evidence.py（_is_non_negative_int 统一校验；
    compute 重新校验三个 counts + new<=current + new==0）
  md_converter/tests/test_release_evidence.py（REG-DI-01..09）

Do not modify:
  Compiler / Parser / Pipeline / Renderer / QualityGate /
  Acceptance Corpus / Golden baseline

Required Evidence:
  test_final_predicate_rejects_malformed_regression_counts（7 例）
  test_regression_fixed_failures_allowed / zero_counts_eligible_candidate

Acceptance Criteria:
  illegal regression evidence escaped Final Gate = 0；
  valid regression evidence 保持 eligible；不新增错误数学约束。
```

### CP-FINAL-02：Canonical Golden Runtime Closure（R2）

```text
Source:
  SPEC-AC-004（Golden 为 Mandatory Release Suite）

Modify:
  pyproject.toml（playwright==1.62.0 精确 pin）
  md_converter/tests/golden_environment.py（preflight：真实 Chromium launch）
  md_converter/tests/test_golden_environment.py（环境契约 FAIL not skip）
  GOLDEN_ENVIRONMENT.md（Setup / preflight / CDN 网络依赖声明）

Do not modify:
  Golden baseline / DiagramPass 语义 / Renderer core

Required Evidence:
  test_canonical_golden_environment PASS（canonical=True）
  Golden PASS（renderer_backend=playwright）

Acceptance Criteria:
  Playwright 包可用 + Chromium 实际 headless launch 成功；
  环境不满足 -> FAIL（不 skip）；Runtime capability detection
  与 Result backend attribution 保持两个独立函数。
```

### CP-FINAL-03：Release Evidence Package Closure（R3）

```text
Source:
  SPEC-INV-010（没有证据的 build 不得标记 RC）

Modify:
  RC_EVIDENCE/（最终 RC 证据包）
  governance_evidence.json / golden_environment_report.json（真实生成）

Do not modify:
  核心代码（本项为证据/发布流程）

Required Evidence:
  RC_EVIDENCE/full_pytest_summary.txt（真实 pytest 输出）
  golden_environment_report.json（真实 Chromium launch）

Acceptance Criteria:
  RC_EVIDENCE 包含 RELEASE_EVIDENCE / release_evidence.json /
  governance_evidence.json / test_report.json / golden_environment_report.json /
  full_pytest_summary.txt；test_report 来自真实运行，不手工写 PASS。
```

### CP-GOV-FINAL-01：Governance Predicate Closure（P7 100%）

```text
Source:
  SPEC-AC-005（Release Default Deny / Defense-in-Depth 与 Regression 对称）

Modify:
  md_converter/release_evidence.py（repair.remaining_errors 谓词 Fail-Closed）
  md_converter/tests/test_release_evidence.py（REPAIR-DI-01..08）

Do not modify:
  Parser / AST / Pipeline / AsciiToMermaid / DiagramPass / DecisionEngine /
  LayoutPlan / WordRenderer / WordWriter / Theme / Acceptance Corpus /
  Golden baseline / Compiler architecture

Required Evidence:
  test_final_predicate_rejects_invalid_remaining_errors（7 例）
  test_final_predicate_accepts_zero_remaining_errors
  test_release_evidence.py 全绿（0 failed / 0 skipped）
  Full pytest 253/253，0 failed，0 skipped
  CLI：malformed/missing evidence -> exit 1；合法 -> RELEASE_ELIGIBLE

Acceptance Criteria:
  remaining_errors 合法（int 非 bool >=0）且 == 0 才放行；
  负数 / None / bool / 字符串 / 浮点 / >0 全部 BLOCK；
  正向合法路径保持 ELIGIBLE（不被误伤）。
```

### CP-GOV-FINAL-02：Top-level Governance Count Predicate Symmetry（P7 最终补丁）

```text
Source:
  SPEC-AC-005（Schema + Final Predicate 双层一致；消除 False/0.0 绕过）

Modify:
  md_converter/release_evidence.py（unauthorized_spec_changes /
    spec_deviations 复用 _is_non_negative_int + ==0）
  md_converter/tests/test_release_evidence.py（GOV-DI-COUNT-01..04 +
    正向保护测试）

Do not modify:
  Parser / AST / Pipeline / NormalizePass / AsciiToMermaid / DiagramPass /
  DecisionEngine / LayoutPlan / StaticQA / RenderedQA / RepairStrategy /
  PostProcessor / FinalArtifactQA / WordRenderer / WordWriter / Theme /
  Acceptance Corpus / Golden baseline

Required Evidence:
  test_final_predicate_rejects_malformed_governance_counts（4 例）
  test_zero_governance_counts_remain_eligible
  test_release_evidence.py 99 项 0 failed / 0 skipped
  Full pytest 258/258，0 failed，0 skipped，0 PytestCacheWarning
  CLI：unauthorized=false -> exit 1；合法 -> RELEASE_ELIGIBLE

Acceptance Criteria:
  `0` 放行；`1 / -1 / None / False / True / 0.0 / "0"` 全部 BLOCK；
  正向合法零计数保持 ELIGIBLE；已知 Fail-Open Path = 0。
```

### MERGER-SEC-01：合并器内容秘密扫描（P0）

```text
Source:
  工具链安全（快照不得携带 embedded credential）

Modify:
  tools/project_merger.py（新建：SECRET_PATTERNS + detect_secrets +
    BLOCK whole file + 只记录 pattern 名称）
  Doc/Install_codex.txt（含 DeepSeek API key 形状的示例值 -> 占位符，
    经确认非真实 key，无需轮换）

Do not modify:
  md_converter/ / CANONICAL_SPEC / P7 Governance / Golden baseline /
  Acceptance corpus

Required Evidence:
  tools/project_merger.py --self-test（9 项）
  merged_code_MDC(8).txt（secrets=0）

Acceptance Criteria:
  sensitive filename leak=0；embedded high-confidence secret=0；
  secret value written to report=0；normal documentation false block=0。
```

### MERGER-CLEAN-01 / MERGER-TEST-01：快照瘦身与自测（P2）

```text
Source:
  降低快照 token 占用与检索噪音

Modify:
  tools/project_merger.py（EXCLUDE_DIRS 含 input/input_test/output/
    *.egg-info；.env / *.min.js 排除；保留 acceptance corpus；
    --self-test 9 项）

Do not modify:
  md_converter/ / CANONICAL_SPEC / P7

Required Evidence:
  --self-test PASS；MDC(8) 无 egg-info/input/output 内容

Acceptance Criteria:
  egg-info=0；input business docs=0；output self inclusion=0；
  .env leak=0；minified files=0；read error=0。
```

### RC-EVID-01：RC Evidence 单一权威目录（P1）

```text
Source:
  P9 RC Closure（单 RC ID、单证据包、0 内部漂移）

Modify:
  RC_EVIDENCE/（唯一正式包，RC-20260831-04）
  删除 root 证据副本（RELEASE_EVIDENCE.md / release_evidence.json /
    governance_evidence.json / golden_environment_report.json）
  tools/rc_evidence_check.py（新建：validate_rc_package）

Do not modify:
  Parser / AST / Pipeline / Renderer / QA semantics / P7 predicates /
  Golden baseline

Required Evidence:
  tools/rc_evidence_check.py --rc-dir RC_EVIDENCE -> mismatches=0

Acceptance Criteria:
  governance.regression.current == release.regression.current == RC-20260831-04；
  spec_version/spec_status/unauthorized/deviations/new_failures 全 MATCH；
  release.result == RELEASE_ELIGIBLE。
```

### IMP-018：Effective Table Border QA + PostProcessor Evidence Semantics（P0-TBL-001/002/003/004）

```text
Source:
  SPEC-QA-004（测试对象 == 发布对象，Final QA 检查 Word 保存后的最终文件）
  SPEC-FUNC-017（FinalArtifactQA 为强制质量门）
  SPEC-INV-006（Fail loudly，禁止静默吞掉异常）
  ADR-007（PostProcessor required capability -> FAIL CLOSED）

Modify:
  md_converter/renderer/layout/final_artifact_qa.py
    （_has_effective_table_borders：direct w:tblBorders OR Table Style 继承，
     修复 Word COM 规范化后 table_borders_missing 误报）
  md_converter/renderer/post_processor.py
    （_add_table_borders / _set_table_header_style 删除内部 try/except，
     异常交给 _style_tables 统一记录，保证“格式化 X/Y”计数可信）
  md_converter/tests/test_quality_gate.py
    （UT-QA-009 style-only borders PASS / UT-QA-010 borderless FAIL）
  md_converter/tests/test_post_processor.py
    （UT-POST-008/009 helper 异常向上传播）
  md_converter/tests/test_word_com_final_artifact.py
    （新建 IT-COMPILER-008：Windows Word COM round-trip FinalArtifactQA PASS）

Do not modify:
  Parser / AST / Pipeline / Renderer core / Theme V1.5 / CANONICAL_SPEC.md /
  冻结 Golden baseline / input 业务文档 / release_evidence.py predicates

Required Evidence:
  UT-QA-009（test_final_qa_table_grid_style_only_borders_pass）
  UT-QA-010（test_final_qa_truly_borderless_table_fails）
  UT-POST-008（test_add_table_borders_propagates_failure）
  UT-POST-009（test_set_table_header_style_propagates_failure）
  IT-COMPILER-008（test_word_com_roundtrip_final_artifact_qa_pass，
    Windows + Word + pywin32 环境）
  Full pytest 通过（仅 Golden 环境依赖项除外）
  md-converter input/（默认 word_com=True）MPC/PPCP 全部 PASS

Acceptance Criteria:
  Word COM 保存后，边框来自 Table Style 继承的表格不再误报
  table_borders_missing；真正无边框表格仍然 FAIL（负向不被放宽）；
  helper 失败时异常向上传播，计数真实反映执行结果；
  默认配置下 MPC_Roadmap.md / PPCP_Roadmap.md 均 FinalArtifactQA PASS。
```

### IMP-019：正文对齐默认改为左对齐（P1）

```text
Source:
  SPEC-ARCH-009（Renderer SHALL obtain formatting through StyleResolver）
  SPEC-FUNC-012（主题系统控制外观；对齐实现位于 StyleResolver，
    冻结主题 YAML 的 paragraph.alignment 配置当前未被实现消费，只报告不修改）

Modify:
  md_converter/renderer/style_resolver.py
    （paragraph_style / adaptive_paragraph_style：正文对齐 JUSTIFY -> LEFT，
     移除未使用的语言自适应两端对齐逻辑与 detect_language import）
  md_converter/tests/test_renderer_v15.py
    （test_cjk_paragraph_justified -> test_cjk_paragraph_left_aligned）

Do not modify:
  CANONICAL_SPEC.md / 冻结 Theme YAML（default_v1_5.yaml）/
  Parser / AST / Pipeline / PostProcessor / release_evidence.py predicates /
  LanguageProfile 检测逻辑（仍用于 Run 字体分割）

Required Evidence:
  test_cjk_paragraph_left_aligned / test_latin_paragraph_left_aligned /
  test_line_break_paragraph_left_aligned 全部通过
  Full pytest 通过（仅 Golden 环境依赖项除外）
  Governance_AI_Engineering.docx 正文段落 alignment == LEFT

Acceptance Criteria:
  编译产物中正文段落不再使用 JUSTIFY，统一 LEFT；
  显式自定义样式中的 "justify" 映射仍保留（_normalize_alignment 不变）；
  冻结主题 YAML 不被修改。
```

### IMP-020：Word COM Lifecycle Cleanup（P10-COM-01）

```text
Source:
  SPEC-GOAL-006
  SPEC-ARCH-005
  SPEC-INV-006
  SPEC-INV-012
  ADR-007

Classification:
  DEFECT

Severity:
  P1 Release Blocker

Problem:
  Windows Word COM round-trip successfully completed TOC refresh
  and DOCX Save, but COM teardown emitted Windows RPC fatal
  diagnostics:

    0x800706BE
    0x800706BA

  The defect was isolated to Word COM proxy lifecycle cleanup.

Allowed Scope:
  md_converter/renderer/post_processor.py
  md_converter/tests/test_word_com_final_artifact.py

Forbidden Scope:
  Parser
  AST
  Pipeline
  NormalizePass
  AsciiToMermaidPass
  DiagramPass semantics
  DecisionEngine
  LayoutPlan
  WordRenderer
  WordWriter
  Theme V1.5
  Golden baseline
  Acceptance Corpus
  release_evidence.py predicates
  CANONICAL_SPEC.md

Implemented Change:
  - Reset COM proxy state at each retry.
  - Release TOC proxy immediately after update.
  - Release Paragraph proxies before Document close.
  - Release Style proxies after each iteration.
  - Enforce cleanup order:

        Child COM proxies
              ↓
        Document Close
              ↓
        Document proxy release
              ↓
        Word.Application Quit
              ↓
        Word proxy release

Required Evidence:
  P10_COM01_before.txt
  P10_COM01_after_1.txt
  P10_COM01_run_1.txt
  P10_COM01_run_2.txt
  P10_COM01_run_3.txt
  RC_EVIDENCE/full_pytest_summary.txt

Acceptance Criteria:
  Dedicated Word COM test = PASS.
  Three consecutive Word COM tests = 3/3 PASS.
  Windows fatal exception = 0.
  0x800706BE = 0.
  0x800706BA = 0.
  Full Regression = 263/263 PASS.
  Required skip = 0.
  New failures = 0.
  Architecture change = 0.
  Canonical Specification change = 0.

Status:
  IMPLEMENTED / VERIFIED
```

### IMP-021：Packaging Single Authority（P10-PKG-01）

```text
Source:
  SPEC（Software Version authority：pyproject.toml / __version__）
  SPEC-QA-004
  SPEC-INV-010
  ADR-007

Classification:
  DEFECT

Category:
  RELEASE_PACKAGING

Severity:
  P1 Release Blocker

Problem:
  pyproject.toml 与 setup.py 并存且互相漂移：
  dependency/extras/scripts/theme entry-points/package-data 双重权威。
  实际代码不再 import pypandoc / typing-extensions；runtime 默认主题为
  V15Theme（default_v1_5.yaml），但 legacy setup.py 的 default entry-point
  指向 DefaultTheme；md-converter-release-evidence script 仅存在于
  pyproject.toml；md-converter-check script 指向 cli.py 中不存在的
  check_dependencies（WP-PKG-05 缺陷）；py.typed 声明存在但文件缺失；
  MANIFEST.in 引用不存在的
  LICENSE / CHANGELOG / CONTRIBUTING / requirements.txt / examples 与
  错误路径的 tests；README 仍指导“在 setup.py 中添加 entry_points”并声称
  Pandoc 可选依赖；AGENTS.md 声明 `pip install -e .[dev]` 但 pyproject
  无 dev extra（仅 legacy setup.py 有）。

Allowed Scope:
  pyproject.toml
  MANIFEST.in
  setup.py（删除）
  README.md（packaging/install/plugin 文档对齐）
  md_converter/cli.py（新增 check_dependencies，修复 md-converter-check
    缺失目标；纯依赖可用性报告，不改编译逻辑）
  .gitignore（build/ dist/ *.egg-info/ 忽略）
  md_converter.egg-info（git rm --cached：生成 metadata 不再入库）
  md_converter/py.typed（新建 PEP 561 marker）
  md_converter/tests/test_packaging_metadata.py（新建）
  IMPLEMENTATION_PLAN.md
  Phase_10_Development_Specification.md

Forbidden Scope:
  CANONICAL_SPEC.md（FROZEN）
  Parser / AST / Pipeline / DiagramPass semantics / DecisionEngine /
  LayoutPlan / WordRenderer / WordWriter / PostProcessor
  Theme V1.5（default_v1_5.yaml）
  Golden baseline / Acceptance Corpus
  release_evidence.py predicates
  RC_EVIDENCE/ 既有证据
  chk_dependency_packages.py（额外发现，只报告不修改）

Implemented Change:
  - pyproject.toml 为唯一 production packaging authority。
  - 删除 legacy setup.py（不再维护第二套 dependencies/extras）。
  - 新增 cli.check_dependencies（md-converter-check 脚本目标，
    importlib.metadata 探测 required/optional 依赖，exit 0/1）。
  - package-data 收口：py.typed + renderer/themes/*.yaml。
  - 新建 md_converter/py.typed（PEP 561 marker）。
  - MANIFEST.in 对齐实际 sdist 资源，清除不存在文件引用。
  - extras 收口：windows / mermaid / dev；README 与 AGENTS.md 声称的
    `.[windows]` `.[mermaid]` `.[dev]` 全部可解析。
  - scripts 3 个（md-converter / md-converter-check /
    md-converter-release-evidence）与 entry-points 校验一致。
  - Development Status classifier -> 5 - Production/Stable。
  - license 字段改 SPDX（"MIT"），移除 License classifier（PEP 639，
    build-system setuptools>=77），构建零 deprecation warning。
  - .gitignore 增加 build/ dist/ *.egg-info/；egg-info 停止入库。
  - README：插件注册改 pyproject [project.entry-points]；删除 Pandoc
    声称；dev 安装命令示例补齐。
  - 新增 metadata 契约测试（PKG-META-01..12）。

Required Evidence:
  PKG-META-01..14（test_packaging_metadata.py 全绿）
  wheel / sdist 构建成功且包含 py.typed + default_v1_5.yaml
  Full pytest 回归（P10-18 最终门执行；本 WP 内 metadata 套件全绿）

Acceptance Criteria:
  Packaging authorities = 1（仅 pyproject.toml）。
  pyproject / wheel metadata / README 三方一致（metadata mismatch=0）。
  `pip install -e ".[dev]"` 可解析（dev extra 存在）。
  3 个 console scripts 与 entry-points 可导入解析。
  wheel 与 sdist 内含 md_converter/py.typed 与
    md_converter/renderer/themes/default_v1_5.yaml。
  MANIFEST.in 不再引用不存在的文件/目录。
  README 不再指导 setup.py entry_points，不再声称未声明的 Pandoc 依赖。
  `md-converter-check` 可执行且 required 依赖全绿时 exit 0。

Status:
  CLOSED / ACCEPTED

Closure Commit:
  cae92ff99accac94ce7dd2356cc470072efecdba

Human Acceptance:
  APPROVED

Packaging Authorities:
  1

Metadata Mismatch:
  0
```
