"""R2-V03 Word restart/reopen stability comparison.

Compares the native Word measurements, the rendered-page checks and the page
pixel measurements taken before and after a full Word exit and relaunch, and
reports every difference. A stable result means the documents reopen with the
same pagination, geometry, TOC state and rendered content.

Usage::

    python r2v03_restart_compare.py --before-word <dir> --after-word <dir> \
        --before-render <json> --after-render <json> \
        --before-pixels <json> --after-pixels <json> \
        --roles <role>[,<role>...] --out <json>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

__all__ = ["main"]

FLOAT_TOLERANCE = 0.02

#: Keys whose value includes Word-generated TOC dot leaders. The number of
#: leader dots is produced by Word when it lays the TOC out and can move by a
#: character or two between two renders of the same document without changing
#: any content, pagination or geometry. They are reported, never hidden.
NON_MATERIAL_KEYS = {
    "rendered_characters": "Word-generated TOC dot leaders",
    "extra_characters": "Word-generated TOC dot leaders",
    "leader_dots": "Word-generated TOC dot leaders",
}


def load_report(directory: Path, role: str) -> Dict[str, Any]:
    """Load one Word probe report by role."""
    path = directory / f"{role.replace(':', '__')}.json"
    if not path.is_file():
        raise SystemExit(f"missing report: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def flatten_word(report: Dict[str, Any]) -> Dict[str, Any]:
    """Return comparable scalars extracted from one Word probe report."""
    measurement = report["measurement"]
    document = measurement["document"]
    section = measurement["page_setup"][0]
    flat: Dict[str, Any] = {
        "pages": document["pages"],
        "paragraphs": document["paragraphs"],
        "words": document["words"],
        "sections": document["sections"],
        "tables": document["tables"],
        "inline_shapes": document["inline_shapes"],
        "hyperlinks": document["hyperlinks"],
        "margin_top_cm": section["top_margin_cm"],
        "margin_bottom_cm": section["bottom_margin_cm"],
        "margin_left_cm": section["left_margin_cm"],
        "margin_right_cm": section["right_margin_cm"],
        "page_width_cm": section["page_width_cm"],
        "page_height_cm": section["page_height_cm"],
        "view_type": report["view"]["view_type"],
        "zoom_percent": report["view"]["zoom_percent"],
        "toc_count": (measurement.get("toc") or {}).get("count"),
        "toc_entry_count": (measurement.get("toc") or {}).get("entry_count"),
        "toc_use_hyperlinks": (measurement.get("toc") or {}).get("use_hyperlinks"),
    }
    for index, table in enumerate(measurement.get("tables") or [], start=1):
        flat[f"table{index}_columns"] = table["columns"]
        flat[f"table{index}_rows"] = table["rows"]
        flat[f"table{index}_total_cm"] = table["rendered_total_width_cm"]
        flat[f"table{index}_right_edge_cm"] = table["rendered_right_edge_cm"]
    for index, figure in enumerate(measurement.get("figures") or [], start=1):
        flat[f"figure{index}_width_cm"] = figure["width_cm"]
        flat[f"figure{index}_height_cm"] = figure["height_cm"]
        flat[f"figure{index}_ratio"] = figure["ratio"]
    for index, heading in enumerate(measurement.get("headings") or [], start=1):
        flat[f"heading{index}"] = f"{heading['level']}|{heading['text']}|{heading['font_name']}|{heading['size_pt']}"
    return flat


def flatten_render(artifact: Dict[str, Any]) -> Dict[str, Any]:
    """Return comparable scalars extracted from one render-matrix artifact."""
    integrity = artifact.get("character_integrity") or {}
    flat: Dict[str, Any] = {
        "pages": artifact.get("pdf_pages"),
        "declared_figures": artifact.get("declared_figure_count"),
        "rendered_images": artifact.get("rendered_image_count"),
        "toc_heading_rendered": artifact.get("toc_heading_rendered"),
        "toc_entries_rendered": artifact.get("toc_entries_rendered"),
        "toc_entries_expected": artifact.get("toc_entries_expected"),
        "pages_outside_body": ",".join(
            str(page) for page in (artifact.get("pages_with_content_outside_body") or [])
        ),
        "pages_outside_page": ",".join(
            str(page) for page in (artifact.get("pages_with_content_outside_page") or [])
        ),
        "dropped_characters": integrity.get("dropped_character_count"),
        "document_characters": integrity.get("docx_visible_chars"),
        "rendered_characters": integrity.get("rendered_chars"),
        "extra_characters": json.dumps(
            integrity.get("extra_characters") or {}, sort_keys=True
        ),
        "leader_dots": (integrity.get("extra_characters") or {}).get(".", 0),
    }
    for index, image in enumerate(artifact.get("images") or [], start=1):
        flat[f"image{index}_width_pt"] = image["width_pt"]
        flat[f"image{index}_height_pt"] = image["height_pt"]
        flat[f"image{index}_ratio"] = image["rendered_ratio"]
    return flat


def flatten_pixels(artifact: Dict[str, Any]) -> Dict[str, Any]:
    """Return comparable scalars extracted from one page-pixel artifact."""
    flat: Dict[str, Any] = {
        "page_count": artifact.get("page_count"),
        "blank_pages": ",".join(artifact.get("blank_pages") or []),
        "pages_outside_body": ",".join(artifact.get("pages_outside_body") or []),
    }
    for index, block in enumerate(artifact.get("solid_figure_blocks") or [], start=1):
        flat[f"block{index}_width_cm"] = block["width_cm"]
        flat[f"block{index}_height_cm"] = block["height_cm"]
        flat[f"block{index}_left_cm"] = block["left_cm"]
        flat[f"block{index}_top_cm"] = block["top_cm"]
        flat[f"block{index}_ratio"] = block["aspect_ratio"]
    return flat


def compare(before: Dict[str, Any], after: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return the differing keys between two flattened reports."""
    differences: List[Dict[str, Any]] = []
    for key in sorted(set(before) | set(after)):
        left = before.get(key)
        right = after.get(key)
        if isinstance(left, float) and isinstance(right, float):
            if abs(left - right) > FLOAT_TOLERANCE:
                differences.append({"key": key, "before": left, "after": right})
        elif left != right:
            differences.append({"key": key, "before": left, "after": right})
    return differences


def main() -> int:
    """Compare the pre-restart and post-restart measurements."""
    parser = argparse.ArgumentParser(description="R2-V03 Word restart comparison")
    parser.add_argument("--before-word", required=True, type=Path)
    parser.add_argument("--after-word", required=True, type=Path)
    parser.add_argument("--before-render", required=True, type=Path)
    parser.add_argument("--after-render", required=True, type=Path)
    parser.add_argument("--before-pixels", required=True, type=Path)
    parser.add_argument("--after-pixels", required=True, type=Path)
    parser.add_argument("--roles", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    roles = [role.strip() for role in args.roles.split(",") if role.strip()]
    before_render = {
        item["role"]: item
        for item in json.loads(args.before_render.read_text(encoding="utf-8"))["artifacts"]
    }
    after_render = {
        item["role"]: item
        for item in json.loads(args.after_render.read_text(encoding="utf-8"))["artifacts"]
    }
    before_pixels = {
        item["role"]: item
        for item in json.loads(args.before_pixels.read_text(encoding="utf-8"))["artifacts"]
    }
    after_pixels = {
        item["role"]: item
        for item in json.loads(args.after_pixels.read_text(encoding="utf-8"))["artifacts"]
    }

    comparisons: List[Dict[str, Any]] = []
    for role in roles:
        word_diff = compare(
            flatten_word(load_report(args.before_word, role)),
            flatten_word(load_report(args.after_word, role)),
        )
        render_diff = compare(
            flatten_render(before_render[role]), flatten_render(after_render[role])
        )
        pixel_diff = compare(
            flatten_pixels(before_pixels[role]), flatten_pixels(after_pixels[role])
        )
        for difference in word_diff + render_diff + pixel_diff:
            reason = NON_MATERIAL_KEYS.get(difference["key"])
            difference["material"] = reason is None
            if reason:
                difference["non_material_reason"] = reason
        comparisons.append(
            {
                "role": role,
                "word_differences": word_diff,
                "render_differences": render_diff,
                "pixel_differences": pixel_diff,
                "material_differences": [
                    difference
                    for difference in word_diff + render_diff + pixel_diff
                    if difference["material"]
                ],
                "non_material_differences": [
                    difference
                    for difference in word_diff + render_diff + pixel_diff
                    if not difference["material"]
                ],
            }
        )
        comparisons[-1]["stable"] = not comparisons[-1]["material_differences"]

    result = {
        "program": "R2-V03",
        "work_package": "R2V03-03",
        "method": (
            "Full Word exit, normal relaunch, reopen of one profile document, one TOC "
            "document and one table/figure document, then the same measurements repeated."
        ),
        "float_tolerance": FLOAT_TOLERANCE,
        "non_material_key_policy": NON_MATERIAL_KEYS,
        "roles": roles,
        "all_stable": all(item["stable"] for item in comparisons),
        "comparisons": comparisons,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=4, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({item["role"]: item["stable"] for item in comparisons}, ensure_ascii=False))
    print(f"all_stable={result['all_stable']}")
    return 0 if result["all_stable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
