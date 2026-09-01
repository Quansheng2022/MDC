下面是基于最新 **MDC(10)**、P7/P8/P9 验收结果整理后的 **MD_Converter Project Roadmap 当前冻结版**。原项目 Roadmap 定义了 P0–P12 的生命周期；当前实际进度已经推进到 **P9 CLOSED / ACCEPTED，P10 为下一阶段**。

| S/N | Phase   | 任务                            | 主要交付物                                                                                 | 交付验收清单                                                                                                                                                                                        | 完成状态                         |
| --: | ------- | ----------------------------- | ------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------- |
|   1 | **P0**  | Product Definition            | 产品目标、Scope、Must/Should/Not Now                                                        | ✓ 明确 Markdown→DOCX 产品定位；✓ 控制系统复杂度；✓ 明确非目标；✓ 不追求完整 Markdown 生态/GUI/Cloud 等非当前需求                                                                                                                | ✅ **100% COMPLETE**          |
|   2 | **P1**  | Canonical Specification       | `CANONICAL_SPEC.md`、`SPEC_CHANGELOG.md`                                               | ✓ Canonical Spec 为唯一权威；✓ `spec_version=1.0`；✓ `spec_status=FROZEN`；✓ Software/Architecture/Theme/Acceptance/Governance baseline 明确；✓ 修改必须走 ADR→Spec→Changelog→Re-freeze                       | ✅ **FROZEN / COMPLETE**      |
|   3 | **P2**  | Architecture Design           | Architecture Spec、ADR-001~009                                                         | ✓ Parser→AST→Pipeline→LayoutPlan→Renderer→PostProcessor；✓ 模块职责隔离；✓ AST immutable；✓ Decision≠Execution；✓ Architecture Freeze                                                                   | ✅ **FROZEN / COMPLETE**      |
|   4 | **P3**  | Implementation Specification  | Implementation Specification、Implementation Plan、Phase Specs                          | ✓ Architecture 映射到类/函数/模块；✓ SPEC-ID→IMP-ID 可追踪；✓ Allowed/Forbidden Scope；✓ 测试及 Acceptance mapping 完整                                                                                          | ✅ **100% COMPLETE**          |
|   5 | **P4**  | Foundation Development        | Parser、AST、CompilerContext、Pipeline、PassRegistry、NormalizePass、Diagnostics、Config     | ✓ Parser deterministic；✓ Immutable AST；✓ Pipeline boundary 清晰；✓ Config resolved before execution；✓ Foundation unit tests PASS                                                                 | ✅ **100% COMPLETE**          |
|   6 | **P5**  | Rendering Development         | DecisionEngine、LayoutPlan、WordRenderer、WordWriter、Theme、Diagram/ASCII、Cover/TOC/Table | ✓ AST→Plan→DOCX 路径完整；✓ Renderer 不越权；✓ Theme V1.5 冻结；✓ Mermaid/ASCII 支持；✓ Integration tests PASS                                                                                               | ✅ **100% COMPLETE**          |
|   7 | **P6**  | Quality Engineering           | StaticQA、RenderedQA、RepairStrategy、PostProcessor、FinalArtifactQA                      | ✓ StaticQA FAIL→reject；✓ RenderedQA 强制；✓ Repair bounded；✓ PostProcessor evidence；✓ FinalArtifactQA 检查最终发布对象；✓ SHA256 evidence                                                                 | ✅ **100% COMPLETE**          |
|   8 | **P7**  | Governance Engineering        | Canonical Authority、Change Control、Evidence Gate、Release Predicate                    | ✓ Spec Freeze；✓ unauthorized changes=0；✓ spec deviations=0；✓ Governance provenance；✓ Regression/Repair/Governance counts fail-closed；✓ Schema + direct-object attack tests；✓ Known bypass=0   | ✅ **100% CLOSED / ACCEPTED** |
|   9 | **P8**  | Verification & Acceptance     | Unit / Integration / Golden / Acceptance / Regression Evidence                        | ✓ Unit PASS；✓ Integration PASS；✓ Golden PASS；✓ Acceptance PASS；✓ Playwright+Chromium canonical；✓ Full Regression **258/258**；✓ failed=0；✓ required skip=0                                     | ✅ **PASS / COMPLETE**        |
|  10 | **P9**  | Release Candidate Closure     | `RC_EVIDENCE/`、Release Evidence、Governance Evidence、Golden report、Test report         | ✓ 单一 RC ID；✓ RC package consistency=0 mismatch；✓ `RC-20260831-04`；✓ QA 全 PASS；✓ remaining_errors=0；✓ new_failures=0；✓ artifact SHA；✓ `RELEASE_ELIGIBLE`                                       | ✅ **100% CLOSED / ACCEPTED** |
|  11 | **P10** | **v1.0.0 Production Release** | 正式 v1.0.0 Release Package、Tag、Release Notes、Install Guide                             | □ Version Freeze；□ Final clean checkout/build；□ Final regression；□ RC evidence attach；□ Git tag `v1.0.0`；□ Release Notes；□ Installation/Golden Environment Guide；□ Known Limitations；□ 正式发布审批 | 🟡 **NEXT / CURRENT TARGET** |
|  12 | **P11** | Maintenance                   | v1.0.x Patch Releases                                                                 | □ Bug/Implementation/Spec Change 正确分类；□ 不改变冻结 architecture；□ backward compatibility；□ regression mandatory；□ Golden mandatory；□ Patch Release Evidence                                        | ⏳ **PLANNED**                |
|  13 | **P12** | Product Evolution             | v1.1+ Product Quality / Feature Evolution                                             | □ 根据真实使用反馈立项；□ Complex Table；□ Long Document；□ Mermaid robustness；□ Image handling；□ CN/EN typography；□ Spec Change 必须重新走 Change Gate                                                         | ⏳ **PLANNED**                |

P1 的冻结状态在最新 Canonical Spec 中仍明确为 `spec_version=1.0 / spec_status=FROZEN / software_version=1.0.0 / acceptance baseline AC001–AC015`。

P7 已有明确关闭证据：Governance Authority、Freeze、Change Control、Provenance、Regression/Repair integrity、Default Deny、Attack Tests 全部 PASS，且 `Governance Test Failures=0 / Required Skips=0 / Known Governance Bypasses=0`。

P9 的正式 RC Evidence 当前记录 `RC-20260831-04`，Unit/Integration/Golden/Acceptance 全 PASS，四个 QA stage 全 PASS，`remaining_errors=0`、`new_failures=0`，最终决策为 **`RELEASE_ELIGIBLE`**。

### Supporting Tooling Roadmap

| S/N | 工具任务                            | 交付验收清单                                                                                                                                                                                  | 状态                      |
| --: | ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- |
|  T1 | Project Snapshot Generator      | ✓ Project-root scan；✓ `input/input_test/output` 排除；✓ `.egg-info` 排除；✓ historical `merged_code_*` 排除；✓ sensitive dotfile default-deny；✓ embedded secret scan；✓ RC/Acceptance evidence 保留 | ✅ **CLOSED / ACCEPTED** |
|  T2 | Merger Self-Test                | ✓ `.env/.env.local/.env.production/.npmrc/.pypirc` BLOCK；✓ `.env.example` Allow；✓ minified JS/CSS BLOCK；✓ Secret BLOCK；✓ historical/current snapshot BLOCK                              | ✅ **18/18 PASS**        |
|  T3 | Snapshot Integrity              | ✓ 144 visited；✓ 135 merged；✓ 9 intentional skips；✓ **0 read failures**；✓ snapshot SHA256 generated                                                                                      | ✅ **PASS**              |
|  T4 | RC Evidence Consistency Checker | ✓ Governance/Release spec fields MATCH；✓ RC ID MATCH；✓ new_failures MATCH；✓ release result=`RELEASE_ELIGIBLE`；✓ mismatch→exit 1                                                         | ✅ **CLOSED / ACCEPTED** |

MDC(10) 本身证明最新 Snapshot 已达到 **135 files merged / 9 intentional skips / 0 read failures**。 Merge Report 也确认历史 `merged_code_MDC(8).txt` 已被正确排除。

### 当前项目位置

```text
P0  Product Definition           ✅
 ↓
P1  Canonical Specification      ✅ FROZEN
 ↓
P2  Architecture Design          ✅ FROZEN
 ↓
P3  Implementation Spec          ✅
 ↓
P4  Foundation Development       ✅
 ↓
P5  Rendering Development        ✅
 ↓
P6  Quality Engineering          ✅
 ↓
P7  Governance Engineering       ✅ CLOSED / ACCEPTED
 ↓
P8  Verification & Acceptance    ✅ PASS
 ↓
P9  RC Closure                   ✅ CLOSED / ACCEPTED
 ↓
P10 v1.0.0 Production Release    ◀ CURRENT TARGET
 ↓
P11 Maintenance                 ⏳
 ↓
P12 Product Evolution           ⏳
```

因此现在最合理的工程动作不是继续修改 P7、P8、P9 或合并器，而是**冻结已验收 RC，制定并执行 P10 v1.0.0 Production Release Checklist**。
