"""P10-PKG-01 metadata contract tests.

Guarantee that ``pyproject.toml`` is the single packaging authority and
that the wheel/sdist-facing metadata stays consistent with the README,
the package version, and the resources declared in package-data.
"""

import importlib
import json
import re
import sys
from pathlib import Path

import pytest

import md_converter

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = PROJECT_ROOT / "pyproject.toml"
SETUP_PY = PROJECT_ROOT / "setup.py"
MANIFEST_IN = PROJECT_ROOT / "MANIFEST.in"
README = PROJECT_ROOT / "README.md"
AGENTS = PROJECT_ROOT / "AGENTS.md"
RELEASE_MANIFEST = PROJECT_ROOT / "RELEASE_MANIFEST_v1.0.0.json"


def _load_pyproject() -> dict:
    """Read pyproject.toml using tomllib (Python 3.11+)."""
    if sys.version_info < (3, 11):
        pytest.skip("tomllib requires Python 3.11+")
    import tomllib

    with open(PYPROJECT, "rb") as fh:
        return tomllib.load(fh)


@pytest.fixture(scope="module")
def pyproject() -> dict:
    return _load_pyproject()


def _import_target(target: str) -> object:
    """Import an entry-point target like 'module.path:Attr'."""
    module_name, _, attr = target.rpartition(":")
    module = importlib.import_module(module_name)
    if not attr:
        return module
    return getattr(module, attr)


def test_pkg_single_packaging_authority() -> None:
    """PKG-META-01: pyproject.toml is the only packaging authority."""
    assert PYPROJECT.is_file()
    assert not SETUP_PY.exists(), "legacy setup.py must not reintroduce duplicate authority"


def test_pkg_core_metadata(pyproject: dict) -> None:
    """PKG-META-02: core [project] metadata is present and canonical."""
    project = pyproject["project"]
    assert project["name"] == "md_converter"
    assert project["version"] == "1.0.0"
    assert project["readme"] == "README.md"
    assert pyproject["build-system"]["build-backend"] == "setuptools.build_meta"


def test_pkg_version_consistency(pyproject: dict) -> None:
    """PKG-META-03: pyproject / __version__ / release manifest agree on 1.0.0."""
    assert pyproject["project"]["version"] == md_converter.__version__ == "1.0.0"
    manifest = json.loads(RELEASE_MANIFEST.read_text(encoding="utf-8"))
    assert manifest["release"] == "v1.0.0"


def test_pkg_scripts_contract(pyproject: dict) -> None:
    """PKG-META-04: all documented console scripts resolve to CLI callables."""
    expected = {
        "md-converter": "md_converter.cli:main",
        "md-converter-check": "md_converter.cli:check_dependencies",
        "md-converter-release-evidence": "md_converter.cli:release_evidence",
    }
    assert pyproject["project"]["scripts"] == expected
    for target in expected.values():
        assert callable(_import_target(target))


def test_pkg_passes_entry_points_resolve(pyproject: dict) -> None:
    """PKG-META-05: pipeline pass entry points match the registered passes."""
    passes_eps = pyproject["project"]["entry-points"]["md_converter.passes"]
    assert set(passes_eps) == {"normalize", "diagram"}
    assert passes_eps["normalize"] == ("md_converter.pipeline.passes.normalize_pass:NormalizePass")
    assert passes_eps["diagram"] == "md_converter.pipeline.passes.diagram_pass:DiagramPass"
    for target in passes_eps.values():
        _import_target(target)


def test_pkg_theme_entry_points_resolve(pyproject: dict) -> None:
    """PKG-META-06: theme entry points point at V1.5 default + legacy getters."""
    themes = pyproject["project"]["entry-points"]["md_converter.themes"]
    assert themes["default"] == "md_converter.renderer.themes.v15_theme:V15Theme"
    assert themes["v1_5"] == "md_converter.renderer.themes.v15_theme:V15Theme"
    assert themes["github"] == "md_converter.renderer.themes.default:get_github_theme"
    assert themes["academic"] == "md_converter.renderer.themes.default:get_academic_theme"
    assert themes["corporate"] == "md_converter.renderer.themes.default:get_corporate_theme"
    for target in themes.values():
        assert callable(_import_target(target))


def test_pkg_extras_contract(pyproject: dict) -> None:
    """PKG-META-07: extras are exactly windows / mermaid / dev with pins."""
    extras = pyproject["project"]["optional-dependencies"]
    assert set(extras) == {"dev", "mermaid", "windows"}
    assert "pywin32>=306" in extras["windows"]
    assert "playwright==1.62.0" in extras["mermaid"]


def test_pkg_dev_extra_covers_documented_tooling(pyproject: dict) -> None:
    """PKG-META-08: AGENTS.md's 'pip install -e .[dev]' workflow is real."""
    dev = pyproject["project"]["optional-dependencies"]["dev"]
    dev_names = {dep.partition(">=")[0].partition("[")[0].strip() for dep in dev}
    for name in ("black", "build", "isort", "mypy", "pytest", "pytest-cov", "ruff"):
        assert name in dev_names


def test_pkg_documented_extras_exist_in_metadata(pyproject: dict) -> None:
    """PKG-META-09: README/AGENTS extras claims are a subset of metadata."""
    documented = set(re.findall(r"\.\[([a-zA-Z0-9_-]+)\]", README.read_text(encoding="utf-8")))
    documented |= set(re.findall(r"\.\[([a-zA-Z0-9_-]+)\]", AGENTS.read_text(encoding="utf-8")))
    metadata = set(pyproject["project"]["optional-dependencies"])
    assert documented <= metadata
    assert {"dev", "mermaid", "windows"} <= documented


def test_pkg_readme_has_no_legacy_packaging_references() -> None:
    """PKG-META-10: README no longer directs users to setup.py or Pandoc."""
    text = README.read_text(encoding="utf-8")
    assert "setup.py" not in text
    assert "Pandoc" not in text
    assert "pandoc" not in text.lower()
    assert "[project.entry-points" in text


def test_pkg_package_data_covers_runtime_resources(pyproject: dict) -> None:
    """PKG-META-11: py.typed and the frozen theme YAML ship in the wheel."""
    pkg_data = pyproject["tool"]["setuptools"]["package-data"]["md_converter"]
    assert "py.typed" in pkg_data
    assert "renderer/themes/*.yaml" in pkg_data
    assert "themes/*.py" not in pkg_data
    assert (PROJECT_ROOT / "md_converter" / "py.typed").is_file()
    assert (PROJECT_ROOT / "md_converter" / "renderer" / "themes" / "default_v1_5.yaml").is_file()


def test_pkg_manifest_in_only_references_existing_paths() -> None:
    """PKG-META-12: MANIFEST.in must not reference files or dirs that do not exist."""
    assert MANIFEST_IN.is_file()
    for raw_line in MANIFEST_IN.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if parts[0] == "include":
            assert (
                PROJECT_ROOT / parts[1]
            ).is_file(), f"MANIFEST.in references missing file: {parts[1]}"
        elif parts[0] == "recursive-include":
            assert (
                PROJECT_ROOT / parts[1]
            ).is_dir(), f"MANIFEST.in references missing directory: {parts[1]}"
        else:
            raise AssertionError(f"Unsupported MANIFEST.in directive: {parts[0]}")


def test_pkg_classifier_claims_production_stable() -> None:
    """PKG-META-13: a v1.0.0 production release is not classified Beta."""
    classifiers = _load_pyproject()["project"]["classifiers"]
    assert "Development Status :: 5 - Production/Stable" in classifiers


def test_pkg_check_dependencies_command_runs() -> None:
    """PKG-META-14: the md-converter-check script target works end to end."""
    from click.testing import CliRunner

    from md_converter.cli import check_dependencies

    runner = CliRunner()
    result = runner.invoke(check_dependencies, ["--json-output"])
    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    assert report["ok"] is True
    assert {item["distribution"] for item in report["required"]} == {
        "click",
        "markdown-it-py",
        "python-docx",
        "pyyaml",
    }
