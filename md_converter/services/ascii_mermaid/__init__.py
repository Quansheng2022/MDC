"""
ASCII → Mermaid 自动转换服务

基于规则引擎的 ASCII 图识别与转换：
    - 流程图 (flowchart)
    - 时序图 (sequence)
    - 类图 (class)
    - 思维导图 (mindmap)
    - 类型自动检测
    - 多方案生成与交互式选择
"""

from .analyzer import AsciiAnalyzer, is_drawing_char
from .detector import DiagramTypeDetector
from .model import (
    Arrow,
    Box,
    ClassBox,
    ClassRelation,
    ClassSection,
    ConversionPlan,
    ConversionScheme,
    DiagramFeatures,
    Lifeline,
    Message,
    TreeNode,
    TypeScore,
)
from .selector import auto_select, interactive_select
from .service import (
    AsciiToMermaidService,
    convert_ascii_to_mermaid,
)

__all__ = [
    "Arrow",
    "AsciiAnalyzer",
    "AsciiToMermaidService",
    "Box",
    "ClassBox",
    "ClassRelation",
    "ClassSection",
    "ConversionPlan",
    "ConversionScheme",
    "DiagramFeatures",
    "DiagramTypeDetector",
    "Lifeline",
    "Message",
    "TreeNode",
    "TypeScore",
    "auto_select",
    "convert_ascii_to_mermaid",
    "interactive_select",
    "is_drawing_char",
]
