#!/usr/bin/env python3
"""
Project Merger - 项目快照生成器（MERGER-SEC-01 / MERGER-CLEAN-01 / MERGER-TEST-01）

把项目源码树合并为单个文本快照，供 AI Review / Architecture Review 使用。

安全模型（两层过滤）:
    Filename filter
        ↓
    Read text
        ↓
    Content secret scan
        ↓
    secret? -> BLOCK（跳过文件，仅记录 pattern 名称）
        ↓
    no      -> MERGE

原则:
    - 高置信度 credential（sk- token / AWS AKIA / GitHub token / private key header）
      直接 BLOCK 整个文件，不做自动 REDACT。
    - Merge Report 只输出 pattern 名称，绝不输出匹配到的秘密值。
    - 排除 generated / noisy 内容：.egg-info、input/、input_test/、output/ 等。
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ============================================================
# 排除规则
# ============================================================

EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".codex",
    ".agents",
    "node_modules",
    # P2（MERGER-CLEAN-01）：噪声目录
    "input",
    "input_test",
    "output",
}

TEXT_EXTENSIONS = {
    ".py",
    ".md",
    ".txt",
    ".toml",
    ".yaml",
    ".yml",
    ".json",
    ".cfg",
    ".ini",
    ".sh",
    ".ps1",
    ".bat",
    ".csv",
    ".tsv",
    ".xml",
}

EXCLUDE_FILE_EXACT = {
    ".env",
}


def should_exclude_dir(name: str) -> bool:
    """目录是否排除（含 *.egg-info generated metadata）。"""
    if name in EXCLUDE_DIRS:
        return True
    return name.endswith(".egg-info")


def should_exclude_file(name: str) -> bool:
    """文件是否按名称排除。"""
    if name in EXCLUDE_FILE_EXACT:
        return True
    if name.endswith(".min.js"):
        return True
    if name.endswith(".pyc"):
        return True
    return False


def is_text_extension(name: str) -> bool:
    """仅合并文本类文件；二进制/文档文件不进入快照。"""
    if name.startswith("."):
        # dotfile（.env.example / .gitignore 等）是文本配置模板
        return True
    return Path(name).suffix.lower() in TEXT_EXTENSIONS


# ============================================================
# 内容秘密扫描（MERGER-SEC-01）
# ============================================================

SECRET_PATTERNS = {
    "generic_api_key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "github_token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}


def detect_secrets(content: str) -> List[str]:
    """
    检测高置信度 credential。

    返回:
        List[str]: 命中的 pattern 名称列表；**绝不返回秘密值**。
    """
    detected: List[str] = []
    for name, pattern in SECRET_PATTERNS.items():
        if pattern.search(content):
            detected.append(name)
    return detected


# ============================================================
# 快照生成
# ============================================================


def build_snapshot(
    root: Path,
    output_path: Path,
) -> Dict[str, object]:
    """
    合并项目树为单个文本快照。

    返回:
        Dict: 包含 merged_entries / skipped_entries / read_failures 的报告
    """
    root = Path(root).resolve()
    output_abs = Path(output_path).resolve()
    merged_entries: List[Tuple[str, str]] = []
    skipped_entries: List[Tuple[str, str]] = []
    read_failures: List[Tuple[str, str]] = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not should_exclude_dir(d)]
        for filename in sorted(filenames):
            file_path = Path(dirpath) / filename
            rel_path = file_path.relative_to(root).as_posix()
            if file_path.resolve() == output_abs:
                skipped_entries.append((rel_path, "output snapshot excluded"))
                continue
            if should_exclude_file(filename):
                skipped_entries.append((rel_path, f"excluded file name: {filename}"))
                continue
            if not is_text_extension(filename):
                skipped_entries.append((rel_path, "non-text file skipped"))
                continue
            try:
                content = file_path.read_text(encoding="utf-8")
            except Exception as e:  # noqa: BLE001 - 记录读取失败
                read_failures.append((rel_path, str(e)))
                continue

            secret_types = detect_secrets(content)
            if secret_types:
                # BLOCK whole file；只记录 pattern 名称，不记录秘密值
                skipped_entries.append(
                    (
                        rel_path,
                        "possible embedded secret detected: " + ", ".join(secret_types),
                    )
                )
                continue

            merged_entries.append((rel_path, content))

    report = {
        "root": str(root),
        "output": str(output_path),
        "merged_count": len(merged_entries),
        "skipped_count": len(skipped_entries),
        "read_failure_count": len(read_failures),
        "merged_entries": merged_entries,
        "skipped_entries": skipped_entries,
        "read_failures": read_failures,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    parts = [
        "PROJECT SNAPSHOT",
        "================",
        f"root: {root}",
        f"merged files: {len(merged_entries)}",
        f"security/other skips: {len(skipped_entries)}",
        f"read failures: {len(read_failures)}",
        "",
    ]
    for rel_path, content in merged_entries:
        parts.append(f"===== FILE: {rel_path} =====")
        parts.append(content.rstrip("\n"))
        parts.append("")
    output_path.write_text("\n".join(parts), encoding="utf-8")
    return report


def print_report(report: Dict[str, object]) -> None:
    """打印合并报告（skipped 只显示原因，不显示秘密值）。"""
    print(f"Merged files: {report['merged_count']}")
    print(f"Skipped entries: {report['skipped_count']}")
    print(f"Read failures: {report['read_failure_count']}")
    for rel_path, reason in report["skipped_entries"]:  # type: ignore[union-attr]
        print(f"  SKIP {rel_path}: {reason}")
    for rel_path, error in report["read_failures"]:  # type: ignore[union-attr]
        print(f"  FAIL {rel_path}: {error}")


# ============================================================
# 自测（MERGER-TEST-01）
# ============================================================


def _self_test() -> int:
    """6 条最小自测。"""
    import tempfile

    with tempfile.TemporaryDirectory(prefix="merger_self_test_") as tmp:
        root = Path(tmp)
        (root / "ok.py").write_text("x = 1\n", encoding="utf-8")
        (root / "ok.md").write_text("# doc\n", encoding="utf-8")
        (root / ".env").write_text("TOKEN=abc\n", encoding="utf-8")
        (root / ".env.example").write_text("TOKEN=\n", encoding="utf-8")
        (root / "app.min.js").write_text("var a=1;\n", encoding="utf-8")
        (root / "leak.txt").write_text(
            "key=sk-" + "1" * 30 + "\n",
            encoding="utf-8",
        )
        (root / "docs").mkdir()
        (root / "docs" / "safe.txt").write_text(
            "Enter API key (starts with sk-) here\n", encoding="utf-8"
        )
        (root / "output").mkdir()
        (root / "output" / "snapshot.txt").write_text("noise\n", encoding="utf-8")
        (root / "input").mkdir()
        (root / "input" / "business.md").write_text("noise\n", encoding="utf-8")

        out = root / "merged.txt"
        report = build_snapshot(root, out)

        merged = {p for p, _ in report["merged_entries"]}  # type: ignore[union-attr]
        skipped = dict(report["skipped_entries"])  # type: ignore[arg-type]

        checks = [
            (".env" not in merged, "SEC .env excluded"),
            (".env.example" in merged, "SEC .env.example included"),
            ("app.min.js" not in merged, "SEC foo.min.js excluded"),
            ("ok.py" in merged, "SEC foo.py included"),
            (
                "leak.txt" not in merged
                and "possible embedded secret detected" in skipped.get("leak.txt", ""),
                "SEC API-key text security blocked",
            ),
            ("output/snapshot.txt" not in merged, "SEC output snapshot excluded"),
            ("input/business.md" not in merged, "SEC input dir excluded"),
            ("docs/safe.txt" in merged, "SEC sk- instruction text not blocked"),
            (not report["read_failures"], "SEC read failures = 0"),
        ]

        all_pass = True
        for ok, name in checks:
            print(("PASS " if ok else "FAIL ") + name)
            all_pass = all_pass and ok
        return 0 if all_pass else 1


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Project snapshot generator")
    parser.add_argument("--root", default=".", help="Project root to scan")
    parser.add_argument(
        "--output",
        default="merged_code_MDC.txt",
        help="Output snapshot path",
    )
    parser.add_argument("--self-test", action="store_true", help="Run minimal self-test")
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()

    report = build_snapshot(Path(args.root), Path(args.output))
    print_report(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
