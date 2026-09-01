---
title: MD converter 文档转换器架构设计
date: 2026-07-29
tags: [Deepseek]
---


# 务实的演进路线：从核心价值到平台生态

您的担心非常正确。这是软件工程中最常见的陷阱之一——**架构先行，产品难产**。

让我帮您从"大而全的架构"回到"可落地的产品"。

---

## 一、现状分析：架构 vs 产品

### 当前状态

```mermaid
flowchart LR
    subgraph Chart["架构完整度 vs 产品完整度"]
        direction LR
        A["架构设计"] --> A1["███████████████████████████████████████░ 95%"]
        B["产品功能"] --> B1["████████████████░░░░░░░░░░░░░░░░░░░░░░░░ 40%"]
        C["代码实现"] --> C1["██████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 35%"]
        D["可用性"] --> D1["████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 15%"]
    end
```

### 核心问题

| 问题 | 描述 | 影响 |
|------|------|------|
| 架构过度设计 | 追求LLVM级别的完美 | 开发周期无限延长 |
| 范围蔓延 | 不断增加新能力 | 永远无法完成 |
| 缺少MVP | 没有最小可行产品 | 无法验证市场需求 |
| 工程债务 | 设计远超前于实现 | 团队疲劳、产品难产 |

---

## 二、回到核心：本平台真正解决什么问题？

### 用户最痛的点

```mermaid
mindmap
  root((用户真实痛点))
    技术文档写得慢
      画图费时
        架构图
        流程图
      格式调整费时
        Word排版
      图表与文字不同步
    文档版本管理混乱
      多人协作冲突
      变更不知影响范围
      需求与设计脱节
    文档难以复用
      技术文档 → Word → PDF
      下次重新写
      知识无法积累
    文档质量参差不齐
      格式不统一
      内容不完整
      评审效率低
```

### 核心价值主张

> **"让技术人员像写代码一样写文档"**

用最熟悉的Markdown写作，自动生成专业的Word/PDF文档。

---

## 三、建议演进路线

### 阶段一：核心可用（MVP）—— 当前最重要

**目标**：让用户真正能用起来，解决80%的日常需求

```mermaid
flowchart LR
    subgraph MVP["✅ MVP v1.0 - 核心能力"]
        direction TB

        subgraph Input["📥 输入"]
            I1["Markdown"]
            I2["ASCII图"]
            I3["Mermaid"]
        end

        subgraph Core["⚙️ 核心能力"]
            direction TB
            C1["标题/段落/列表/表格/代码块"]
            C2["ASCII图 → SVG/矢量图"]
            C3["自动目录"]
            C4["自动编号"]
            C5["简单样式主题"]
        end

        subgraph Output["📤 输出"]
            O1["Word文档 (.docx)"]
        end

        subgraph Delivery["📦 交付物"]
            D1["可安装的Python包"]
            D2["命令行工具"]
        end

        subgraph Target["👥 目标用户"]
            T1["技术文档编写者"]
            T2["架构师"]
        end

        Input --> Core --> Output
        Delivery ~~~ Target
    end
```

**MVP实现代码结构**（精简版）：

```
doc-compiler/
├── src/
│   ├── core/
│   │   ├── converter.py      # 主转换器
│   │   └── config.py         # 配置
│   ├── parser/
│   │   └── markdown.py       # Markdown解析（含Mermaid/ASCII）
│   ├── renderer/
│   │   └── word.py           # Word渲染
│   └── cli.py                # 命令行入口
├── tests/
├── README.md
└── setup.py
```

### 阶段二：体验优化（产品化）

**目标**：让用户用得更舒服、更高效

```mermaid
mindmap
  root((v2.0 - 产品化提升))
    新增
      实时预览
      VSCode插件
      多主题支持
        Corporate
        Academic
      配置化模板
      增量编译
      错误诊断和修复提示
    目标用户
      技术团队
      文档团队
    预计开发
      4-6周
```

### 阶段三：协作与知识（团队级）

**目标**：支持团队协作和知识管理

```
mindmap
  root((v3.0 - 团队协作))
    新增功能
      Workspace
        多文档管理
      需求追踪
        REQ-001 → Design → Test
      影响分析
        修改一处，标记所有受影响
      知识图谱基础
      多格式输出
        PDF
        HTML
    目标用户
      研发团队
      产品团队
    预计开发
      8-12周
```

### 阶段四：智能平台（企业级）

**目标**：AI驱动、知识管理、企业级部署

```mermaid
mindmap
  root((v4.0 - 智能平台))
    新增功能
      AI辅助写作
        补全
        改写
        摘要
      语义搜索
        向量
        知识图谱
      智能问答
        Graph RAG
      企业级部署
        多租户
        权限
      完整IDE体验
        LSP
    目标用户
      企业知识团队
      合规部门
    预计开发
      12-16周
```

---

## 四、MVP详细设计

### 核心功能清单

```mermaid
flowchart LR
    subgraph Root["🎯 MVP v1.0 功能清单"]
        direction TB

        subgraph MD["📝 Markdown支持"]
            direction TB
            M1["标题 (#, ##, ###)"]
            M2["段落和换行"]
            M3["粗体/斜体/删除线"]
            M4["列表 (有序/无序)"]
            M5["表格"]
            M6["代码块 (语法高亮)"]
            M7["引用块"]
            M8["链接和图片"]
            M9["水平分割线"]
        end

        subgraph Chart["🎨 图表支持"]
            direction TB
            C1["ASCII结构图<br/>┌┐└┘├┤─│"]
            C2["Mermaid<br/>流程图 / 时序图 / 类图"]
            C3["自动生成矢量图<br/>DrawingML"]
        end

        subgraph Word["📄 Word输出"]
            direction TB
            W1["专业排版<br/>字号/字体/间距"]
            W2["自动目录 (TOC)"]
            W3["自动编号<br/>标题 / 图表"]
            W4["表格样式<br/>边框 / 表头"]
            W5["图片居中"]
            W6["代码块样式"]
        end

        subgraph Use["🎯 使用方式"]
            direction TB
            U1["命令行<br/>doc-compiler input.md -o output.docx"]
            U2["Python API"]
            U3["配置文件<br/>.doc-compiler.yaml"]
        end

        MD ~~~ Chart ~~~ Word ~~~ Use
    end
```

### 简单实现架构

```python
# src/core/converter.py - 核心转换器（精简版）

import re
from pathlib import Path
from typing import List, Dict, Any

from src.parser.markdown import MarkdownParser
from src.renderer.word import WordRenderer
from src.utils.logger import get_logger


class DocumentConverter:
    """
    文档转换器 - MVP版本
    只有核心能力，没有过度设计
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = get_logger(__name__)
        
        # 核心组件
        self.parser = MarkdownParser()
        self.renderer = WordRenderer()
    
    def convert(self, input_path: Path, output_path: Path) -> Path:
        """
        转换Markdown到Word
        
        Args:
            input_path: 输入Markdown文件路径
            output_path: 输出Word文件路径
            
        Returns:
            输出文件路径
        """
        self.logger.info(f"Converting: {input_path} → {output_path}")
        
        # 1. 读取文件
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 2. 解析Markdown
        ast = self.parser.parse(content)
        
        # 3. 渲染Word
        self.renderer.render(ast, output_path, self.config)
        
        return output_path


# src/parser/markdown.py - Markdown解析器（精简版）

import re
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class Node:
    """AST节点 - 极简设计"""
    type: str
    text: str = ""
    children: List['Node'] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []
        if self.metadata is None:
            self.metadata = {}


class MarkdownParser:
    """
    Markdown解析器 - MVP版本
    只支持最常用的Markdown语法
    """
    
    def parse(self, content: str) -> Node:
        """解析Markdown内容为AST"""
        lines = content.split('\n')
        root = Node(type='document')
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # 标题
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                text = line.lstrip('#').strip()
                node = Node(type='heading', text=text, metadata={'level': level})
                root.children.append(node)
                i += 1
                continue
            
            # 代码块
            if line.startswith('```'):
                language = line[3:].strip()
                code_lines = []
                i += 1
                while i < len(lines) and not lines[i].startswith('```'):
                    code_lines.append(lines[i])
                    i += 1
                node = Node(
                    type='code_block',
                    text='\n'.join(code_lines),
                    metadata={'language': language}
                )
                root.children.append(node)
                i += 1
                continue
            
            # 列表
            if re.match(r'^[\-\*\+]\s+', line):
                nodes = self._parse_list(lines, i)
                root.children.extend(nodes)
                i += len(nodes)
                continue
            
            # 表格
            if line.startswith('|'):
                nodes = self._parse_table(lines, i)
                root.children.extend(nodes)
                i += len(nodes)
                continue
            
            # ASCII图
            if self._is_ascii_diagram(line):
                nodes = self._parse_ascii_diagram(lines, i)
                root.children.extend(nodes)
                i += len(nodes)
                continue
            
            # Mermaid图
            if '```mermaid' in line:
                nodes = self._parse_mermaid(lines, i)
                root.children.extend(nodes)
                i += len(nodes)
                continue
            
            # 普通段落
            if line.strip():
                node = Node(type='paragraph', text=line)
                root.children.append(node)
            
            i += 1
        
        return root
    
    def _parse_list(self, lines: List[str], start: int) -> List[Node]:
        """解析列表"""
        # TODO: 实现列表解析
        return [Node(type='list', text='list')]
    
    def _parse_table(self, lines: List[str], start: int) -> List[Node]:
        """解析表格"""
        # TODO: 实现表格解析
        return [Node(type='table', text='table')]
    
    def _parse_ascii_diagram(self, lines: List[str], start: int) -> List[Node]:
        """解析ASCII图"""
        # TODO: 实现ASCII图解析
        return [Node(type='diagram', text='ascii')]
    
    def _parse_mermaid(self, lines: List[str], start: int) -> List[Node]:
        """解析Mermaid图"""
        # TODO: 实现Mermaid解析
        return [Node(type='diagram', text='mermaid')]
    
    def _is_ascii_diagram(self, line: str) -> bool:
        """检测是否为ASCII图"""
        chars = set('┌┐└┘├┤┬┴┼─│')
        return any(c in chars for c in line)
```

---

## 五、开发优先级

### P0 - 必须完成（MVP）

```mermaid
flowchart LR
    subgraph P0["🎯 优先级 P0"]
        direction TB
        T1["✅ 1. Markdown基础语法解析<br/>标题 / 段落 / 列表 / 表格 / 代码块"]
        T2["✅ 2. Word文档生成<br/>标题 / 段落 / 列表 / 表格 / 代码块<br/>基本样式（字体、大小、颜色）"]
        T3["✅ 3. ASCII结构图 → 矢量图<br/>检测ASCII图块 → 转换为DrawingML"]
        T4["✅ 4. 自动目录<br/>根据标题生成目录"]
        T5["✅ 5. 命令行工具<br/>doc-compiler input.md -o output.docx"]
        T6["✅ 6. 基本文档<br/>README + 使用示例"]
        T1 ~~~ T2 ~~~ T3 ~~~ T4 ~~~ T5 ~~~ T6
    end
```

### P1 - 重要但可延后（v2.0）

```mermaid
flowchart LR
    subgraph P1["🎯 优先级 P1"]
        direction TB
        T1["✅ 1. 自动编号"]
        T2["✅ 2. 多主题支持"]
        T3["✅ 3. 实时预览"]
        T4["✅ 4. VSCode插件"]
        T5["✅ 5. PDF输出"]
        T6["✅ 6. 错误诊断和修复提示"]
        T1 ~~~ T2 ~~~ T3 ~~~ T4 ~~~ T5 ~~~ T6
    end
```

### P2 - 锦上添花（v3.0+）

```mermaid
flowchart LR
    subgraph P2["🎯 优先级 P2"]
        direction TB
        P2_1["1. 需求追踪<br/>REQ-001 → Design → Test"]
        P2_2["2. 知识图谱"]
        P2_3["3. 影响分析"]
        P2_4["4. 多文档工作区"]
        P2_5["5. AI辅助写作"]
        P2_6["6. 语义搜索"]
        P2_1 ~~~ P2_2 ~~~ P2_3 ~~~ P2_4 ~~~ P2_5 ~~~ P2_6
    end
```

---

## 六、立即行动清单

### 本周可以开始的工作

| 任务 | 时间 | 产出 |
|------|------|------|
| 1. 精简代码，只保留核心能力 | 1天 | 清理后的代码库 |
| 2. 实现Markdown基础解析 | 2天 | 支持标题/段落/列表/表格 |
| 3. 实现Word基础渲染 | 2天 | 生成可用的Word文档 |
| 4. 实现ASCII图转换 | 1天 | ASCII → 矢量图 |
| 5. 集成测试 | 1天 | 端到端工作流 |

### 第一周交付物

```mermaid
graph LR
    ROOT["📁 doc-compiler/"]
    ROOT --> README["📄 README.md<br/>项目说明 + 快速开始"]
    ROOT --> SETUP["📄 setup.py<br/>安装脚本"]
    ROOT --> CLI["🔧 doc-compiler<br/>命令行工具"]
    ROOT --> SRC["📁 src/"]
    ROOT --> TESTS["📁 tests/"]
    ROOT --> EXAMPLES["📁 examples/"]
    
    SRC --> CORE["📁 core/"]
    SRC --> PARSER["📁 parser/"]
    SRC --> RENDERER["📁 renderer/"]
    SRC --> CLIPY["📄 cli.py<br/>~50行"]
    
    CORE --> CONVERTER["📄 converter.py<br/>~200行<br/>核心转换器"]
    PARSER --> MARKDOWN["📄 markdown.py<br/>~300行<br/>Markdown解析"]
    RENDERER --> WORD["📄 word.py<br/>~400行<br/>Word渲染"]
    
    TESTS --> TEST["📄 test_converter.py<br/>单元测试"]
    
    EXAMPLES --> SAMPLE["📄 sample.md<br/>示例文档"]
    EXAMPLES --> OUTPUT["📄 output.docx<br/>生成示例"]
    
    classDef root fill:#4CAF50,color:#fff,stroke:#2E7D32,stroke-width:3px
    classDef folder fill:#2196F3,color:#fff,stroke:#0D47A1,stroke-width:2px
    classDef file fill:#FFC107,color:#333,stroke:#F57F17,stroke-width:2px
    classDef emphasis fill:#FF5722,color:#fff,stroke:#BF360C,stroke-width:2px
    
    class ROOT root
    class SRC,TESTS,EXAMPLES,CORE,PARSER,RENDERER folder
    class README,SETUP,CLI,CLIPY,TEST,SAMPLE,OUTPUT file
    class CONVERTER,MARKDOWN,WORD emphasis
```

### 验证标准

```mermaid
flowchart LR
    subgraph Test["🧪 验证通过标准"]
        direction TB
        
        subgraph Input["📥 输入内容"]
            direction TB
            I1["Markdown内容"]
            I1 --> I2["标题: # 系统架构, ## 整体设计"]
            I1 --> I3["段落: 用户通过浏览器访问系统..."]
            I1 --> I4["ASCII图: 前端 → 后端"]
            I1 --> I5["表格: GET /api"]
        end
        
        subgraph Pipeline["⚙️ 处理过程"]
            direction TB
            P1["Markdown解析"] --> P2["AST构建"]
            P2 --> P3["图表转换"] --> P4["渲染"]
        end
        
        subgraph Output["📤 输出要求"]
            direction TB
            O1["Word文档"]
            O1 --> O2["目录自动生成"]
            O1 --> O3["图表正确显示"]
            O1 --> O4["表格格式正确"]
            O1 --> O5["排版专业"]
        end
        
        Input --> Pipeline --> Output
    end
```

---

## 七、核心建议

### 1. 停止设计，开始交付

```
当前状态：95% 设计 + 35% 代码 → 永远在"设计"
目标状态：20% 设计 + 80% 代码 + 100% 交付
```

### 2. MVP三原则

| 原则 | 说明 |
|------|------|
| **够用即可** | 不追求完美，只要能解决核心问题 |
| **快速验证** | 2-3周内让用户用起来 |
| **持续迭代** | 根据反馈不断改进 |

### 3. 放弃的假设

```
❌ 需要支持所有Markdown语法 → ✅ 只支持最常用的80%
❌ 需要完美的架构 → ✅ 够用的架构，后续重构
❌ 需要支持所有输出格式 → ✅ 只支持Word，后续扩展
❌ 需要知识图谱 → ✅ 先让用户能用起来
❌ 需要AI集成 → ✅ 先做好基础功能
```

### 4. 成功标准

> **"2周后，有10个用户真正在用这个工具写技术文档"**

---

## 总结

| 问题 | 当前状态 | 建议 |
|------|---------|------|
| 架构 | 95% 完成 | 停止设计，开始编码 |
| 代码 | 35% 完成 | 聚焦MVP，快速交付 |
| 产品 | 15% 完成 | 2周内推出可用的v1.0 |
| 用户 | 0 用户 | 用产品吸引第一批用户 |

**立即行动：**

1. 梳理当前代码，删除不必要的抽象
2. 确定MVP功能清单（不超过10个功能）
3. 每天交付可工作的代码
4. 2周后发布v1.0
5. 根据用户反馈迭代

**记住：**

> 一个正在使用的v0.1，远比一个完美的v1.0更有价值。