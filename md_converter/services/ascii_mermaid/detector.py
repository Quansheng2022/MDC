"""
ASCII 图类型自动检测器

基于特征分析结果对 flowchart / sequence / class / mindmap 四种
图表类型进行置信度打分，返回按置信度降序的类型得分列表。
"""

from __future__ import annotations

from typing import List, Tuple

from .analyzer import AsciiAnalyzer
from .model import DiagramFeatures, TypeScore


class DiagramTypeDetector:
    """
    图表类型检测器。

    对四种 Mermaid 图表类型分别计算 0..1 的置信度，
    输出稳定排序（置信度降序，同类按固定优先级）。
    """

    # 平局时的固定优先级（数值越小越优先）
    TYPE_PRIORITY = {
        "flowchart": 0,
        "sequence": 1,
        "class": 2,
        "mindmap": 3,
    }

    @classmethod
    def detect(cls, features: DiagramFeatures) -> Tuple[TypeScore, ...]:
        """
        检测图表类型。

        参数:
            features: 特征分析结果

        返回:
            Tuple[TypeScore, ...]: 按置信度降序的类型得分
        """
        scores = [
            cls._flowchart_score(features),
            cls._sequence_score(features),
            cls._class_score(features),
            cls._mindmap_score(features),
        ]
        scores.sort(
            key=lambda s: (
                -s.confidence,
                cls.TYPE_PRIORITY.get(s.diagram_type, 99),
            )
        )
        return tuple(scores)

    # ============================================================
    # 各类型打分
    # ============================================================

    @classmethod
    def _flowchart_score(cls, features: DiagramFeatures) -> TypeScore:
        """流程图：方框 + 有向箭头 / 分支连接符。"""
        evidence: List[str] = []
        score = 0.0

        box_count = len(features.boxes)
        arrow_count = len(features.arrows)
        junction_count = len(features.junction_rows)

        # 树形结构（单根，无方框/箭头）→ flowchart（目录树/层级树）
        if features.tree_nodes and not features.boxes and not features.messages:
            min_depth = min(n.depth for n in features.tree_nodes)
            roots = [n for n in features.tree_nodes if n.depth == min_depth]
            if len(roots) == 1 and len(features.tree_nodes) >= 2:
                return TypeScore(
                    diagram_type="flowchart",
                    confidence=0.90,
                    evidence=("tree → flowchart",),
                )
            # 多根 + 垂直箭头 → 文本流程（分支汇合型）
            vertical = any(a.direction in ("down", "up") for a in features.arrows)
            if len(roots) > 1 and vertical:
                return TypeScore(
                    diagram_type="flowchart",
                    confidence=0.85,
                    evidence=("text flow → flowchart",),
                )

        # 嵌套盒分层布局（产品全景图）→ flowchart
        if AsciiAnalyzer.is_landscape_layout(list(features.boxes)):
            return TypeScore(
                diagram_type="flowchart",
                confidence=0.90,
                evidence=("landscape layout → flowchart",),
            )

        # 内嵌盒图（外层盒 + 多个内部盒子 + 箭头）
        raw = list(features.boxes)
        if len(raw) >= 5:
            outer = min(raw, key=lambda box: (box.y0, box.x0))
            inner = [
                box
                for box in raw
                if box is not outer
                and outer.x0 <= box.x0
                and outer.x1 >= box.x1
                and outer.y0 <= box.y0
                and outer.y1 >= box.y1
            ]
            inner_arrows = [
                arrow
                for arrow in AsciiAnalyzer.extract_arrows(features.grid)
                if outer.x0 < arrow.col < outer.x1 and outer.y0 < arrow.row < outer.y1
            ]
            if len(inner) >= 4 and len(inner_arrows) >= 2:
                return TypeScore(
                    diagram_type="flowchart",
                    confidence=0.85,
                    evidence=("inner box graph → flowchart",),
                )

        # 内容盒（标题 + 分节内容，无箭头/生命线）→ flowchart with subgraph
        if (
            not features.arrows
            and not features.lifelines
            and not features.messages
            and not features.class_boxes
        ):
            merged = AsciiAnalyzer._merge_stacked_boxes(list(features.boxes))
            top_level = AsciiAnalyzer._top_level_boxes(merged)
            if len(top_level) == 1:
                sections = AsciiAnalyzer._split_sections(top_level[0], features.grid)
                if len(sections) >= 2:
                    return TypeScore(
                        diagram_type="flowchart",
                        confidence=0.85,
                        evidence=("content box → subgraph",),
                    )

        # 强惩罚：时序图特征明显时降低流程图得分
        if len(features.lifelines) >= 2 and len(features.messages) >= 1:
            score -= 0.3
            evidence.append("lifelines detected")

        if arrow_count > 0:
            score += 0.35
            evidence.append(f"{arrow_count} arrows")
        if box_count >= 2:
            score += 0.2
            evidence.append(f"{box_count} boxes")
        if arrow_count >= 2:
            score += 0.15
        if junction_count > 0:
            score += 0.15
            evidence.append(f"{junction_count} junction rows")
        if box_count >= 1 and arrow_count >= 1:
            score += 0.15
        if arrow_count >= 3:
            score += 0.05

        return TypeScore(
            diagram_type="flowchart",
            confidence=max(0.0, min(0.95, score)),
            evidence=tuple(evidence),
        )

    @classmethod
    def _sequence_score(cls, features: DiagramFeatures) -> TypeScore:
        """时序图：生命线 + 水平消息箭头。"""
        evidence: List[str] = []
        lifelines = len(features.lifelines)
        messages = len(features.messages)

        score = 0.0
        if lifelines >= 2:
            score += 0.3
            evidence.append(f"{lifelines} lifelines")
        if messages >= 1:
            score += 0.4
            evidence.append(f"{messages} messages")
        if lifelines >= 3:
            score += 0.1
        if messages >= 2:
            score += 0.1
        if messages >= 4:
            score += 0.05

        return TypeScore(
            diagram_type="sequence",
            confidence=max(0.0, min(0.95, score)),
            evidence=tuple(evidence),
        )

    @classmethod
    def _class_score(cls, features: DiagramFeatures) -> TypeScore:
        """类图：多节方框 + 可见性标记 / 构造型 / UML 关系。"""
        evidence: List[str] = []
        class_boxes = len(features.class_boxes)
        relations = len(features.class_relations)

        score = 0.0
        if class_boxes >= 1:
            score += 0.4
            evidence.append(f"{class_boxes} class boxes")
        if class_boxes >= 2:
            score += 0.15
        if any(cb.stereotype for cb in features.class_boxes):
            score += 0.1
            evidence.append("stereotype")
        if any(
            section.kind in ("attributes", "methods")
            for cb in features.class_boxes
            for section in cb.sections
        ):
            score += 0.1
            evidence.append("sections")
        if relations > 0:
            score += 0.2
            evidence.append(f"{relations} relations")

        return TypeScore(
            diagram_type="class",
            confidence=max(0.0, min(0.95, score)),
            evidence=tuple(evidence),
        )

    @classmethod
    def _mindmap_score(cls, features: DiagramFeatures) -> TypeScore:
        """思维导图：缩进树 + 无明显方框/箭头。"""
        evidence: List[str] = []
        tree_count = len(features.tree_nodes)
        max_depth = max((n.depth for n in features.tree_nodes), default=0)

        if tree_count < 2:
            return TypeScore(
                diagram_type="mindmap",
                confidence=0.0,
                evidence=("no tree",),
            )

        score = 0.0
        if tree_count >= 2:
            score += 0.3
            evidence.append(f"{tree_count} tree nodes")
        if max_depth >= 1:
            score += 0.25
            evidence.append(f"depth {max_depth}")
        if max_depth >= 2:
            score += 0.15

        # 方框与箭头会显著削弱思维导图得分
        if len(features.boxes) == 0 and len(features.arrows) == 0:
            score += 0.15
        elif len(features.boxes) <= 1 and len(features.arrows) == 0:
            score += 0.05

        return TypeScore(
            diagram_type="mindmap",
            confidence=max(0.0, min(0.95, score)),
            evidence=tuple(evidence),
        )
