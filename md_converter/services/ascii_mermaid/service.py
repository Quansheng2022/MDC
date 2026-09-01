"""
ASCII → Mermaid 转换服务

编排特征分析、类型检测、多方案生成与方案选择，
返回纯数据对象 :class:`ConversionPlan`，不直接修改 AST。
"""

from __future__ import annotations

from typing import Callable, List, Optional

from .analyzer import AsciiAnalyzer
from .converters import (
    BaseConverter,
    ClassDiagramConverter,
    FlowchartConverter,
    MindmapConverter,
    SequenceConverter,
)
from .detector import DiagramTypeDetector
from .model import ConversionPlan, ConversionScheme


class AsciiToMermaidService:
    """
    ASCII → Mermaid 转换服务。

    流程：
        1. 特征分析（方框、箭头、生命线、树）
        2. 类型自动检测（flowchart / sequence / class / mindmap）
        3. 多方案生成（每种类型生成一个可用方案）
        4. 方案选择（自动优选或交互式）
    """

    def __init__(self, converters: Optional[List[BaseConverter]] = None):
        """
        初始化服务。

        参数:
            converters: 自定义转换器列表；默认使用四种内置转换器
        """
        self.converters: List[BaseConverter] = converters or [
            FlowchartConverter(),
            SequenceConverter(),
            ClassDiagramConverter(),
            MindmapConverter(),
        ]
        self._converter_map = {converter.diagram_type: converter for converter in self.converters}

    def analyze(self, text: str) -> ConversionPlan:
        """
        分析 ASCII 图并生成转换计划。

        参数:
            text: ASCII 图原始内容

        返回:
            ConversionPlan: 转换计划（含特征、得分与方案）
        """
        features = AsciiAnalyzer.analyze(text)
        scores = DiagramTypeDetector.detect(features)

        schemes: List[ConversionScheme] = []
        for score in scores:
            if score.confidence <= 0.0:
                continue
            converter = self._converter_map.get(score.diagram_type)
            if converter is None:
                continue
            try:
                mermaid = converter.convert(features)
            except Exception:
                mermaid = None
            if not mermaid:
                continue
            schemes.append(
                ConversionScheme(
                    scheme_id=f"scheme_{len(schemes) + 1}_{score.diagram_type}",
                    diagram_type=score.diagram_type,
                    confidence=score.confidence,
                    mermaid=mermaid,
                    summary=converter.summarize(mermaid),
                )
            )

        detected_type = schemes[0].diagram_type if schemes else "unknown"
        return ConversionPlan(
            features=features,
            detected_type=detected_type,
            scores=scores,
            schemes=tuple(schemes),
            original=text,
        )

    def convert(
        self,
        text: str,
        mode: str = "auto",
        selector: Optional[Callable[[ConversionPlan], Optional[ConversionScheme]]] = None,
        confidence_threshold: float = 0.30,
    ) -> Optional[ConversionScheme]:
        """
        将 ASCII 图转换为选中的 Mermaid 方案。

        参数:
            text: ASCII 图原始内容
            mode: 'auto' | 'interactive' | 'preview'
            selector: 交互选择回调
            confidence_threshold: 最低置信度，低于此值返回 None

        返回:
            Optional[ConversionScheme]: 选中的方案；无法转换时返回 None
        """
        plan = self.analyze(text)
        if plan.best is None or plan.best.confidence < confidence_threshold:
            return None
        return plan.select(mode=mode, selector=selector)

    @staticmethod
    def is_ascii_diagram(text: str) -> bool:
        """
        判断文本是否具备 ASCII 图结构。

        参数:
            text: 待检测文本

        返回:
            bool: 是否具备可识别的图结构
        """
        features = AsciiAnalyzer.analyze(text)
        if not features.has_structure:
            return False
        # 至少需要两类结构证据，避免误判普通文本
        # 方框与深层树属于强证据（计 2 分）
        max_tree_depth = max((n.depth for n in features.tree_nodes), default=0)
        evidence = sum(
            [
                2 if features.boxes else 0,
                bool(features.arrows),
                bool(features.lifelines),
                bool(features.messages),
                bool(features.class_boxes),
                2 if max_tree_depth >= 2 else (1 if len(features.tree_nodes) >= 2 else 0),
            ]
        )
        return evidence >= 2


def convert_ascii_to_mermaid(
    text: str,
    mode: str = "auto",
    confidence_threshold: float = 0.30,
) -> Optional[str]:
    """
    便捷函数：将 ASCII 图转换为 Mermaid 代码。

    参数:
        text: ASCII 图原始内容
        mode: 'auto' | 'interactive' | 'preview'
        confidence_threshold: 最低置信度

    返回:
        Optional[str]: Mermaid 代码；无法转换时返回 None
    """
    service = AsciiToMermaidService()
    scheme = service.convert(
        text,
        mode=mode,
        confidence_threshold=confidence_threshold,
    )
    return scheme.mermaid if scheme else None
