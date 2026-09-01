"""
Theme Protocol - 布局模块使用的主题协议

避免 layout 包直接依赖 themes.v15_theme，保持单向依赖：
layout -> 协议；themes -> 无依赖。
"""

from __future__ import annotations

from typing import Any, Dict, Protocol, runtime_checkable


@runtime_checkable
class ThemeProtocol(Protocol):
    """布局模块所需的最小主题接口。"""

    @property
    def body_size(self) -> float: ...

    @property
    def table_font_size(self) -> float: ...

    @property
    def readability_minimums(self) -> Dict[str, float]: ...

    def pagination_policy(self, content_type: str) -> Dict[str, Any]: ...

    @property
    def cjk_threshold(self) -> float: ...

    @property
    def latin_threshold(self) -> float: ...
