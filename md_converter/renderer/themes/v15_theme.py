"""
V15 Theme - QS-Word-Default-V1.5 已冻结主题模型

依据 Doc/Default_theme_设计文档.md（V1.5 冻结版）实现。

设计原则（文档第三章）:
    - YAML 定义 WHAT，Python 决定 HOW
    - 决策与渲染分离：主题只提供常量与偏好，决策算法在 layout/ 模块
    - 可读性不可妥协：最小字号门

本类同时提供与 DefaultTheme 兼容的访问接口，使 StyleResolver /
WordRenderer 可以无侵入地切换主题。
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml
from docx.shared import Cm, Inches, Length, Pt, RGBColor

# ============================================================
# 长度解析
# ============================================================


def parse_length(value: Union[str, int, float]) -> Length:
    """
    解析 YAML 中的长度值。

    支持:
        - "10.5pt" / "1in" / "2.5cm" / "0.5in"
        - 纯数字（按磅处理）

    参数:
        value: 长度字符串或数字

    返回:
        Length: python-docx 长度对象
    """
    if isinstance(value, (int, float)):
        return Pt(float(value))
    text = str(value).strip().lower()
    if text.endswith("pt"):
        return Pt(float(text[:-2].strip()))
    if text.endswith("in"):
        return Inches(float(text[:-2].strip()))
    if text.endswith("cm"):
        return Cm(float(text[:-2].strip()))
    if text.endswith("mm"):
        return Cm(float(text[:-2].strip()) / 10.0)
    try:
        return Pt(float(text))
    except ValueError:
        raise ValueError(f"Unsupported length value: {value!r}") from None


def parse_pt(value: Union[str, int, float]) -> float:
    """解析为磅值（float）。"""
    return float(parse_length(value).pt)


def parse_cm(value: Union[str, int, float]) -> float:
    """解析为厘米值（float）。"""
    return float(parse_length(value).cm)


# ============================================================
# 默认颜色（V1.5 未冻结颜色，沿用项目既有视觉体系）
# ============================================================

DEFAULT_COLORS: Dict[str, RGBColor] = {
    "heading_color": RGBColor(0x00, 0x00, 0x00),
    "body_color": RGBColor(0x00, 0x00, 0x00),
    "link_color": RGBColor(0x00, 0x00, 0xFF),
    "code_color": RGBColor(0x80, 0x00, 0x00),
    "table_header_bg": RGBColor(0x2F, 0x54, 0x96),
    "table_header_fg": RGBColor(0xFF, 0xFF, 0xFF),
    "code_bg": RGBColor(0xF0, 0xF0, 0xF0),
}


class V15Theme:
    """
    QS-Word-Default-V1.5 主题模型。

    属性:
        data: 从 YAML 加载的完整配置字典（冻结结构）

    提供类型化访问器（字号、字体、间距、分页策略、可读性保护等），
    并兼容 DefaultTheme 的既有 API。
    """

    def __init__(self, data: Dict[str, Any]):
        self.data = deepcopy(data)

    # ============================================================
    # 加载
    # ============================================================

    @classmethod
    def load(cls, path: Optional[Union[str, Path]] = None) -> "V15Theme":
        """
        从 YAML 文件加载主题。

        参数:
            path: YAML 路径；默认加载包内 default_v1_5.yaml

        返回:
            V15Theme: 主题实例
        """
        if path is None:
            path = Path(__file__).parent / "default_v1_5.yaml"
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(data)

    @classmethod
    def load_default(cls) -> "V15Theme":
        """加载包内冻结的默认 V1.5 主题。"""
        return cls.load()

    # ============================================================
    # 主题标识
    # ============================================================

    @property
    def name(self) -> str:
        return str(self.data.get("theme", {}).get("name", "QS-Word-Default-V1.5"))

    @property
    def version(self) -> str:
        return str(self.data.get("theme", {}).get("version", "1.5"))

    @property
    def status(self) -> str:
        return str(self.data.get("theme", {}).get("status", "frozen"))

    # ============================================================
    # 页面
    # ============================================================

    @property
    def page_size(self) -> str:
        return str(self.data.get("page", {}).get("size", "A4"))

    @property
    def page_margins_cm(self) -> Dict[str, float]:
        """页边距（厘米）。YAML 中 1in -> 2.54cm。"""
        margins = self.data.get("page", {}).get("margins", {})
        return {
            "top": parse_cm(margins.get("top", "1in")),
            "bottom": parse_cm(margins.get("bottom", "1in")),
            "left": parse_cm(margins.get("left", "1in")),
            "right": parse_cm(margins.get("right", "1in")),
        }

    # ============================================================
    # 字体体系
    # ============================================================

    def font_mapping_for(self, kind: str = "body") -> Dict[str, str]:
        """
        获取 Word XML 四槽位字体映射（ascii / hAnsi / eastAsia / cs）。

        参数:
            kind: 'body' 或 'heading'

        返回:
            Dict[str, str]: 字体映射
        """
        mapping = self.data.get("font_mapping", {})
        result: Dict[str, str] = {}
        for slot in ("ascii", "hAnsi", "eastAsia", "cs"):
            result[slot] = str(mapping.get(slot, {}).get(kind, "Calibri"))
        return result

    @property
    def body_font(self) -> str:
        """兼容 DefaultTheme：正文西文字体（ascii）。"""
        return self.font_mapping_for("body")["ascii"]

    @property
    def heading_font(self) -> str:
        """兼容 DefaultTheme：标题西文字体（ascii）。"""
        return self.font_mapping_for("heading")["ascii"]

    @property
    def body_east_asia_font(self) -> str:
        """正文东亚字体（eastAsia）。"""
        return self.font_mapping_for("body")["eastAsia"]

    @property
    def heading_east_asia_font(self) -> str:
        """标题东亚字体（eastAsia）。"""
        return self.font_mapping_for("heading")["eastAsia"]

    @property
    def code_font(self) -> str:
        return str(self.data.get("typography", {}).get("code", {}).get("font", "Consolas"))

    @property
    def ascii_font(self) -> str:
        return str(self.data.get("typography", {}).get("ascii", {}).get("font", "Consolas"))

    # ============================================================
    # 字号
    # ============================================================

    @property
    def body_size(self) -> float:
        """正文磅值（float），默认 10.5pt。"""
        return parse_pt(self.data.get("typography", {}).get("body", {}).get("size", "10.5pt"))

    @property
    def code_size(self) -> float:
        return parse_pt(self.data.get("typography", {}).get("code", {}).get("size", "10pt"))

    @property
    def ascii_size(self) -> float:
        return parse_pt(self.data.get("typography", {}).get("ascii", {}).get("size", "8.5pt"))

    def heading_size(self, level: int) -> float:
        """获取指定级别标题字号（磅）。H5/H6 沿用 H4。"""
        headings = self.data.get("typography", {}).get("heading", {})
        key = f"H{min(max(level, 1), 4)}"
        spec = headings.get(key, {})
        return parse_pt(spec.get("size", "14pt"))

    def heading_bold(self, level: int) -> bool:
        headings = self.data.get("typography", {}).get("heading", {})
        key = f"H{min(max(level, 1), 4)}"
        return bool(headings.get(key, {}).get("bold", True))

    def heading_italic(self, level: int) -> bool:
        headings = self.data.get("typography", {}).get("heading", {})
        key = f"H{min(max(level, 1), 4)}"
        return bool(headings.get(key, {}).get("italic", False))

    def heading_before(self, level: int) -> float:
        headings = self.data.get("typography", {}).get("heading", {})
        key = f"H{min(max(level, 1), 4)}"
        return parse_pt(headings.get(key, {}).get("before", "12pt"))

    def heading_after(self, level: int) -> float:
        headings = self.data.get("typography", {}).get("heading", {})
        key = f"H{min(max(level, 1), 4)}"
        return parse_pt(headings.get(key, {}).get("after", "6pt"))

    # ============================================================
    # 段落
    # ============================================================

    @property
    def line_spacing(self) -> float:
        paragraph = self.data.get("paragraph", {})
        spacing = paragraph.get("line_spacing", {})
        if spacing.get("type") == "multiple":
            return float(spacing.get("value", 1.15))
        return float(spacing.get("value", 1.15))

    @property
    def paragraph_space_before(self) -> float:
        return parse_pt(self.data.get("paragraph", {}).get("spacing", {}).get("before", "0pt"))

    @property
    def paragraph_space_after(self) -> float:
        return parse_pt(self.data.get("paragraph", {}).get("spacing", {}).get("after", "6pt"))

    @property
    def paragraph_alignment(self) -> Dict[str, Any]:
        return self.data.get("paragraph", {}).get("alignment", {})

    @property
    def cjk_threshold(self) -> float:
        return float(
            self.data.get("language_detection", {}).get("thresholds", {}).get("cjk_dominant", 0.55)
        )

    @property
    def latin_threshold(self) -> float:
        return float(
            self.data.get("language_detection", {})
            .get("thresholds", {})
            .get("latin_dominant", 0.60)
        )

    # ============================================================
    # 标题
    # ============================================================

    @property
    def heading_keep_with_next(self) -> bool:
        return bool(self.data.get("heading", {}).get("keep_with_next", True))

    @property
    def heading_keep_together(self) -> bool:
        return bool(self.data.get("heading", {}).get("keep_together", True))

    @property
    def preserve_source_numbering(self) -> bool:
        return bool(self.data.get("heading", {}).get("preserve_source_numbering", True))

    # ============================================================
    # 表格
    # ============================================================

    @property
    def table_style(self) -> str:
        return str(self.data.get("table", {}).get("style", "Table Grid"))

    @property
    def table_font_size(self) -> float:
        return parse_pt(self.data.get("table", {}).get("font_size", "9.5pt"))

    @property
    def table_header_repeat(self) -> bool:
        return bool(self.data.get("table", {}).get("header", {}).get("repeat", True))

    @property
    def table_vertical_alignment(self) -> str:
        return str(self.data.get("table", {}).get("vertical_alignment", "top"))

    @property
    def table_split_rows_across_pages(self) -> bool:
        return bool(self.data.get("table", {}).get("split_rows_across_pages", True))

    @property
    def table_landscape_candidate(self) -> bool:
        return bool(self.data.get("table", {}).get("landscape_candidate", True))

    # ============================================================
    # 代码 / ASCII
    # ============================================================

    @property
    def code_line_spacing(self) -> float:
        return float(self.data.get("code", {}).get("line_spacing", 1.0))

    @property
    def code_keep_together_if_lines(self) -> int:
        return int(self.data.get("code", {}).get("keep_together_if_lines", 25))

    @property
    def code_max_lines_per_page(self) -> int:
        return int(self.data.get("code", {}).get("max_lines_per_page", 45))

    @property
    def ascii_no_wrap(self) -> bool:
        return bool(self.data.get("ascii", {}).get("no_wrap", True))

    @property
    def ascii_alignment(self) -> str:
        return str(self.data.get("ascii", {}).get("alignment", "center"))

    # ============================================================
    # URL / 长英文
    # ============================================================

    @property
    def url_break_points(self) -> list:
        return list(
            self.data.get("url_and_long_words", {})
            .get("url", {})
            .get("break_points", ["/", ".", "-", "_", "?", "&", "="])
        )

    @property
    def long_word_threshold(self) -> int:
        return int(self.data.get("url_and_long_words", {}).get("long_word_threshold", 20))

    # ============================================================
    # Section
    # ============================================================

    @property
    def default_orientation(self) -> str:
        return str(self.data.get("section", {}).get("default_orientation", "portrait"))

    @property
    def landscape_width_margin_buffer_cm(self) -> float:
        return parse_cm(
            self.data.get("section", {})
            .get("landscape_trigger", {})
            .get("width_margin_buffer", "1cm")
        )

    # ============================================================
    # 分页策略
    # ============================================================

    def pagination_policy(self, content_type: str) -> Dict[str, Any]:
        """
        获取指定内容类型的分页策略。

        参数:
            content_type: 内容类型（heading/paragraph/table/figure/code/ascii/url/list）

        返回:
            Dict[str, Any]: 分页策略字典
        """
        policies = deepcopy(self.data.get("pagination_policies", {}))
        base = {
            "heading": {
                "keep_with_next": True,
                "keep_together": True,
                "allow_split": False,
            },
            "paragraph": {
                "keep_together": False,
                "allow_split": True,
                "widow_orphan_control": True,
            },
            "list": {
                "keep_together": False,
                "allow_split": True,
            },
            "table": {
                "keep_together": False,
                "allow_split": True,
                "split_rows_across_pages": True,
                "repeat_header": True,
            },
            "figure": {
                "keep_together": True,
                "allow_split": False,
                "move_to_next_page_if_insufficient": True,
            },
            "code": {
                "keep_together_if_lines": self.code_keep_together_if_lines,
                "allow_split_if_lines": self.code_keep_together_if_lines,
                "max_lines_per_page": self.code_max_lines_per_page,
            },
            "ascii": {
                "keep_together": True,
                "allow_split": False,
                "no_wrap": True,
            },
            "url": {
                "keep_together": False,
                "allow_split": True,
                "break_points": self.url_break_points,
            },
        }
        policy = dict(base.get(content_type, {}))
        policy.update(policies.get(content_type, {}))
        return policy

    # ============================================================
    # 可读性保护
    # ============================================================

    @property
    def readability_minimums(self) -> Dict[str, float]:
        """最小字号（磅）。margin 以磅表示（0.5in = 36pt）。"""
        minimums = self.data.get("readability", {}).get("minimum", {})
        return {
            "body_font": parse_pt(minimums.get("body_font", "10pt")),
            "table_font": parse_pt(minimums.get("table_font", "8.5pt")),
            "figure_text": parse_pt(minimums.get("figure_text", "8pt")),
            "ascii_font": parse_pt(minimums.get("ascii_font", "8pt")),
            "code_font": parse_pt(minimums.get("code_font", "8pt")),
            "margin": parse_pt(minimums.get("margin", "0.5in")),
        }

    @property
    def overflow_response(self) -> list:
        return list(self.data.get("readability", {}).get("overflow_response", []))

    # ============================================================
    # Layout QA
    # ============================================================

    @property
    def layout_qa_config(self) -> Dict[str, Any]:
        return self.data.get("layout_qa", {})

    @property
    def document_structure(self) -> Dict[str, Any]:
        return self.data.get("document_structure", {})

    # ============================================================
    # 颜色（兼容 DefaultTheme）
    # ============================================================

    def _color(self, key: str) -> RGBColor:
        return DEFAULT_COLORS.get(key, RGBColor(0x00, 0x00, 0x00))

    @property
    def heading_color(self) -> RGBColor:
        return self._color("heading_color")

    @property
    def body_color(self) -> RGBColor:
        return self._color("body_color")

    @property
    def link_color(self) -> RGBColor:
        return self._color("link_color")

    @property
    def code_color(self) -> RGBColor:
        return self._color("code_color")

    @property
    def table_header_bg(self) -> RGBColor:
        return self._color("table_header_bg")

    @property
    def table_header_fg(self) -> RGBColor:
        return self._color("table_header_fg")

    @property
    def code_bg(self) -> RGBColor:
        return self._color("code_bg")

    # ============================================================
    # 兼容 DefaultTheme 的样式 API
    # ============================================================

    def get_heading_size(self, level: int) -> float:
        """获取标题字号（磅，float）。"""
        return self.heading_size(level)

    def get_heading_style(self, level: int) -> Dict[str, Any]:
        """获取完整标题样式字典（与 DefaultTheme 兼容）。"""
        return {
            "font_name": self.heading_font,
            "font_size": self.heading_size(level),
            "bold": self.heading_bold(level),
            "italic": self.heading_italic(level),
            "color": self.heading_color,
            "space_before": Pt(self.heading_before(level)),
            "space_after": Pt(self.heading_after(level)),
        }

    def get_paragraph_style(self) -> Dict[str, Any]:
        """获取正文段落样式字典。"""
        return {
            "font_name": self.body_font,
            "font_size": self.body_size,
            "color": self.body_color,
            "space_after": Pt(self.paragraph_space_after),
            "line_spacing": self.line_spacing,
        }

    def get_code_style(self) -> Dict[str, Any]:
        """获取代码块样式字典。"""
        return {
            "font_name": self.code_font,
            "font_size": self.code_size,
            "color": self.code_color,
            "background": self.code_bg,
            "indent": Cm(0.5),
            "space_before": Pt(6),
            "space_after": Pt(6),
        }

    def get_list_style(self, depth: int) -> Dict[str, Any]:
        """获取列表项样式字典。"""
        return {
            "font_name": self.body_font,
            "font_size": self.body_size,
            "color": self.body_color,
            "left_indent": Cm(0.5 * (depth + 1)),
            "space_after": Pt(3),
        }

    def get_table_style(self) -> Dict[str, Any]:
        """获取表格样式字典。"""
        return {
            "style_name": self.table_style,
            "header_bg": self.table_header_bg,
            "header_fg": self.table_header_fg,
            "cell_padding": {"top": 2.0, "bottom": 2.0, "left": 3.0, "right": 3.0},
        }

    def get_blockquote_style(self) -> Dict[str, Any]:
        """获取引用块样式字典。"""
        return {
            "font_name": self.body_font,
            "font_size": self.body_size,
            "color": RGBColor(0x55, 0x55, 0x55),
            "left_indent": Cm(1.0),
            "border": {"left": {"style": "single", "width": 4, "color": "auto"}},
        }

    def get_page_margins(self) -> Dict[str, float]:
        """获取页边距（厘米），与 DefaultTheme 兼容。"""
        return self.page_margins_cm

    # ============================================================
    # 序列化
    # ============================================================

    def to_dict(self) -> Dict[str, Any]:
        """返回冻结 YAML 数据的深拷贝。"""
        return deepcopy(self.data)

    def __repr__(self) -> str:
        return f"V15Theme(name={self.name!r}, version={self.version!r}, " f"status={self.status!r})"
