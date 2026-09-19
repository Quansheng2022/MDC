"""
AsciiToMermaid Pass - ASCII 图自动转 Mermaid Pass

将 ASCII 结构图（Diagram 节点或疑似图的代码块）自动转换为
最合适的 Mermaid 代码，供后续 DiagramPass 渲染。

支持三种模式：
    - auto: 规则引擎自动优选（默认，确定性）
    - interactive: 多方案交互式选择
    - preview: 生成多方案预览文件并采用最优方案

仅做 AST 转换，不渲染图片，不解析 Markdown。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...ast.nodes import (
    CodeBlock,
    Diagram,
    Emphasis,
    HardBreak,
    Node,
    Paragraph,
    SoftBreak,
    Strong,
    Text,
)
from ...diagnostics.collector import DiagnosticCollector
from ...services.ascii_mermaid import (
    AsciiToMermaidService,
    ConversionPlan,
    ConversionScheme,
)
from .base import PassResult, TransformPass


class AsciiToMermaidPass(TransformPass):
    """
    ASCII 图 → Mermaid 转换 Pass。

    配置:
        mode: 'auto' | 'interactive' | 'preview'，默认 'auto'
        confidence_threshold: 最低置信度，默认 0.30
        preview_dir: 多方案预览目录，默认 'output/ascii_preview'
        selector: 交互选择回调（接收 ConversionPlan 返回 ConversionScheme）
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config=config or {})
        self._load_config()

    def _load_config(self) -> None:
        """从配置字典加载运行参数（__init__ 与 configure 共用）。"""
        self.mode = str(self.config.get("mode", "auto"))
        self.confidence_threshold = float(self.config.get("confidence_threshold", 0.30))
        self.preview_dir = str(self.config.get("preview_dir", "output/ascii_preview"))
        self.selector = self.config.get("selector")
        self.service = AsciiToMermaidService()
        self._counter = 0
        self._preview_files: List[str] = []
        self._stats: Dict[str, int] = {}

    def configure(self, config: Dict[str, Any]) -> None:
        """应用配置并刷新运行参数。"""
        super().configure(config)
        self._load_config()

    # ============================================================
    # Pass 入口
    # ============================================================

    def run(
        self,
        document: Node,
        diag: DiagnosticCollector,
    ) -> PassResult:
        self._counter = 0
        self._stats = {
            "ascii_diagrams": 0,
            "converted": 0,
            "skipped": 0,
            "low_confidence": 0,
            "preview_written": 0,
            "schemes_generated": 0,
        }

        new_doc = self._transform_node(document, diag)
        files = self._preview_files
        self._preview_files = []

        if self._stats["converted"] > 0:
            diag.info(
                f"Converted {self._stats['converted']} ASCII diagrams to Mermaid",
                code="ASCI001",
            )

        return PassResult(
            document=new_doc,
            files=files,
            metadata={"stats": self._stats.copy()},
        )

    # ============================================================
    # 节点转换
    # ============================================================

    def _transform_node(
        self,
        node: Node,
        diag: DiagnosticCollector,
    ) -> Node:
        if node is None:
            return node

        if isinstance(node, Diagram) and node.diagram_type in ("ascii", "diagram"):
            self._stats["ascii_diagrams"] += 1
            converted = self._convert_ascii(node.content, node.span, diag)
            return converted or node

        if isinstance(node, CodeBlock):
            lang = (node.language or "").strip().lower()
            # 显式 ```text 是字面代码块，不得被 Mermaid 抢救或 ASCII 启发式覆盖。
            if lang == "text":
                return node
            # 抢救因围栏错配而被吞进代码块的 mermaid/gantt 图
            rescued = self._rescue_diagram_code(node.text, node.span)
            if rescued is not None:
                self._stats["converted"] += 1
                return rescued
            if lang in ("ascii", "diagram") or (
                lang in ("", "text", "plain", "txt", "markdown")
                and self.service.is_ascii_diagram(node.text)
            ):
                converted = self._convert_ascii(node.text, node.span, diag)
                if converted is not None:
                    return converted
            return node

        if isinstance(node, Paragraph):
            text = self._paragraph_text(node)
            # 仅当段落本身具备图表结构（方框/箭头/树）时才转换；
            # 普通「**字段**：+ 列表」等 markdown 内容保持不变。
            if text.count("\n") >= 1 and self.service.is_ascii_diagram(text):
                converted = self._convert_ascii(text, node.span, diag)
                if converted is not None:
                    return converted
            return node

        children = list(node.iter_children())
        if children:
            new_children: List[Node] = []
            for child in children:
                transformed = self._transform_node(child, diag)
                if transformed is not None:
                    new_children.append(transformed)
            return node.replace_children(new_children)
        return node

    def _rescue_diagram_code(
        self,
        text: str,
        span: Any,
    ) -> Optional[Diagram]:
        """
        从代码块内容中抢救被围栏错配吞掉的 mermaid/gantt 图。

        两种情况：
            - 整个文本即为 Mermaid 图（graph/flowchart/gantt 等开头）
            - 文本内嵌 ```mermaid / ```gantt 块
        """
        if not text or not text.strip():
            return None
        stripped = text.strip()
        if re.match(
            r"^(graph|flowchart|sequenceDiagram|classDiagram|stateDiagram|"
            r"mindmap|gantt|pie|journey|timeline|erDiagram|gitGraph)\b",
            stripped,
        ):
            return Diagram(diagram_type="mermaid", content=stripped, span=span)
        if re.match(r"^(title|dateFormat)\b", stripped):
            # ```gantt 围栏体以 title/dateFormat 开头，需补 gantt 类型关键字
            return Diagram(
                diagram_type="mermaid",
                content="gantt\n" + stripped,
                span=span,
            )

        in_block = False
        buf: List[str] = []
        block_lang = ""
        for line in text.splitlines():
            match = re.match(r"^```\s*([A-Za-z0-9_-]*)\s*$", line.strip())
            if match:
                if not in_block:
                    block_lang = match.group(1).lower()
                    if block_lang in ("mermaid", "gantt"):
                        in_block = True
                        buf = []
                else:
                    if block_lang in ("mermaid", "gantt") and "\n".join(buf).strip():
                        body = "\n".join(buf)
                        if block_lang == "gantt" and not re.match(
                            r"^\s*(gantt|graph|flowchart)\b", body
                        ):
                            body = "gantt\n" + body
                        return Diagram(
                            diagram_type="mermaid",
                            content=body,
                            span=span,
                        )
                    in_block = False
                    buf = []
            elif in_block:
                buf.append(line)

        if in_block and block_lang in ("mermaid", "gantt") and "\n".join(buf).strip():
            body = "\n".join(buf)
            if block_lang == "gantt" and not re.match(r"^\s*(gantt|graph|flowchart)\b", body):
                body = "gantt\n" + body
            return Diagram(diagram_type="mermaid", content=body, span=span)
        return None

    @staticmethod
    def _paragraph_text(node: Paragraph) -> str:
        """重建段落的多行纯文本（SoftBreak/HardBreak → 换行）。"""
        parts: List[str] = []
        for child in node.iter_children():
            if isinstance(child, Text):
                parts.append(child.content)
            elif isinstance(child, (SoftBreak, HardBreak)):
                parts.append("\n")
            elif isinstance(child, Strong):
                parts.append(f"**{child.to_plain_text()}**")
            elif isinstance(child, Emphasis):
                parts.append(f"*{child.to_plain_text()}*")
            else:
                parts.append(child.to_plain_text())
        return "".join(parts)

    # ============================================================
    # 转换核心
    # ============================================================

    def _convert_ascii(
        self,
        content: str,
        span: Any,
        diag: DiagnosticCollector,
    ) -> Optional[Diagram]:
        plan = self.service.analyze(content)
        if not plan.schemes:
            self._stats["skipped"] += 1
            diag.warning(
                "ASCII diagram structure not recognized, keeping original",
                code="ASCI002",
                location=span,
            )
            return None

        best = plan.best
        assert best is not None
        self._stats["schemes_generated"] += len(plan.schemes)

        if best.confidence < self.confidence_threshold:
            self._stats["low_confidence"] += 1
            diag.warning(
                f"ASCII diagram confidence too low ({best.confidence:.2f} < "
                f"{self.confidence_threshold:.2f}), keeping original",
                code="ASCI003",
                location=span,
            )
            return None

        if len(plan.schemes) > 1:
            diag.info(
                f"Generated {len(plan.schemes)} candidate schemes for ASCII diagram",
                code="ASCI005",
                location=span,
                data={
                    "schemes": [
                        {
                            "id": s.scheme_id,
                            "type": s.diagram_type,
                            "confidence": s.confidence,
                        }
                        for s in plan.schemes
                    ]
                },
            )

        chosen = self._select_scheme(plan, diag, span)
        if chosen is None:
            self._stats["skipped"] += 1
            return None

        if self.mode == "preview":
            self._write_preview(plan, diag, span)

        self._stats["converted"] += 1
        diag.info(
            f"Converted ASCII diagram to Mermaid "
            f"({chosen.diagram_type}, confidence {chosen.confidence:.2f})",
            code="ASCI004",
            location=span,
            data={
                "scheme_id": chosen.scheme_id,
                "diagram_type": chosen.diagram_type,
                "confidence": chosen.confidence,
            },
        )
        return Diagram(
            diagram_type="mermaid",
            content=chosen.mermaid,
            span=span,
        )

    def _select_scheme(
        self,
        plan: ConversionPlan,
        diag: DiagnosticCollector,
        span: Any,
    ) -> Optional[ConversionScheme]:
        """按模式选择方案。"""
        if self.mode == "interactive":
            if self.selector is None:
                diag.warning(
                    "Interactive selection requested but no selector configured, "
                    "using best scheme",
                    code="ASCI006",
                    location=span,
                )
                return plan.best
            return self.selector(plan)
        return plan.best

    # ============================================================
    # 多方案预览
    # ============================================================

    def _write_preview(
        self,
        plan: ConversionPlan,
        diag: DiagnosticCollector,
        span: Any,
    ) -> None:
        """将全部候选方案写入预览目录并生成报告。"""
        self._counter += 1
        preview_dir = Path(self.preview_dir)
        preview_dir.mkdir(parents=True, exist_ok=True)

        report_lines = [
            f"# ASCII Diagram Preview #{self._counter}",
            "",
            f"检测类型: **{plan.detected_type}**",
            "",
            "| 方案 | 类型 | 置信度 | 文件 |",
            "|------|------|--------|------|",
        ]
        preview_files: List[str] = []

        for scheme in plan.schemes:
            filename = f"ascii_{self._counter:02d}_{scheme.diagram_type}.mmd"
            filepath = preview_dir / filename
            filepath.write_text(scheme.mermaid, encoding="utf-8")
            preview_files.append(str(filepath))
            report_lines.append(
                f"| {scheme.scheme_id} | {scheme.diagram_type} | "
                f"{scheme.confidence:.2f} | `{filename}` |"
            )

        report_lines.extend(["", "## Mermaid 代码", ""])
        for scheme in plan.schemes:
            report_lines.extend(
                [
                    f"### {scheme.scheme_id} ({scheme.diagram_type})",
                    "",
                    "```mermaid",
                    scheme.mermaid,
                    "```",
                    "",
                ]
            )

        report_md = preview_dir / f"preview_report_{self._counter:02d}.md"
        report_json = preview_dir / f"preview_report_{self._counter:02d}.json"
        report_md.write_text("\n".join(report_lines), encoding="utf-8")
        report_json.write_text(
            json.dumps(
                {
                    "index": self._counter,
                    "detected_type": plan.detected_type,
                    "schemes": [
                        {
                            "id": s.scheme_id,
                            "type": s.diagram_type,
                            "confidence": s.confidence,
                            "mermaid": s.mermaid,
                            "summary": s.summary,
                        }
                        for s in plan.schemes
                    ],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        self._preview_files.extend(preview_files)
        self._preview_files.append(str(report_md))
        self._preview_files.append(str(report_json))
        self._stats["preview_written"] += len(plan.schemes)
        diag.info(
            f"Wrote {len(plan.schemes)} preview schemes to {preview_dir}",
            code="ASCI007",
            location=span,
        )

    # ============================================================
    # 统计
    # ============================================================

    def get_stats(self) -> Dict[str, int]:
        return self._stats.copy()

    def reset_stats(self) -> None:
        self._stats = {
            "ascii_diagrams": 0,
            "converted": 0,
            "skipped": 0,
            "low_confidence": 0,
            "preview_written": 0,
            "schemes_generated": 0,
        }
