"""
Repair Strategy - Render -> Inspect -> Repair 闭环（第四章 4.1 / P0-07）

根据 QA 结果调整 LayoutPlan，然后重新渲染。

P0-07 约束:
    - Repair 不允许修改 AST semantic content，只能调整 LayoutPlan。
    - 任何被 Repair 的 DOCX 至少再经过一次 RenderedQA（由编译器闭环保证）。
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Dict, List, Optional

from .layout_plan import LayoutPlan
from .rendered_qa import RenderedQAResult
from .static_qa import StaticQAResult

REPAIRABLE_CODES = ("table_clipping", "orphan_heading")


class RepairStrategy:
    """
    根据 QA 结果生成修订后的 LayoutPlan。

    支持的修复:
        - 表格溢出 -> 标记 Landscape / 允许拆分
        - 长代码 -> 允许拆分 + 每页最大行数
        - 孤立标题 -> Keep with Next
    """

    def __init__(self, max_repair_iterations: int = 2):
        self.max_repair_iterations = max_repair_iterations

    def can_repair(
        self,
        plan: LayoutPlan,
        static_result: StaticQAResult,
        rendered_result: RenderedQAResult,
    ) -> bool:
        """
        判断是否存在可用修复策略。

        返回:
            bool: 存在至少一个可应用策略且能实际改变 Plan 时为 True
        """
        issues = list(static_result.warnings) + list(rendered_result.warnings)
        for issue in issues:
            if issue.get("code") in REPAIRABLE_CODES and self._find_targets(plan, issue):
                return True
        return False

    @staticmethod
    def select_strategy(issue: Dict[str, Any]) -> str:
        """根据 issue code 返回修复策略名。"""
        code = issue.get("code")
        if code == "table_clipping":
            return "table_landscape"
        if code == "orphan_heading":
            return "heading_keep_with_next"
        return "none"

    def first_repairable_issue(
        self,
        static_result: StaticQAResult,
        rendered_result: RenderedQAResult,
    ) -> Optional[Dict[str, Any]]:
        """返回第一个可修复的 issue。"""
        issues = list(static_result.warnings) + list(rendered_result.warnings)
        return next((issue for issue in issues if issue.get("code") in REPAIRABLE_CODES), None)

    def repair(
        self,
        plan: LayoutPlan,
        static_result: StaticQAResult,
        rendered_result: RenderedQAResult,
    ) -> LayoutPlan:
        """
        生成修订后的 LayoutPlan。

        参数:
            plan: 原始布局计划
            static_result: Static QA 结果
            rendered_result: Rendered QA 结果

        返回:
            LayoutPlan: 修订后的布局计划
        """
        blocks = list(plan.blocks)
        changed = False
        changed_ids: List[str] = []
        strategies: List[str] = []

        for issue in rendered_result.warnings:
            if issue.get("code") == "table_clipping":
                for idx, block in enumerate(blocks):
                    if block.type.value.startswith("table"):
                        if not block.landscape:
                            changed_ids.append(block.id)
                            strategies.append("table_landscape")
                            blocks[idx] = replace(
                                block,
                                landscape=True,
                                allow_split=True,
                                metadata={**block.metadata, "repaired": "table_landscape"},
                            )
                            changed = True

        for issue in static_result.warnings + rendered_result.warnings:
            if issue.get("code") == "orphan_heading":
                for idx, block in enumerate(blocks):
                    if block.type.value == "heading":
                        if not block.keep_with_next:
                            changed_ids.append(block.id)
                            strategies.append("heading_keep_with_next")
                            blocks[idx] = replace(
                                block,
                                keep_with_next=True,
                                metadata={**block.metadata, "repaired": "heading_keep_with_next"},
                            )
                            changed = True

        if not changed:
            return plan

        return LayoutPlan(
            version=plan.version,
            sections=list(plan.sections),
            blocks=blocks,
            metadata={
                **plan.metadata,
                "repaired": True,
                "repair_strategies": sorted(set(strategies)),
                "changed_blocks": changed_ids,
            },
        )

    def _find_targets(self, plan: LayoutPlan, issue: Dict[str, Any]) -> List[Any]:
        """返回 issue 可作用的 block 列表。"""
        code = issue.get("code")
        if code == "table_clipping":
            return [b for b in plan.blocks if b.type.value.startswith("table") and not b.landscape]
        if code == "orphan_heading":
            return [b for b in plan.blocks if b.type.value == "heading" and not b.keep_with_next]
        return []
