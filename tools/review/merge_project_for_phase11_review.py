#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MD_Converter / MDC
Phase 11 Project File Merger for Review

Purpose
-------
Create a deterministic, review-friendly merged text snapshot for Phase 11
Maintenance governance / maintenance-package / patch-release review.

The tool is intentionally READ-ONLY with respect to project source files.
It never edits product code, Canonical authority, Golden baselines, Acceptance
baselines, Git tags, or release evidence.

Modes
-----
foundation   P11 governance foundation review (default)
maintenance  Review a specific/active maintenance implementation state
release      Review a candidate P11 patch-release state

Typical usage
-------------
python tools/review/merge_project_for_phase11_review.py

python tools/review/merge_project_for_phase11_review.py \
    --mode foundation \
    --run-pytest

python tools/review/merge_project_for_phase11_review.py \
    --mode maintenance \
    --output Merged_Code/merged_MDC_phase11_maintenance_review.txt

python tools/review/merge_project_for_phase11_review.py \
    --mode release \
    --run-pytest \
    --strict

Exit codes
----------
0  merge completed and required validations passed
1  merge completed but one or more required validations failed
2  invalid command usage / unrecoverable tool error

Design notes
------------
Phase 11 is Maintenance, not feature development. This merger therefore:
- records authority and Git baselines;
- protects secrets and binary/generated artifacts from being merged;
- preserves deterministic file ordering;
- includes SHA256 per merged file;
- does not silently mutate or normalize source files;
- can optionally run pytest, but test execution never changes merge scope.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence


TOOL_VERSION = "1.1.0"

EXPECTED_RELEASE_TAG = "v1.0.0"
EXPECTED_RELEASE_TAG_TARGET = "5d2c92a6af662ec8ee392f5a1a4d66f1f022229e"
EXPECTED_P10_CLOSURE_SHA = "dab9142f1ece898f7dcd66c2fe53d6106f59230c"

# P11 governance closure baselines. These identify governance commits; they do
# not change the immutable product release baseline above.
EXPECTED_P11_SPEC_VERSION = "1.0"
EXPECTED_P11_FREEZE_DATE = "2026-09-04"
EXPECTED_P11_FREEZE_SHA = "bddf36f0ae5667c485aca7cd7132a38d765eb5cc"
EXPECTED_P11_FOUNDATION_SHA = "617463ef0f412211e5bfad98c934d27b1d01895b"
EXPECTED_P11_CLOSURE_SHA = "76a3b52d8f68b970672990045757bd5164d59628"

# Common mojibake signatures seen when UTF-8 Chinese text is decoded/written
# through the wrong legacy code page. Authority documents are checked strictly.
MOJIBAKE_SIGNATURES = (
    "\ufffd",
    "Ã",
    "Â",
    "â€",
    "â†",
    "ï¼",
    "é¡",
    "å½",
    "ç»",
    "æœ",
    "è¿",
    "å†",
    "å¼",
    "ä¸",
    "æ­",
    "æŽ",
    "çš",
    "è¯",
)

PYTEST_FATAL_SIGNATURES = (
    "Windows fatal exception",
    "0x800706be",
    "0x800706ba",
)

DEFAULT_OUTPUT = {
    "foundation": "Merged_Code/merged_MDC_phase11_foundation_review.txt",
    "maintenance": "Merged_Code/merged_MDC_phase11_maintenance_review.txt",
    "release": "Merged_Code/merged_MDC_phase11_release_review.txt",
}

# Directories that should not be traversed for review snapshots.
EXCLUDED_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".nox",
    "node_modules",
    "dist",
    "build",
    "_build",
    "htmlcov",
    ".coverage",
    "site-packages",
}

# Large/generated/release-evidence folders are represented by metadata rather
# than recursively embedded unless explicitly selected by a named authority file.
EXCLUDED_PATH_PARTS = {
    "RC_EVIDENCE",
    "release_bundle",
    "release_bundles",
    "artifacts",
    "downloads",
    "tmp",
    "temp",
}

# Source-like files safe and useful for code/governance review.
TEXT_EXTENSIONS = {
    ".py",
    ".pyi",
    ".md",
    ".markdown",
    ".txt",
    ".rst",
    ".toml",
    ".ini",
    ".cfg",
    ".yaml",
    ".yml",
    ".json",
    ".jsonc",
    ".xml",
    ".ps1",
    ".psm1",
    ".bat",
    ".cmd",
    ".sh",
    ".sql",
    ".css",
    ".html",
    ".jinja",
    ".jinja2",
}

# Always-useful filenames even if they have no extension.
TEXT_FILENAMES = {
    "LICENSE",
    "NOTICE",
    "README",
    "CHANGELOG",
    "MANIFEST.in",
    "Makefile",
}

# Never merge credential / key material.
SECRET_NAME_PATTERNS = [
    re.compile(r"^\.env(?:\..+)?$", re.I),
    re.compile(r".*\.pem$", re.I),
    re.compile(r".*\.key$", re.I),
    re.compile(r".*\.pfx$", re.I),
    re.compile(r".*\.p12$", re.I),
    re.compile(r".*\.jks$", re.I),
    re.compile(r".*\.keystore$", re.I),
    re.compile(r".*credentials.*", re.I),
    re.compile(r".*secrets?.*", re.I),
    re.compile(r".*password.*", re.I),
    re.compile(r".*token.*", re.I),
]

# Review-oriented path priorities. The merger still walks the repository, but
# foundation mode uses a narrower inclusion policy than maintenance/release.
FOUNDATION_HINTS = (
    "CANONICAL_SPEC.md",
    "Phase_11_Maintenance_Specification.md",
    "Phase_11_Maintenance_Specification(1).md",
    "MDC_Project_Roadmap_Updates.md",
    "IMPLEMENTATION_PLAN.md",
    "pyproject.toml",
)

GOVERNANCE_KEYWORDS = (
    "adr",
    "architecture",
    "canonical",
    "governance",
    "implementation_plan",
    "maintenance",
    "phase_11",
    "phase11",
    "roadmap",
    "release",
    "known_limit",
    "install",
    "manifest",
)

SOURCE_ROOT_NAMES = {
    "src",
    "tests",
    "tools",
    "scripts",
    "docs",
    "adr",
    "architecture",
    "governance",
    "p11",
    "maintenance",
}

MAX_FILE_BYTES_DEFAULT = 2 * 1024 * 1024  # 2 MiB per text file


@dataclass
class Check:
    name: str
    status: str  # PASS / FAIL / WARN / INFO / SKIP
    detail: str

    @property
    def is_failure(self) -> bool:
        return self.status == "FAIL"


def eprint(*args: object) -> None:
    print(*args, file=sys.stderr)


def run_cmd(
    args: Sequence[str],
    cwd: Path,
    timeout: int = 120,
) -> tuple[int, str]:
    """Run a command without shell=True and return (rc, combined output)."""
    try:
        cp = subprocess.run(
            list(args),
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        return cp.returncode, cp.stdout.rstrip()
    except FileNotFoundError:
        return 127, f"command not found: {args[0]}"
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout or ""
        if isinstance(out, bytes):
            out = out.decode("utf-8", errors="replace")
        return 124, f"command timed out after {timeout}s\n{out}".rstrip()


def find_project_root(start: Path) -> Path:
    """
    Resolve project root.

    Priority:
      1. explicit --project-root is handled by caller;
      2. walk upward from CWD for .git or pyproject.toml;
      3. use current directory.
    """
    start = start.resolve()
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
        if (candidate / "pyproject.toml").exists():
            return candidate
    return start


def is_secret_path(path: Path) -> bool:
    name = path.name
    return any(p.fullmatch(name) or p.match(name) for p in SECRET_NAME_PATTERNS)


def has_excluded_dir(path: Path, root: Path) -> bool:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return True

    for part in rel.parts[:-1]:
        if part in EXCLUDED_DIR_NAMES:
            return True
        if part in EXCLUDED_PATH_PARTS:
            return True
    return False


def is_text_candidate(path: Path) -> bool:
    if path.name in TEXT_FILENAMES:
        return True
    return path.suffix.lower() in TEXT_EXTENSIONS


def contains_governance_keyword(path: Path, root: Path) -> bool:
    rel = path.relative_to(root).as_posix().lower()
    return any(k in rel for k in GOVERNANCE_KEYWORDS)


def top_level_component(path: Path, root: Path) -> str:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return ""
    return rel.parts[0].lower() if rel.parts else ""


def include_for_mode(path: Path, root: Path, mode: str) -> bool:
    """
    Decide whether a candidate text file belongs in the review snapshot.

    foundation:
      Governance / authority / roadmap / config / review tools.
      Product source is intentionally not bulk-merged.

    maintenance:
      Governance plus product source/tests/tools, suitable for a bounded patch review.

    release:
      Same as maintenance plus release documentation/configuration.
    """
    rel = path.relative_to(root).as_posix()
    rel_lower = rel.lower()
    name_lower = path.name.lower()
    top = top_level_component(path, root)

    if any(rel == hint for hint in FOUNDATION_HINTS):
        return True

    if mode == "foundation":
        if contains_governance_keyword(path, root):
            return True
        if top in {"docs", "adr", "architecture", "governance", "p11", "maintenance"}:
            return True
        if top in {"tools", "scripts"} and "review" in rel_lower:
            return True
        if name_lower in {
            "pyproject.toml",
            "pytest.ini",
            "tox.ini",
            "setup.cfg",
            "conftest.py",
            "requirements.txt",
            "requirements-dev.txt",
            "requirements-lock.txt",
        }:
            return True
        return False

    if mode in {"maintenance", "release"}:
        if top in SOURCE_ROOT_NAMES:
            return True
        if contains_governance_keyword(path, root):
            return True
        if name_lower in {
            "pyproject.toml",
            "pytest.ini",
            "tox.ini",
            "setup.cfg",
            "conftest.py",
            "requirements.txt",
            "requirements-dev.txt",
            "requirements-lock.txt",
            "manifest.in",
        }:
            return True
        if path.parent == root and is_text_candidate(path):
            return True

    return False


def enumerate_files(
    root: Path,
    mode: str,
    max_file_bytes: int,
) -> tuple[list[Path], list[tuple[str, str]]]:
    files: list[Path] = []
    skipped: list[tuple[str, str]] = []

    for current_root, dirnames, filenames in os.walk(root):
        current = Path(current_root)

        # Prune traversal early.
        dirnames[:] = sorted(
            d for d in dirnames
            if d not in EXCLUDED_DIR_NAMES and d not in EXCLUDED_PATH_PARTS
        )

        for filename in sorted(filenames):
            p = current / filename
            rel = p.relative_to(root).as_posix()

            if has_excluded_dir(p, root):
                skipped.append((rel, "excluded directory"))
                continue
            if is_secret_path(p):
                skipped.append((rel, "sensitive filename"))
                continue
            if not is_text_candidate(p):
                continue
            if not include_for_mode(p, root, mode):
                continue

            try:
                size = p.stat().st_size
            except OSError as exc:
                skipped.append((rel, f"stat failed: {exc}"))
                continue

            if size > max_file_bytes:
                skipped.append(
                    (rel, f"file too large ({size} bytes > {max_file_bytes})")
                )
                continue

            files.append(p)

    files.sort(key=lambda x: x.relative_to(root).as_posix().lower())
    return files, skipped


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_text_file(path: Path) -> tuple[str, bytes, str | None]:
    """
    Read raw bytes for hashing; decode text without modifying source.
    Returns (text, raw_bytes, warning).
    """
    raw = path.read_bytes()

    # BOM-aware UTF-8 first; then plain UTF-8; last-resort cp1252 to retain reviewability.
    for encoding in ("utf-8-sig", "utf-8"):
        try:
            return raw.decode(encoding), raw, None
        except UnicodeDecodeError:
            pass

    try:
        text = raw.decode("cp1252")
        return text, raw, "decoded with cp1252 fallback"
    except UnicodeDecodeError:
        text = raw.decode("utf-8", errors="replace")
        return text, raw, "undecodable bytes replaced with U+FFFD"



def read_utf8_strict(path: Path) -> tuple[str | None, str | None]:
    """Read an authority file as UTF-8/UTF-8-BOM only."""
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return None, f"read failed: {exc}"

    for encoding in ("utf-8-sig", "utf-8"):
        try:
            return raw.decode(encoding), None
        except UnicodeDecodeError:
            continue
    return None, "not valid UTF-8"


def mojibake_hits(text: str) -> list[str]:
    """Return detected mojibake markers, preserving deterministic order."""
    hits: list[str] = []
    for marker in MOJIBAKE_SIGNATURES:
        count = text.count(marker)
        if count:
            hits.append(f"{marker!r} x{count}")
    return hits


def authority_encoding_check(label: str, path: Path | None) -> Check:
    if path is None:
        return Check(label, "FAIL", "authority file NOT FOUND")
    text, error = read_utf8_strict(path)
    rel = path.as_posix()
    if error is not None or text is None:
        return Check(label, "FAIL", f"{rel}: {error}")
    hits = mojibake_hits(text)
    if hits:
        preview = ", ".join(hits[:8])
        if len(hits) > 8:
            preview += f", ... (+{len(hits) - 8} more markers)"
        return Check(label, "FAIL", f"{rel}: mojibake signatures detected: {preview}")
    return Check(label, "PASS", f"{rel}: valid UTF-8; mojibake signatures=0")


def git_commit_check(root: Path, label: str, sha: str) -> Check:
    rc, detail = run_cmd(["git", "cat-file", "-e", f"{sha}^{{commit}}"], root)
    if rc != 0:
        return Check(label, "FAIL", f"commit not found: {sha}\n{detail}".rstrip())
    rc, detail = run_cmd(["git", "merge-base", "--is-ancestor", sha, "HEAD"], root)
    if rc != 0:
        return Check(label, "FAIL", f"commit exists but is not an ancestor of HEAD: {sha}\n{detail}".rstrip())
    return Check(label, "PASS", sha)


def p11_authority_state_checks(root: Path, p11_spec: Path | None) -> list[Check]:
    checks: list[Check] = []
    if p11_spec is None:
        return [Check("P11 Authority state", "FAIL", "Phase 11 Maintenance Specification NOT FOUND")]

    text, error = read_utf8_strict(p11_spec)
    rel = p11_spec.relative_to(root).as_posix()
    if error is not None or text is None:
        return [Check("P11 Authority state", "FAIL", f"{rel}: {error}")]

    header = "\n".join(text.splitlines()[:80])
    if "DRAFT" in header.upper():
        checks.append(
            Check(
                "P11 Authority state",
                "FAIL",
                f"{rel}: header still declares DRAFT after Human Freeze",
            )
        )
    elif "FROZEN / ACTIVE" not in header.upper():
        checks.append(
            Check(
                "P11 Authority state",
                "FAIL",
                f"{rel}: header does not declare FROZEN / ACTIVE",
            )
        )
    else:
        checks.append(Check("P11 Authority state", "PASS", "FROZEN / ACTIVE"))

    # The spec header should no longer describe the Authority as only becoming
    # effective after a future Human Freeze once that Freeze has occurred.
    stale_fragments = (
        "READY FOR HUMAN REVIEW / FREEZE",
        "经 Human Freeze 后生效",
    )
    stale = [frag for frag in stale_fragments if frag in header]
    if stale:
        checks.append(
            Check(
                "P11 Authority header consistency",
                "WARN",
                f"stale pre-freeze wording remains: {', '.join(stale)}",
            )
        )
    else:
        checks.append(Check("P11 Authority header consistency", "PASS", "no stale pre-freeze wording"))

    return checks


def p11_governance_consistency_checks(root: Path) -> list[Check]:
    checks: list[Check] = []
    baseline = root / "P11" / "P11_GOVERNANCE_BASELINE.md"
    closure = root / "P11" / "evidence" / "P11-MNT-GOV-01" / "GOVERNANCE_CLOSURE.md"

    for label, path in (
        ("P11 Governance Baseline encoding", baseline),
        ("P11 Governance Closure encoding", closure),
    ):
        checks.append(authority_encoding_check(label, path if path.is_file() else None))

    if baseline.is_file():
        text, error = read_utf8_strict(baseline)
        if error is None and text is not None:
            required = {
                "P11 Authority Status": "FROZEN / ACTIVE",
                "Human Freeze": "APPROVED",
                "Freeze Date": EXPECTED_P11_FREEZE_DATE,
                "Freeze Commit": EXPECTED_P11_FREEZE_SHA,
            }
            missing = [f"{k}={v}" for k, v in required.items() if v not in text]
            checks.append(
                Check(
                    "P11 Governance Baseline state",
                    "PASS" if not missing else "FAIL",
                    "consistent" if not missing else "missing/incorrect: " + "; ".join(missing),
                )
            )
    else:
        checks.append(Check("P11 Governance Baseline state", "FAIL", baseline.as_posix() + " NOT FOUND"))

    if closure.is_file():
        text, error = read_utf8_strict(closure)
        if error is None and text is not None:
            required_values = (
                "FROZEN / ACTIVE",
                "APPROVED",
                EXPECTED_P11_FREEZE_DATE,
                EXPECTED_P11_FREEZE_SHA,
                EXPECTED_P11_FOUNDATION_SHA,
                "CLOSED / ACCEPTED",
                "P11 Program:\nACTIVE",
            )
            missing = [v for v in required_values if v not in text]
            checks.append(
                Check(
                    "P11 Governance Closure state",
                    "PASS" if not missing else "FAIL",
                    "consistent" if not missing else "missing/incorrect: " + "; ".join(missing),
                )
            )
    else:
        checks.append(Check("P11 Governance Closure state", "FAIL", closure.as_posix() + " NOT FOUND"))

    checks.extend(
        [
            git_commit_check(root, "P11 Authority Freeze commit", EXPECTED_P11_FREEZE_SHA),
            git_commit_check(root, "P11 Governance Foundation commit", EXPECTED_P11_FOUNDATION_SHA),
            git_commit_check(root, "P11 Governance Closure commit", EXPECTED_P11_CLOSURE_SHA),
        ]
    )
    return checks


def architecture_authority_checks(root: Path) -> list[Check]:
    checks: list[Check] = []
    preferred = root / "Doc" / "ARCHITECTURE.md"
    architecture = preferred if preferred.is_file() else locate_first(root, ["ARCHITECTURE.md"])
    if architecture is None:
        return [Check("ADR / architecture authority", "FAIL", "Doc/ARCHITECTURE.md NOT FOUND")]

    rel = architecture.relative_to(root).as_posix()
    checks.append(Check("ADR / architecture authority", "PASS", rel))
    checks.append(authority_encoding_check("Architecture authority encoding", architecture))

    text, error = read_utf8_strict(architecture)
    if error is None and text is not None:
        missing = [f"ADR-{i:03d}" for i in range(1, 10) if f"ADR-{i:03d}" not in text]
        checks.append(
            Check(
                "ADR-001..ADR-009 coverage",
                "PASS" if not missing else "FAIL",
                "ADR-001..ADR-009 located" if not missing else "missing: " + ", ".join(missing),
            )
        )
    return checks


def git_check(root: Path) -> list[Check]:
    checks: list[Check] = []

    rc, top = run_cmd(["git", "rev-parse", "--show-toplevel"], root)
    if rc != 0:
        return [Check("Git repository", "FAIL", top or "not a Git repository")]

    checks.append(Check("Git repository", "PASS", top))

    rc, status = run_cmd(["git", "status", "--short"], root)
    if rc == 0:
        checks.append(
            Check(
                "Working tree",
                "PASS" if not status.strip() else "WARN",
                "CLEAN" if not status.strip() else status,
            )
        )
    else:
        checks.append(Check("Working tree", "FAIL", status))

    rc, head = run_cmd(["git", "rev-parse", "HEAD"], root)
    checks.append(Check("HEAD", "PASS" if rc == 0 else "FAIL", head))

    rc, branch = run_cmd(["git", "branch", "--show-current"], root)
    checks.append(
        Check(
            "Current branch",
            "PASS" if rc == 0 else "WARN",
            branch or "(detached HEAD)",
        )
    )

    rc, tag_type = run_cmd(
        ["git", "cat-file", "-t", f"refs/tags/{EXPECTED_RELEASE_TAG}"], root
    )
    if rc != 0:
        checks.append(
            Check(
                "Release tag exists",
                "FAIL",
                f"{EXPECTED_RELEASE_TAG} not found",
            )
        )
    else:
        status = "PASS" if tag_type.strip() == "tag" else "FAIL"
        checks.append(
            Check(
                "Release tag annotated",
                status,
                f"{EXPECTED_RELEASE_TAG}: object type={tag_type.strip()}",
            )
        )

    rc, tag_target = run_cmd(
        ["git", "rev-list", "-n", "1", EXPECTED_RELEASE_TAG], root
    )
    if rc == 0:
        checks.append(
            Check(
                "Release tag target",
                "PASS"
                if tag_target.strip() == EXPECTED_RELEASE_TAG_TARGET
                else "FAIL",
                f"actual={tag_target.strip()} expected={EXPECTED_RELEASE_TAG_TARGET}",
            )
        )
    else:
        checks.append(Check("Release tag target", "FAIL", tag_target))

    rc, _ = run_cmd(
        ["git", "cat-file", "-e", f"{EXPECTED_P10_CLOSURE_SHA}^{{commit}}"], root
    )
    checks.append(
        Check(
            "P10 governance closure commit",
            "PASS" if rc == 0 else "FAIL",
            EXPECTED_P10_CLOSURE_SHA,
        )
    )

    return checks


def locate_first(root: Path, names: Sequence[str]) -> Path | None:
    for name in names:
        direct = root / name
        if direct.is_file():
            return direct

    # Narrow recursive search for authority documents.
    lowered = {n.lower() for n in names}
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.name.lower() in lowered:
            if not has_excluded_dir(p, root):
                return p
    return None


def structure_checks(root: Path, mode: str) -> list[Check]:
    checks: list[Check] = []

    canonical = locate_first(root, ["CANONICAL_SPEC.md"])
    p11_spec = locate_first(
        root,
        [
            "Phase_11_Maintenance_Specification.md",
            "Phase_11_Maintenance_Specification(1).md",
        ],
    )
    impl_plan = locate_first(root, ["IMPLEMENTATION_PLAN.md"])
    pyproject = locate_first(root, ["pyproject.toml"])

    required = [
        ("CANONICAL_SPEC.md", canonical),
        ("Phase 11 Maintenance Specification", p11_spec),
        ("IMPLEMENTATION_PLAN.md", impl_plan),
        ("pyproject.toml", pyproject),
    ]

    for label, path in required:
        checks.append(
            Check(
                label,
                "PASS" if path else "FAIL",
                path.relative_to(root).as_posix() if path else "NOT FOUND",
            )
        )

    # Encoding/authority checks are semantic gates, not mere existence checks.
    checks.append(authority_encoding_check("Canonical authority encoding", canonical))
    checks.append(authority_encoding_check("P11 Maintenance Authority encoding", p11_spec))
    checks.extend(p11_authority_state_checks(root, p11_spec))
    checks.extend(architecture_authority_checks(root))
    checks.extend(p11_governance_consistency_checks(root))

    governance_names = [
        "P11_GOVERNANCE_BASELINE.md",
        "P11_SCOPE_BASELINE.md",
        "P11_CLASSIFICATION_RULES.md",
        "P11_SEVERITY_RULES.md",
        "P11_TEST_MATRIX.md",
        "P11_GIT_CLOSURE_GATE.md",
        "P11_PATCH_RELEASE_GATE.md",
        "P11_P12_BOUNDARY.md",
        "P11_MAINTENANCE_REGISTRY.md",
    ]
    found_count = sum(1 for name in governance_names if locate_first(root, [name]))
    status = "PASS" if found_count == len(governance_names) else "WARN"
    checks.append(
        Check(
            "P11 governance artifact set",
            status,
            f"{found_count}/{len(governance_names)} conventional artifacts found",
        )
    )

    return checks

def pytest_run(root: Path, timeout: int) -> Check:
    rc, output = run_cmd(
        [sys.executable, "-m", "pytest"],
        root,
        timeout=timeout,
    )
    output = output or ""
    lower = output.lower()
    fatal_hits = [sig for sig in PYTEST_FATAL_SIGNATURES if sig.lower() in lower]

    if rc == 0 and fatal_hits:
        return Check(
            "Pytest",
            "WARN",
            output
            + "\n\nFATAL SIGNATURE DETECTED despite pytest rc=0: "
            + ", ".join(fatal_hits),
        )
    if rc == 0:
        return Check("Pytest", "PASS", output or "pytest exited 0")
    if rc == 5:
        return Check("Pytest", "WARN", output or "no tests collected")
    return Check("Pytest", "FAIL", output or f"pytest exited {rc}")

def format_checks(checks: Sequence[Check]) -> str:
    lines = []
    for c in checks:
        lines.append(f"[{c.status}] {c.name}")
        if c.detail:
            for line in c.detail.splitlines():
                lines.append(f"    {line}")
    return "\n".join(lines)


def file_manifest_rows(files: Sequence[Path], root: Path) -> list[tuple[str, int, str]]:
    rows = []
    for p in files:
        raw = p.read_bytes()
        rows.append(
            (
                p.relative_to(root).as_posix(),
                len(raw),
                sha256_bytes(raw),
            )
        )
    return rows


def render_header(
    root: Path,
    output: Path,
    mode: str,
    checks: Sequence[Check],
    files: Sequence[Path],
    skipped: Sequence[tuple[str, str]],
) -> str:
    timestamp = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

    manifest = file_manifest_rows(files, root)

    lines = [
        "=" * 100,
        "MDC / MD_Converter — PHASE 11 REVIEW MERGED SNAPSHOT",
        "=" * 100,
        f"Tool Version:        {TOOL_VERSION}",
        f"Generated At:        {timestamp}",
        f"Mode:                {mode}",
        f"Project Root:        {root}",
        f"Output:              {output}",
        f"Expected Release:    {EXPECTED_RELEASE_TAG}",
        f"Expected Release SHA:{EXPECTED_RELEASE_TAG_TARGET}",
        f"P10 Closure SHA:     {EXPECTED_P10_CLOSURE_SHA}",
        f"Merged File Count:   {len(files)}",
        f"Skipped File Count:  {len(skipped)}",
        "",
        "PHASE 11 REVIEW PRINCIPLES",
        "-" * 100,
        "1. Maintenance is subordinate to Canonical and frozen architecture authority.",
        "2. Foundation review must not authorize product-code modification.",
        "3. Default-deny scope: files outside an approved maintenance scope are not implicitly authorized.",
        "4. Golden / Acceptance baselines must not drift merely to make implementation tests pass.",
        "5. Feature / semantic / architecture evolution belongs to Phase 12.",
        "6. Git tag v1.0.0 is treated as immutable release baseline.",
        "",
        "VALIDATION SUMMARY",
        "-" * 100,
        format_checks(checks),
        "",
        "MERGED FILE MANIFEST",
        "-" * 100,
        "PATH | BYTES | SHA256",
    ]

    for rel, size, digest in manifest:
        lines.append(f"{rel} | {size} | {digest}")

    if skipped:
        lines.extend(
            [
                "",
                "SKIPPED / EXCLUDED REVIEW FILES",
                "-" * 100,
            ]
        )
        for rel, reason in skipped:
            lines.append(f"{rel} | {reason}")

    lines.extend(
        [
            "",
            "=" * 100,
            "BEGIN MERGED FILE CONTENT",
            "=" * 100,
            "",
        ]
    )
    return "\n".join(lines)


def append_file_section(
    out,
    path: Path,
    root: Path,
) -> None:
    rel = path.relative_to(root).as_posix()
    text, raw, warning = read_text_file(path)
    digest = sha256_bytes(raw)

    out.write("\n")
    out.write("=" * 100 + "\n")
    out.write(f"FILE: {rel}\n")
    out.write(f"SIZE: {len(raw)} bytes\n")
    out.write(f"SHA256: {digest}\n")
    if warning:
        out.write(f"READ WARNING: {warning}\n")
    out.write("=" * 100 + "\n")
    out.write(text)
    if not text.endswith("\n"):
        out.write("\n")
    out.write(f"--- END FILE: {rel} ---\n")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Merge MDC / MD_Converter Phase 11 review files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "--project-root",
        type=Path,
        help="Project root. If omitted, auto-detect from current directory.",
    )
    p.add_argument(
        "--output",
        type=Path,
        help="Output merged text file.",
    )
    p.add_argument(
        "--mode",
        choices=("foundation", "maintenance", "release"),
        default="foundation",
        help="P11 review mode.",
    )
    p.add_argument(
        "--run-pytest",
        action="store_true",
        help="Run full pytest and embed the result in validation summary.",
    )
    p.add_argument(
        "--pytest-timeout",
        type=int,
        default=900,
        help="Maximum seconds for pytest.",
    )
    p.add_argument(
        "--max-file-bytes",
        type=int,
        default=MAX_FILE_BYTES_DEFAULT,
        help="Maximum merged size for any single text file.",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Escalate dirty tree, incomplete governance, stale Authority wording, "
            "and pytest fatal/no-test warnings to failure."
        ),
    )
    p.add_argument(
        "--list-only",
        action="store_true",
        help="Print selected files without creating merged output.",
    )
    p.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {TOOL_VERSION}",
    )
    return p.parse_args(argv)


def apply_strict_policy(checks: list[Check], mode: str) -> None:
    """Escalate review warnings that are unacceptable for a strict final gate."""
    strict_warn_names = {
        "Working tree",
        "P11 governance artifact set",
        "P11 Authority header consistency",
        "Pytest",
    }
    for c in checks:
        if c.status == "WARN" and c.name in strict_warn_names:
            c.status = "FAIL"
            c.detail = "strict mode: warning escalated to failure\n" + c.detail

def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)

    root = (
        args.project_root.expanduser().resolve()
        if args.project_root
        else find_project_root(Path.cwd())
    )

    if not root.exists() or not root.is_dir():
        eprint(f"ERROR: project root does not exist or is not a directory: {root}")
        return 2

    if args.max_file_bytes < 1:
        eprint("ERROR: --max-file-bytes must be >= 1")
        return 2

    output = (
        args.output.expanduser()
        if args.output
        else Path(DEFAULT_OUTPUT[args.mode])
    )
    if not output.is_absolute():
        output = root / output
    output = output.resolve()

    print("=" * 80)
    print("MDC PHASE 11 REVIEW TOOL")
    print("=" * 80)
    print(f"Mode:         {args.mode}")
    print(f"Project root: {root}")
    print(f"Output:       {output}")
    print("=" * 80)

    checks: list[Check] = []
    checks.extend(git_check(root))
    checks.extend(structure_checks(root, args.mode))

    if args.run_pytest:
        print("Running pytest...")
        checks.append(pytest_run(root, args.pytest_timeout))
    else:
        checks.append(Check("Pytest", "SKIP", "--run-pytest not requested"))

    if args.strict:
        apply_strict_policy(checks, args.mode)

    files, skipped = enumerate_files(
        root=root,
        mode=args.mode,
        max_file_bytes=args.max_file_bytes,
    )

    # Prevent accidental self-inclusion if output is inside project and already exists.
    files = [p for p in files if p.resolve() != output]

    print()
    print("Validation:")
    print(format_checks(checks))
    print()
    print(f"Selected files: {len(files)}")
    for p in files:
        print(f"  {p.relative_to(root).as_posix()}")

    if args.list_only:
        print("\nList-only mode: no merged file created.")
        return 1 if any(c.is_failure for c in checks) else 0

    output.parent.mkdir(parents=True, exist_ok=True)

    try:
        with output.open("w", encoding="utf-8", newline="\n") as out:
            out.write(
                render_header(
                    root=root,
                    output=output,
                    mode=args.mode,
                    checks=checks,
                    files=files,
                    skipped=skipped,
                )
            )
            for p in files:
                append_file_section(out, p, root)

            out.write("\n")
            out.write("=" * 100 + "\n")
            out.write("END MERGED FILE CONTENT\n")
            out.write("=" * 100 + "\n")
    except OSError as exc:
        eprint(f"ERROR: failed to create merged output: {exc}")
        return 2

    print()
    print(f"Merged review snapshot created: {output}")
    print(f"Merged files: {len(files)}")
    print(f"Skipped/excluded files recorded: {len(skipped)}")

    failed = [c for c in checks if c.is_failure]
    if failed:
        print()
        print("RESULT: FAIL")
        print("One or more required validations failed.")
        return 1

    print()
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
