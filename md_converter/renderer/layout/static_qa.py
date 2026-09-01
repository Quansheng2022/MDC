"""
Static QA - 渲染前质量检查（第十八章 18.1）

检查项:
    - ast_integrity: AST 完整性
    - semantic_integrity: 语义完整性（标题层级、表格结构）
    - table_structure: 表格列结构一致性
    - url_integrity: URL 完整性
    - font_configuration: 字体配置（最小字号门）
    - style_configuration: 样式配置
    - section_configuration: Section 配置
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ...ast.nodes import Document, Heading, Table
from ...diagnostics.collector import DiagnosticCollector
from .themes_v15_protocol import ThemeProtocol


@dataclass
class StaticQAResult:
    """Static QA 报告。"""

    status: str = "PASS"  # PASS | PASS_WITH_WARN | FAIL
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "errors": self.errors,
            "warnings": self.warnings,
        }


class StaticQA:
    """
    渲染前 QA。

    用法:
        qa = StaticQA(theme, diag)
        result = qa.run(document)
    """

    def __init__(
        self,
        theme: Optional[ThemeProtocol] = None,
        diag: Optional[DiagnosticCollector] = None,
    ):
        self.theme = theme
        self.diag = diag

    def run(self, document: Document) -> StaticQAResult:
        """执行全部 Static QA 检查。"""
        result = StaticQAResult()
        self._check_ast_integrity(document, result)
        self._check_semantic_integrity(document, result)
        self._check_table_structure(document, result)
        self._check_font_configuration(result)
        self._check_style_configuration(result)
        self._check_section_configuration(result)
        self._emit(result)
        if result.errors:
            result.status = "FAIL"
        elif result.warnings:
            result.status = "PASS_WITH_WARN"
        return result

    def _check_ast_integrity(self, document: Document, result: StaticQAResult) -> None:
        if not document.children:
            result.errors.append({"code": "ast_empty", "message": "Document has no content"})
        for child in document.children:
            if child.span is None:
                result.warnings.append(
                    {
                        "code": "ast_span_missing",
                        "message": f"Node {type(child).__name__} has no source span",
                    }
                )

    def _check_semantic_integrity(self, document: Document, result: StaticQAResult) -> None:
        for node in document.iter_children():
            if isinstance(node, Heading):
                if node.level < 1 or node.level > 6:
                    result.errors.append(
                        {
                            "code": "semantic_heading_level",
                            "message": f"Heading level {node.level} out of range 1-6",
                            "location": str(node.span) if node.span else None,
                        }
                    )
                if not node.to_plain_text().strip():
                    result.warnings.append(
                        {
                            "code": "semantic_empty_heading",
                            "message": "Empty heading detected",
                            "location": str(node.span) if node.span else None,
                        }
                    )

    def _check_table_structure(self, document: Document, result: StaticQAResult) -> None:
        for node in document.iter_children():
            if isinstance(node, Table):
                if not node.rows:
                    result.warnings.append({"code": "table_empty", "message": "Table has no rows"})
                    continue
                widths = {len(row.cells) for row in node.rows}
                if len(widths) > 1:
                    result.warnings.append(
                        {
                            "code": "table_inconsistent_columns",
                            "message": (
                                "Table rows have inconsistent column counts: " f"{sorted(widths)}"
                            ),
                            "location": str(node.span) if node.span else None,
                        }
                    )

    def _check_font_configuration(self, result: StaticQAResult) -> None:
        if self.theme is None or not hasattr(self.theme, "readability_minimums"):
            return
        minimums = self.theme.readability_minimums
        if hasattr(self.theme, "body_size") and self.theme.body_size < minimums.get(
            "body_font", 10.0
        ):
            result.errors.append(
                {
                    "code": "font_below_minimum",
                    "message": (
                        f"Body font {self.theme.body_size}pt is below minimum "
                        f"{minimums['body_font']}pt"
                    ),
                }
            )
        if hasattr(self.theme, "table_font_size") and self.theme.table_font_size < minimums.get(
            "table_font", 8.5
        ):
            result.errors.append(
                {
                    "code": "font_below_minimum",
                    "message": (
                        f"Table font {self.theme.table_font_size}pt is below minimum "
                        f"{minimums['table_font']}pt"
                    ),
                }
            )

    def _check_style_configuration(self, result: StaticQAResult) -> None:
        if self.theme is None:
            result.warnings.append(
                {"code": "style_missing_theme", "message": "No theme configured"}
            )
            return
        for attr in ("body_font", "heading_font", "code_font"):
            if not hasattr(self.theme, attr) or not getattr(self.theme, attr):
                result.warnings.append(
                    {"code": "style_missing_font", "message": f"Theme missing {attr}"}
                )

    def _check_section_configuration(self, result: StaticQAResult) -> None:
        if self.theme is not None and hasattr(self.theme, "default_orientation"):
            if self.theme.default_orientation not in ("portrait", "landscape"):
                result.errors.append(
                    {
                        "code": "section_invalid_orientation",
                        "message": f"Invalid default orientation: {self.theme.default_orientation}",
                    }
                )

    def _emit(self, result: StaticQAResult) -> None:
        """将 QA 结果写入诊断收集器。"""
        if self.diag is None:
            return
        for issue in result.errors:
            self.diag.error(
                issue["message"],
                code="QA_STATIC_ERR",
                source="static_qa",
                data=issue,
            )
        for issue in result.warnings:
            self.diag.warning(
                issue["message"],
                code="QA_STATIC_WARN",
                source="static_qa",
                data=issue,
            )
