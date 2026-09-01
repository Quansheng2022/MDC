"""
Validity Gate - 用户显式意图过滤（第五章 5.2，P0 前置过滤器）

用户显式指定必须经过 Validity Gate 验证；非法意图忽略并告警。

非法意图（invalid_intents）:
    - body_font_size < 8pt
    - heading_font_size < 10pt
    - table_font_size < 6pt
    - margin < 0.5in
    - content_deletion
    - semantic_destruction
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ValidityResult:
    """Validity Gate 结果。"""

    accepted: Dict[str, Any] = field(default_factory=dict)
    rejected: Dict[str, Any] = field(default_factory=dict)
    fallbacks: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.rejected


class ValidityGate:
    """
    P0 用户意图过滤器。

    用法:
        gate = ValidityGate(body_min_pt=10, heading_min_pt=10,
                            table_min_pt=8.5, margin_min_in=0.5)
        result = gate.validate({"body_font_size": 9})
        # result.rejected == {"body_font_size": 9}
        # result.fallbacks == {"body_font_size": 10.5}
    """

    def __init__(
        self,
        body_min_pt: float = 10.0,
        heading_min_pt: float = 10.0,
        table_min_pt: float = 8.5,
        margin_min_in: float = 0.5,
        fallback_body_pt: float = 10.5,
        fallback_heading_pt: float = 14.0,
        fallback_table_pt: float = 9.5,
        fallback_margin_in: float = 1.0,
    ):
        self.body_min_pt = body_min_pt
        self.heading_min_pt = heading_min_pt
        self.table_min_pt = table_min_pt
        self.margin_min_in = margin_min_in
        self.fallback_body_pt = fallback_body_pt
        self.fallback_heading_pt = fallback_heading_pt
        self.fallback_table_pt = fallback_table_pt
        self.fallback_margin_in = fallback_margin_in

    @classmethod
    def from_theme(cls, theme: Any) -> "ValidityGate":
        """从主题可读性配置创建 Validity Gate。"""
        minimums = theme.readability_minimums if hasattr(theme, "readability_minimums") else {}
        return cls(
            body_min_pt=minimums.get("body_font", 10.0),
            heading_min_pt=minimums.get("body_font", 10.0),
            table_min_pt=minimums.get("table_font", 8.5),
            margin_min_in=0.5,
        )

    def validate(self, overrides: Dict[str, Any]) -> ValidityResult:
        """
        验证用户显式意图。

        参数:
            overrides: 用户布局覆盖项

        返回:
            ValidityResult: 过滤结果
        """
        result = ValidityResult()
        for key, value in overrides.items():
            if self._is_invalid(key, value):
                result.rejected[key] = value
                fallback = self._fallback(key)
                result.fallbacks[key] = fallback
                result.warnings.append(
                    f"User intent rejected: {key}={value!r} violates readability "
                    f"minimum; falling back to {fallback!r}"
                )
            else:
                result.accepted[key] = value
        return result

    def _is_invalid(self, key: str, value: Any) -> bool:
        """判断覆盖项是否非法。"""
        if key in ("content_deletion", "semantic_destruction"):
            return bool(value)
        if key in ("body_font_size", "body_font"):
            return self._to_pt(value) < self.body_min_pt
        if key in ("heading_font_size", "heading_font"):
            return self._to_pt(value) < self.heading_min_pt
        if key in ("table_font_size", "table_font"):
            return self._to_pt(value) < self.table_min_pt
        if key in ("margin", "page_margin"):
            return self._to_inches(value) < self.margin_min_in
        return False

    def _fallback(self, key: str) -> Any:
        if key in ("body_font_size", "body_font"):
            return self.fallback_body_pt
        if key in ("heading_font_size", "heading_font"):
            return self.fallback_heading_pt
        if key in ("table_font_size", "table_font"):
            return self.fallback_table_pt
        if key in ("margin", "page_margin"):
            return self.fallback_margin_in
        return None

    @staticmethod
    def _to_pt(value: Any) -> float:
        try:
            text = str(value).strip().lower()
            if text.endswith("pt"):
                return float(text[:-2].strip())
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _to_inches(value: Any) -> float:
        try:
            text = str(value).strip().lower()
            if text.endswith("in"):
                return float(text[:-2].strip())
            if text.endswith("cm"):
                return float(text[:-2].strip()) / 2.54
            return float(value)
        except (TypeError, ValueError):
            return 0.0
