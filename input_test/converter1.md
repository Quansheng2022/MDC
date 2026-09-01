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

```
┌─────────────────────────────────────────────────────────────┐
│                    架构完整度 vs 产品完整度                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  架构设计: ████████████████████████████████████░ 95%       │
│  产品功能: ████████████░░░░░░░░░░░░░░░░░░░░░░░░ 40%       │
│  代码实现: ██████████░░░░░░░░░░░░░░░░░░░░░░░░░░ 35%       │
│  可用性:   ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 15%       │
│                                                             │
│  风险：大而全的架构 → 永远在"设计"而无法"交付"              │
└─────────────────────────────────────────────────────────────┘
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

```
┌─────────────────────────────────────────────────────────────┐
│                    用户真实痛点                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1️⃣ 技术文档写得慢                                         │
│     - 画图费时（架构图、流程图）                            │
│     - 格式调整费时（Word排版）                              │
│     - 图表与文字不同步                                      │
│                                                             │
│  2️⃣ 文档版本管理混乱                                        │
│     - 多人协作冲突                                          │
│     - 变更不知影响范围                                      │
│     - 需求与设计脱节                                        │
│                                                             │
│  3️⃣ 文档难以复用                                            │
│     - 技术文档 → Word → PDF                                │
│     - 下次还要重新写                                        │
│     - 知识无法积累                                          │
│                                                             │
│  4️⃣ 文档质量参差不齐                                        │
│     - 格式不统一                                            │
│     - 内容不完整                                            │
│     - 评审效率低                                            │
└─────────────────────────────────────────────────────────────┘
```

### 核心价值主张

> **"让技术人员像写代码一样写文档"**

用最熟悉的Markdown写作，自动生成专业的Word/PDF文档。

---

## 三、建议演进路线

### 阶段一：核心可用（MVP）—— 当前最重要

**目标**：让用户真正能用起来，解决80%的日常需求

```
┌─────────────────────────────────────────────────────────────┐
│                    MVP v1.0 - 核心能力                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ✅ 输入：Markdown + ASCII图 + Mermaid                      │
│  ✅ 输出：Word文档 (.docx)                                 │
│  ✅ 核心能力：                                              │
│     - 标题/段落/列表/表格/代码块                            │
│     - ASCII图 → SVG/矢量图                                 │
│     - 自动目录                                             │
│     - 自动编号                                             │
│     - 简单样式主题                                          │
│     - 命令行工具                                           │
│                                                             │
│  📦 交付物：可安装的Python包 + 命令行工具                  │
│  👥 目标用户：技术文档编写者、架构师                        │
│  ⏱️ 预计开发：2-3周                                         │
└─────────────────────────────────────────────────────────────┘
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

```
┌─────────────────────────────────────────────────────────────┐
│                    v2.0 - 产品化提升                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🚀 新增：                                                 │
│     - 实时预览 (Live Preview)                              │
│     - VSCode插件                                           │
│     - 多主题支持 (Corporate/Academic)                      │
│     - 配置化模板                                           │
│     - 增量编译                                             │
│     - 错误诊断和修复提示                                   │
│                                                             │
│  👥 目标用户：技术团队、文档团队                            │
│  ⏱️ 预计开发：4-6周                                         │
└─────────────────────────────────────────────────────────────┘
```

### 阶段三：协作与知识（团队级）

**目标**：支持团队协作和知识管理

```
┌─────────────────────────────────────────────────────────────┐
│                    v3.0 - 团队协作                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🚀 新增：                                                 │
│     - Workspace (多文档管理)                               │
│     - 需求追踪 (REQ-001 → Design → Test)                  │
│     - 影响分析 (修改一处，标记所有受影响)                  │
│     - 知识图谱基础                                         │
│     - 多格式输出 (PDF/HTML)                                │
│                                                             │
│  👥 目标用户：研发团队、产品团队                            │
│  ⏱️ 预计开发：8-12周                                        │
└─────────────────────────────────────────────────────────────┘
```

### 阶段四：智能平台（企业级）

**目标**：AI驱动、知识管理、企业级部署

```
┌─────────────────────────────────────────────────────────────┐
│                    v4.0 - 智能平台                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🚀 新增：                                                 │
│     - AI辅助写作 (补全、改写、摘要)                        │
│     - 语义搜索 (向量 + 知识图谱)                          │
│     - 智能问答 (Graph RAG)                                 │
│     - 企业级部署 (多租户、权限)                            │
│     - 完整的IDE体验 (LSP)                                  │
│                                                             │
│  👥 目标用户：企业知识团队、合规部门                        │
│  ⏱️ 预计开发：12-16周                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 四、MVP详细设计

### 核心功能清单

```
┌─────────────────────────────────────────────────────────────┐
│                    MVP v1.0 功能清单                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📝 Markdown支持：                                         │
│     ✅ 标题 (#, ##, ###)                                   │
│     ✅ 段落和换行                                          │
│     ✅ 粗体/斜体/删除线                                    │
│     ✅ 列表 (有序/无序)                                    │
│     ✅ 表格                                                │
│     ✅ 代码块 (语法高亮)                                   │
│     ✅ 引用块                                              │
│     ✅ 链接和图片                                          │
│     ✅ 水平分割线                                          │
│                                                             │
│  🎨 图表支持：                                             │
│     ✅ ASCII结构图 (┌┐└┘├┤─│)                            │
│     ✅ Mermaid (流程图/时序图/类图)                        │
│     ✅ 自动生成矢量图 (DrawingML)                          │
│                                                             │
│  📄 Word输出：                                             │
│     ✅ 专业排版 (字号/字体/间距)                           │
│     ✅ 自动目录 (TOC)                                      │
│     ✅ 自动编号 (标题/图表)                                │
│     ✅ 表格样式 (边框/表头)                                │
│     ✅ 图片居中                                            │
│     ✅ 代码块样式                                          │
│                                                             │
│  🎯 使用方式：                                             │
│     ✅ 命令行: doc-compiler input.md -o output.docx       │
│     ✅ Python API                                          │
│     ✅ 配置文件 (.doc-compiler.yaml)                       │
└─────────────────────────────────────────────────────────────┘
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

```
┌─────────────────────────────────────────────────────────────┐
│                    优先级 P0                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Markdown基础语法解析                                    │
│     - 标题、段落、列表、表格、代码块                       │
│                                                             │
│  2. Word文档生成                                           │
│     - 标题、段落、列表、表格、代码块                       │
│     - 基本样式（字体、大小、颜色）                         │
│                                                             │
│  3. ASCII结构图 → 矢量图                                   │
│     - 检测ASCII图块                                        │
│     - 转换为DrawingML                                      │
│                                                             │
│  4. 自动目录                                               │
│     - 根据标题生成目录                                     │
│                                                             │
│  5. 命令行工具                                             │
│     - doc-compiler input.md -o output.docx               │
│                                                             │
│  6. 基本文档                                               │
│     - README + 使用示例                                    │
└─────────────────────────────────────────────────────────────┘
```

### P1 - 重要但可延后（v2.0）

```
┌─────────────────────────────────────────────────────────────┐
│                    优先级 P1                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 自动编号                                               │
│  2. 多主题支持                                             │
│  3. 实时预览                                               │
│  4. VSCode插件                                             │
│  5. PDF输出                                                │
│  6. 错误诊断和修复提示                                     │
└─────────────────────────────────────────────────────────────┘
```

### P2 - 锦上添花（v3.0+）

```
┌─────────────────────────────────────────────────────────────┐
│                    优先级 P2                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 需求追踪 (REQ-001 → Design → Test)                    │
│  2. 知识图谱                                               │
│  3. 影响分析                                               │
│  4. 多文档工作区                                           │
│  5. AI辅助写作                                             │
│  6. 语义搜索                                               │
└─────────────────────────────────────────────────────────────┘
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

```
doc-compiler/
├── README.md               # 项目说明 + 快速开始
├── setup.py                # 安装脚本
├── doc-compiler            # 命令行工具
├── src/
│   ├── core/
│   │   └── converter.py    # 核心转换器 (~200行)
│   ├── parser/
│   │   └── markdown.py     # Markdown解析 (~300行)
│   ├── renderer/
│   │   └── word.py         # Word渲染 (~400行)
│   └── cli.py              # 命令行 (~50行)
├── tests/
│   └── test_converter.py   # 单元测试
└── examples/
    ├── sample.md           # 示例文档
    └── output.docx         # 生成示例
```

### 验证标准

```
┌─────────────────────────────────────────────────────────────┐
│                    验证通过标准                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ✅ 输入以下内容：                                          │
│                                                             │
│  # 系统架构                                                 │
│                                                             │
│  ## 整体设计                                                 │
│                                                             │
│  用户通过浏览器访问系统...                                   │
│                                                             │
│  ```ascii                                                   │
│  ┌──────────────┐                                          │
│  │    前端      │                                          │
│  └──────┬───────┘                                          │
│         │                                                   │
│  ┌──────▼───────┐                                          │
│  │    后端      │                                          │
│  └──────────────┘                                          │
│  ```                                                        │
│                                                             │
│  ## API接口                                                 │
│                                                             │
│  | 方法 | 路径 | 说明 |                                     │
│  |------|------|------|                                    │
│  | GET  | /api | 获取数据 |                                │
│                                                             │
│  ✅ 输出：                                                  │
│     - 格式正确、排版专业的Word文档                          │
│     - 目录自动生成                                          │
│     - 图表正确显示                                          │
│     - 表格格式正确                                          │
└─────────────────────────────────────────────────────────────┘
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