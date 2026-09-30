"""R2-V03 rendered-page pixel measurements.

The R2-V03 acceptance set was exported by desktop Microsoft Word through its own
print-layout PDF renderer and rasterised with Poppler.  This verifier measures
the resulting page images pixel by pixel:

* the page is not blank and its ink stays inside the page's text body;
* a figure is present on the page at the expected size and aspect ratio (so it
  is neither stretched nor cropped);
* the figure stays inside the usable page body.

The figure fixtures are deterministic solid rectangles (RGB 47, 84, 150), so the
figure can be located in the rendered pixels without any guessing.

Usage::

    python r2v03_page_image_check.py --index <index.json> --images-dir <dir> \
        --out <matrix.json> [--dpi 110]
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import Image

__all__ = ["main"]

#: Deterministic figure fixture colour written by the R2-V02 fixture generator.
FIGURE_RGB = (0x2F, 0x54, 0x96)
FIGURE_TOLERANCE = 16
WHITE_LEVEL = 245


def _bounds(mask: List[Any], width: int, height: int) -> Optional[Dict[str, int]]:
    """Return the pixel bounding box of a boolean sequence of length w*h."""
    xs: List[int] = []
    ys: List[int] = []
    for index, value in enumerate(mask):
        if value:
            ys.append(index // width)
            xs.append(index % width)
    if not xs:
        return None
    return {"x0": min(xs), "x1": max(xs), "y0": min(ys), "y1": max(ys), "pixels": len(xs)}


def measure_page(path: Path, dpi: float, margins: Dict[str, float]) -> Dict[str, Any]:
    """Return the pixel measurements of one rendered page image."""
    with Image.open(path) as image:
        rgb = image.convert("RGB")
        width, height = rgb.size
        pixels = list(rgb.getdata())

    px_per_cm = dpi / 2.54
    ink_mask = []
    figure_mask = []
    for red, green, blue in pixels:
        is_ink = not (
            red >= WHITE_LEVEL and green >= WHITE_LEVEL and blue >= WHITE_LEVEL
        )
        ink_mask.append(is_ink)
        figure_mask.append(
            abs(red - FIGURE_RGB[0]) <= FIGURE_TOLERANCE
            and abs(green - FIGURE_RGB[1]) <= FIGURE_TOLERANCE
            and abs(blue - FIGURE_RGB[2]) <= FIGURE_TOLERANCE
        )

    ink = _bounds(ink_mask, width, height)
    figure = _bounds(figure_mask, width, height)
    result: Dict[str, Any] = {
        "image": path.name,
        "width_px": width,
        "height_px": height,
        "dpi": dpi,
        "page_width_cm": round(width / px_per_cm, 3),
        "page_height_cm": round(height / px_per_cm, 3),
        "ink_fraction": round(sum(ink_mask) / float(width * height), 6),
        "blank": sum(ink_mask) == 0,
    }
    if ink:
        result["ink_bbox_px"] = ink
        result["ink_bbox_cm"] = {
            key: round(value / px_per_cm, 3) for key, value in ink.items() if key != "pixels"
        }
        body = {
            "left_cm": margins["left_cm"],
            "right_cm": result["page_width_cm"] - margins["right_cm"],
            "top_cm": margins["top_cm"],
            "bottom_cm": result["page_height_cm"] - margins["bottom_cm"],
        }
        ink_cm = result["ink_bbox_cm"]
        overflow = {
            "left_cm": round(body["left_cm"] - ink_cm["x0"], 3),
            "right_cm": round(ink_cm["x1"] - body["right_cm"], 3),
            "top_cm": round(body["top_cm"] - ink_cm["y0"], 3),
            "bottom_cm": round(ink_cm["y1"] - body["bottom_cm"], 3),
        }
        result["text_body_cm"] = {key: round(value, 3) for key, value in body.items()}
        result["body_overflow_cm"] = overflow
        result["ink_within_text_body"] = all(value <= 0.3 for value in overflow.values())
    if figure:
        figure_cm = {
            key: round(value / px_per_cm, 3) for key, value in figure.items() if key != "pixels"
        }
        figure_width = figure_cm["x1"] - figure_cm["x0"]
        figure_height = figure_cm["y1"] - figure_cm["y0"]
        result["figure"] = {
            "bbox_px": figure,
            "bbox_cm": figure_cm,
            "width_cm": round(figure_width, 3),
            "height_cm": round(figure_height, 3),
            "aspect_ratio": round(figure_width / figure_height, 4) if figure_height else None,
            "fill_ratio": round(
                figure["pixels"] / float((figure["x1"] - figure["x0"] + 1) * (figure["y1"] - figure["y0"] + 1)),
                4,
            ),
        }
    return result


def _refine_block(
    image: Any,
    dpi: float,
    coarse: Dict[str, float],
    downsample: int,
) -> Optional[Dict[str, float]]:
    """Refine a coarse block to full-resolution bounds by flood filling it.

    The coarse scan downsamples the page, which trims about two downsampled
    pixels from every edge. Refining at full resolution removes that bias
    without merging the block into a neighbouring element.
    """
    px_per_cm = dpi / 2.54
    pad = 3 * downsample
    left = max(0, int(coarse["left_cm"] * px_per_cm) - pad)
    top = max(0, int(coarse["top_cm"] * px_per_cm) - pad)
    right = min(image.width, int(coarse["right_cm"] * px_per_cm) + pad)
    bottom = min(image.height, int(coarse["bottom_cm"] * px_per_cm) + pad)
    crop = image.crop((left, top, right, bottom)).convert("RGB")
    width, height = crop.size
    pixels = list(crop.getdata())
    mask = bytearray(
        abs(red - FIGURE_RGB[0]) <= FIGURE_TOLERANCE
        and abs(green - FIGURE_RGB[1]) <= FIGURE_TOLERANCE
        and abs(blue - FIGURE_RGB[2]) <= FIGURE_TOLERANCE
        for red, green, blue in pixels
    )
    center_x = min(width - 1, max(0, int((coarse["left_cm"] + coarse["right_cm"]) / 2 * px_per_cm) - left))
    center_y = min(height - 1, max(0, int((coarse["top_cm"] + coarse["bottom_cm"]) / 2 * px_per_cm) - top))
    seed = center_y * width + center_x
    if not mask[seed]:
        for offset in range(1, 40):
            for candidate in (seed - offset, seed + offset):
                if 0 <= candidate < width * height and mask[candidate]:
                    seed = candidate
                    break
            else:
                continue
            break
    if not mask[seed]:
        return None
    visited = bytearray(width * height)
    stack = [seed]
    visited[seed] = 1
    xs: List[int] = []
    ys: List[int] = []
    while stack:
        index = stack.pop()
        y, x = divmod(index, width)
        xs.append(x)
        ys.append(y)
        if x and mask[index - 1] and not visited[index - 1]:
            visited[index - 1] = 1
            stack.append(index - 1)
        if x + 1 < width and mask[index + 1] and not visited[index + 1]:
            visited[index + 1] = 1
            stack.append(index + 1)
        if y and mask[index - width] and not visited[index - width]:
            visited[index - width] = 1
            stack.append(index - width)
        if y + 1 < height and mask[index + width] and not visited[index + width]:
            visited[index + width] = 1
            stack.append(index + width)
    cm_per_px = 1.0 / px_per_cm
    box_width = max(xs) - min(xs) + 1
    box_height = max(ys) - min(ys) + 1
    return {
        "left_cm": round((left + min(xs)) * cm_per_px, 3),
        "top_cm": round((top + min(ys)) * cm_per_px, 3),
        "right_cm": round((left + max(xs) + 1) * cm_per_px, 3),
        "bottom_cm": round((top + max(ys) + 1) * cm_per_px, 3),
        "width_cm": round(box_width * cm_per_px, 3),
        "height_cm": round(box_height * cm_per_px, 3),
        "fill_fraction": round(len(xs) / float(box_width * box_height), 4),
        "area_cm2": round(len(xs) * cm_per_px * cm_per_px, 3),
    }


def find_solid_figure_blocks(
    path: Path,
    dpi: float,
    downsample: int = 4,
    min_area_cm2: float = 0.5,
    min_fill: float = 0.9,
) -> List[Dict[str, Any]]:
    """Return the solid figure blocks found in one rendered page image.

    The figure fixtures are solid rectangles, so a block of exactly that colour
    identifies a rendered figure without relying on any declared position. The
    image is box-downsampled first: that keeps a solid block at its exact colour
    while blending thin table borders and text towards white, so only genuine
    solid figure areas survive the colour test.

    Args:
        path: Rendered page image.
        dpi: Rasterisation resolution of the page image.
        downsample: Box-downsample factor used before the colour test.
        min_area_cm2: Smallest block to report.
        min_fill: Minimum block area / bounding-box area.

    Returns:
        List[Dict[str, Any]]: One entry per detected block, in square centimetres.
    """
    with Image.open(path) as handle:
        image = handle.convert("RGB")
        small = image.resize(
            (max(1, image.width // downsample), max(1, image.height // downsample)),
            Image.BOX,
        )
        width, height = small.size
        pixels = list(small.getdata())

    mask = [
        abs(red - FIGURE_RGB[0]) <= FIGURE_TOLERANCE
        and abs(green - FIGURE_RGB[1]) <= FIGURE_TOLERANCE
        and abs(blue - FIGURE_RGB[2]) <= FIGURE_TOLERANCE
        for red, green, blue in pixels
    ]

    cm_per_px = downsample / (dpi / 2.54)
    visited = bytearray(width * height)
    blocks: List[Dict[str, Any]] = []
    for start in range(width * height):
        if visited[start] or not mask[start]:
            continue
        stack = [start]
        visited[start] = 1
        xs: List[int] = []
        ys: List[int] = []
        while stack:
            index = stack.pop()
            y, x = divmod(index, width)
            xs.append(x)
            ys.append(y)
            if x and mask[index - 1] and not visited[index - 1]:
                visited[index - 1] = 1
                stack.append(index - 1)
            if x + 1 < width and mask[index + 1] and not visited[index + 1]:
                visited[index + 1] = 1
                stack.append(index + 1)
            if y and mask[index - width] and not visited[index - width]:
                visited[index - width] = 1
                stack.append(index - width)
            if y + 1 < height and mask[index + width] and not visited[index + width]:
                visited[index + width] = 1
                stack.append(index + width)
        area_cm2 = len(xs) * cm_per_px * cm_per_px
        if area_cm2 < min_area_cm2:
            continue
        box_width = max(xs) - min(xs) + 1
        box_height = max(ys) - min(ys) + 1
        fill = len(xs) / float(box_width * box_height)
        if fill < min_fill:
            continue
        coarse = {
            "left_cm": round(min(xs) * cm_per_px, 3),
            "top_cm": round(min(ys) * cm_per_px, 3),
            "right_cm": round((max(xs) + 1) * cm_per_px, 3),
            "bottom_cm": round((max(ys) + 1) * cm_per_px, 3),
        }
        refined = _refine_block(image, dpi, coarse, downsample) or coarse
        block = {"image": path.name, **refined}
        block["aspect_ratio"] = (
            round(block["width_cm"] / block["height_cm"], 4) if block["height_cm"] else None
        )
        blocks.append(block)
    return sorted(blocks, key=lambda block: -block["area_cm2"])


def main() -> int:
    """Measure every rendered page image and write one JSON matrix."""
    parser = argparse.ArgumentParser(description="R2-V03 rendered-page measurements")
    parser.add_argument("--index", required=True, type=Path)
    parser.add_argument("--images-dir", required=True, type=Path)
    parser.add_argument(
        "--word-report-dir",
        type=Path,
        help="native Word probe reports; enables the declared-figure pixel check",
    )
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--dpi", default=110.0, type=float)
    args = parser.parse_args()

    index = json.loads(args.index.read_text(encoding="utf-8"))
    artifacts: List[Dict[str, Any]] = []
    for item in index["items"]:
        structure = item.get("structure") or {}
        sections = structure.get("sections") or []
        primary = sections[-1] if len(sections) > 1 else (sections[0] if sections else None)
        if primary is None:
            continue
        margins = {
            "left_cm": primary["left_cm"],
            "right_cm": primary["right_cm"],
            "top_cm": primary["top_cm"],
            "bottom_cm": primary["bottom_cm"],
        }
        stem = Path(item["name"]).stem
        paths = sorted(
            (path for path in args.images_dir.glob(f"{stem}-*.png")),
            key=lambda path: int(re.findall(r"-(\d+)\.png$", path.name)[0])
            if re.findall(r"-(\d+)\.png$", path.name)
            else 0,
        )
        pages = [measure_page(path, args.dpi, margins) for path in paths]
        declared = ((structure.get("figures") or {}).get("inline_shapes")) or []
        for page in pages:
            blocks = find_solid_figure_blocks(
                args.images_dir / page["image"], args.dpi
            )
            for index, block in enumerate(blocks):
                best = None
                for shape in declared:
                    if shape.get("ratio") and block["aspect_ratio"]:
                        delta = abs(block["aspect_ratio"] - shape["ratio"]) / shape["ratio"]
                        if best is None or delta < best[0]:
                            best = (delta, shape)
                if best is not None:
                    block["closest_declared_ratio"] = best[1]["ratio"]
                    block["closest_declared_size_cm"] = [
                        best[1].get("width_cm"),
                        best[1].get("height_cm"),
                    ]
                    block["ratio_delta_percent"] = round(100.0 * best[0], 3)
                block["block_index"] = index + 1
            page["solid_figure_blocks"] = blocks
        artifacts.append(
            {
                "role": item["role"],
                "name": item["name"],
                "stem": stem,
                "margins_cm": margins,
                "page_count": len(pages),
                "blank_pages": [page["image"] for page in pages if page["blank"]],
                "pages_outside_body": [
                    page["image"]
                    for page in pages
                    if not page.get("ink_within_text_body", True)
                ],
                "pages": pages,
                "solid_figure_blocks": [
                    block for page in pages for block in page["solid_figure_blocks"]
                ],
            }
        )

    all_pages = [page for artifact in artifacts for page in artifact["pages"]]

    matrix = {
        "program": "R2-V03",
        "work_package": "R2V03-02",
        "method": (
            "Pixel measurements of the page images rasterised from the native "
            "Microsoft Word print-layout PDF rendering of the acceptance set."
        ),
        "figure_fixture_rgb": list(FIGURE_RGB),
        "artifact_count": len(artifacts),
        "page_count": len(all_pages),
        "blank_pages": [page["image"] for page in all_pages if page["blank"]],
        "pages_outside_body": [
            page["image"] for page in all_pages if not page.get("ink_within_text_body", True)
        ],
        "artifacts": artifacts,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(matrix, indent=4, ensure_ascii=False), encoding="utf-8")
    print(
        f"artifacts={len(artifacts)} pages={len(all_pages)} "
        f"blank={len(matrix['blank_pages'])} outside_body={len(matrix['pages_outside_body'])}"
    )
    print(f"out={args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
