#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
collect_project_for_review.py

Collect MD_Converter review-relevant documents, core code, tests, and review
tooling into a deterministic text bundle.

The collector is intentionally read-only. It does not run tests, modify project
files, change governance state, or create Git commits/tags.

Profiles
--------
architecture
    Canonical / architecture / implementation documents + core implementation.
    Tests are OFF by default, but --include-tests can add them.

maintenance
    Recommended for P11 maintenance review. Includes architecture authority,
    P11 governance / maintenance packages, core implementation, tests, and
    tools/review. Tests are ON by default.

full
    Broad static review. Includes all supported root text files, project docs,
    governance, P11, core implementation, tests, and tools. Tests are ON.

lean
    Small context bundle: key root documents + core implementation only.
    Tests are OFF by default.

Examples
--------
python tools/review/collect_project_for_review.py --profile maintenance
python tools/review/collect_project_for_review.py --profile architecture --include-tests
python tools/review/collect_project_for_review.py --profile full --list-only
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import zipfile
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Sequence


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_MAX_FILE_SIZE = 1_000_000  # 1 MB per collected text file
DEFAULT_OUTPUT_DIR = "Review_Bundle"
DEFAULT_PROFILE = "maintenance"

TEXT_EXTENSIONS = {
    ".py",
    ".typed",
    ".md",
    ".txt",
    ".toml",
    ".yaml",
    ".yml",
    ".json",
    ".ini",
    ".cfg",
    ".ps1",
    ".bat",
    ".cmd",
    ".sh",
    ".xml",
    ".csv",
}

KEY_ROOT_FILES = {
    "CANONICAL_SPEC.md",
    "ARCHITECTURE.md",
    "IMPLEMENTATION_PLAN.md",
    "README.md",
    "AGENTS.md",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "requirements.txt",
    "MANIFEST.in",
    "REVIEW_TEMPLATE.md",
    "SPEC_CHANGELOG.md",
    "KNOWN_LIMITATIONS_v1.0.0.md",
    "RELEASE_NOTES_v1.0.0.md",
    "RELEASE_MANIFEST_v1.0.0.json",
}

DEFAULT_TEST_DIRS = (
    "tests",
    "md_converter/tests",
)

EXCLUDED_DIR_NAMES = {
    ".git",
    ".github",
    ".idea",
    ".vscode",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".hypothesis",
    ".tox",
    "node_modules",
    "build",
    "dist",
    "site",
    "htmlcov",
    "coverage",
    "output",
    "outputs",
    "input",
    "inputs",
    "tmp",
    "temp",
    "cache",
    "logs",
    "Log",
    "Merged_Code",
    "Review_Bundle",
}

EXCLUDED_FILE_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    "secrets.json",
    "credentials.json",
    "token.json",
    "id_rsa",
    "id_ed25519",
}

EXCLUDED_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".dll",
    ".exe",
    ".so",
    ".dylib",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".zip",
    ".7z",
    ".tar",
    ".gz",
    ".whl",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".svg",
    ".pdf",
    ".docx",
    ".xlsx",
    ".pptx",
}

GENERATED_NAME_PATTERNS = (
    re.compile(r"^merged[_-].*", re.IGNORECASE),
    re.compile(r".*review.*bundle.*", re.IGNORECASE),
    re.compile(r"^MDC_review_\d{8}_\d{6}.*", re.IGNORECASE),
)

# Conservative high-confidence secret patterns.
SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("OPENAI_STYLE_KEY", re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}\b")),
    ("GITHUB_TOKEN", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("AWS_ACCESS_KEY", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    (
        "BEARER_TOKEN",
        re.compile(
            r"(?i)(authorization\s*[:=]\s*bearer\s+)"
            r"([A-Za-z0-9._~+/=-]{20,})"
        ),
    ),
    (
        "GENERIC_API_KEY_ASSIGNMENT",
        re.compile(
            r"(?i)\b(api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token)"
            r"(\s*[:=]\s*[\"']?)"
            r"([A-Za-z0-9._~+/=-]{20,})"
        ),
    ),
)


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProfileSpec:
    description: str
    root_files: tuple[str, ...]
    directories: tuple[str, ...]
    tool_directories: tuple[str, ...]
    tests_default: bool
    all_root_text: bool = False
    all_docs: bool = False


PROFILES: dict[str, ProfileSpec] = {
    "lean": ProfileSpec(
        description=(
            "Small review context: key root authority/docs + md_converter core code."
        ),
        root_files=(
            "CANONICAL_SPEC.md",
            "IMPLEMENTATION_PLAN.md",
            "AGENTS.md",
            "pyproject.toml",
            "README.md",
        ),
        directories=("Doc", "md_converter"),
        tool_directories=(),
        tests_default=False,
    ),
    "architecture": ProfileSpec(
        description=(
            "Architecture/spec review: canonical authority, architecture/docs, "
            "governance context, and core implementation."
        ),
        root_files=tuple(sorted(KEY_ROOT_FILES)),
        directories=("Doc", "governance", "P11", "md_converter"),
        tool_directories=(),
        tests_default=False,
    ),
    "maintenance": ProfileSpec(
        description=(
            "P11 maintenance review: authority + P11 packages + core code + tests "
            "+ review tooling. Recommended during active maintenance."
        ),
        root_files=tuple(sorted(KEY_ROOT_FILES)),
        directories=("Doc", "governance", "P11", "md_converter"),
        tool_directories=("tools/review",),
        tests_default=True,
    ),
    "full": ProfileSpec(
        description=(
            "Broad static review: all supported root text files, project docs, "
            "governance, P11, core code, tests, and tools."
        ),
        root_files=tuple(sorted(KEY_ROOT_FILES)),
        directories=("Doc", "docs", "governance", "P11", "md_converter"),
        tool_directories=("tools",),
        tests_default=True,
        all_root_text=True,
        all_docs=True,
    ),
}


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CollectedFile:
    path: str
    category: str
    size_bytes: int
    sha256: str
    encoding: str
    line_count: int
    redactions: int


@dataclass(frozen=True)
class SkippedFile:
    path: str
    reason: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def is_generated_name(path: Path) -> bool:
    return any(pattern.fullmatch(path.name) for pattern in GENERATED_NAME_PATTERNS)


def should_exclude_path(
    path: Path,
    root: Path,
    output_dir: Path,
) -> tuple[bool, str]:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return True, "outside-project-root"

    if output_dir in path.parents or path == output_dir:
        return True, "review-output"

    if any(part in EXCLUDED_DIR_NAMES for part in rel.parts[:-1]):
        return True, "excluded-directory"

    if path.name in EXCLUDED_FILE_NAMES:
        return True, "sensitive-filename"

    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return True, "binary-or-excluded-suffix"

    if is_generated_name(path):
        return True, "generated-review-artifact"

    return False, ""


def is_supported_text_file(path: Path) -> bool:
    # Extensionless files such as LICENSE are allowed when explicitly selected.
    return path.suffix.lower() in TEXT_EXTENSIONS or path.suffix == ""


def read_text_file(path: Path) -> tuple[str, str]:
    data = path.read_bytes()

    for encoding in ("utf-8", "utf-8-sig"):
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            pass

    # Last resort: preserve review visibility without dropping the file.
    return data.decode("latin-1"), "latin-1-fallback"


def redact_secrets(text: str) -> tuple[str, int]:
    count = 0
    redacted = text

    for name, pattern in SECRET_PATTERNS:
        if name == "BEARER_TOKEN":
            def repl_bearer(match: re.Match[str]) -> str:
                nonlocal count
                count += 1
                return match.group(1) + f"<REDACTED:{name}>"

            redacted = pattern.sub(repl_bearer, redacted)

        elif name == "GENERIC_API_KEY_ASSIGNMENT":
            def repl_assignment(match: re.Match[str]) -> str:
                nonlocal count
                count += 1
                return (
                    match.group(1)
                    + match.group(2)
                    + f"<REDACTED:{name}>"
                )

            redacted = pattern.sub(repl_assignment, redacted)

        else:
            def repl_simple(
                _: re.Match[str],
                label: str = name,
            ) -> str:
                nonlocal count
                count += 1
                return f"<REDACTED:{label}>"

            redacted = pattern.sub(repl_simple, redacted)

    return redacted, count


def iter_files_under(
    base: Path,
    *,
    root: Path,
    output_dir: Path,
) -> Iterator[Path]:
    if not base.exists():
        return

    if base.is_file():
        excluded, _ = should_exclude_path(base, root, output_dir)
        if not excluded:
            yield base
        return

    for current_root, dirnames, filenames in os.walk(base):
        current = Path(current_root)

        dirnames[:] = sorted(
            dirname
            for dirname in dirnames
            if dirname not in EXCLUDED_DIR_NAMES
            and (current / dirname).resolve() != output_dir
        )

        for filename in sorted(filenames):
            path = current / filename
            excluded, _ = should_exclude_path(path, root, output_dir)
            if not excluded:
                yield path


def is_test_path(path: Path, root: Path) -> bool:
    parts = path.relative_to(root).parts
    return (
        "tests" in parts
        or path.name.startswith("test_")
        or path.name == "conftest.py"
    )


def classify_file(path: Path, root: Path) -> str:
    rel = path.relative_to(root)
    parts = rel.parts

    if is_test_path(path, root):
        return "tests"

    if parts and parts[0] == "md_converter":
        return "core-code"

    if parts and parts[0] == "P11":
        if "maintenance" in parts:
            return "maintenance-package"
        if "templates" in parts:
            return "maintenance-template"
        return "maintenance-governance"

    if len(parts) >= 2 and parts[0] == "tools" and parts[1] == "review":
        return "review-tooling"

    if parts and parts[0] == "tools":
        return "tooling"

    if parts and parts[0] in {"Doc", "docs", "governance"}:
        return "project-docs"

    if len(parts) == 1:
        if path.suffix.lower() in {".toml", ".cfg", ".ini"} or path.name in {
            "MANIFEST.in",
            "requirements.txt",
            "setup.py",
            "setup.cfg",
        }:
            return "build-metadata"
        return "root-docs"

    return "other"


def profile_tests_enabled(
    profile: ProfileSpec,
    include_tests: bool,
    exclude_tests: bool,
) -> bool:
    if include_tests:
        return True
    if exclude_tests:
        return False
    return profile.tests_default


def add_directory_files(
    candidates: set[Path],
    *,
    base: Path,
    root: Path,
    output_dir: Path,
    include_tests: bool,
    allow_all_docs: bool,
) -> None:
    if not base.exists():
        return

    for path in iter_files_under(base, root=root, output_dir=output_dir):
        if not include_tests and is_test_path(path, root):
            continue

        if allow_all_docs or is_supported_text_file(path):
            candidates.add(path)


def collect_candidates(
    root: Path,
    output_dir: Path,
    *,
    profile_name: str,
    include_tests_override: bool,
    exclude_tests_override: bool,
    include_all_docs_override: bool,
) -> tuple[list[Path], bool]:
    profile = PROFILES[profile_name]
    tests_enabled = profile_tests_enabled(
        profile,
        include_tests_override,
        exclude_tests_override,
    )
    candidates: set[Path] = set()

    # 1) Explicit root files.
    for name in profile.root_files:
        path = root / name
        if path.exists() and path.is_file():
            excluded, _ = should_exclude_path(path, root, output_dir)
            if not excluded:
                candidates.add(path)

    # 2) Full profile can add any supported root-level text files.
    if profile.all_root_text:
        for path in root.iterdir():
            if not path.is_file():
                continue
            excluded, _ = should_exclude_path(path, root, output_dir)
            if excluded:
                continue
            if is_supported_text_file(path):
                candidates.add(path)

    # 3) Profile directories.
    allow_all_docs = profile.all_docs or include_all_docs_override
    for dirname in profile.directories:
        base = root / dirname
        add_directory_files(
            candidates,
            base=base,
            root=root,
            output_dir=output_dir,
            include_tests=tests_enabled,
            allow_all_docs=allow_all_docs,
        )

    # 4) Tooling directories.
    for dirname in profile.tool_directories:
        base = root / dirname
        add_directory_files(
            candidates,
            base=base,
            root=root,
            output_dir=output_dir,
            include_tests=tests_enabled,
            allow_all_docs=False,
        )

    # 5) Explicit test roots ensure tests outside md_converter are not missed.
    if tests_enabled:
        for dirname in DEFAULT_TEST_DIRS:
            base = root / dirname
            add_directory_files(
                candidates,
                base=base,
                root=root,
                output_dir=output_dir,
                include_tests=True,
                allow_all_docs=False,
            )

    return (
        sorted(
            candidates,
            key=lambda path: path.relative_to(root).as_posix().lower(),
        ),
        tests_enabled,
    )


def write_bundle(
    root: Path,
    output_dir: Path,
    *,
    bundle_name: str,
    profile_name: str,
    include_tests_override: bool,
    exclude_tests_override: bool,
    include_all_docs_override: bool,
    max_file_size: int,
    create_zip: bool,
) -> tuple[Path, Path, Path | None]:
    output_dir.mkdir(parents=True, exist_ok=True)

    merged_path = output_dir / f"{bundle_name}.txt"
    manifest_path = output_dir / f"{bundle_name}.manifest.json"
    zip_path = output_dir / f"{bundle_name}.zip" if create_zip else None

    candidates, tests_enabled = collect_candidates(
        root,
        output_dir,
        profile_name=profile_name,
        include_tests_override=include_tests_override,
        exclude_tests_override=exclude_tests_override,
        include_all_docs_override=include_all_docs_override,
    )

    collected: list[CollectedFile] = []
    skipped: list[SkippedFile] = []
    merged_sections: list[str] = []

    for path in candidates:
        rel = path.relative_to(root).as_posix()

        excluded, reason = should_exclude_path(path, root, output_dir)
        if excluded:
            skipped.append(SkippedFile(rel, reason))
            continue

        try:
            size = path.stat().st_size
        except OSError as exc:
            skipped.append(SkippedFile(rel, f"stat-error: {exc}"))
            continue

        if size > max_file_size:
            skipped.append(
                SkippedFile(
                    rel,
                    f"file-too-large: {size} > {max_file_size}",
                )
            )
            continue

        try:
            source_bytes = path.read_bytes()
            text, encoding = read_text_file(path)
        except OSError as exc:
            skipped.append(SkippedFile(rel, f"read-error: {exc}"))
            continue

        redacted_text, redaction_count = redact_secrets(text)

        item = CollectedFile(
            path=rel,
            category=classify_file(path, root),
            size_bytes=len(source_bytes),
            sha256=sha256_bytes(source_bytes),
            encoding=encoding,
            line_count=redacted_text.count("\n") + (1 if redacted_text else 0),
            redactions=redaction_count,
        )
        collected.append(item)

        merged_sections.append(
            "\n".join(
                [
                    "=" * 100,
                    f"FILE: {rel}",
                    f"CATEGORY: {item.category}",
                    f"SIZE: {item.size_bytes} bytes",
                    f"SHA256: {item.sha256}",
                    f"ENCODING: {item.encoding}",
                    f"REDACTIONS: {item.redactions}",
                    "=" * 100,
                    redacted_text.rstrip("\n"),
                    f"--- END FILE: {rel} ---",
                    "",
                ]
            )
        )

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    category_counts = Counter(item.category for item in collected)

    header_lines = [
        "MD_CONVERTER PROJECT REVIEW BUNDLE",
        "=" * 100,
        f"Generated UTC: {now}",
        f"Project root: {root}",
        f"Profile: {profile_name}",
        f"Profile description: {PROFILES[profile_name].description}",
        f"Tests included: {tests_enabled}",
        f"Include-all-docs override: {include_all_docs_override}",
        f"Max file size: {max_file_size}",
        f"Collected files: {len(collected)}",
        f"Skipped files: {len(skipped)}",
        "",
        "Category counts:",
    ]
    for category, count in sorted(category_counts.items()):
        header_lines.append(f"  {category}: {count}")

    header_lines.extend(
        [
            "",
            "Purpose:",
            "  Produce one deterministic static review artifact containing the",
            "  authority/docs/code/tests/tooling selected by the chosen profile.",
            "",
            "Safety:",
            "  Common secret files are excluded and high-confidence secret values",
            "  are redacted from the merged review artifact.",
            "",
            "Important:",
            "  This collector does NOT execute pytest or prove runtime correctness.",
            "=" * 100,
            "",
        ]
    )

    merged_path.write_text(
        "\n".join(header_lines) + "\n".join(merged_sections),
        encoding="utf-8",
        newline="\n",
    )

    manifest = {
        "schema_version": 2,
        "generated_utc": now,
        "project_root": str(root),
        "bundle_name": bundle_name,
        "profile": profile_name,
        "profile_description": PROFILES[profile_name].description,
        "merged_file": merged_path.name,
        "tests_included": tests_enabled,
        "include_all_docs_override": include_all_docs_override,
        "max_file_size": max_file_size,
        "summary": {
            "collected_files": len(collected),
            "skipped_files": len(skipped),
            "total_source_bytes": sum(item.size_bytes for item in collected),
            "total_redactions": sum(item.redactions for item in collected),
            "category_counts": dict(sorted(category_counts.items())),
        },
        "files": [asdict(item) for item in collected],
        "skipped": [asdict(item) for item in skipped],
    }

    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )

    if zip_path is not None:
        with zipfile.ZipFile(
            zip_path,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as archive:
            archive.write(merged_path, arcname=merged_path.name)
            archive.write(manifest_path, arcname=manifest_path.name)

    return merged_path, manifest_path, zip_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def resolve_default_project_root() -> Path:
    """
    When stored at <PROJECT_ROOT>/tools/review/collect_project_for_review.py,
    parents[2] is PROJECT_ROOT. Otherwise fall back to cwd.
    """
    script_path = Path(__file__).resolve()

    try:
        candidate = script_path.parents[2]
    except IndexError:
        return Path.cwd().resolve()

    if (
        (candidate / "md_converter").exists()
        or (candidate / "CANONICAL_SPEC.md").exists()
    ):
        return candidate

    return Path.cwd().resolve()


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Collect MD_Converter documents, code, tests and review tooling "
            "into a deterministic static review bundle."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--project-root",
        type=Path,
        default=resolve_default_project_root(),
        help="Project root.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory; default is <project-root>/Review_Bundle.",
    )
    parser.add_argument(
        "--name",
        default=None,
        help="Bundle base name; timestamped name is used when omitted.",
    )
    parser.add_argument(
        "--profile",
        choices=tuple(PROFILES),
        default=DEFAULT_PROFILE,
        help="Collection profile.",
    )

    tests_group = parser.add_mutually_exclusive_group()
    tests_group.add_argument(
        "--include-tests",
        action="store_true",
        help="Force test collection ON, overriding the profile default.",
    )
    tests_group.add_argument(
        "--exclude-tests",
        action="store_true",
        help="Force test collection OFF, overriding the profile default.",
    )

    parser.add_argument(
        "--include-all-docs",
        action="store_true",
        help=(
            "Include all non-excluded files under profile document directories "
            "that pass safety filters."
        ),
    )
    parser.add_argument(
        "--max-file-size",
        type=int,
        default=DEFAULT_MAX_FILE_SIZE,
        help="Maximum bytes per collected text file.",
    )
    parser.add_argument(
        "--no-zip",
        action="store_true",
        help="Do not create the ZIP containing merged text + manifest.",
    )
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="Print selected files and exit without creating a bundle.",
    )
    parser.add_argument(
        "--show-profiles",
        action="store_true",
        help="Print profile definitions and exit.",
    )
    return parser.parse_args(argv)


def print_profiles() -> None:
    print("Available profiles:")
    for name, spec in PROFILES.items():
        print(f"\n{name}")
        print(f"  {spec.description}")
        print(f"  tests_default={spec.tests_default}")
        print(f"  directories={', '.join(spec.directories) or '-'}")
        print(f"  tooling={', '.join(spec.tool_directories) or '-'}")


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)

    if args.show_profiles:
        print_profiles()
        return 0

    root = args.project_root.resolve()
    if not root.exists() or not root.is_dir():
        print(
            "ERROR: project root does not exist or is not a directory: "
            f"{root}"
        )
        return 2

    output_dir = (
        args.output_dir.resolve()
        if args.output_dir is not None
        else (root / DEFAULT_OUTPUT_DIR).resolve()
    )

    if args.max_file_size <= 0:
        print("ERROR: --max-file-size must be > 0")
        return 2

    candidates, tests_enabled = collect_candidates(
        root,
        output_dir,
        profile_name=args.profile,
        include_tests_override=args.include_tests,
        exclude_tests_override=args.exclude_tests,
        include_all_docs_override=args.include_all_docs,
    )

    if args.list_only:
        print(f"Project root : {root}")
        print(f"Profile      : {args.profile}")
        print(f"Tests        : {tests_enabled}")
        print(f"Candidates   : {len(candidates)}")
        for path in candidates:
            print(path.relative_to(root).as_posix())
        return 0

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bundle_name = args.name or f"MDC_{args.profile}_review_{timestamp}"

    merged_path, manifest_path, zip_path = write_bundle(
        root,
        output_dir,
        bundle_name=bundle_name,
        profile_name=args.profile,
        include_tests_override=args.include_tests,
        exclude_tests_override=args.exclude_tests,
        include_all_docs_override=args.include_all_docs,
        max_file_size=args.max_file_size,
        create_zip=not args.no_zip,
    )

    print("=" * 80)
    print("MD_Converter review bundle created")
    print("=" * 80)
    print(f"Project root : {root}")
    print(f"Profile      : {args.profile}")
    print(f"Tests        : {tests_enabled}")
    print(f"Merged review: {merged_path}")
    print(f"Manifest     : {manifest_path}")
    if zip_path is not None:
        print(f"ZIP bundle   : {zip_path}")

    print("")
    print("Recommended current P11 review command:")
    print(
        f'  python "{Path(__file__).resolve()}" '
        f'--project-root "{root}" --profile maintenance'
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
