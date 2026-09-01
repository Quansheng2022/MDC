"""
ASCII 图特征分析器

基于 ASCII 字符特征（方框、箭头、生命线、树形分支）识别图结构，
产出 :class:`DiagramFeatures` 纯数据对象，供类型检测器与转换器使用。
"""

from __future__ import annotations

import re
import unicodedata
from typing import List, Optional, Set, Tuple

from .model import (
    Arrow,
    Box,
    ClassBox,
    ClassRelation,
    ClassSection,
    DiagramFeatures,
    Lifeline,
    Message,
    TreeNode,
)

# ============================================================
# 字符集合
# ============================================================

HORIZONTAL_CHARS: Set[str] = set("─━═-–—")
VERTICAL_CHARS: Set[str] = set("│┃║|:")

# 角点与连接符（同时参与水平/垂直连接）
CORNER_CHARS: Set[str] = set("┌┐└┘┌┐╭╮╰╯+*")
JUNCTION_CHARS: Set[str] = set("├┤┬┴┼╠╣╦╩╬")
HEAVY_CORNER_CHARS: Set[str] = set("┏┓┗┛┣┫┳┻╋")

HORIZONTAL_CONNECTORS: Set[str] = (
    HORIZONTAL_CHARS | CORNER_CHARS | JUNCTION_CHARS | HEAVY_CORNER_CHARS
)
VERTICAL_CONNECTORS: Set[str] = VERTICAL_CHARS | CORNER_CHARS | JUNCTION_CHARS | HEAVY_CORNER_CHARS

# 方框顶/底边中嵌入的垂直箭头（如 ┌──▼──┐）视为连续水平连接
HORIZONTAL_RUN_CONNECTORS: Set[str] = HORIZONTAL_CONNECTORS | {"▼", "▲", "↓", "↑", "▽", "△"}

UNICODE_ARROWS: Set[str] = set("→←↑↓↔⇄⇒⇐⇔►◄▶◀▼▲▽△")

# 全角/宽字符展开后占位的填充符（不可见，仅用于保持列对齐）
FILLER: str = "\u0000"

# 树形分支前缀（行首）
TREE_BRANCH_PATTERN = re.compile(r"^[\s│|]*[├└└┌+\\`]\s*[-─=]+\s*")


def char_display_width(ch: str) -> int:
    """
    计算字符的显示宽度（列数）。

    全角（F/W）字符按 2 列计，其余按 1 列计；
    用于解决中文/全角字符导致的 ASCII 图列错位问题。
    """
    return 2 if unicodedata.east_asian_width(ch) in ("F", "W") else 1


def is_horizontal_connector(ch: str) -> bool:
    """字符是否参与水平连接。"""
    return ch in HORIZONTAL_CONNECTORS


def is_vertical_connector(ch: str) -> bool:
    """字符是否参与垂直连接。"""
    return ch in VERTICAL_CONNECTORS


def is_drawing_char(ch: str) -> bool:
    """字符是否属于绘图字符（连接符、角点、箭头）。"""
    return (
        ch in HORIZONTAL_CONNECTORS
        or ch in VERTICAL_CONNECTORS
        or ch in UNICODE_ARROWS
        or ch in "vV^<>"
    )


class AsciiAnalyzer:
    """
    ASCII 图特征分析器。

    将 ASCII 图文本解析为字符网格，提取方框、箭头、生命线、
    时序消息、类结构与树形节点，供下游类型检测与转换使用。
    """

    # 最大搜索半径（内容型盒子可能很高，需要足够大的上限）
    MAX_GAP: int = 120
    # 边框列容差（应对全角字符导致的行边界轻微错位）
    BORDER_TOL: int = 2

    @classmethod
    def analyze(cls, text: str) -> DiagramFeatures:
        """
        分析 ASCII 图文本。

        参数:
            text: ASCII 图原始内容

        返回:
            DiagramFeatures: 特征分析结果
        """
        lines = text.splitlines() if text else []
        grid = cls.normalize_grid(lines)
        boxes = cls.extract_boxes(grid)
        arrows = cls._filter_arrows_inside_boxes(cls.extract_arrows(grid), boxes)
        junction_rows = cls.extract_junction_rows(grid)
        lifelines = cls.extract_lifelines(grid, boxes)
        messages = cls.extract_messages(grid, lifelines)
        class_boxes = cls.extract_class_boxes(grid, boxes)
        class_relations = cls.extract_class_relations(grid, class_boxes)
        tree_nodes = cls.extract_tree_nodes(grid)

        horizontal_count = sum(1 for line in grid for ch in line if ch in HORIZONTAL_CONNECTORS)
        vertical_count = sum(1 for line in grid for ch in line if ch in VERTICAL_CONNECTORS)

        return DiagramFeatures(
            grid=grid,
            boxes=tuple(boxes),
            arrows=tuple(arrows),
            lifelines=tuple(lifelines),
            messages=tuple(messages),
            class_boxes=tuple(class_boxes),
            class_relations=tuple(class_relations),
            tree_nodes=tuple(tree_nodes),
            junction_rows=tuple(sorted(junction_rows)),
            horizontal_connectors=horizontal_count,
            vertical_connectors=vertical_count,
        )

    # ============================================================
    # 网格
    # ============================================================

    @classmethod
    def normalize_grid(cls, lines: List[str]) -> Tuple[str, ...]:
        """
        将输入行规范化为按显示宽度对齐的等宽网格。

        全角/宽字符（如中文）在终端中占 2 列，直接按码点索引会导致
        方框边界错位；这里将宽字符展开为「字符 + 填充符」两格，
        使所有行的边界在列坐标上对齐。

        参数:
            lines: 原始行列表

        返回:
            Tuple[str, ...]: 等宽字符串元组（含填充符）
        """
        expanded: List[List[str]] = []
        width = 0
        for line in lines:
            cells: List[str] = []
            for ch in line:
                cells.append(ch)
                if char_display_width(ch) == 2:
                    cells.append(FILLER)
            expanded.append(cells)
            width = max(width, len(cells))
        return tuple("".join(cells).ljust(width, FILLER) for cells in expanded)

    @staticmethod
    def _strip_filler(text: str) -> str:
        """移除网格中的宽字符占位填充符。"""
        return text.replace(FILLER, "")

    # ============================================================
    # 方框
    # ============================================================

    @classmethod
    def extract_boxes(cls, grid: Tuple[str, ...]) -> List[Box]:
        """
        提取闭合矩形方框。

        方框由水平顶边/底边、垂直左右边围成；
        顶边与底边的左右端点为角点或连接符。
        """
        height = len(grid)
        boxes: List[Box] = []
        seen: Set[Tuple[int, int, int, int]] = set()

        for r in range(height - 1):
            runs = cls._horizontal_runs(grid, r)
            for c0, c1 in runs:
                if c1 - c0 < 3:
                    continue
                left_ok = cls._connects_vertical(grid, r, c0)
                right_ok = cls._connects_vertical(grid, r, c1)
                if not (left_ok and right_ok):
                    continue
                # 向下寻找匹配的底边
                bottom = cls._find_bottom_edge(grid, r, c0, c1)
                if bottom is None:
                    continue
                key = (r, c0, bottom, c1)
                if key in seen:
                    continue
                seen.add(key)
                interior = [
                    cls._strip_filler(grid[k][c0 + 1 : c1]).strip("│┃| ")
                    for k in range(r + 1, bottom)
                ]
                boxes.append(Box(x0=c0, x1=c1, y0=r, y1=bottom, lines=tuple(interior)))

        # 稳定排序：按行、按列
        boxes.sort(key=lambda b: (b.y0, b.x0))
        return boxes

    @staticmethod
    def _horizontal_runs(grid: Tuple[str, ...], row: int) -> List[Tuple[int, int]]:
        """提取某行中所有水平连接符连续段。"""
        runs: List[Tuple[int, int]] = []
        start: Optional[int] = None
        line = grid[row]
        for col, ch in enumerate(line):
            if ch in HORIZONTAL_RUN_CONNECTORS:
                if start is None:
                    start = col
            else:
                if start is not None:
                    runs.append((start, col - 1))
                    start = None
        if start is not None:
            runs.append((start, len(line) - 1))
        return runs

    @classmethod
    def _connects_vertical(cls, grid: Tuple[str, ...], row: int, col: int) -> bool:
        """单元格是否参与垂直连接（自身为垂直连接符）。"""
        if row < 0 or row >= len(grid) or col < 0 or col >= len(grid[row]):
            return False
        return is_vertical_connector(grid[row][col])

    @classmethod
    def _find_bottom_edge(
        cls,
        grid: Tuple[str, ...],
        top_row: int,
        c0: int,
        c1: int,
    ) -> Optional[int]:
        """
        在 top_row 下方寻找与 [c0, c1] 匹配的方框底边。

        采用容差匹配：底边列允许在 ±BORDER_TOL 内抖动；
        中间行只需多数两侧存在垂直边框（应对中文混排导致的行宽不一致）。
        """
        height = len(grid)
        limit = min(top_row + cls.MAX_GAP, height)
        for r in range(top_row + 1, limit):
            bottom_run = cls._match_bottom_run(grid, r, c0, c1)
            if bottom_run is None:
                continue
            interior = list(range(top_row + 1, r))
            if not interior:
                return r
            both_hits = sum(
                1
                for k in interior
                if cls._has_side_border(grid, k, c0, left=True)
                and cls._has_side_border(grid, k, c1, left=False)
            )
            # 两侧边框需同时覆盖绝大多数内容行，
            # 避免箭头通道 / 关系区域被误认为盒子侧边
            if both_hits >= len(interior) * 0.75:
                return r
        return None

    @classmethod
    def _match_bottom_run(
        cls,
        grid: Tuple[str, ...],
        row: int,
        c0: int,
        c1: int,
    ) -> Optional[Tuple[int, int]]:
        """
        在指定行查找与 [c0, c1] 匹配的底边水平段。

        底边要求两端垂直连接、中间水平连接，列允许 ±BORDER_TOL 抖动。
        """
        for rc0, rc1 in cls._horizontal_runs(grid, row):
            if rc1 - rc0 < 3:
                continue
            if abs(rc0 - c0) > cls.BORDER_TOL or abs(rc1 - c1) > cls.BORDER_TOL:
                continue
            if not cls._connects_vertical(grid, row, rc0):
                continue
            if not cls._connects_vertical(grid, row, rc1):
                continue
            return (rc0, rc1)
        return None

    @classmethod
    def _has_side_border(
        cls,
        grid: Tuple[str, ...],
        row: int,
        col: int,
        left: bool,
    ) -> bool:
        """
        判断行在指定列附近是否存在垂直边框。

        参数:
            left: True 表示检查左边界（取容差范围内最靠左的竖线）；
                  False 表示检查右边界（取最靠右的竖线）
        """
        lo = max(0, col - cls.BORDER_TOL)
        hi = min(len(grid[row]), col + cls.BORDER_TOL + 1)
        for c in range(lo, hi):
            if is_vertical_connector(grid[row][c]):
                return True
        return False

    # ============================================================
    # 箭头
    # ============================================================

    @classmethod
    def extract_arrows(cls, grid: Tuple[str, ...]) -> List[Arrow]:
        """提取水平与垂直箭头。"""
        arrows: List[Arrow] = []
        for row, line in enumerate(grid):
            arrows.extend(cls._horizontal_arrows(line, row))
            arrows.extend(cls._vertical_arrows(grid, row, line))

        # 去重并稳定排序
        seen: Set[Tuple[int, int, str]] = set()
        unique: List[Arrow] = []
        for arrow in arrows:
            key = (arrow.row, arrow.col, arrow.direction)
            if key in seen:
                continue
            seen.add(key)
            unique.append(arrow)
        unique.sort(key=lambda a: (a.row, a.col, a.direction))
        return unique

    @classmethod
    def _filter_arrows_inside_boxes(
        cls,
        arrows: List[Arrow],
        boxes: List[Box],
    ) -> List[Arrow]:
        """
        过滤位于方框内部的箭头。

        方框内容中的 `→` 等字符属于文本装饰（如 "A → B"），
        不应被当作流程图箭头；真实箭头位于方框之间。
        """
        if not boxes:
            return arrows
        return [
            arrow
            for arrow in arrows
            if not any(box.x0 < arrow.col < box.x1 and box.y0 < arrow.row < box.y1 for box in boxes)
        ]

    @classmethod
    def _horizontal_arrows(cls, line: str, row: int) -> List[Arrow]:
        """提取一行中的水平箭头。"""
        arrows: List[Arrow] = []

        for col, ch in enumerate(line):
            if ch in "→⇒►▶":
                tail = cls._find_horizontal_tail(line, col - 1, left=True)
                token = line[tail : col + 1].strip() or "->"
                arrows.append(
                    Arrow(
                        row=row,
                        col=col,
                        direction="right",
                        tail_row=row,
                        tail_col=tail,
                        head_row=row,
                        head_col=col,
                        label=cls._left_label(line, tail),
                        token=token,
                    )
                )
            elif ch in "←⇐◄◀":
                head = cls._find_horizontal_tail(line, col + 1, left=False)
                token = line[col : head + 1].strip() or "<-"
                arrows.append(
                    Arrow(
                        row=row,
                        col=col,
                        direction="left",
                        tail_row=row,
                        tail_col=col,
                        head_row=row,
                        head_col=head,
                        label=cls._right_label(line, head + 1),
                        token=token,
                    )
                )
            elif ch in "↔⇔":
                left_tail = cls._find_horizontal_tail(line, col - 1, left=True)
                right_tail = cls._find_horizontal_tail(line, col + 1, left=False)
                arrows.append(
                    Arrow(
                        row=row,
                        col=col,
                        direction="right",
                        tail_row=row,
                        tail_col=left_tail,
                        head_row=row,
                        head_col=right_tail,
                        label=cls._right_label(line, right_tail + 1),
                        token="<->",
                    )
                )
            elif ch == ">":
                tail = cls._find_horizontal_tail(line, col - 1, left=True)
                if col - tail >= 2:
                    token = line[tail : col + 1].strip()
                    arrows.append(
                        Arrow(
                            row=row,
                            col=col,
                            direction="right",
                            tail_row=row,
                            tail_col=tail,
                            head_row=row,
                            head_col=col,
                            label=cls._left_label(line, tail),
                            token=token,
                        )
                    )
            elif ch == "<":
                head = cls._find_horizontal_tail(line, col + 1, left=False)
                if head - col >= 2:
                    token = line[col : head + 1].strip()
                    arrows.append(
                        Arrow(
                            row=row,
                            col=col,
                            direction="left",
                            tail_row=row,
                            tail_col=col,
                            head_row=row,
                            head_col=head,
                            label=cls._right_label(line, head + 1),
                            token=token,
                        )
                    )
        return arrows

    @staticmethod
    def _find_horizontal_tail(line: str, start: int, left: bool) -> int:
        """
        沿箭头方向寻找水平连接符连续段的末端。

        参数:
            line: 当前行
            start: 起始列
            left: True 表示向左搜索（箭头在右），False 表示向右搜索（箭头在左）
        """
        n = len(line)
        if left:
            col = start
            while col >= 0 and line[col] in HORIZONTAL_CONNECTORS:
                col -= 1
            return col + 1
        col = start
        while col < n and line[col] in HORIZONTAL_CONNECTORS:
            col += 1
        return col - 1

    @staticmethod
    def _right_label(line: str, start: int) -> str:
        """提取箭头右侧的标签文本。"""
        tail = AsciiAnalyzer._strip_filler(line[start:]).strip()
        if tail.startswith(":"):
            tail = tail[1:].strip()
        return AsciiAnalyzer._clean_label(tail)

    @staticmethod
    def _left_label(line: str, tail: int) -> str:
        """
        提取水平箭头左侧的标签文本。

        仅当箭头尾部前一个词包含字母/数字时视为标签，
        避免误取方框边框（如 `|`）。
        """
        prefix = AsciiAnalyzer._strip_filler(line[:tail]).rstrip()
        if not prefix:
            return ""
        token = prefix.split()[-1]
        if any(ch.isalnum() for ch in token):
            return token
        return ""

    @staticmethod
    def _clean_label(text: str) -> str:
        """
        清理标签文本：移除首尾的方框边框与连接符。
        """
        text = AsciiAnalyzer._strip_filler(text)
        drawing = "─━═-–—│┃║|:┌┐└┘├┤┬┴┼╠╣╦╩╬+*"
        text = text.strip()
        while text and text[0] in drawing:
            text = text[1:].strip()
        while text and text[-1] in drawing:
            text = text[:-1].strip()
        return text

    @classmethod
    def _vertical_arrows(
        cls,
        grid: Tuple[str, ...],
        row: int,
        line: str,
    ) -> List[Arrow]:
        """提取一行中的垂直箭头。"""
        arrows: List[Arrow] = []
        height = len(grid)
        for col, ch in enumerate(line):
            if ch in "↓▼▽vV":
                # 词内的 v/V（如 converter）是文本，不是箭头
                if ch in "vV" and (
                    cls._is_word_char(line, col - 1) or cls._is_word_char(line, col + 1)
                ):
                    continue
                tail = row
                while (
                    tail - 1 >= 0
                    and row - tail < cls.MAX_GAP
                    and is_vertical_connector(grid[tail - 1][col])
                ):
                    tail -= 1
                arrows.append(
                    Arrow(
                        row=row,
                        col=col,
                        direction="down",
                        tail_row=tail,
                        tail_col=col,
                        head_row=row,
                        head_col=col,
                        label=cls._vertical_label(grid, row, col),
                        token="v" if ch in "vV" else ch,
                    )
                )
            elif ch in "↑▲△^":
                if ch == "^" and (
                    cls._is_word_char(line, col - 1) or cls._is_word_char(line, col + 1)
                ):
                    continue
                head = row
                while (
                    head + 1 < height
                    and head - row < cls.MAX_GAP
                    and is_vertical_connector(grid[head + 1][col])
                ):
                    head += 1
                arrows.append(
                    Arrow(
                        row=row,
                        col=col,
                        direction="up",
                        tail_row=row,
                        tail_col=col,
                        head_row=head,
                        head_col=col,
                        label=cls._vertical_label(grid, row, col),
                        token="^" if ch in "^" else ch,
                    )
                )
        return arrows

    @staticmethod
    def _is_word_char(line: str, col: int) -> bool:
        """列位置上的字符是否为单词字符（字母/数字/下划线）。"""
        if col < 0 or col >= len(line):
            return False
        ch = line[col]
        return ch.isalnum() or ch == "_"

    @staticmethod
    def _vertical_label(grid: Tuple[str, ...], row: int, col: int) -> str:
        """提取垂直箭头右侧的标签。"""
        if row + 1 < len(grid):
            candidate = AsciiAnalyzer._strip_filler(grid[row + 1][col + 1 :]).strip()
            if candidate:
                return AsciiAnalyzer._clean_label(candidate)
        if col + 1 < len(grid[row]):
            return AsciiAnalyzer._clean_label(AsciiAnalyzer._strip_filler(grid[row][col + 1 :]))
        return ""

    # ============================================================
    # 分支连接符
    # ============================================================

    @classmethod
    def extract_junction_rows(cls, grid: Tuple[str, ...]) -> Set[int]:
        """提取包含分支连接符的行。"""
        rows: Set[int] = set()
        for r, line in enumerate(grid):
            for c, ch in enumerate(line):
                if ch not in JUNCTION_CHARS and ch != "+":
                    continue
                if cls._is_junction(grid, r, c):
                    rows.add(r)
                    break
        return rows

    @staticmethod
    def _is_junction(grid: Tuple[str, ...], row: int, col: int) -> bool:
        """
        判断单元格是否为分支连接符。

        要求水平两侧均有水平连接，且上方或下方有垂直连接。
        """
        line = grid[row]
        if col <= 0 or col >= len(line) - 1:
            return False
        left_h = is_horizontal_connector(line[col - 1])
        right_h = is_horizontal_connector(line[col + 1])
        if not (left_h and right_h):
            return False
        above = row - 1 >= 0 and is_vertical_connector(grid[row - 1][col])
        below = row + 1 < len(grid) and is_vertical_connector(grid[row + 1][col])
        return above or below

    # ============================================================
    # 时序图
    # ============================================================

    @classmethod
    def extract_lifelines(
        cls,
        grid: Tuple[str, ...],
        boxes: Optional[List[Box]] = None,
    ) -> List[Lifeline]:
        """
        提取生命线（垂直虚线/实线列）。

        参数:
            grid: 字符网格
            boxes: 已检测的方框；位于方框边框或内部的竖线
                   属于盒子边框而非生命线，会被过滤
        """
        height = len(grid)
        candidates: List[Lifeline] = []

        for col in range(len(grid[0]) if grid else 0):
            spans: List[Tuple[int, int]] = []
            start: Optional[int] = None
            for r in range(height):
                ch = grid[r][col]
                if ch in VERTICAL_CHARS:
                    if start is None:
                        start = r
                else:
                    if start is not None and r - start >= 3:
                        spans.append((start, r - 1))
                    start = None
            if start is not None and height - start >= 3:
                spans.append((start, height - 1))

            for y0, y1 in spans:
                if cls._inside_any_box(boxes, col, y0, y1):
                    continue
                label = cls._lifeline_label(grid, col, y0, boxes)
                candidates.append(Lifeline(col=col, y0=y0, y1=y1, label=label))

        # 合并相邻列（同一生命线的加粗/双线效果）
        merged: List[Lifeline] = []
        for line_item in sorted(candidates, key=lambda ll: (ll.y1 - ll.y0, ll.col), reverse=True):
            if any(abs(line_item.col - m.col) <= 2 for m in merged):
                continue
            merged.append(line_item)
        merged.sort(key=lambda ll: ll.col)
        return merged

    @classmethod
    def _inside_any_box(
        cls,
        boxes: Optional[List[Box]],
        col: int,
        y0: int,
        y1: int,
    ) -> bool:
        """
        竖线是否为某个方框的边框或内部。

        堆叠方框共享边框时，跨盒竖线也按边框处理。
        """
        if not boxes:
            return False
        for box in boxes:
            inside = box.x0 <= col <= box.x1 and box.y0 <= y0 <= y1 <= box.y1
            on_border = (
                min(abs(col - box.x0), abs(col - box.x1)) <= cls.BORDER_TOL
                and box.y0 <= y0 <= box.y1
            )
            if inside or on_border:
                return True
        return False

    @classmethod
    def _lifeline_label(
        cls,
        grid: Tuple[str, ...],
        col: int,
        y0: int,
        boxes: Optional[List[Box]] = None,
    ) -> str:
        """
        查找生命线上方的参与者标签。

        优先取上方最近的方框，其次取同行文本。
        """
        candidates = [b for b in (boxes or []) if b.contains_col(col) and b.y1 < y0]
        if candidates:
            nearest = max(candidates, key=lambda b: b.y1)
            text = nearest.text.strip()
            if text:
                return text
        # 直接文本
        for r in range(max(0, y0 - 6), y0):
            left = cls._strip_filler(grid[r][:col]).rstrip()
            if left:
                word = left.split()[-1] if left.split() else ""
                if word:
                    return word
        return ""

    @classmethod
    def extract_messages(
        cls,
        grid: Tuple[str, ...],
        lifelines: List[Lifeline],
    ) -> List[Message]:
        """提取时序消息。"""
        messages: List[Message] = []
        if not lifelines:
            return messages

        for row, line in enumerate(grid):
            arrows = cls._horizontal_arrows(line, row)
            if not arrows:
                continue
            left_arrow = min(arrows, key=lambda a: a.tail_col)
            right_arrow = max(arrows, key=lambda a: a.head_col)
            tail_l = cls._nearest_lifeline(lifelines, left_arrow.tail_col, prefer_left=True)
            head_l = cls._nearest_lifeline(lifelines, right_arrow.head_col, prefer_left=False)
            if tail_l is None or head_l is None or tail_l.col == head_l.col:
                continue

            if left_arrow is right_arrow:
                if left_arrow.direction == "right":
                    text = cls._strip_filler(line[tail_l.col + 1 : left_arrow.tail_col]).strip()
                else:
                    text = cls._strip_filler(line[right_arrow.head_col + 1 : head_l.col]).strip()
                token = left_arrow.token
            else:
                text = cls._strip_filler(
                    line[left_arrow.head_col + 1 : right_arrow.tail_col]
                ).strip()
                token = right_arrow.token
                if right_arrow.direction == "left":
                    token = cls._mirror_token(token)

            text = cls._clean_label(text)
            left, right = sorted([tail_l, head_l], key=lambda ll: ll.col)
            messages.append(
                Message(
                    row=row,
                    col0=left.col,
                    col1=right.col,
                    direction="right",
                    token=token,
                    text=text,
                )
            )

        # 去重
        seen: Set[Tuple[int, int, int, str]] = set()
        unique: List[Message] = []
        for msg in messages:
            key = (msg.row, msg.col0, msg.col1, msg.text)
            if key in seen:
                continue
            seen.add(key)
            unique.append(msg)
        unique.sort(key=lambda m: (m.row, m.col0))
        return unique

    @staticmethod
    def _nearest_lifeline(
        lifelines: List[Lifeline],
        col: int,
        prefer_left: bool,
    ) -> Optional[Lifeline]:
        """查找距离列最近的参与者。"""
        if not lifelines:
            return None
        lefts = [ll for ll in lifelines if ll.col <= col]
        rights = [ll for ll in lifelines if ll.col >= col]
        if prefer_left:
            if lefts:
                return max(lefts, key=lambda ll: ll.col)
            return min(rights, key=lambda ll: ll.col) if rights else None
        if rights:
            return min(rights, key=lambda ll: ll.col)
        return max(lefts, key=lambda ll: ll.col) if lefts else None

    @staticmethod
    def _mirror_token(token: str) -> str:
        """反转水平箭头记号方向。"""
        if "<" in token and ">" in token:
            return token
        if token.startswith("<"):
            return token[1:] + ">"
        if token.endswith("<"):
            return ">" + token[:-1]
        return token

    # ============================================================
    # 类图
    # ============================================================

    @classmethod
    def extract_class_boxes(
        cls,
        grid: Tuple[str, ...],
        boxes: List[Box],
    ) -> List[ClassBox]:
        """从方框中提取类方框（含分节与构造型）。"""
        class_boxes: List[ClassBox] = []
        for box in cls._merge_stacked_boxes(boxes):
            sections = cls._split_sections(box, grid)
            if len(sections) < 2:
                continue
            title_lines = sections[0]
            title = " ".join(t.strip() for t in title_lines if t.strip())
            stereotype = cls._extract_stereotype(title)
            content = sections[1:]
            if not stereotype and not cls._has_visibility_markers(content):
                continue
            name = cls._strip_stereotype(title)
            parts: List[ClassSection] = [ClassSection(kind="title", lines=tuple(title_lines))]
            for group in content:
                kind = "methods" if cls._looks_like_methods(group) else "attributes"
                parts.append(ClassSection(kind=kind, lines=tuple(group)))
            class_boxes.append(
                ClassBox(box=box, name=name, stereotype=stereotype, sections=tuple(parts))
            )
        return class_boxes

    @classmethod
    def _merge_stacked_boxes(cls, boxes: List[Box]) -> List[Box]:
        """
        合并共享边框、垂直相邻的方框。

        典型 UML ASCII 类图用整行分隔线切分成员区，会被识别为
        多个垂直堆叠的小方框；这里合并为单个逻辑方框。
        """
        if not boxes:
            return []
        grouped: dict = {}
        for box in boxes:
            grouped.setdefault((box.x0, box.x1), []).append(box)

        merged: List[Box] = []
        for group in grouped.values():
            group.sort(key=lambda b: b.y0)
            current = group[0]
            for box in group[1:]:
                if box.y0 == current.y1:
                    current = Box(
                        x0=current.x0,
                        x1=current.x1,
                        y0=current.y0,
                        y1=box.y1,
                        lines=current.lines + box.lines,
                    )
                else:
                    merged.append(current)
                    current = box
            merged.append(current)
        merged.sort(key=lambda b: (b.y0, b.x0))
        return merged

    @staticmethod
    def _top_level_boxes(boxes: List[Box]) -> List[Box]:
        """
        返回不被其他方框包含的最外层方框。

        内容盒内可能内嵌示例图（嵌套方框），转换时应取最外层盒。
        """
        result = []
        for box in boxes:
            contained = any(
                other is not box
                and other.x0 <= box.x0
                and other.x1 >= box.x1
                and other.y0 <= box.y0
                and other.y1 >= box.y1
                for other in boxes
            )
            if not contained:
                result.append(box)
        return result

    @classmethod
    def is_landscape_layout(cls, boxes: List[Box]) -> bool:
        """
        判断是否为嵌套盒分层布局（如「对标产品全景」）。

        特征：存在三层嵌套（容器 → 类别盒 → 产品盒），
        且至少有 2 个中间层盒子。
        """
        merged = cls._merge_stacked_boxes(list(boxes))
        if len(merged) < 6:
            return False
        depths = []
        for box in merged:
            depths.append(
                sum(
                    1
                    for other in merged
                    if other is not box
                    and other.x0 <= box.x0
                    and other.x1 >= box.x1
                    and other.y0 <= box.y0
                    and other.y1 >= box.y1
                )
            )
        return max(depths) >= 2 and sum(1 for depth in depths if depth >= 1) >= 2

    @classmethod
    def _split_sections(
        cls,
        box: Box,
        grid: Tuple[str, ...],
    ) -> List[List[str]]:
        """按水平分隔线将方框内部拆分为若干节。"""
        sections: List[List[str]] = []
        current: List[str] = []
        width = max(1, box.x1 - box.x0 - 1)
        for k in range(box.y0 + 1, box.y1):
            segment = cls._strip_filler(grid[k][box.x0 + 1 : box.x1])
            # 仅当外侧边框抖动到切片内时才去除，保留内嵌盒子边框
            left_ok = k < len(grid) and grid[k][box.x0] in "│┃|"
            right_ok = k < len(grid) and box.x1 < len(grid[k]) and grid[k][box.x1] in "│┃|"
            segment = segment.rstrip()
            if not right_ok and segment and segment[-1] in "│┃|":
                segment = segment[:-1].rstrip()
            if not left_ok and segment and segment[0] in "│┃|":
                segment = segment[1:].lstrip()
            stripped = segment.strip()
            if not stripped:
                continue
            if cls._is_separator(segment, width):
                if current:
                    sections.append(current)
                    current = []
            else:
                current.append(segment.rstrip())
        if current:
            sections.append(current)
        return sections

    @staticmethod
    def _is_separator(segment: str, width: int) -> bool:
        """判断行是否为水平分隔线。"""
        stripped = segment.strip()
        if not stripped:
            return False
        connector_count = sum(1 for ch in stripped if ch in HORIZONTAL_CONNECTORS)
        return connector_count >= max(2, int(width * 0.7))

    @staticmethod
    def _extract_stereotype(title: str) -> str:
        """提取 <<...>> 构造型。"""
        match = re.search(r"<<\s*([^>]+?)\s*>>", title)
        return match.group(1).strip().lower() if match else ""

    @staticmethod
    def _strip_stereotype(title: str) -> str:
        """移除构造型后的类名。"""
        return re.sub(r"<<\s*[^>]+?\s*>>", "", title).strip()

    @staticmethod
    def _has_visibility_markers(sections: List[List[str]]) -> bool:
        """
        内容节中是否包含类成员可见性标记（+ - # ~）。

        仅当成员形如类型化属性（`- name: str`）或 ASCII 方法签名
        （`+ getName()`）时计为类成员；自由文本列表项（`- VSCode插件`）
        不算，避免内容盒误判为类图。
        """
        member_pattern = re.compile(
            r"^[+\-#~]\s*[A-Za-z_]\w*\s*"
            r"(?:\(\s*[A-Za-z_0-9,.\s]*\)\s*$"
            r"|:\s*[A-Za-z_0-9<>\[\].]+\s*$)"
        )
        for group in sections:
            for line in group:
                stripped = line.strip()
                if stripped and member_pattern.match(stripped):
                    return True
        return False

    @staticmethod
    def _looks_like_methods(lines: List[str]) -> bool:
        """内容行是否更像方法（包含括号）。"""
        return any("(" in line for line in lines)

    @classmethod
    def extract_class_relations(
        cls,
        grid: Tuple[str, ...],
        class_boxes: List[ClassBox],
    ) -> List[ClassRelation]:
        """提取类之间的关系。"""
        if len(class_boxes) < 2:
            return []
        relations: List[ClassRelation] = []
        seen: Set[Tuple[str, str, str]] = set()

        for row, line in enumerate(grid):
            for start, end, _token, kind, child_left in cls._uml_tokens(line):
                left = cls._nearest_class_box(class_boxes, row, start, side="left")
                right = cls._nearest_class_box(class_boxes, row, end, side="right")
                above = cls._nearest_class_box(class_boxes, row, start, side="above")
                below = cls._nearest_class_box(class_boxes, row, start, side="below")

                if left is not None and right is not None:
                    src = left.name if child_left else right.name
                    dst = right.name if child_left else left.name
                elif above is not None and below is not None:
                    src = above.name if child_left else below.name
                    dst = below.name if child_left else above.name
                else:
                    continue
                key = (src, dst, kind)
                if key in seen:
                    continue
                seen.add(key)
                relations.append(ClassRelation(src=src, dst=dst, kind=kind))
        return relations

    @staticmethod
    def _uml_tokens(line: str) -> List[Tuple[int, int, str, str, bool]]:
        """
        识别 UML 关系记号。

        返回 (起始列, 结束列, 记号, 关系类型, 左侧是否为子类/源)。
        """
        patterns = [
            (r"<\|--", "inheritance", True),
            (r"--\|>", "inheritance", True),
            (r"\.\.\|>", "realization", True),
            (r"<\|\.\.", "realization", True),
            (r"\*--", "composition", True),
            (r"o--", "aggregation", True),
            (r"\.\.>", "dependency", True),
            (r"--\*>", "dependency", True),
            (r"--\>", "association", True),
            (r"<--", "association", True),
            (r"--", "link", True),
        ]
        # 长记号优先，避免 `--` 吞掉 `--|>`
        patterns.sort(key=lambda p: len(p[0]), reverse=True)
        found: List[Tuple[int, int, str, str, bool]] = []
        occupied: Set[int] = set()
        for pattern, kind, child_left in patterns:
            for match in re.finditer(pattern, line):
                if any(pos in occupied for pos in range(match.start(), match.end())):
                    continue
                found.append(
                    (
                        match.start(),
                        match.end(),
                        match.group(0),
                        kind,
                        child_left,
                    )
                )
                occupied.update(range(match.start(), match.end()))
        return found

    @staticmethod
    def _nearest_class_box(
        class_boxes: List[ClassBox],
        row: int,
        col: int,
        side: str,
    ) -> Optional[ClassBox]:
        """
        按方位查找最近的类方框。

        距离 = 主轴距离 + 0.5 * 副轴距离；超过 12 行的候选忽略。
        """
        candidates: List[tuple] = []
        for cb in class_boxes:
            box = cb.box
            if side == "left" and box.x1 >= col:
                continue
            if side == "right" and box.x0 <= col:
                continue
            if side == "above" and box.y1 >= row:
                continue
            if side == "below" and box.y0 <= row:
                continue
            if side in ("left", "right"):
                primary = col - box.x1 if side == "left" else box.x0 - col
                secondary = abs(box.center_y - row)
            else:
                primary = row - box.y1 if side == "above" else box.y0 - row
                secondary = abs(box.center_x - col)
            if primary > 12 or secondary > 12:
                continue
            candidates.append((primary + 0.5 * secondary, cb))
        if not candidates:
            return None
        return min(candidates, key=lambda t: t[0])[1]

    # ============================================================
    # 思维导图
    # ============================================================

    @classmethod
    def extract_tree_nodes(cls, grid: Tuple[str, ...]) -> List[TreeNode]:
        """
        提取树形节点。

        优先识别 `├──` / `└──` / `|--` / `\\--` 等分支前缀并据此计算深度；
        否则基于缩进计算深度。
        """
        if cls._looks_like_markdown_text(grid):
            return []
        raw: List[Tuple[int, str, int]] = []
        has_branch = False
        for row, line in enumerate(grid):
            stripped = cls._strip_filler(line).rstrip()
            if not stripped.strip():
                continue
            indent = len(stripped) - len(stripped.lstrip(" "))
            content = stripped.strip()
            if not content:
                continue
            raw.append((indent, content, row))

        if len(raw) < 2:
            return []

        processed: List[Tuple[int, str, int]] = []
        for indent, content, row in raw:
            content = re.sub(r"^[*-]\s+", "", content)
            if not content:
                continue
            branch = cls._branch_depth(content, indent)
            if branch is not None:
                has_branch = True
                processed.append((branch, cls._branch_text(content), row))
            else:
                processed.append((indent, content, row))

        if has_branch:
            nodes = [TreeNode(text=text, depth=depth, row=row) for depth, text, row in processed]
        else:
            # 纯缩进树要求文本行，不包含方框/箭头结构
            structured_lines = 0
            for _, text, _ in processed:
                drawing_count = sum(1 for ch in text if is_drawing_char(ch))
                if drawing_count >= 2:
                    structured_lines += 1
            if structured_lines > 0:
                return []
            # 纯缩进至少需要 3 个节点且多个子节点，避免误判代码片段
            if len(processed) < 3:
                return []
            min_indent = min(indent for indent, _, _ in processed)
            nodes = [
                TreeNode(
                    text=text,
                    depth=max(0, (indent - min_indent) // 2),
                    row=row,
                )
                for indent, text, row in processed
            ]
            if sum(1 for n in nodes if n.depth >= 1) < 2:
                return []

        # 需要至少一层嵌套才认为是树
        if max((n.depth for n in nodes), default=0) < 1:
            return []
        return nodes

    @staticmethod
    def _looks_like_markdown_text(grid: Tuple[str, ...]) -> bool:
        """
        判断网格内容是否为 Markdown 文档文本（示例代码）。

        出现标题、表格、复选框或粗体标签列表等 Markdown 语法时，
        说明内容是文档示例而非 ASCII 图，不应转为树形图。
        """
        heading = re.compile(r"^#{1,6}\s")
        table = re.compile(r"^\|.*\|$")
        checkbox = re.compile(r"^-\s*\[[ xX]\]")
        bold_label = re.compile(r"^\*\*[^*]+\*\*[：:]\s*$")
        dash_item = re.compile(r"^[-*]\s+")
        has_bold_label = False
        has_dash_item = False
        for line in grid:
            stripped = line.strip()
            if not stripped:
                continue
            if heading.match(stripped) or table.match(stripped) or checkbox.match(stripped):
                return True
            if bold_label.match(stripped):
                has_bold_label = True
            if dash_item.match(stripped):
                has_dash_item = True
        return has_bold_label and has_dash_item

    @staticmethod
    @staticmethod
    def _branch_depth(content: str, indent: int = 0) -> Optional[int]:
        """
        若行包含树形分支前缀，返回其深度；否则返回 None。

        深度 = 1 + `│`/`|` 延续符数量 + 纯空格缩进层级；
        兼容 `│   ├──` 与 `    ├──` 两种续行风格。
        """
        match = re.search(
            r"(?:[├└┌][─\-]|[│|][─\-]|[\\`][─\-]|\+[─\-]|[│|]_)[─\-=]*-?\s*",
            content,
        )
        if not match:
            return None
        rest = content[match.end() :].strip()
        if not rest or all(ch in "─━═-–—│┃║|:┌┐└┘├┤┬┴┼╠╣╦╩╬+*" or ch.isspace() for ch in rest):
            return None
        # 拒绝包含其他箭头/生命线结构的行（如时序消息 `|--- msg ---->|`）
        if re.search(r"[<>^]", rest) or rest.endswith(("|", "│", "┐", "┘")):
            return None
        prefix = content[: match.start()]
        bars = prefix.count("│") + prefix.count("|")
        marker_col = indent + match.start()
        space_levels = max(0, (marker_col - 4 * bars) // 4)
        return 1 + bars + space_levels

    @staticmethod
    def _branch_text(content: str) -> str:
        """移除树形分支前缀，提取节点文本。"""
        match = re.search(
            r"(?:[├└┌][─\-]|[│|][─\-]|[\\`][─\-]|\+[─\-]|[│|]_)[─\-=]*-?\s*",
            content,
        )
        if not match:
            return content
        return content[match.end() :].strip()
