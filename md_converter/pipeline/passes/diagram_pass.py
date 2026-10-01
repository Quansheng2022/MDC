"""
Diagram Pass - 图表转换 Pass

将 Diagram 节点或 Mermaid 代码块转换为 Image 节点。
支持 ASCII 结构图和 Mermaid 图表渲染。
"""

import base64
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from ...ast.nodes import CodeBlock, Diagram, Image, Node
from ...diagnostics.collector import DiagnosticCollector
from ...services.diagram_service import DiagramService
from .base import PassResult, TransformPass

#: Vendored Mermaid 10 runtime shipped with the product.  Rendering must not
#: depend on outbound access to a CDN at conversion time, and the packaged
#: desktop build must render exactly what the source environment renders.
_MERMAID_RUNTIME_ASSET = (
    Path(__file__).resolve().parents[2] / "renderer" / "assets" / "mermaid.min.js"
)

#: Mermaid runtime used only when the vendored asset is unavailable.
_MERMAID_RUNTIME_CDN = "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"

#: Explicit Chromium executable override (deployment/verification hook).
_BROWSER_PATH_ENV = "MDC_MERMAID_BROWSER_PATH"

#: Page shell used for Mermaid rendering.  The Mermaid runtime itself is
#: injected separately (vendored asset, or the CDN as a last resort).
_MERMAID_PAGE_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ margin: 0; padding: 20px; background: white; }}
        .mermaid {{ text-align: center; }}
    </style>
</head>
<body>
    <pre class="mermaid">{content}</pre>
</body>
</html>
"""


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
        self._last_render_error = ""
        self._browser_source = ""

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
        self._last_render_error = ""
        self._browser_source = ""
        if self._has_mmdc:
            src = self._render_with_mmdc(node.content, diag)
        if not src and self._has_playwright:
            src = self._render_with_playwright(node.content, diag)
        if src:
            print(f"[DiagramPass] Mermaid rendered successfully ({self._browser_source})")
            return Image(alt=f"Mermaid Diagram {self._counter}", src=src, span=node.span)

        print(f"[DiagramPass] Mermaid rendering failed, using fallback: {self._last_render_error}")
        message = (
            "Mermaid rendering failed, using text fallback. "
            "Install mmdc: npm install -g @mermaid-js/mermaid-cli"
        )
        if self._last_render_error:
            message = f"{message} (reason: {self._last_render_error})"
        diag.warning(
            message,
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
                self._last_render_error = f"mmdc exit {result.returncode}: {result.stderr}"
        except subprocess.TimeoutExpired:
            print("[DiagramPass] mmdc timeout")
            self._last_render_error = "mmdc timeout"
        except Exception as e:
            print(f"[DiagramPass] mmdc error: {e}")
            self._last_render_error = f"mmdc error: {e}"
        return ""

    def _render_with_playwright(self, content: str, diag: DiagnosticCollector) -> str:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("[DiagramPass] Playwright not installed")
            self._last_render_error = "Playwright is not installed"
            return ""

        bundled_browsers = self._bundled_browsers_dir()
        if bundled_browsers is not None:
            os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(bundled_browsers))

        try:
            with sync_playwright() as p:
                browser, source = self._launch_chromium(p)
                if browser is None:
                    self._last_render_error = f"no usable Chromium ({source})"
                    print(f"[DiagramPass] Playwright error: {self._last_render_error}")
                    return ""
                self._browser_source = source
                page = browser.new_page(viewport={'width': 1200, 'height': 800})
                try:
                    page.set_content(_MERMAID_PAGE_TEMPLATE.format(content=content))
                    runtime_script = self._mermaid_runtime_script()
                    if runtime_script:
                        page.add_script_tag(content=runtime_script)
                    else:
                        page.add_script_tag(url=_MERMAID_RUNTIME_CDN)
                    page.evaluate(
                        """async () => {
                            mermaid.initialize({
                                startOnLoad: false,
                                theme: 'default',
                                themeVariables: {
                                    primaryColor: '#E8F0FE',
                                    primaryTextColor: '#333',
                                    primaryBorderColor: '#4A7FB5',
                                    lineColor: '#555',
                                }
                            });
                            try {
                                await mermaid.run({ querySelector: '.mermaid' });
                            } catch (error) {
                                window.__mermaidRunError = String(error);
                            }
                        }"""
                    )
                    # Rendering guard: only a real <svg> counts as rendered, so a
                    # page that never ran Mermaid can never be screenshotted as
                    # "raw Mermaid source" and silently written into the DOCX.
                    page.wait_for_selector(".mermaid svg", timeout=15000)
                    element = page.query_selector(".mermaid")
                    if element is None:
                        self._last_render_error = "mermaid container missing after render"
                        return ""
                    screenshot = element.screenshot(type='png')
                    b64 = base64.b64encode(screenshot).decode('ascii')
                    return f"data:image/png;base64,{b64}"
                finally:
                    browser.close()
        except Exception as e:
            print(f"[DiagramPass] Playwright error: {e}")
            self._last_render_error = f"playwright error: {e}"
        return ""

    def _bundled_browsers_dir(self) -> Optional[Path]:
        """
        返回随包分发的 Playwright 浏览器目录（仅冻结构建存在）。

        Returns:
            Optional[Path]: 打包内置的浏览器根目录；源码运行时为 None。
        """
        bundle_root = getattr(sys, "_MEIPASS", None)
        if not bundle_root:
            return None
        candidate = Path(bundle_root) / "ms-playwright"
        return candidate if candidate.is_dir() else None

    def _browser_candidates(self) -> list:
        """
        返回按优先级排列的 Chromium 启动参数。

        顺序为：显式配置的浏览器可执行文件 → Playwright 自带浏览器 →
        操作系统自带的 Chromium/Edge。这样打包发布既可以使用随包浏览器，
        也可以使用目标机器已有的浏览器，而不是静默退化为原始源码图片。

        Returns:
            list: playwright ``chromium.launch`` 关键字参数列表（含 source 标签）。
        """
        candidates = []
        explicit = os.environ.get(_BROWSER_PATH_ENV, "").strip()
        if explicit and Path(explicit).is_file():
            candidates.append({"executable_path": explicit, "source": f"explicit:{explicit}"})
        candidates.append({"source": "playwright-chromium"})
        candidates.append({"channel": "msedge", "source": "system-microsoft-edge"})
        return candidates

    def _launch_chromium(self, playwright_obj: Any) -> tuple:
        """
        启动一个可用的 Chromium。

        Args:
            playwright_obj: ``sync_playwright()`` 上下文对象。

        Returns:
            tuple: ``(browser, source)``；全部候选失败时为 ``(None, reason)``。
        """
        reason = ""
        for candidate in self._browser_candidates():
            source = candidate.get("source", "unknown")
            options = {key: value for key, value in candidate.items() if key != "source"}
            try:
                browser = playwright_obj.chromium.launch(headless=True, **options)
                return browser, source
            except Exception as exc:
                reason = f"{source}: {exc}"
                print(f"[DiagramPass] Chromium launch failed via {source}: {exc}")
        return None, reason

    def _mermaid_runtime_script(self) -> str:
        """
        返回要注入页面的 Mermaid 运行时代码。

        Returns:
            str: 随包分发的 Mermaid 运行时；缺失时返回空串（调用方回退到 CDN）。
        """
        cached = getattr(self, "_mermaid_runtime_cache", None)
        if cached is not None:
            return cached
        script = ""
        if _MERMAID_RUNTIME_ASSET.is_file():
            script = _MERMAID_RUNTIME_ASSET.read_text(encoding="utf-8")
        self._mermaid_runtime_cache = script
        return script

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
