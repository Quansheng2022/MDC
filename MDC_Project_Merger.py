#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Project Merger - 项目级审查快照生成器

用途:
    为 Code Review / Architecture Review / Governance Review /
    Release Candidate Review 生成单一文本快照。

主要能力:
    1. 默认扫描整个 project root。
    2. 排除 .git / .venv / cache / input / input_test / output 等噪声目录。
    3. 排除 *.egg-info generated metadata。
    4. 排除 .env / .env.* / .npmrc / .pypirc 等敏感配置文件。
    5. 仅允许显式白名单中的安全 dotfile。
    6. 排除 *.min.js / *.min.css / binary / temp 等无价值文件。
    7. 排除历史 merged_code_*.txt，防止 snapshot 嵌套膨胀。
    8. 自动排除当前正在生成的 output snapshot。
    9. 对普通文本内容执行高置信度 Secret Scan。
   10. 命中 Secret 时 BLOCK 整个文件，只记录 pattern 名，不记录 Secret 值。
   11. 支持 UTF-8 / UTF-8-SIG / GB18030。
   12. 输出 Merge Report。
   13. 显式排除 Merged_Code/ 以及所有符号链接，防止审查快照越界/嵌套。
   14. 显式纳入 MANIFEST.in 等项目审查关键文件。
   15. 目录排除大小写不敏感，适配 Windows。
   16. 提供 --self-test 自测。

设计原则:
    - Fail safe for secrets.
    - Hidden files default deny.
    - Snapshot 不应包含业务输入和生成产物。
    - 不把这个工具发展成复杂 DLP/Governance subsystem。
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


# ==============================================================================
# 默认配置
# ==============================================================================

DEFAULT_PROJECT_ROOT = Path(
    r"C:\Users\Quansheng\Documents\projects\MD_Converter"
)

DEFAULT_OUTPUT_FILE = Path(
    r"C:\Users\Quansheng\Documents\projects"
    r"\MD_Converter\Merged_Code\merged_code_MDC.txt"
)

# 单个文本文件最大允许大小。
# 防止误把大型生成文本 / 数据 dump 合入快照。
MAX_FILE_SIZE_BYTES: Optional[int] = 5 * 1024 * 1024

TEXT_ENCODINGS = (
    "utf-8-sig",
    "utf-8",
    "gb18030",
)


# ==============================================================================
# 目录排除规则
# ==============================================================================

EXCLUDE_DIRS = {
    # Version control
    ".git",

    # Python virtual environments
    ".venv",
    "venv",
    "env",

    # Python caches
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".nox",
    ".eggs",

    # IDE / tools
    ".idea",
    ".vscode",
    ".codex",
    ".agents",

    # JS
    "node_modules",

    # Build / generated
    "build",
    "dist",
    "htmlcov",
    "merged_code",

    # Project runtime / business data
    "input",
    "input_test",
    "output",

    # Misc cache/temp
    ".cache",
}


def should_exclude_dir(path: Path) -> bool:
    """
    判断目录是否应该排除。

    规则:
        - 目录名匹配大小写不敏感。
        - *.egg-info 属于 setuptools generated metadata。
        - 所有符号链接目录默认拒绝，避免越过 project root。
    """

    path = Path(path)

    try:
        if path.is_symlink():
            return True
    except OSError:
        # 无法可靠判断目录属性时按 fail-safe 处理。
        return True

    name = path.name.casefold()
    excluded_dirs = {
        item.casefold()
        for item in EXCLUDE_DIRS
    }

    if name in excluded_dirs:
        return True

    if name.endswith(".egg-info"):
        return True

    return False


# ==============================================================================
# 文件白名单 / 黑名单
# ==============================================================================

TEXT_EXTENSIONS = {
    # Python / scripts
    ".py",
    ".pyi",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",

    # Other languages
    ".java",
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
    ".h",
    ".hpp",
    ".go",
    ".rs",
    ".rb",
    ".php",

    # Web
    ".html",
    ".htm",
    ".css",
    ".scss",
    ".less",

    # Config / structured text
    ".json",
    ".xml",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",

    # Documentation / text
    ".txt",
    ".md",
    ".rst",

    # Data useful for project review
    ".csv",
    ".tsv",

    # SQL
    ".sql",

    # Shell
    ".sh",
    ".bash",
    ".bat",
    ".cmd",
    ".ps1",

    # Lock
    ".lock",
}


# 安全的无扩展名 / dotfile。
# Hidden file 默认拒绝，只有这里的文件明确允许。
INCLUDE_FILENAMES = {
    "Dockerfile",
    "Makefile",
    "Procfile",
    "Pipfile",
    "MANIFEST.in",

    ".gitignore",
    ".gitattributes",
    ".editorconfig",
    ".flake8",
    ".coveragerc",

    # 仅允许模板，不允许实际 .env.*
    ".env.example",
    ".env.sample",
}


# 永远不能进入 AI Snapshot 的敏感文件。
SENSITIVE_FILENAMES = {
    ".env",
    ".npmrc",
    ".pypirc",

    "credentials.json",
    "credential.json",
    "secrets.json",
    "secret.json",

    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
}


# 文件名模式。
SENSITIVE_FILE_PATTERNS = {
    ".env.*",

    "*.pem",
    "*.key",
    "*.pfx",
    "*.p12",
    "*.jks",
    "*.keystore",

    "*credentials*.json",
    "*secrets*.json",
}


EXCLUDE_FILE_PATTERNS = {
    # Minified frontend assets
    "*.min.js",
    "*.min.css",

    # Logs / temp / backups
    "*.log",
    "*.tmp",
    "*.bak",
    "*.old",
    "*.swp",
    "*.swo",
    "~*",

    # Historical merged snapshots:
    # merged_code_MDC(7).txt / merged_code_MDC(8).txt / etc.
    "merged_code_*.txt",
}


EXCLUDE_EXTENSIONS = {
    # Python compiled
    ".pyc",
    ".pyo",
    ".pyd",

    # Native binaries
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".bin",

    # Image
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".ico",
    ".svg",
    ".webp",

    # Video
    ".mp4",
    ".avi",
    ".mov",
    ".mkv",
    ".webm",

    # Audio
    ".mp3",
    ".wav",
    ".flac",

    # Archives
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".xz",
    ".rar",
    ".7z",

    # Office / document binaries
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",

    # DB
    ".db",
    ".sqlite",
    ".sqlite3",
}


# ==============================================================================
# Secret Scan
# ==============================================================================

# 这里只检测高置信度 Secret。
# 不试图实现完整企业 DLP。
SECRET_PATTERNS = {
    "generic_api_key": re.compile(
        r"\bsk-[A-Za-z0-9_-]{20,}\b"
    ),
    "aws_access_key": re.compile(
        r"\bAKIA[0-9A-Z]{16}\b"
    ),
    "github_token": re.compile(
        r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"
    ),
    "private_key": re.compile(
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
    ),
}


# ==============================================================================
# 类型
# ==============================================================================

MergedEntry = Tuple[str, str]
SkippedEntry = Tuple[str, str]
ReadFailure = Tuple[str, str]


# ==============================================================================
# 基础工具函数
# ==============================================================================

def matches_any_pattern(
    filename: str,
    patterns: Iterable[str],
) -> bool:
    """大小写不敏感地匹配任一 fnmatch pattern。"""

    filename_lower = filename.lower()

    return any(
        fnmatch.fnmatch(
            filename_lower,
            pattern.lower(),
        )
        for pattern in patterns
    )


def detect_secrets(content: str) -> List[str]:
    """
    检测文本中的高置信度 credential。

    Returns:
        命中的 Secret pattern 名称。

    安全原则:
        绝不返回实际秘密值。
    """

    detected: List[str] = []

    for name, pattern in SECRET_PATTERNS.items():
        if pattern.search(content):
            detected.append(name)

    return detected


def is_sensitive_filename(filename: str) -> bool:
    """
    判断是否为敏感文件名。

    .env.example / .env.sample 属于安全模板，
    需要先于 .env.* pattern 放行。
    """

    if filename in INCLUDE_FILENAMES:
        return False

    if filename in SENSITIVE_FILENAMES:
        return True

    if matches_any_pattern(
        filename,
        SENSITIVE_FILE_PATTERNS,
    ):
        return True

    return False


def should_exclude_file(
    path: Path,
    output_path: Path,
) -> Tuple[bool, str]:
    """
    判断文件是否应该排除。

    Returns:
        (excluded, reason)
    """

    filename = path.name

    # ------------------------------------------------------------------
    # Symbolic link default deny
    # ------------------------------------------------------------------

    try:
        if path.is_symlink():
            return True, "symlink file excluded"
    except OSError:
        return True, "unable to verify symlink status; fail-safe excluded"

    # ------------------------------------------------------------------
    # 当前正在生成的 output snapshot
    # ------------------------------------------------------------------

    try:
        if path.resolve() == output_path.resolve():
            return True, "current output snapshot excluded"
    except OSError:
        pass

    # ------------------------------------------------------------------
    # 安全模板必须优先允许
    # ------------------------------------------------------------------

    if filename in INCLUDE_FILENAMES:
        return False, ""

    # ------------------------------------------------------------------
    # Sensitive filename
    # ------------------------------------------------------------------

    if is_sensitive_filename(filename):
        return True, "sensitive filename excluded"

    # ------------------------------------------------------------------
    # Historical snapshot / generated/noisy file
    # ------------------------------------------------------------------

    if matches_any_pattern(
        filename,
        EXCLUDE_FILE_PATTERNS,
    ):
        return True, "excluded filename pattern"

    # ------------------------------------------------------------------
    # Hidden file default deny
    # ------------------------------------------------------------------

    if filename.startswith("."):
        return True, "unapproved hidden file excluded"

    # ------------------------------------------------------------------
    # Extension
    # ------------------------------------------------------------------

    suffix = path.suffix.lower()

    if suffix in EXCLUDE_EXTENSIONS:
        return True, "binary/generated extension excluded"

    if suffix not in TEXT_EXTENSIONS:
        return True, "unsupported/non-text file skipped"

    return False, ""


# ==============================================================================
# 文本读取
# ==============================================================================

def read_text_file(
    path: Path,
) -> Tuple[
    Optional[str],
    Optional[str],
    Optional[str],
]:
    """
    使用有限编码集合安全读取文本。

    Returns:
        (content, encoding, error)
    """

    try:
        size = path.stat().st_size
    except OSError as exc:
        return None, None, f"stat failed: {exc}"

    if (
        MAX_FILE_SIZE_BYTES is not None
        and size > MAX_FILE_SIZE_BYTES
    ):
        return (
            None,
            None,
            (
                f"file too large: "
                f"{size:,} bytes > "
                f"{MAX_FILE_SIZE_BYTES:,} bytes"
            ),
        )

    decode_errors: List[str] = []

    for encoding in TEXT_ENCODINGS:
        try:
            content = path.read_text(
                encoding=encoding,
                errors="strict",
            )
            return content, encoding, None

        except UnicodeDecodeError as exc:
            decode_errors.append(
                f"{encoding}: {exc}"
            )

        except OSError as exc:
            return (
                None,
                None,
                f"read failed: {exc}",
            )

    return (
        None,
        None,
        (
            "encoding detection failed: "
            + " | ".join(decode_errors)
        ),
    )


# ==============================================================================
# Snapshot Builder
# ==============================================================================

def build_snapshot(
    root: Path,
    output_path: Path,
) -> Dict[str, object]:
    """
    将项目树转换成单一文本 Review Snapshot。

    Pipeline:

        directory filter
              ↓
        filename filter
              ↓
        text read
              ↓
        content secret scan
              ↓
        merge / block
              ↓
        snapshot + audit report
    """

    root = Path(root).resolve()
    output_path = Path(output_path).expanduser().absolute()

    merged_entries: List[MergedEntry] = []
    skipped_entries: List[SkippedEntry] = []
    read_failures: List[ReadFailure] = []

    files_visited = 0

    # ------------------------------------------------------------------
    # Scan
    # ------------------------------------------------------------------

    for dirpath, dirnames, filenames in os.walk(root):

        current_dir = Path(dirpath)

        dirnames[:] = sorted(
            [
                directory
                for directory in dirnames
                if not should_exclude_dir(
                    current_dir / directory
                )
            ],
            key=str.lower,
        )

        for filename in sorted(
            filenames,
            key=str.lower,
        ):
            files_visited += 1

            file_path = current_dir / filename

            try:
                rel_path = (
                    file_path
                    .relative_to(root)
                    .as_posix()
                )
            except ValueError:
                rel_path = os.path.relpath(
                    file_path,
                    root,
                ).replace("\\", "/")

            # ----------------------------------------------------------
            # Filename/path filtering
            # ----------------------------------------------------------

            excluded, reason = should_exclude_file(
                file_path,
                output_path,
            )

            if excluded:
                skipped_entries.append(
                    (
                        rel_path,
                        reason,
                    )
                )
                continue

            # ----------------------------------------------------------
            # Read
            # ----------------------------------------------------------

            content, encoding, error = read_text_file(
                file_path
            )

            if content is None:
                read_failures.append(
                    (
                        rel_path,
                        error or "unknown read error",
                    )
                )
                continue

            # ----------------------------------------------------------
            # Embedded Secret Scan
            # ----------------------------------------------------------

            secret_types = detect_secrets(content)

            if secret_types:
                # Fail safe:
                # BLOCK whole file.
                #
                # Never include match value.
                skipped_entries.append(
                    (
                        rel_path,
                        (
                            "possible embedded secret detected: "
                            + ", ".join(secret_types)
                        ),
                    )
                )
                continue

            # ----------------------------------------------------------
            # Safe to merge
            # ----------------------------------------------------------

            merged_entries.append(
                (
                    rel_path,
                    content,
                )
            )

    # Stable output.
    merged_entries.sort(
        key=lambda item: item[0].lower()
    )

    skipped_entries.sort(
        key=lambda item: item[0].lower()
    )

    read_failures.sort(
        key=lambda item: item[0].lower()
    )

    # ------------------------------------------------------------------
    # Snapshot text
    # ------------------------------------------------------------------

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    total_chars = sum(
        len(content)
        for _, content in merged_entries
    )

    parts: List[str] = [
        "PROJECT SNAPSHOT",
        "================",
        f"root: {root}",
        f"files visited: {files_visited}",
        f"merged files: {len(merged_entries)}",
        f"security/other skips: {len(skipped_entries)}",
        f"read failures: {len(read_failures)}",
        "",
    ]

    for rel_path, content in merged_entries:

        parts.append(
            f"===== FILE: {rel_path} ====="
        )

        parts.append(
            content.rstrip("\n")
        )

        parts.append("")

    # ------------------------------------------------------------------
    # Embedded audit report
    # ------------------------------------------------------------------

    parts.extend(
        [
            "",
            "=" * 80,
            "MERGE REPORT",
            "=" * 80,
            f"Files visited: {files_visited}",
            f"Merged successfully: {len(merged_entries)}",
            f"Security/other skips: {len(skipped_entries)}",
            f"Read failures: {len(read_failures)}",
            f"Total source characters: {total_chars:,}",
            "",
        ]
    )

    if skipped_entries:
        parts.append("Skipped entries:")

        for rel_path, reason in skipped_entries:
            parts.append(
                f"- {rel_path}: {reason}"
            )

    else:
        parts.append(
            "Skipped entries: NONE"
        )

    parts.append("")

    if read_failures:
        parts.append("Read failures:")

        for rel_path, error in read_failures:
            parts.append(
                f"- {rel_path}: {error}"
            )

    else:
        parts.append(
            "Read failures: NONE"
        )

    parts.append(
        "=" * 80
    )

    output_path.write_text(
        "\n".join(parts) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    # ------------------------------------------------------------------
    # Result
    # ------------------------------------------------------------------

    return {
        "root": str(root),
        "output": str(output_path),
        "files_visited": files_visited,
        "merged_count": len(merged_entries),
        "skipped_count": len(skipped_entries),
        "read_failure_count": len(read_failures),
        "total_chars": total_chars,
        "merged_entries": merged_entries,
        "skipped_entries": skipped_entries,
        "read_failures": read_failures,
    }


# ==============================================================================
# Report
# ==============================================================================

def calculate_sha256(path: Path) -> str:
    """计算 snapshot SHA256。"""

    digest = hashlib.sha256()

    with path.open("rb") as file_obj:
        while True:
            block = file_obj.read(
                1024 * 1024
            )

            if not block:
                break

            digest.update(block)

    return digest.hexdigest()


def format_file_size(size: int) -> str:
    """格式化文件大小。"""

    if size >= 1024 * 1024:
        return (
            f"{size / (1024 * 1024):.2f} MB"
        )

    if size >= 1024:
        return (
            f"{size / 1024:.2f} KB"
        )

    return f"{size} bytes"


def print_report(
    report: Dict[str, object],
) -> None:
    """
    输出报告。

    Security note:
        skipped reason 只能包含 pattern 名称，
        不允许包含实际 Secret。
    """

    print()
    print("=" * 80)
    print("PROJECT SNAPSHOT REPORT")
    print("=" * 80)

    print(
        f"Root: {report['root']}"
    )

    print(
        f"Output: {report['output']}"
    )

    print(
        f"Files visited: "
        f"{report['files_visited']}"
    )

    print(
        f"Merged files: "
        f"{report['merged_count']}"
    )

    print(
        f"Skipped entries: "
        f"{report['skipped_count']}"
    )

    print(
        f"Read failures: "
        f"{report['read_failure_count']}"
    )

    print(
        f"Source characters: "
        f"{report['total_chars']:,}"
    )

    skipped_entries = report[
        "skipped_entries"
    ]

    if skipped_entries:
        print()
        print("Skipped:")

        for rel_path, reason in skipped_entries:
            print(
                f"  SKIP {rel_path}: {reason}"
            )

    read_failures = report[
        "read_failures"
    ]

    if read_failures:
        print()
        print("Read failures:")

        for rel_path, error in read_failures:
            print(
                f"  FAIL {rel_path}: {error}"
            )

    output_path = Path(
        str(report["output"])
    )

    if output_path.exists():
        size = output_path.stat().st_size

        print()
        print(
            f"Output size: "
            f"{format_file_size(size)}"
        )

        print(
            f"SHA256: "
            f"{calculate_sha256(output_path)}"
        )

    print("=" * 80)


# ==============================================================================
# Self Test
# ==============================================================================

def _self_test_symlink_guard(
    root: Path,
    output_path: Path,
) -> bool:
    """
    验证 symlink fail-safe 分支。

    使用 mock 避免要求 Windows Developer Mode / 管理员权限
    才能创建真实 symlink。真实扫描路径仍由 Path.is_symlink()
    强制拒绝文件和目录符号链接。
    """

    from unittest.mock import patch

    candidate_file = root / "linked.md"
    candidate_dir = root / "linked_dir"

    with patch.object(
        Path,
        "is_symlink",
        return_value=True,
    ):
        excluded_file, reason = should_exclude_file(
            candidate_file,
            output_path,
        )
        excluded_dir = should_exclude_dir(
            candidate_dir
        )

    return (
        excluded_file
        and reason == "symlink file excluded"
        and excluded_dir
    )


def _self_test() -> int:
    """
    最小自测。

    覆盖:
        SEC-01  normal Python
        SEC-02  normal Markdown
        SEC-03  .env blocked
        SEC-04  .env.example allowed
        SEC-05  .env.local blocked
        SEC-06  .npmrc blocked
        SEC-07  minified JS blocked
        SEC-08  embedded API key blocked
        SEC-09  sk- instruction text allowed
        CLEAN-01 input excluded
        CLEAN-02 output excluded
        CLEAN-03 *.egg-info excluded
        CLEAN-04 historical merged snapshot excluded
        CLEAN-05 current output excluded
        CLEAN-06 Merged_Code directory excluded
        CLEAN-07 directory exclusion is case-insensitive
        COVER-01 MANIFEST.in included
        SEC-13 symlink file/directory default deny
        IO-01 read failures == 0
    """

    with tempfile.TemporaryDirectory(
        prefix="project_merger_selftest_"
    ) as tmp:

        root = Path(tmp)

        # --------------------------------------------------------------
        # Normal safe files
        # --------------------------------------------------------------

        (root / "ok.py").write_text(
            "x = 1\n",
            encoding="utf-8",
        )

        (root / "ok.md").write_text(
            "# Safe documentation\n",
            encoding="utf-8",
        )

        # --------------------------------------------------------------
        # Sensitive dotfiles
        # --------------------------------------------------------------

        (root / ".env").write_text(
            "TOKEN=abc\n",
            encoding="utf-8",
        )

        (root / ".env.local").write_text(
            "TOKEN=abc\n",
            encoding="utf-8",
        )

        (root / ".env.production").write_text(
            "TOKEN=abc\n",
            encoding="utf-8",
        )

        (root / ".npmrc").write_text(
            "token=abc\n",
            encoding="utf-8",
        )

        (root / ".pypirc").write_text(
            "password=abc\n",
            encoding="utf-8",
        )

        # Safe template
        (root / ".env.example").write_text(
            "TOKEN=\n",
            encoding="utf-8",
        )

        # --------------------------------------------------------------
        # Minified asset
        # --------------------------------------------------------------

        (root / "app.min.js").write_text(
            "var a=1;\n",
            encoding="utf-8",
        )

        (root / "style.min.css").write_text(
            "body{margin:0}",
            encoding="utf-8",
        )

        # --------------------------------------------------------------
        # Embedded secret
        # --------------------------------------------------------------

        (root / "leak.txt").write_text(
            "key=sk-" + "1" * 30 + "\n",
            encoding="utf-8",
        )

        # Safe instruction mentioning prefix only.
        docs = root / "docs"
        docs.mkdir()

        (
            docs / "safe.txt"
        ).write_text(
            "Enter API key (starts with sk-) here.\n",
            encoding="utf-8",
        )

        # --------------------------------------------------------------
        # Runtime / noise dirs
        # --------------------------------------------------------------

        input_dir = root / "input"
        input_dir.mkdir()

        (
            input_dir / "business.md"
        ).write_text(
            "noise\n",
            encoding="utf-8",
        )

        output_dir = root / "output"
        output_dir.mkdir()

        (
            output_dir / "generated.txt"
        ).write_text(
            "noise\n",
            encoding="utf-8",
        )

        merged_code_dir = root / "Merged_Code"
        merged_code_dir.mkdir()

        (
            merged_code_dir / "review_notes.txt"
        ).write_text(
            "generated review workspace\n",
            encoding="utf-8",
        )

        mixed_case_build = root / "Build"
        mixed_case_build.mkdir()

        (
            mixed_case_build / "noise.txt"
        ).write_text(
            "case-insensitive exclusion check\n",
            encoding="utf-8",
        )

        (root / "MANIFEST.in").write_text(
            "include README.md\n",
            encoding="utf-8",
        )

        egg_dir = root / "md_converter.egg-info"
        egg_dir.mkdir()

        (
            egg_dir / "SOURCES.txt"
        ).write_text(
            "generated metadata\n",
            encoding="utf-8",
        )

        # --------------------------------------------------------------
        # Historical snapshot
        # --------------------------------------------------------------

        (
            root / "merged_code_MDC(8).txt"
        ).write_text(
            "old snapshot\n",
            encoding="utf-8",
        )

        # --------------------------------------------------------------
        # Current output
        # --------------------------------------------------------------

        out = root / "merged_code_MDC.txt"

        report = build_snapshot(
            root,
            out,
        )

        merged = {
            path
            for path, _ in report[
                "merged_entries"
            ]
        }

        skipped = dict(
            report[
                "skipped_entries"
            ]
        )

        checks = [
            # Normal files
            (
                "ok.py" in merged,
                "SEC-01 normal Python included",
            ),
            (
                "ok.md" in merged,
                "SEC-02 normal Markdown included",
            ),

            # Dotfile security
            (
                ".env" not in merged,
                "SEC-03 .env excluded",
            ),
            (
                ".env.example" in merged,
                "SEC-04 .env.example included",
            ),
            (
                ".env.local" not in merged,
                "SEC-05 .env.local excluded",
            ),
            (
                ".env.production" not in merged,
                "SEC-06 .env.production excluded",
            ),
            (
                ".npmrc" not in merged,
                "SEC-07 .npmrc excluded",
            ),
            (
                ".pypirc" not in merged,
                "SEC-08 .pypirc excluded",
            ),

            # Minified
            (
                "app.min.js" not in merged,
                "SEC-09 minified JS excluded",
            ),
            (
                "style.min.css" not in merged,
                "SEC-10 minified CSS excluded",
            ),

            # Content secret
            (
                (
                    "leak.txt" not in merged
                    and "possible embedded secret detected"
                    in skipped.get(
                        "leak.txt",
                        "",
                    )
                ),
                "SEC-11 embedded API key blocked",
            ),

            # Safe prefix documentation
            (
                "docs/safe.txt" in merged,
                "SEC-12 sk- instruction text allowed",
            ),

            # Noise dirs
            (
                "input/business.md" not in merged,
                "CLEAN-01 input directory excluded",
            ),
            (
                "output/generated.txt" not in merged,
                "CLEAN-02 output directory excluded",
            ),
            (
                "md_converter.egg-info/SOURCES.txt"
                not in merged,
                "CLEAN-03 egg-info excluded",
            ),

            # Historical snapshot
            (
                "merged_code_MDC(8).txt"
                not in merged,
                "CLEAN-04 historical snapshot excluded",
            ),

            # Current output must not be included.
            (
                "merged_code_MDC.txt"
                not in merged,
                "CLEAN-05 current snapshot excluded",
            ),

            # Generated review workspace.
            (
                "Merged_Code/review_notes.txt"
                not in merged,
                "CLEAN-06 Merged_Code directory excluded",
            ),

            # Directory matching must be case-insensitive.
            (
                "Build/noise.txt"
                not in merged,
                "CLEAN-07 directory exclusion is case-insensitive",
            ),

            # Packaging review authority file.
            (
                "MANIFEST.in" in merged,
                "COVER-01 MANIFEST.in included",
            ),

            # Symlink guard.
            (
                _self_test_symlink_guard(root, out),
                "SEC-13 symlink file/directory default deny",
            ),

            # IO
            (
                not report["read_failures"],
                "IO-01 read failures = 0",
            ),
        ]

        all_pass = True

        print()
        print("=" * 80)
        print("PROJECT MERGER SELF TEST")
        print("=" * 80)

        for passed, name in checks:
            print(
                ("PASS " if passed else "FAIL ")
                + name
            )

            all_pass = (
                all_pass and passed
            )

        print("=" * 80)

        print(
            f"Result: "
            f"{sum(1 for ok, _ in checks if ok)}"
            f"/{len(checks)} passed"
        )

        if all_pass:
            print(
                "STATUS: PASS"
            )
            return 0

        print(
            "STATUS: FAIL"
        )
        return 1


# ==============================================================================
# CLI
# ==============================================================================

def main(
    argv: Optional[List[str]] = None,
) -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Generate a safe project-level "
            "review snapshot."
        )
    )

    parser.add_argument(
        "--root",
        default=str(
            DEFAULT_PROJECT_ROOT
        ),
        help="Project root to scan",
    )

    parser.add_argument(
        "--output",
        default=str(
            DEFAULT_OUTPUT_FILE
        ),
        help="Output snapshot path",
    )

    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run merger security/cleanliness self-test",
    )

    args = parser.parse_args(argv)

    # ------------------------------------------------------------------
    # Self-test
    # ------------------------------------------------------------------

    if args.self_test:
        return _self_test()

    root = Path(args.root)
    output_path = Path(args.output)

    # ------------------------------------------------------------------
    # Validate root
    # ------------------------------------------------------------------

    if not root.exists():
        print(
            f"ERROR: project root does not exist: "
            f"{root}",
            file=sys.stderr,
        )
        return 1

    if not root.is_dir():
        print(
            f"ERROR: project root is not a directory: "
            f"{root}",
            file=sys.stderr,
        )
        return 1

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    try:
        report = build_snapshot(
            root,
            output_path,
        )

    except Exception as exc:
        print(
            (
                "ERROR: snapshot generation failed: "
                f"{type(exc).__name__}: {exc}"
            ),
            file=sys.stderr,
        )
        return 1

    print_report(report)

    # Read failures should fail the merger command.
    if report["read_failure_count"]:
        print(
            "STATUS: FAILED "
            "(one or more eligible files could not be read)",
            file=sys.stderr,
        )
        return 1

    print()
    print("STATUS: SNAPSHOT GENERATED")
    return 0


if __name__ == "__main__":
    sys.exit(main())