"""
流程图转换器

将带方框与箭头的 ASCII 图转换为 Mermaid flowchart。
支持上→下与左→右两种主流布局方向。
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

from ..analyzer import AsciiAnalyzer, is_horizontal_connector
from ..model import Arrow, Box, DiagramFeatures, TreeNode
from .base import BaseConverter, escape_mermaid_label, node_id


class FlowchartConverter(BaseConverter):
    """方框 + 箭头 → Mermaid flowchart。"""

    diagram_type = "flowchart"
    MAX_GAP = 24

    def convert(self, features: DiagramFeatures) -> Optional[str]:
        # 树形结构（目录树/层级树）→ flowchart，文件夹/文件节点 + 样式
        if features.tree_nodes and not features.boxes and not features.messages:
            mermaid = self._convert_tree(features)
            if mermaid:
                return mermaid
            # 多根 + 垂直箭头 → 文本流程（分支汇合型）
            mermaid = self._convert_text_flow(features)
            if mermaid:
                return mermaid

        boxes = list(features.boxes)
        arrows = list(features.arrows)
        if boxes:
            # 嵌套盒布局（产品全景 / 内嵌盒图）优先于内容盒
            if AsciiAnalyzer.is_landscape_layout(boxes):
                mermaid = self._convert_landscape(features)
                if mermaid:
                    return mermaid
            if self._has_inner_box_graph(features):
                mermaid = self._convert_inner_box_graph(features)
                if mermaid:
                    return mermaid
            # 纵向堆叠方框图（多个大框自上而下连接，框内含条目/内嵌小框）
            if self._has_stack_layout(features):
                mermaid = self._convert_stack_boxes(features)
                if mermaid:
                    return mermaid

        # 内容盒（标题 + 分节内容，无箭头/生命线）→ flowchart with subgraph
        if (
            not features.arrows
            and not features.lifelines
            and not features.messages
            and not features.class_boxes
        ):
            content = self._convert_content_box(features)
            if content:
                return content

        if boxes and self._has_nested_boxes(boxes):
            # 嵌套方框（无法归类的内容盒）不是简单流程图
            return None
        if self._has_nested_boxes(boxes):
            # 嵌套方框（如内容盒内嵌示例图）不是简单流程图
            return None
        if self._is_structured_flow(boxes):
            mermaid = self._convert_structured_flow(features, boxes, arrows)
            if mermaid:
                return mermaid

        direction = self._detect_direction(arrows)
        edges = self._build_edges(boxes, arrows, features)

        lines = [f"flowchart {direction}"]
        for i, box in enumerate(boxes):
            label = box.text
            if not label:
                continue
            label_html = "<br/>".join(
                escape_mermaid_label(self._strip_ascii_branch(part)) for part in label.splitlines()
            )
            lines.append(f'    {node_id(i)}["{label_html}"]')

        for src, dst, label in edges:
            if src == dst:
                continue
            if label:
                edge_label = escape_mermaid_label(label)
                lines.append(f"    {src} -->|{edge_label}| {dst}")
            else:
                lines.append(f"    {src} --> {dst}")

        return "\n".join(lines)

    # ============================================================
    # 纵向堆叠方框图（多个大框 + 内嵌小框，自上而下连接）
    # ============================================================

    def _has_stack_layout(self, features: DiagramFeatures) -> bool:
        """是否存在纵向堆叠方框图：同一列至少有 2 行以 ┌ 开头的顶边。"""
        col_counts: Dict[int, int] = {}
        for line in features.grid:
            match = re.match(r"^\s*┌", line)
            if match:
                col = len(line) - len(line.lstrip(" "))
                col_counts[col] = col_counts.get(col, 0) + 1
        return max(col_counts.values(), default=0) >= 2

    def _convert_stack_boxes(self, features: DiagramFeatures) -> Optional[str]:
        """
        纵向堆叠方框图 → flowchart（每个大方框一个 subgraph，按顺序连接）。

        直接基于原始网格解析顶层方框（同一列的 ┌…┐ 顶边与 └…┘ 底边），
        方框内容提取标题与条目；内嵌小框（┌…┐）解析为条目节点。
        """
        boxes = self._parse_stack_boxes(list(features.grid))
        if len(boxes) < 2:
            return None
        # 简单纵向流（每个框只有标题、无内容条目）交给旧路径生成扁平节点
        if all(not items for _, items in boxes):
            return None

        lines = ["flowchart TD"]
        for index, (title, items) in enumerate(boxes, start=1):
            bid = f"B{index}"
            lines.append(f'    subgraph {bid}["{escape_mermaid_label(title)}"]')
            lines.append("        direction TB")
            for j, item in enumerate(items, start=1):
                lines.append(f'        {bid}_{j}["{escape_mermaid_label(item)}"]')
            lines.append("    end")
        for i in range(1, len(boxes)):
            lines.append(f"    B{i} --> B{i + 1}")
        return "\n".join(lines)

    @classmethod
    def _parse_stack_boxes(cls, grid: List[str]) -> List[Tuple[str, List[str]]]:
        """解析纵向堆叠的顶层方框，返回 [(标题, 条目列表), ...]。"""
        boxes: List[Tuple[str, List[str]]] = []
        i = 0
        n = len(grid)
        while i < n:
            line = grid[i]
            match = re.match(r"^\s*┌", line)
            if not match:
                i += 1
                continue
            col0 = len(line) - len(line.lstrip(" "))
            bottom = None
            j = i + 1
            while j < n:
                bline = grid[j]
                if re.match(r"^\s*└", bline) and (len(bline) - len(bline.lstrip(" "))) == col0:
                    bottom = j
                    break
                j += 1
            if bottom is None:
                i += 1
                continue
            title, items = cls._extract_box_content(grid[i + 1 : bottom])
            if title:
                boxes.append((title, items))
            i = bottom + 1
        return boxes

    @classmethod
    def _extract_box_content(
        cls,
        rows: List[str],
    ) -> Tuple[str, List[str]]:
        """
        从方框内容行提取标题与条目（含内嵌小框解析）。

        内嵌小框按其 ┌…┐ 顶边与 └…┘ 底边的列区间读取文本；
        方框外内容行去除 │ 边框与 ├── / └── 分支前缀后作为条目。
        """
        # 1) 定位内嵌小框区域（顶边 ┌ 到同列底边 └）
        inner_regions: List[Tuple[int, int, int, int]] = []
        i = 0
        while i < len(rows):
            line = rows[i]
            spans = [(m.start(), line.find("┐", m.start())) for m in re.finditer("┌", line)]
            valid_spans = [(c0, c1) for c0, c1 in spans if c1 != -1]
            if not valid_spans:
                i += 1
                continue
            max_bottom = i
            for c0, c1 in valid_spans:
                j = i + 1
                while j < len(rows) and not (len(rows[j]) > c0 and rows[j][c0] == "└"):
                    j += 1
                if j < len(rows):
                    inner_regions.append((i, j, c0, c1))
                    max_bottom = max(max_bottom, j)
            i = max_bottom + 1

        def in_region(row: int) -> bool:
            return any(r0 <= row <= r1 for r0, r1, _, _ in inner_regions)

        # 2) 标题：第一个非空、非内嵌区域、非纯边框的行
        title = ""
        for r, raw in enumerate(rows):
            text = cls._clean_box_line(raw)
            if text and not in_region(r) and not cls._is_border_only(text):
                title = text
                break

        # 3) 条目：按行序提取（内嵌小框内容行 → 各自方框文本；其余行 → 文本条目）
        items: List[str] = []
        for r, raw in enumerate(rows):
            for r0, r1, c0, c1 in inner_regions:
                if r0 < r < r1:
                    # 右边界取 c1 之后第一个 │（源图方框可能错位一列）
                    right = len(raw)
                    for pos in range(c1, len(raw)):
                        if raw[pos] == "│":
                            right = pos
                            break
                    segment = raw[c0 + 1 : right] if len(raw) > c0 else ""
                    segment = segment.replace("\x00", "")
                    text = re.sub(r"^[\s│]+", "", segment)
                    text = re.sub(r"[\s│]+$", "", text)
                    text = cls._strip_ascii_branch(text).strip()
                    if text:
                        items.append(text)
            if in_region(r):
                continue
            text = cls._clean_box_line(raw)
            if text and text != title and not cls._is_border_only(text):
                text = cls._strip_ascii_branch(text)
                if text:
                    items.append(text)
        return title, items

    @staticmethod
    def _clean_box_line(raw: str) -> str:
        """去除方框内容行两侧的 │ 边框与空白。"""
        return raw.replace("\x00", "").strip(" │").strip()

    @staticmethod
    def _is_border_only(text: str) -> bool:
        """判断一行是否仅由方框/连接线字符组成。"""
        if not text:
            return True
        return all(ch in "┌┐└┘─│┬▼" for ch in text)

    def _convert_content_box(self, features: DiagramFeatures) -> Optional[str]:
        """
        将单个「标题 + 内容」方框转换为 flowchart with subgraph。

        以「：」结尾的基缩进行作为分节标题，生成嵌套 subgraph；
        其余顶层内容单元生成节点，缩进子项以 `<br/>` 合并。
        所有节点/分节按顺序用 `~~~` 串联。
        """
        merged = AsciiAnalyzer._merge_stacked_boxes(list(features.boxes))
        top_level = AsciiAnalyzer._top_level_boxes(merged)
        if len(top_level) != 1:
            return None
        box = top_level[0]
        sections = AsciiAnalyzer._split_sections(box, features.grid)
        if len(sections) < 2:
            return None

        title = self._first_text(sections[0])
        if not title:
            return None

        content_lines = [line for section in sections[1:] for line in section]
        chunks = self._build_content_chunks(content_lines)
        if not chunks:
            return None

        lines = ["flowchart LR"]
        lines.append(f'    subgraph R["{escape_mermaid_label(title)}"]')
        lines.append("        direction TB")
        node_names: List[str] = []
        node_index = 0
        section_index = 0
        for chunk in chunks:
            if chunk["kind"] == "section":
                section_index += 1
                sid = f"S{section_index}"
                node_names.append(sid)
                lines.append(f'        subgraph {sid}["{escape_mermaid_label(chunk["title"])}"]')
                lines.append("            direction TB")
                for block in self._split_fenced_blocks(chunk["items"]):
                    if block["kind"] == "fence":
                        sub = self._render_fenced_subgraph(block, sid)
                        if sub:
                            lines.extend(sub)
                            continue
                        for raw in block["lines"]:
                            node_index += 1
                            nid = f"N{node_index}"
                            lines.append(
                                f'            {nid}["{escape_mermaid_label(raw.strip())}"]'
                            )
                    else:
                        groups = self._group_section_items(block["lines"])
                        if groups:
                            node_index += 1
                            root_nid = f"N{node_index}"
                            lines.append(
                                f'            {root_nid}["{escape_mermaid_label("Markdown内容")}"]'
                            )
                            for label, parts in groups:
                                node_index += 1
                                nid = f"N{node_index}"
                                joined = "<br/>".join(escape_mermaid_label(part) for part in parts)
                                lines.append(
                                    f'            {nid}["{escape_mermaid_label(label)}: '
                                    f'{joined}"]'
                                )
                                lines.append(f"            {root_nid} --> {nid}")
                        else:
                            for item in block["lines"]:
                                node_index += 1
                                nid = f"N{node_index}"
                                lines.append(
                                    f'            {nid}["{escape_mermaid_label(item.strip())}"]'
                                )
                lines.append("        end")
            else:
                node_index += 1
                nid = f"N{node_index}"
                node_names.append(nid)
                unit_text = "<br/>".join(
                    escape_mermaid_label(text) for text in chunk["lines"] if text.strip()
                )
                if unit_text:
                    lines.append(f'        {nid}["{unit_text}"]')
        if node_names:
            lines.append("        " + " ~~~ ".join(node_names))
        lines.append("    end")
        return "\n".join(lines)

    @staticmethod
    def _build_content_chunks(lines: List[str]) -> List[dict]:
        """
        将内容行分组为「分节」或「节点」块。

        规则：
            - 以 `：`/`:` 结尾的基缩进行 → 分节标题，其后所有行归入该分节
            - 含冒号但不以冒号结尾的基缩进行 → 独立节点
            - 其余基缩进行 → 若在分节内则作为条目，否则开新节点块
            - Markdown 围栏行（```）跳过
        """
        chunks: List[dict] = []
        base_indent: Optional[int] = None
        current_section: Optional[dict] = None
        last_node_indent: Optional[int] = None
        # 内容中存在冒号分节时，Markdown 标题（#/##）视为示例内容而非分节
        has_colon_sections = False

        for line in lines:
            if not line.strip():
                continue
            indent = len(line) - len(line.lstrip(" "))
            text = FlowchartConverter._strip_ascii_branch(line)
            if base_indent is None:
                base_indent = indent
            if indent <= base_indent and text.rstrip().endswith(("：", ":")):
                has_colon_sections = True

            if indent <= base_indent and (
                text.rstrip().endswith(("：", ":"))
                or (not has_colon_sections and re.match(r"^#{1,6}\s+\S", text))
            ):
                title = text.rstrip("：:").strip() if not text.startswith("#") else text
                current_section = {
                    "kind": "section",
                    "title": title,
                    "items": [],
                }
                chunks.append(current_section)
                last_node_indent = None
            elif indent <= base_indent and ("：" in text or ":" in text):
                current_section = None
                chunks.append({"kind": "node", "lines": [text]})
                last_node_indent = indent
            elif current_section is not None:
                current_section["items"].append(text)
            elif last_node_indent is not None and indent > last_node_indent:
                chunks[-1]["lines"].append(text)
            else:
                chunks.append({"kind": "node", "lines": [text]})
                last_node_indent = indent
        return chunks

    @classmethod
    def _group_section_items(cls, items: List[str]) -> List[Tuple[str, List[str]]]:
        """
        对类似 Markdown 示例的分节内容做语义分组。

        返回 (标签, 片段列表) 列表；非 Markdown 示例内容返回空列表。
        """
        if not items:
            return []
        is_markdown = any(
            line.strip().startswith("#")
            or re.match(r"^```", line.strip())
            or line.strip().startswith("|")
            for line in items
        )
        if not is_markdown:
            return []

        headings: List[str] = []
        paragraphs: List[str] = []
        ascii_boxes: List[str] = []
        table_rows: List[str] = []
        in_fence = False
        for raw in items:
            line = raw.strip()
            if not line:
                continue
            if line.startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                ascii_boxes.append(line)
                continue
            if line.startswith("#"):
                headings.append(line)
            elif line.startswith("|"):
                table_rows.append(line)
            else:
                paragraphs.append(line)

        groups: List[Tuple[str, List[str]]] = []
        if headings:
            groups.append(("标题", [", ".join(headings)]))
        if paragraphs:
            groups.append(("段落", paragraphs))
        if ascii_boxes:
            labels = cls._extract_ascii_box_labels(ascii_boxes)
            summary = " → ".join(labels) if labels else ascii_boxes
            groups.append(("ASCII图", [summary] if isinstance(summary, str) else summary))
        if table_rows:
            groups.append(("表格", [cls._extract_table_summary(table_rows)]))
        return groups

    @staticmethod
    def _extract_ascii_box_labels(lines: List[str]) -> List[str]:
        """从方框文本中提取节点标签（用于 ASCII 图摘要）。"""
        labels = []
        for line in lines:
            stripped = line.strip(" │┃|")
            if stripped and not stripped.startswith(
                ("┌", "└", "├", "─", "┐", "┘", "┤", "┬", "┴", "▼", "▲", "v", "V", "|")
            ):
                labels.append(stripped)
        return labels

    @staticmethod
    def _extract_table_summary(rows: List[str]) -> str:
        """提取表格首行数据摘要。"""
        data_rows = []
        for row in rows:
            cells = [c.strip() for c in row.strip().strip("|").split("|")]
            if cells and any(cells) and not all(re.match(r"^[-:]+$", c) for c in cells):
                data_rows.append(cells)
        # 跳过表头行（第一行非分隔行），取首个数据行
        if len(data_rows) >= 2:
            cells = data_rows[1]
        elif data_rows:
            cells = data_rows[0]
        else:
            return rows[0].strip() if rows else ""
        filled = [c for c in cells if c]
        return " ".join(filled[:2])

    @staticmethod
    def _split_fenced_blocks(items: List[str]) -> List[dict]:
        """
        将分节条目按 Markdown 围栏拆分为块。

        返回 [{"kind": "fence", "lang": ..., "lines": [...]},
              {"kind": "text", "lines": [...]}, ...]
        """
        blocks: List[dict] = []
        current_lang: Optional[str] = None
        fence_lines: List[str] = []
        plain: List[str] = []

        def flush_plain() -> None:
            if plain:
                blocks.append({"kind": "text", "lines": list(plain)})
                plain.clear()

        for raw in items:
            line = raw.strip()
            match = re.match(r"^```(\w*)$", line)
            if match:
                if current_lang is None:
                    current_lang = match.group(1).lower()
                    fence_lines = []
                else:
                    blocks.append(
                        {
                            "kind": "fence",
                            "lang": current_lang,
                            "lines": fence_lines,
                        }
                    )
                    current_lang = None
            elif current_lang is not None:
                fence_lines.append(raw)
            else:
                plain.append(raw)
        if current_lang is not None:
            blocks.append({"kind": "fence", "lang": current_lang, "lines": fence_lines})
        flush_plain()
        return blocks

    def _render_fenced_subgraph(
        self,
        block: dict,
        prefix: str,
    ) -> Optional[List[str]]:
        """渲染围栏内容为嵌套子图（ASCII 迷你流程 / Mermaid 时序）。"""
        lang = block.get("lang", "")
        if lang == "ascii":
            inner = AsciiAnalyzer.analyze("\n".join(block["lines"]))
            return self._mini_flow_subgraph(inner, f"{prefix}_ASCII", "ASCII Diagram")
        if lang == "mermaid":
            return self._sequence_subgraph(block["lines"], f"{prefix}_SEQ", "Sequence Diagram")
        return None

    def _mini_flow_subgraph(
        self,
        features: DiagramFeatures,
        prefix: str,
        title: str,
    ) -> Optional[List[str]]:
        """将内嵌 ASCII 迷你流程渲染为子图。"""
        boxes = list(features.boxes)
        arrows = list(features.arrows)
        if not boxes:
            return None
        direction = self._detect_direction(arrows)
        # mermaid v10 的 direction 语句仅接受 TB/BT/LR/RL，不支持 TD
        if direction == "TD":
            direction = "TB"
        ids = {id(box): f"{prefix}_{node_id(index)}" for index, box in enumerate(boxes)}
        lines = [
            f'            subgraph {prefix}["{escape_mermaid_label(title)}"]',
            f"                direction {direction}",
        ]
        for box in boxes:
            label = "<br/>".join(
                escape_mermaid_label(part) for part in box.text.splitlines() if part.strip()
            )
            lines.append(f'                {ids[id(box)]}["{label}"]')
        for src, dst, _label in self._build_edges(boxes, arrows, features, prefix=f"{prefix}_"):
            lines.append(f"                {src} --> {dst}")
        lines.append("            end")
        return lines

    @staticmethod
    def _sequence_subgraph(
        lines: List[str],
        prefix: str,
        title: str,
    ) -> Optional[List[str]]:
        """将内嵌 Mermaid sequenceDiagram 源码渲染为子图。"""
        participants: List[str] = []
        messages: List[Tuple[str, str, str]] = []
        seen: Set[str] = set()

        for raw in lines:
            line = raw.strip()
            match = re.match(r"participant\s+([A-Za-z_]\w*)", line)
            if match:
                pid = match.group(1)
                if pid not in seen:
                    seen.add(pid)
                    participants.append(pid)
                continue
            match = re.match(
                r"([A-Za-z_]\w*)\s*(->>|-->>|->|-->|-x|--x)\s*" r"([A-Za-z_]\w*)(?:\s*:\s*(.*))?",
                line,
            )
            if match:
                src, _token, dst, label = match.groups()
                for pid in (src, dst):
                    if pid not in seen:
                        seen.add(pid)
                        participants.append(pid)
                messages.append((src, dst, (label or "").strip()))

        if not messages:
            return None
        out = [
            f'            subgraph {prefix}["{escape_mermaid_label(title)}"]',
            "                direction TB",
        ]
        for pid in participants:
            out.append(f'                {prefix}_{pid}["{escape_mermaid_label(pid)}"]')
        for src, dst, label in messages:
            edge_label = f'|"{escape_mermaid_label(label)}"|' if label else ""
            out.append(f"                {prefix}_{src} -->{edge_label} {prefix}_{dst}")
        out.append("            end")
        return out

    @staticmethod
    def _first_text(lines: List[str]) -> str:
        """取第一段非空文本。"""
        for line in lines:
            text = line.strip()
            if text:
                return text
        return ""

    # ============================================================
    # 树形结构 → flowchart
    # ============================================================

    def _convert_tree(self, features: DiagramFeatures) -> Optional[str]:
        """
        将树形结构（目录树/层级树）转换为 flowchart。

        目录树使用 📁/📄/🔧 图标与 classDef 样式；
        普通层级树仅生成节点与父子边。
        """
        nodes = sorted(features.tree_nodes, key=lambda n: (n.row, n.depth))
        if len(nodes) < 2:
            return None
        min_depth = min(n.depth for n in nodes)
        roots = [n for n in nodes if n.depth == min_depth]
        if len(roots) != 1:
            return None

        # 构建父子关系（行序 + 深度栈）
        used_ids: Set[str] = set()
        stack: List[Tuple[int, str]] = []
        entries: List[Tuple[TreeNode, str]] = []
        parent_of: Dict[str, str] = {}
        for node in nodes:
            while stack and stack[-1][0] >= node.depth:
                stack.pop()
            node_id = self._tree_node_id(node.text, used_ids)
            used_ids.add(node_id)
            if stack:
                parent_of[node_id] = stack[-1][1]
            stack.append((node.depth, node_id))
            entries.append((node, node_id))

        children_of: Dict[str, List[str]] = defaultdict(list)
        for child_id, parent_id in parent_of.items():
            children_of[parent_id].append(child_id)
        is_folder = {node_id: bool(children_of.get(node_id)) for _, node_id in entries}
        # 以 `/` 结尾的目录即使无子节点也视为文件夹
        for node, node_id in entries:
            name, _, _ = self._tree_name_comment(node.text)
            if name.rstrip().endswith("/"):
                is_folder[node_id] = True
        root_id = entries[0][1]
        file_like = self._is_file_tree_like(nodes)

        lines = ["flowchart LR"]
        node_classes: Dict[str, str] = {}
        for node, node_id in entries:
            label_parts = self._tree_node_label_parts(
                node.text,
                is_folder=is_folder[node_id],
                is_root=(node_id == root_id),
                file_like=file_like,
            )
            label = "<br/>".join(escape_mermaid_label(part) for part in label_parts)
            lines.append(f'    {node_id}["{label}"]')
            if node_id == root_id:
                node_classes[node_id] = "root"
            elif is_folder[node_id]:
                # 一级目录 → folder；深层目录 → subfolder
                node_classes[node_id] = "subfolder" if node.depth >= 2 else "folder"
            else:
                name, size, _ = self._tree_name_comment(node.text)
                if re.match(r"^test_", name):
                    node_classes[node_id] = "test"
                else:
                    # 仅较深层级（≥3）且带规模信息的核心文件做强调
                    node_classes[node_id] = "emphasis" if size and node.depth >= 3 else "file"

        for child_id, parent_id in parent_of.items():
            lines.append(f"    {parent_id} --> {child_id}")

        if file_like:
            lines.extend(
                [
                    "    classDef root fill:#4CAF50,color:#fff,stroke:#2E7D32,stroke-width:3px",
                    "    classDef folder fill:#2196F3,color:#fff,stroke:#0D47A1,stroke-width:2px",
                    "    classDef subfolder "
                    "fill:#1976D2,color:#fff,stroke:#0D47A1,stroke-width:2px",
                    "    classDef file fill:#FFC107,color:#333,stroke:#F57F17,stroke-width:2px",
                    "    classDef emphasis fill:#FF5722,color:#fff,stroke:#BF360C,stroke-width:2px",
                    "    classDef test fill:#9C27B0,color:#fff,stroke:#4A148C,stroke-width:2px",
                ]
            )
            for class_name in ("root", "folder", "subfolder", "file", "emphasis", "test"):
                ids = [nid for nid, cls in node_classes.items() if cls == class_name]
                if ids:
                    lines.append(f"    class {','.join(ids)} {class_name}")

        return "\n".join(lines)

    @staticmethod
    def _tree_name_comment(text: str) -> Tuple[str, str, str]:
        """
        解析树节点文本为 (名称, 规模, 注释)。

        支持 `名称 # 注释 (~200行)` 形式。
        """
        name = text
        comment = ""
        match = re.search(r"^(.*?)\s*#\s*(.*)$", text)
        if match:
            name = match.group(1).strip()
            comment = match.group(2).strip()
        size = ""
        size_match = re.search(r"\(?~?\d+\s*行\)?", comment)
        if size_match:
            size = size_match.group(0).strip("()")
            comment = (comment[: size_match.start()] + comment[size_match.end() :]).strip(" ()")
        return name, size, comment

    @classmethod
    def _tree_node_label_parts(
        cls,
        text: str,
        is_folder: bool,
        is_root: bool,
        file_like: bool,
    ) -> List[str]:
        """生成带图标的节点标签片段（调用方负责转义与 <br/> 拼接）。"""
        name, size, comment = cls._tree_name_comment(text)
        name = cls._strip_markdown_emphasis(name)
        comment = cls._strip_markdown_emphasis(comment)
        if not file_like:
            parts = [name]
            if size:
                parts.append(size)
            if comment:
                parts.append(comment)
            return parts
        if is_root:
            icon = "📁"
        elif is_folder:
            icon = "📁"
        elif cls._looks_like_command(name):
            icon = "🔧"
        else:
            icon = "📄"
        parts = [f"{icon} {name}"]
        if size:
            parts.append(size)
        if comment:
            parts.append(comment)
        return parts

    @staticmethod
    def _strip_markdown_emphasis(text: str) -> str:
        """去除 Markdown 加粗/斜体标记（**、*、_）。"""
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        text = re.sub(r"(?<!\w)[*_]([^*_]+)[*_](?!\w)", r"\1", text)
        return text.strip()

    @staticmethod
    def _looks_like_command(name: str) -> bool:
        """无扩展名且不像路径的叶子节点视为可执行命令。"""
        if "." in name or "/" in name or "\\" in name:
            return False
        return bool(re.match(r"^[a-z0-9_-]+$", name))

    @staticmethod
    def _tree_node_id(text: str, used: Set[str]) -> str:
        """生成稳定且唯一的节点 ID。"""
        name = text.split("#")[0].strip()
        base = re.sub(r"[^A-Za-z0-9_]", "", name).upper() or "NODE"
        candidate = base
        counter = 2
        while candidate in used:
            candidate = f"{base}{counter}"
            counter += 1
        return candidate

    @staticmethod
    def _is_file_tree_like(nodes: List[TreeNode]) -> bool:
        """树节点是否包含文件/目录特征（# 注释、扩展名、路径分隔符）。"""
        pattern = re.compile(r"#|\.\w{1,5}$|/")
        return any(pattern.search(node.text) for node in nodes)

    def _convert_text_flow(self, features: DiagramFeatures) -> Optional[str]:
        """
        将「文本流程」ASCII 图转换为 flowchart。

        文本流程由多个主节点与 `├──`/`└──` 分支组成，分支汇合到下一主节点
        （如 `A → B；B → C/D/E/F；C/D/E/F → G`）。
        """
        nodes = sorted(features.tree_nodes, key=lambda n: (n.row, n.depth))
        if len(nodes) < 3:
            return None
        min_depth = min(n.depth for n in nodes)
        if min_depth != 0:
            return None
        vertical = any(a.direction in ("down", "up") for a in features.arrows)
        if not vertical:
            return None

        # 分组：深度 0 = 主节点，深度 1 = 该主节点的分支
        stages: List[Dict[str, object]] = []
        current: Optional[Dict[str, object]] = None
        for node in nodes:
            if node.depth == min_depth:
                main, inline_branches = self._split_flow_options(node.text)
                current = {"main": main, "branches": list(inline_branches)}
                stages.append(current)
            elif node.depth == min_depth + 1 and current is not None:
                current["branches"].append(node.text)
        if len(stages) < 2:
            return None

        # 显示顺序：主节点后紧跟其分支
        display: List[str] = []
        for stage in stages:
            display.append(stage["main"])
            display.extend(stage["branches"])
        ids: Dict[str, str] = {}
        for index, text in enumerate(display):
            ids[text] = node_id(index)

        lines = ["flowchart TD"]
        for text in display:
            lines.append(f'    {ids[text]}["{escape_mermaid_label(text)}"]')

        # 边：主 → 分支；分支 → 下一主节点；无分支时主 → 下一主节点
        for index, stage in enumerate(stages):
            main_id = ids[stage["main"]]
            branches = stage["branches"]
            if branches:
                for branch in branches:
                    lines.append(f"    {main_id} --> {ids[branch]}")
                if index + 1 < len(stages):
                    next_main = ids[stages[index + 1]["main"]]
                    for branch in branches:
                        lines.append(f"    {ids[branch]} --> {next_main}")
            elif index + 1 < len(stages):
                lines.append(f"    {main_id} --> {ids[stages[index + 1]['main']]}")
        return "\n".join(lines)

    @staticmethod
    def _split_flow_options(text: str) -> Tuple[str, List[str]]:
        """
        将 `标题：选项A / 选项B` 拆分为 (标题, 选项列表)。

        仅当冒号后存在 ≥2 个 `/` 分隔项时拆分。
        """
        match = re.search(r"[:：]\s*(.*)$", text)
        if not match or match.start() == 0:
            return text, []
        header = text[: match.start()].strip()
        rest = match.group(1).strip()
        parts = [part.strip() for part in re.split(r"/", rest) if part.strip()]
        if len(parts) >= 2:
            return header, parts
        return text, []

    # ============================================================
    # 分层/分阶段流程图（结构化盒子 → subgraph + 配色）
    # ============================================================

    _INPUT_CLASS = ("input", "#E3F2FD", "#1565C0")
    _OUTPUT_CLASS = ("output", "#E0F7FA", "#00838F")
    _STAGE_CLASSES = [
        ("cli", "#FFF3E0", "#E65100"),
        ("parser", "#F3E5F5", "#6A1B9A"),
        ("pipeline", "#E8F5E9", "#2E7D32"),
        ("renderer", "#FFF8E1", "#F57F17"),
        ("post", "#FCE4EC", "#C62828"),
    ]

    @staticmethod
    def _is_structured_flow(boxes: List[Box]) -> bool:
        """盒子大多为「标题 + 条目」结构时使用分层渲染。"""
        if len(boxes) < 2:
            return False
        structured = sum(
            1 for box in boxes if len([line for line in box.lines if line.strip()]) >= 2
        )
        return structured >= max(2, len(boxes) * 0.5)

    @staticmethod
    def _strip_ascii_branch(text: str) -> str:
        """去除行首的 ASCII 树形分支标记（├── / └── / │ 等）。"""
        # 盒子底边（└───┘）以角字符结尾，不作为分支剥离
        if not re.search(r"[┐┘┤┐]$", text):
            text = re.sub(r"^[\s│|]*[├└][─\-=]+\s*", "", text)
        text = re.sub(r"^[|\\`+][─\-=]+\s*", "", text)
        return text.strip()

    def _convert_structured_flow(
        self,
        features: DiagramFeatures,
        boxes: List[Box],
        arrows: List[Arrow],
    ) -> str:
        """
        将「标题 + 条目」盒子流转换为分层 flowchart。

        每个盒子生成一个 subgraph（标题 + 条目节点），
        箭头连接盒子/首尾文本节点，并按流程位置配色。
        """
        direction = self._detect_direction(arrows)
        lines = [f"flowchart {direction}"]
        box_id = {id(box): f"B{index + 1}" for index, box in enumerate(boxes)}
        positions: Dict[str, Tuple[int, int]] = {box_id[id(box)]: (box.y0, box.x0) for box in boxes}

        # 1. 方框 → subgraph（标题 + 条目）或扁平节点
        for box in boxes:
            bid = box_id[id(box)]
            interior = [self._strip_ascii_branch(line) for line in box.lines if line.strip()]
            if len(interior) >= 2:
                lines.append(f'    subgraph {bid}["{escape_mermaid_label(interior[0])}"]')
                lines.append("        direction TB")
                for j, item in enumerate(interior[1:], start=1):
                    lines.append(f'        {bid}_{j}["{escape_mermaid_label(item)}"]')
                lines.append("    end")
            else:
                label = "<br/>".join(escape_mermaid_label(line) for line in interior)
                lines.append(f'    {bid}["{label}"]')

        # 2. 文本锚点（箭头端无方框时取附近文本作为首尾节点）
        text_ids: Dict[str, str] = {}

        def node_for_side(arrow: Arrow, side: str) -> Optional[str]:
            box = self._nearest_box(boxes, arrow.row, arrow.col, side)
            if box is not None:
                return box_id[id(box)]
            anchor = self._text_anchor(features, arrow, side)
            if anchor is None:
                return None
            text, text_row = anchor
            if text not in text_ids:
                tid = f"T{len(text_ids) + 1}"
                text_ids[text] = tid
                positions[tid] = (text_row, arrow.col)
                lines.append(f'    {tid}["{escape_mermaid_label(text)}"]')
            return text_ids[text]

        # 3. 边
        edges: List[Tuple[str, str]] = []
        seen_edges: Set[Tuple[str, str]] = set()
        for arrow in arrows:
            src = node_for_side(arrow, self._tail_side(arrow))
            dst = node_for_side(arrow, self._head_side(arrow))
            if src and dst and src != dst and (src, dst) not in seen_edges:
                seen_edges.add((src, dst))
                edges.append((src, dst))
        for src, dst in edges:
            lines.append(f"    {src} --> {dst}")

        # 4. 按流程位置分配配色（首个 input，末个 output，中间循环调色板）
        order = sorted(positions, key=lambda nid: positions[nid])
        class_of: Dict[str, str] = {}
        palette = self._STAGE_CLASSES
        for index, nid in enumerate(order):
            if index == 0:
                class_of[nid] = self._INPUT_CLASS[0]
            elif index == len(order) - 1:
                class_of[nid] = self._OUTPUT_CLASS[0]
            else:
                class_of[nid] = palette[(index - 1) % len(palette)][0]
            if nid.startswith("B"):
                idx = int(nid[1:]) - 1
                interior = [line.strip() for line in boxes[idx].lines if line.strip()]
                if len(interior) >= 2:
                    for j in range(1, len(interior)):
                        class_of[f"{nid}_{j}"] = class_of[nid]

        used_classes = {cls for cls in class_of.values() if cls}
        for cls_name, fill, stroke in [self._INPUT_CLASS] + palette + [self._OUTPUT_CLASS]:
            if cls_name in used_classes:
                lines.append(
                    f"    classDef {cls_name} fill:{fill},stroke:{stroke},stroke-width:2px"
                )
        for cls_name in used_classes:
            ids = [nid for nid, cls in class_of.items() if cls == cls_name]
            lines.append(f"    class {','.join(ids)} {cls_name}")
        return "\n".join(lines)

    @staticmethod
    def _text_anchor(
        features: DiagramFeatures,
        arrow: Arrow,
        side: str,
    ) -> Optional[Tuple[str, int]]:
        """
        在箭头缺失方框的一侧查找附近的文本锚点。

        返回 (文本, 行号)；找不到返回 None。
        """
        grid = features.grid
        row = arrow.row
        if side in ("above", "left"):
            rows = range(row - 1, max(-1, row - 5), -1)
        else:
            rows = range(row + 1, min(len(grid), row + 5))
        for r in rows:
            if r < 0 or r >= len(grid):
                break
            text = AsciiAnalyzer._strip_filler(grid[r]).strip()
            if not text:
                continue
            if any(ch in text for ch in "│┌┐└┘├┤┬┴┼─▼▲▽△^vV|"):
                continue
            return text, r
        return None

    # ============================================================
    # 嵌套盒分层布局（产品全景图）→ flowchart TB
    # ============================================================

    def _convert_landscape(self, features: DiagramFeatures) -> Optional[str]:
        """
        将嵌套盒分层布局转换为 flowchart TB。

        外层标题盒 → 根 subgraph；每个类别盒 → 子 subgraph
        （direction LR + 产品节点）；类别间若有垂直连接符则加边。
        """
        raw = list(features.boxes)
        if len(raw) < 6:
            return None
        title_box = min(raw, key=lambda box: (box.y0, box.x0))
        title = self._first_text(title_box.lines) or title_box.text.strip()
        if not title:
            return None
        container_width = title_box.x1 - title_box.x0

        def contains(outer: Box, inner: Box) -> bool:
            return (
                outer.x0 <= inner.x0
                and outer.x1 >= inner.x1
                and outer.y0 <= inner.y0
                and outer.y1 >= inner.y1
            )

        def direct_children(outer: Box) -> List[Box]:
            """outer 的直接子盒（不被其他盒夹在中间）。"""
            return [
                box
                for box in raw
                if box is not outer
                and contains(outer, box)
                and not any(
                    other is not outer
                    and other is not box
                    and contains(outer, other)
                    and contains(other, box)
                    for other in raw
                )
            ]

        # 类别盒：宽盒（≥60% 容器宽）且直接包含 ≥2 个子盒
        categories: List[Tuple[Box, List[Box]]] = []
        for box in raw:
            if box is title_box:
                continue
            if box.x1 - box.x0 < container_width * 0.6:
                continue
            children = direct_children(box)
            if len(children) >= 2:
                categories.append((box, children))
        if len(categories) < 2:
            return None
        categories.sort(key=lambda item: (item[0].y0, item[0].x0))

        lines = ["flowchart TB"]
        lines.append(f'    subgraph LANDSCAPE["{escape_mermaid_label(title)}"]')
        for index, (category, products) in enumerate(categories, start=1):
            gid = f"G{index}"
            cat_title = self._first_text_line(category)
            if not cat_title:
                return None
            products.sort(key=lambda box: (box.y0, box.x0))
            lines.append(f'        subgraph {gid}["{escape_mermaid_label(cat_title)}"]')
            lines.append("            direction LR")
            for pindex, product in enumerate(products, start=1):
                pid = f"{gid}_P{pindex}"
                name = " ".join(product.text.splitlines())
                lines.append(f'            {pid}["{escape_mermaid_label(name)}"]')
            lines.append("        end")

        for index in range(len(categories) - 1):
            if self._has_vertical_link_between(
                features, categories[index][0], categories[index + 1][0]
            ):
                lines.append(f"        G{index + 1} --> G{index + 2}")
        lines.append("    end")
        return "\n".join(lines)

    @staticmethod
    def _first_text_line(box: Box) -> str:
        """取方框中第一行非空、非绘图字符的文本。"""
        for line in box.lines:
            text = line.strip()
            if not text:
                continue
            if any(ch in text for ch in "┌┐└┘├┤┬┴┼─▼▲▽△│|"):
                continue
            return text
        return ""

    @staticmethod
    def _has_vertical_link_between(
        features: DiagramFeatures,
        upper: Box,
        lower: Box,
    ) -> bool:
        """
        两个类别盒之间是否存在垂直连接符（│/▼）。

        类别盒通常共享边框行，箭头可能位于下盒顶部附近，
        因此从 `upper.y1` 扫描到 `lower.y0 + 3`。
        """
        grid = features.grid
        c0 = max(upper.x0, lower.x0)
        c1 = min(upper.x1, lower.x1)
        # 排除盒边界列（侧边框），只检查中心区域
        c0, c1 = c0 + 2, c1 - 1
        # 仅扫描边界区（上盒底边到下盒顶边附近），避免误取产品盒边框
        row_end = min(len(grid), lower.y0 + 2)
        for row in range(max(0, upper.y1), row_end):
            for col in range(c0, c1 + 1):
                if col < 0 or col >= len(grid[row]):
                    continue
                if row < len(grid) and col < len(grid[row]):
                    ch = grid[row][col]
                    if ch in "│|┃▼↓":
                        return True
        return False

    # ============================================================
    # 内嵌盒图（外层盒 + 内部盒子 + 箭头）
    # ============================================================

    @staticmethod
    def _has_inner_box_graph(features: DiagramFeatures) -> bool:
        """外层盒内直接包含多个盒子，且存在内部箭头。"""
        raw = list(features.boxes)
        if len(raw) < 5:
            return False

        def contains(o: Box, b: Box) -> bool:
            return o is not b and o.x0 <= b.x0 and o.x1 >= b.x1 and o.y0 <= b.y0 and o.y1 >= b.y1

        outer = FlowchartConverter._find_container(raw, contains)
        if outer is None:
            return False
        inner = [box for box in raw if contains(outer, box)]
        if len(inner) < 4:
            return False
        inner_arrows = FlowchartConverter._inner_arrows(features, outer)
        return len(inner_arrows) >= 2

    @staticmethod
    def _inner_arrows(
        features: DiagramFeatures,
        outer: Box,
    ) -> List[Arrow]:
        """提取外层盒内部的箭头（不过滤盒内）。"""
        return [
            arrow
            for arrow in AsciiAnalyzer.extract_arrows(features.grid)
            if outer.x0 < arrow.col < outer.x1 and outer.y0 < arrow.row < outer.y1
        ]

    def _convert_inner_box_graph(
        self,
        features: DiagramFeatures,
    ) -> Optional[str]:
        """
        将外层盒 + 内部盒子 + 箭头转换为 flowchart。

        外层盒 → 根 subgraph；内部盒子 → 节点；箭头 → 边；
        盒外的文本行（如特性描述）→ 节点。
        """
        raw = list(features.boxes)

        def contains(o: Box, b: Box) -> bool:
            return o is not b and o.x0 <= b.x0 and o.x1 >= b.x1 and o.y0 <= b.y0 and o.y1 >= b.y1

        container = FlowchartConverter._find_container(raw, contains)
        if container is None:
            return None
        title_box = min(raw, key=lambda box: (box.y0, box.x0))
        title = self._first_text(title_box.lines) or title_box.text.strip()
        if not title:
            return None

        outer = container
        inner = [box for box in raw if contains(outer, box)]
        inner.sort(key=lambda box: (box.y0, box.x0))
        arrows = self._inner_arrows(features, outer)

        lines = ["flowchart TB"]
        lines.append(f'    subgraph R["{escape_mermaid_label(title)}"]')
        lines.append("        direction TB")

        ids = {id(box): node_id(index) for index, box in enumerate(inner)}
        for box in inner:
            label = "<br/>".join(
                escape_mermaid_label(part) for part in box.text.splitlines() if part.strip()
            )
            lines.append(f'        {ids[id(box)]}["{label}"]')

        seen_edges: Set[Tuple[str, str]] = set()
        for arrow in arrows:
            src = self._nearest_box(inner, arrow.row, arrow.col, self._tail_side(arrow))
            dst = self._nearest_box(inner, arrow.row, arrow.col, self._head_side(arrow))
            if src is None or dst is None or src is dst:
                continue
            edge = (ids[id(src)], ids[id(dst)])
            if edge in seen_edges:
                continue
            seen_edges.add(edge)
            lines.append(f"        {edge[0]} --> {edge[1]}")

        text_index = 0
        for text in self._outer_text_lines(features, outer, inner):
            text_index += 1
            lines.append(f'        T{text_index}["{escape_mermaid_label(text)}"]')
        lines.append("    end")
        return "\n".join(lines)

    @staticmethod
    def _outer_text_lines(
        features: DiagramFeatures,
        outer: Box,
        inner: List[Box],
    ) -> List[str]:
        """外层盒内、内部盒子之外的非空文本行。"""
        grid = features.grid
        inner_rows = set()
        for box in inner:
            inner_rows.update(range(box.y0, box.y1 + 1))
        texts: List[str] = []
        for row in range(outer.y0 + 1, outer.y1):
            if row in inner_rows:
                continue
            text = AsciiAnalyzer._strip_filler(grid[row]).strip("│┃| ").strip()
            if text:
                # 跳过纯箭头/连接行（如 `▼ ▼ ▼`）
                remaining = re.sub(r"[▼▲↓↑▶◀→←]", "", text)
                if not remaining.strip():
                    continue
                texts.append(text)
        return texts

    @staticmethod
    def _find_container(
        raw: List[Box],
        contains,
    ) -> Optional[Box]:
        """返回包含最多子盒的容器盒。"""
        best: Optional[Box] = None
        best_count = 0
        for box in raw:
            count = sum(1 for other in raw if contains(box, other))
            if count > best_count:
                best, best_count = box, count
        return best if best_count >= 1 else None

    @staticmethod
    def _has_nested_boxes(boxes: List[Box]) -> bool:
        """是否存在一个方框完全包含另一个方框。"""
        for outer in boxes:
            for inner in boxes:
                if inner is outer:
                    continue
                if (
                    outer.x0 <= inner.x0
                    and outer.x1 >= inner.x1
                    and outer.y0 <= inner.y0
                    and outer.y1 >= inner.y1
                    and (outer.x0 < inner.x0 or outer.y0 < inner.y0)
                ):
                    return True
        return False

    # ============================================================
    # 方向检测
    # ============================================================

    @staticmethod
    def _detect_direction(arrows: List[Arrow]) -> str:
        """根据箭头方向统计选择 TD 或 LR。"""
        vertical = sum(1 for a in arrows if a.direction in ("up", "down"))
        horizontal = sum(1 for a in arrows if a.direction in ("left", "right"))
        return "LR" if horizontal > vertical else "TD"

    # ============================================================
    # 边构建
    # ============================================================

    def _build_edges(
        self,
        boxes: List[Box],
        arrows: List[Arrow],
        features: DiagramFeatures,
        prefix: str = "",
    ) -> List[Tuple[str, str, str]]:
        """
        构建有向边列表 (src_id, dst_id, label)。

        边来源：
            1. 箭头（尾部方框 → 头部方框）
            2. 方框垂直邻接（无箭头）
            3. 分支连接符（父方框 → 子方框）
        """
        edges: List[Tuple[str, str, str]] = []
        seen: Set[Tuple[str, str]] = set()
        ids = {id(box): f"{prefix}{node_id(i)}" for i, box in enumerate(boxes)}

        def add_edge(src: Box, dst: Box, label: str = "") -> None:
            src_id = ids[id(src)]
            dst_id = ids[id(dst)]
            key = (src_id, dst_id)
            if key in seen:
                return
            seen.add(key)
            edges.append((src_id, dst_id, label))

        # 1. 箭头
        for arrow in arrows:
            src = self._nearest_box(boxes, arrow.row, arrow.col, self._tail_side(arrow))
            dst = self._nearest_box(boxes, arrow.row, arrow.col, self._head_side(arrow))
            if src is not None and dst is not None:
                add_edge(src, dst, arrow.label)

        # 2. 垂直邻接（仅连接最近的、无箭头覆盖的下方盒子）
        for i, upper in enumerate(boxes):
            candidates = [
                lower for lower in boxes[i + 1 :] if lower.y0 > upper.y1 and upper.overlaps_x(lower)
            ]
            if not candidates:
                continue
            nearest = min(candidates, key=lambda b: b.y0)
            gap = nearest.y0 - upper.y1
            if gap <= 0 or gap > self.MAX_GAP:
                continue
            if gap > 3 and not self._has_vertical_link(features, upper, nearest):
                continue
            add_edge(upper, nearest)

        # 3. 分支连接符
        for row in features.junction_rows:
            for col in self._junction_columns(features, row):
                parent = self._junction_parent(boxes, row, col)
                child = self._junction_child(boxes, row, col)
                if parent is not None and child is not None:
                    add_edge(parent, child)

        return edges

    @staticmethod
    def _junction_parent(
        boxes: List[Box],
        row: int,
        col: int,
    ) -> Optional[Box]:
        """
        查找分支连接行上方的父方框。

        连接行通常是父方框的底边（y1 == row），因此使用包含式匹配。
        """
        candidates = [
            b
            for b in boxes
            if b.y1 <= row and row - b.y1 <= FlowchartConverter.MAX_GAP and b.contains_col(col)
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda b: (row - b.y1, abs(b.center_x - col)))

    @staticmethod
    def _junction_child(
        boxes: List[Box],
        row: int,
        col: int,
    ) -> Optional[Box]:
        """查找分支连接行下方的子方框。"""
        candidates = [
            b
            for b in boxes
            if b.y0 > row and b.y0 - row <= FlowchartConverter.MAX_GAP and b.contains_col(col)
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda b: (b.y0 - row, abs(b.center_x - col)))

    @staticmethod
    def _tail_side(arrow: Arrow) -> str:
        """箭头尾部对应的方框方位。"""
        return {
            "down": "above",
            "up": "below",
            "right": "left",
            "left": "right",
        }[arrow.direction]

    @staticmethod
    def _head_side(arrow: Arrow) -> str:
        """箭头头部对应的方框方位。"""
        return {
            "down": "below",
            "up": "above",
            "right": "right",
            "left": "left",
        }[arrow.direction]

    def _nearest_box(
        self,
        boxes: List[Box],
        row: int,
        col: int,
        side: str,
    ) -> Optional[Box]:
        """按方位查找最近的方框。"""
        if side == "above":
            return self._nearest_box_above(boxes, row, col)
        if side == "below":
            return self._nearest_box_below(boxes, row, col)
        if side == "left":
            candidates = [b for b in boxes if b.x1 < col and b.contains_row(row)]
            if not candidates:
                return None
            return max(candidates, key=lambda b: b.x1)
        candidates = [b for b in boxes if b.x0 > col and b.contains_row(row)]
        if not candidates:
            return None
        return min(candidates, key=lambda b: b.x0)

    @staticmethod
    def _nearest_box_above(
        boxes: List[Box],
        row: int,
        col: int,
    ) -> Optional[Box]:
        """查找方框上方最近的方框。"""
        candidates = [
            b
            for b in boxes
            if b.y1 < row
            and row - b.y1 <= FlowchartConverter.MAX_GAP
            and abs(b.center_x - col) <= max(2, (b.x1 - b.x0 + 1) / 2)
        ]
        if not candidates:
            return None
        return min(
            candidates,
            key=lambda b: (row - b.y1, abs(b.center_x - col)),
        )

    @staticmethod
    def _nearest_box_below(
        boxes: List[Box],
        row: int,
        col: int,
    ) -> Optional[Box]:
        """查找方框下方最近的方框。"""
        candidates = [
            b
            for b in boxes
            if b.y0 > row
            and b.y0 - row <= FlowchartConverter.MAX_GAP
            and abs(b.center_x - col) <= max(2, (b.x1 - b.x0 + 1) / 2)
        ]
        if not candidates:
            return None
        return min(
            candidates,
            key=lambda b: (b.y0 - row, abs(b.center_x - col)),
        )

    @staticmethod
    def _has_vertical_link(
        features: DiagramFeatures,
        upper: Box,
        lower: Box,
    ) -> bool:
        """检查两个方框之间是否存在垂直连接符。"""
        grid = features.grid
        c0 = max(upper.x0, lower.x0)
        c1 = min(upper.x1, lower.x1)
        for row in range(upper.y1 + 1, lower.y0):
            for col in range(c0, c1 + 1):
                if row < len(grid) and col < len(grid[row]):
                    ch = grid[row][col]
                    if ch in "│┃║|↓▼▽vV" or ch in "├┤┴┬┼╠╣╦╩╬":
                        return True
        return False

    @staticmethod
    def _junction_columns(features: DiagramFeatures, row: int) -> List[int]:
        """提取某行中的分支连接符列。"""
        grid = features.grid
        if row >= len(grid):
            return []
        line = grid[row]
        columns: List[int] = []
        for col, ch in enumerate(line):
            if ch not in "├┤┬┴┼╠╣╦╩╬+":
                continue
            left_ok = col > 0 and is_horizontal_connector(line[col - 1])
            right_ok = col < len(line) - 1 and is_horizontal_connector(line[col + 1])
            if left_ok and right_ok:
                columns.append(col)
        return columns
