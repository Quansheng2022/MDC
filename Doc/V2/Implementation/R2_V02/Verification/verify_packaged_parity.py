"""R2-V02 WP-03 packaged profile/feature parity measurement.

Verification tooling only.  It measures DOCX artifacts that the *packaged*
application produced through its own GUI path and compares the semantic
measurements with the frozen R2-V01 evidence:

* effective profile layout (section margins / content box);
* TOC heading (English and localized control) and canonical TOC field;
* table fitting (explicit column widths inside the content width, 1.2 cm
  column floor, fixed layout, no cell mutation);
* figure fitting (aspect ratio preserved, delivered width equal to
  ``min(image_width, content width)``, page-height cap exercised);
* ``image_width`` target/cap semantics (frozen default 5 in -> 12.70 cm).

The measurement helpers are imported from the accepted R2-V01 verification
module, so the packaged artifact is measured with exactly the same code that
measured the accepted source baseline.

Usage::

    python verify_packaged_parity.py --runs runs.json --output report.json
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from docx import Document

__all__ = ["main"]


def _load_r2v01_measurement_module(repo_root: Path) -> Any:
    """Import the accepted R2-V01 measurement module by path."""
    module_path = (
        repo_root
        / "Doc"
        / "V2"
        / "Implementation"
        / "R2_V01"
        / "Verification"
        / "verify_cross_feature_documents.py"
    )
    spec = importlib.util.spec_from_file_location("r2v01_measurements", module_path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise RuntimeError(f"cannot load measurement module: {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["r2v01_measurements"] = module
    spec.loader.exec_module(module)
    return module


#: Frozen profile geometry measured by R2-V01 WP-03 C (cm).
PROFILE_GEOMETRY: Dict[str, Dict[str, float]] = {
    "professional_report": {
        "left": 2.54,
        "right": 2.54,
        "top": 2.54,
        "bottom": 2.54,
        "content_width": 15.921,
        "content_height": 24.62,
    },
    "business_report": {
        "left": 2.0,
        "right": 2.0,
        "top": 2.0,
        "bottom": 2.0,
        "content_width": 17.0,
        "content_height": 25.7,
    },
    "academic": {
        "left": 3.0,
        "right": 3.0,
        "top": 2.54,
        "bottom": 2.54,
        "content_width": 15.0,
        "content_height": 24.62,
    },
    "technical": {
        "left": 2.2,
        "right": 2.2,
        "top": 2.2,
        "bottom": 2.2,
        "content_width": 16.602,
        "content_height": 25.301,
    },
    "clean_minimal": {
        "left": 2.54,
        "right": 2.54,
        "top": 2.54,
        "bottom": 2.54,
        "content_width": 15.921,
        "content_height": 24.62,
    },
}

#: Frozen canonical ``image_width`` default (``md_converter.config`` DEFAULT_CONFIG).
IMAGE_WIDTH_IN = 5.0
CM_PER_INCH = 2.54
TABLE_MIN_COLUMN_CM = 1.2
MEASURE_TOL_CM = 1e-3

NORMAL_TABLE_CELLS = [
    ["Component", "Authority", "Status"],
    ["Parser", "markdown-it", "frozen"],
    ["Renderer", "WordRenderer", "frozen"],
    ["QA", "compiler", "frozen"],
]


class ParityReport:
    """Collect PASS/FAIL parity checks for the packaged artifacts."""

    def __init__(self) -> None:
        self.checks: List[Dict[str, Any]] = []

    def check(self, label: str, ok: bool, detail: str = "") -> None:
        """Record one parity check."""
        self.checks.append({"label": label, "passed": bool(ok), "detail": detail})


def measure(doc: Any, module: Any, path: Path) -> Dict[str, Any]:
    """Return the semantic measurements of one DOCX artifact."""
    sections = []
    for section in doc.sections:
        sections.append(
            {
                "left": round(section.left_margin.cm, 3),
                "right": round(section.right_margin.cm, 3),
                "top": round(section.top_margin.cm, 3),
                "bottom": round(section.bottom_margin.cm, 3),
                "page_width": round(section.page_width.cm, 3),
                "page_height": round(section.page_height.cm, 3),
            }
        )
    tables = []
    for table in doc.tables:
        widths = module.table_widths_cm(table)
        tables.append(
            {
                "rows": len(table.rows),
                "columns": len(table.columns),
                "widths_cm": widths,
                "total_cm": round(sum(widths), 4),
                "min_cm": min(widths) if widths else None,
                "cells": module.table_matrix(table),
            }
        )
    shapes = [
        {
            "width_cm": round(shape.width.cm, 4),
            "height_cm": round(shape.height.cm, 4),
            "ratio": round(shape.width.cm / shape.height.cm, 4) if shape.height.cm else None,
        }
        for shape in doc.inline_shapes
    ]
    return {
        "document_xml_present": module.doc_xml(path) != "",
        "sections": sections,
        "toc_heading": module.toc_heading(doc),
        "toc_entries": module.toc_entry_texts(doc),
        "toc_field_present": module.toc_field_present(path),
        "tables": tables,
        "figures": shapes,
    }


def check_matrix_run(run: Dict[str, Any], measurements: Dict[str, Any], report: ParityReport) -> None:
    """Check one five-profile matrix artifact against the frozen semantics."""
    profile = run["profile"]
    geometry = PROFILE_GEOMETRY[profile]
    tag = f"{profile}"

    section = measurements["sections"][-1]
    report.check(
        f"{tag}: profile margins reach the packaged artifact",
        all(
            abs(section[key] - geometry[key]) < 0.02
            for key in ("left", "right", "top", "bottom")
        ),
        "margins(L,R,T,B)={0}".format(
            (section["left"], section["right"], section["top"], section["bottom"])
        ),
    )
    content_w = round(section["page_width"] - section["left"] - section["right"], 3)
    content_h = round(section["page_height"] - section["top"] - section["bottom"], 3)
    report.check(
        f"{tag}: effective content box matches R2-V01",
        abs(content_w - geometry["content_width"]) < 0.01
        and abs(content_h - geometry["content_height"]) < 0.01,
        f"content={content_w}x{content_h} expected={geometry['content_width']}x{geometry['content_height']}",
    )
    report.check(
        f"{tag}: TOC heading is the English title",
        measurements["toc_heading"] == "Table of Contents",
        f"heading={measurements['toc_heading']!r}",
    )
    report.check(
        f"{tag}: canonical TOC field present",
        bool(measurements["toc_field_present"]),
    )
    entries = {entry.rstrip() for entry in measurements["toc_entries"]}
    report.check(
        f"{tag}: TOC caches the document headings",
        {"Architecture", "Financial Overview", "Projected Growth"} <= entries,
        f"entries={measurements['toc_entries']}",
    )
    report.check(
        f"{tag}: normal table cells unchanged",
        measurements["tables"][0]["cells"] == NORMAL_TABLE_CELLS,
        f"cells={measurements['tables'][0]['cells']}",
    )
    wide = measurements["tables"][1]
    report.check(
        f"{tag}: wide table fits the profile content width",
        len(wide["widths_cm"]) == 8 and wide["total_cm"] <= content_w + 0.01,
        f"columns={len(wide['widths_cm'])} total={wide['total_cm']} content={content_w}",
    )
    report.check(
        f"{tag}: wide table respects the 1.2 cm column floor",
        wide["min_cm"] is not None and wide["min_cm"] >= TABLE_MIN_COLUMN_CM - MEASURE_TOL_CM,
        f"min_column={wide['min_cm']}",
    )
    report.check(
        f"{tag}: wide table keeps every cell (no mutation)",
        wide["rows"] == 5
        and wide["columns"] == 8
        and wide["cells"][1][0] == "North"
        and wide["cells"][4][0] == "West",
        f"rows={wide['rows']} columns={wide['columns']} first={wide['cells'][1][0]!r}",
    )

    figures = measurements["figures"]
    report.check(
        f"{tag}: both figures rendered",
        len(figures) == 2,
        f"figures={figures}",
    )
    if len(figures) == 2:
        wide_fig, tall_fig = figures
        target = min(IMAGE_WIDTH_IN * CM_PER_INCH, content_w)
        report.check(
            f"{tag}: image_width target respected (5 in default, capped by content)",
            abs(wide_fig["width_cm"] - target) < 0.05,
            f"width={wide_fig['width_cm']} target={round(target, 3)}",
        )
        report.check(
            f"{tag}: wide figure aspect ratio preserved (4:1)",
            abs(wide_fig["ratio"] - 4.0) < 0.02,
            f"ratio={wide_fig['ratio']}",
        )
        report.check(
            f"{tag}: page-height cap exercised on the tall figure",
            abs(tall_fig["height_cm"] - content_h) < 0.05,
            f"height={tall_fig['height_cm']} content_height={content_h}",
        )
        report.check(
            f"{tag}: tall figure aspect ratio preserved (1:10)",
            abs(tall_fig["ratio"] - 0.1) < 0.002,
            f"ratio={tall_fig['ratio']}",
        )
        report.check(
            f"{tag}: figures stay inside the content box",
            all(
                figure["width_cm"] <= content_w + 0.05 and figure["height_cm"] <= content_h + 0.05
                for figure in figures
            ),
            f"figures={figures} box={content_w}x{content_h}",
        )


def check_toc_control_run(
    run: Dict[str, Any], measurements: Dict[str, Any], report: ParityReport
) -> None:
    """Check the localized TOC control artifact."""
    profile = run["profile"]
    geometry = PROFILE_GEOMETRY[profile]
    section = measurements["sections"][-1]
    report.check(
        "toc_cn: localized TOC heading",
        measurements["toc_heading"] == "目录",
        f"heading={measurements['toc_heading']!r}",
    )
    report.check(
        "toc_cn: canonical TOC field present",
        bool(measurements["toc_field_present"]),
    )
    report.check(
        "toc_cn: profile geometry still applied",
        abs(section["left"] - geometry["left"]) < 0.02
        and abs(section["right"] - geometry["right"]) < 0.02,
        f"margins(L,R)=({section['left']},{section['right']})",
    )
    report.check(
        "toc_cn: table and figure rendered",
        len(measurements["tables"]) >= 1 and len(measurements["figures"]) == 1,
        f"tables={len(measurements['tables'])} figures={len(measurements['figures'])}",
    )
    report.check(
        "toc_cn: figure aspect ratio preserved (4:1)",
        len(measurements["figures"]) == 1 and abs(measurements["figures"][0]["ratio"] - 4.0) < 0.02,
        f"figures={measurements['figures']}",
    )


def main() -> int:
    """Measure every packaged artifact and report parity checks as JSON."""
    parser = argparse.ArgumentParser(description="R2-V02 packaged parity measurement")
    parser.add_argument("--runs", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--repo-root", required=True, type=Path)
    args = parser.parse_args()

    module = _load_r2v01_measurement_module(args.repo_root)
    runs = json.loads(args.runs.read_text(encoding="utf-8"))
    report = ParityReport()
    measurements: Dict[str, Any] = {}

    for run in runs:
        path = Path(run["docx"])
        if not path.exists():
            report.check(f"{run['name']}: packaged DOCX exists", False, f"missing {path}")
            continue
        try:
            document = Document(str(path))
        except Exception as exc:  # noqa: BLE001 - measurement report, not product code
            report.check(f"{run['name']}: packaged DOCX opens", False, str(exc))
            continue
        measured = measure(document, module, path)
        measurements[run["name"]] = {"path": str(path), **measured}
        report.check(f"{run['name']}: packaged DOCX opens", True, str(path))
        if run.get("kind") == "toc_control":
            check_toc_control_run(run, measured, report)
        else:
            check_matrix_run(run, measured, report)

    failures = [check for check in report.checks if not check["passed"]]
    result = {
        "checks": report.checks,
        "measurements": measurements,
        "total": len(report.checks),
        "failed": len(failures),
        "status": "PASS" if not failures else "FAIL",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"parity checks={result['total']} failed={result['failed']} status={result['status']}")
    for check in failures:
        print(f"FAIL {check['label']} :: {check['detail']}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
