"""单元测试：ASCII → Mermaid 服务（检测、转换、多方案选择）。"""

# ruff: noqa: E501  # ASCII 示例行可能超过行长限制

import re
import unicodedata
from pathlib import Path

import pytest

from md_converter.services.ascii_mermaid import (
    AsciiToMermaidService,
    interactive_select,
)

FLOWCHART_ASCII = """+--------+     +--------+
| Start  | --> |  Done  |
+--------+     +--------+
    |
    v
+--------+
|  End   |
+--------+
"""

SEQUENCE_ASCII = """+------+          +------+
| User |          | API  |
+------+          +------+
   |                 |
   |--- login() ---->|
   |                 |
   |<-- token -------|
"""

BOX_FLOW_ASCII = """┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                    CLI (薄层)                                      │
│                        result = compile() → exit code                            │
└──────────────────────────────────┬──────────────────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────────────────────┐
│                           CompilationSession (全局配置)                           │
│  └── options, diagnostics, services, cache                                        │
└──────────────────────────────────┬──────────────────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────────────────────┐
│                          Parser Layer                                              │
│  MarkdownParser → Dispatcher → Builders → AST                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                            │
│  │ HeadingBuilder│  │ TableBuilder │  │ ListBuilder  │                            │
│  └──────────────┘  └──────────────┘  └──────────────┘                            │
└──────────────────────────────────┬──────────────────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────────────────────┐
│                         AST (Immutable)                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │  Block: Document │ Heading │ Paragraph │ List │ Table │ Code │ Diagram     │  │
│  │  Inline: Text │ Strong │ Emphasis │ Link │ Code │ Image                     │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────┬──────────────────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────────────────────┐
│                        Visitor (type(node)缓存)                                   │
│  visitor.visit(node) → _cache[type(node)] → visit_xxx                            │
└──────────────────────────────────┬──────────────────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────────────────────┐
│                         Services Layer                                            │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                              │
│  │ DiagramService│ │ReferenceService│ │   TOCService │                              │
│  └──────────────┘ └──────────────┘ └──────────────┘                              │
│  DiagramService → RenderedDiagram (不返回AST)                                    │
└──────────────────────────────────┬──────────────────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────────────────────┐
│                              Pipeline (Passes)                                    │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                              │
│  │  DiagramPass │ │ReferencePass │ │  StylePass   │                              │
│  └──────────────┘ └──────────────┘ └──────────────┘                              │
│  TransformPass.run(document, session) → PassResult                               │
└──────────────────────────────────┬──────────────────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────────────────────┐
│                         Renderer Layer                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │  WordRenderer (Visitor) → RenderContext → WordWriter (无状态)              │  │
│  │                              ├── heading_counter                            │  │
"""

CLASS_ASCII = """+----------------+
|    Person      |
+----------------+
| - name: str    |
| - age: int     |
+----------------+
| + getName()    |
+----------------+
       |
       |--|>
+----------------+
|    Student     |
+----------------+
| + study()      |
+----------------+
"""

MINDMAP_ASCII = """Root
├── Child 1
│   ├── Grand 1.1
│   └── Grand 1.2
└── Child 2
"""

VERTICAL_FLOW = """        ┌──────────┐
        │  Start   │
        └────┬─────┘
             │
             ▼
        ┌──────────┐
        │  Input   │
        └────┬─────┘
             │
             ▼
        ┌──────────┐
        │  Output  │
        └──────────┘
"""


def _char_width(ch: str) -> int:
    """按东亚宽度计算显示列数。"""
    return 2 if unicodedata.east_asian_width(ch) in ("F", "W") else 1


def _make_box(title: str, content_lines, width: int = 40) -> str:
    """构造显示宽度对齐的内容盒（模拟真实文档中的盒子）。"""

    def pad(text: str) -> str:
        used = sum(_char_width(c) for c in text)
        return text + " " * max(0, width - used)

    rows = ["┌" + "─" * width + "┐"]
    rows.append("│" + pad(f"  {title}") + "│")
    rows.append("├" + "─" * width + "┤")
    for line in content_lines:
        rows.append("│" + pad(f"  {line}") + "│")
    rows.append("└" + "─" * width + "┘")
    return "\n".join(rows)


CJK_CONTENT_BOX = _make_box(
    "v2.0 - 产品化提升",
    [
        "🚀 新增：",
        "- 实时预览 (Live Preview)",
        "- VSCode插件",
        "👥 目标用户：技术团队、文档团队",
        "⏱️ 预计开发：4-6周",
    ],
)


def test_flowchart_detection_and_conversion() -> None:
    service = AsciiToMermaidService()
    plan = service.analyze(FLOWCHART_ASCII)

    assert plan.detected_type == "flowchart"
    assert plan.best is not None
    assert "flowchart TD" in plan.best.mermaid
    assert 'A["Start"]' in plan.best.mermaid
    assert "A --> B" in plan.best.mermaid
    assert "A --> C" in plan.best.mermaid


def test_sequence_detection_and_conversion() -> None:
    service = AsciiToMermaidService()
    plan = service.analyze(SEQUENCE_ASCII)

    assert plan.detected_type == "sequence"
    assert plan.best is not None
    assert "sequenceDiagram" in plan.best.mermaid
    assert "participant A as User" in plan.best.mermaid
    assert "participant B as API" in plan.best.mermaid
    assert "A-->B: login()" in plan.best.mermaid
    assert "token" in plan.best.mermaid


def test_box_flow_diagram_converts_to_flowchart() -> None:
    """纵向堆叠方框图应转换为 flowchart（而非破坏 Mermaid 语法的时序图）。"""
    service = AsciiToMermaidService()
    plan = service.analyze(BOX_FLOW_ASCII)
    assert all(s.diagram_type != "sequence" for s in plan.schemes)
    assert plan.best is not None
    assert plan.best.diagram_type == "flowchart"
    assert plan.best.mermaid.startswith("flowchart TD")
    assert "subgraph B1[" in plan.best.mermaid
    assert "B1 --> B2" in plan.best.mermaid


def test_label_sanitize_and_box_strip() -> None:
    """标签净化：压缩换行；框线字符仅从未加引号的标签（时序图）中移除。"""
    from md_converter.services.ascii_mermaid.converters.base import (
        escape_mermaid_label,
        sanitize_label,
        strip_box_drawing,
    )

    assert sanitize_label("A\n  B") == "A B"
    raw_box = "A\n" + "\u250c\u2500\u2500\u25bc\u2500\u2510" + " B"
    assert sanitize_label(strip_box_drawing(raw_box)) == "A B"
    # 带引号的流程图标签保留 │（如 "Block: Document │ Heading"）
    assert escape_mermaid_label("x\u2502y") == "x\u2502y"
    assert '"' not in escape_mermaid_label('say "hi"')


def test_class_detection_and_conversion() -> None:
    service = AsciiToMermaidService()
    plan = service.analyze(CLASS_ASCII)

    assert plan.detected_type == "class"
    assert plan.best is not None
    assert "classDiagram" in plan.best.mermaid
    assert "class Person {" in plan.best.mermaid
    assert "-str name" in plan.best.mermaid
    assert "+getName()" in plan.best.mermaid
    assert "Person --|> Student" in plan.best.mermaid


def test_tree_converts_to_flowchart() -> None:
    """树形结构（含分支符）转换为 flowchart。"""
    service = AsciiToMermaidService()
    plan = service.analyze(MINDMAP_ASCII)

    assert plan.detected_type == "flowchart"
    assert plan.best is not None
    assert plan.best.mermaid.startswith("flowchart")
    assert "Root" in plan.best.mermaid
    assert "Child 1" in plan.best.mermaid
    assert "Grand 1.1" in plan.best.mermaid
    assert "--> " in plan.best.mermaid


def test_cjk_content_box_converts_to_flowchart_subgraph() -> None:
    """中文内容盒（标题 + 分节内容）应识别为 flowchart with subgraph 且内容完整。"""
    service = AsciiToMermaidService()
    plan = service.analyze(CJK_CONTENT_BOX)

    assert plan.detected_type == "flowchart"
    assert plan.best is not None
    assert 'subgraph R["v2.0 - 产品化提升"]' in plan.best.mermaid
    assert "direction TB" in plan.best.mermaid
    assert "实时预览 (Live Preview)" in plan.best.mermaid
    assert "VSCode插件" in plan.best.mermaid
    assert "技术团队" in plan.best.mermaid
    assert "文档团队" in plan.best.mermaid
    assert "4-6周" in plan.best.mermaid
    assert "~~~" in plan.best.mermaid


def test_list_item_not_misdetected_as_class() -> None:
    """`- VSCode插件` 这类列表项不应触发类图识别。"""
    service = AsciiToMermaidService()
    plan = service.analyze(CJK_CONTENT_BOX)

    assert len(plan.features.class_boxes) == 0
    assert plan.detected_type != "class"


def test_vertical_flow_with_junction_bottom_no_overlink() -> None:
    """带 ┬ 底边的垂直流程图不应产生跨级边。"""
    service = AsciiToMermaidService()
    plan = service.analyze(VERTICAL_FLOW)

    assert plan.detected_type == "flowchart"
    assert plan.best is not None
    assert "A --> B" in plan.best.mermaid
    assert "B --> C" in plan.best.mermaid
    assert "A --> C" not in plan.best.mermaid


NESTED_CONTENT_BOX = _make_box(
    "验证通过标准",
    [
        "✅ 输入以下内容：",
        "```ascii",
        "┌──────────────┐",
        "│    前端      │",
        "└──────┬───────┘",
        "       │",
        "┌──────▼───────┐",
        "│    后端      │",
        "└──────────────┘",
        "```",
    ],
)


def test_nested_content_box_converts_to_flowchart_subgraph() -> None:
    """内容盒内嵌示例图时，使用最外层盒转 flowchart with subgraph。"""
    service = AsciiToMermaidService()
    plan = service.analyze(NESTED_CONTENT_BOX)

    assert plan.detected_type == "flowchart"
    assert plan.best is not None
    assert 'subgraph R["验证通过标准"]' in plan.best.mermaid
    assert "输入以下内容" in plan.best.mermaid
    assert "前端" in plan.best.mermaid
    assert "后端" in plan.best.mermaid


def test_file_tree_converts_to_styled_flowchart() -> None:
    """目录树转换为带文件夹/文件图标的 flowchart，并保留注释与规模。"""
    file_tree = """doc-compiler/
├── README.md               # 项目说明
├── src/
│   ├── core/
│   │   └── converter.py    # 核心转换器
│   └── cli.py              # 命令行
└── tests/
    └── test_converter.py   # 单元测试
"""
    service = AsciiToMermaidService()
    plan = service.analyze(file_tree)

    assert plan.detected_type == "flowchart"
    assert plan.best is not None
    mermaid = plan.best.mermaid
    assert "📁 doc-compiler/" in mermaid
    assert "📄 README.md" in mermaid
    assert "📄 converter.py" in mermaid
    assert "项目说明" in mermaid
    assert "classDef root" in mermaid
    assert "classDef folder" in mermaid
    assert "classDef file" in mermaid
    assert service.is_ascii_diagram(file_tree)


def test_section_subgraph_conversion_and_fence_skip() -> None:
    """内容盒按「：」分节生成嵌套 subgraph，并跳过 Markdown 围栏行。"""
    box = _make_box(
        "验证通过标准",
        [
            "✅ 输入以下内容：",
            "# 系统架构",
            "## 整体设计",
            "用户通过浏览器访问系统...",
            "```ascii",
            "┌──────────────┐",
            "│    前端      │",
            "└──────┬───────┘",
            "```",
            "✅ 输出：",
            "- 目录自动生成",
            "- 表格格式正确",
        ],
        width=48,
    )
    service = AsciiToMermaidService()
    plan = service.analyze(box)

    assert plan.detected_type == "flowchart"
    assert plan.best is not None
    mermaid = plan.best.mermaid
    assert 'subgraph S1["✅ 输入以下内容"]' in mermaid
    assert mermaid.count("subgraph ") == 4  # R + S1 + 内嵌 ASCII + S2
    assert '["✅ 输出"]' in mermaid
    assert "系统架构" in mermaid
    assert 'subgraph S1_ASCII["ASCII Diagram"]' in mermaid
    assert "前端" in mermaid
    assert "目录自动生成" in mermaid
    # 围栏行不应出现在节点标签里（已转为嵌套子图）
    assert "```" not in mermaid


def test_structured_flow_uses_subgraphs_with_colors() -> None:
    """「标题 + 条目」盒子流转换为分层 subgraph + classDef 配色。"""
    flow = """+---------------+
| CLI (Click)   |
| - 单文件       |
+-------+-------+
        |
        v
+---------------+
| Parser Layer  |
| markdown-it   |
+---------------+
        |
        v
+---------------+
| Renderer      |
| WordRenderer  |
+---------------+
"""
    service = AsciiToMermaidService()
    plan = service.analyze(flow)

    assert plan.detected_type == "flowchart"
    assert plan.best is not None
    mermaid = plan.best.mermaid
    assert 'subgraph B1["CLI (Click)"]' in mermaid
    assert 'subgraph B2["Parser Layer"]' in mermaid
    assert "classDef input" in mermaid
    assert "classDef cli" in mermaid
    assert "B1 --> B2" in mermaid


def test_tree_uses_subfolder_and_test_classes() -> None:
    """目录树深层目录用 subfolder，测试文件用 test 类。"""
    tree = """md_converter/
├── ast/
│   ├── nodes.py
├── tests/
│   ├── test_ascii_mermaid_service.py
│   └── golden/
"""
    service = AsciiToMermaidService()
    plan = service.analyze(tree)

    assert plan.detected_type == "flowchart"
    assert plan.best is not None
    mermaid = plan.best.mermaid
    assert "classDef subfolder" in mermaid
    assert "classDef test" in mermaid
    assert "class NODESPY,TEST_ASCII_MERMAID_SERVICEPY" not in mermaid
    assert "test" in mermaid


def test_text_flow_converts_to_flowchart() -> None:
    """「文本流程」ASCII（多根 + 垂直箭头 + 分支汇合）转换为 flowchart。"""
    text_flow = """ASCII 图文本
  \u2193
AsciiAnalyzer.analyze()
  \u251c\u2500\u2500 \u663e\u793a\u5bbd\u5ea6\u7f51\u683c
  \u2514\u2500\u2500 \u65b9\u6846\u68c0\u6d4b
  \u2193
DiagramTypeDetector.detect()
  \u2193
\u591a\u65b9\u6848\u751f\u6210\uff08\u6bcf\u79cd\u7c7b\u578b\u4e00\u4e2a\u53ef\u7528\u65b9\u6848\uff09
"""
    service = AsciiToMermaidService()
    plan = service.analyze(text_flow)

    assert plan.detected_type == "flowchart"
    assert plan.best is not None
    mermaid = plan.best.mermaid
    assert mermaid.startswith("flowchart TD")
    assert "A --> B" in mermaid
    assert "B --> C" in mermaid
    assert "B --> D" in mermaid
    assert "C --> E" in mermaid
    assert "D --> E" in mermaid


def test_landscape_layout_converts_to_subgraphs() -> None:
    """嵌套盒分层布局（对标产品全景）转换为根 subgraph + 类别子图。"""
    # C3：fixture 固化在测试目录内，Full Regression 不再依赖工作区 input/。
    source = Path(__file__).resolve().parent / "fixtures" / "converter2.md"
    if not source.exists():
        pytest.fail(
            "test fixture missing: md_converter/tests/fixtures/converter2.md "
            "(Required Regression fixture)"
        )
    content = source.read_text(encoding="utf-8")
    match = re.search(r"^```\n(.*?)\n```", content, re.S | re.M)
    if not match:
        pytest.fail("fixture corrupted: no fence found in converter2.md")

    plan = AsciiToMermaidService().analyze(match.group(1))

    assert plan.detected_type == "flowchart"
    assert plan.best is not None
    mermaid = plan.best.mermaid
    assert 'subgraph LANDSCAPE["对标产品全景"]' in mermaid
    assert "文档生成类" in mermaid
    assert "编译器类" in mermaid
    assert "Pandoc" in mermaid
    assert "LLVM" in mermaid
    assert "Roslyn Compiler" in mermaid
    assert "G1 --> G2" in mermaid
    assert "G3 --> G4" in mermaid
    assert "G4 --> G5" not in mermaid


PLATFORM_BOX = """┌─────────────────────────────────────────────────────────────┐
│                    Software Design Document                  │
├─────────────────────────────────────────────────────────────┤
│  ## System Architecture                                      │
│  ```ascii                                                    │
│  ┌──────────────┐    ┌──────────────┐                      │
│  │   Frontend   │───▶│   Backend    │                      │
│  └──────────────┘    └──────────────┘                      │
│  ```                                                         │
│  ## API Design                                               │
│  ```mermaid                                                  │
│  sequenceDiagram                                             │
│    Client->>API: Request                                     │
│    API->>DB: Query                                           │
│    DB-->>API: Result                                         │
│    API-->>Client: Response                                   │
│  ```                                                         │
├─────────────────────────────────────────────────────────────┤
│  ✅ Live Preview: 实时查看渲染效果                           │
│  ✅ Diagram Sync: 修改AST自动更新图表                       │
└─────────────────────────────────────────────────────────────┘
"""


def test_platform_box_nested_subgraphs() -> None:
    """标题分节 + 内嵌 ASCII/时序源码 → 嵌套子图。"""
    service = AsciiToMermaidService()
    plan = service.analyze(PLATFORM_BOX)

    assert plan.detected_type == "flowchart"
    assert plan.best is not None
    mermaid = plan.best.mermaid
    assert 'subgraph R["Software Design Document"]' in mermaid
    assert 'subgraph S1["## System Architecture"]' in mermaid
    assert 'subgraph S1_ASCII["ASCII Diagram"]' in mermaid
    assert 'S1_ASCII_A["Frontend"]' in mermaid
    assert 'S1_ASCII_B["Backend"]' in mermaid
    assert "S1_ASCII_A --> S1_ASCII_B" in mermaid
    assert 'subgraph S2["## API Design"]' in mermaid
    assert 'subgraph S2_SEQ["Sequence Diagram"]' in mermaid
    assert 'S2_SEQ_Client -->|"Request"| S2_SEQ_API' in mermaid
    assert 'S2_SEQ_DB -->|"Result"| S2_SEQ_API' in mermaid
    assert "✅ Live Preview" in mermaid


REQUIREMENTS_TEXT = """## 3.2 功能需求

### REQ-001: 用户登录
**优先级**: High
**验收标准**:
- 支持邮箱密码登录
- 支持Google OAuth
- 登录失败3次锁定账户

### REQ-002: 数据导出
**优先级**: Medium
**验收标准**:
- 支持CSV格式导出
- 支持JSON格式导出
"""


def test_markdown_text_not_converted() -> None:
    """普通 Markdown 文档文本（标题/列表/表格）不应转为 Mermaid。"""
    service = AsciiToMermaidService()
    plan = service.analyze(REQUIREMENTS_TEXT)

    assert not plan.schemes
    assert plan.detected_type == "unknown"
    assert not service.is_ascii_diagram(REQUIREMENTS_TEXT)


MULTI_ROOT_FRAGMENT = """**核心能力**：
- OpenAPI/Swagger集成
- 请求/响应示例自动生成

**产出**：
- API参考文档
- Postman Collection

## 二、知识管理领域

### 4. 企业知识库 (Knowledge Base)

**场景描述**：企业构建内部知识库。

**痛点**：
- 知识分散在多个系统
- 搜索效率低
"""


def test_markdown_label_list_not_converted() -> None:
    """「**字段**：+ 列表」等普通 Markdown 内容不应转为 Mermaid。"""
    service = AsciiToMermaidService()
    plan = service.analyze(MULTI_ROOT_FRAGMENT)

    assert not plan.schemes
    assert plan.detected_type == "unknown"
    assert not service.is_ascii_diagram(MULTI_ROOT_FRAGMENT)


def test_enterprise_knowledge_base_box_converts() -> None:
    """外层内容盒内嵌流程图（Enterprise Knowledge Base）应转换且内容完整。"""
    service = AsciiToMermaidService()
    plan = service.analyze(EKB_BOX)

    assert plan.detected_type == "flowchart"
    assert plan.best is not None
    mermaid = plan.best.mermaid
    assert "Enterprise Knowledge Base" in mermaid
    assert "Technology" in mermaid
    assert "API" in mermaid
    assert "Incident" in mermaid
    assert "Semantic Search" in mermaid
    assert service.is_ascii_diagram(EKB_BOX)


EKB_BOX = """┌─────────────────────────────────────────────────────────────┐
│                    Enterprise Knowledge Base                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │  Technology │    │  Best       │    │  Troubleshoot│   │
│  │  Docs       │◀───│  Practices  │───▶│  Guides     │   │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
│         │                  │                  │            │
│         ▼                  ▼                  ▼            │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │  API        │    │  Code       │    │  Incident   │    │
│  │  Reference  │    │  Examples   │    │  Reports    │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
│                                                             │
│  🔍 Semantic Search: "How to handle timeout?"              │
│  🕸️ Knowledge Graph: API → Error → Solution               │
│  🤖 AI Assistant: "What's the best practice for..."        │
└─────────────────────────────────────────────────────────────┘
"""


def test_inner_box_graph_converts_to_flowchart() -> None:
    """外层盒 + 内部盒子 + 箭头 + 特性文本 → 节点与边。"""
    service = AsciiToMermaidService()
    plan = service.analyze(EKB_BOX)

    assert plan.detected_type == "flowchart"
    assert plan.best is not None
    mermaid = plan.best.mermaid
    assert 'subgraph R["Enterprise Knowledge Base"]' in mermaid
    assert "Technology<br/>Docs" in mermaid
    assert "Best<br/>Practices" in mermaid
    assert "API<br/>Reference" in mermaid
    assert "Semantic Search" in mermaid
    assert "Knowledge Graph" in mermaid
    assert "B --> C" in mermaid
    assert "A --> D" in mermaid
    assert "C --> F" in mermaid


def test_multi_scheme_generation_and_ranking() -> None:
    service = AsciiToMermaidService()
    plan = service.analyze(FLOWCHART_ASCII)

    # 至少生成 flowchart 方案，且最高置信度方案排在最前
    assert len(plan.schemes) >= 1
    assert plan.schemes[0].diagram_type == "flowchart"
    confidences = [s.confidence for s in plan.schemes]
    assert confidences == sorted(confidences, reverse=True)


def test_auto_select_is_deterministic() -> None:
    service = AsciiToMermaidService()
    plan_a = service.analyze(FLOWCHART_ASCII)
    plan_b = service.analyze(FLOWCHART_ASCII)

    assert plan_a.best.mermaid == plan_b.best.mermaid
    assert plan_a.best.scheme_id == plan_b.best.scheme_id


def test_interactive_select_picks_requested_scheme(monkeypatch) -> None:
    service = AsciiToMermaidService()
    plan = service.analyze(FLOWCHART_ASCII)
    assert len(plan.schemes) >= 1

    def fake_prompt(text: str) -> str:
        return "1"

    chosen = interactive_select(plan, prompt_fn=fake_prompt)
    assert chosen is plan.schemes[0]


def test_low_confidence_returns_none() -> None:
    service = AsciiToMermaidService()
    result = service.convert(
        "just some plain text\nwith no structure at all\nand more words",
        confidence_threshold=0.5,
    )
    assert result is None


def test_is_ascii_diagram_detection() -> None:
    service = AsciiToMermaidService()
    assert service.is_ascii_diagram(FLOWCHART_ASCII)
    assert service.is_ascii_diagram(SEQUENCE_ASCII)
    assert service.is_ascii_diagram(CLASS_ASCII)
    assert service.is_ascii_diagram(MINDMAP_ASCII)
    assert not service.is_ascii_diagram("plain text\nwithout structure")


def test_conversion_scheme_summary() -> None:
    service = AsciiToMermaidService()
    plan = service.analyze(FLOWCHART_ASCII)
    assert plan.best is not None
    assert "lines" in plan.best.summary
    assert plan.best.summary["lines"] > 0


def test_convert_returns_mermaid_string() -> None:
    from md_converter.services.ascii_mermaid import convert_ascii_to_mermaid

    mermaid = convert_ascii_to_mermaid(FLOWCHART_ASCII)
    assert mermaid is not None
    assert mermaid.startswith("flowchart")
