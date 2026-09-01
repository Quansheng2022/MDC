"""
Layout Package - V1.5 布局决策模块

依据 Doc/Default_theme_设计文档.md（第七章 LayoutPlan）实现。

职责边界:
    - decision_engine: AST -> LayoutPlan（决策与渲染分离）
    - content_analyzer: 内容类型分类
    - pagination: 按内容类型分页策略
    - section_manager: Section 决策（Portrait/Landscape）
    - validity_gate: 用户显式意图过滤（P0）
    - static_qa / rendered_qa: 双层 Layout QA
    - repair_strategy: Render -> Inspect -> Repair 闭环
"""

from .content_analyzer import ContentAnalyzer, ContentProfile
from .decision_engine import DecisionEngine
from .layout_plan import BlockPlan, ContentType, LayoutPlan, SectionPlan
from .pagination import PaginationPolicyResolver
from .rendered_qa import RenderedQA
from .repair_strategy import RepairStrategy
from .section_manager import SectionManager
from .static_qa import StaticQA, StaticQAResult
from .validity_gate import ValidityGate

__all__ = [
    "BlockPlan",
    "ContentAnalyzer",
    "ContentProfile",
    "ContentType",
    "DecisionEngine",
    "LayoutPlan",
    "PaginationPolicyResolver",
    "RenderedQA",
    "RepairStrategy",
    "SectionManager",
    "SectionPlan",
    "StaticQA",
    "StaticQAResult",
    "ValidityGate",
]
