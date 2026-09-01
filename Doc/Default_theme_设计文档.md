# `QS-Word-Default-V1.5`

## 冻结版设计文档（适合中英文的默认Word文档编辑风格 -- default theme)

### Universal CJK + Latin Document Compiler Theme

---

**文档状态**：✅ **已冻结 (Frozen)**

**生效日期**：2026-08-08

**适用范围**：Markdown → DOCX Converter 默认 Word 主题

**版本演进**：V1.0 → V1.1 → V1.2 → V1.3 → V1.4 → **V1.5（冻结版）**

---

## 一、文档目的与范围

本文档是 **QS-Word-Default-V1.5** 的完整设计规范，适用于 `md_converter` 项目中 `renderer/layout/` 模块的实现。

V1.5 是当前 V1.4 的架构升级版。它修正了 V1.4 中“预渲染决策无法获知 Word 真实布局”的架构缺陷，引入了 **Estimate → Render → Inspect → Repair** 闭环模型，并新增 **`LayoutPlan`** 作为决策与渲染的解耦边界。

**本文档冻结后，后续所有变更需通过正式 RFC 流程，不得随意增删 YAML 参数或修改决策优先级。**

---

## 二、版本演进总览

| 版本 | 定位 | 核心贡献 | 状态 |
| :--- | :--- | :--- | :--- |
| V1.0 | Basic Style | 基础字体/标题/表格/代码样式 | 已归档 |
| V1.1 | CJK/Latin Enhancement | 中英文混排视觉优化 | 已归档（部分规则已废弃） |
| V1.2 | Engineering Specification | 四层分离（Run/段落/节/文档） | 已归档 |
| V1.3 | Layout Policy | 定义“内容装不下怎么办” | 已归档 |
| V1.4 | Layout Decision Engine | 定义“多个排版方案冲突时选哪个” | 已归档 |
| **V1.5** | **Document Compiler Architecture** | **Estimate→Render→Inspect→Repair 闭环** | **✅ 已冻结** |

---

## 三、核心设计哲学（不可变原则）

V1.5 遵循以下 **8 条不可变原则**，任何后续变更不得违反：

```
┌─────────────────────────────────────────────────────────────────────┐
│                    QS-Word-Default-V1.5 核心原则                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. 语义优先（Semantic First）                                      │
│     Markdown 标题层级、列表嵌套、表格结构、代码语义、URL 完整性     │
│     在任何情况下都不可牺牲。                                        │
│                                                                     │
│  2. 可读性不可妥协（Readability Not Negotiable）                   │
│     正文最小 10pt，表格最小 8.5pt。字体缩小是最后手段，不是常规策略。│
│                                                                     │
│  3. 决策与渲染分离（Decision != Rendering）                        │
│     LayoutDecisionEngine 输出 LayoutPlan，Renderer 仅执行 Plan。   │
│                                                                     │
│  4. 闭环反馈（Closed Loop）                                        │
│     Render → Inspect → Repair → Re-render 是标准流程。             │
│                                                                     │
│  5. 内容类型特化（Type-Specific Policies）                         │
│     Heading / Paragraph / Table / Figure / Code / ASCII            │
│     各有独立的分页与溢出策略。                                     │
│                                                                     │
│  6. 用户意图优先（User Intent First）                              │
│     用户显式指定 > 主题默认，但必须经过 Validity Gate 过滤。       │
│                                                                     │
│  7. YAML 定义 WHAT，Python 决定 HOW                                │
│     YAML 只存储常量、偏好与开关，决策算法全部在 Python 实现。      │
│                                                                     │
│  8. 排版错误必须可见（Fail Visible）                                │
│     Layout QA 捕获的问题不得静默通过；必须生成报告或告警。          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 四、V1.5 完整架构

### 4.1 整体 Pipeline

```
                    Markdown
                       │
                       ▼
                      AST
                       │
                       ▼
              Semantic Analysis
                       │
                       ▼
              Content Analysis
                       │
                       ▼
              Layout Estimation
                       │
                       ▼
            Candidate Generation
                       │
                       ▼
             Constraint Filtering
                       │
                       ▼
          Decision / Priority Ranking
                       │
                       ▼
                   LayoutPlan
                       │
                       ▼
               Word Renderer
                       │
                       ▼
              Rendered DOCX
                       │
                       ▼
            Rendered Layout QA
                       │
                 ┌─────┴─────┐
                 │           │
               PASS        FAIL
                 │           │
                 │           ▼
                 │    Repair Strategy
                 │           │
                 │           ▼
                 │      Re-render
                 │           │
                 └─────┬─────┘
                       ▼
                 Final DOCX
                       │
                       ▼
              Conversion Report
```

### 4.2 模块职责

| 模块 | 职责 | 输入 | 输出 |
| :--- | :--- | :--- | :--- |
| **Semantic Analysis** | 提取语义结构（标题层级、列表嵌套、表格结构、引用关系） | AST | Semantic Model |
| **Content Analysis** | 分类内容类型（CJK/Latin 比例、代码行数、列数、内容密度） | AST + Semantic Model | Content Profile |
| **Layout Estimation** | 估算各 Block 所需空间（基于字体、字号、行距、列数） | Content Profile | Layout Estimate |
| **Candidate Generation** | 为每个 Block 生成多种布局候选方案 | Layout Estimate | Candidate List |
| **Constraint Filtering** | 剔除违反硬约束的候选方案 | Candidate List + Constraints | Filtered Candidates |
| **Decision / Priority** | 按优先级排序，选择最优方案 | Filtered Candidates | Layout Decision |
| **LayoutPlan** | 序列化的布局指令集 | Layout Decision | LayoutPlan |
| **Word Renderer** | 执行 LayoutPlan，生成 DOCX | LayoutPlan | Rendered DOCX |
| **Static QA** | 渲染前检查 AST/语义/配置完整性 | AST + Theme | Static QA Report |
| **Rendered QA** | 渲染后检查溢出/裁剪/ASCII 破损 | Rendered DOCX | Rendered QA Report |
| **Repair Strategy** | 根据 QA 结果调整 LayoutPlan | QA Report + LayoutPlan | Revised LayoutPlan |
| **PostProcessor** | 封面/TOC/页码等收尾处理 | Rendered DOCX | Final DOCX |

---

## 五、决策优先级体系（6 级）

### 5.1 优先级定义

| 优先级 | 名称 | 性质 | 约束类型 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| **P0** | User Explicit Intent | 最高 | 经 Validity Gate 后硬约束 | 用户显式指定（如 `<!-- landscape -->`） |
| **P1** | Semantic Integrity | 硬约束 | 绝对不可牺牲 | 标题层级、编号、列表、表格结构、代码语义 |
| **P2** | Readability | 硬约束 | 不可妥协 | 最小字号、行距、英文单词完整性 |
| **P3** | Structural Integrity | 硬约束 | 尽可能保持 | Heading Keep with next、Table Header 重复 |
| **P4** | Layout Efficiency | 软偏好 | 优化目标 | 页面利用率、最小化空白、合理分页数量 |
| **P5** | Visual Optimization | 软偏好 | 微调目标 | 列宽平衡、标题间距、图形位置 |

### 5.2 Validity Gate（P0 前置过滤器）

用户显式意图必须经过 Validity Gate 验证：

```yaml
validity_gate:
  invalid_intents:
    - body_font_size < 8pt
    - heading_font_size < 10pt
    - table_font_size < 6pt
    - margin < 0.5in
    - content_deletion
    - semantic_destruction

  invalid_response: ignore_and_warn
```

**示例**：
- 用户指定 `body_font: 9pt` → Validity Gate 拒绝，回退至 10.5pt，生成 Warning。
- 用户指定 `orientation: landscape` → 合法，P0 生效。

### 5.3 词典序决策（Lexicographic Priority）

```
Hard Constraints (P0-P1-P2-P3)
       ↓
Feasible Candidates
       ↓
Lexicographic Priority（P0 优先，再 P1，再 P2...）
       ↓
Score Optimization (P4-P5 仅在同分时使用)
```

**关键：P0-P1-P2-P3 的违规不能由 P4-P5 的高分抵消。**

---

## 六、内容类型分类器

所有 AST Node 首先完成内容类型分类：

```yaml
content_types:
  prose_cjk          # 中文主导正文（CJK 占比 > 55%）
  prose_latin        # 英文主导正文（Latin 占比 > 60%）
  prose_mixed        # 混合正文
  heading            # 标题
  list               # 列表
  quote              # 引用
  table_general      # 普通表格
  table_financial    # 金融数据表格（数字列较多）
  table_code         # 含代码的表格
  code_short         # 短代码块（≤ 25 行）
  code_long          # 长代码块（> 25 行）
  inline_code        # 行内代码
  ascii_diagram      # ASCII 图
  figure             # 图形（Mermaid/SVG）
  url                # URL
  formula            # 数学公式
  footnote           # 脚注
  metadata           # 元数据
```

**每个 Content Type 绑定一个 Layout Profile，其中定义了字体、对齐、行距、分页策略。**

---

## 七、LayoutPlan（中间表示）

**这是 V1.5 最重要的工程化产物。**

LayoutPlan 是 LayoutDecisionEngine 输出的唯一产物，Renderer 仅负责执行它。

### 7.1 数据结构

```python
@dataclass
class LayoutPlan:
    version: str = "1.5"
    sections: List[SectionPlan]
    blocks: List[BlockPlan]
    metadata: Dict[str, Any]

@dataclass
class SectionPlan:
    id: str
    orientation: Literal["portrait", "landscape"]
    page_size: Literal["A4", "Letter"]
    margins: Margins
    page_break_before: bool = False

@dataclass
class BlockPlan:
    id: str
    type: ContentType
    original_ast_id: str           # 指向原始 AST 节点
    page_break_before: bool = False
    keep_together: bool = False
    allow_split: bool = False
    font_override: Optional[FontSpec] = None
    width_override: Optional[Dimension] = None
    height_override: Optional[Dimension] = None
    alignment_override: Optional[str] = None
    repeat_header: bool = False    # 仅 Table
    max_lines_per_page: Optional[int] = None  # 仅 Code
```

### 7.2 LayoutPlan 序列化

LayoutPlan 应支持 JSON 序列化，用于调试、审计和测试回放：

```json
{
  "version": "1.5",
  "sections": [
    {"id": "sec_1", "orientation": "portrait", "page_size": "A4"},
    {"id": "sec_2", "orientation": "landscape", "page_size": "A4"},
    {"id": "sec_3", "orientation": "portrait", "page_size": "A4"}
  ],
  "blocks": [
    {"id": "blk_001", "type": "heading", "original_ast_id": "h1_001", "keep_together": true},
    {"id": "blk_002", "type": "table_financial", "original_ast_id": "tbl_001", "allow_split": true, "repeat_header": true},
    {"id": "blk_003", "type": "code_long", "original_ast_id": "code_001", "allow_split": true, "max_lines_per_page": 45}
  ]
}
```

---

## 八、按内容类型的分页策略

V1.5 废弃单一 Pagination State Machine，采用以下分策略体系：

### 8.1 策略总览

| Content Type | Keep Together | Allow Split | Keep with Next | 特殊规则 |
| :--- | :---: | :---: | :---: | :--- |
| **Heading** | ✅ | ❌ | ✅ | 标题与下一段同页 |
| **Paragraph** | ❌ | ✅ | ❌ | 启用 Widow/Orphan 控制 |
| **List** | ❌ | ✅ | ❌ | 保持列表项连续性 |
| **Table** | ❌ | ✅ | ❌ | 拆分时重复表头；保留列结构 |
| **Figure** | ✅ | ❌ | ❌ | 空间不足时移至下一页 |
| **Code Short (≤25行)** | ✅ | ❌ | ❌ | 整个块同页 |
| **Code Long (>25行)** | ❌ | ✅ | ❌ | 按行数拆分，每页最多 45 行 |
| **ASCII Diagram** | ✅ | ❌ | ❌ | 禁止拆分，否则几何结构破坏 |
| **URL** | ❌ | ✅ | ❌ | 允许在 `/` `.` `-` `_` 处断行 |

### 8.2 配置（YAML）

```yaml
pagination_policies:
  heading:
    keep_with_next: true
    keep_together: true

  paragraph:
    keep_together: false
    widow_orphan_control: true

  table:
    split_rows_across_pages: true
    repeat_header: true
    preserve_column_structure: true

  figure:
    keep_together: true
    move_to_next_page_if_insufficient: true

  code:
    keep_together_if_lines: <= 25
    allow_split_if_lines: > 25
    max_lines_per_page: 45

  ascii:
    keep_together: true
    no_wrap: true
```

---

## 九、表格布局规范

### 9.1 表格通用规范

```yaml
table:
  style: Table Grid
  font_size: 9.5pt
  vertical_alignment: top
  header:
    bold: true
    repeat: true
  width:
    mode: fit_content_width
  constraints:
    min_width: 1.2cm
    max_width: content_width
  overflow:
    long_text: wrap
    url: break
    code: shrink_or_break
```

### 9.2 列对齐（按数据类型）

| 数据类型 | 水平对齐 | 示例 |
| :--- | :--- | :--- |
| Text | Left | "Description" |
| Number | Right | "1,250.5" |
| Percentage | Right | "35.6%" |
| Currency | Right | "$12.8B" |
| Date | Center | "2026-08-08" |
| Boolean | Center | "✅ / ❌" |
| Code | Left | "`import sys`" |
| URL | Left | "https://example.com" |

### 9.3 表格横置（Landscape）

当表格宽度超过 Portrait 可用宽度（且缩小字号至 8.5pt 仍无法解决）时：

```yaml
section:
  landscape_trigger:
    table_width_exceeds_content_width: true
    width_margin_buffer: 1cm

  landscape_scope: local          # 仅当前表格所在 Section
  restore_previous_orientation: true
```

### 9.4 表格跨页拆分（合法行为）

**明确：表格拆分行跨页是合法行为，不破坏语义。**

```yaml
table_pagination:
  split_rows_across_pages: true
  repeat_header: true
  preserve_column_structure: true
  preserve_table_identity: true
```

---

## 十、字体体系

### 10.1 字体映射

| 元素 | 东亚字符（CJK） | 拉丁字符（Latin） | 数字 | 符号 | 字号 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **正文** | DengXian | Calibri | Calibri | fallback | **10.5 pt** |
| **H1** | Microsoft YaHei | Arial | Arial | fallback | **20 pt** |
| **H2** | Microsoft YaHei | Arial | Arial | fallback | **16 pt** |
| **H3** | Microsoft YaHei | Arial | Arial | fallback | **14 pt** |
| **H4** | Microsoft YaHei | Arial | Arial | fallback | **14 pt BoldItalic** |
| **表格** | DengXian | Calibri | Calibri | fallback | **9.5 pt** |
| **代码** | — | Consolas | Consolas | — | **10 pt** |
| **ASCII 图** | — | Consolas | Consolas | — | **8.5 pt** |

### 10.2 字体映射规则（Word XML）

```yaml
font_mapping:
  ascii:      # 拉丁字母
    body: Calibri
    heading: Arial
  eastAsia:   # CJK 字符
    body: DengXian
    heading: Microsoft YaHei
  hAnsi:      # 西文扩展
    body: Calibri
    heading: Arial
  cs:         # 复杂脚本
    body: Arial
    heading: Arial
```

**原则：Converter 指定主要字体；Word 负责最终 fallback。**

### 10.3 Run 分割逻辑

```yaml
run_segmentation:
  split_on:
    formatting:
      - bold
      - italic
      - underline
      - strike
      - color
      - highlight
    semantic:
      - hyperlink
      - inline_code
      - footnote
      - citation
    typography:
      - east_asia_font
      - latin_font
      - complex_script_font

  atomic_sequences:
    - word
    - number
    - decimal
    - percentage
    - currency
    - unit
    - identifier
    - url
    - email

  preserve_markdown_spaces: true
```

**关键：`35.6%` 保持为单个原子序列，不拆分为 5 个独立 Run。**

---

## 十一、正文段落规范

### 11.1 段落参数

```yaml
paragraph:
  line_spacing:
    type: multiple
    value: 1.15
  spacing:
    before: 0pt
    after: 6pt
  cjk_latin_spacing:
    auto: true
    preserve_markdown_spaces: true
```

### 11.2 段落对齐（语言自适应）

```yaml
paragraph_alignment:
  detection:
    cjk_ratio_threshold: 0.55
    latin_ratio_threshold: 0.60

  rules:
    - cjk_ratio > 0.55:
        alignment: justified
    - latin_ratio > 0.60:
        alignment: left
    - mixed:
        alignment: justified
    - code_heavy:
        alignment: left
    - url_heavy:
        alignment: left
    - table_cell:
        alignment: left
    - explicit_line_breaks (标签/元数据/公式行):
        alignment: left
```

### 11.3 中文标点

```yaml
east_asian_layout:
  kinsoku: true              # 禁止行首出现 。，、！？）」
  hanging_punctuation: true  # 标点悬挂边界
  auto_space_cjk_latin: true
  auto_space_cjk_digits: true
```

---

## 十二、标题规范

### 12.1 字号与间距

```yaml
heading:
  H1:
    size: 20pt
    bold: true
    before: 12pt
    after: 6pt
  H2:
    size: 16pt
    bold: true
    before: 12pt
    after: 6pt
  H3:
    size: 14pt
    bold: true
    before: 12pt
    after: 6pt
  H4:
    size: 14pt
    bold: true
    italic: true
    before: 12pt
    after: 6pt

  keep_with_next: true
  keep_together: true
```

### 12.2 编号体系（关键约束）

**Markdown 原始编号必须保留，禁用 Word 自动重编号。**

```yaml
source_semantics:
  preserve_source_numbering: true
  never_auto_renumber_heading: true
```

**示例**：
- Markdown `## 第四层：风险过滤` → Word 中显示 `第四层：风险过滤`
- **不能**自动变成 `4. 第四层：风险过滤`

---

## 十三、代码块规范

### 13.1 代码块参数

```yaml
code:
  font: Consolas
  size: 10pt
  line_spacing: 1.0
  alignment: left
  no_auto_hyphenation: true
  keep_together_if_lines: <= 25
  allow_split_if_lines: > 25
  max_lines_per_page: 45
```

### 13.2 长代码块分页

```
Code Block > 25 lines
        ↓
第 1 页显示 45 行
        ↓
换页，继续显示剩余行
        ↓
无额外语言标记（保持纯代码块结构）
```

---

## 十四、ASCII 图规范

```yaml
ascii:
  font: Consolas
  size: 8.5pt
  alignment: center
  no_wrap: true
  keep_lines_together: true
  keep_with_next: false
  integrity_check: true
  min_line_length_check: true
  broken_box_detection: true
```

**关键：ASCII 图必须在整图保持在同一页，且禁止自动换行，否则几何结构破坏。**

---

## 十五、图形（Figure）规范

```yaml
figure:
  alignment: center
  max_width: content_width
  max_height: available_page_height
  preserve_aspect_ratio: true
  min_width: 8cm
  min_height: auto
  keep_together: true
  overflow_handling:
    - move_to_next_page
    - scale_down
    - warn
  format: svg_to_drawingml     # 保留矢量，不转 PNG
```

**废弃 V1.3 的固定 `max_height: 8.5in`，改为动态计算 `available_page_height`。**

---

## 十六、URL / 长英文断行策略

```yaml
url_and_long_words:
  url:
    allow_break: true
    break_points: ["/", ".", "-", "_", "?", "&", "="]
  technical_identifier:
    allow_break: false
  normal_english:
    allow_break: false
  long_word_threshold: 20
```

---

## 十七、可读性保护（最小字号约束）

```yaml
readability:
  minimum:
    body_font: 10pt
    table_font: 8.5pt
    figure_text: 8pt
    ascii_font: 8pt
    code_font: 8pt
    margin: 0.5in

  overflow_response:
    - reflow
    - split
    - landscape
    - new_page
    - warn_if_all_fail
```

**绝对禁止：为了塞进内容将正文缩小至 10pt 以下。**

---

## 十八、Layout QA（质量保证）

### 18.1 Static QA（渲染前）

```yaml
layout_qa:
  static:
    enabled: true
    checks:
      - ast_integrity
      - semantic_integrity
      - table_structure
      - url_integrity
      - font_configuration
      - style_configuration
      - section_configuration
```

### 18.2 Rendered QA（渲染后）

```yaml
  rendered:
    enabled: true
    checks:
      - page_overflow
      - orphan_heading
      - empty_page
      - table_clipping
      - figure_clipping
      - ascii_corruption
      - bad_page_break
      - font_substitution
      - section_break_anomaly
```

### 18.3 质量门（Quality Gate）

```yaml
  quality_gate:
    fatal:
      - semantic_loss
      - content_loss
    error:
      - overflow
      - clipping
      - broken_table
      - broken_figure
    warning:
      - unusual_page_break
      - excessive_whitespace
```

### 18.4 QA 输出

```json
{
  "status": "PASS_WITH_WARNING",
  "errors": 0,
  "warnings": 2,
  "metrics": {
    "overflow": 0,
    "empty_pages": 0,
    "orphan_headings": 0,
    "table_overflow": 0,
    "figure_overflow": 0,
    "font_violations": 0
  },
  "warnings_list": [
    "Table 3: Landscape section triggered (table width: 18.2cm, available: 15.5cm)",
    "Figure 2: Moved to next page due to insufficient space"
  ]
}
```

---

## 十九、文档结构

### 19.1 四段式标准化结构

```yaml
document_structure:
  sections:
    - cover
    - toc
    - body
    - appendix

  cover:
    font: Microsoft YaHei
    title_size: 28pt
    date_size: 16pt
    author_size: 14pt

  toc:
    font: Microsoft YaHei
    levels: 3
    title_size: 18pt
    level_1_size: 14pt
    level_2_size: 12pt
    level_3_size: 11pt
```

### 19.2 封面模板

```
                    文档标题

                    日期

                  作者 / 来源
```

---

## 二十、V1.5 完整 YAML 配置

```yaml
theme:
  name: QS-Word-Default-V1.5
  version: 1.5
  status: frozen

# ============================================================
# 页面
# ============================================================
page:
  size: A4
  margins:
    top: 1in
    bottom: 1in
    left: 1in
    right: 1in

# ============================================================
# 字体体系
# ============================================================
font_mapping:
  ascii:
    body: Calibri
    heading: Arial
  eastAsia:
    body: DengXian
    heading: Microsoft YaHei
  hAnsi:
    body: Calibri
    heading: Arial
  cs:
    body: Arial
    heading: Arial

number_font: Calibri
symbol_font: inherit_or_symbol_fallback

# ============================================================
# 字号
# ============================================================
typography:
  body:
    size: 10.5pt
  heading:
    H1:
      size: 20pt
      bold: true
      before: 12pt
      after: 6pt
    H2:
      size: 16pt
      bold: true
      before: 12pt
      after: 6pt
    H3:
      size: 14pt
      bold: true
      before: 12pt
      after: 6pt
    H4:
      size: 14pt
      bold: true
      italic: true
      before: 12pt
      after: 6pt
  code:
    font: Consolas
    size: 10pt
  ascii:
    font: Consolas
    size: 8.5pt

# ============================================================
# 段落
# ============================================================
paragraph:
  line_spacing:
    type: multiple
    value: 1.15
  spacing:
    before: 0pt
    after: 6pt
  alignment:
    mode: adaptive
    cjk_dominant: justified
    latin_dominant: left
    mixed: justified
    code_heavy: left
    url_heavy: left
    table_cell: left
  cjk_latin_spacing:
    auto: true
    preserve_markdown_spaces: true

# ============================================================
# Run 分割
# ============================================================
run_segmentation:
  split_on:
    formatting:
      - bold
      - italic
      - underline
      - strike
      - color
      - highlight
    semantic:
      - hyperlink
      - inline_code
      - footnote
      - citation
    typography:
      - east_asia_font
      - latin_font
      - complex_script_font
  atomic_sequences:
    - word
    - number
    - decimal
    - percentage
    - currency
    - unit
    - identifier
    - url
    - email
  preserve_markdown_spaces: true

# ============================================================
# 语言检测
# ============================================================
language_detection:
  weights:
    cjk: 1.0
    latin_word: 1.0
    number: 0.25
    punctuation: 0
    whitespace: 0
    symbol: 0
  thresholds:
    cjk_dominant: 0.55
    latin_dominant: 0.60

# ============================================================
# 标题
# ============================================================
heading:
  keep_with_next: true
  keep_together: true
  preserve_source_numbering: true

# ============================================================
# 表格
# ============================================================
table:
  style: Table Grid
  font_size: 9.5pt
  vertical_alignment: top
  header:
    bold: true
    repeat: true
  width:
    mode: fit_content_width
  constraints:
    min_width: 1.2cm
    max_width: content_width
  overflow:
    long_text: wrap
    url: break
    code: shrink_or_break
  split_rows_across_pages: true
  preserve_column_structure: true
  landscape_candidate: true

# ============================================================
# 图形
# ============================================================
figure:
  alignment: center
  max_width: content_width
  max_height: available_page_height
  preserve_aspect_ratio: true
  min_width: 8cm
  min_height: auto
  keep_together: true
  overflow_handling:
    - move_to_next_page
    - scale_down
    - warn
  format: svg_to_drawingml

# ============================================================
# 代码块
# ============================================================
code:
  font: Consolas
  size: 10pt
  line_spacing: 1.0
  alignment: left
  no_auto_hyphenation: true
  keep_together_if_lines: 25
  allow_split_if_lines: 25
  max_lines_per_page: 45

# ============================================================
# ASCII 图
# ============================================================
ascii:
  font: Consolas
  size: 8.5pt
  alignment: center
  no_wrap: true
  keep_lines_together: true
  keep_with_next: false
  integrity_check: true

# ============================================================
# URL / 长英文
# ============================================================
url_and_long_words:
  url:
    allow_break: true
    break_points: ["/", ".", "-", "_", "?", "&", "="]
  technical_identifier:
    allow_break: false
  normal_english:
    allow_break: false
  long_word_threshold: 20

# ============================================================
# Section / 分页
# ============================================================
section:
  default_orientation: portrait
  landscape_trigger:
    table_width_exceeds_content_width: true
    width_margin_buffer: 1cm
  landscape_scope: local
  restore_previous_orientation: true

pagination_policies:
  heading:
    keep_with_next: true
    keep_together: true
  paragraph:
    keep_together: false
    widow_orphan_control: true
  table:
    split_rows_across_pages: true
    repeat_header: true
  figure:
    keep_together: true
  code:
    keep_together_if_lines: 25
    allow_split_if_lines: 25
  ascii:
    keep_together: true
    no_wrap: true

# ============================================================
# 可读性保护
# ============================================================
readability:
  minimum:
    body_font: 10pt
    table_font: 8.5pt
    figure_text: 8pt
    ascii_font: 8pt
    code_font: 8pt
    margin: 0.5in
  overflow_response:
    - reflow
    - split
    - landscape
    - new_page
    - warn_if_all_fail

# ============================================================
# Layout QA
# ============================================================
layout_qa:
  static:
    enabled: true
  rendered:
    enabled: true
  quality_gate:
    fatal:
      - semantic_loss
      - content_loss
    error:
      - overflow
      - clipping
      - broken_table
      - broken_figure
    warning:
      - unusual_page_break
      - excessive_whitespace
  fail_on_error: true
  fail_on_warning: false
  output: conversion_report.json

# ============================================================
# 文档结构
# ============================================================
document_structure:
  sections:
    - cover
    - toc
    - body
    - appendix
  cover:
    font: Microsoft YaHei
    title_size: 28pt
    date_size: 16pt
    author_size: 14pt
  toc:
    font: Microsoft YaHei
    levels: 3
    title_size: 18pt
    level_1_size: 14pt
    level_2_size: 12pt
    level_3_size: 11pt
```

---

## 二十一、V1.4 → V1.5 变更摘要

| 变更项 | V1.4 | V1.5 |
| :--- | :--- | :--- |
| 架构模式 | 一次性决策 → 渲染 | **Estimate → Render → Inspect → Repair（闭环）** |
| 中间表示 | 无 | **LayoutPlan（决策与渲染分离）** |
| Layout QA | 单层 | **Static QA + Rendered QA（双层）** |
| 分页策略 | 全局状态机 | **按内容类型分策略（8 种独立策略）** |
| 表格拆分 | P0 违规（非法） | **合法行为（拆分行 + 重复表头）** |
| 用户意图 | 未显式处理 | **P0 最高优先级 + Validity Gate** |
| 决策依据 | 预渲染估算 | **估算 + 渲染后真实反馈** |
| 优先级 | 4 级 | **6 级 + Validity Gate** |
| 字体缩小 | 未明确限制 | **最后手段 + 范围限制** |
| 质量门 | 检测器 | **PASS / PASS_WITH_WARN / FAIL** |

---

## 二十二、与现有 MD Converter 架构的映射

```text
md_converter/
├── ast/                            # 已有
├── pipeline/                       # 已有
├── renderer/
│   ├── word/
│   │   ├── renderer.py             # 已有（执行 LayoutPlan）
│   │   ├── writer.py               # 已有
│   │   ├── style_resolver.py       # 已有
│   │   ├── inline_state.py         # 已有
│   │   └── post_processor.py       # 已有
│   └── layout/                     # 【V1.5 新增】
│       ├── decision_engine.py      # 输出 LayoutPlan
│       ├── content_analyzer.py     # 内容类型分类
│       ├── layout_plan.py          # LayoutPlan 数据结构
│       ├── pagination.py           # 按内容类型分页策略
│       ├── section_manager.py      # Section 决策（Portrait/Landscape）
│       ├── repair_strategy.py      # Render → Inspect → Repair
│       ├── static_qa.py            # 渲染前 QA
│       ├── rendered_qa.py          # 渲染后 QA（基于 python-docx 解析）
│       └── validity_gate.py        # 用户意图过滤
└── themes/
    └── default_v1_5.yaml           # 【V1.5 已冻结】
```

---

## 二十三、冻结声明

### 23.1 冻结范围

以下内容已冻结，后续不得随意变更：

1. **8 条不可变原则**（第三章）
2. **6 级决策优先级体系**（第五章）
3. **LayoutPlan 数据结构**（第七章）
4. **按内容类型的分页策略**（第八章）
5. **YAML 配置结构**（第二十章）

### 23.2 变更流程

任何对冻结内容的变更需通过正式 RFC 流程：

```text
1. 提交 RFC 文档（说明变更动机、影响范围、回退方案）
2. 至少 2 名核心评审人批准
3. 更新冻结版本文档
4. 创建版本迁移指南（V1.5.x）
```

### 23.3 允许的变更（无需 RFC）

以下变更无需 RFC：

- Layout QA 的警告级别调整
- Golden Test Fixtures 增加
- 性能优化（不改变输出）
- 文档错误修正

---

## 二十四、版本对应关系

| 阶段 | 版本 | 状态 |
| :--- | :--- | :--- |
| 概念设计 | V1.0 - V1.4 | 已归档 |
| **架构冻结** | **V1.5** | **✅ 已冻结** |
| 实施契约 | Implementation Contract | 即将编写 |
| 实现 | Python `layout/` 模块 | 待开发 |
| 测试 | Golden Tests + QA Fixtures | 待建立 |

---

## 二十五、签署信息

| 角色 | 签署人 | 日期 |
| :--- | :--- | :--- |
| 架构负责人 | QS 财富方舟 AI 投资委员会 | 2026-08-08 |
| 技术评审人 | DeepSeek (AI) | 2026-08-08 |
| 文档管理者 | MD Converter 项目组 | 2026-08-08 |

---

**V1.5 冻结。后续所有实现必须严格遵循此规范。**
