"""
Inline State - 行内样式状态栈管理

使用栈结构管理行内元素的嵌套样式，支持粗体、斜体、代码、链接等样式的嵌套组合。
正确处理 **AAA *BBB* CCC** 这类嵌套样式。
"""

from copy import copy
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from docx.shared import RGBColor


@dataclass
class InlineStyle:
    """
    行内样式状态。

    属性:
        bold: 是否加粗
        italic: 是否斜体
        underline: 是否下划线
        code: 是否为代码
        link: 链接 URL（如果有）
        color: 文字颜色
        highlight: 高亮颜色
        font_name: 字体名称
        font_size: 字号
        subscript: 是否下标
        superscript: 是否上标
        strikethrough: 是否删除线
    """

    bold: bool = False
    italic: bool = False
    underline: bool = False
    code: bool = False
    link: Optional[str] = None
    color: Optional[RGBColor] = None
    highlight: Optional[RGBColor] = None
    font_name: Optional[str] = None
    font_size: Optional[int] = None
    subscript: bool = False
    superscript: bool = False
    strikethrough: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典（用于 WordWriter）。

        返回:
            Dict[str, Any]: 样式字典
        """
        result = {
            "bold": self.bold,
            "italic": self.italic,
            "underline": self.underline,
        }

        if self.code:
            # 代码样式：使用等宽字体
            result["font_name"] = "Consolas"
            result["font_size"] = 10

        if self.link:
            # 链接样式：蓝色、下划线
            result["color"] = self.color or RGBColor(0x00, 0x00, 0xFF)
            result["underline"] = True

        if self.color:
            result["color"] = self.color

        if self.highlight:
            result["highlight"] = self.highlight

        if self.font_name:
            result["font_name"] = self.font_name

        if self.font_size:
            result["font_size"] = self.font_size

        if self.subscript or self.superscript:
            result["subscript"] = self.subscript
            result["superscript"] = self.superscript

        if self.strikethrough:
            result["strikethrough"] = self.strikethrough

        return result

    def merge(self, other: "InlineStyle") -> "InlineStyle":
        """
        合并两个样式（后者覆盖前者）。

        参数:
            other: 要合并的样式

        返回:
            InlineStyle: 合并后的新样式
        """
        merged = copy(self)

        # 布尔值：如果 other 为 True 则覆盖
        if other.bold:
            merged.bold = True
        if other.italic:
            merged.italic = True
        if other.underline:
            merged.underline = True
        if other.code:
            merged.code = True
        if other.subscript:
            merged.subscript = True
        if other.superscript:
            merged.superscript = True
        if other.strikethrough:
            merged.strikethrough = True

        # 字符串/对象：直接覆盖（如果存在）
        if other.link is not None:
            merged.link = other.link
        if other.color is not None:
            merged.color = other.color
        if other.highlight is not None:
            merged.highlight = other.highlight
        if other.font_name is not None:
            merged.font_name = other.font_name
        if other.font_size is not None:
            merged.font_size = other.font_size

        return merged

    def __repr__(self) -> str:
        attrs = []
        if self.bold:
            attrs.append("bold")
        if self.italic:
            attrs.append("italic")
        if self.underline:
            attrs.append("underline")
        if self.code:
            attrs.append("code")
        if self.link:
            attrs.append(f"link={self.link}")
        return f"InlineStyle({', '.join(attrs)})" if attrs else "InlineStyle()"


class InlineState:
    """
    行内样式状态栈。

    维护一个样式栈，支持 push/pop 操作，用于处理嵌套样式。
    每次 push 时基于当前栈顶样式创建新样式。

    示例:
        >>> state = InlineState()
        >>> state.push(bold=True)
        >>> state.current_style()  # bold=True
        >>> state.push(italic=True)
        >>> state.current_style()  # bold=True, italic=True
        >>> state.pop()
        >>> state.current_style()  # bold=True
        >>> state.pop()
        >>> state.current_style()  # {}
    """

    def __init__(self):
        """初始化样式栈，包含一个基础空样式"""
        self.stack: List[InlineStyle] = [InlineStyle()]

    def push(self, **kwargs) -> None:
        """
        推入新样式。

        基于当前栈顶样式创建新样式，并应用 kwargs 中的属性。

        参数:
            **kwargs: 样式属性（bold, italic, underline, code, link, color, highlight, font_name, font_size, subscript, superscript, strikethrough）

        示例:
            >>> state.push(bold=True)
            >>> state.push(italic=True, link="https://example.com")
        """
        current = self.stack[-1]
        # 浅拷贝即可：InlineStyle 为普通 dataclass，
        # 深拷贝 RGBColor 在 python-docx 1.2+ 中会失败
        new_style = copy(current)

        # 应用新属性
        for key, value in kwargs.items():
            if hasattr(new_style, key):
                setattr(new_style, key, value)

        self.stack.append(new_style)

    def pop(self) -> Optional[InlineStyle]:
        """
        弹出栈顶样式。

        返回:
            Optional[InlineStyle]: 弹出的样式，如果栈为空则返回 None
        """
        if len(self.stack) > 1:
            return self.stack.pop()
        return None

    def current_style(self) -> Dict[str, Any]:
        """
        获取当前样式（字典格式）。

        返回:
            Dict[str, Any]: 当前样式字典，可直接用于 WordWriter
        """
        return self.stack[-1].to_dict()

    def current_style_object(self) -> InlineStyle:
        """
        获取当前样式对象。

        返回:
            InlineStyle: 当前样式对象
        """
        return self.stack[-1]

    def depth(self) -> int:
        """
        获取栈深度。

        返回:
            int: 栈深度
        """
        return len(self.stack) - 1  # 减去基础样式

    def is_empty(self) -> bool:
        """
        检查是否为空（只有基础样式）。

        返回:
            bool: 是否为空
        """
        return len(self.stack) == 1

    def reset(self) -> None:
        """重置样式栈"""
        self.stack = [InlineStyle()]

    def get_nested_styles(self) -> List[InlineStyle]:
        """
        获取所有嵌套样式（从内到外）。

        返回:
            List[InlineStyle]: 样式列表（不包含基础样式）
        """
        return self.stack[1:]

    def has_style(self, style_name: str) -> bool:
        """
        检查当前是否包含指定样式。

        参数:
            style_name: 样式名称 (bold, italic, etc.)

        返回:
            bool: 是否包含该样式
        """
        return bool(getattr(self.stack[-1], style_name, False))

    def __repr__(self) -> str:
        return f"InlineState(depth={self.depth()}, current={self.current_style()})"


# ============================================================
# 工厂函数
# ============================================================


def create_inline_style(
    bold: bool = False,
    italic: bool = False,
    underline: bool = False,
    code: bool = False,
    link: Optional[str] = None,
    color: Optional[RGBColor] = None,
    highlight: Optional[RGBColor] = None,
    font_name: Optional[str] = None,
    font_size: Optional[int] = None,
) -> InlineStyle:
    """
    创建行内样式对象的便捷函数。

    参数:
        bold: 是否加粗
        italic: 是否斜体
        underline: 是否下划线
        code: 是否为代码
        link: 链接 URL
        color: 文字颜色
        highlight: 高亮颜色
        font_name: 字体名称
        font_size: 字号

    返回:
        InlineStyle: 样式对象
    """
    return InlineStyle(
        bold=bold,
        italic=italic,
        underline=underline,
        code=code,
        link=link,
        color=color,
        highlight=highlight,
        font_name=font_name,
        font_size=font_size,
    )


# ============================================================
# 预定义样式
# ============================================================


def get_bold_style() -> InlineStyle:
    """获取粗体样式"""
    return InlineStyle(bold=True)


def get_italic_style() -> InlineStyle:
    """获取斜体样式"""
    return InlineStyle(italic=True)


def get_code_style() -> InlineStyle:
    """获取代码样式"""
    return InlineStyle(code=True, font_name="Consolas", font_size=10)


def get_link_style(href: str) -> InlineStyle:
    """获取链接样式"""
    return InlineStyle(
        link=href,
        color=RGBColor(0x00, 0x00, 0xFF),
        underline=True,
    )


def get_strikethrough_style() -> InlineStyle:
    """获取删除线样式"""
    return InlineStyle(strikethrough=True)


def get_superscript_style() -> InlineStyle:
    """获取上标样式"""
    return InlineStyle(superscript=True)


def get_subscript_style() -> InlineStyle:
    """获取下标样式"""
    return InlineStyle(subscript=True)


# ============================================================
# 样式组合
# ============================================================


def combine_styles(*styles: InlineStyle) -> InlineStyle:
    """
    合并多个样式。

    参数:
        *styles: 样式对象列表

    返回:
        InlineStyle: 合并后的样式

    示例:
        >>> bold = get_bold_style()
        >>> italic = get_italic_style()
        >>> combined = combine_styles(bold, italic)
        >>> # combined.bold = True, combined.italic = True
    """
    result = InlineStyle()
    for style in styles:
        result = result.merge(style)
    return result


def style_from_dict(data: Dict[str, Any]) -> InlineStyle:
    """
    从字典创建样式。

    参数:
        data: 样式字典

    返回:
        InlineStyle: 样式对象
    """
    return InlineStyle(
        bold=data.get("bold", False),
        italic=data.get("italic", False),
        underline=data.get("underline", False),
        code=data.get("code", False),
        link=data.get("link"),
        color=data.get("color"),
        highlight=data.get("highlight"),
        font_name=data.get("font_name"),
        font_size=data.get("font_size"),
        subscript=data.get("subscript", False),
        superscript=data.get("superscript", False),
        strikethrough=data.get("strikethrough", False),
    )
