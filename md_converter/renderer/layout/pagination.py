"""
Pagination - 按内容类型分页策略（第八章）

V1.5 废弃单一 Pagination State Machine，采用按内容类型分策略体系。
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .content_analyzer import ContentProfile
from .layout_plan import ContentType
from .themes_v15_protocol import ThemeProtocol


class PaginationPolicyResolver:
    """
    将 ContentProfile 映射为分页指令。

    依据第八章 8.1 策略总览：
        - Heading: Keep Together + Keep with Next
        - Paragraph: 允许拆分 + Widow/Orphan 控制
        - Table: 允许拆分 + 重复表头
        - Figure: Keep Together + 不足时移到下一页
        - Code Short (<=25): 整块同页；Code Long: 按行拆分
        - ASCII: 禁止拆分 + 禁止换行
        - URL: 允许在分隔符断行
    """

    def __init__(self, theme: Optional[ThemeProtocol] = None):
        self.theme = theme

    def resolve(self, profile: ContentProfile) -> Dict[str, Any]:
        """解析单个内容画像的分页策略。"""
        policy = self._theme_policy(profile.content_type)
        return policy

    def _theme_policy(self, content_type: ContentType) -> Dict[str, Any]:
        """从主题获取分页策略；无主题时使用内置默认。"""
        if self.theme is not None and hasattr(self.theme, "pagination_policy"):
            try:
                key = self._theme_key(content_type)
                return dict(self.theme.pagination_policy(key))
            except Exception:
                pass
        return self._default_policy(content_type)

    def _theme_key(self, content_type: ContentType) -> str:
        mapping = {
            ContentType.HEADING: "heading",
            ContentType.PROSE_CJK: "paragraph",
            ContentType.PROSE_LATIN: "paragraph",
            ContentType.PROSE_MIXED: "paragraph",
            ContentType.LIST: "list",
            ContentType.QUOTE: "paragraph",
            ContentType.TABLE_GENERAL: "table",
            ContentType.TABLE_FINANCIAL: "table",
            ContentType.TABLE_CODE: "table",
            ContentType.CODE_SHORT: "code",
            ContentType.CODE_LONG: "code",
            ContentType.ASCII_DIAGRAM: "ascii",
            ContentType.FIGURE: "figure",
            ContentType.URL: "url",
        }
        return mapping.get(content_type, "paragraph")

    def _default_policy(self, content_type: ContentType) -> Dict[str, Any]:
        policies = {
            ContentType.HEADING: {
                "keep_with_next": True,
                "keep_together": True,
                "allow_split": False,
            },
            ContentType.PROSE_CJK: {
                "keep_together": False,
                "allow_split": True,
                "widow_orphan_control": True,
            },
            ContentType.PROSE_LATIN: {
                "keep_together": False,
                "allow_split": True,
                "widow_orphan_control": True,
            },
            ContentType.PROSE_MIXED: {
                "keep_together": False,
                "allow_split": True,
                "widow_orphan_control": True,
            },
            ContentType.LIST: {
                "keep_together": False,
                "allow_split": True,
            },
            ContentType.QUOTE: {
                "keep_together": False,
                "allow_split": True,
            },
            ContentType.TABLE_GENERAL: {
                "keep_together": False,
                "allow_split": True,
                "split_rows_across_pages": True,
                "repeat_header": True,
            },
            ContentType.TABLE_FINANCIAL: {
                "keep_together": False,
                "allow_split": True,
                "split_rows_across_pages": True,
                "repeat_header": True,
            },
            ContentType.TABLE_CODE: {
                "keep_together": False,
                "allow_split": True,
                "split_rows_across_pages": True,
                "repeat_header": True,
            },
            ContentType.CODE_SHORT: {
                "keep_together": True,
                "allow_split": False,
                "max_lines_per_page": None,
            },
            ContentType.CODE_LONG: {
                "keep_together": False,
                "allow_split": True,
                "max_lines_per_page": 45,
            },
            ContentType.ASCII_DIAGRAM: {
                "keep_together": True,
                "allow_split": False,
                "no_wrap": True,
            },
            ContentType.FIGURE: {
                "keep_together": True,
                "allow_split": False,
                "move_to_next_page_if_insufficient": True,
            },
            ContentType.URL: {
                "keep_together": False,
                "allow_split": True,
                "break_points": ["/", ".", "-", "_", "?", "&", "="],
            },
        }
        return dict(policies.get(content_type, {"keep_together": False, "allow_split": True}))
