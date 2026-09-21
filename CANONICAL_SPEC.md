# MD Converter Canonical Specification

## 规范头部（Specification Header）

| 字段 | 值 |
| --- | --- |
| spec_version | 1.1 |
| spec_status | FROZEN |
| freeze_date | 2026-09-21 |
| architecture_version | 2.0 |
| theme_version | QS-Word-Default-V1.5 (1.5, frozen) |
| software_version | 1.1.0 |
| applicable_ADRs | ADR-001 至 ADR-009（见 `Doc/ARCHITECTURE.md`） |
| acceptance_baseline | AC001–AC018（`md_converter/tests/acceptance/`） |
| governance_baseline | P0-01..P0-08, P1-09, P1-10, P12（S/N 117–118，Human approved 2026-09-21） |

> 本文件是**整个项目的唯一 Canonical Authority**。当 `Doc/ARCHITECTURE.md`、
> `Doc/MD_Converter_Design_MVP3.0.md`、Theme YAML、代码、测试或任何 AI 生成计划
> 与本文件冲突时，**以本文件为准**。

## 版本号语义（Version Clarification）

本项目存在四类互相独立的版本号，**不得混用**：

| 版本号 | 含义 | 当前值 | 变更控制 |
| --- | --- | --- | --- |
| Specification Version | 规范版本（本文件） | 1.1 | 必须通过 SPEC_CHANGELOG + Re-freeze |
| Software Version | 软件包版本（`pyproject.toml` / `md_converter.__version__`） | 1.1.0 | 按语义化版本发布 |
| Theme Version | 冻结主题版本 | 1.5 (QS-Word-Default-V1.5) | 必须通过正式 RFC 流程 |
| Release Version | 发布版本（Release Evidence 中记录） | 1.1.0 | 由 Release Evidence 固化 |

设计文档中的“MVP 3.0”指**设计阶段**（Phase 3 MVP），不是 Software Version，
也不是 Specification Version。

## Specification Status 生命周期

```text
DRAFT → REVIEW → FROZEN → SUPERSEDED
```

规则：

1. `FROZEN` 状态的 Specification 只能通过正式的
   **ADR → SPEC Update → SPEC_CHANGELOG → Re-freeze** 流程修改。
2. 普通功能 Patch 不得顺便修改 `FROZEN` Specification。
3. 任何冻结项的修改必须记录 `spec_version`、`freeze_date`、
   `architecture_version`、`theme_version`、`applicable_ADRs`、
   `acceptance_baseline`。
4. 被替代的版本标记为 `SUPERSEDED`，保留在 `SPEC_CHANGELOG.md` 中供审计。

---

## 1. System Goals（SPEC-GOAL）

- **SPEC-GOAL-001**：将 Markdown 编译为生产级 DOCX，输出应可直接用于正式文档交付。
- **SPEC-GOAL-002**：保持严格编译器架构：Parser → AST → Pipeline → Renderer →
  Post-Processor → 最终产物，任何阶段不得被绕过。
- **SPEC-GOAL-003**：输出必须确定性：同一输入、同一配置、同一环境产生同一结果。
- **SPEC-GOAL-004**：语义保真优先于视觉表现：Markdown 语义内容不得静默丢失。
- **SPEC-GOAL-005**：质量门必须是真实 Gate，而不是诊断建议；FAIL 不得静默产出
  Release Candidate。
- **SPEC-GOAL-006**：开发与发布流程必须可审计：SPEC → IMP → Code → Test →
  QA → Release Evidence 可双向追踪。

## 2. Functional Scope（SPEC-FUNC）

### 2.1 已实现（FROZEN）

- **SPEC-FUNC-001**：标题（Heading 1–6）
- **SPEC-FUNC-002**：段落（Paragraph）
- **SPEC-FUNC-003**：列表（有序 / 无序 / 嵌套）
- **SPEC-FUNC-004**：表格（Table，含表头重复、数字列右对齐）
- **SPEC-FUNC-005**：代码块（Code Block）
- **SPEC-FUNC-006**：引用块（Block Quote）
- **SPEC-FUNC-007**：水平分割线（Horizontal Rule）
- **SPEC-FUNC-008**：行内格式（粗体 / 斜体 / 行内代码 / 链接 / 图片）
- **SPEC-FUNC-009**：Frontmatter 元数据
- **SPEC-FUNC-010**：封面页（Cover Page）
- **SPEC-FUNC-011**：目录（TOC，原生域代码）
- **SPEC-FUNC-012**：主题系统（QS-Word-Default-V1.5，冻结）
- **SPEC-FUNC-013**：DiagramPass（Mermaid 图渲染，失败时降级保留文本）
- **SPEC-FUNC-014**：AsciiToMermaidPass（ASCII 图 → Mermaid）
- **SPEC-FUNC-015**：NormalizePass（合并相邻文本节点）
- **SPEC-FUNC-016**：诊断系统（Diagnostics：code / severity / message / location / suggestion）
- **SPEC-FUNC-017**：质量门（StaticQA / RenderedQA / FinalArtifactQA，见 §4）
- **SPEC-FUNC-018**：修复闭环（Repair loop，默认最多 2 次迭代）
- **SPEC-FUNC-019**：Golden Tests
- **SPEC-FUNC-020**：Canonical Acceptance Corpus（AC001–AC018）
- **SPEC-FUNC-021**：Release Evidence（RELEASE_EVIDENCE.md + release_evidence.json）
- **SPEC-FUNC-022**：Simple Table Recognition（空白对齐简单表格识别）。
  仅当以下条件全部满足时，顶层段落 SHALL 转换为两列 `Table`：至少 3 行；第 2 行是
  ruler 行（仅空格与 >= 2 段 >= 3 个连字符，段间至少 1 个空格）；其余每行恰好含 1 段
  >= 2 个连续空格的列间隔且不含制表符；两个单元格均非空；所有列间隔存在公共锚点
  `b = max(起始) < min(结束)`；无 `|`；段落仅含纯文本与换行。ruler 行 SHALL NOT
  产生行，首行为表头行，单元格内容为去除首尾空白的纯文本。不满足任一条件时 SHALL
  保留原段落，且 SHALL NOT 产生诊断（CLAR-01：识别失败不是错误/警告条件）。
  识别结果 SHALL 与外部语料、文件路径无关，且对相同输入确定。
- **SPEC-FUNC-023**：Figure Page-Fit / 图形尺寸策略。交付图形 SHALL 适配**有效 section
  内容区**：有效宽度 = section 宽度 − 左右页边距，有效高度 = section 高度 − 上下页边距，
  目标宽度 = min(配置 `image_width`, 有效宽度)；有效内容区 SHALL 取自实际 section 几何，
  不得退化为硬编码常数（CLAR-02：A4 / 1in ≈ 15.92 × 24.62 cm 仅为当前参考几何）。
  尺寸 SHALL 保持宽高比、SHALL NOT 放大超过目标宽度、SHALL NOT 超出有效内容区宽高。
  按主题 `figure.overflow_handling` 顺序执行：先 `move_to_next_page`（按目标宽度插入，
  保留既有 keep-together 语义，由 Word 决定分页），再 `scale_down`（按有效高度收缩），
  再 `warn`（收缩后宽度低于主题 `figure.min_width` 时仍交付适配尺寸并产生结构化 WARNING）。
  图形无法读取时保留既有文档化降级行为。最终物理分页归 Word，converter 不承诺页码或
  分页确定性。
- **SPEC-FUNC-024**：空标题行为（WARN + DROP）。plain text 去空白后为空的标题
  SHALL NOT 被渲染：不产生段落、不产生占位文本、不递增标题计数。该 Heading 节点
  SHALL 保留在 AST 中（source truth），既有 StaticQA 空标题 WARNING SHALL 保持。
  compiler SHALL NOT 为空标题注入字面内容（如 `"Heading"`），SHALL NOT 产生合成 TOC
  条目或标题编号。

### 2.2 未实现（明确不在当前 Scope）

- 交叉引用（Cross References）
- 脚注（Footnotes）
- 增量编译（Incremental Compilation）
- PDF 后端
- HTML 后端
- 多线程编译
- 数学公式渲染

## 3. Architecture Contract（SPEC-ARCH）

以下条目为 **Architecture Invariant**，任何变更必须先走 ADR + Spec Re-freeze：

- **SPEC-ARCH-001**：Parser SHALL only construct AST。Parser 不得生成 DOCX、
  不得渲染图片、不得执行业务逻辑。
- **SPEC-ARCH-002**：AST SHALL be immutable。所有节点使用
  `@dataclass(frozen=True)`；修改必须返回新节点；AST 只存储语法，
  不得存储渲染状态或运行时状态。
- **SPEC-ARCH-003**：Pipeline SHALL only transform AST。每个 Pass 必须返回
  `PassResult`，Pipeline 不得操作 Word 对象、不得解析 Markdown。
- **SPEC-ARCH-004**：Renderer SHALL only render AST/LayoutPlan。Renderer 不得
  解析 Markdown、不得调用外部 API、不得修改 AST、不得执行后处理。
- **SPEC-ARCH-005**：Post-Processor SHALL own cover page / TOC / table styling /
  font normalization / Word automation。Renderer 不得执行这些任务。
- **SPEC-ARCH-006**：Services（DiagramService、MermaidService 等）SHALL return
  data objects，SHALL NOT modify AST。
- **SPEC-ARCH-007**：依赖方向必须是单向的：
  Parser → AST → Pipeline → Renderer → PostProcessor → Services；
  禁止循环导入。
- **SPEC-ARCH-008**：Renderer SHALL use NodeVisitor 动态分发；AST 节点不得实现
  `accept()`。
- **SPEC-ARCH-009**：Renderer SHALL obtain formatting through StyleResolver；
  禁止硬编码样式；Themes 控制外观，Renderer 控制结构。
- **SPEC-ARCH-010**：布局决策由 DecisionEngine 输出 `LayoutPlan`；Renderer 仅执行
  Plan。不得绕过 LayoutPlan 直接渲染。
- **SPEC-ARCH-011**：Word 字体设置 SHALL use `set_style_font()`（同时设置
  ascii / hAnsi / eastAsia / cs），禁止直接用 `style.font.name` 处理东亚文本。
- **SPEC-ARCH-012**：Parser 检测 diagram 块，DiagramPass 转换为图片，
  Renderer 只渲染图片；Renderer 不得生成 SVG。
- **SPEC-ARCH-013**：质量门属于编译流程的强制阶段，位于
  Render 前后与 Post-Processor 之后（见 §4）。

## 4. Quality Gate Contract（SPEC-QA）

### 4.1 编译流程（FROZEN）

```text
Markdown
  ↓
Parser → AST
  ↓
Pipeline → AST
  ↓
LayoutPlan (DecisionEngine)
  ↓
StaticQA ── FAIL ──→ QualityGateError（Build rejected）
  │
  └─ PASS / PASS_WITH_WARN
       ↓
     Render → save
       ↓
     RenderedQA ── PASS ──→ CONTINUE
       │
       ├─ PASS_WITH_WARN ── fail_on_warning? → ABORT
       │                      else → CONTINUE / 可修复则 REPAIR
       │
       └─ FAIL ── fail_on_error? ── repairable? → REPAIR（≤ max_repair_iterations）
                        │           └─ unrepairable → ABORT
                        └─ fail_on_error=false → 记录警告后 CONTINUE（非静默）
       ↓
     Post-Processor
       ↓
     FinalArtifactQA（检查对象 == 发布对象，记录 artifact sha256）
       ↓
     Acceptance Gate（AC001–AC018）
       ↓
     Release Evidence → Release Candidate
```

### 4.2 状态语义

- `PASS`：通过。
- `PASS_WITH_WARN`：存在 warning；默认放行，`fail_on_warning=true` 时 ABORT。
- `FAIL`：存在 error；`fail_on_error=true`（默认）时不得进入下一阶段。
- QA 基础设施自身抛异常时 **FAIL CLOSED**：必须转换为 `QualityGateError`，
  不得降级为 warning 后继续。

### 4.3 默认 Governance Policy（FROZEN）

```yaml
quality_gate:
  fail_on_error: true
  fail_on_warning: false
  max_repair_iterations: 2
```

对应 SPEC-ID：**SPEC-QA-001**（StaticQA FAIL → build rejected）、
**SPEC-QA-002**（RenderedQA FAIL 不得静默进入 Release Candidate）、
**SPEC-QA-003**（任何被 Repair 的 DOCX 至少再经过一次 RenderedQA）、
**SPEC-QA-004**（最终发布文件 sha256 必须等于 Final QA 检查文件的 sha256）、
**SPEC-QA-005**（RenderedQA SHALL 真实测量每个交付图形的尺寸与有效内容区的关系：
超出有效内容区 = error，按既有 `fail_on_error` 语义使 Gate FAIL；低于主题
`figure.min_width` = warning 并计数；测量结果 SHALL 来自已产出文档且确定）。

## 5. Invariants（SPEC-INV）

- **SPEC-INV-001**：Markdown 语义内容 SHALL NOT be silently lost。
  “No Content Loss” 是最高优先级 invariant。
- **SPEC-INV-002**：最终 DOCX SHALL satisfy configured readability minimums
  （body ≥ 10pt、table ≥ 8.5pt、figure/ascii/code ≥ 8pt、margin ≥ 0.5in）。
- **SPEC-INV-003**：同一输入 + 同一配置必须产生确定性输出。
- **SPEC-INV-004**：AST 节点不可变；任何转换返回新节点。
- **SPEC-INV-005**：编译流程不得绕过任一阶段（Parser → AST → Pipeline →
  Renderer → Post-Processor）。
- **SPEC-INV-006**：Fail loudly：可恢复问题必须生成 Diagnostic；
  错误必须抛出有意义异常，禁止静默吞掉异常。
- **SPEC-INV-007**：StaticQA FAIL 时不存在最终 DOCX Release artifact。
- **SPEC-INV-008**：RenderedQA FAIL 无法静默进入 Release Candidate。
- **SPEC-INV-009**：Repair 不允许修改 AST semantic content；只能调整
  LayoutPlan / formatting policy。
- **SPEC-INV-010**：没有 Release Evidence 的 build 不得标记为 RC。
- **SPEC-INV-011**：Golden baseline 更新不得由 DeepSeek Patch 自动完成；
  必须经过 investigate → ADR/Spec approval → approve baseline 流程。
- **SPEC-INV-012**：任何未列入 Change Plan 的模块不得被修改；发现额外问题
  只报告、不修改。
- **SPEC-INV-013**：Ambiguous whitespace-aligned input SHALL remain paragraph
  content；Simple Table Recognition 不得转换不满足全部条件的输入，且不得在识别决策中
  丢弃、重排或改写源文本。
- **SPEC-INV-014**：No delivered figure SHALL exceed the effective section content
  box；任何交付图形超出有效内容区的 build SHALL NOT 通过质量门。

## 6. Acceptance Criteria（SPEC-AC）

每个 Release Candidate 必须通过完整 Acceptance Corpus（AC001–AC018），
评价维度固定为：

| 维度 | 定义 | 对应检查 |
| --- | --- | --- |
| Semantic Fidelity | Markdown 语义在 DOCX 中保持 | 标题/列表/表格结构保留 |
| Structural Fidelity | 文档结构（标题层级、表格、分节）保持 | 结构签名比较 |
| Formatting Validity | 字体、字号、页边距满足冻结主题 | StaticQA / RenderedQA |
| No Content Loss | 源内容全部出现在最终 DOCX | token 覆盖率 == 1.0 |
| Deterministic Output | 同一输入两次编译结果一致 | 确定性抽查 |

- **SPEC-AC-001**：全部 Acceptance 用例通过。
- **SPEC-AC-002**：StaticQA = PASS；RenderedQA ≠ FAIL；FinalArtifactQA = PASS。
- **SPEC-AC-003**：Markdown 源文本 token 覆盖率 == 1.0（允许 Markdown 语法
  与展示性空白差异）。
- **SPEC-AC-004**：Unit / Integration / Golden / Acceptance 测试全部通过。
- **SPEC-AC-005**：Release Evidence 中 Spec Deviations == 0，
  且未经授权的 Spec Change == 0。

## 7. Non-Goals（SPEC-NON）

- **SPEC-NON-001**：本规范不定义业务模块的新功能（如脚注、交叉引用、PDF/HTML
  后端）；这些功能按“Adding New Syntax”流程另行立项。
- **SPEC-NON-002**：本治理体系到此为止，**不继续增加治理层级**（不再新增
  Reviewer、审批层、Agent 编排层），避免治理成本超过收益。
- **SPEC-NON-003**：不追求无限修复；`max_repair_iterations` 必须有上界。
- **SPEC-NON-004**：不以“主观评价”替代证据；Release Decision 必须由规则生成。

## 8. Feature Status

| 状态 | 条目 |
| --- | --- |
| FROZEN（已实现） | §2.1 全部功能 |
| PLANNED（未实现） | §2.2 全部条目 |
| FROZEN（治理） | Canonical Spec 1.1、Change Classification、Traceable Implementation Plan、Quality Gates、Acceptance Corpus、Release Evidence |

## 9. Referenced ADR

- ADR-001：不可变 AST
- ADR-002：无 `accept()` 模式（NodeVisitor 动态分发）
- ADR-003：Pass 返回 PassResult
- ADR-004：RenderContext 与 CompilerContext 分离
- ADR-005：Service 层解耦
- ADR-006：统一字体设置（set_style_font）
- ADR-007：后处理器分离
- ADR-008：规则引擎驱动的 ASCII → Mermaid 转换
- ADR-009：QS-Word-Default-V1.5 默认主题（中英混排）

## 10. 治理规则速查

1. **Authority**：本文件唯一权威；冲突时本文件优先。
2. **变更控制**：任何 FROZEN 修改必须 ADR → Spec Update → Re-freeze。
3. **分类 Gate**：ChatGPT/Reviewer 输出必须按 REVIEW_TEMPLATE 分类
   （DEFECT / TEST_DEFECT / SPEC_GAP / ARCH_CHANGE / OPTIONAL_IMPROVEMENT）。
4. **实施追踪**：每个 Implementation Item 必须引用 SPEC-ID / ADR-ID，
   并声明 Allowed/Forbidden Scope。
5. **QA Gate**：StaticQA / RenderedQA / FinalArtifactQA 均为强制阶段，
   FAIL 不得静默通过。
6. **Release Evidence**：没有 RELEASE_EVIDENCE 的 build 不得标记为 RC。
