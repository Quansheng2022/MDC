"""R2-V03 native Word render checks.

Reads the PDFs that desktop Microsoft Word produced from the accepted R2-V02
artifacts (``Document.ExportAsFixedFormat``, i.e. Word's own print-layout
renderer) and checks page-level rendering facts that a reader would otherwise
judge by eye:

* every page's text and figures stay inside the page and inside the page's
  usable text body (nothing clipped off the page or spilling into the margin);
* figure aspect ratio on the rendered page matches the intrinsic image, so the
  figure is neither stretched nor cropped;
* declared figures actually appear on the rendered pages (no missing image);
* TOC heading and entries are rendered on the page;
* table cell content is present in the rendered output.

The checks are measurements, not taste judgements. Output is one JSON document.

Usage::

    python r2v03_pdf_render_check.py --index <index.json> --pdf-dir <dir> \
        --out <matrix.json> [--png-dir <dir>]
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import zipfile
from pathlib import Path
from typing import Any, Dict, List

import pdfplumber

__all__ = ["main"]

PT_PER_CM = 72.0 / 2.54
#: Glyph side bearings and table borders can sit a hair outside the text body.
TOLERANCE_CM = 0.3


def normalise(text: str) -> str:
    """Return a comparison form of ``text`` (no whitespace, lower case)."""
    return re.sub(r"\s+", "", text).lower()


#: Matches a literal ``w:t`` element only (never ``w:instrText`` field codes).
W_T_ELEMENT = re.compile(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>", flags=re.S)


def docx_visible_characters(docx_path: Path) -> collections.Counter:
    """Return the character multiset of the document's visible text runs.

    Only ``w:t`` text is read, so TOC/PAGEREF field instructions (stored in
    ``w:instrText``) are excluded exactly as Word excludes them from the page.
    Mid-word table wrapping re-flows characters without dropping them, so a
    character multiset is a loss-free integrity check for rendered output.
    """
    with zipfile.ZipFile(docx_path) as archive:
        xml = archive.read("word/document.xml").decode("utf-8", "replace")
    text = []
    for chunk in W_T_ELEMENT.findall(xml):
        text.append(re.sub(r"<[^>]+>", "", chunk))
    return collections.Counter(
        character
        for character in "".join(text)
        if not character.isspace()
    )


def pdf_visible_characters(pdf: Any) -> collections.Counter:
    """Return the character multiset Word's rendered pages actually contain."""
    characters = []
    for page in pdf.pages:
        for char in page.chars:
            value = char.get("text") or ""
            if not value.isspace():
                characters.append(value)
    return collections.Counter("".join(characters))


def check_page(page: Any, margins: Dict[str, float]) -> Dict[str, Any]:
    """Return the render measurements and body-containment check for one page."""
    width = float(page.width)
    height = float(page.height)
    words = page.extract_words(use_text_flow=False, keep_blank_chars=False)
    images = page.images

    text_boxes = [
        {"x0": float(w["x0"]), "x1": float(w["x1"]), "top": float(w["top"]), "bottom": float(w["bottom"]), "text": w["text"]}
        for w in words
    ]
    image_boxes = []
    for image in images:
        rendered_ratio = round(float(image["width"]) / float(image["height"]), 4)
        intrinsic = image.get("srcsize") or (None, None)
        intrinsic_ratio = (
            round(float(intrinsic[0]) / float(intrinsic[1]), 4)
            if intrinsic and intrinsic[0] and intrinsic[1]
            else None
        )
        image_boxes.append(
            {
                "x0": round(float(image["x0"]), 3),
                "x1": round(float(image["x1"]), 3),
                "top": round(float(image["top"]), 3),
                "bottom": round(float(image["bottom"]), 3),
                "width_pt": round(float(image["width"]), 3),
                "height_pt": round(float(image["height"]), 3),
                "srcsize": list(intrinsic) if intrinsic else None,
                "rendered_ratio": rendered_ratio,
                "intrinsic_ratio": intrinsic_ratio,
                "ratio_delta_percent": round(
                    100.0 * abs(rendered_ratio - intrinsic_ratio) / intrinsic_ratio, 3
                )
                if intrinsic_ratio
                else None,
            }
        )

    xs0 = [box["x0"] for box in text_boxes] + [box["x0"] for box in image_boxes]
    xs1 = [box["x1"] for box in text_boxes] + [box["x1"] for box in image_boxes]
    tops = [box["top"] for box in text_boxes] + [box["top"] for box in image_boxes]
    bottoms = [box["bottom"] for box in text_boxes] + [box["bottom"] for box in image_boxes]

    body = {
        "left_pt": margins["left_cm"] * PT_PER_CM,
        "right_pt": width - margins["right_cm"] * PT_PER_CM,
        "top_pt": margins["top_cm"] * PT_PER_CM,
        "bottom_pt": height - margins["bottom_cm"] * PT_PER_CM,
    }
    tolerance = TOLERANCE_CM * PT_PER_CM
    overflow = {
        "left_pt": round(body["left_pt"] - min(xs0), 3) if xs0 else 0.0,
        "right_pt": round(max(xs1) - body["right_pt"], 3) if xs1 else 0.0,
        "top_pt": round(body["top_pt"] - min(tops), 3) if tops else 0.0,
        "bottom_pt": round(max(bottoms) - body["bottom_pt"], 3) if bottoms else 0.0,
    }
    within_body = all(value <= tolerance for value in overflow.values())
    within_page = (
        (not xs0 or (min(xs0) >= -1.0 and max(xs1) <= width + 1.0))
        and (not tops or (min(tops) >= -1.0 and max(bottoms) <= height + 1.0))
    )
    return {
        "page_width_pt": round(width, 3),
        "page_height_pt": round(height, 3),
        "page_width_cm": round(width / PT_PER_CM, 3),
        "page_height_cm": round(height / PT_PER_CM, 3),
        "word_count": len(words),
        "text_box_count": len(text_boxes),
        "content_bbox_pt": {
            "x0": round(min(xs0), 3) if xs0 else None,
            "x1": round(max(xs1), 3) if xs1 else None,
            "top": round(min(tops), 3) if tops else None,
            "bottom": round(max(bottoms), 3) if bottoms else None,
        },
        "text_body_pt": {key: round(value, 3) for key, value in body.items()},
        "body_overflow_pt": overflow,
        "content_within_text_body": within_body,
        "content_within_page": within_page,
        "images": image_boxes,
        "image_count": len(image_boxes),
        "text_sample": " ".join(w["text"] for w in words[:40]),
    }


def main() -> int:
    """Render-check every exported PDF and write one matrix JSON."""
    parser = argparse.ArgumentParser(description="R2-V03 native Word render checks")
    parser.add_argument("--index", required=True, type=Path)
    parser.add_argument("--pdf-dir", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    index = json.loads(args.index.read_text(encoding="utf-8"))
    artifacts: List[Dict[str, Any]] = []
    failures: List[str] = []

    for item in index["items"]:
        name = item["name"]
        structure = item.get("structure") or {}
        sections = structure.get("sections") or []
        primary = sections[-1] if len(sections) > 1 else (sections[0] if sections else None)
        if primary is None:
            failures.append(f"{item['role']}: no section geometry in the index")
            continue
        margins = {
            "left_cm": primary["left_cm"],
            "right_cm": primary["right_cm"],
            "top_cm": primary["top_cm"],
            "bottom_cm": primary["bottom_cm"],
        }
        declared_figures = structure.get("figures", {}).get("inline_shapes", [])

        pdf_path = args.pdf_dir / f"{Path(name).stem}.pdf"
        if not pdf_path.is_file():
            failures.append(f"{item['role']}: missing exported PDF {pdf_path}")
            continue

        pages: List[Dict[str, Any]] = []
        char_check: Dict[str, Any] = {}
        with pdfplumber.open(str(pdf_path)) as pdf:
            for number, page in enumerate(pdf.pages, start=1):
                measured = check_page(page, margins)
                measured["page"] = number
                pages.append(measured)
            docx_chars = docx_visible_characters(Path(item["acceptance_path"]))
            pdf_chars = pdf_visible_characters(pdf)
            dropped = docx_chars - pdf_chars
            extra = pdf_chars - docx_chars
            char_check = {
                "docx_visible_chars": sum(docx_chars.values()),
                "rendered_chars": sum(pdf_chars.values()),
                "dropped_characters": dict(dropped),
                "dropped_character_count": sum(dropped.values()),
                "extra_characters": dict(extra),
                "extra_character_count": sum(extra.values()),
                "content_lossless": sum(dropped.values()) == 0,
            }

        toc_heading = (structure.get("toc") or {}).get("heading") or ""
        toc_entries = [
            entry
            for entry in ((structure.get("toc") or {}).get("entries") or [])
            if entry
        ]
        full_page_texts = []
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page in pdf.pages:
                full_page_texts.append(normalise(page.extract_text() or ""))

        declared_table_headers = [
            table
            for table in structure.get("tables", [])
            if table.get("columns", 0) >= 8
        ]
        header_expectations: List[Dict[str, Any]] = []
        for table in declared_table_headers:
            headers = [cell for cell in table.get("header_cells", []) if cell]
            present = [header for header in headers if normalise(header) in "".join(full_page_texts)]
            header_expectations.append(
                {
                    "columns": table["columns"],
                    "header_count": len(headers),
                    "headers_present": len(present),
                    "missing_headers": [h for h in headers if h not in present],
                }
            )

        images_total = sum(page["image_count"] for page in pages)
        ratios = [
            image
            for page in pages
            for image in page["images"]
        ]
        combined_page_text = "".join(full_page_texts)
        artifacts.append(
            {
                "role": item["role"],
                "name": name,
                "pdf_path": str(pdf_path),
                "pdf_pages": len(pages),
                "declared_margins_cm": margins,
                "declared_figure_count": len(declared_figures),
                "rendered_image_count": images_total,
                "character_integrity": char_check,
                "images": ratios,
                "toc_heading_expected": toc_heading,
                "toc_heading_rendered": bool(toc_heading)
                and normalise(toc_heading) in "".join(full_page_texts),
                "toc_entries_expected": len(toc_entries),
                "toc_entries_rendered": sum(
                    1 for entry in toc_entries if normalise(entry) in "".join(full_page_texts)
                ),
                "wide_table_headers": header_expectations,
                "pages": [
                    {k: v for k, v in page.items() if k != "text_sample"} for page in pages
                ],
                "pages_with_content_outside_body": [
                    page["page"] for page in pages if not page["content_within_text_body"]
                ],
                "pages_with_content_outside_page": [
                    page["page"] for page in pages if not page["content_within_page"]
                ],
            }
        )

    matrix = {
        "program": "R2-V03",
        "work_package": "R2V03-02",
        "method": (
            "Native Microsoft Word print-layout rendering exported to PDF "
            "(Document.ExportAsFixedFormat) and measured page by page."
        ),
        "tolerance_cm": TOLERANCE_CM,
        "artifact_count": len(artifacts),
        "failures": failures,
        "artifacts": artifacts,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(matrix, indent=4, ensure_ascii=False), encoding="utf-8"
    )
    print(f"artifacts={len(artifacts)} failures={len(failures)}")
    print(f"out={args.out}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
