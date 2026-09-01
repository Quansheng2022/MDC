"""
Document Post-Processor - DOCX 文档后处理

在文档生成后，添加封面页、目录更新、表格样式等。
复用 convert_md_docx10.py 中的成熟逻辑，适配新架构。
"""

import platform
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from docx import Document
    from docx.enum.style import WD_STYLE_TYPE
    from docx.enum.text import (
        WD_ALIGN_PARAGRAPH,
        WD_BREAK,
        WD_TAB_ALIGNMENT,
        WD_TAB_LEADER,
    )
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Pt, RGBColor
    from docx.text.paragraph import Paragraph

    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import win32com.client

    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

from .word_writer import set_run_font, set_style_font


class DocxPostProcessor:
    """
    DOCX 文档后处理器。

    功能：
        1. 在文档开头插入封面页（标题、日期、标签）
        2. 为所有表格添加边框和表头样式
        3. 更新目录（TOC）并在 TOC 后插入分页（使用 Word COM）
    """

    @classmethod
    def process(
        cls,
        docx_path: Path,
        metadata: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        执行完整的后处理流程。

        参数:
            docx_path: DOCX 文件路径
            metadata: Frontmatter 元数据（包含 title, date, tags 等）
        config: 配置字典（可控制是否启用封面、TOC 等）
        """
        # C2 说明：此处的 .get(..., True) 是低层 API 的 backward-compatible
        # fallback（本类可被独立调用），不是 Canonical configuration authority。
        # 唯一默认值来源是 config.DEFAULT_CONFIG（经 resolve_config 注入）。
        if not DOCX_AVAILABLE:
            print("  ⚠️ python-docx 未安装，跳过后处理")
            return

        if metadata is None:
            metadata = {}
        if config is None:
            config = {}

        docx_path = Path(docx_path)
        if not docx_path.exists():
            print(f"  ⚠️ 文件不存在: {docx_path}")
            return

        # 1. 插入封面页
        if config.get("enable_cover", True):
            cls._insert_cover_page(docx_path, metadata)

        # 2. 重新加载文档（封面页插入后需要重新加载）
        doc = Document(str(docx_path))

        # 3. 设置表格样式
        if config.get("style_tables", True):
            cls._style_tables(doc)

        # 4. 原生插入 TOC（域代码 + 分页符），不依赖 win32com
        if config.get("toc", True):
            cls._insert_toc_native(doc)

        # 5. 保存文档
        doc.save(str(docx_path))

        # 6. win32com 可用时用 Word 刷新 TOC 页码（增强，可通过 word_com=False 关闭）
        if config.get("toc", True):
            if WIN32_AVAILABLE and platform.system() == "Windows" and config.get("word_com", True):
                cls._update_toc_with_word(docx_path)
            else:
                print("  📄 TOC 已插入（含目录条目；页码可在 Word 中按 F9 刷新）")

    # ============================================================
    # 封面页插入
    # ============================================================

    @classmethod
    def _insert_cover_page(cls, docx_path: Path, metadata: Dict[str, Any]) -> None:
        """
        在文档开头插入封面页（标题、日期、标签）。
        """
        doc = Document(str(docx_path))

        # 提取元数据
        title = str(metadata.get("title", Path(docx_path).stem))
        date = metadata.get("date", "")
        if hasattr(date, "isoformat"):
            date = date.isoformat()
        else:
            date = str(date)

        tags = metadata.get("tags", [])
        if isinstance(tags, list):
            tags_str = ", ".join(str(t) for t in tags if t)
        elif tags:
            tags_str = str(tags)
        else:
            tags_str = ""

        # 构建封面页段落列表
        cover_paragraphs = []
        preferred_fonts = ["Microsoft YaHei", "Aptos Display", "Arial"]

        # 标题
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(title)
        run.font.size = Pt(28)
        run.font.bold = True
        for font_name in preferred_fonts:
            try:
                run.font.name = font_name
                break
            except Exception:
                continue
        cover_paragraphs.append(p)

        # 日期
        if date:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(date)
            run.font.size = Pt(16)
            for font_name in preferred_fonts:
                try:
                    run.font.name = font_name
                    break
                except Exception:
                    continue
            cover_paragraphs.append(p)

        # Tags
        if tags_str:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(tags_str)
            run.font.size = Pt(14)
            run.font.italic = True
            for font_name in preferred_fonts:
                try:
                    run.font.name = font_name
                    break
                except Exception:
                    continue
            cover_paragraphs.append(p)

        # 分页（封面页和正文之间）
        p = doc.add_paragraph()
        run = p.add_run()
        run.add_break(WD_BREAK.PAGE)
        cover_paragraphs.append(p)

        # 将封面页段落移动到文档开头
        cover_elements = [p._element for p in cover_paragraphs]
        body = doc._body._element
        first_para = doc.paragraphs[0] if doc.paragraphs else None

        if first_para:
            for elem in reversed(cover_elements):
                body.insert(0, elem)
        else:
            for elem in cover_elements:
                body.append(elem)

        doc.save(str(docx_path))

    # ============================================================
    # 表格样式
    # ============================================================

    @classmethod
    def _style_tables(cls, doc: Document) -> None:
        """
        为所有表格添加边框和表头样式。
        """
        if not doc.tables:
            return

        print(f"  📊 处理 {len(doc.tables)} 个表格...")
        success = 0
        for idx, table in enumerate(doc.tables):
            try:
                cls._add_table_borders(table)
                cls._set_table_header_style(table)
                success += 1
            except Exception as e:
                print(f"    处理表格 {idx+1} 时出错: {e}")
        print(f"  ✓ 格式化 {success}/{len(doc.tables)} 个表格")

    @staticmethod
    def _add_table_borders(table) -> None:
        """
        为表格添加边框。

        异常直接向上传播，由 _style_tables 统一记录（SPEC-INV-006：
        禁止静默吞掉异常，保证“格式化 X/Y”计数真实可信）。
        """
        tbl = table._tbl
        tblPr = tbl.tblPr
        if tblPr is None:
            tblPr = OxmlElement("w:tblPr")
            tbl.insert(0, tblPr)

        # 移除现有边框
        for border in tblPr.findall(qn("w:tblBorders")):
            tblPr.remove(border)

        # 添加新边框
        borders = OxmlElement("w:tblBorders")
        border_props = {
            "top": ("single", "4", "auto"),
            "left": ("single", "4", "auto"),
            "bottom": ("single", "4", "auto"),
            "right": ("single", "4", "auto"),
            "insideH": ("single", "4", "auto"),
            "insideV": ("single", "4", "auto"),
        }
        for name, (style, size, color) in border_props.items():
            border = OxmlElement(f"w:{name}")
            border.set(qn("w:val"), style)
            border.set(qn("w:sz"), size)
            border.set(qn("w:space"), "0")
            border.set(qn("w:color"), color)
            borders.append(border)

        tblPr.append(borders)

    @staticmethod
    def _set_table_header_style(table) -> None:
        """
        设置表头样式（第一行背景色、白色加粗文字）。

        异常直接向上传播，由 _style_tables 统一记录（SPEC-INV-006）。
        """
        if not table.rows:
            return
        header_row = table.rows[0]
        for cell in header_row.cells:
            tcPr = cell._tc.get_or_add_tcPr()
            shd = OxmlElement("w:shd")
            shd.set(qn("w:val"), "clear")
            shd.set(qn("w:color"), "auto")
            shd.set(qn("w:fill"), "2F5496")  # 深蓝色背景
            tcPr.append(shd)

            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.color.rgb = RGBColor(255, 255, 255)
                    run.font.bold = True
                # 如果段落没有 run，创建新的 run
                if not paragraph.runs and paragraph.text:
                    run = paragraph.add_run(paragraph.text)
                    run.font.color.rgb = RGBColor(255, 255, 255)
                    run.font.bold = True

    # ============================================================
    # TOC 插入（原生域代码，不依赖 Word COM）
    # ============================================================

    @classmethod
    def _insert_toc_native(cls, doc: Document) -> None:
        """
        原生插入 Word TOC 域（不依赖 win32com）。

        在封面分页符之后插入“目录”标题、TOC 域代码、目录条目与分页符。
        TOC 域的缓存结果会写入真实的标题条目（超链接到标题书签），
        因此打开文档即可看到目录。

        注意：域起始标记不带 w:dirty，且 settings.xml 不写入 updateFields，
        避免 Word 打开文档时弹出“更新域”对话框；页码由 Word 按 F9 更新，
        或在 win32com 可用时由 _update_toc_with_word 在保存前刷新。
        """
        # 收集 Heading 1-3 标题（需在插入目录段落前完成）
        headings = cls._collect_headings(doc, max_level=3)

        # 定位封面页后的分页符段落（无封面时回退到文档开头）
        anchor = None
        for para in doc.paragraphs:
            if cls._paragraph_contains_page_break(para):
                anchor = para._element
                break

        # 目录标题
        title_p = doc.add_paragraph()
        title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        try:
            title_p.style = doc.styles["TOC Heading"]
        except Exception:
            pass
        title_run = title_p.add_run("目录")
        title_run.font.bold = True
        title_run.font.size = Pt(18)
        set_run_font(title_run, font_name="Microsoft YaHei", east_asia="Microsoft YaHei")

        # TOC 域：TOC \o "1-3" \h \z \u
        toc_p = doc.add_paragraph()
        cls._append_field_char(toc_p, "begin")
        instr_run = toc_p.add_run()
        instr = OxmlElement("w:instrText")
        instr.set(qn("xml:space"), "preserve")
        instr.text = ' TOC \\o "1-3" \\h \\z \\u '
        instr_run._element.append(instr)
        cls._append_field_char(toc_p, "separate")

        # 确保 TOC 1..3 段落样式存在（模板默认只有 TOC Heading）
        cls._ensure_toc_styles(doc)

        # 为标题添加书签，并生成真实目录条目（TOC 域缓存结果）
        bookmark_id = cls._next_bookmark_id(doc)
        entry_paragraphs: List[Paragraph] = []
        for para, level, text in headings:
            bookmark_name = f"_Toc_{bookmark_id}"
            cls._add_bookmark(para, bookmark_id, bookmark_name)
            bookmark_id += 1
            entry_paragraphs.append(cls._append_toc_entry(doc, level, text, bookmark_name))

        if entry_paragraphs:
            # 域结束标记放在最后一个条目的段落末尾
            cls._append_field_char(entry_paragraphs[-1], "end")
        else:
            placeholder_run = toc_p.add_run("（文档暂无标题，目录为空）")
            placeholder_run.font.size = Pt(10.5)
            set_run_font(placeholder_run, font_name="Microsoft YaHei", east_asia="Microsoft YaHei")
            cls._append_field_char(toc_p, "end")

        # TOC 后的分页符
        break_p = doc.add_paragraph()
        break_run = break_p.add_run()
        break_run.add_break(WD_BREAK.PAGE)

        # 将标题、域、条目与分页符移动到锚点之后（保持顺序）
        body = doc._body._element
        elements = (
            [title_p._element, toc_p._element]
            + [entry._element for entry in entry_paragraphs]
            + [break_p._element]
        )
        if anchor is not None:
            current = anchor
            for elem in elements:
                current.addnext(elem)
                current = elem
        else:
            first_para = doc.paragraphs[0]._element if doc.paragraphs else None
            if first_para is not None:
                for elem in elements:
                    first_para.addprevious(elem)
            else:
                for elem in elements:
                    body.append(elem)

    @staticmethod
    def _collect_headings(
        doc: Document,
        max_level: int = 3,
    ) -> List[Tuple[Paragraph, int, str]]:
        """
        收集文档中 Heading 1..max_level 样式的段落。

        参数:
            doc: python-docx 文档对象
            max_level: 最大标题级别（默认 3，与 TOC \\o "1-3" 一致）

        返回:
            List[Tuple[Paragraph, int, str]]: (段落, 级别, 标题纯文本)
        """
        headings: List[Tuple[Paragraph, int, str]] = []
        for para in doc.paragraphs:
            style = para.style
            style_name = style.name if style is not None else ""
            match = re.match(r"^Heading ([1-6])$", style_name)
            if not match:
                continue
            level = int(match.group(1))
            if level > max_level:
                continue
            text = para.text.strip()
            if text:
                headings.append((para, level, text))
        return headings

    @staticmethod
    def _next_bookmark_id(doc: Document) -> int:
        """返回文档中可用的下一个书签 ID（现有最大 ID + 1）。"""
        max_id = 0
        for bm in doc._element.iter(qn("w:bookmarkStart")):
            try:
                max_id = max(max_id, int(bm.get(qn("w:id")) or 0))
            except (TypeError, ValueError):
                continue
        return max_id + 1

    @staticmethod
    def _add_bookmark(paragraph: Paragraph, bookmark_id: int, name: str) -> None:
        """
        为段落添加书签（bookmarkStart/End 包裹段落内容）。

        参数:
            paragraph: 目标段落
            bookmark_id: 书签 ID（文档内唯一）
            name: 书签名称（Word 要求唯一且不以数字开头）
        """
        p_el = paragraph._element
        start = OxmlElement("w:bookmarkStart")
        start.set(qn("w:id"), str(bookmark_id))
        start.set(qn("w:name"), name)
        end = OxmlElement("w:bookmarkEnd")
        end.set(qn("w:id"), str(bookmark_id))

        first_run = p_el.find(qn("w:r"))
        if first_run is not None:
            first_run.addprevious(start)
        else:
            p_pr = p_el.find(qn("w:pPr"))
            if p_pr is not None:
                p_pr.addnext(start)
            else:
                p_el.insert(0, start)
        p_el.append(end)

    @classmethod
    def _append_toc_entry(
        cls,
        doc: Document,
        level: int,
        text: str,
        bookmark_name: str,
    ) -> Paragraph:
        """
        追加一个 TOC 条目段落（超链接到标题书签）。

        条目文本放在 w:hyperlink 内，点击即可跳转到对应标题；
        页码留待 Word 按 F9 更新（或 win32com 在保存前刷新）时生成。
        """
        entry = doc.add_paragraph()
        try:
            entry.style = doc.styles[f"TOC {level}"]
        except Exception:
            try:
                entry.style = doc.styles["Normal"]
            except Exception:
                pass
            entry.paragraph_format.left_indent = Pt((level - 1) * 18)
            entry.paragraph_format.space_before = Pt(0)
            entry.paragraph_format.space_after = Pt(2)

        hyperlink = OxmlElement("w:hyperlink")
        hyperlink.set(qn("w:anchor"), bookmark_name)
        run = OxmlElement("w:r")
        run_text = OxmlElement("w:t")
        run_text.set(qn("xml:space"), "preserve")
        run_text.text = text
        run.append(run_text)
        hyperlink.append(run)
        entry._element.append(hyperlink)

        # 右侧点线制表位（页码位置），与 Word 内置 TOC 样式一致；
        # 页码由 Word 按 F9 更新后填充
        try:
            section = doc.sections[0]
            tab_pos = section.page_width - section.left_margin - section.right_margin
            entry.paragraph_format.tab_stops.add_tab_stop(
                tab_pos, WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS
            )
        except Exception:
            pass
        tab_run = entry.add_run()
        tab_run.add_tab()
        return entry

    @staticmethod
    def _ensure_toc_styles(doc: Document) -> None:
        """
        确保 TOC 1..3 段落样式存在（python-docx 默认模板只有 TOC Heading）。

        缺失时创建样式，统一字体（东亚 Microsoft YaHei）与缩进，保证目录观感。
        """
        existing = {style.name for style in doc.styles}
        for level in range(1, 4):
            style_name = f"TOC {level}"
            if style_name in existing:
                continue
            try:
                style = doc.styles.add_style(style_name, WD_STYLE_TYPE.PARAGRAPH)
                style.base_style = doc.styles["Normal"]
                style.font.size = Pt(max(10.5 - (level - 1) * 0.5, 9))
                set_style_font(style, font_name="Microsoft YaHei", east_asia="Microsoft YaHei")
                style.paragraph_format.left_indent = Pt((level - 1) * 18)
                style.paragraph_format.space_before = Pt(0)
                style.paragraph_format.space_after = Pt(2)
                style.paragraph_format.keep_with_next = True
            except Exception:
                continue

    @staticmethod
    def _append_field_char(
        paragraph: Paragraph,
        fld_char_type: str,
        dirty: bool = False,
    ) -> None:
        """向段落追加 w:fldChar 元素（begin/separate/end）。"""
        run = paragraph.add_run()
        fld_char = OxmlElement("w:fldChar")
        fld_char.set(qn("w:fldCharType"), fld_char_type)
        if dirty:
            fld_char.set(qn("w:dirty"), "true")
        run._element.append(fld_char)

    @staticmethod
    def _paragraph_contains_page_break(paragraph: Paragraph) -> bool:
        """判断段落是否包含分页符（w:br w:type='page'）。"""
        for br in paragraph._element.iter(qn("w:br")):
            if br.get(qn("w:type")) == "page":
                return True
        return False

    # ============================================================
    # TOC 更新（使用 Word COM）
    # ============================================================

    @staticmethod
    def _update_toc_with_word(docx_path: Path) -> None:
        """
        使用 Word COM 刷新已存在的 TOC（页码与条目由 Word 计算）。

        TOC 域与分页符已由 _insert_toc_native 原生插入；
        此方法仅在 win32com 可用时刷新域结果，使页码在保存时即正确。
        """
        if not WIN32_AVAILABLE:
            print("  ⚠️ win32com 不可用，无法更新 TOC")
            return

        max_retries = 3
        for attempt in range(max_retries):
            # WP-COM-02/07: 每次 retry 都从完全干净的 COM object state 开始，
            # 不允许 attempt #1 的 proxy 泄漏到 attempt #2
            word = None
            doc = None
            toc = None
            paragraph = None
            style = None
            try:
                abs_path = str(docx_path.resolve())
                print(f"  📄 正在打开: {abs_path} (尝试 {attempt + 1}/{max_retries})")

                # 使用独立实例，避免复用用户已打开的 Word 导致文件锁冲突
                word = win32com.client.DispatchEx("Word.Application")
                word.Visible = False
                word.DisplayAlerts = 0
                doc = word.Documents.Open(abs_path, False, False, False)

                # 刷新已存在的 TOC（域已由 _insert_toc_native 原生插入）
                toc_count = doc.TablesOfContents.Count
                if toc_count == 0:
                    print("  ⚠️ 未找到 TOC 域，跳过 Word 刷新")
                    return
                for i in range(1, toc_count + 1):
                    try:
                        toc = doc.TablesOfContents(i)
                        toc.Update()
                    finally:
                        # WP-COM-03: TOC proxy 生命周期 = 单次 update 操作
                        toc = None
                print(f"  ✓ 刷新了 {toc_count} 个 TOC")

                # 更新所有字段
                doc.Fields.Update()

                # ✅ 设置 TOC 标题居中，字体优先使用 Microsoft YaHei
                preferred_fonts = ["Microsoft YaHei", "Aptos Display", "Arial"]

                toc_title_found = False
                for paragraph in doc.Paragraphs:
                    style_name = paragraph.Style.NameLocal if paragraph.Style else ""
                    if style_name in ("TOC Heading", "目录标题", "TOC 标题"):
                        paragraph.Alignment = 1
                        paragraph.Range.Font.Bold = True
                        paragraph.Range.Font.Size = 18
                        for font_name in preferred_fonts:
                            try:
                                paragraph.Range.Font.Name = font_name
                                break
                            except Exception:
                                continue
                        toc_title_found = True
                        # WP-COM-04: break 前释放 paragraph proxy
                        paragraph = None
                        break
                # WP-COM-04: 循环正常结束路径也释放 paragraph proxy
                paragraph = None

                if not toc_title_found:
                    for paragraph in doc.Paragraphs:
                        text = paragraph.Range.Text.strip()
                        if text in ("目录", "Table of Contents", "TOC"):
                            paragraph.Alignment = 1
                            paragraph.Range.Font.Bold = True
                            paragraph.Range.Font.Size = 18
                            for font_name in preferred_fonts:
                                try:
                                    paragraph.Range.Font.Name = font_name
                                    break
                                except Exception:
                                    continue
                            toc_title_found = True
                            paragraph = None
                            break
                    paragraph = None

                # ✅ 设置 TOC 条目字体（所有级别）
                for i in range(1, 10):
                    style_name = f"TOC {i}"
                    try:
                        style = doc.Styles(style_name)
                        if style:
                            for font_name in preferred_fonts:
                                try:
                                    style.Font.Name = font_name
                                    break
                                except Exception:
                                    continue
                    except Exception:
                        pass
                    finally:
                        # WP-COM-05: 每个 style proxy 仅在当前 iteration 有效
                        style = None

                doc.Save()
                print("  ✓ TOC 页码已刷新（Word）")
                return

            except Exception as e:
                print(f"  ⚠️ 尝试 {attempt + 1} 失败: {e}")
                if attempt < max_retries - 1:
                    print("  ⏳ 等待 1 秒后重试...")
                    time.sleep(1)
                else:
                    print(f"  ✗ 所有重试均失败: {e}")
            finally:
                # WP-COM-06: 释放顺序 child proxies -> document -> application

                # 1. Child COM proxies（先于 Document / Application 释放）
                toc = None
                paragraph = None
                style = None

                # 2. Document
                try:
                    if doc is not None:
                        doc.Close(False)
                except Exception:
                    pass
                finally:
                    doc = None

                # 3. Word Application
                try:
                    if word is not None:
                        word.Quit()
                except Exception:
                    pass
                finally:
                    word = None
