"""
Rendered QA - 渲染后质量检查（第十八章 18.2）

基于 python-docx 解析渲染后的文档，检查:
    - font_substitution / 最小字号违规
    - table_clipping（表格估算宽度超内容宽度）
    - figure_overflow / figure_below_min_width（图形几何，P12-CAND-002）
    - orphan_heading（孤立标题，无后续内容）
    - empty_page（连续分页符）
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ...diagnostics.collector import DiagnosticCollector
from .figure_sizing import figure_policy_from_theme
from .themes_v15_protocol import ThemeProtocol


@dataclass
class RenderedQAResult:
    """Rendered QA 报告。"""

    status: str = "PASS"  # PASS | PASS_WITH_WARN | FAIL
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "errors": self.errors,
            "warnings": self.warnings,
            "metrics": self.metrics,
        }


class RenderedQA:
    """
    渲染后 QA（基于 python-docx 解析）。

    用法:
        qa = RenderedQA(theme, diag)
        result = qa.run(doc, layout_plan)
    """

    def __init__(
        self,
        theme: Optional[ThemeProtocol] = None,
        diag: Optional[DiagnosticCollector] = None,
    ):
        self.theme = theme
        self.diag = diag

    def run(self, doc: Any, layout_plan: Any = None) -> RenderedQAResult:
        """执行渲染后检查。"""
        result = RenderedQAResult()
        self._check_font_violations(doc, result)
        self._check_table_overflow(doc, result)
        self._check_figure_geometry(doc, result)
        self._check_orphan_headings(doc, result)
        self._check_empty_pages(doc, result)
        self._finalize(result)
        self._emit(result)
        return result

    def _check_figure_geometry(self, doc: Any, result: RenderedQAResult) -> None:
        """
        检查交付图形是否落在有效内容区内（P12-CAND-002；SPEC-QA-005 提案）。

        内容区取自文档实际 section 几何（CLAR-02）；仅在几何不可用时退回参考 A4 几何。
        超出内容区为 error（由既有 ``fail_on_error`` 语义决定是否 FAIL），
        低于主题声明最小宽度下限为 warning。

        参数:
            doc: 已打开/已渲染的 python-docx 文档。
            result: RenderedQA 结果（就地写入 metrics / errors / warnings）。
        """
        tolerance_cm = 0.05
        try:
            section = doc.sections[-1]
            content_width_cm = (
                section.page_width.cm - section.left_margin.cm - section.right_margin.cm
            )
            content_height_cm = (
                section.page_height.cm - section.top_margin.cm - section.bottom_margin.cm
            )
        except Exception:
            from .section_manager import PageGeometry

            geometry = PageGeometry()
            margins = getattr(self.theme, "page_margins_cm", None) or {}
            content_width_cm = (
                geometry.portrait_width_cm
                - float(margins.get("left", 2.54))
                - float(margins.get("right", 2.54))
            )
            content_height_cm = (
                geometry.portrait_height_cm
                - float(margins.get("top", 2.54))
                - float(margins.get("bottom", 2.54))
            )

        min_width_cm = figure_policy_from_theme(self.theme).min_width_cm
        overflow = 0
        below_min_width = 0

        for idx, shape in enumerate(doc.inline_shapes):
            try:
                width_cm = shape.width.cm
                height_cm = shape.height.cm
            except Exception:
                continue

            if (
                width_cm > content_width_cm + tolerance_cm
                or height_cm > content_height_cm + tolerance_cm
            ):
                overflow += 1
                if overflow <= 5:
                    result.errors.append(
                        {
                            "code": "figure_overflow",
                            "message": (
                                f"Figure {idx + 1}: {width_cm:.2f}cm x {height_cm:.2f}cm "
                                f"exceeds the content area "
                                f"{content_width_cm:.2f}cm x {content_height_cm:.2f}cm"
                            ),
                        }
                    )

            if min_width_cm is not None and width_cm < min_width_cm - tolerance_cm:
                below_min_width += 1
                if below_min_width <= 5:
                    result.warnings.append(
                        {
                            "code": "figure_below_min_width",
                            "message": (
                                f"Figure {idx + 1}: width {width_cm:.2f}cm is below the "
                                f"theme minimum {min_width_cm:.2f}cm"
                            ),
                        }
                    )

        result.metrics["figure_overflow"] = overflow
        result.metrics["figure_below_min_width"] = below_min_width

    def _check_font_violations(self, doc: Any, result: RenderedQAResult) -> None:
        minimums = (
            self.theme.readability_minimums
            if self.theme and hasattr(self.theme, "readability_minimums")
            else {}
        )
        # 正文最小 10pt、表格 8.5pt、ASCII/代码 8pt。
        # 渲染后无法区分 Run 的内容角色，因此以绝对下限 8pt 作为硬门；
        # 分类型的字号门由 Static QA（渲染前）检查主题配置保证。
        body_min = min(minimums.values()) if minimums else 8.0
        violations = 0
        for paragraph in doc.paragraphs:
            for run in paragraph.runs:
                size = run.font.size
                if size is not None and size.pt < body_min:
                    violations += 1
                    if violations <= 5:
                        result.errors.append(
                            {
                                "code": "font_violation",
                                "message": (
                                    f"Run {run.text[:40]!r} uses {size.pt:.1f}pt "
                                    f"below minimum {body_min}pt"
                                ),
                            }
                        )
        result.metrics["font_violations"] = violations

    def _check_table_overflow(self, doc: Any, result: RenderedQAResult) -> None:
        overflow = 0
        try:
            section = doc.sections[0]
            content_width_cm = (
                section.page_width.cm - section.left_margin.cm - section.right_margin.cm
            )
        except Exception:
            content_width_cm = 16.0
        for idx, table in enumerate(doc.tables):
            # autofit 表格会在 Word 打开时自动收缩到页面宽度，
            # XML 网格列宽之和只是估算，不构成实际溢出。
            if self._table_is_autofit(table):
                continue
            width_cm = 0.0
            try:
                for col in table.columns:
                    if col.width is not None:
                        width_cm += col.width.cm
            except Exception:
                width_cm = 0.0
            if width_cm > 0 and width_cm > content_width_cm + 1.0:
                overflow += 1
                result.warnings.append(
                    {
                        "code": "table_clipping",
                        "message": (
                            f"Table {idx + 1}: estimated width {width_cm:.1f}cm "
                            f"exceeds content width {content_width_cm:.1f}cm"
                        ),
                    }
                )
        result.metrics["table_overflow"] = overflow

    @staticmethod
    def _table_is_autofit(table: Any) -> bool:
        """表格是否为 Word 自动适应页面宽度（autofit）。"""
        from docx.oxml.ns import qn

        tbl_pr = table._tbl.tblPr
        if tbl_pr is None:
            return True
        layout = tbl_pr.find(qn("w:tblLayout"))
        if layout is not None:
            return layout.get(qn("w:type")) != "fixed"
        tbl_w = tbl_pr.find(qn("w:tblW"))
        if tbl_w is not None:
            return tbl_w.get(qn("w:type")) == "auto"
        return True

    def _check_orphan_headings(self, doc: Any, result: RenderedQAResult) -> None:
        orphans = 0
        paragraphs = [p for p in doc.paragraphs if p.text.strip()]
        for i, paragraph in enumerate(paragraphs[:-1]):
            style = paragraph.style.name if paragraph.style else ""
            next_text = paragraphs[i + 1].text.strip() if i + 1 < len(paragraphs) else ""
            if style.startswith("Heading") and not next_text:
                orphans += 1
                result.warnings.append(
                    {
                        "code": "orphan_heading",
                        "message": f"Heading {paragraph.text[:40]!r} has no following content",
                    }
                )
        result.metrics["orphan_headings"] = orphans

    def _check_empty_pages(self, doc: Any, result: RenderedQAResult) -> None:
        empty_pages = 0
        consecutive_breaks = 0
        for paragraph in doc.paragraphs:
            has_page_break = False
            for run in paragraph.runs:
                for break_el in run._element.findall(
                    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}br"
                ):
                    if (
                        break_el.get(
                            "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type"
                        )
                        == "page"
                    ):
                        has_page_break = True
            if has_page_break:
                consecutive_breaks += 1
            else:
                if consecutive_breaks > 1:
                    empty_pages += consecutive_breaks - 1
                consecutive_breaks = 0
        if consecutive_breaks > 1:
            empty_pages += consecutive_breaks - 1
        result.metrics["empty_pages"] = empty_pages

    def _finalize(self, result: RenderedQAResult) -> None:
        result.metrics.setdefault("overflow", 0)
        result.metrics.setdefault("empty_pages", 0)
        result.metrics.setdefault("orphan_headings", 0)
        result.metrics.setdefault("table_overflow", 0)
        result.metrics.setdefault("figure_overflow", 0)
        result.metrics.setdefault("figure_below_min_width", 0)
        result.metrics.setdefault("font_violations", 0)
        if result.errors:
            result.status = "FAIL"
        elif result.warnings:
            result.status = "PASS_WITH_WARN"

    def _emit(self, result: RenderedQAResult) -> None:
        if self.diag is None:
            return
        for issue in result.errors:
            self.diag.error(
                issue["message"],
                code="QA_RENDERED_ERR",
                source="rendered_qa",
                data=issue,
            )
        for issue in result.warnings:
            self.diag.warning(
                issue["message"],
                code="QA_RENDERED_WARN",
                source="rendered_qa",
                data=issue,
            )
