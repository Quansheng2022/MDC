"""
Diagram Pass - 图表转换 Pass

将 Diagram 节点或 Mermaid 代码块转换为 Image 节点。
支持 ASCII 结构图和 Mermaid 图表渲染。
"""

import base64
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from ...ast.nodes import CodeBlock, Diagram, Image, Node
from ...diagnostics.collector import DiagnosticCollector
from ...services.diagram_service import DiagramService
from .base import PassResult, TransformPass


class DiagramPass(TransformPass):
    """
    图表转换 Pass。

    将 Diagram 节点转换为 Image 节点：
        1. 检测 Mermaid 图表 → 渲染为 PNG/SVG
        2. 检测 ASCII 结构图 → 渲染为 SVG
        3. 将图片嵌入为 data URI 或保存为文件

    配置:
        format: 输出格式 ('svg', 'png')，默认 'svg'
        embed: 是否嵌入为 data URI，默认 True
        output_dir: 输出目录（如果 embed=False）
        scale: 缩放比例，默认 1.0
        background: 背景色，默认 'white'
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config=config or {})
        self.format = self.config.get("format", "svg")
        self.embed = self.config.get("embed", True)
        self.output_dir = self.config.get("output_dir", "output/images")
        self.scale = self.config.get("scale", 1.0)
        self.background = self.config.get("background", "white")
        self._counter = 0
        self._generated_files = []
        self._has_mmdc = self._check_mmdc()
        self._has_playwright = self._check_playwright()

    def _check_mmdc(self) -> bool:
        try:
            result = subprocess.run(
                ['mmdc', '--version'],
                capture_output=True,
                timeout=5,
                check=False
            )
            if result.returncode == 0:
                print("[DiagramPass] mmdc available")
                return True
        except Exception:
            pass
        print("[DiagramPass] mmdc not available")
        return False

    def _check_playwright(self) -> bool:
        try:
            import playwright
            return True
        except ImportError:
            return False

    def run(self, document: Node, diag: DiagnosticCollector) -> PassResult:
        self._counter = 0
        self._generated_files = []
        print(f"[DiagramPass] Running... (mmdc: {self._has_mmdc}, playwright: {self._has_playwright})")
        new_doc = self._transform_node(document, diag)
        return PassResult(
            document=new_doc,
            files=self._generated_files,
            diagnostics=[],
        )

    def _transform_node(self, node: Node, diag: DiagnosticCollector) -> Node:
        if node is None:
            return None

        if isinstance(node, Diagram):
            print(f"[DiagramPass] Found Diagram node (type: {node.diagram_type})")
            return self._render_diagram(node, diag)

        if isinstance(node, CodeBlock):
            lang = node.language.strip().lower() if node.language else ""
            print(f"[DiagramPass] Found CodeBlock with language: '{lang}'")
            if lang == "mermaid":
                print("[DiagramPass] Converting Mermaid code block to Diagram...")
                diagram = Diagram(
                    diagram_type="mermaid",
                    content=node.text,
                    span=node.span,
                )
                return self._render_diagram(diagram, diag)
            return node

        children = list(node.iter_children())
        if children:
            new_children = []
            for child in children:
                transformed = self._transform_node(child, diag)
                if transformed is not None:
                    new_children.append(transformed)
            if new_children:
                return node.replace_children(new_children)
        return node

    def _render_diagram(self, node: Diagram, diag: DiagnosticCollector) -> Image:
        self._counter += 1
        print(f"[DiagramPass] Rendering diagram #{self._counter} (type: {node.diagram_type})")
        if node.diagram_type == "mermaid":
            return self._render_mermaid(node, diag)
        else:
            return self._render_ascii(node, diag)

    def _render_ascii(self, node: Diagram, diag: DiagnosticCollector) -> Image:
        """
        渲染 ASCII 结构图，失败时降级为文本 SVG。
        """
        try:
            lines = node.content.splitlines() if node.content else []
            if not lines:
                raise ValueError("Empty diagram content")

            svg = DiagramService.render_svg(lines)
            if not svg:
                raise ValueError("DiagramService returned empty SVG")

            if self.embed:
                b64 = base64.b64encode(svg.encode('utf-8')).decode('ascii')
                src = f"data:image/svg+xml;base64,{b64}"
            else:
                src = self._save_svg_to_file(svg, "ascii", diag)

            print("[DiagramPass] ASCII diagram rendered successfully")
            return Image(alt=f"ASCII Diagram {self._counter}", src=src, span=node.span)

        except Exception as e:
            print(f"[DiagramPass] ASCII rendering failed: {e}")
            diag.warning(
                f"Failed to render ASCII diagram, using text fallback: {e}",
                code="DIAG001",
                location=node.span
            )
            # ✅ 增强降级：生成包含原始文本的 SVG
            return self._create_text_fallback_image(node)

    def _render_mermaid(self, node: Diagram, diag: DiagnosticCollector) -> Image:
        print("[DiagramPass] Rendering Mermaid diagram...")
        src = None
        if self._has_mmdc:
            src = self._render_with_mmdc(node.content, diag)
        if not src and self._has_playwright:
            src = self._render_with_playwright(node.content, diag)
        if src:
            print("[DiagramPass] Mermaid rendered successfully")
            return Image(alt=f"Mermaid Diagram {self._counter}", src=src, span=node.span)

        print("[DiagramPass] Mermaid rendering failed, using fallback")
        diag.warning(
            "Mermaid rendering failed, using text fallback. Install mmdc: npm install -g @mermaid-js/mermaid-cli",
            code="DIAG002",
            location=node.span
        )
        return self._create_text_fallback_image(node)

    def _render_with_mmdc(self, content: str, diag: DiagnosticCollector) -> str:
        try:
            with tempfile.NamedTemporaryFile(suffix='.mmd', delete=False, mode='w', encoding='utf-8') as f:
                f.write(content)
                mmd_file = Path(f.name)
            output_dir = Path(self.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"mermaid_{self._counter:04d}.png"
            print(f"[DiagramPass] Running mmdc: {mmd_file} -> {output_file}")
            result = subprocess.run([
                'mmdc',
                '-i', str(mmd_file),
                '-o', str(output_file),
                '-f', 'png',
                '--scale', '2',
                '--backgroundColor', 'white'
            ], capture_output=True, timeout=60)
            mmd_file.unlink()
            if result.returncode == 0 and output_file.exists():
                if self.embed:
                    with open(output_file, 'rb') as f:
                        img_data = f.read()
                    output_file.unlink()
                    b64 = base64.b64encode(img_data).decode('ascii')
                    return f"data:image/png;base64,{b64}"
                else:
                    self._generated_files.append(str(output_file))
                    return str(output_file)
            else:
                print(f"[DiagramPass] mmdc failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            print("[DiagramPass] mmdc timeout")
        except Exception as e:
            print(f"[DiagramPass] mmdc error: {e}")
        return ""

    def _render_with_playwright(self, content: str, diag: DiagnosticCollector) -> str:
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(viewport={'width': 1200, 'height': 800})
                html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
                    <style>
                        body {{ margin: 0; padding: 20px; background: white; }}
                        .mermaid {{ text-align: center; }}
                    </style>
                </head>
                <body>
                    <pre class="mermaid">{content}</pre>
                    <script>
                        mermaid.initialize({{
                            startOnLoad: true,
                            theme: 'default',
                            themeVariables: {{
                                primaryColor: '#E8F0FE',
                                primaryTextColor: '#333',
                                primaryBorderColor: '#4A7FB5',
                                lineColor: '#555',
                            }}
                        }});
                    </script>
                </body>
                </html>
                """
                page.set_content(html)
                page.wait_for_timeout(3000)
                element = page.query_selector(".mermaid")
                if element:
                    screenshot = element.screenshot(type='png')
                    browser.close()
                    b64 = base64.b64encode(screenshot).decode('ascii')
                    return f"data:image/png;base64,{b64}"
                browser.close()
        except ImportError:
            print("[DiagramPass] Playwright not installed")
        except Exception as e:
            print(f"[DiagramPass] Playwright error: {e}")
        return ""

    def _save_svg_to_file(self, svg_content: str, diagram_type: str, diag: DiagnosticCollector) -> str:
        output_dir = Path(self.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{diagram_type}_{self._counter:04d}.svg"
        filepath = output_dir / filename
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            self._generated_files.append(str(filepath))
            return str(filepath)
        except Exception as e:
            diag.warning(f"Failed to save diagram to {filepath}: {e}", code="DIAG003")
            return ""

    def _create_text_fallback_image(self, node: Diagram) -> Image:
        """
        生成包含原始 ASCII 文本的 SVG 占位图（降级方案）。
        """
        # 转义 XML 特殊字符
        text_content = node.content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        lines = node.content.splitlines() if node.content else []
        line_height = 18
        padding = 10
        width = max(600, max((len(line) * 8) for line in lines) + padding * 2)
        height = max(100, len(lines) * line_height + padding * 2)

        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
            <rect width="100%" height="100%" fill="#f8f9fa" rx="4"/>
            <text x="{padding}" y="{padding + 14}" font-family="monospace" font-size="12" fill="#333">
                <tspan x="{padding}" dy="0">⚠️ ASCII Diagram (rendering failed, showing raw text):</tspan>
            </text>
            <text x="{padding}" y="{padding + 14 + line_height}" font-family="monospace" font-size="11" fill="#555">
                <tspan x="{padding}" dy="0">{text_content}</tspan>
            </text>
        </svg>'''

        b64 = base64.b64encode(svg.encode('utf-8')).decode('ascii')
        return Image(
            alt=f"{node.diagram_type.capitalize()} Diagram (fallback)",
            src=f"data:image/svg+xml;base64,{b64}",
            span=node.span
        )

    def get_stats(self) -> Dict[str, Any]:
        return {
            "diagrams_processed": self._counter,
            "format": self.format,
            "embed": self.embed,
            "files_generated": len(self._generated_files),
            "generated_files": self._generated_files,
            "has_mmdc": self._has_mmdc,
            "has_playwright": self._has_playwright,
        }