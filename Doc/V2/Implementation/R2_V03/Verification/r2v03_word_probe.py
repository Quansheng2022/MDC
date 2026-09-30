"""R2-V03 native Word layout probe (verification only).

Drives the *already running* desktop Microsoft Word through its COM object
model so the R2-V03 gate can record what Word itself renders: page setup,
pagination, table and figure geometry, TOC fields, typography and headings.

The probe never saves a document, never edits product source, and never changes
any product setting. Documents are opened through Word's normal document-open
path and closed with "do not save".

Subcommands::

    open-and-measure --name <id> --file <docx> --report <dir>
    scroll-to        --name <id> --anchor figure|table|toc|top --report <dir>
    close-all        --report <dir>
    quit-word        --report <dir>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import pythoncom
import win32com.client

__all__ = ["main"]

# Word object-model constants (WdInformation / WdStatistic / view enums).
WD_HORIZONTAL_POSITION_RELATIVE_TO_PAGE = 5
WD_VERTICAL_POSITION_RELATIVE_TO_PAGE = 6
WD_ACTIVE_END_PAGE_NUMBER = 3
WD_ACTIVE_END_VERTICAL_POSITION_RELATIVE_TO_PAGE = 8
WD_FIRST_CHARACTER_COLUMN_NUMBER = 9

WD_STATISTIC_PAGES = 2
WD_STATISTIC_WORDS = 0

WD_PRINT_VIEW = 3
WD_WINDOW_STATE_MAXIMIZE = 1

# Built-in style indexes (locale independent).
WD_STYLE_NORMAL = -1
WD_STYLE_HEADING1 = -2
WD_STYLE_HEADING2 = -3
WD_STYLE_HEADING3 = -4
WD_STYLE_TOC_HEADING = -81

POINTS_PER_CM = 72.0 / 2.54


def cm(points: Any) -> float | None:
    """Return centimetres from Word points (``None`` when unavailable)."""
    try:
        return round(float(points) / POINTS_PER_CM, 4)
    except (TypeError, ValueError):
        return None


def sha256_of(path: Path) -> str:
    """Return the uppercase SHA-256 hex digest of ``path``."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def get_word() -> Any:
    """Return the running Word application, starting it only if necessary."""
    try:
        return win32com.client.GetActiveObject("Word.Application")
    except Exception:  # noqa: BLE001 - no running instance
        return win32com.client.DispatchEx("Word.Application")


def _text_of(com_range: Any) -> str:
    try:
        return str(com_range.Text).replace("\r", "").replace("\x07", "").strip()
    except Exception:  # noqa: BLE001 - defensive
        return ""


def _style_name(item: Any, *, local: bool) -> str:
    """Return a table's style name (localised or the invariant name)."""
    try:
        style = item.Style
        return str(style.NameLocal if local else style.Name)
    except Exception:  # noqa: BLE001 - defensive
        return ""


def measure_document(doc: Any, word: Any) -> Dict[str, Any]:
    """Return the native Word layout measurement of one open document."""
    doc.Repaginate()
    sections: List[Dict[str, Any]] = []
    for index in range(1, doc.Sections.Count + 1):
        setup = doc.Sections(index).PageSetup
        sections.append(
            {
                "index": index,
                "left_margin_cm": cm(setup.LeftMargin),
                "right_margin_cm": cm(setup.RightMargin),
                "top_margin_cm": cm(setup.TopMargin),
                "bottom_margin_cm": cm(setup.BottomMargin),
                "page_width_cm": cm(setup.PageWidth),
                "page_height_cm": cm(setup.PageHeight),
                "orientation": "landscape" if int(setup.Orientation) == 1 else "portrait",
                "text_width_cm": cm(setup.PageWidth - setup.LeftMargin - setup.RightMargin),
                "text_height_cm": cm(setup.PageHeight - setup.TopMargin - setup.BottomMargin),
            }
        )

    tables: List[Dict[str, Any]] = []
    for index in range(1, doc.Tables.Count + 1):
        table = doc.Tables(index)
        widths: List[float] = []
        for column in range(1, table.Columns.Count + 1):
            try:
                widths.append(round(float(table.Columns(column).Width) / POINTS_PER_CM, 4))
            except Exception:  # noqa: BLE001 - merged cells
                widths.append(None)  # type: ignore[arg-type]
        numeric = [value for value in widths if value is not None]
        header = [
            _text_of(table.Cell(1, column).Range)
            for column in range(1, min(table.Columns.Count, 8) + 1)
        ]
        try:
            left = cm(table.Rows(1).Cells(1).Range.Information(WD_HORIZONTAL_POSITION_RELATIVE_TO_PAGE))
        except Exception:  # noqa: BLE001
            left = None
        try:
            top = cm(table.Rows(1).Range.Information(WD_VERTICAL_POSITION_RELATIVE_TO_PAGE))
        except Exception:  # noqa: BLE001
            top = None
        try:
            page = int(table.Rows(1).Range.Information(WD_ACTIVE_END_PAGE_NUMBER))
        except Exception:  # noqa: BLE001
            page = None
        total = round(sum(numeric), 4) if numeric else None
        right_edge = round(left + total, 4) if (left is not None and total is not None) else None
        tables.append(
            {
                "index": index,
                "rows": int(table.Rows.Count),
                "columns": int(table.Columns.Count),
                "rendered_column_widths_cm": widths,
                "rendered_total_width_cm": total,
                "rendered_left_cm": left,
                "rendered_right_edge_cm": right_edge,
                "page": page,
                "top_cm": top,
                "header_cells": header,
                "body_font_size_pt": float(table.Range.Font.Size)
                if not isinstance(table.Range.Font.Size, bool)
                else None,
                "cell_count": int(table.Range.Cells.Count),
                "style_name_local": _style_name(table, local=True),
                "style_name": _style_name(table, local=False),
            }
        )

    shapes: List[Dict[str, Any]] = []
    for index in range(1, doc.InlineShapes.Count + 1):
        shape = doc.InlineShapes(index)
        try:
            left = cm(shape.Range.Information(WD_HORIZONTAL_POSITION_RELATIVE_TO_PAGE))
            top = cm(shape.Range.Information(WD_VERTICAL_POSITION_RELATIVE_TO_PAGE))
            page = int(shape.Range.Information(WD_ACTIVE_END_PAGE_NUMBER))
        except Exception:  # noqa: BLE001
            left = top = page = None
        width_pt, height_pt = float(shape.Width), float(shape.Height)
        shapes.append(
            {
                "index": index,
                "type": int(shape.Type),
                "width_cm": cm(width_pt),
                "height_cm": cm(height_pt),
                "ratio": round(width_pt / height_pt, 4) if height_pt else None,
                "scale_width": float(shape.ScaleWidth),
                "scale_height": float(shape.ScaleHeight),
                "left_cm": left,
                "top_cm": top,
                "right_edge_cm": round(left + width_pt / POINTS_PER_CM, 4)
                if left is not None
                else None,
                "bottom_edge_cm": round(top + height_pt / POINTS_PER_CM, 4)
                if top is not None
                else None,
                "page": page,
                "alternative_text": str(shape.AlternativeText or ""),
            }
        )

    headings: List[Dict[str, Any]] = []
    style_names: Dict[str, int] = {}
    for index in range(1, doc.Paragraphs.Count + 1):
        paragraph = doc.Paragraphs(index)
        try:
            style_name = str(paragraph.Style.NameLocal)
        except Exception:  # noqa: BLE001
            style_name = ""
        style_names[style_name] = style_names.get(style_name, 0) + 1
        try:
            level = int(paragraph.OutlineLevel)
        except Exception:  # noqa: BLE001
            level = 10
        if 1 <= level <= 3:
            text = _text_of(paragraph.Range)
            if text:
                font = paragraph.Range.Font
                headings.append(
                    {
                        "level": level,
                        "text": text,
                        "style": style_name,
                        "font_name": str(font.Name),
                        "font_name_ascii": str(font.NameAscii),
                        "font_name_far_east": str(font.NameFarEast),
                        "size_pt": float(font.Size),
                        "bold": float(font.Bold),
                        "space_before_pt": float(paragraph.SpaceBefore),
                        "space_after_pt": float(paragraph.SpaceAfter),
                        "page": int(
                            paragraph.Range.Information(WD_ACTIVE_END_PAGE_NUMBER)
                        ),
                    }
                )

    toc: Dict[str, Any] = {"count": int(doc.TablesOfContents.Count)}
    if doc.TablesOfContents.Count:
        toc_field = doc.TablesOfContents(1)
        raw = str(toc_field.Range.Text)
        lines = [line.strip() for line in raw.split("\r") if line.strip()]
        toc.update(
            {
                "entries": lines,
                "entry_count": len(lines),
                "use_hyperlinks": bool(toc_field.UseHyperlinks),
                "heading_text_from_body": toc_heading_text(doc),
                "heading_style": _toc_heading_style_summary(doc),
            }
        )

    def style_font(style_index: int) -> Dict[str, Any]:
        try:
            style = doc.Styles(style_index)
            font = style.Font
            paragraph_format = style.ParagraphFormat
            return {
                "name": str(font.Name),
                "name_far_east": str(font.NameFarEast),
                "name_ascii": str(font.NameAscii) if hasattr(font, "NameAscii") else "",
                "size_pt": float(font.Size),
                "bold": float(font.Bold),
                "space_before_pt": float(paragraph_format.SpaceBefore),
                "space_after_pt": float(paragraph_format.SpaceAfter),
                "line_spacing": float(paragraph_format.LineSpacing),
                "line_spacing_rule": int(paragraph_format.LineSpacingRule),
                "alignment": int(paragraph_format.Alignment),
                "keep_with_next": bool(paragraph_format.KeepWithNext),
            }
        except Exception as error:  # noqa: BLE001
            return {"error": f"{type(error).__name__}: {error}"}

    body_paragraphs = []
    for index in range(1, doc.Paragraphs.Count + 1):
        paragraph = doc.Paragraphs(index)
        text = _text_of(paragraph.Range)
        if len(text) > 40:
            body_paragraphs.append(
                {
                    "text_prefix": text[:60],
                    "style": str(paragraph.Style.NameLocal),
                    "font": str(paragraph.Range.Font.Name),
                    "font_far_east": str(paragraph.Range.Font.NameFarEast),
                    "size_pt": float(paragraph.Range.Font.Size),
                    "space_before_pt": float(paragraph.SpaceBefore),
                    "space_after_pt": float(paragraph.SpaceAfter),
                    "line_spacing": float(paragraph.LineSpacing),
                }
            )

    return {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "word_version": str(word.Version),
        "word_build": str(word.Build),
        "document": {
            "name": str(doc.Name),
            "full_name": str(doc.FullName),
            "saved": bool(doc.Saved),
            "read_only": bool(doc.ReadOnly),
            "paragraphs": int(doc.Paragraphs.Count),
            "words": int(doc.ComputeStatistics(WD_STATISTIC_WORDS)),
            "pages": int(doc.ComputeStatistics(WD_STATISTIC_PAGES)),
            "sections": int(doc.Sections.Count),
            "tables": int(doc.Tables.Count),
            "inline_shapes": int(doc.InlineShapes.Count),
            "hyperlinks": int(doc.Hyperlinks.Count),
        },
        "page_setup": sections,
        "tables": tables,
        "figures": shapes,
        "toc": toc,
        "headings": headings,
        "style_names": style_names,
        "styles": {
            "normal": style_font(WD_STYLE_NORMAL),
            "heading1": style_font(WD_STYLE_HEADING1),
            "heading2": style_font(WD_STYLE_HEADING2),
            "heading3": style_font(WD_STYLE_HEADING3),
        },
        "body_paragraph_samples": body_paragraphs[:4],
    }


def find_toc_heading_paragraph(doc: Any) -> Any | None:
    """Return the paragraph that carries the "TOC Heading" style, if present.

    The style name is matched case-insensitively on "toc" + "heading" so the
    lookup still works when Word's user-interface language differs.
    """
    for index in range(1, doc.Paragraphs.Count + 1):
        paragraph = doc.Paragraphs(index)
        try:
            name = str(paragraph.Style.NameLocal)
        except Exception:  # noqa: BLE001
            continue
        lowered = name.lower()
        if "toc" in lowered and "heading" in lowered:
            return paragraph
    return None


def toc_heading_text(doc: Any) -> str:
    """Return the visible text of the TOC heading paragraph."""
    paragraph = find_toc_heading_paragraph(doc)
    if paragraph is None:
        return ""
    return _text_of(paragraph.Range)


def _toc_heading_style_summary(doc: Any) -> Dict[str, Any]:
    """Return font details of the TOC heading paragraph."""
    paragraph = find_toc_heading_paragraph(doc)
    if paragraph is None:
        return {"error": "TOC heading paragraph not found"}
    try:
        font = paragraph.Range.Font
        return {
            "style_name": str(paragraph.Style.NameLocal),
            "font": str(font.Name),
            "font_ascii": str(font.NameAscii),
            "font_far_east": str(font.NameFarEast),
            "size_pt": float(font.Size),
            "bold": float(font.Bold),
            "page": int(paragraph.Range.Information(WD_ACTIVE_END_PAGE_NUMBER)),
        }
    except Exception as error:  # noqa: BLE001
        return {"error": f"{type(error).__name__}: {error}"}


def set_print_layout(doc: Any) -> Dict[str, Any]:
    """Standardise the native Word view: Print Layout, 100% zoom, maximised."""
    window = doc.ActiveWindow
    window.View.Type = WD_PRINT_VIEW
    window.View.Zoom.Percentage = 100
    window.View.ShowFieldCodes = False
    window.WindowState = WD_WINDOW_STATE_MAXIMIZE
    doc.Application.Activate()
    window.Activate()
    return {
        "view_type": int(window.View.Type),
        "zoom_percent": int(window.View.Zoom.Percentage),
        "window_state": int(window.WindowState),
        "caption": str(window.Caption),
    }


def scroll_to(doc: Any, anchor: str) -> Dict[str, Any]:
    """Bring a document anchor into view using Word's own navigation."""
    window = doc.ActiveWindow
    target = None
    label = anchor
    if anchor == "top":
        target = doc.Range(0, 0)
    elif anchor == "toc":
        if doc.TablesOfContents.Count:
            target = doc.TablesOfContents(1).Range
    elif anchor == "figure":
        if doc.InlineShapes.Count:
            target = doc.InlineShapes(1).Range
            label = f"figure-1-of-{int(doc.InlineShapes.Count)}"
    elif anchor == "figure2":
        if doc.InlineShapes.Count >= 2:
            target = doc.InlineShapes(2).Range
            label = f"figure-2-of-{int(doc.InlineShapes.Count)}"
    elif anchor == "table":
        if doc.Tables.Count:
            target = doc.Tables(doc.Tables.Count).Range
            label = f"table-{int(doc.Tables.Count)}"
    elif anchor == "table1":
        if doc.Tables.Count:
            target = doc.Tables(1).Range
            label = "table-1"
    if target is None:
        return {"anchor": anchor, "found": False}
    window.ScrollIntoView(target, True)
    window.View.Zoom.Percentage = 100
    window.Activate()
    return {
        "anchor": anchor,
        "found": True,
        "label": label,
        "page": int(target.Information(WD_ACTIVE_END_PAGE_NUMBER)),
        "vertical_cm": cm(target.Information(WD_VERTICAL_POSITION_RELATIVE_TO_PAGE)),
        "caption": str(window.Caption),
    }


def open_document(word: Any, path: Path) -> Any:
    """Open one document through Word's normal document-open path."""
    return word.Documents.Open(
        FileName=str(path),
        ConfirmConversions=False,
        ReadOnly=False,
        AddToRecentFiles=False,
        Revert=False,
        Visible=True,
        OpenAndRepair=False,
        NoEncodingDialog=True,
    )


def export_pdf(document: Any, pdf_path: Path) -> Dict[str, Any]:
    """Export one document with Word's native print-layout PDF renderer.

    ``ExportAsFixedFormat`` uses Word's own page layout and print renderer, so
    the produced PDF is the document as Word lays it out for printing. The
    caller is responsible for the destination directory.
    """
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    if pdf_path.exists():
        pdf_path.unlink()
    document.ExportAsFixedFormat(
        OutputFileName=str(pdf_path),
        ExportFormat=17,  # wdExportFormatPDF
        OpenAfterExport=False,
        OptimizeFor=0,  # wdExportOptimizeForPrint
        Range=0,  # wdExportAllDocument
        Item=0,  # wdExportDocumentContent
        IncludeDocProps=True,
        KeepIRM=False,
        CreateBookmarks=0,  # wdExportCreateNoBookmarks
        DocStructureTags=True,
        BitmapMissingFonts=True,
        UseISO19005_1=False,
    )
    return {
        "path": str(pdf_path),
        "bytes": pdf_path.stat().st_size,
        "sha256": sha256_of(pdf_path),
    }


def find_open_document(word: Any, path: Path) -> Any | None:
    """Return the already-open document for ``path`` when present."""
    target = str(path).lower()
    for index in range(1, word.Documents.Count + 1):
        document = word.Documents(index)
        if str(document.FullName).lower() == target:
            return document
    return None


def write_report(report_dir: Path, name: str, payload: Dict[str, Any]) -> Path:
    """Write one JSON report document."""
    report_dir.mkdir(parents=True, exist_ok=True)
    safe = name.replace(":", "__").replace("/", "_")
    path = report_dir / f"{safe}.json"
    path.write_text(json.dumps(payload, indent=4, ensure_ascii=False), encoding="utf-8")
    return path


def main() -> int:
    """Execute one probe subcommand."""
    try:  # the acceptance set contains non-ASCII names; never fail on stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001 - older interpreters have no reconfigure
        pass
    parser = argparse.ArgumentParser(description="R2-V03 native Word layout probe")
    parser.add_argument(
        "command",
        choices=("open-and-measure", "scroll-to", "close-all", "quit-word", "pass"),
    )
    parser.add_argument("--name")
    parser.add_argument("--file", type=Path)
    parser.add_argument("--spec", type=Path)
    parser.add_argument("--pdf-dir", type=Path)
    parser.add_argument("--anchor", default="top")
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    pythoncom.CoInitialize()
    word = get_word()
    try:
        if not word.Visible:
            word.Visible = True
    except Exception:  # noqa: BLE001 - a visible window is required to activate
        pass
    result: Dict[str, Any] = {"command": args.command, "pythoncom": "initialised"}

    if args.command == "pass":
        if not args.spec:
            raise SystemExit("--spec is required for the pass command")
        spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
        results: List[Dict[str, Any]] = []
        for item in spec:
            name = str(item["name"])
            path = Path(item["file"])
            anchor = str(item.get("anchor", "top"))
            entry: Dict[str, Any] = {"name": name, "file": str(path), "anchor": anchor}
            try:
                document = find_open_document(word, path)
                entry["reused_open_document"] = document is not None
                if document is None:
                    before = sha256_of(path)
                    document = open_document(word, path)
                    after = sha256_of(path)
                    entry["sha256_before_open"] = before
                    entry["sha256_after_open"] = after
                    entry["artifact_unchanged_by_open"] = before == after
                entry["view"] = set_print_layout(document)
                entry["anchored"] = scroll_to(document, anchor)
                entry["measurement"] = measure_document(document, word)
                if args.pdf_dir:
                    entry["pdf"] = export_pdf(
                        document, args.pdf_dir / f"{path.stem}.pdf"
                    )
                    entry["pdf"]["rendered_pages"] = int(
                        document.ComputeStatistics(WD_STATISTIC_PAGES)
                    )
                entry["ok"] = True
            except Exception as error:  # noqa: BLE001 - record, never abort the pass
                entry["ok"] = False
                entry["error"] = f"{type(error).__name__}: {error}"
            write_report(args.report, name, entry)
            results.append({key: value for key, value in entry.items() if key != "measurement"})
        print(json.dumps({"pass_results": results}, ensure_ascii=False, indent=2))
        return 0

    if args.command == "open-and-measure":
        if not args.name or not args.file:
            raise SystemExit("--name and --file are required")
        before = sha256_of(args.file)
        document = find_open_document(word, args.file)
        reused = document is not None
        if document is None:
            document = open_document(word, args.file)
        view = set_print_layout(document)
        measurement = measure_document(document, word)
        after = sha256_of(args.file)
        result.update(
            {
                "name": args.name,
                "file": str(args.file),
                "reused_open_document": reused,
                "sha256_before_open": before,
                "sha256_after_measure": after,
                "artifact_unchanged_by_word": before == after,
                "view": view,
                "measurement": measurement,
            }
        )
        write_report(args.report, args.name, result)
    elif args.command == "scroll-to":
        if not args.name or not args.file:
            raise SystemExit("--name and --file are required")
        document = find_open_document(word, args.file)
        if document is None:
            raise SystemExit(f"document is not open: {args.file}")
        result.update({"name": args.name, "anchor": scroll_to(document, args.anchor)})
        write_report(args.report, f"{args.name}__anchor-{args.anchor}", result)
    elif args.command == "close-all":
        closed: List[str] = []
        while word.Documents.Count:
            document = word.Documents(1)
            closed.append(str(document.Name))
            document.Close(SaveChanges=0)
        result["closed"] = closed
        write_report(args.report, "close-all", result)
    else:
        names: List[str] = []
        while word.Documents.Count:
            document = word.Documents(1)
            names.append(str(document.Name))
            document.Close(SaveChanges=0)
        result["closed"] = names
        word.Quit(SaveChanges=0)
        result["word_quit"] = True
        write_report(args.report, "quit-word", result)

    print(json.dumps({k: v for k, v in result.items() if k != "measurement"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
