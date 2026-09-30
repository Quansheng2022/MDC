"""
Compiler Context - 编译器上下文和编译流程控制

集成后处理器，支持封面页、目录更新和表格样式。
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from docx import Document

from .ast.nodes import Diagram, Heading, Image
from .config import resolve_config
from .diagnostics.collector import DiagnosticCollector
from .diagnostics.diagnostic import Severity
from .parser.markdown_parser import MarkdownParser
from .parser.parser_context import ParserContext
from .pipeline.pass_registry import PassRegistry
from .pipeline.passes.ascii_mermaid_pass import AsciiToMermaidPass
from .pipeline.passes.diagram_pass import DiagramPass
from .pipeline.passes.normalize_pass import NormalizePass
from .pipeline.passes.simple_table_pass import SimpleTablePass
from .pipeline.pipeline import Pipeline
from .profiles import (
    DEFAULT_PROFILE_ID,
    is_known_profile_id,
    profile_ids,
    resolve_profile,
    theme_presentation_overrides,
)
from .quality_gate import (
    QualityGateDecision,
    QualityGateError,
    QualityGatePolicy,
    RepairRecord,
    decide_qa,
)
from .renderer.layout.artifact_contract import ArtifactContract
from .renderer.layout.decision_engine import DecisionEngine
from .renderer.layout.final_artifact_qa import FinalArtifactQA
from .renderer.layout.rendered_qa import RenderedQA
from .renderer.layout.repair_strategy import RepairStrategy
from .renderer.layout.static_qa import StaticQA
from .renderer.layout.validity_gate import ValidityGate
from .renderer.post_processor import DocxPostProcessor
from .renderer.render_context import RenderContext
from .renderer.themes.default import create_theme
from .renderer.themes.v15_theme import V15Theme
from .renderer.word_renderer import WordRenderer
from .renderer.word_writer import WordWriter

logger = logging.getLogger(__name__)


def _is_unresolved_profile_request(value: Any) -> bool:
    """Return whether ``value`` is a non-empty profile identifier that is unknown.

    The registry resolves an unknown identifier safely; this helper only decides
    whether the fallback deserves a diagnostic, so the compiler never silently
    ignores an unsupported request (``AGENTS.md``: no silent failures).
    """
    return isinstance(value, str) and bool(value.strip()) and not is_known_profile_id(value)


@dataclass
class CompilerContext:
    """
    编译器上下文，包含所有编译过程中需要的组件。

    采用依赖注入方式，所有子上下文通过构造函数注入，
    便于测试和扩展。
    """

    diag: DiagnosticCollector
    config: Dict[str, Any]
    parser_ctx: ParserContext
    render_ctx: RenderContext
    pass_registry: PassRegistry
    quality_gate_policy: QualityGatePolicy = field(default_factory=QualityGatePolicy)
    static_qa_result: Any = None
    rendered_qa_result: Any = None
    final_artifact_qa_result: Any = None
    post_processor_result: Optional[Dict[str, Any]] = None
    repair_evidence: List[RepairRecord] = field(default_factory=list)
    final_artifact_sha256: str = ""

    @classmethod
    def create(cls, config: Dict[str, Any] = None) -> "CompilerContext":
        """
        创建编译器上下文的工厂方法。

        参数:
            config: 配置字典，可包含以下键:
                - theme: 主题实例或主题名称
                - output_dir: 输出目录
                - verbose: 是否显示详细信息
                - normalize: 是否启用 NormalizePass (默认 True)
                - diagram: 是否启用 DiagramPass (默认 True)
                - enable_cover / toc / style_tables: 最终产物能力开关，
                  默认值由 config.DEFAULT_CONFIG 唯一定义（F4）
                - word_com: 是否使用 Word COM 刷新 TOC 页码 (默认 True)

        返回:
            CompilerContext: 初始化完成的编译器上下文
        """
        config = resolve_config(config)

        # 诊断收集器
        diag = DiagnosticCollector()

        # 主题：默认使用 QS-Word-Default-V1.5（已冻结）
        theme = config.get("theme")
        if theme is None or theme == "default":
            theme = V15Theme.load_default()
        elif isinstance(theme, str):
            theme = create_theme(theme)

        # Program C：专业输出档案（有界呈现配置，单一集成点）
        #
        # 唯一权威是 md_converter.profiles.registry；GUI 只传递标识符。渲染器
        # 不含任何 profile 分支，只消费叠加后的既有主题数据。
        requested_profile = config.get("output_profile")
        profile = resolve_profile(requested_profile)
        if _is_unresolved_profile_request(requested_profile):
            diag.warning(
                f"Unknown output profile {requested_profile!r}; falling back to {profile.id!r}",
                code="PROFILE001",
                source="compiler",
                suggestion="Supported profiles: " + ", ".join(profile_ids()),
            )
        # 默认档案无需覆盖：编译器默认主题本身就是默认档案的呈现，因此主题对象
        # 保持不动（最强“不静默改版”保证，同时保留调用方自定义主题）。
        if profile.id != DEFAULT_PROFILE_ID:
            if hasattr(theme, "with_presentation_overrides"):
                theme = theme.with_presentation_overrides(theme_presentation_overrides(profile))
            else:
                diag.warning(
                    f"Output profile {profile.id!r} was ignored: theme "
                    f"{type(theme).__name__} does not accept presentation overrides",
                    code="PROFILE002",
                    source="compiler",
                    suggestion="Use the default V1.5 theme to apply an output profile",
                )

        # 解析器上下文
        parser_ctx = ParserContext(
            diag=diag,
            config=config,
            frontmatter={},
        )

        # 渲染器上下文
        #
        # IMG-CFG-01：把已解析配置中的图形目标宽度传入既有 ``RenderContext.config``
        # 槽（SPEC-FUNC-023：目标宽度 = min(配置 image_width, 有效宽度)）。渲染器在
        # ``WordRenderer._figure_bounds_cm()`` 中经 ``self.ctx.config`` 读取该键，并交给
        # ``plan_figure_fit``（唯一尺寸权威）。此处只传播 ``image_width``：整份已解析配置
        # 传入会顺带激活同槽位上其它此前未在该路径上授权的键（``page_margins`` /
        # ``page_width`` / ``toc_depth``），构成越界语义变更；因此保持最小、零漂移的传播。
        render_ctx = RenderContext(
            theme=theme,
            diag=diag,
            config={"image_width": config["image_width"]},
        )

        # Pass 注册表
        pass_registry = PassRegistry()

        # 注册内置 Pass
        if config.get("normalize", True):
            pass_registry.register(NormalizePass)

        if config.get("diagram", True):
            ascii_config = config.get("ascii_to_mermaid") or {}
            if ascii_config.get("enabled", True):
                pass_registry.register(
                    AsciiToMermaidPass,
                    priority=50,
                    config=ascii_config,
                )
            pass_registry.register(DiagramPass)

        # P12-CAND-001：空白对齐简单表格识别（在 NormalizePass 之后运行）
        simple_tables_config = config.get("simple_tables") or {}
        if simple_tables_config.get("enabled", True):
            pass_registry.register(SimpleTablePass, priority=110)

        logger.debug("Registered compiler passes: %s", pass_registry.get_names())

        # 插件发现（暂时禁用）
        # try:
        #     discovered = discover_passes()
        #     for pass_inst in discovered:
        #         pass_registry.register(type(pass_inst))
        # except Exception as e:
        #     diag.warning(f"Failed to discover plugins: {e}", code="PLUGIN001")

        return cls(
            diag=diag,
            config=config,
            parser_ctx=parser_ctx,
            render_ctx=render_ctx,
            pass_registry=pass_registry,
            quality_gate_policy=QualityGatePolicy.from_config(config),
        )

    def compile(
        self,
        markdown_text: str,
        metadata: Optional[Dict[str, Any]] = None,
        output_path: Optional[Path] = None,
    ) -> Document:
        """
        编译 Markdown 文本为 Word 文档。

        执行流程（CANONICAL_SPEC.md §4 Quality Gate Contract）:
            1. 解析: Markdown → AST
            2. Pipeline: AST → AST (经过 Pass 转换)
            3. LayoutPlan + StaticQA（Build Gate: FAIL → QualityGateError）
            4. 渲染: AST → Word 文档
            5. RenderedQA + Repair 有限闭环（≤ max_repair_iterations）
            6. 后处理: 插入封面页、样式化表格、更新 TOC
            7. FinalArtifactQA（检查对象 == 发布对象，记录 sha256）

        参数:
            markdown_text: Markdown 源文本
            metadata: Frontmatter 元数据（用于封面页）
            output_path: 输出文件路径（默认为配置中的 output_dir）

        返回:
            docx.Document: python-docx 文档对象

        异常:
            QualityGateError: 任一质量门 FAIL（或 QA 基础设施异常，FAIL CLOSED）
        """
        if metadata is None:
            metadata = {}

        policy = QualityGatePolicy.from_config(self.config)
        self.quality_gate_policy = policy
        self.repair_evidence.clear()
        self.static_qa_result = None
        self.rendered_qa_result = None
        self.final_artifact_qa_result = None
        self.final_artifact_sha256 = ""
        post_features = {
            "cover": bool(self.config["enable_cover"]),
            "toc": bool(self.config["toc"]),
            "table_styling": bool(self.config["style_tables"]),
        }
        post_required = any(post_features.values())
        self.post_processor_result = {
            "status": "NOT_RUN",
            "required": post_required,
            "features": post_features,
        }

        # 1. 解析阶段
        parser = MarkdownParser(self.parser_ctx)
        try:
            ast = parser.parse(markdown_text)
            logger.debug("Parsed AST with %d children", len(ast.children))
        except Exception as e:
            self.diag.error(f"Parser error: {e}", code="PARSE001")
            raise

        # 2. Pipeline 阶段
        try:
            passes = self.pass_registry.get_passes()
            logger.debug("Running %d pipeline passes", len(passes))
            pipeline = Pipeline(passes=passes)
            ast = pipeline.run(ast, self.diag)
        except Exception as e:
            self.diag.error(f"Pipeline error: {e}", code="PIPE001")
            raise

        # 3. LayoutPlan + StaticQA（Build Gate，P0-05）
        try:
            writer = WordWriter.create()
            renderer = WordRenderer(self.render_ctx, writer)
            gate = ValidityGate.from_theme(self.render_ctx.theme)
            engine = DecisionEngine(
                theme=self.render_ctx.theme,
                validity_gate=gate,
            )
            plan = engine.build_plan(ast, user_overrides=self._extract_layout_overrides())
            static_qa = StaticQA(theme=self.render_ctx.theme, diag=self.diag)
            static_result = static_qa.run(ast)
            self.static_qa_result = static_result
            if static_result.status == "FAIL":
                raise QualityGateError(stage="static_qa", result=static_result)
            if static_result.status == "PASS_WITH_WARN" and policy.fail_on_warning:
                raise QualityGateError(stage="static_qa", result=static_result)
        except QualityGateError:
            raise
        except Exception as e:
            self.diag.error(f"Renderer error: {e}", code="RENDER001")
            raise

        # 4. 确定输出路径
        if output_path is None:
            output_dir = Path(self.config.get("output_dir", "output"))
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / "document.docx"

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 5. 渲染并保存
        try:
            doc = renderer.render(ast, layout_plan=plan)
            doc.save(str(output_path))
            logger.debug("Document saved to %s", output_path)
        except Exception as e:
            self.diag.error(f"Failed to render/save document: {e}", code="RENDER001")
            raise

        # 6. RenderedQA + Repair 有限闭环（P0-06 / P0-07）
        current_plan = plan
        try:
            rendered_qa = RenderedQA(theme=self.render_ctx.theme, diag=self.diag)
            repair_strategy = RepairStrategy(max_repair_iterations=policy.max_repair_iterations)
            from docx import Document as _Document

            iteration = 0
            pending_record: Optional[RepairRecord] = None
            while True:
                doc = _Document(str(output_path))
                rendered_result = rendered_qa.run(doc, current_plan)
                self.rendered_qa_result = rendered_result
                if pending_record is not None:
                    pending_record.after_status = rendered_result.status
                    pending_record = None

                repairable = repair_strategy.can_repair(
                    current_plan, static_result, rendered_result
                )
                decision = decide_qa(rendered_result.status, repairable, policy)

                if decision == QualityGateDecision.CONTINUE:
                    break
                if decision == QualityGateDecision.ABORT:
                    raise QualityGateError(stage="rendered_qa", result=rendered_result)

                # REPAIR（有界闭环）
                if iteration >= policy.max_repair_iterations:
                    if rendered_result.status == "FAIL":
                        raise QualityGateError(
                            stage="repair",
                            result=rendered_result,
                            message=(
                                f"Repair iterations exhausted ({iteration}) with status "
                                f"{rendered_result.status}"
                            ),
                        )
                    break

                issue = repair_strategy.first_repairable_issue(static_result, rendered_result)
                revised = repair_strategy.repair(current_plan, static_result, rendered_result)
                if revised is current_plan:
                    raise QualityGateError(
                        stage="repair",
                        result=rendered_result,
                        message="No repair progress possible",
                    )

                strategies = list(revised.metadata.get("repair_strategies", []))
                strategy = (
                    strategies[0] if strategies else repair_strategy.select_strategy(issue or {})
                )
                pending_record = RepairRecord(
                    repair_iteration=iteration,
                    original_issue=issue
                    or {"code": "unknown", "message": "Unknown repair trigger"},
                    selected_strategy=strategy,
                    changed_blocks=list(revised.metadata.get("changed_blocks", [])),
                    before_status=rendered_result.status,
                )
                self.repair_evidence.append(pending_record)
                logger.debug(
                    "Repair iteration %d: %s -> %s",
                    iteration,
                    rendered_result.status,
                    strategy,
                )

                writer2 = WordWriter.create()
                renderer2 = WordRenderer(self.render_ctx, writer2)
                doc = renderer2.render(ast, layout_plan=revised)
                doc.save(str(output_path))
                current_plan = revised
                iteration += 1
        except Exception as e:
            if isinstance(e, QualityGateError):
                raise
            raise QualityGateError(
                stage="rendered_qa",
                result=None,
                message=f"Rendered QA infrastructure failure (FAIL CLOSED): {e}",
            ) from e

        # 7. 后处理（封面页、表格样式、TOC）
        # 只要任一 required post-processing 能力启用，调用失败即 FAIL CLOSED：
        # POST001 从 warning 升级为 ERROR / QualityGateError(stage="post_processor")。
        if post_required:
            try:
                # 合并元数据：如果标题未在 metadata 中，使用文件名
                if "title" not in metadata:
                    metadata["title"] = output_path.stem
                DocxPostProcessor.process(output_path, metadata, self.config)
                # 重新加载后处理后的文档
                doc = Document(str(output_path))
                logger.debug("Post-processing completed")
                self.post_processor_result = {
                    "status": "PASS",
                    "required": True,
                    "features": post_features,
                }
            except Exception as e:
                self.post_processor_result = {
                    "status": "FAIL",
                    "required": True,
                    "features": post_features,
                }
                self.diag.error(f"Post-processing failed: {e}", code="POST001")
                logger.error("Post-processing failed", exc_info=True)
                raise QualityGateError(
                    stage="post_processor",
                    result=None,
                    message=f"Required post-processing failed: {e}",
                ) from e
        else:
            self.post_processor_result = {
                "status": "NOT_REQUIRED",
                "required": False,
                "features": post_features,
            }

        # 8. Final Artifact QA（P0-08：测试对象 == 发布对象）
        try:
            final_qa = FinalArtifactQA(theme=self.render_ctx.theme, diag=self.diag)
            final_result = final_qa.run(
                output_path,
                layout_plan=current_plan,
                source_text=self._semantic_text(ast),
                metadata=metadata,
                config=self.config,
                contract=ArtifactContract.from_config(self.config),
                expected_headings=[
                    heading.to_plain_text() for heading in self._collect_headings(ast)
                ],
            )
            self.final_artifact_qa_result = final_result
            self.final_artifact_sha256 = str(final_result.metrics.get("artifact_sha256", ""))
            if final_result.status == "FAIL" and policy.fail_on_error:
                raise QualityGateError(stage="final_artifact_qa", result=final_result)
            if final_result.status == "PASS_WITH_WARN" and policy.fail_on_warning:
                raise QualityGateError(stage="final_artifact_qa", result=final_result)
        except QualityGateError:
            raise
        except Exception as e:
            raise QualityGateError(
                stage="final_artifact_qa",
                result=None,
                message=f"Final QA infrastructure failure (FAIL CLOSED): {e}",
            ) from e

        return doc

    def _extract_layout_overrides(self) -> Dict[str, Any]:
        """从配置中提取用户显式布局意图（P0，经过 Validity Gate）。"""
        override_keys = [
            "body_font_size",
            "heading_font_size",
            "table_font_size",
            "margin",
            "page_orientation",
            "content_deletion",
            "semantic_destruction",
        ]
        return {key: self.config[key] for key in override_keys if key in self.config}

    @staticmethod
    def _semantic_text(document: Any) -> str:
        """
        提取用于 No Content Loss 检查的语义纯文本。

        跳过视觉节点（Diagram / Image）：它们以图片形式保留，
        不作为文本 token 参与保全检查。
        """
        parts: List[str] = []
        stack: List[Any] = [document]
        while stack:
            node = stack.pop()
            if isinstance(node, (Diagram, Image)):
                continue
            children = list(node.iter_children())
            if not children:
                parts.append(node.to_plain_text())
            else:
                stack.extend(reversed(children))
        return "\n".join(parts)

    @staticmethod
    def _collect_headings(document: Any) -> List[Heading]:
        """深度优先收集文档中的标题节点。"""
        headings: List[Heading] = []
        stack: List[Any] = [document]
        while stack:
            node = stack.pop()
            if isinstance(node, Heading):
                headings.append(node)
            stack.extend(node.iter_children())
        return headings

    def get_quality_gate_report(self) -> Dict[str, Any]:
        """返回本次编译的质量门证据（供 Release Evidence 使用）。"""
        return {
            "policy": {
                "fail_on_error": self.quality_gate_policy.fail_on_error,
                "fail_on_warning": self.quality_gate_policy.fail_on_warning,
                "max_repair_iterations": self.quality_gate_policy.max_repair_iterations,
            },
            "static_qa": self.static_qa_result.to_dict() if self.static_qa_result else None,
            "post_processor": self.post_processor_result,
            "rendered_qa": (self.rendered_qa_result.to_dict() if self.rendered_qa_result else None),
            "final_artifact_qa": (
                self.final_artifact_qa_result.to_dict() if self.final_artifact_qa_result else None
            ),
            "repair_evidence": [record.to_dict() for record in self.repair_evidence],
            "artifact_sha256": self.final_artifact_sha256,
        }

    def compile_file(
        self,
        file_path: Path,
        metadata: Optional[Dict[str, Any]] = None,
        output_path: Optional[Path] = None,
    ) -> Document:
        """
        编译 Markdown 文件为 Word 文档。

        参数:
            file_path: Markdown 文件路径
            metadata: 额外的 Frontmatter 元数据（将覆盖文件内解析的）
            output_path: 输出文件路径

        返回:
            docx.Document: python-docx 文档对象
        """
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        # 解析 Frontmatter
        from .utils.helpers import parse_frontmatter

        body, meta = parse_frontmatter(text)
        # 合并 metadata
        if metadata:
            meta.update(metadata)
        # 如果 output_path 未指定，根据 title 或文件名生成
        if output_path is None:
            title = meta.get("title", file_path.stem)
            safe_title = "".join(c for c in title if c.isalnum() or c in " _-")
            safe_title = safe_title.replace(" ", "_")
            output_dir = Path(self.config.get("output_dir", "output"))
            output_path = output_dir / f"{safe_title}.docx"
        return self.compile(body, meta, output_path)

    def has_errors(self) -> bool:
        """检查是否有错误"""
        return any(d.severity == Severity.ERROR for d in self.diag.diagnostics)

    def has_warnings(self) -> bool:
        """检查是否有警告"""
        return any(d.severity == Severity.WARNING for d in self.diag.diagnostics)

    def get_diagnostics(self, severity: Severity = None):
        """获取诊断信息"""
        if severity is None:
            return self.diag.diagnostics
        return [d for d in self.diag.diagnostics if d.severity == severity]

    def clear_diagnostics(self):
        """清空诊断"""
        self.diag.diagnostics.clear()


# 便捷函数
def compile_markdown(
    text: str,
    config: Dict[str, Any] = None,
    theme: Any = None,
    metadata: Optional[Dict[str, Any]] = None,
    output_path: Optional[Path] = None,
) -> Document:
    """便捷函数：编译 Markdown 文本"""
    config = dict(config or {})
    if theme is not None:
        config["theme"] = theme
    ctx = CompilerContext.create(config)
    return ctx.compile(text, metadata, output_path)


def compile_file(
    file_path: str,
    config: Dict[str, Any] = None,
    theme: Any = None,
    metadata: Optional[Dict[str, Any]] = None,
    output_path: Optional[Path] = None,
) -> Document:
    """便捷函数：编译 Markdown 文件"""
    config = dict(config or {})
    if theme is not None:
        config["theme"] = theme
    ctx = CompilerContext.create(config)
    return ctx.compile_file(Path(file_path), metadata, output_path)
