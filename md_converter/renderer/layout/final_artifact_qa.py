"""
Final Artifact QA - 最终产物质量检查（P0-08）

在 Post-Processor 之后对**最终发布文件**执行 QA，保证
“测试对象 == 发布对象”。

检查项:
    - artifact_sha256: 最终文件 hash（Final QA 检查对象即发布对象）
    - artifact_opens: 文件可被 python-docx 打开
    - body_not_empty: 正文非空
    - heading_structure: 标题结构保留
    - table_structure: 表格结构有效
    - font_minimums / clipping / empty_pages: 复用 RenderedQA
    - expected_cover: 封面页存在（ArtifactContract.cover_required，缺失=ERROR）
    - expected_toc: TOC 域存在（ArtifactContract.toc_required，缺失=ERROR）
    - table_styling: 表格样式化生效（ArtifactContract.table_styling_required，
      存在表格时缺失=ERROR）
    - content_loss: 源语义内容 token 覆盖率 == 1.0
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ...diagnostics.collector import DiagnosticCollector
from .artifact_contract import ArtifactContract
from .rendered_qa import RenderedQA
from .themes_v15_protocol import ThemeProtocol


@dataclass
class FinalArtifactQAResult:
    """Final Artifact QA 报告。"""

    status: str = "PASS"  # PASS | PASS_WITH_WARN | FAIL
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "errors": self.errors,
            "warnings": self.warnings,
            "metrics": self.metrics,
        }


_CJK_CHAR_RE = re.compile(r"[\u4e00-\u9fff]")
_LATIN_TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_./:%@#$&?=+\-]{1,}")


def extract_tokens(text: str) -> List[str]:
    """
    提取用于内容保全检查的 token。

    规则:
        - CJK 单字逐一作为 token
        - 拉丁/数字 token 长度 >= 2
        - URL、小数、百分比等原子序列保持完整
    """
    tokens: List[str] = []
    for token in _LATIN_TOKEN_RE.findall(text):
        if len(token) >= 2:
            tokens.append(token)
    tokens.extend(_CJK_CHAR_RE.findall(text))
    return tokens


class FinalArtifactQA:
    """
    最终产物 QA。

    用法:
        qa = FinalArtifactQA(theme, diag)
        result = qa.run(docx_path, source_text=..., metadata=..., config=...)
    """

    def __init__(
        self,
        theme: Optional[ThemeProtocol] = None,
        diag: Optional[DiagnosticCollector] = None,
    ):
        self.theme = theme
        self.diag = diag

    def run(
        self,
        docx_path: Any,
        layout_plan: Any = None,
        source_text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
        contract: Optional[ArtifactContract] = None,
        expected_headings: Optional[List[str]] = None,
    ) -> FinalArtifactQAResult:
        """
        对最终发布文件执行 QA。

        参数:
            docx_path: 最终 DOCX 文件路径（QA 对象 == 发布对象）
            layout_plan: LayoutPlan（用于结构核对，可选）
            source_text: 源语义纯文本（用于 No Content Loss，可选）
            metadata: Frontmatter 元数据（封面检查）
            config: 编译器配置（封面 / TOC 开关）
            contract: ArtifactContract；缺省时由 config 推导
            expected_headings: 期望出现的标题文本列表

        返回:
            FinalArtifactQAResult: 检查报告
        """
        result = FinalArtifactQAResult()
        cfg = config or {}
        meta = metadata or {}
        if contract is None:
            contract = ArtifactContract.from_config(cfg)

        # 0. artifact hash（QA 检查对象 == 发布对象）
        result.metrics["artifact_sha256"] = self._file_sha256(docx_path)

        # 1. 文件可打开
        try:
            from docx import Document

            doc = Document(str(docx_path))
        except Exception as e:
            result.errors.append(
                {
                    "code": "artifact_unreadable",
                    "message": f"Final artifact cannot be opened: {e}",
                }
            )
            self._finalize(result)
            self._emit(result)
            return result

        paragraphs = doc.paragraphs
        tables = doc.tables
        doc_text = self._collect_doc_text(doc)
        result.metrics["paragraphs"] = len(paragraphs)
        result.metrics["tables"] = len(tables)
        result.metrics["inline_shapes"] = len(doc.inline_shapes)

        # 2. 正文非空
        body_text = "".join(p.text for p in paragraphs).strip()
        if not body_text and not tables:
            result.errors.append(
                {
                    "code": "body_empty",
                    "message": "Final artifact body is empty",
                }
            )

        # 3. 标题结构保留
        heading_paragraphs = [
            p for p in paragraphs if p.style is not None and p.style.name.startswith("Heading")
        ]
        heading_texts = [p.text.strip() for p in heading_paragraphs if p.text.strip()]
        result.metrics["headings"] = len(heading_texts)
        for expected in expected_headings or []:
            expected_stripped = expected.strip()
            if expected_stripped and not any(expected_stripped in text for text in heading_texts):
                result.errors.append(
                    {
                        "code": "heading_lost",
                        "message": (
                            f"Heading text not retained in final artifact: "
                            f"{expected_stripped!r}"
                        ),
                    }
                )

        # 4. 表格结构有效
        for idx, table in enumerate(tables):
            if not table.rows:
                result.warnings.append(
                    {
                        "code": "table_empty",
                        "message": f"Table {idx + 1} has no rows in final artifact",
                    }
                )
                continue
            widths = {len(row.cells) for row in table.rows}
            if len(widths) > 1:
                result.warnings.append(
                    {
                        "code": "table_inconsistent_columns",
                        "message": (
                            f"Table {idx + 1} has inconsistent column counts: {sorted(widths)}"
                        ),
                    }
                )

        # 5. 字体 / 裁剪 / 空页（复用 RenderedQA 检查逻辑）
        rendered = RenderedQA(theme=self.theme, diag=None).run(doc, layout_plan)
        result.errors.extend(rendered.errors)
        result.warnings.extend(rendered.warnings)
        for key, value in rendered.metrics.items():
            result.metrics[f"rendered_{key}"] = value

        # 6. 期望封面（required -> ERROR；未要求 -> 不检查）
        if contract.cover_required:
            title = meta.get("title")
            if title:
                non_empty = [p.text.strip() for p in paragraphs if p.text.strip()]
                if not any(str(title) in text for text in non_empty[:8]):
                    result.errors.append(
                        {
                            "code": "cover_missing",
                            "message": (
                                "Required cover title not found in the beginning " "of the document"
                            ),
                        }
                    )

        # 7. 期望 TOC（required -> ERROR；未要求 -> 不检查）
        if contract.toc_required:
            if not self._has_toc_field(doc):
                result.errors.append(
                    {
                        "code": "toc_missing",
                        "message": "Required TOC field not found in final artifact",
                    }
                )

        # 7b. 表格样式化验收（style_tables=True 且存在表格时必须生效）
        self._check_table_styling(doc, result, contract)

        # 8. No Content Loss（语义 token 覆盖率）
        if source_text:
            coverage = self._content_coverage(source_text, doc_text)
            result.metrics["content_coverage"] = coverage["coverage"]
            result.metrics["missing_tokens"] = coverage["missing"][:20]
            if coverage["coverage"] < 1.0:
                result.errors.append(
                    {
                        "code": "content_loss",
                        "message": (
                            f"Content loss detected: {coverage['missing_total']} semantic "
                            f"token(s) missing from final artifact "
                            f"(coverage {coverage['coverage']:.3f})"
                        ),
                        "data": {"missing": coverage["missing"][:20]},
                    }
                )

        self._finalize(result)
        self._emit(result)
        return result

    # ============================================================
    # 内部工具
    # ============================================================

    @staticmethod
    def _file_sha256(docx_path: Any) -> str:
        """计算文件 sha256；文件不可读时返回空字符串。"""
        try:
            with open(str(docx_path), "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except OSError:
            return ""

    @staticmethod
    def _collect_doc_text(doc: Any) -> str:
        """收集段落与表格单元格的全部文本。"""
        parts = [p.text for p in doc.paragraphs]
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    parts.append(cell.text)
        return "\n".join(parts)

    @staticmethod
    def _has_toc_field(doc: Any) -> bool:
        """检查文档是否包含 TOC 域代码（w:instrText 包含 TOC）。"""
        try:
            from docx.oxml.ns import qn

            for instr in doc.element.iter(qn("w:instrText")):
                if instr.text and "TOC" in instr.text.upper():
                    return True
        except Exception:
            return False
        return False

    def _check_table_styling(
        self,
        doc: Any,
        result: FinalArtifactQAResult,
        contract: ArtifactContract,
    ) -> None:
        """
        验收 style_tables 是否真正生效。

        规则（Required capability + Applicable content exists -> 必须验证）:
            - 表格样式名应包含 Grid（Table Grid 体系）
            - 表头行存在
            - 有效边框存在（direct w:tblBorders 或 Table Style 继承；
              Word COM 保存时可能规范化移除冗余 direct 边框节点，
              但边框仍由 Table Grid 等样式继承）
        """
        if not contract.table_styling_required or not doc.tables:
            return

        for idx, table in enumerate(doc.tables):
            style_name = table.style.name if table.style is not None else ""
            has_borders = self._has_effective_table_borders(table)
            has_header = bool(table.rows)

            issues = []
            if not style_name or "Grid" not in style_name:
                issues.append("table_style_missing")
            if not has_header:
                issues.append("header_row_missing")
            if not has_borders:
                issues.append("table_borders_missing")
            if issues:
                result.errors.append(
                    {
                        "code": "table_styling_missing",
                        "message": (
                            f"Table {idx + 1} missing required styling: {', '.join(issues)}"
                        ),
                    }
                )

    @staticmethod
    def _border_set_is_visible(border_set: Any) -> bool:
        """
        判断一组边框节点是否构成完整可见边框。

        返回 True 当且仅当 top / left / bottom / right / insideH / insideV
        全部存在且 w:val 为可见值（非空、非 none、非 nil）。
        """
        if border_set is None:
            return False

        from docx.oxml.ns import qn

        required_edges = ("top", "left", "bottom", "right", "insideH", "insideV")
        for edge_name in required_edges:
            edge = border_set.find(qn(f"w:{edge_name}"))
            if edge is None:
                return False
            value = (edge.get(qn("w:val")) or "").lower()
            if value in {"", "none", "nil"}:
                return False
        return True

    @classmethod
    def _has_effective_table_borders(cls, table: Any) -> bool:
        """
        解析表格的 effective borders。

        Word COM 保存时可能规范化冗余 direct formatting：document.xml 中的
        直接 w:tblBorders 可能被移除，但边框仍由 Table Style（如 Table Grid）
        继承。因此分别检查 direct 与 style（含 base_style 链）两处来源。
        """
        from docx.oxml.ns import qn

        # 1. Direct table formatting
        try:
            tbl_pr = table._tbl.tblPr
            if tbl_pr is not None:
                direct_borders = tbl_pr.find(qn("w:tblBorders"))
                if cls._border_set_is_visible(direct_borders):
                    return True
        except Exception:
            pass

        # 2. Table style / inherited style chain
        try:
            style = table.style
            visited = set()
            while style is not None:
                style_id = getattr(style, "style_id", None)
                if style_id in visited:
                    break
                if style_id is not None:
                    visited.add(style_id)

                style_element = style._element
                style_tbl_pr = style_element.find(qn("w:tblPr"))
                if style_tbl_pr is not None:
                    style_borders = style_tbl_pr.find(qn("w:tblBorders"))
                    if cls._border_set_is_visible(style_borders):
                        return True
                style = style.base_style
        except Exception:
            pass

        return False

    @staticmethod
    def _content_coverage(source_text: str, doc_text: str) -> Dict[str, Any]:
        """计算源语义 token 在最终文档文本中的覆盖率。"""
        tokens = extract_tokens(source_text)
        if not tokens:
            return {"coverage": 1.0, "missing": [], "missing_total": 0}
        missing: List[str] = []
        for token in tokens:
            if token not in doc_text:
                missing.append(token)
        total = len(tokens)
        found = total - len(missing)
        return {
            "coverage": round(found / total, 4),
            "missing": missing,
            "missing_total": len(missing),
        }

    def _finalize(self, result: FinalArtifactQAResult) -> None:
        """根据 errors/warnings 汇总状态。"""
        if result.errors:
            result.status = "FAIL"
        elif result.warnings:
            result.status = "PASS_WITH_WARN"

    def _emit(self, result: FinalArtifactQAResult) -> None:
        """将 QA 结果写入诊断收集器。"""
        if self.diag is None:
            return
        for issue in result.errors:
            self.diag.error(
                issue["message"],
                code="QA_FINAL_ERR",
                source="final_artifact_qa",
                data=issue,
            )
        for issue in result.warnings:
            self.diag.warning(
                issue["message"],
                code="QA_FINAL_WARN",
                source="final_artifact_qa",
                data=issue,
            )
