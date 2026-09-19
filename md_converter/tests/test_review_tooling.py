"""Focused regression tests for Phase 11 review tooling (P11-MNT-002)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MERGER_PATH = PROJECT_ROOT / "tools" / "review" / "merge_project_for_phase11_review.py"
COLLECTOR_PATH = PROJECT_ROOT / "tools" / "review" / "collect_project_for_review.py"
MAX_FILE_BYTES = 2 * 1024 * 1024


def _load_tool(module_name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


MERGER = _load_tool("mdc_phase11_review_merger", MERGER_PATH)
COLLECTOR = _load_tool("mdc_project_review_collector", COLLECTOR_PATH)


def _relative_paths(files: list[Path], root: Path) -> set[str]:
    return {path.relative_to(root).as_posix() for path in files}


def test_merger_excludes_generated_snapshot_locations(tmp_path: Path) -> None:
    (tmp_path / "Merged_Code").mkdir()
    (tmp_path / "Merged_Code" / "merged_MDC_phase11_maintenance_review.txt").write_text(
        "prior snapshot",
        encoding="utf-8",
    )
    (tmp_path / "Review_Bundle").mkdir()
    (tmp_path / "Review_Bundle" / "MDC_maintenance_review_20260919_155555.txt").write_text(
        "prior collector bundle",
        encoding="utf-8",
    )
    (tmp_path / "md_converter").mkdir()
    (tmp_path / "md_converter" / "core.py").write_text("VALUE = 1\n", encoding="utf-8")

    files, _ = MERGER.enumerate_files(
        root=tmp_path,
        mode="maintenance",
        max_file_bytes=MAX_FILE_BYTES,
    )
    rels = _relative_paths(files, tmp_path)

    assert "md_converter/core.py" in rels
    assert not any(rel.startswith("Merged_Code/") for rel in rels)
    assert not any(rel.startswith("Review_Bundle/") for rel in rels)


def test_merger_excludes_generated_snapshot_names_outside_conventional_dirs(
    tmp_path: Path,
) -> None:
    for name in (
        "merged_MDC_phase11_maintenance_review.txt",
        "MDC_maintenance_review_20260919_155555.txt",
        "MDC_maintenance_review_20260919_155555.manifest.json",
    ):
        (tmp_path / name).write_text("generated", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("project source", encoding="utf-8")

    files, _ = MERGER.enumerate_files(
        root=tmp_path,
        mode="maintenance",
        max_file_bytes=MAX_FILE_BYTES,
    )
    rels = _relative_paths(files, tmp_path)

    assert rels == {"notes.txt"}


def test_collector_maintenance_profile_includes_py_typed_and_tests() -> None:
    candidates, tests_enabled = COLLECTOR.collect_candidates(
        PROJECT_ROOT,
        PROJECT_ROOT / "Review_Bundle",
        profile_name="maintenance",
        include_tests_override=False,
        exclude_tests_override=False,
        include_all_docs_override=False,
    )
    rels = _relative_paths(candidates, PROJECT_ROOT)

    assert tests_enabled is True
    assert "md_converter/py.typed" in rels
    assert "md_converter/tests/test_word_com_final_artifact.py" in rels
    assert "tools/review/merge_project_for_phase11_review.py" in rels


def test_collector_exclude_tests_override_keeps_py_typed() -> None:
    candidates, tests_enabled = COLLECTOR.collect_candidates(
        PROJECT_ROOT,
        PROJECT_ROOT / "Review_Bundle",
        profile_name="maintenance",
        include_tests_override=False,
        exclude_tests_override=True,
        include_all_docs_override=False,
    )
    rels = _relative_paths(candidates, PROJECT_ROOT)

    assert tests_enabled is False
    assert "md_converter/py.typed" in rels
    assert "md_converter/tests/test_word_com_final_artifact.py" not in rels
