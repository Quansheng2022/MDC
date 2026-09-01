# Review Template + Change Classification Gate

本文件定义 ChatGPT/DeepSeek 等模型在 Review 后的**固定输出格式**与
**Issue 分类规则**。目的是防止 Reviewer 无意中拥有 Architecture Authority。

## 1. 工作流

```text
ChatGPT Review
      ↓
Issue Classification
   ├─ DEFECT
   ├─ TEST_DEFECT
   ├─ SPEC_GAP
   ├─ ARCH_CHANGE
   └─ OPTIONAL_IMPROVEMENT
```

## 2. 分类规则

| 分类 | 判定条件 | 路由 |
| --- | --- | --- |
| `DEFECT` | 代码行为不符合 Canonical Spec / 已冻结行为，属于实现缺陷 | Change Plan → Patch |
| `TEST_DEFECT` | 测试自身有误（断言、夹具、基线过期但不是有意行为变更） | Test Change Review → Test Patch |
| `SPEC_GAP` | 规范未覆盖、不清晰或相互矛盾，需要澄清行为 | Canonical Spec clarification → Re-freeze |
| `ARCH_CHANGE` | 修改 Parser/AST/Pipeline/Renderer/PostProcessor 职责边界、AST 结构、Pass 顺序、依赖方向等冻结架构 | ADR → Spec Update → Re-freeze |
| `OPTIONAL_IMPROVEMENT` | 无 SPEC-ID 支撑的增强建议 | backlog |

硬性规则：

1. **不存在未经 ADR/Spec Update 就修改 Frozen Architecture 的 Patch。**
2. 普通 Patch 不得“顺便”修改 FROZEN Specification、冻结 Theme 或 AST 结构。
3. Reviewer 只报告问题与分类，不直接修改架构文档或代码（除非被显式授权）。

## 3. 固定输出格式

每个 Issue 必须使用以下字段，禁止自由发挥：

```text
ISSUE-ID: ISSUE-<NNN>
Classification: <DEFECT | TEST_DEFECT | SPEC_GAP | ARCH_CHANGE | OPTIONAL_IMPROVEMENT>
Severity: <P0 | P1 | P2>
Violated SPEC-ID: <SPEC-XXX-NNN | N/A>
Evidence: <复现步骤 / 测试输出 / 代码位置，必须可验证>
Required Change: <期望的修复行为>
Allowed Scope: <允许修改的模块/文件>
Forbidden Scope: <禁止修改的模块/文件>
Required Tests: <UT-XXX / IT-XXX / GOLDEN-XXX / AC-XXX>
```

### 示例

```text
ISSUE-ID: ISSUE-001
Classification: DEFECT
Severity: P0
Violated SPEC-ID: SPEC-QA-001
Evidence: 空 Markdown 输入时 compiler 仍生成 document.docx，StaticQA
          返回 FAIL 但未被拦截（compiler.py 渲染阶段）。
Required Change: StaticQA FAIL 时必须抛出 QualityGateError，停止编译。
Allowed Scope: md_converter/compiler.py, md_converter/quality_gate.py
Forbidden Scope: Parser 行为、AST schema、Pass 顺序、冻结 Theme YAML
Required Tests: UT-QA-001（空 AST → build rejected）
```

## 4. 分类后的处理路径

```text
DEFECT
  → Change Plan → Patch（只允许 Allowed Scope）

TEST_DEFECT
  → Test Change Review → Test Patch

SPEC_GAP
  → Canonical Spec clarification → Re-freeze

ARCH_CHANGE
  → ADR → Spec Update → Re-freeze

OPTIONAL_IMPROVEMENT
  → backlog
```

## 5. 与 Traceable Implementation Plan 的衔接

每个被批准进入实施的问题，必须在 `IMPLEMENTATION_PLAN.md` 中登记为
一个 IMP-ID，引用本文件的 ISSUE-ID，并遵守 Allowed/Forbidden Scope。
