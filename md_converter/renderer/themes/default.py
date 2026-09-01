"""
Default Theme - 默认主题配置

提供文档的默认样式配置，包括字体、颜色、间距等。
所有样式值可在创建主题时自定义。
"""

from dataclasses import dataclass, field
from typing import Any, Dict

from docx.shared import Cm, Pt, RGBColor


@dataclass
class DefaultTheme:
    """
    默认主题配置。

    包含文档的所有样式配置，包括字体、颜色、间距、表格样式等。
    所有属性都是可选的，可以使用默认值或自定义。

    属性:
        # 字体配置
        heading_font: 标题字体
        body_font: 正文字体
        code_font: 代码字体

        # 颜色配置
        heading_color: 标题颜色（默认黑色）
        body_color: 正文颜色（默认黑色）
        link_color: 链接颜色（默认蓝色）
        code_color: 代码颜色（默认深红色）
        table_header_bg: 表头背景色（默认深蓝）
        table_header_fg: 表头文字颜色（默认白色）
        code_bg: 代码块背景色（默认浅灰）

        # 字号配置（单位：磅）
        heading_1_size: 一级标题字号
        heading_2_size: 二级标题字号
        heading_3_size: 三级标题字号
        heading_4_size: 四级标题字号
        heading_5_size: 五级标题字号
        heading_6_size: 六级标题字号
        body_size: 正文字号
        code_size: 代码字号

        # 间距配置（单位：磅）
        heading_space_before: 标题段前间距
        heading_space_after: 标题段后间距
        paragraph_space_after: 段落段后间距
        list_item_space_after: 列表项段后间距
        code_space_before: 代码块段前间距
        code_space_after: 代码块段后间距

        # 缩进配置（单位：厘米）
        code_indent: 代码块缩进
        blockquote_indent: 引用块缩进
        list_indent_base: 列表项基础缩进

        # 表格配置
        table_style: 表格样式名称
        table_cell_padding: 单元格内边距（单位：磅）

        # 页面配置
        page_margins: 页面边距（单位：厘米）

        # 其他配置
        enable_smart_quotes: 是否启用智能引号
        enable_ligatures: 是否启用连字
    """

    # ============================================================
    # 字体配置
    # ============================================================

    heading_font: str = "Arial"
    body_font: str = "Calibri"
    code_font: str = "Consolas"

    # ============================================================
    # 颜色配置
    # ============================================================

    heading_color: RGBColor = RGBColor(0x00, 0x00, 0x00)
    body_color: RGBColor = RGBColor(0x00, 0x00, 0x00)
    link_color: RGBColor = RGBColor(0x00, 0x00, 0xFF)
    code_color: RGBColor = RGBColor(0x80, 0x00, 0x00)
    table_header_bg: RGBColor = RGBColor(0x2F, 0x54, 0x96)
    table_header_fg: RGBColor = RGBColor(0xFF, 0xFF, 0xFF)
    code_bg: RGBColor = RGBColor(0xF0, 0xF0, 0xF0)

    # ============================================================
    # 字号配置（单位：磅）
    # ============================================================

    heading_1_size: int = 20
    heading_2_size: int = 16
    heading_3_size: int = 14
    heading_4_size: int = 14
    heading_5_size: int = 14
    heading_6_size: int = 14
    body_size: int = 11
    code_size: int = 10

    # ============================================================
    # 间距配置（单位：磅）
    # ============================================================

    heading_space_before: int = 12
    heading_space_after: int = 6
    paragraph_space_after: int = 6
    list_item_space_after: int = 3
    code_space_before: int = 6
    code_space_after: int = 6

    # ============================================================
    # 缩进配置（单位：厘米）
    # ============================================================

    code_indent: float = 0.5
    blockquote_indent: float = 1.0
    list_indent_base: float = 0.5

    # ============================================================
    # 表格配置
    # ============================================================

    table_style: str = "Table Grid"
    table_cell_padding: Dict[str, float] = field(default_factory=lambda: {
        "top": 2.0,
        "bottom": 2.0,
        "left": 3.0,
        "right": 3.0,
    })

    # ============================================================
    # 页面配置（单位：厘米）
    # ============================================================

    page_margins: Dict[str, float] = field(default_factory=lambda: {
        "top": 2.5,
        "bottom": 2.5,
        "left": 2.5,
        "right": 2.5,
    })
    page_width: str = "A4"  # A4, Letter, Legal, etc.

    # ============================================================
    # 其他配置
    # ============================================================

    enable_smart_quotes: bool = True
    enable_ligatures: bool = False

    # ============================================================
    # 辅助方法
    # ============================================================

    def get_heading_size(self, level: int) -> int:
        """
        获取指定级别的标题字号。

        参数:
            level: 标题级别 (1-6)

        返回:
            int: 字号（磅）
        """
        sizes = {
            1: self.heading_1_size,
            2: self.heading_2_size,
            3: self.heading_3_size,
            4: self.heading_4_size,
            5: self.heading_5_size,
            6: self.heading_6_size,
        }
        return sizes.get(level, self.body_size)

    def get_heading_font(self, level: int) -> str:
        """
        获取指定级别的标题字体。

        参数:
            level: 标题级别 (1-6)

        返回:
            str: 字体名称
        """
        # 所有标题使用相同字体，可自定义扩展
        return self.heading_font

    def get_heading_color(self, level: int) -> RGBColor:
        """
        获取指定级别的标题颜色。

        参数:
            level: 标题级别 (1-6)

        返回:
            RGBColor: 颜色
        """
        # 所有标题使用相同颜色，可自定义扩展
        return self.heading_color

    def get_heading_style(self, level: int) -> Dict[str, Any]:
        """
        获取完整的标题样式字典。

        参数:
            level: 标题级别 (1-6)

        返回:
            Dict[str, Any]: 样式字典
        """
        return {
            "font_name": self.get_heading_font(level),
            "font_size": self.get_heading_size(level),
            "bold": True,
            "color": self.get_heading_color(level),
            "space_before": Pt(self.heading_space_before),
            "space_after": Pt(self.heading_space_after),
        }

    def get_paragraph_style(self) -> Dict[str, Any]:
        """
        获取段落样式字典。

        返回:
            Dict[str, Any]: 样式字典
        """
        return {
            "font_name": self.body_font,
            "font_size": self.body_size,
            "color": self.body_color,
            "space_after": Pt(self.paragraph_space_after),
        }

    def get_code_style(self) -> Dict[str, Any]:
        """
        获取代码样式字典。

        返回:
            Dict[str, Any]: 样式字典
        """
        return {
            "font_name": self.code_font,
            "font_size": self.code_size,
            "color": self.code_color,
            "background": self.code_bg,
            "indent": Cm(self.code_indent),
            "space_before": Pt(self.code_space_before),
            "space_after": Pt(self.code_space_after),
        }

    def get_list_style(self, depth: int) -> Dict[str, Any]:
        """
        获取列表样式字典。

        参数:
            depth: 列表嵌套深度

        返回:
            Dict[str, Any]: 样式字典
        """
        return {
            "font_name": self.body_font,
            "font_size": self.body_size,
            "color": self.body_color,
            "left_indent": Cm(self.list_indent_base * (depth + 1)),
            "space_after": Pt(self.list_item_space_after),
        }

    def get_table_style(self) -> Dict[str, Any]:
        """
        获取表格样式字典。

        返回:
            Dict[str, Any]: 样式字典
        """
        return {
            "style_name": self.table_style,
            "header_bg": self.table_header_bg,
            "header_fg": self.table_header_fg,
            "cell_padding": self.table_cell_padding,
        }

    def get_blockquote_style(self) -> Dict[str, Any]:
        """
        获取引用块样式字典。

        返回:
            Dict[str, Any]: 样式字典
        """
        return {
            "font_name": self.body_font,
            "font_size": self.body_size,
            "color": RGBColor(0x55, 0x55, 0x55),
            "left_indent": Cm(self.blockquote_indent),
            "border": {
                "left": {
                    "style": "single",
                    "width": 4,
                    "color": "auto",
                }
            },
        }

    def get_page_margins(self) -> Dict[str, float]:
        """
        获取页面边距配置。

        返回:
            Dict[str, float]: 页面边距（厘米）
        """
        return self.page_margins

    # ============================================================
    # 序列化方法
    # ============================================================

    def to_dict(self) -> Dict[str, Any]:
        """
        将主题转换为字典。

        返回:
            Dict[str, Any]: 主题字典
        """
        return {
            "heading_font": self.heading_font,
            "body_font": self.body_font,
            "code_font": self.code_font,
            "heading_color": self.heading_color.rgb,
            "body_color": self.body_color.rgb,
            "link_color": self.link_color.rgb,
            "code_color": self.code_color.rgb,
            "table_header_bg": self.table_header_bg.rgb,
            "table_header_fg": self.table_header_fg.rgb,
            "code_bg": self.code_bg.rgb,
            "heading_1_size": self.heading_1_size,
            "heading_2_size": self.heading_2_size,
            "heading_3_size": self.heading_3_size,
            "heading_4_size": self.heading_4_size,
            "heading_5_size": self.heading_5_size,
            "heading_6_size": self.heading_6_size,
            "body_size": self.body_size,
            "code_size": self.code_size,
            "heading_space_before": self.heading_space_before,
            "heading_space_after": self.heading_space_after,
            "paragraph_space_after": self.paragraph_space_after,
            "list_item_space_after": self.list_item_space_after,
            "code_space_before": self.code_space_before,
            "code_space_after": self.code_space_after,
            "code_indent": self.code_indent,
            "blockquote_indent": self.blockquote_indent,
            "list_indent_base": self.list_indent_base,
            "table_style": self.table_style,
            "table_cell_padding": self.table_cell_padding,
            "page_margins": self.page_margins,
            "page_width": self.page_width,
            "enable_smart_quotes": self.enable_smart_quotes,
            "enable_ligatures": self.enable_ligatures,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DefaultTheme":
        """
        从字典创建主题。

        参数:
            data: 主题字典

        返回:
            DefaultTheme: 主题实例
        """
        # 转换颜色值
        color_keys = [
            "heading_color", "body_color", "link_color",
            "code_color", "table_header_bg", "table_header_fg", "code_bg"
        ]
        for key in color_keys:
            if key in data:
                val = data[key]
                if isinstance(val, int):
                    data[key] = RGBColor(val)
                elif isinstance(val, str) and val.startswith("#"):
                    data[key] = RGBColor.from_string(val)

        return cls(**data)


# ============================================================
# 预定义主题
# ============================================================

def get_github_theme() -> DefaultTheme:
    """
    获取 GitHub 风格主题。

    返回:
        DefaultTheme: GitHub 风格主题
    """
    return DefaultTheme(
        heading_font="Segoe UI",
        body_font="Segoe UI",
        code_font="Consolas",
        heading_color=RGBColor(0x24, 0x29, 0x2E),
        body_color=RGBColor(0x24, 0x29, 0x2E),
        table_header_bg=RGBColor(0xF6, 0xF8, 0xFA),
        table_header_fg=RGBColor(0x24, 0x29, 0x2E),
        code_bg=RGBColor(0xF6, 0xF8, 0xFA),
        heading_1_size=20,
        heading_2_size=18,
        heading_3_size=16,
        heading_4_size=14,
        heading_5_size=12,
        heading_6_size=11,
        body_size=11,
        table_style="Light Shading Accent 1",
    )


def get_academic_theme() -> DefaultTheme:
    """
    获取学术风格主题。

    返回:
        DefaultTheme: 学术风格主题
    """
    return DefaultTheme(
        heading_font="Times New Roman",
        body_font="Times New Roman",
        code_font="Courier New",
        heading_color=RGBColor(0x00, 0x00, 0x00),
        body_color=RGBColor(0x00, 0x00, 0x00),
        table_header_bg=RGBColor(0x2F, 0x54, 0x96),
        table_header_fg=RGBColor(0xFF, 0xFF, 0xFF),
        code_bg=RGBColor(0xF0, 0xF0, 0xF0),
        heading_1_size=18,
        heading_2_size=16,
        heading_3_size=14,
        heading_4_size=12,
        heading_5_size=11,
        heading_6_size=10,
        body_size=12,
        table_style="Light Grid Accent 1",
    )


def get_corporate_theme() -> DefaultTheme:
    """
    获取企业风格主题。

    返回:
        DefaultTheme: 企业风格主题
    """
    return DefaultTheme(
        heading_font="Calibri",
        body_font="Calibri",
        code_font="Consolas",
        heading_color=RGBColor(0x00, 0x3B, 0x71),
        body_color=RGBColor(0x33, 0x33, 0x33),
        table_header_bg=RGBColor(0x00, 0x3B, 0x71),
        table_header_fg=RGBColor(0xFF, 0xFF, 0xFF),
        code_bg=RGBColor(0xF0, 0xF0, 0xF0),
        heading_1_size=20,
        heading_2_size=17,
        heading_3_size=15,
        heading_4_size=13,
        heading_5_size=12,
        heading_6_size=11,
        body_size=11,
        table_style="Table Grid",
    )


# ============================================================
# 主题工厂
# ============================================================

def create_theme(name: str, **kwargs) -> DefaultTheme:
    """
    根据名称创建主题。

    参数:
        name: 主题名称 ('default', 'github', 'academic', 'corporate')
        **kwargs: 覆盖的主题属性

    返回:
        DefaultTheme: 主题实例

    异常:
        ValueError: 如果主题名称未知
    """
    themes = {
        "default": DefaultTheme,
        "github": get_github_theme,
        "academic": get_academic_theme,
        "corporate": get_corporate_theme,
    }

    theme_fn = themes.get(name.lower())
    if theme_fn is None:
        raise ValueError(f"Unknown theme: {name}. Available: {', '.join(themes.keys())}")

    theme = theme_fn()
    for key, value in kwargs.items():
        if hasattr(theme, key):
            setattr(theme, key, value)

    return theme
