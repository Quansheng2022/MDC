"""
Style Resolver - 样式解析器

将 AST 节点和主题配置转换为具体的样式字典。
负责所有样式决策，与 Renderer 和 Writer 解耦。
"""

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Dict, Optional

from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor

from .inline_state import InlineStyle
from .themes.default import DefaultTheme


@dataclass
class ParagraphStyle:
    """
    段落样式。

    属性:
        font_name: 字体名称
        font_size: 字号
        bold: 是否加粗
        italic: 是否斜体
        color: 文字颜色
        alignment: 对齐方式
        space_before: 段前间距
        space_after: 段后间距
        left_indent: 左缩进
        right_indent: 右缩进
        first_line_indent: 首行缩进
        line_spacing: 行距倍数
        background: 背景色
        border: 边框样式
    """

    font_name: Optional[str] = None
    font_size: Optional[int] = None
    bold: bool = False
    italic: bool = False
    color: Optional[RGBColor] = None
    alignment: Optional[int] = None  # WD_ALIGN_PARAGRAPH
    space_before: Optional[Pt] = None
    space_after: Optional[Pt] = None
    left_indent: Optional[Cm] = None
    right_indent: Optional[Cm] = None
    first_line_indent: Optional[Cm] = None
    line_spacing: Optional[float] = None
    background: Optional[RGBColor] = None
    border: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {}
        if self.font_name:
            result["font_name"] = self.font_name
        if self.font_size:
            result["font_size"] = self.font_size
        if self.bold:
            result["bold"] = self.bold
        if self.italic:
            result["italic"] = self.italic
        if self.color:
            result["color"] = self.color
        if self.alignment is not None:
            result["alignment"] = self.alignment
        if self.space_before:
            result["space_before"] = self.space_before
        if self.space_after:
            result["space_after"] = self.space_after
        if self.left_indent:
            result["left_indent"] = self.left_indent
        if self.right_indent:
            result["right_indent"] = self.right_indent
        if self.first_line_indent:
            result["first_line_indent"] = self.first_line_indent
        if self.line_spacing:
            result["line_spacing"] = self.line_spacing
        if self.background:
            result["background"] = self.background
        if self.border:
            result["border"] = self.border
        return result

    def merge(self, other: "ParagraphStyle") -> "ParagraphStyle":
        """
        合并两个样式（后者覆盖前者）。

        参数:
            other: 要合并的样式

        返回:
            ParagraphStyle: 合并后的新样式
        """
        merged = deepcopy(self)
        for key, value in other.__dict__.items():
            if value is not None:
                setattr(merged, key, value)
        return merged


@dataclass
class TableStyle:
    """
    表格样式。

    属性:
        style_name: 表格样式名称
        alignment: 表格对齐方式
        header_bg: 表头背景色
        header_fg: 表头文字颜色
        cell_padding: 单元格内边距
        border: 边框样式
    """

    style_name: str = "Table Grid"
    alignment: Optional[int] = None  # WD_TABLE_ALIGNMENT
    header_bg: Optional[RGBColor] = None
    header_fg: Optional[RGBColor] = None
    cell_padding: Optional[Dict[str, float]] = None
    border: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "style_name": self.style_name,
        }
        if self.alignment is not None:
            result["alignment"] = self.alignment
        if self.header_bg:
            result["header_bg"] = self.header_bg
        if self.header_fg:
            result["header_fg"] = self.header_fg
        if self.cell_padding:
            result["cell_padding"] = self.cell_padding
        if self.border:
            result["border"] = self.border
        return result


class StyleResolver:
    """
    样式解析器。

    负责将 AST 节点和主题配置转换为具体的样式字典。
    所有样式决策集中在此，便于统一管理和定制。

    属性:
        theme: 主题配置
        custom_styles: 自定义样式覆盖
    """

    def __init__(self, theme: Optional[Any] = None, custom_styles: Optional[Dict[str, Any]] = None):
        """
        初始化样式解析器。

        参数:
            theme: 主题配置（默认使用 DefaultTheme）
            custom_styles: 自定义样式覆盖
        """
        self.theme = theme or DefaultTheme()
        self.custom_styles = custom_styles or {}

    # ============================================================
    # 段落样式
    # ============================================================

    def heading_style(self, level: int) -> Dict[str, Any]:
        """
        获取标题样式。

        参数:
            level: 标题级别 (1-6)

        返回:
            Dict[str, Any]: 样式字典
        """
        # 基础样式由主题提供，确保主题中的标题字号实际参与渲染。
        base = self._dict_to_paragraph_style(self.theme.get_heading_style(level))

        # 自定义覆盖
        custom_key = f"heading_{level}"
        if custom_key in self.custom_styles:
            custom = self._dict_to_paragraph_style(self.custom_styles[custom_key])
            base = base.merge(custom)

        return base.to_dict()

    def paragraph_style(self) -> Dict[str, Any]:
        """
        获取普通段落样式。

        返回:
            Dict[str, Any]: 样式字典
        """
        body_size = self._theme_value("body_size", 11)
        base = ParagraphStyle(
            font_name=self.theme.body_font,
            font_size=body_size,
            space_after=Pt(6),
            alignment=WD_ALIGN_PARAGRAPH.LEFT,
        )

        if "paragraph" in self.custom_styles:
            custom = self._dict_to_paragraph_style(self.custom_styles["paragraph"])
            base = base.merge(custom)

        return base.to_dict()

    def adaptive_paragraph_style(
        self,
        text: str,
        has_line_breaks: bool = False,
    ) -> Dict[str, Any]:
        """
        段落样式（统一左对齐）。

        正文不再采用两端对齐（JUSTIFY），统一左对齐，避免 Word 对
        中文/混合段落逐行撑满导致短行被拉伸。

        参数:
            text: 段落正文
            has_line_breaks: 段落是否包含显式换行（SoftBreak/HardBreak）

        返回:
            Dict[str, Any]: 样式字典
        """
        return self.paragraph_style()

    def blockquote_style(self) -> Dict[str, Any]:
        """
        获取引用块样式。

        返回:
            Dict[str, Any]: 样式字典
        """
        base = ParagraphStyle(
            font_name=self.theme.body_font,
            font_size=11,
            left_indent=Cm(1.0),
            space_after=Pt(6),
            color=RGBColor(0x55, 0x55, 0x55),
            border={"left": {"style": "single", "width": 4, "color": "auto"}},
        )

        if "blockquote" in self.custom_styles:
            custom = self._dict_to_paragraph_style(self.custom_styles["blockquote"])
            base = base.merge(custom)

        return base.to_dict()

    def code_style(self) -> Dict[str, Any]:
        """
        获取代码块样式。

        返回:
            Dict[str, Any]: 样式字典
        """
        code_size = self._theme_value("code_size", 10)
        base = ParagraphStyle(
            font_name=self.theme.code_font,
            font_size=code_size,
            left_indent=Cm(0.5),
            space_before=Pt(6),
            space_after=Pt(6),
            background=self.theme.code_bg,
        )

        if "code" in self.custom_styles:
            custom = self._dict_to_paragraph_style(self.custom_styles["code"])
            base = base.merge(custom)

        return base.to_dict()

    def ascii_style(self) -> Dict[str, Any]:
        """
        获取 ASCII 图样式（第十四章）。

        字体 Consolas 8.5pt，左对齐（避免长行居中导致版面失衡）。

        返回:
            Dict[str, Any]: 样式字典
        """
        ascii_size = self._theme_value("ascii_size", 8.5)
        ascii_font = self._theme_value("ascii_font", "Consolas")
        base = ParagraphStyle(
            font_name=ascii_font,
            font_size=ascii_size,
            alignment=self._normalize_alignment(self._theme_value("ascii_alignment", "left")),
            line_spacing=1.0,
            space_before=Pt(6),
            space_after=Pt(6),
        )
        if "ascii" in self.custom_styles:
            custom = self._dict_to_paragraph_style(self.custom_styles["ascii"])
            base = base.merge(custom)
        return base.to_dict()

    @staticmethod
    def _normalize_alignment(value: Any) -> int:
        """将字符串对齐方式规范化为 WD_ALIGN_PARAGRAPH 枚举值。"""
        mapping = {
            "left": WD_ALIGN_PARAGRAPH.LEFT,
            "center": WD_ALIGN_PARAGRAPH.CENTER,
            "centre": WD_ALIGN_PARAGRAPH.CENTER,
            "right": WD_ALIGN_PARAGRAPH.RIGHT,
            "both": WD_ALIGN_PARAGRAPH.JUSTIFY,
            "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
        }
        if isinstance(value, str):
            return mapping.get(value.lower().strip(), WD_ALIGN_PARAGRAPH.LEFT)
        return value if value is not None else WD_ALIGN_PARAGRAPH.LEFT

    def list_item_style(self, depth: int) -> Dict[str, Any]:
        """
        获取列表项样式。

        参数:
            depth: 列表嵌套深度

        返回:
            Dict[str, Any]: 样式字典
        """
        body_size = self._theme_value("body_size", 11)
        base = ParagraphStyle(
            font_name=self.theme.body_font,
            font_size=body_size,
            left_indent=Cm(0.5 * depth + 0.5),
            space_after=Pt(3),
        )

        custom_key = f"list_item_{depth}"
        if custom_key in self.custom_styles:
            custom = self._dict_to_paragraph_style(self.custom_styles[custom_key])
            base = base.merge(custom)
        elif "list_item" in self.custom_styles:
            custom = self._dict_to_paragraph_style(self.custom_styles["list_item"])
            base = base.merge(custom)

        return base.to_dict()

    # ============================================================
    # 表格样式
    # ============================================================

    def table_style(self) -> Dict[str, Any]:
        """
        获取表格样式。

        返回:
            Dict[str, Any]: 样式字典
        """
        base = TableStyle(
            style_name=self.theme.table_style or "Table Grid",
            alignment=WD_TABLE_ALIGNMENT.CENTER,
            header_bg=self.theme.table_header_bg,
            header_fg=self.theme.table_header_fg,
            cell_padding={"top": 2, "bottom": 2, "left": 3, "right": 3},
        )

        if "table" in self.custom_styles:
            custom = self._dict_to_table_style(self.custom_styles["table"])
            base = self._merge_table_styles(base, custom)

        return base.to_dict()

    def table_header_cell_style(self) -> Dict[str, Any]:
        """
        获取表头单元格样式。

        返回:
            Dict[str, Any]: 样式字典
        """
        style = self.table_style()
        return {
            "bold": True,
            "background": style.get("header_bg"),
            "color": style.get("header_fg"),
            "alignment": WD_ALIGN_PARAGRAPH.CENTER,
        }

    def table_cell_style(self, align: Optional[str] = None) -> Dict[str, Any]:
        """
        获取表格单元格样式。

        参数:
            align: 对齐方式 ('left', 'center', 'right')

        返回:
            Dict[str, Any]: 样式字典
        """
        alignment_map = {
            "left": WD_ALIGN_PARAGRAPH.LEFT,
            "center": WD_ALIGN_PARAGRAPH.CENTER,
            "right": WD_ALIGN_PARAGRAPH.RIGHT,
        }
        alignment = alignment_map.get(align, WD_ALIGN_PARAGRAPH.LEFT)
        table_font_size = self._theme_value("table_font_size", 9.5)

        return {
            "alignment": alignment,
            "font_name": self.theme.body_font,
            "font_size": table_font_size,
        }

    def table_cell_style_by_type(self, data_type: str) -> Dict[str, Any]:
        """
        按数据类型决定对齐（第九章 9.2）。

        Text/Code/URL -> Left；Number/Percentage/Currency -> Right；Date/Boolean -> Center

        参数:
            data_type: 单元格数据类型

        返回:
            Dict[str, Any]: 样式字典
        """
        align_map = {
            "number": "right",
            "percentage": "right",
            "currency": "right",
            "date": "center",
            "boolean": "center",
            "code": "left",
            "url": "left",
            "text": "left",
        }
        return self.table_cell_style(align_map.get(data_type, "left"))

    # ============================================================
    # 行内样式
    # ============================================================

    def inline_text_style(self, **kwargs) -> Dict[str, Any]:
        """
        获取行内文本样式。

        参数:
            **kwargs: 样式属性

        返回:
            Dict[str, Any]: 样式字典
        """
        body_size = self._theme_value("body_size", 11)
        style = InlineStyle(
            bold=kwargs.get("bold", False),
            italic=kwargs.get("italic", False),
            underline=kwargs.get("underline", False),
            code=kwargs.get("code", False),
            link=kwargs.get("link"),
            color=kwargs.get("color"),
            highlight=kwargs.get("highlight"),
            font_name=kwargs.get("font_name", self.theme.body_font),
            font_size=kwargs.get("font_size", body_size),
        )

        return style.to_dict()

    def strong_style(self) -> Dict[str, Any]:
        """获取粗体样式"""
        return {"bold": True}

    def emphasis_style(self) -> Dict[str, Any]:
        """获取斜体样式"""
        return {"italic": True}

    def inline_code_style(self) -> Dict[str, Any]:
        """获取行内代码样式"""
        code_size = self._theme_value("code_size", 10)
        return {
            "font_name": self.theme.code_font,
            "font_size": code_size,
            "color": RGBColor(0x80, 0x00, 0x00),
        }

    def figure_style(self) -> Dict[str, Any]:
        """获取图形段落样式（第十五章）。"""
        return {
            "alignment": WD_ALIGN_PARAGRAPH.CENTER,
            "keep_together": True,
        }

    def link_style(self, href: str) -> Dict[str, Any]:
        """获取链接样式"""
        return {
            "color": RGBColor(0x00, 0x00, 0xFF),
            "underline": True,
            "link": href,
        }

    # ============================================================
    # 工具方法
    # ============================================================

    def _theme_value(self, name: str, default: Any) -> Any:
        """从主题提取属性，不存在时使用默认值。"""
        return getattr(self.theme, name, default)

    def _dict_to_paragraph_style(self, data: Dict[str, Any]) -> ParagraphStyle:
        """将字典转换为 ParagraphStyle"""
        return ParagraphStyle(
            font_name=data.get("font_name"),
            font_size=data.get("font_size"),
            bold=data.get("bold", False),
            italic=data.get("italic", False),
            color=data.get("color"),
            alignment=self._normalize_alignment(data.get("alignment")),
            space_before=data.get("space_before"),
            space_after=data.get("space_after"),
            left_indent=data.get("left_indent"),
            right_indent=data.get("right_indent"),
            first_line_indent=data.get("first_line_indent"),
            line_spacing=data.get("line_spacing"),
            background=data.get("background"),
            border=data.get("border"),
        )

    def _dict_to_table_style(self, data: Dict[str, Any]) -> TableStyle:
        """将字典转换为 TableStyle"""
        return TableStyle(
            style_name=data.get("style_name", "Table Grid"),
            alignment=data.get("alignment"),
            header_bg=data.get("header_bg"),
            header_fg=data.get("header_fg"),
            cell_padding=data.get("cell_padding"),
            border=data.get("border"),
        )

    def _merge_table_styles(self, base: TableStyle, custom: TableStyle) -> TableStyle:
        """合并表格样式"""
        result = deepcopy(base)
        for key, value in custom.__dict__.items():
            if value is not None:
                setattr(result, key, value)
        return result

    # ============================================================
    # 样式注册
    # ============================================================

    def register_style(self, name: str, style: Dict[str, Any]) -> None:
        """
        注册自定义样式。

        参数:
            name: 样式名称
            style: 样式字典
        """
        self.custom_styles[name] = style

    def get_style(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取自定义样式。

        参数:
            name: 样式名称

        返回:
            Optional[Dict[str, Any]]: 样式字典
        """
        return self.custom_styles.get(name)

    def clear_custom_styles(self) -> None:
        """清空所有自定义样式"""
        self.custom_styles.clear()


# ============================================================
# 预定义样式集合
# ============================================================


def get_academic_style() -> Dict[str, Any]:
    """
    获取学术风格样式配置。

    返回:
        Dict[str, Any]: 样式配置
    """
    return {
        "heading_1": {"font_name": "Times New Roman", "font_size": 18, "bold": True},
        "heading_2": {"font_name": "Times New Roman", "font_size": 16, "bold": True},
        "heading_3": {"font_name": "Times New Roman", "font_size": 14, "bold": True},
        "paragraph": {
            "font_name": "Times New Roman",
            "font_size": 12,
            "alignment": WD_ALIGN_PARAGRAPH.JUSTIFY,
            "first_line_indent": Cm(0.75),
            "space_after": Pt(6),
        },
        "code": {
            "font_name": "Courier New",
            "font_size": 10,
        },
        "table": {
            "style_name": "Light Grid Accent 1",
        },
    }


def get_technical_style() -> Dict[str, Any]:
    """
    获取技术文档风格样式配置。

    返回:
        Dict[str, Any]: 样式配置
    """
    return {
        "heading_1": {
            "font_name": "Arial",
            "font_size": 16,
            "bold": True,
            "color": RGBColor(0x00, 0x3B, 0x71),
        },
        "heading_2": {
            "font_name": "Arial",
            "font_size": 14,
            "bold": True,
            "color": RGBColor(0x00, 0x3B, 0x71),
        },
        "heading_3": {"font_name": "Arial", "font_size": 12, "bold": True},
        "paragraph": {
            "font_name": "Calibri",
            "font_size": 11,
            "alignment": WD_ALIGN_PARAGRAPH.LEFT,
            "space_after": Pt(6),
        },
        "code": {
            "font_name": "Consolas",
            "font_size": 10,
            "background": RGBColor(0xF0, 0xF0, 0xF0),
        },
        "blockquote": {
            "left_indent": Cm(1.0),
            "color": RGBColor(0x55, 0x55, 0x55),
            "border": {"left": {"style": "single", "width": 4, "color": "auto"}},
        },
        "table": {
            "style_name": "Table Grid",
            "header_bg": RGBColor(0x00, 0x3B, 0x71),
            "header_fg": RGBColor(0xFF, 0xFF, 0xFF),
        },
    }
