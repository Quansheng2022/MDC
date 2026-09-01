"""
Diagram Service - 图表渲染服务

将 ASCII 结构图渲染为 SVG 格式。
支持多种 ASCII 图表风格，输出高质量矢量图形。
"""

from dataclasses import dataclass
from typing import List, Optional, Set


@dataclass
class DiagramStyle:
    """
    图表样式配置。

    属性:
        line_color: 线条颜色
        line_width: 线条宽度
        box_fill: 方框填充色
        box_stroke: 方框边框色
        text_color: 文字颜色
        font_family: 字体
        font_size: 字号
        background: 背景色
        padding: 内边距
        char_width: 字符宽度（像素）
        char_height: 字符高度（像素）
        title_color: 标题颜色
        title_font_size: 标题字号
    """
    line_color: str = "#555"
    line_width: int = 2
    box_fill: str = "#E8F0FE"
    box_stroke: str = "#4A7FB5"
    text_color: str = "#333"
    font_family: str = "Microsoft YaHei, Segoe UI, sans-serif"
    font_size: int = 11
    background: str = "white"
    padding: int = 20
    char_width: int = 12
    char_height: int = 20
    title_color: str = "#1a1a1a"
    title_font_size: int = 13


class DiagramService:
    """
    图表渲染服务。

    将 ASCII 结构图转换为 SVG。
    支持多种 ASCII 字符集和样式配置。

    示例:
        >>> lines = ["┌─────┐", "│ DB  │", "└─────┘"]
        >>> svg = DiagramService.render_svg(lines)
    """

    # ASCII 结构图特征字符
    DIAGRAM_CHARS: Set[str] = {
        '┌', '┐', '└', '┘', '├', '┤', '┬', '┴', '┼',
        '─', '━', '═', '│', '┃', '║', '╔', '╗', '╚', '╝',
        '▄', '▀', '■', '□', '▬', '▭', '▮', '▯',
        '▼', '▲', '◄', '►', '◆', '◇', '○', '●',
        '→', '←', '↑', '↓', '↔', '↕',
        '╱', '╲',
    }

    @classmethod
    def render_svg(
        cls,
        lines: List[str],
        style: Optional[DiagramStyle] = None,
    ) -> str:
        """
        渲染 ASCII 结构图为 SVG。

        参数:
            lines: ASCII 图的行列表
            style: 图表样式（可选）

        返回:
            str: SVG 字符串

        异常:
            ValueError: 如果输入为空或无效
        """
        if not lines or not any(line.strip() for line in lines):
            raise ValueError("Empty or invalid diagram input")

        if style is None:
            style = DiagramStyle()

        # 清理输入
        cleaned_lines = cls._clean_lines(lines)

        if len(cleaned_lines) < 2:
            raise ValueError("Diagram must have at least 2 lines")

        return cls._generate_svg(cleaned_lines, style)

    @classmethod
    def _clean_lines(cls, lines: List[str]) -> List[str]:
        """
        清理输入行。

        移除行首的管道符（用于 Markdown 中的转义），
        移除空行（保留结构完整性）。

        参数:
            lines: 原始行列表

        返回:
            List[str]: 清理后的行列表
        """
        cleaned = []

        for line in lines:
            # 移除行首的 | 或空格（Markdown 转义）
            cleaned_line = line.lstrip('| \t')

            # 如果行以结构图字符开头，保留
            if cleaned_line and any(c in cleaned_line for c in cls.DIAGRAM_CHARS):
                cleaned.append(cleaned_line)
            elif cleaned_line and not cleaned_line.isspace():
                # 非空行也保留（可能是文字说明）
                cleaned.append(cleaned_line)

        return cleaned

    @classmethod
    def _generate_svg(cls, lines: List[str], style: DiagramStyle) -> str:
        """
        生成 SVG 字符串。

        参数:
            lines: 清理后的行列表
            style: 图表样式

        返回:
            str: SVG 字符串
        """
        # 计算尺寸
        max_len = max(len(line) for line in lines)
        height = len(lines)

        char_width = style.char_width
        char_height = style.char_height
        padding = style.padding

        svg_width = max(400, max_len * char_width + padding * 2)
        svg_height = max(200, height * char_height + padding * 2)

        # 构建 SVG
        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{svg_width}" height="{svg_height}" '
            f'viewBox="0 0 {svg_width} {svg_height}">',
            '<style>',
            f'  .line {{ stroke: {style.line_color}; stroke-width: {style.line_width}; fill: none; stroke-linecap: round; stroke-linejoin: round; }}',
            f'  .box {{ stroke: {style.box_stroke}; stroke-width: {style.line_width}; fill: {style.box_fill}; rx: 2; }}',
            f'  .text {{ font-family: "{style.font_family}"; font-size: {style.font_size}px; fill: {style.text_color}; }}',
            f'  .title {{ font-weight: bold; font-size: {style.title_font_size}px; fill: {style.title_color}; }}',
            '</style>',
            f'<rect width="100%" height="100%" fill="{style.background}"/>'
        ]

        # 遍历每个字符
        for y, line in enumerate(lines):
            for x, ch in enumerate(line):
                px = padding + x * char_width
                py = padding + y * char_height

                # 处理不同类型的字符
                if ch in cls._get_box_chars():
                    svg_parts.append(cls._render_box(px, py, ch, char_width, char_height, style))
                elif ch in cls._get_line_chars():
                    svg_parts.append(cls._render_line(px, py, ch, char_width, char_height, style))
                elif ch in cls._get_arrow_chars():
                    svg_parts.append(cls._render_arrow(px, py, ch, char_width, char_height, style))
                elif ch in cls._get_box_corners():
                    svg_parts.append(cls._render_corner(px, py, ch, char_width, char_height, style))
                elif ch in cls._get_junction_chars():
                    svg_parts.append(cls._render_junction(px, py, ch, char_width, char_height, style))
                elif ch not in ' \t':
                    # 文字字符
                    is_title = cls._is_title_line(y, line, lines)
                    text_class = 'title' if is_title else 'text'
                    svg_parts.append(
                        f'<text x="{px + char_width // 2}" y="{py + char_height * 0.75}" '
                        f'text-anchor="middle" class="{text_class}">{cls._escape_xml(ch)}</text>'
                    )

        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)

    # ============================================================
    # 字符分类
    # ============================================================

    @classmethod
    def _get_box_chars(cls) -> Set[str]:
        """获取方框字符"""
        return {'┌', '┐', '└', '┘', '╔', '╗', '╚', '╝'}

    @classmethod
    def _get_line_chars(cls) -> Set[str]:
        """获取线条字符"""
        return {'─', '━', '═', '│', '┃', '║'}

    @classmethod
    def _get_box_corners(cls) -> Set[str]:
        """获取方框角字符"""
        return {'┌', '┐', '└', '┘'}

    @classmethod
    def _get_junction_chars(cls) -> Set[str]:
        """获取连接点字符"""
        return {'├', '┤', '┬', '┴', '┼', '╠', '╣', '╦', '╩', '╬'}

    @classmethod
    def _get_arrow_chars(cls) -> Set[str]:
        """获取箭头字符"""
        return {'▼', '▲', '◄', '►', '→', '←', '↑', '↓', '↔', '↕'}

    # ============================================================
    # 渲染函数
    # ============================================================

    @classmethod
    def _render_box(cls, px: int, py: int, ch: str, cw: int, ch_h: int, style: DiagramStyle) -> str:
        """渲染方框"""
        rect_x = px - 2
        rect_y = py - 2
        rect_w = cw + 4
        rect_h = ch_h + 4
        return f'<rect x="{rect_x}" y="{rect_y}" width="{rect_w}" height="{rect_h}" class="box"/>'

    @classmethod
    def _render_line(cls, px: int, py: int, ch: str, cw: int, ch_h: int, style: DiagramStyle) -> str:
        """渲染线条"""
        if ch in {'─', '━', '═'}:
            # 水平线
            return f'<line x1="{px}" y1="{py + ch_h // 2}" x2="{px + cw}" y2="{py + ch_h // 2}" class="line"/>'
        else:
            # 垂直线
            return f'<line x1="{px + cw // 2}" y1="{py}" x2="{px + cw // 2}" y2="{py + ch_h}" class="line"/>'

    @classmethod
    def _render_corner(cls, px: int, py: int, ch: str, cw: int, ch_h: int, style: DiagramStyle) -> str:
        """渲染角"""
        # 角用方框表示
        rect_x = px - 2
        rect_y = py - 2
        rect_w = cw + 4
        rect_h = ch_h + 4
        return f'<rect x="{rect_x}" y="{rect_y}" width="{rect_w}" height="{rect_h}" class="box"/>'

    @classmethod
    def _render_junction(cls, px: int, py: int, ch: str, cw: int, ch_h: int, style: DiagramStyle) -> str:
        """渲染连接点"""
        parts = []

        # 垂直连接线
        if ch in {'├', '┤', '┴', '┼', '╠', '╣', '╩', '╬'}:
            parts.append(f'<line x1="{px + cw // 2}" y1="{py}" x2="{px + cw // 2}" y2="{py + ch_h}" class="line"/>')
        # 水平连接线
        if ch in {'├', '┤', '┬', '┼', '╠', '╣', '╦', '╬'}:
            parts.append(f'<line x1="{px}" y1="{py + ch_h // 2}" x2="{px + cw}" y2="{py + ch_h // 2}" class="line"/>')
        # T 型连接点
        if ch == '├':
            # 左侧连接
            parts.append(f'<line x1="{px + cw // 2}" y1="{py + ch_h // 2}" x2="{px + cw}" y2="{py + ch_h // 2}" class="line"/>')
        elif ch == '┤':
            # 右侧连接
            parts.append(f'<line x1="{px}" y1="{py + ch_h // 2}" x2="{px + cw // 2}" y2="{py + ch_h // 2}" class="line"/>')
        elif ch == '┬':
            # 上侧连接
            parts.append(f'<line x1="{px + cw // 2}" y1="{py + ch_h // 2}" x2="{px + cw // 2}" y2="{py + ch_h}" class="line"/>')
        elif ch == '┴':
            # 下侧连接
            parts.append(f'<line x1="{px + cw // 2}" y1="{py}" x2="{px + cw // 2}" y2="{py + ch_h // 2}" class="line"/>')

        return '\n'.join(parts)

    @classmethod
    def _render_arrow(cls, px: int, py: int, ch: str, cw: int, ch_h: int, style: DiagramStyle) -> str:
        """渲染箭头"""
        # 箭头作为多边形
        if ch in {'▼', '▲'}:
            # 上下箭头
            if ch == '▼':
                points = [
                    (px + 3, py + 3),
                    (px + cw - 3, py + 3),
                    (px + cw // 2, py + ch_h - 3)
                ]
            else:  # '▲'
                points = [
                    (px + 3, py + ch_h - 3),
                    (px + cw - 3, py + ch_h - 3),
                    (px + cw // 2, py + 3)
                ]
            points_str = ' '.join(f'{p[0]},{p[1]}' for p in points)
            return f'<polygon points="{points_str}" fill="{style.line_color}"/>'
        elif ch in {'►', '→'}:
            points = [
                (px + 3, py + 3),
                (px + 3, py + ch_h - 3),
                (px + cw - 3, py + ch_h // 2)
            ]
            points_str = ' '.join(f'{p[0]},{p[1]}' for p in points)
            return f'<polygon points="{points_str}" fill="{style.line_color}"/>'
        elif ch in {'◄', '←'}:
            points = [
                (px + cw - 3, py + 3),
                (px + cw - 3, py + ch_h - 3),
                (px + 3, py + ch_h // 2)
            ]
            points_str = ' '.join(f'{p[0]},{p[1]}' for p in points)
            return f'<polygon points="{points_str}" fill="{style.line_color}"/>'
        else:
            # 其他箭头符号
            return ''

    # ============================================================
    # 辅助方法
    # ============================================================

    @classmethod
    def _is_title_line(cls, y: int, line: str, lines: List[str]) -> bool:
        """
        判断是否标题行。

        标题行通常在第一行，且包含方框字符。

        参数:
            y: 行索引
            line: 当前行
            lines: 所有行

        返回:
            bool: 是否为标题行
        """
        if y != 0:
            return False

        # 检查是否包含方框字符
        box_chars = cls._get_box_chars()
        return any(c in line for c in box_chars)

    @classmethod
    def _escape_xml(cls, text: str) -> str:
        """
        转义 XML 特殊字符。

        参数:
            text: 要转义的文本

        返回:
            str: 转义后的文本
        """
        replacements = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&apos;',
        }
        for char, escaped in replacements.items():
            text = text.replace(char, escaped)
        return text


# ============================================================
# 便捷函数
# ============================================================

def render_diagram(lines: List[str], **kwargs) -> str:
    """
    渲染 ASCII 结构图为 SVG 的便捷函数。

    参数:
        lines: ASCII 图的行列表
        **kwargs: 样式覆盖参数

    返回:
        str: SVG 字符串

    示例:
        >>> lines = ["┌─────┐", "│ DB  │", "└─────┘"]
        >>> svg = render_diagram(lines, line_color="#FF0000")
    """
    style = DiagramStyle(**kwargs)
    return DiagramService.render_svg(lines, style)


def render_diagram_from_text(text: str, **kwargs) -> str:
    """
    从文本渲染 ASCII 结构图。

    参数:
        text: 包含 ASCII 图的文本
        **kwargs: 样式覆盖参数

    返回:
        str: SVG 字符串
    """
    lines = text.strip().split('\n')
    return render_diagram(lines, **kwargs)


def is_diagram(lines: List[str]) -> bool:
    """
    检查是否为 ASCII 结构图。

    参数:
        lines: 行列表

    返回:
        bool: 是否为结构图
    """
    if not lines or len(lines) < 3:
        return False

    # 统计结构图字符
    count = 0
    for line in lines:
        for ch in line:
            if ch in DiagramService.DIAGRAM_CHARS:
                count += 1

    return count >= 10