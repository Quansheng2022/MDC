#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MD Converter - Setup Script

Markdown to DOCX Converter with compiler architecture.
"""

import os
import sys
from setuptools import setup, find_packages

# ============================================================
# 版本信息
# ============================================================

VERSION = "1.0.0"
PACKAGE_NAME = "md_converter"
AUTHOR = "MD Converter Team"
AUTHOR_EMAIL = "support@mdconverter.io"
DESCRIPTION = "A production-grade Markdown to DOCX compiler with immutable AST, pipeline, and plugin support"
LICENSE = "MIT"
PYTHON_REQUIRES = ">=3.8"

# ============================================================
# 读取 README
# ============================================================

try:
    with open("README.md", "r", encoding="utf-8") as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = DESCRIPTION

# ============================================================
# 依赖配置
# ============================================================

INSTALL_REQUIRES = [
    "pypandoc>=1.5",
    "python-docx>=0.8.10",
    "pyyaml>=5.0",
    "markdown-it-py>=3.0.0",
    "click>=8.0.0",
    "typing-extensions>=4.0.0",
]

EXTRAS_REQUIRE = {
    # Windows COM automation (Word)
    "win32": [
        "pywin32>=300",
    ],
    # SVG rendering (choose one or more)
    "svg": [
        "cairosvg>=2.5.0",
        "wand>=0.6.0",
        "svglib>=1.5.0",
        "reportlab>=3.6.0",
    ],
    # Mermaid rendering
    "mermaid": [
        "playwright>=1.30.0",
    ],
    # Image processing
    "image": [
        "pillow>=9.0.0",
    ],
    # Development dependencies
    "dev": [
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
        "pytest-xdist>=3.0.0",
        "pytest-html>=3.0.0",
        "black>=23.0.0",
        "isort>=5.0.0",
        "mypy>=1.0.0",
        "flake8>=6.0.0",
        "pylint>=2.0.0",
        "pre-commit>=3.0.0",
        "setuptools>=61.0.0",
        "wheel>=0.40.0",
        "build>=0.10.0",
        "twine>=4.0.0",
        "types-pyyaml>=6.0.0",
        "types-python-docx>=1.0.0",
    ],
    # Documentation
    "docs": [
        "sphinx>=5.0.0",
        "sphinx-rtd-theme>=1.0.0",
        "sphinx-autodoc-typehints>=1.0.0",
        "myst-parser>=0.18.0",
    ],
    # Performance
    "perf": [
        "pytest-benchmark>=4.0.0",
        "memory-profiler>=0.60.0",
        "line-profiler>=4.0.0",
    ],
}

# 将所有 extras 合并到 "all"
EXTRAS_REQUIRE["all"] = []
for key, deps in EXTRAS_REQUIRE.items():
    if key not in ["all", "dev", "docs", "perf"]:
        EXTRAS_REQUIRE["all"].extend(deps)

# ============================================================
# 入口点配置
# ============================================================

ENTRY_POINTS = {
    "console_scripts": [
        "md-converter=md_converter.cli:main",
        "md-converter-check=md_converter.cli:check_dependencies",
    ],
    "md_converter.passes": [
        "normalize=md_converter.pipeline.passes.normalize_pass:NormalizePass",
        "diagram=md_converter.pipeline.passes.diagram_pass:DiagramPass",
    ],
    "md_converter.themes": [
        "default=md_converter.renderer.themes.default:DefaultTheme",
        "github=md_converter.renderer.themes.default:get_github_theme",
        "academic=md_converter.renderer.themes.default:get_academic_theme",
        "corporate=md_converter.renderer.themes.default:get_corporate_theme",
    ],
}

# ============================================================
# 包数据
# ============================================================

PACKAGE_DATA = {
    "md_converter": [
        "py.typed",
    ],
}

# ============================================================
# 分类信息
# ============================================================

CLASSIFIERS = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Intended Audience :: Information Technology",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Text Processing :: Markup :: Markdown",
    "Topic :: Office/Business :: Word Processors",
    "Topic :: Software Development :: Documentation",
]

# ============================================================
# Setup 配置
# ============================================================

setup(
    name=PACKAGE_NAME,
    version=VERSION,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    license=LICENSE,
    python_requires=PYTHON_REQUIRES,
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    packages=find_packages(
        where=".",
        exclude=[
            "tests",
            "tests.*",
            "docs",
            "docs.*",
            "examples",
            "examples.*",
            "scripts",
            "scripts.*",
            "*.egg-info",
            "*.egg-info.*",
            "__pycache__",
            "__pycache__.*",
        ],
    ),
    package_data=PACKAGE_DATA,
    entry_points=ENTRY_POINTS,
    include_package_data=True,
    zip_safe=False,
    platforms=["any"],
    classifiers=CLASSIFIERS,
    keywords=[
        "markdown",
        "docx",
        "converter",
        "compiler",
        "document",
        "word",
        "pandoc",
        "ast",
        "pipeline",
        "plugin",
    ],
    project_urls={
        "Bug Reports": "https://github.com/yourusername/md_converter/issues",
        "Source Code": "https://github.com/yourusername/md_converter",
        "Documentation": "https://github.com/yourusername/md_converter/wiki",
        "Changelog": "https://github.com/yourusername/md_converter/blob/main/CHANGELOG.md",
    },
)

# ============================================================
# 安装后信息
# ============================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  MD Converter Setup Complete")
    print("=" * 70)
    print(f"\nPackage: {PACKAGE_NAME} v{VERSION}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Install Path: {os.path.dirname(sys.executable)}")
    print("\nQuick Start:")
    print("  # Convert a Markdown file")
    print("  md-converter input.md --open")
    print("\n  # Check dependencies")
    print("  md-converter-check")
    print("\n  # Run tests")
    print("  pytest tests/")
    print("\n" + "=" * 70 + "\n")