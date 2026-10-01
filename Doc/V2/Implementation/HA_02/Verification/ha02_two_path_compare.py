"""HA-02 two-path comparison (verification-only).

Compares the direct Mermaid runtime renders (Path A: project Playwright runtime)
with the images the installed MD Converter embedded in its DOCX (Path B) for the
exact same Mermaid source.

Both paths are compared geometrically: pixel size, the bounding box of non-white
content, that box's aspect ratio, and a 24x24 occupancy-grid IoU computed on the
content box (layout shape independent of colours and of the surrounding page).

Usage:
    python ha02_two_path_compare.py --direct <png...> --docx-media <png...> [--json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ha02_docx_check import load_png  # noqa: E402  (shares the PNG decoder)

GRID = 24
WHITE_THRESHOLD = 240


def content_mask(path: Path) -> tuple[int, int, list[list[bool]], tuple[int, int, int, int]]:
    """Return (width, height, grid, content bounding box) for one image."""
    width, height, channels, pixels = load_png(path)
    rows: list[list[bool]] = []
    x_min, y_min, x_max, y_max = width, height, -1, -1
    for y in range(height):
        row = y * width * channels
        flags = []
        for x in range(width):
            offset = row + x * channels
            r, g, b = pixels[offset], pixels[offset + 1], pixels[offset + 2]
            ink = not (r > WHITE_THRESHOLD and g > WHITE_THRESHOLD and b > WHITE_THRESHOLD)
            flags.append(ink)
            if ink:
                x_min = min(x_min, x)
                x_max = max(x_max, x)
                y_min = min(y_min, y)
                y_max = max(y_max, y)
        rows.append(flags)
    if x_max < 0:
        return width, height, [[False] * GRID for _ in range(GRID)], (0, 0, 0, 0)

    box = (x_min, y_min, x_max + 1, y_max + 1)
    grid = [[False] * GRID for _ in range(GRID)]
    box_w = max(1, box[2] - box[0])
    box_h = max(1, box[3] - box[1])
    for gy in range(GRID):
        y0 = box[1] + box_h * gy // GRID
        y1 = max(y0 + 1, box[1] + box_h * (gy + 1) // GRID)
        for gx in range(GRID):
            x0 = box[0] + box_w * gx // GRID
            x1 = max(x0 + 1, box[0] + box_w * (gx + 1) // GRID)
            grid[gy][gx] = any(
                rows[y][x] for y in range(y0, min(y1, height)) for x in range(x0, min(x1, width))
            )
    return width, height, grid, box


def grid_iou(a: list[list[bool]], b: list[list[bool]]) -> float:
    """Intersection-over-union of two occupancy grids."""
    inter = union = 0
    for i in range(min(len(a), len(b))):
        row_a, row_b = a[i], b[i]
        for j in range(min(len(row_a), len(row_b))):
            cell_a, cell_b = row_a[j], row_b[j]
            if cell_a or cell_b:
                union += 1
                if cell_a and cell_b:
                    inter += 1
    return round(inter / union, 4) if union else 0.0


def describe(path: Path) -> dict:
    """Summarise one render."""
    width, height, grid, box = content_mask(path)
    box_w = max(1, box[2] - box[0])
    box_h = max(1, box[3] - box[1])
    return {
        "file": path.name,
        "pixels": f"{width}x{height}",
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest()[:16],
        "content_box": box,
        "content_aspect": round(box_w / box_h, 3),
        "grid": grid,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--direct", nargs="+", required=True)
    parser.add_argument("--docx-media", nargs="+", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    direct = [Path(p) for p in args.direct]
    installed = [Path(p) for p in args.docx_media]
    if len(direct) != len(installed):
        print(
            f"count mismatch: {len(direct)} direct vs {len(installed)} installed", file=sys.stderr
        )
        return 2

    results = []
    for index in range(len(direct)):
        path_a, path_b = direct[index], installed[index]
        case_number = index + 1
        a = describe(path_a)
        b = describe(path_b)
        grid_a, grid_b = a.pop("grid"), b.pop("grid")
        results.append(
            {
                "case": case_number,
                "path_a_direct": a,
                "path_b_installed": b,
                "identical_bytes": a["sha256"] == b["sha256"],
                "same_pixel_size": a["pixels"] == b["pixels"],
                "layout_iou": grid_iou(grid_a, grid_b),
            }
        )

    report = {"pairs": len(results), "comparisons": results}
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for row in results:
            print(
                f"case {row['case']}: {row['path_a_direct']['pixels']} vs "
                f"{row['path_b_installed']['pixels']} | aspect "
                f"{row['path_a_direct']['content_aspect']} vs "
                f"{row['path_b_installed']['content_aspect']} | IoU {row['layout_iou']}"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
