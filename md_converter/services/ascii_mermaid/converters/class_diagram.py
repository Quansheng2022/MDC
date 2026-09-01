"""
类图转换器

将带分节方框与可见性标记的 ASCII 图转换为 Mermaid classDiagram。
支持构造型、成员规范化与 UML 关系。
"""

from __future__ import annotations

import re
from typing import Optional

from ..model import DiagramFeatures
from .base import BaseConverter, escape_mermaid_label

RELATION_SYMBOLS = {
    "inheritance": "--|>",
    "realization": "..|>",
    "composition": "*--",
    "aggregation": "o--",
    "association": "-->",
    "dependency": "..>",
    "link": "--",
}


class ClassDiagramConverter(BaseConverter):
    """类方框 + 关系 → Mermaid classDiagram。"""

    diagram_type = "class"

    def convert(self, features: DiagramFeatures) -> Optional[str]:
        class_boxes = sorted(
            features.class_boxes,
            key=lambda cb: (cb.box.y0, cb.box.x0),
        )
        if not class_boxes:
            return None

        names = [self._sanitize_name(cb.name) for cb in class_boxes]
        if len(set(names)) != len(names):
            return None

        lines = ["classDiagram"]
        for cb, name in zip(class_boxes, names, strict=True):
            lines.append(f"    class {name} {{")
            if cb.stereotype:
                stereotype = escape_mermaid_label(cb.stereotype)
                lines.append(f"        <<{stereotype}>>")
            for section in cb.sections:
                if section.kind == "title":
                    continue
                for member in section.lines:
                    normalized = self._normalize_member(member.strip())
                    if normalized:
                        lines.append(f"        {escape_mermaid_label(normalized)}")
            lines.append("    }")

        for relation in features.class_relations:
            if relation.src not in names or relation.dst not in names:
                continue
            symbol = RELATION_SYMBOLS.get(relation.kind, "--")
            label = f" : {escape_mermaid_label(relation.label)}" if relation.label else ""
            lines.append(f"    {relation.src} {symbol} {relation.dst}{label}")

        return "\n".join(lines)

    # ============================================================
    # 工具函数
    # ============================================================

    @staticmethod
    def _sanitize_name(name: str) -> str:
        """将类名规范化为 Mermaid 合法标识符。"""
        cleaned = re.sub(r"[^\w]", "_", name).strip("_")
        if not cleaned:
            return "Class"
        if cleaned[0].isdigit():
            cleaned = f"C_{cleaned}"
        return cleaned

    @staticmethod
    def _normalize_member(member: str) -> str:
        """
        规范化类成员行。

        - 保留可见性前缀（+ - # ~）
        - 将 `name: Type` 转换为 Mermaid 的 `Type name`
        """
        member = member.strip()
        if not member:
            return ""
        visibility = ""
        if member[0] in "+-#~":
            visibility = member[0]
            member = member[1:].strip()
        if ":" in member:
            name, type_name = member.split(":", 1)
            name = name.strip()
            type_name = type_name.strip()
            if name and type_name:
                return f"{visibility}{type_name} {name}"
        return f"{visibility}{member}"
