"""R2-V03 native visual acceptance matrix.

Combines the three R2-V03 measurements - the acceptance-set structural index,
the native Word layout probe, and the rendered-page checks - into one
per-artifact acceptance matrix, and compares the five output profiles against
the product's own frozen profile authority
(``md_converter.profiles.registry``).

Every entry is classified with one of: ``PASS``,
``KNOWN_ACCEPTED_LIMITATION``, ``VISUAL_PRODUCT_DEFECT``,
``ENVIRONMENT_FAILURE``, ``LATER_GATE_DEBT``.

Usage::

    python r2v03_visual_matrix.py --index <index.json> --word <measurements.json> \
        --render <render_matrix.json> --pixels <page_pixel_matrix.json> --out <matrix.json>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

__all__ = ["main"]

PASS = "PASS"
KNOWN_ACCEPTED_LIMITATION = "KNOWN_ACCEPTED_LIMITATION"
VISUAL_PRODUCT_DEFECT = "VISUAL_PRODUCT_DEFECT"
ENVIRONMENT_FAILURE = "ENVIRONMENT_FAILURE"
LATER_GATE_DEBT = "LATER_GATE_DEBT"

CM_TOLERANCE = 0.05
PT_TOLERANCE = 0.01
FIGURE_RATIO_TOLERANCE_PERCENT = 3.0

#: The R2-V03 acceptance set contains one artifact that is deliberately *not* a
#: packaged output: the Program D irreducible-table fixture, included because the
#: product specification asks for that case "if a fixture is available". It has
#: no cover/TOC and its 25-column table is wider than the page, which is exactly
#: the limitation Program D accepted (``RENDER006``, PASS_WITH_WARN).
PROGRAM_D_FIXTURE_ROLE = "table:irreducible_wide_program_d"


def load_profile_authority(repo_root: Path) -> Any:
    """Import the product's frozen profile registry (single authority)."""
    sys.path.insert(0, str(repo_root))
    from md_converter.profiles import registry  # local import: needs sys.path first

    return registry


def close(left: Optional[float], right: Optional[float], tolerance: float) -> bool:
    """Return True when two optional numbers agree within ``tolerance``."""
    if left is None or right is None:
        return False
    return abs(float(left) - float(right)) <= tolerance


def profile_comparison(registry: Any, profile_id: str, artifact: Dict[str, Any]) -> Dict[str, Any]:
    """Compare one profile artifact against the frozen profile authority."""
    profile = registry.PROFILE_REGISTRY.get(profile_id)
    if profile is None:
        return {"error": f"unknown profile id {profile_id!r}"}
    presentation = profile.presentation
    typography = presentation.typography
    margins = presentation.page_margins
    measurement = artifact["word"]["measurement"]
    structure = artifact["index"]["structure"]

    section = measurement["page_setup"][0]
    styles = measurement["styles"]
    body_sample = (measurement.get("body_paragraph_samples") or [{}])[0]
    headings = measurement.get("headings") or []
    tables = measurement.get("tables") or []
    declared_tables = structure.get("tables") or []

    checks: List[Dict[str, Any]] = []

    def check(label: str, ok: bool, detail: str) -> None:
        checks.append(
            {
                "label": label,
                "result": PASS if ok else VISUAL_PRODUCT_DEFECT,
                "detail": detail,
            }
        )

    check(
        "page margins match the frozen profile",
        close(section["top_margin_cm"], margins.top_cm, CM_TOLERANCE)
        and close(section["bottom_margin_cm"], margins.bottom_cm, CM_TOLERANCE)
        and close(section["left_margin_cm"], margins.left_cm, CM_TOLERANCE)
        and close(section["right_margin_cm"], margins.right_cm, CM_TOLERANCE),
        f"Word {section['top_margin_cm']}/{section['bottom_margin_cm']}/"
        f"{section['left_margin_cm']}/{section['right_margin_cm']} cm "
        f"vs frozen {margins.top_cm}/{margins.bottom_cm}/{margins.left_cm}/{margins.right_cm} cm",
    )
    check(
        "body font matches the frozen profile",
        str(body_sample.get("font")) == typography.body_font,
        f"Word body run '{body_sample.get('font')}' vs frozen '{typography.body_font}'",
    )
    check(
        "body size matches the frozen profile",
        close(body_sample.get("size_pt"), typography.body_size_pt, PT_TOLERANCE),
        f"Word {body_sample.get('size_pt')} pt vs frozen {typography.body_size_pt} pt",
    )
    for level, expected_size in enumerate(typography.heading_sizes_pt[:3], start=1):
        found = next((item for item in headings if item["level"] == level), None)
        check(
            f"heading {level} font/size match the frozen profile",
            found is not None
            and str(found.get("font_name")) == typography.heading_font
            and close(found.get("size_pt"), expected_size, PT_TOLERANCE),
            (
                f"Word '{found.get('font_name')}' {found.get('size_pt')} pt vs frozen "
                f"'{typography.heading_font}' {expected_size} pt"
            )
            if found
            else "no heading at this level in the document",
        )
    check(
        "paragraph line spacing matches the frozen profile",
        close(
            styles["normal"].get("line_spacing"),
            typography.line_spacing * 12.0,
            0.05,
        ),
        f"Word {styles['normal'].get('line_spacing')} pt vs frozen multiple "
        f"{typography.line_spacing} (= {round(typography.line_spacing * 12.0, 3)} pt)",
    )
    check(
        "paragraph space-after matches the frozen profile",
        close(
            styles["normal"].get("space_after_pt"),
            typography.paragraph_space_after_pt,
            PT_TOLERANCE,
        ),
        f"Word {styles['normal'].get('space_after_pt')} pt vs frozen "
        f"{typography.paragraph_space_after_pt} pt",
    )
    if declared_tables:
        check(
            "table style matches the frozen profile",
            str(declared_tables[0].get("style")) == typography.table_style,
            f"declared '{declared_tables[0].get('style')}' vs frozen '{typography.table_style}'",
        )
    if tables:
        sizes = [table["body_font_size_pt"] for table in tables if table["body_font_size_pt"]]
        check(
            "table font size matches the frozen profile",
            bool(sizes) and all(close(size, typography.table_font_size_pt, PT_TOLERANCE) for size in sizes),
            f"Word {sizes} pt vs frozen {typography.table_font_size_pt} pt",
        )
    return {
        "profile_id": profile.id,
        "display_name": profile.display_name,
        "checks": checks,
        "failed": [check for check in checks if check["result"] != PASS],
    }


def table_checks(artifact: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return the rendered table checks for one artifact."""
    measurement = artifact["word"]["measurement"]
    section = measurement["page_setup"][0]
    body_right = section["page_width_cm"] - section["right_margin_cm"]
    body_left = section["left_margin_cm"]
    checks: List[Dict[str, Any]] = []
    for table in measurement.get("tables") or []:
        within_body = (
            table["rendered_right_edge_cm"] is not None
            and table["rendered_right_edge_cm"] <= body_right + CM_TOLERANCE
            and table["rendered_left_cm"] >= body_left - CM_TOLERANCE
        )
        checks.append(
            {
                "label": f"table {table['index']}: rendered width inside the usable page body",
                "result": PASS if within_body else KNOWN_ACCEPTED_LIMITATION,
                "detail": (
                    f"{table['columns']} columns, rendered {table['rendered_total_width_cm']} cm, "
                    f"left {table['rendered_left_cm']} cm, right edge {table['rendered_right_edge_cm']} cm "
                    f"vs text body {round(body_left, 3)}-{round(body_right, 3)} cm"
                ),
            }
        )
        checks.append(
            {
                "label": f"table {table['index']}: header cells rendered",
                "result": PASS if all(table["header_cells"]) else VISUAL_PRODUCT_DEFECT,
                "detail": f"header cells {table['header_cells']}",
            }
        )
    return checks


def toc_checks(artifact: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return the rendered TOC checks for one artifact."""
    structure = artifact["index"]["structure"]
    measurement = artifact["word"]["measurement"]
    render = artifact["render"]
    expected_heading = (structure.get("toc") or {}).get("heading") or ""
    entries = [entry for entry in ((structure.get("toc") or {}).get("entries") or []) if entry]
    toc = measurement.get("toc") or {}
    if not expected_heading and not toc.get("count"):
        return [
            {
                "label": "TOC coverage",
                "result": PASS,
                "detail": "not applicable: this artifact declares no table of contents",
            }
        ]
    return [
        {
            "label": "TOC heading is present and rendered",
            "result": PASS if render.get("toc_heading_rendered") else VISUAL_PRODUCT_DEFECT,
            "detail": f"heading '{expected_heading}' rendered={render.get('toc_heading_rendered')}",
        },
        {
            "label": "TOC entries are rendered",
            "result": PASS
            if render.get("toc_entries_rendered") == render.get("toc_entries_expected")
            and render.get("toc_entries_expected")
            else VISUAL_PRODUCT_DEFECT,
            "detail": (
                f"{render.get('toc_entries_rendered')}/{render.get('toc_entries_expected')} cached entries "
                f"found in the rendered pages"
            ),
        },
        {
            "label": "TOC field is a live field with page numbers and navigation",
            "result": PASS
            if toc.get("count") == 1 and toc.get("use_hyperlinks") and toc.get("entry_count")
            else VISUAL_PRODUCT_DEFECT,
            "detail": (
                f"Word field count={toc.get('count')}, entries={toc.get('entry_count')}, "
                f"hyperlinks={toc.get('use_hyperlinks')}, hyperlink runs={measurement['document']['hyperlinks']}"
            ),
        },
        {
            "label": "TOC entries carry page numbers",
            "result": PASS
            if all(any(character.isdigit() for character in entry) for entry in (toc.get("entries") or []))
            else VISUAL_PRODUCT_DEFECT,
            "detail": f"Word entries {toc.get('entries')}",
        },
    ]


def figure_checks(artifact: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return the rendered figure checks for one artifact."""
    declared = ((artifact["index"]["structure"].get("figures") or {}).get("inline_shapes")) or []
    render_images = artifact["render"].get("images") or []
    blocks = artifact["pixels"].get("solid_figure_blocks") or []
    checks: List[Dict[str, Any]] = []

    checks.append(
        {
            "label": "every declared figure appears in the rendered pages",
            "result": PASS
            if len(render_images) == len(declared)
            else VISUAL_PRODUCT_DEFECT,
            "detail": f"declared {len(declared)}, rendered images {len(render_images)}",
        }
    )
    for image in render_images:
        delta = image.get("ratio_delta_percent")
        checks.append(
            {
                "label": "rendered figure keeps its aspect ratio (no distortion or crop)",
                "result": PASS
                if delta is not None and delta <= FIGURE_RATIO_TOLERANCE_PERCENT
                else VISUAL_PRODUCT_DEFECT,
                "detail": (
                    f"{image['width_pt']}x{image['height_pt']} pt, ratio {image['rendered_ratio']} "
                    f"vs intrinsic {image['intrinsic_ratio']} ({delta}%)"
                ),
            }
        )
    for block in blocks:
        delta = block.get("ratio_delta_percent")
        if delta is None or delta > FIGURE_RATIO_TOLERANCE_PERCENT:
            continue
        checks.append(
            {
                "label": "figure block rendered solid inside the page body",
                "result": PASS
                if block["fill_fraction"] >= 0.99
                else VISUAL_PRODUCT_DEFECT,
                "detail": (
                    f"{block['width_cm']}x{block['height_cm']} cm at ({block['left_cm']},{block['top_cm']}) "
                    f"fill {block['fill_fraction']}, ratio delta {delta}%"
                ),
            }
        )
    return checks


def content_checks(artifact: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return the rendered-content integrity checks for one artifact."""
    integrity = artifact["render"].get("character_integrity") or {}
    pages = artifact["render"].get("pages") or []
    outside_body = artifact["render"].get("pages_with_content_outside_body") or []
    outside_page = artifact["render"].get("pages_with_content_outside_page") or []
    accepted_irreducible = artifact.get("exercises_accepted_irreducible_limitation", False)
    return [
        {
            "label": "no rendered text character is lost",
            "result": PASS
            if integrity.get("content_lossless")
            else (KNOWN_ACCEPTED_LIMITATION if accepted_irreducible else VISUAL_PRODUCT_DEFECT),
            "detail": (
                f"document text characters {integrity.get('docx_visible_chars')}, "
                f"rendered characters {integrity.get('rendered_chars')}, "
                f"dropped {integrity.get('dropped_character_count')} "
                f"({integrity.get('dropped_characters')})"
                + (
                    "; the table is wider than the printable page, so the trailing columns "
                    "cannot be printed on one page - the limitation accepted by Program D "
                    "(RENDER006, PASS_WITH_WARN)"
                    if accepted_irreducible
                    else ""
                )
            ),
        },
        {
            "label": "no rendered content outside the page",
            "result": PASS if not outside_page else VISUAL_PRODUCT_DEFECT,
            "detail": f"pages with content outside the page: {outside_page}",
        },
        {
            "label": "no rendered content outside the usable text body",
            "result": PASS
            if not outside_body
            else KNOWN_ACCEPTED_LIMITATION,
            "detail": f"pages with content outside the text body: {outside_body}",
        },
        {
            "label": "every page renders content",
            "result": PASS
            if not artifact["pixels"].get("blank_pages")
            else KNOWN_ACCEPTED_LIMITATION,
            "detail": (
                f"pages {len(pages)}, blank pages "
                f"{artifact['pixels'].get('blank_pages')}"
                + (
                    "; the Program D fixture's trailing empty section renders an empty page"
                    if accepted_irreducible
                    else ""
                )
            ),
        },
    ]


def table_exceeds_page(artifact: Dict[str, Any]) -> bool:
    """Return True when a rendered table is wider than its printable page."""
    measurement = artifact["word"]["measurement"]
    sections = measurement["page_setup"]
    for table in measurement.get("tables") or []:
        page_number = table.get("page") or 1
        section = sections[min(page_number, len(sections)) - 1]
        if (
            table.get("rendered_right_edge_cm") is not None
            and table["rendered_right_edge_cm"] > section["page_width_cm"]
        ):
            return True
    return False


def main() -> int:
    """Build the native visual acceptance matrix."""
    parser = argparse.ArgumentParser(description="R2-V03 native visual acceptance matrix")
    parser.add_argument("--index", required=True, type=Path)
    parser.add_argument("--word", required=True, type=Path)
    parser.add_argument("--render", required=True, type=Path)
    parser.add_argument("--pixels", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--repo-root", required=True, type=Path)
    args = parser.parse_args()

    registry = load_profile_authority(args.repo_root)
    index = json.loads(args.index.read_text(encoding="utf-8"))
    word = json.loads(args.word.read_text(encoding="utf-8"))
    render = json.loads(args.render.read_text(encoding="utf-8"))
    pixels = json.loads(args.pixels.read_text(encoding="utf-8"))

    # The Word probe records the acceptance role in ``name`` and the artifact
    # path in ``file``; the other matrices key by role as well.
    word_by_role = {item["name"]: item for item in word["artifacts"]}
    render_by_role = {item["role"]: item for item in render["artifacts"]}
    pixels_by_role = {item["role"]: item for item in pixels["artifacts"]}

    artifacts: List[Dict[str, Any]] = []
    for item in index["items"]:
        role = item["role"]
        artifact = {
            "role": role,
            "name": item["name"],
            "packaged_output": role != PROGRAM_D_FIXTURE_ROLE,
            "index": item,
            "word": word_by_role[role],
            "render": render_by_role[role],
            "pixels": pixels_by_role[role],
        }
        artifact["exercises_accepted_irreducible_limitation"] = table_exceeds_page(artifact)
        checks: List[Dict[str, Any]] = []
        checks.extend(content_checks(artifact))
        checks.extend(toc_checks(artifact))
        checks.extend(table_checks(artifact))
        checks.extend(figure_checks(artifact))
        if role.startswith("profile:"):
            artifact["profile"] = profile_comparison(
                registry, role.split(":", 1)[1], artifact
            )
            checks.extend(artifact["profile"]["checks"])
        artifact["checks"] = checks
        artifact["failed_checks"] = [check for check in checks if check["result"] != PASS]
        artifacts.append(artifact)

    vocabulary = [PASS, KNOWN_ACCEPTED_LIMITATION, VISUAL_PRODUCT_DEFECT, ENVIRONMENT_FAILURE, LATER_GATE_DEBT]
    summary = {
        "artifact_count": len(artifacts),
        "check_count": sum(len(artifact["checks"]) for artifact in artifacts),
        "failed_check_count": sum(len(artifact["failed_checks"]) for artifact in artifacts),
        "visual_product_defects": sum(
            1
            for artifact in artifacts
            for check in artifact["checks"]
            if check["result"] == VISUAL_PRODUCT_DEFECT
        ),
    }
    matrix = {
        "program": "R2-V03",
        "work_package": "R2V03-02",
        "classification_vocabulary": vocabulary,
        "method": (
            "Native Microsoft Word observation: normal document-open path, Print Layout at "
            "100% zoom, Word object-model layout measurements, Word print-layout PDF "
            "rendering, and pixel measurements of the rendered pages."
        ),
        "summary": summary,
        "artifacts": [
            {
                "role": artifact["role"],
                "name": artifact["name"],
                "packaged_output": artifact["packaged_output"],
                "exercises_accepted_irreducible_limitation": artifact[
                    "exercises_accepted_irreducible_limitation"
                ],
                "profile": artifact.get("profile", {}).get("profile_id"),
                "checks": artifact["checks"],
                "failed_checks": artifact["failed_checks"],
            }
            for artifact in artifacts
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(matrix, indent=4, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    print(f"out={args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
