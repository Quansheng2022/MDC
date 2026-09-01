"""
思维导图转换器

将缩进/树形分支文本转换为 Mermaid mindmap。
"""

from __future__ import annotations

from typing import Optional

from ..model import DiagramFeatures
from .base import BaseConverter, escape_mindmap_label


class MindmapConverter(BaseConverter):
    """树形节点 → Mermaid mindmap。"""

    diagram_type = "mindmap"

    # mindmap 中作为图类型关键字的词，节点文本以这些词开头时需加引号
    _RESERVED_WORDS = (
        "mindmap",
        "graph",
        "flowchart",
        "sequenceDiagram",
        "classDiagram",
        "stateDiagram",
        "erDiagram",
        "journey",
        "gantt",
        "pie",
        "gitGraph",
        "timeline",
        "quadrantChart",
        "xychart",
        "sankey",
        "block",
    )

    def convert(self, features: DiagramFeatures) -> Optional[str]:
        nodes = sorted(features.tree_nodes, key=lambda n: (n.row, n.depth))
        if len(nodes) < 2:
            return None

        # Mermaid mindmap 只允许一个根节点；多根（如缩进代码）不转换
        min_depth = min(n.depth for n in nodes)
        roots = [n for n in nodes if n.depth == min_depth]
        if len(roots) != 1:
            return None

        root = nodes[0]
        lines = ["mindmap"]
        root_text = self._format_node_text(root.text)
        lines.append(f"  {root_text}")

        root_depth = root.depth
        for node in nodes[1:]:
            depth = max(0, node.depth - root_depth)
            indent = "  " * (1 + depth)
            text = self._format_node_text(node.text)
            if text:
                lines.append(f"{indent}{text}")

        return "\n".join(lines)

    # ============================================================
    # 工具函数
    # ============================================================

    @staticmethod
    def _format_node_text(text: str) -> str:
        """
        规范化思维导图节点文本。

        - 压缩空白
        - 转义特殊字符（括号/波浪线等使用字符实体）
        """
        text = " ".join(text.split())
        if not text:
            return ""
        escaped = escape_mindmap_label(text)
        if any(escaped.lstrip().startswith(word) for word in MindmapConverter._RESERVED_WORDS):
            return f'"{escaped}"'
        return escaped
