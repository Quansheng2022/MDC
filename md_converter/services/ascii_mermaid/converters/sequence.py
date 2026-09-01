"""
时序图转换器

将带生命线与水平消息箭头的 ASCII 图转换为 Mermaid sequenceDiagram。
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from ..model import DiagramFeatures, Lifeline, Message
from .base import (
    BOX_DRAWING_RE,
    BaseConverter,
    escape_mermaid_label,
    node_id,
    strip_box_drawing,
)


class SequenceConverter(BaseConverter):
    """生命线 + 消息 → Mermaid sequenceDiagram。"""

    diagram_type = "sequence"

    def convert(self, features: DiagramFeatures) -> Optional[str]:
        lifelines = sorted(features.lifelines, key=lambda ll: ll.col)
        if len(lifelines) < 2 or not features.messages:
            return None
        # 生命线标签含方框/连接线字符 → 这通常是方框图而非真正的时序图，
        # 直接放弃转换，让上层保留原始 ASCII 文本（避免生成无意义或错误的时序图）。
        if any(BOX_DRAWING_RE.search(ll.label or "") for ll in lifelines):
            return None

        participants = self._assign_participants(lifelines)
        lines = ["sequenceDiagram"]
        for lifeline, pid in participants:
            label = lifeline.label.strip() or pid
            if label == pid:
                lines.append(f"    participant {pid}")
            else:
                label = strip_box_drawing(label)
                lines.append(f"    participant {pid} as {escape_mermaid_label(label)}")

        col_to_id = {lifeline.col: pid for lifeline, pid in participants}
        for msg in self._usable_messages(features.messages, col_to_id):
            left_id = col_to_id[msg.col0]
            right_id = col_to_id[msg.col1]
            token = self._normalize_token(msg.token)
            text = msg.text.strip()
            if text:
                text = strip_box_drawing(text)
                lines.append(f"    {left_id}{token}{right_id}: {escape_mermaid_label(text)}")
            else:
                lines.append(f"    {left_id}{token}{right_id}")

        return "\n".join(lines)

    # ============================================================
    # 参与者
    # ============================================================

    @staticmethod
    def _assign_participants(
        lifelines: List[Lifeline],
    ) -> List[Tuple[Lifeline, str]]:
        """
        为生命线分配稳定参与者 ID，并处理重名。

        返回:
            List[Tuple[Lifeline, str]]: (生命线, 参与者 ID)
        """
        return [(lifeline, node_id(i)) for i, lifeline in enumerate(lifelines)]

    @staticmethod
    def _usable_messages(
        messages: List[Message],
        col_to_id: Dict[int, str],
    ) -> List[Message]:
        """过滤掉无法映射到参与者的消息。"""
        return [msg for msg in messages if msg.col0 in col_to_id and msg.col1 in col_to_id]

    @staticmethod
    def _normalize_token(token: str) -> str:
        """
        将 ASCII 箭头记号规范化为 Mermaid 支持的记号。

        例如: '-->' -> '-->'，'->>' -> '->>'，'--x' -> '--x'。
        """
        if "<" in token and ">" in token:
            return "<-->" if "--" in token or "==" in token else "<->"
        if ">>" in token:
            return "-->>" if "--" in token else "->>"
        if "x" in token:
            return "--x" if "--" in token else "-x"
        if ">" in token:
            return "-->" if "--" in token or "==" in token else "->"
        if "<" in token:
            return "<--" if "--" in token else "<-"
        return "-->"
