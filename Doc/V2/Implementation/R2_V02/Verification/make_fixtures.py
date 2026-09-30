"""R2-V02 verification fixtures (packaged multi-file runtime gate).

Verification tooling only: this module writes deterministic Markdown inputs and
deterministic PNG figures into a *neutral* work directory (never into the
repository source tree).  It contains no product logic and is never imported by
the product.

Usage::

    python make_fixtures.py --work <dir> --set wp02
    python make_fixtures.py --work <dir> --set wp03
"""

from __future__ import annotations

import argparse
import json
import struct
import zlib
from pathlib import Path

__all__ = ["write_png", "main"]


def _png_bytes(width: int, height: int) -> bytes:
    """Return a deterministic solid-colour PNG of ``width`` x ``height``."""
    scanline = b"\x00" + bytes((0x2F, 0x54, 0x96)) * width
    raw = scanline * height

    def chunk(tag: bytes, payload: bytes) -> bytes:
        body = tag + payload
        return (
            struct.pack(">I", len(payload))
            + body
            + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def write_png(path: Path, width: int, height: int) -> Path:
    """Write a deterministic PNG and return its path."""
    path.write_bytes(_png_bytes(width, height))
    return path


def _wide_table(columns: int, cell_text: str) -> str:
    """Return a Markdown table with ``columns`` columns."""
    header = "|" + "|".join(f" H{index} " for index in range(columns)) + "|"
    separator = "|" + "|".join(" --- " for _ in range(columns)) + "|"
    row = "|" + "|".join(f" {cell_text} " for _ in range(columns)) + "|"
    return "\n".join([header, separator, row, ""])


NORMAL_TABLE = """| Component | Authority | Status |
| --- | --- | --- |
| Parser | markdown-it | frozen |
| Renderer | WordRenderer | frozen |
| QA | compiler | frozen |
"""

WIDE_TABLE = """| Region | Q1 | Q2 | Q3 | Q4 | Notes | Owner | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| North | 120 | 130 | 140 | 150 | steady | A. Lee | accepted |
| South | 98 | 105 | 111 | 118 | recovering | B. Ng | accepted |
| East | 210 | 214 | 219 | 225 | expanding | C. Tan | accepted |
| West | 64 | 70 | 75 | 81 | new | D. Rao | accepted |
"""


def fixture_set_wp02(work: Path) -> None:
    """Write the four-file serial-batch fixture set."""
    write_png(work / "fig_wide.png", 400, 100)
    (work / "01_english.md").write_text(
        "# English Document\n"
        "\n"
        "A valid English document converted in the packaged serial batch.\n"
        "\n"
        "- packaged runtime\n"
        "- strict serial queue\n",
        encoding="utf-8",
    )
    (work / "02_wide_table_figure.md").write_text(
        "---\n"
        "title: Wide Table Report\n"
        "---\n"
        "\n"
        "# Wide Table Report\n"
        "\n"
        "## Data\n"
        "\n"
        f"{WIDE_TABLE}\n"
        "## Figure\n"
        "\n"
        "![Wide figure](fig_wide.png)\n",
        encoding="utf-8",
    )
    # Deliberate failing case: an empty Markdown source is accepted by the GUI
    # boundary (a file with a supported extension) and fails in the canonical
    # conversion core - exactly the failure isolation the packaged serial batch
    # must survive.
    (work / "03_failure.md").write_text("", encoding="utf-8")
    (work / "04_after_failure.md").write_text(
        "# After Failure\n"
        "\n"
        "This document must still convert after the previous file failed.\n",
        encoding="utf-8",
    )


def _integrated_document(title: str, wide_figure: str, tall_figure: str) -> str:
    """Return the integrated representative document for one profile run."""
    return (
        "---\n"
        f"title: {title}\n"
        "---\n"
        "\n"
        "# Competitive Foundation Report\n"
        "\n"
        "Integrated packaged-runtime verification document.\n"
        "\n"
        "## Architecture\n"
        "\n"
        f"{NORMAL_TABLE}\n"
        "## Financial Overview\n"
        "\n"
        f"{WIDE_TABLE}\n"
        "## Projected Growth\n"
        "\n"
        f"![Growth chart]({wide_figure})\n"
        "\n"
        "## Page Capped Figure\n"
        "\n"
        f"![Tall figure]({tall_figure})\n"
        "\n"
        "### Notes\n"
        "\n"
        "Deterministic packaged verification only.\n"
    )


#: (profile id, fixture stem, document title) for the five-profile matrix.
MATRIX_PROFILES = (
    ("professional_report", "matrix_professional_report", "Matrix Professional Report"),
    ("business_report", "matrix_business_report", "Matrix Business Report"),
    ("academic", "matrix_academic", "Matrix Academic"),
    ("technical", "matrix_technical", "Matrix Technical"),
    ("clean_minimal", "matrix_clean_minimal", "Matrix Clean Minimal"),
)

#: Profile selector display names (the labels the packaged GUI shows).
PROFILE_DISPLAY = {
    "professional_report": "Professional Report",
    "business_report": "Business Report",
    "academic": "Academic",
    "technical": "Technical",
    "clean_minimal": "Clean / Minimal",
}


def fixture_set_wp03(work: Path) -> None:
    """Write the integrated five-profile matrix fixtures plus one TOC control."""
    write_png(work / "fig_wide.png", 400, 100)
    write_png(work / "fig_tall.png", 20, 200)
    for _profile, stem, title in MATRIX_PROFILES:
        (work / f"{stem}.md").write_text(
            _integrated_document(title, "fig_wide.png", "fig_tall.png"),
            encoding="utf-8",
        )
    # TOC localization control: the frozen invariant is a localized TOC heading,
    # so the packaged runtime is checked for the Chinese heading as well as for
    # the English one produced by the five-profile matrix.
    (work / "toc_cn.md").write_text(
        "---\n"
        "title: 竞争基础集成验证\n"
        "---\n"
        "\n"
        "# 竞争基础集成验证\n"
        "\n"
        "本报告用于验证打包运行时的集成一致性。\n"
        "\n"
        "## 架构\n"
        "\n"
        "| 组件 | 权威 | 状态 |\n"
        "| --- | --- | --- |\n"
        "| 解析器 | markdown-it | 冻结 |\n"
        "| 渲染器 | WordRenderer | 冻结 |\n"
        "| 质量门 | compiler | 冻结 |\n"
        "\n"
        "## 图形\n"
        "\n"
        "![增长图](fig_wide.png)\n"
        "\n"
        "### 备注\n"
        "\n"
        "仅用于确定性验证。\n",
        encoding="utf-8",
    )


def main() -> int:
    """Write one fixture set into the requested work directory."""
    parser = argparse.ArgumentParser(description="R2-V02 verification fixtures")
    parser.add_argument("--work", required=True, type=Path)
    parser.add_argument("--set", required=True, choices=("wp02", "wp03"))
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    if args.set == "wp02":
        fixture_set_wp02(args.work)
        manifest = {
            "set": "wp02",
            "sources": [
                {"file": "01_english.md", "expected_output": "01_english.docx"},
                {"file": "02_wide_table_figure.md", "expected_output": "Wide_Table_Report.docx"},
                {"file": "03_failure.md", "expected_output": None},
                {"file": "04_after_failure.md", "expected_output": "04_after_failure.docx"},
            ],
        }
    else:
        fixture_set_wp03(args.work)
        manifest = {
            "set": "wp03",
            "runs": [
                {
                    "name": stem,
                    "file": f"{stem}.md",
                    "profile": PROFILE_DISPLAY[profile_id],
                    "profile_id": profile_id,
                    "title": title,
                    "expected_output": f"{title.replace(' ', '_')}.docx",
                    "kind": "matrix",
                }
                for profile_id, stem, title in MATRIX_PROFILES
            ]
            + [
                {
                    "name": "toc_cn",
                    "file": "toc_cn.md",
                    "profile": "Professional Report",
                    "profile_id": "professional_report",
                    "title": "竞争基础集成验证",
                    "expected_output": "竞争基础集成验证.docx",
                    "kind": "toc_control",
                }
            ],
        }
    manifest_path = args.manifest or (args.work / "fixture_manifest.json")
    # Written with a BOM: the Windows PowerShell 5.1 harness reads this file
    # without an explicit encoding and would otherwise mis-decode non-ASCII
    # document titles (the localized TOC control fixture).
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8-sig")
    print(f"fixtures={args.set} work={args.work}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
