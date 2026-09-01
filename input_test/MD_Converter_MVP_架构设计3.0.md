---
title: MD Converter MVP 架构设计 3.0
date: 2026-08-06
tags: [Deepseek]
---

# MD Converter MVP 架构设计 3.0

## 项目概述

MD Converter 是一个生产级 Markdown → Word 文档编译器，采用真正的编译器架构
（Parser → AST → Pipeline → Renderer → Post-Processor）。

Phase 1 MVP 已实现的核心能力：

- 标题、段落、列表（有序/无序）、表格、代码块、引用块、水平分割线
- 行内样式：粗体、斜体、行内代码、链接、图片
- **ASCII 图 → Mermaid 自动转换**（规则引擎 + 多方案选择，见「ASCII → Mermaid 子系统」）
- Mermaid 渲染（mmdc / Playwright）、封面页、目录（TOC）自动生成
- 主题系统、样式解析器、诊断框架、Golden Test 回归
- 统一字体设置（Microsoft YaHei / DengXian，避免 MS Mincho 回退）
- 默认输入目录（`PROJECT_ROOT/input`）与批量编译

版本演进：

- **1.0**：基础编译器架构（Parser/AST/Pipeline/Renderer）
- **2.0**：封面页、TOC、表格样式、字体统一、诊断与 Golden Test
- **3.0**：ASCII → Mermaid 规则引擎（四种图表 + 内容盒/目录树智能转换）、
  多方案交互选择、批量编译、默认输入目录

---

## 整体架构

```
用户输入 (Markdown 文件，默认 PROJECT_ROOT/input)
    │
    ▼
┌──────────────────────────────────────┐
│  CLI (Click)                        │
│  - 单文件 / 目录批量编译             │
│  - --ascii-mode auto|interactive|preview │
│  - 初始化 CompilerContext            │
└──────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────┐
│  Parser Layer                       │
│  markdown-it-py + SyntaxTree        │
│  BuilderRegistry (NodeType → Builder)│
│  Immutable AST (带 SourceSpan)      │
└──────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────┐
│  Pipeline (插件化)                  │
│  PassRegistry                        │
│  ├── NormalizePass (合并文本)        │
│  ├── AsciiToMermaidPass (ASCII→Mermaid) │
│  └── DiagramPass (Mermaid→图片)      │
└──────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────┐
│  Renderer Layer                     │
│  WordRenderer (NodeVisitor)          │
│  WordWriter (原子操作 + set_style_font) │
└──────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────┐
│  Post-Processor                     │
│  - 封面页（标题/日期/标签）          │
│  - TOC 更新（Word COM，独立实例）    │
│  - 表格样式、字体统一                │
└──────────────────────────────────────┘
    │
    ▼
Word 文档 (.docx)
```

编译器各阶段职责严格分离：Parser 只建 AST，Pipeline 只做 AST 变换，
Renderer 只渲染，Post-Processor 只做文档后处理，Service 返回纯数据对象。

---

## 关键设计决策（ADR）

| ADR | 决策 | 理由 |
|-----|------|------|
| ADR-001 | 不可变 AST | 线程安全，支持缓存和增量编译 |
| ADR-002 | 无 `accept()` 模式 | `NodeVisitor` 动态分发，符合 Python 生态 |
| ADR-003 | Pass 返回 `PassResult` | 统一传递文档、诊断、生成文件 |
| ADR-004 | RenderContext 与 CompilerContext 分离 | 清晰区分全局配置与渲染状态 |
| ADR-005 | Service 返回数据对象 | 避免服务层与 AST 耦合 |
| ADR-006 | 统一字体设置（`set_style_font`） | 同时设置 ascii/hAnsi/eastAsia/cs |
| ADR-007 | 后处理器分离 | 封面/TOC/表格样式独立于 Renderer |
| ADR-008 | ASCII → Mermaid 规则引擎 | 基于字符特征自动识别并优选，复杂图可交互选择 |
| ADR-009 | 内容盒默认 flowchart with subgraph | 信息盒按 `：` 分节生成嵌套子图 |
| ADR-010 | 目录树转换为 flowchart | 文件夹/文件图标 + classDef 配色 |

---

## 目录结构与模块职责

```
md_converter/
├── __init__.py                  # 包入口
├── cli.py                       # Click CLI（默认 input 目录 + 批量编译）
├── compiler.py                  # CompilerContext 统一上下文
├── config.py                    # 配置加载 (YAML) + 默认配置
├── ast/
│   ├── nodes.py                 # 不可变 AST 节点
│   └── node_visitor.py          # NodeVisitor 基类
├── parser/
│   ├── markdown_parser.py       # markdown-it-py 解析
│   ├── builder_registry.py      # Builder 注册表
│   └── builders/                # Heading/Paragraph/List/Table/Code/Inline 等
├── pipeline/
│   ├── pipeline.py              # Pipeline 执行器
│   ├── pass_registry.py         # Pass 注册表
│   └── passes/
│       ├── normalize_pass.py    # 合并文本
│       ├── ascii_mermaid_pass.py# ASCII → Mermaid Diagram 节点
│       └── diagram_pass.py      # Mermaid → 图片
├── services/
│   ├── diagram_service.py       # ASCII → SVG 渲染
│   └── ascii_mermaid/           # ASCII → Mermaid 规则引擎
│       ├── analyzer.py          # 特征分析（方框/箭头/生命线/树）
│       ├── detector.py          # 类型自动检测（置信度打分）
│       ├── selector.py          # 方案选择（自动/交互）
│       ├── service.py           # 编排入口
│       └── converters/
│           ├── flowchart.py     # 流程图 + 内容盒 subgraph + 目录树
│           ├── sequence.py      # 时序图
│           ├── class_diagram.py # 类图
│           └── mindmap.py       # 思维导图
├── renderer/
│   ├── word_renderer.py         # NodeVisitor 渲染
│   ├── word_writer.py           # 原子操作 + set_style_font
│   ├── post_processor.py        # 封面/TOC/表格样式
│   └── themes/default.py        # 默认主题
├── diagnostics/                 # 诊断收集器
└── tests/
    ├── test_ascii_mermaid_service.py
    ├── test_ascii_mermaid_pass.py
    ├── test_golden.py
    └── golden/                  # 快照
```

---

## ASCII → Mermaid 子系统（MVP 3.0 核心）

### 转换流程

```
ASCII 图文本
  ↓
AsciiAnalyzer.analyze()
  ├── 显示宽度网格（中文/全角字符按 2 列展开）
  ├── 方框检测（容差匹配，支持内嵌示例图）
  ├── 箭头/生命线提取（过滤盒子内部与词内字符）
  └── 树结构提取（分支符 + 缩进）
  ↓
DiagramTypeDetector.detect()   # 置信度打分
  ├── flowchart 0.85~0.90（内容盒 / 目录树默认）
  ├── sequence（生命线 + 消息）
  ├── class（分节 + 可见性/方法签名）
  └── mindmap（纯缩进文本）
  ↓
多方案生成（每种类型一个可用方案）
  ↓
方案选择：auto（最高置信度）/ interactive（逐图确认）/ preview（输出全部方案）
  ↓
Diagram(diagram_type="mermaid", content=...)
  ↓
DiagramPass → 图片（mmdc / Playwright）
```

### 四种转换规则

**1. 内容盒 → flowchart with subgraph（默认，置信度 0.85）**

单个「标题 + 内容」方框：

- 以 `：`/`:` 结尾的基缩进行 → 嵌套 subgraph（如「输入以下内容」「输出」）
- 含冒号但不结尾的行 → 独立节点（如 `目标用户：A、B`）
- 子项以 `<br/>` 合并；节点/分节间 `~~~` 串联
- Markdown 示例内容自动语义分组：标题 / 段落 / ASCII图 / 表格

**2. 目录/层级树 → flowchart（置信度 0.90）**

- 文件夹 📁 / 文件 📄 / 可执行命令 🔧 图标
- `名称 # 注释 (~N行)` 解析为 `名称<br/>规模<br/>注释`
- `classDef` root/folder/file/emphasis 配色
- 兼容 `│   ├──` 与 `    ├──` 两种续行风格

**3. 时序图 / 类图（按特征识别）**

- 时序：生命线 + 消息箭头 → `sequenceDiagram`
- 类图：分节方框 + 可见性标记 / 方法签名 → `classDiagram`

**4. 思维导图（纯缩进文本）**

- 单根节点层级 → `mindmap`
- 标签特殊字符以实体转义（`#40;`/`#41;`/`#126;`/`#96;`）

### 语法安全

所有生成的 Mermaid 均经过真实解析器验证：

- 标签中的反引号转义为 `#96;`（三反引号会触发词法错误）
- `#` 在引号标签内为合法字面量
- mindmap 无引号标签，括号/波浪线使用字符实体
- 多根缩进文本（如代码块）不误转 mindmap

---

## 核心模块详解

### Parser

- 使用 `markdown-it-py` + `SyntaxTreeNode`，`BuilderRegistry` 按节点类型分发
- 代码块语言为 `ascii`/`diagram` 时创建 `Diagram` 节点
- 未标注语言但具备图结构的代码块由 `AsciiToMermaidPass` 自动识别

### Pipeline

Pass 注册顺序（优先级）：

1. `AsciiToMermaidPass`（50）：ASCII Diagram / 疑似图代码块 → Mermaid Diagram
2. `NormalizePass`（100）：合并相邻文本
3. `DiagramPass`（100）：Mermaid → 图片

### Renderer

- `WordRenderer` 基于 `NodeVisitor` 动态分发
- 样式经 `StyleResolver` 获取，`InlineState` 管理嵌套
- 所有中文字体通过 `set_style_font` 同时设置 ascii/hAnsi/eastAsia/cs

### Post-Processor

- 封面页（Frontmatter 的 title/date/tags），默认开启
- TOC 更新使用 Word COM：`DispatchEx` 独立实例，`finally` 释放句柄，
  避免文件锁与「无法打开文件」问题
- 表格边框/表头样式、TOC 条目字体统一

### 诊断

- 结构化诊断（code/severity/message/location/suggestion）
- ASCII 转换相关代码：ASCI001~ASCI007（转换成功、低置信度、多方案、预览等）

---

## 配置示例 (`config.yaml`)

```yaml
output_dir: output          # 输出目录
enable_cover: true          # 封面页（默认开启）
toc: true
theme: default

ascii_to_mermaid:
  enabled: true
  mode: auto                # auto | interactive | preview
  confidence_threshold: 0.30
  preview_dir: output/ascii_preview
```

## 命令行

```bash
# 默认编译 PROJECT_ROOT/input/ 下所有 .md（批量）
md-converter

# 指定单文件
md-converter doc.md --output ./build/result.docx

# ASCII 图交互式选择
md-converter doc.md --ascii-mode interactive

# 多方案预览
md-converter input/ --ascii-mode preview --ascii-preview-dir ./preview
```

输出文件名规则：标题中的空格与非法字符替换为 `_`。

---

## 测试策略

- 单元测试：检测器、四种转换器、多方案选择（32 项）
- Pass 集成测试：AST 转换、交互模式、预览模式
- Golden Test：Markdown → DOCX 快照回归（忽略易变时间戳）
- Mermaid 语法验证：Playwright + 本地 mermaid 解析器全量校验

---

## 扩展指南

### 添加新的 ASCII 转换规则

1. 在 `analyzer.py` 提取结构特征
2. 在 `detector.py` 增加置信度打分
3. 在 `converters/` 实现转换器并注册到 `AsciiToMermaidService`
4. 补充测试

### 添加新的 Pass

1. 继承 `TransformPass`，返回 `PassResult`
2. 在 `PassRegistry` / `CompilerContext.create()` 注册
3. 编写测试

---

## 总结

MD Converter MVP 3.0 在编译器架构之上，以规则引擎实现 ASCII 图到 Mermaid 的
自动化转换：简单流程图/内容盒/目录树全自动，复杂图可交互选择与多方案预览；
默认输入目录与批量编译提升日常使用效率。所有生成结果经真实 Mermaid 解析器
验证，测试与快照回归保障确定性输出。
