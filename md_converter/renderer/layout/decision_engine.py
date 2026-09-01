"""
Decision Engine - 布局决策引擎（第四章 4.2 / 第七章）

输出唯一产物 LayoutPlan。Renderer 仅负责执行 Plan。

流程:
    Semantic Analysis -> Content Analysis -> Layout Estimation
    -> Candidate Generation -> Constraint Filtering
    -> Decision / Priority Ranking -> LayoutPlan
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from ...ast.nodes import Document
from .content_analyzer import ContentAnalyzer, ContentProfile
from .layout_plan import (
    BlockPlan,
    LayoutPlan,
)
from .pagination import PaginationPolicyResolver
from .section_manager import SectionManager, estimate_table_width_cm
from .themes_v15_protocol import ThemeProtocol
from .validity_gate import ValidityGate, ValidityResult


class DecisionEngine:
    """
    将 AST 转换为 LayoutPlan。

    参数:
        theme: 主题（可选）
        analyzer: 内容分类器
        pagination: 分页策略解析器
        section_manager: Section 决策器
        validity_gate: 用户意图过滤器
    """

    def __init__(
        self,
        theme: Optional[ThemeProtocol] = None,
        analyzer: Optional[ContentAnalyzer] = None,
        pagination: Optional[PaginationPolicyResolver] = None,
        section_manager: Optional[SectionManager] = None,
        validity_gate: Optional[ValidityGate] = None,
    ):
        self.theme = theme
        self.analyzer = analyzer or ContentAnalyzer()
        self.pagination = pagination or PaginationPolicyResolver(theme)
        self.section_manager = section_manager or SectionManager(theme)
        self.validity_gate = validity_gate

    def build_plan(
        self,
        document: Document,
        user_overrides: Optional[Dict[str, Any]] = None,
    ) -> LayoutPlan:
        """
        构建 LayoutPlan。

        参数:
            document: AST 文档
            user_overrides: 用户显式布局意图（P0）

        返回:
            LayoutPlan: 布局计划
        """
        profiles = self.analyzer.analyze(document)
        sections = self.section_manager.build_sections(profiles)
        blocks = [self._build_block(p) for p in profiles]

        validity: Optional[ValidityResult] = None
        if user_overrides and self.validity_gate is not None:
            validity = self.validity_gate.validate(user_overrides)

        metadata: Dict[str, Any] = {
            "theme": self.theme.name if self.theme and hasattr(self.theme, "name") else "default",
            "block_count": len(blocks),
            "section_count": len(sections),
        }
        if validity is not None:
            metadata["user_intent"] = {
                "accepted": validity.accepted,
                "rejected": validity.rejected,
                "fallbacks": validity.fallbacks,
                "warnings": validity.warnings,
            }

        return LayoutPlan(
            version="1.5",
            sections=sections,
            blocks=blocks,
            metadata=metadata,
        )

    def _build_block(self, profile: ContentProfile) -> BlockPlan:
        """根据内容画像生成块级指令。"""
        policy = self.pagination.resolve(profile)
        keep_with_next = bool(policy.get("keep_with_next", False))
        keep_together = bool(policy.get("keep_together", False))
        allow_split = bool(policy.get("allow_split", False))
        widow = bool(policy.get("widow_orphan_control", False))
        repeat_header = bool(policy.get("repeat_header", False))
        max_lines = policy.get("max_lines_per_page")

        alignment = None
        landscape = False
        if profile.content_type.value.startswith("table") and profile.language is None:
            width = estimate_table_width_cm(profile)
            available = self.section_manager.geometry.portrait_content_width_cm
            buffer = 1.0
            if self.theme and hasattr(self.theme, "landscape_width_margin_buffer_cm"):
                buffer = self.theme.landscape_width_margin_buffer_cm
            if width > available + buffer:
                landscape = True

        metadata = dict(profile.metadata)
        metadata.update(
            {
                "cjk_ratio": profile.language.cjk_ratio if profile.language else None,
                "latin_ratio": profile.language.latin_ratio if profile.language else None,
                "table_column_types": profile.table_column_types,
            }
        )

        return BlockPlan(
            id=profile.node_id,
            type=profile.content_type,
            original_ast_id=profile.node_id,
            page_break_before=False,
            keep_together=keep_together,
            allow_split=allow_split,
            keep_with_next=keep_with_next,
            widow_orphan_control=widow,
            alignment_override=alignment,
            repeat_header=repeat_header,
            max_lines_per_page=max_lines,
            landscape=landscape,
            metadata=metadata,
        )
