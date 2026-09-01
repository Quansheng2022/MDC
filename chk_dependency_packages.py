#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown to DOCX Converter - 依赖验证脚本 v6
修复:
- 使用 shutil.which() 检测 mmdc
- 更好的 PATH 检测
- 跨平台支持
"""

import importlib
import importlib.metadata
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# ============================================================
# 数据类型定义
# ============================================================


class PackageStatus(Enum):
    """包状态枚举"""

    OK = "[OK]"
    WARNING = "[WARN]"
    MISSING = "[MISS]"
    SKIP = "[SKIP]"
    UNKNOWN = "[UNK]"


@dataclass
class PackageInfo:
    """包信息"""

    name: str
    import_name: Optional[str]
    description: str
    install_cmd: str
    min_version: Optional[str] = None
    platform: Optional[str] = None
    priority: int = 99
    status: PackageStatus = PackageStatus.UNKNOWN
    installed_version: Optional[str] = None
    can_import: bool = False
    extra_info: str = ""
    dist_names: Tuple[str, ...] = ()


@dataclass
class ToolInfo:
    """工具信息"""

    name: str
    available: bool
    info: str
    install_cmd: Optional[str] = None


# ============================================================
# 配置
# ============================================================

REQUIRED_PACKAGES = [
    PackageInfo(
        name="pypandoc",
        import_name="pypandoc",
        min_version="1.5",
        description="Pandoc Python interface (pypandoc_binary bundles pandoc)",
        install_cmd="pip install pypandoc_binary",
        dist_names=("pypandoc_binary",),
    ),
    PackageInfo(
        name="python-docx",
        import_name="docx",
        min_version="0.8.10",
        description="Word document manipulation",
        install_cmd="pip install python-docx",
    ),
    PackageInfo(
        name="pyyaml",
        import_name="yaml",
        min_version="5.0",
        description="YAML Frontmatter parsing",
        install_cmd="pip install pyyaml",
    ),
    PackageInfo(
        name="pywin32",
        import_name="win32com",
        min_version="300",
        description="Windows COM (Word automation)",
        install_cmd="pip install pywin32",
        platform="win32",
    ),
]

OPTIONAL_PACKAGES = [
    PackageInfo(
        name="cairosvg",
        import_name=None,
        min_version="2.5.0",
        description="SVG->PNG conversion (requires Cairo library)",
        install_cmd="pip install cairosvg",
        priority=1,
    ),
    PackageInfo(
        name="wand",
        import_name="wand",
        min_version="0.6.0",
        description="ImageMagick interface (SVG->PNG)",
        install_cmd="pip install wand",
        priority=2,
    ),
    PackageInfo(
        name="svglib",
        import_name="svglib",
        min_version="1.5.0",
        description="Pure Python SVG processing",
        install_cmd="pip install svglib reportlab",
        priority=3,
    ),
    PackageInfo(
        name="playwright",
        import_name="playwright",
        min_version="1.30.0",
        description="Mermaid rendering (browser required)",
        install_cmd="pip install playwright && playwright install chromium",
        priority=4,
    ),
    PackageInfo(
        name="reportlab",
        import_name="reportlab",
        min_version="3.6.0",
        description="PDF generation (svglib dependency)",
        install_cmd="pip install reportlab",
        priority=5,
    ),
    PackageInfo(
        name="pillow",
        import_name="PIL",
        min_version="9.0.0",
        description="Image processing",
        install_cmd="pip install pillow",
        priority=6,
    ),
]


# ============================================================
# 开发工具包
# ============================================================

DEV_PACKAGES = [
    PackageInfo(
        name="pytest",
        import_name="pytest",
        min_version="7.0.0",
        description="Test framework",
        install_cmd="pip install pytest",
        priority=1,
    ),
    PackageInfo(
        name="pytest-cov",
        import_name="pytest_cov",
        min_version="4.0.0",
        description="Coverage plugin for pytest",
        install_cmd="pip install pytest-cov",
        priority=2,
    ),
    PackageInfo(
        name="black",
        import_name="black",
        min_version="23.0.0",
        description="Code formatter",
        install_cmd="pip install black",
        priority=3,
    ),
    PackageInfo(
        name="isort",
        import_name="isort",
        min_version="5.0.0",
        description="Import sorter",
        install_cmd="pip install isort",
        priority=4,
    ),
    PackageInfo(
        name="ruff",
        import_name="ruff",
        min_version="0.0.0",
        description="Linter",
        install_cmd="pip install ruff",
        priority=5,
    ),
    PackageInfo(
        name="mypy",
        import_name="mypy",
        min_version="1.0.0",
        description="Static type checker",
        install_cmd="pip install mypy",
        priority=6,
    ),
    PackageInfo(
        name="coverage",
        import_name="coverage",
        min_version="7.0.0",
        description="Code coverage measurement",
        install_cmd="pip install coverage",
        priority=7,
    ),
]


# ============================================================
# 工具函数
# ============================================================


def get_package_version(package_name: str, alt_names: Tuple[str, ...] = ()) -> Optional[str]:
    """获取包的版本号（支持多个发行名，例如 pypandoc / pypandoc_binary）"""
    for name in (package_name, *alt_names):
        try:
            return importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            continue
        except Exception:
            continue
    return None


def check_import(import_name: str) -> bool:
    """检查是否可以导入"""
    if not import_name:
        return False
    try:
        importlib.import_module(import_name)
        return True
    except ImportError:
        return False
    except Exception:
        return False


def check_cairosvg() -> Tuple[bool, str]:
    """检查 cairosvg 是否可用（做一次真实 SVG→PNG 转换测试）"""
    try:
        import cairosvg
    except ImportError:
        return False, "not installed"
    except Exception as e:
        return False, f"installed but failed to import: {e}"

    if not hasattr(cairosvg, "svg2png"):
        return False, "svg2png function not available"

    # 实际转换测试（比单纯 import 更能反映 Cairo 库是否可用）
    try:
        png_data = cairosvg.svg2png(
            bytestring=b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"/>'
        )
        if png_data:
            return True, f"available (conversion OK, {len(png_data)} bytes)"
        return True, "available (conversion returned empty)"
    except Exception as e:
        if "cairo" in str(e).lower() or "library" in str(e).lower():
            return True, "installed but missing Cairo library"
        return False, f"conversion test failed: {e}"


def _mmdc_version_command(mmdc_path: str) -> List[str]:
    """构造 mmdc --version 命令（Windows 上 .cmd/.bat 需经 cmd /c 执行）"""
    if mmdc_path.lower().endswith((".cmd", ".bat")):
        return ["cmd", "/c", mmdc_path, "--version"]
    return [mmdc_path, "--version"]


def check_mmdc() -> Tuple[bool, str]:
    """检查 mermaid-cli 是否可用"""

    # 方法1: 使用 shutil.which (最可靠)
    mmdc_path = shutil.which("mmdc")
    if mmdc_path:
        try:
            result = subprocess.run(
                _mmdc_version_command(mmdc_path),
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0:
                version_line = (
                    result.stdout.split("\n")[0] if result.stdout else f"installed at {mmdc_path}"
                )
                return True, version_line
        except Exception:
            pass

    # 方法2: 尝试直接运行
    try:
        result = subprocess.run(
            ["mmdc", "--version"], capture_output=True, text=True, timeout=5, check=False
        )
        if result.returncode == 0:
            version_line = result.stdout.split("\n")[0] if result.stdout else "installed"
            return True, version_line
    except Exception:
        pass

    # 方法3: 手动查找 npm 全局路径
    npm_paths = [
        os.path.expandvars(r"%APPDATA%\npm"),
        os.path.expandvars(r"%LOCALAPPDATA%\npm"),
        os.path.expanduser(r"~\AppData\Roaming\npm"),
        os.path.expanduser(r"~\AppData\Local\npm"),
    ]
    exe_candidates = [".exe", ".cmd", ".bat", ""] if platform.system() == "Windows" else [""]

    for path in npm_paths:
        if os.path.exists(path):
            for exe_suffix in exe_candidates:
                mmdc_path = os.path.join(path, f"mmdc{exe_suffix}")
                if not os.path.exists(mmdc_path):
                    continue
                try:
                    result = subprocess.run(
                        _mmdc_version_command(mmdc_path),
                        capture_output=True,
                        text=True,
                        timeout=5,
                        check=False,
                    )
                    if result.returncode == 0:
                        version_line = (
                            result.stdout.split("\n")[0]
                            if result.stdout
                            else f"installed at {mmdc_path}"
                        )
                        return True, version_line
                except Exception:
                    pass

    # 方法4: 尝试通过 where (Windows) 或 which (Linux/Mac) 查找
    try:
        cmd = "where" if platform.system() == "Windows" else "which"
        result = subprocess.run(
            [cmd, "mmdc"], capture_output=True, text=True, timeout=3, check=False
        )
        if result.returncode == 0 and result.stdout.strip():
            mmdc_path = result.stdout.strip().split("\n")[0]
            if os.path.exists(mmdc_path):
                try:
                    result = subprocess.run(
                        _mmdc_version_command(mmdc_path),
                        capture_output=True,
                        text=True,
                        timeout=5,
                        check=False,
                    )
                    if result.returncode == 0:
                        version_line = (
                            result.stdout.split("\n")[0]
                            if result.stdout
                            else f"installed at {mmdc_path}"
                        )
                        return True, version_line
                except Exception:
                    pass
    except Exception:
        pass

    return False, "mmdc not installed or not in PATH"


def find_pandoc_path() -> Optional[str]:
    """查找 Pandoc 可执行文件路径"""
    # 1. 使用 shutil.which
    pandoc_path = shutil.which("pandoc")
    if pandoc_path:
        return pandoc_path

    # 2. 尝试从系统 PATH 查找
    pandoc_names = ["pandoc", "pandoc.exe"]
    for name in pandoc_names:
        try:
            result = subprocess.run(
                ["where" if platform.system() == "Windows" else "which", name],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split("\n")[0]
        except Exception:
            pass

    # 3. 常见安装路径
    common_paths = [
        r"C:\Program Files\Pandoc\pandoc.exe",
        r"C:\Program Files (x86)\Pandoc\pandoc.exe",
        os.path.expanduser(r"~\AppData\Local\Pandoc\pandoc.exe"),
        os.path.expanduser(r"~\AppData\Local\Programs\Pandoc\pandoc.exe"),
        "/usr/bin/pandoc",
        "/usr/local/bin/pandoc",
        "/opt/homebrew/bin/pandoc",
        os.path.expanduser("~/.local/bin/pandoc"),
    ]

    for path in common_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path

    # 4. 尝试使用 pypandoc 查找
    try:
        import pypandoc

        pandoc_path = pypandoc.get_pandoc_path()
        if pandoc_path and os.path.exists(pandoc_path):
            return pandoc_path
        # pypandoc_binary 在 Windows 上可能返回不带 .exe 的路径
        if platform.system() == "Windows" and pandoc_path and os.path.exists(pandoc_path + ".exe"):
            return pandoc_path + ".exe"
    except Exception:
        pass

    return None


def check_pandoc() -> Tuple[bool, str]:
    """检查 Pandoc 是否可用"""
    pandoc_path = find_pandoc_path()

    if not pandoc_path:
        return False, "Pandoc not found in PATH or common locations"

    try:
        result = subprocess.run(
            [pandoc_path, "--version"], capture_output=True, text=True, timeout=5, check=False
        )
        if result.returncode == 0:
            version_line = result.stdout.split("\n")[0] if result.stdout else "installed"
            return True, version_line
        return False, f"Pandoc execution failed: {result.stderr}"
    except Exception as e:
        return False, f"Pandoc check failed: {e}"


def check_word_available() -> Tuple[bool, str]:
    """检查 MS Word 是否可用"""
    if platform.system() != "Windows":
        return False, "only available on Windows"

    try:
        import win32com.client

        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        version = word.Version
        word.Quit()
        return True, f"Word {version} available"
    except ImportError:
        return False, "pywin32 not installed"
    except Exception as e:
        return False, f"Word not available: {e}"


def check_virtual_env() -> Tuple[bool, str]:
    """检查是否在虚拟环境中"""
    in_venv = sys.prefix != sys.base_prefix or os.environ.get("VIRTUAL_ENV") is not None
    if in_venv:
        return True, f"virtual environment: {sys.prefix}"
    return False, "system Python (recommend using virtual environment)"


# ============================================================
# 主验证类
# ============================================================


class DependencyChecker:
    """依赖检查器"""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.results: Dict[str, Any] = {
            "required": [],
            "optional": [],
            "dev": [],
            "tools": [],
            "summary": {
                "total_required": 0,
                "installed_required": 0,
                "total_optional": 0,
                "installed_optional": 0,
                "has_svg_converter": False,
                "has_mermaid_renderer": False,
                "has_word_automation": False,
                "cairo_needed": False,
            },
        }

    def check_required_packages(self) -> None:
        """检查必需包"""
        for pkg in REQUIRED_PACKAGES:
            if pkg.platform and pkg.platform != sys.platform:
                pkg.status = PackageStatus.SKIP
                pkg.extra_info = f"platform: {pkg.platform}"
                self.results["required"].append(pkg)
                continue

            pkg.installed_version = get_package_version(pkg.name, pkg.dist_names)
            pkg.can_import = check_import(pkg.import_name)

            if pkg.name == "pywin32" and pkg.can_import:
                try:
                    importlib.import_module("win32com")
                except Exception:
                    pkg.can_import = False

            if pkg.can_import:
                pkg.status = PackageStatus.OK
                if pkg.min_version and pkg.installed_version:
                    if self._version_compare(pkg.installed_version, pkg.min_version) < 0:
                        pkg.status = PackageStatus.WARNING
                        pkg.extra_info = f"version {pkg.installed_version} < {pkg.min_version}"
            else:
                pkg.status = PackageStatus.MISSING

            self.results["required"].append(pkg)

            if pkg.can_import:
                self.results["summary"]["installed_required"] += 1
            self.results["summary"]["total_required"] += 1

    def check_optional_packages(self) -> None:
        """检查可选包"""
        for pkg in OPTIONAL_PACKAGES:
            pkg.installed_version = get_package_version(pkg.name, pkg.dist_names)

            if pkg.name == "cairosvg":
                can_import, extra_info = check_cairosvg()
                pkg.can_import = can_import
                pkg.extra_info = extra_info
                if can_import and "missing Cairo" in extra_info:
                    pkg.status = PackageStatus.WARNING
                    self.results["summary"]["cairo_needed"] = True
                elif can_import:
                    pkg.status = PackageStatus.OK
                else:
                    pkg.status = PackageStatus.MISSING
            else:
                pkg.can_import = check_import(pkg.import_name)
                if pkg.can_import:
                    pkg.status = PackageStatus.OK
                    if pkg.min_version and pkg.installed_version:
                        if self._version_compare(pkg.installed_version, pkg.min_version) < 0:
                            pkg.status = PackageStatus.WARNING
                            pkg.extra_info = f"version {pkg.installed_version} < {pkg.min_version}"
                else:
                    pkg.status = PackageStatus.MISSING

            self.results["optional"].append(pkg)

            if pkg.can_import:
                self.results["summary"]["installed_optional"] += 1
                if pkg.name in ["cairosvg", "wand", "svglib"]:
                    if pkg.name == "cairosvg" and "missing Cairo" in pkg.extra_info:
                        self.results["summary"]["has_svg_converter"] = False
                    else:
                        self.results["summary"]["has_svg_converter"] = True
                if pkg.name == "playwright":
                    self.results["summary"]["has_mermaid_renderer"] = True
            self.results["summary"]["total_optional"] += 1

    def check_dev_packages(self) -> None:
        """检查开发工具包"""
        for pkg in DEV_PACKAGES:
            pkg.installed_version = get_package_version(pkg.name, pkg.dist_names)
            pkg.can_import = check_import(pkg.import_name)

            if pkg.can_import:
                pkg.status = PackageStatus.OK
            else:
                pkg.status = PackageStatus.MISSING

            self.results["dev"].append(pkg)

    def check_tools(self) -> None:
        """检查外部工具"""
        pandoc_ok, pandoc_info = check_pandoc()
        self.results["tools"].append(
            ToolInfo(
                name="Pandoc",
                available=pandoc_ok,
                info=pandoc_info,
                install_cmd="https://pandoc.org/installing.html",
            )
        )

        mmdc_ok, mmdc_info = check_mmdc()
        self.results["tools"].append(
            ToolInfo(
                name="mmdc",
                available=mmdc_ok,
                info=mmdc_info,
                install_cmd="npm install -g @mermaid-js/mermaid-cli",
            )
        )

        if platform.system() == "Windows":
            word_ok, word_info = check_word_available()
            self.results["tools"].append(
                ToolInfo(name="MS Word", available=word_ok, info=word_info)
            )
            if word_ok:
                self.results["summary"]["has_word_automation"] = True

        venv_ok, venv_info = check_virtual_env()
        self.results["tools"].append(
            ToolInfo(name="Virtual Env", available=venv_ok, info=venv_info)
        )

    def _version_compare(self, v1: str, v2: str) -> int:
        try:
            from packaging.version import parse

            return (parse(v1) > parse(v2)) - (parse(v1) < parse(v2))
        except Exception:
            return 0

    def print_report(self) -> None:
        print("\n" + "=" * 70)
        print("  Markdown to DOCX Converter - Dependency Check Report")
        print("=" * 70)

        print(f"\nPython: {sys.version.split()[0]}")
        print(f"Platform: {platform.system()} {platform.release()}")
        print(f"Path: {sys.prefix}")

        print("\n[Required Packages]:")
        print("-" * 70)
        for pkg in self.results["required"]:
            if pkg.status == PackageStatus.SKIP:
                continue
            version_str = pkg.installed_version or "not installed"
            status_char = pkg.status.value
            extra = f" ({pkg.extra_info})" if pkg.extra_info else ""
            print(f"  {status_char} {pkg.name:15} {version_str:15} - {pkg.description}{extra}")

        print("\n[Optional Packages]:")
        print("-" * 70)
        for pkg in self.results["optional"]:
            version_str = pkg.installed_version or "not installed"
            status_char = pkg.status.value
            priority_mark = " *" if pkg.priority <= 3 else ""
            extra = f" ({pkg.extra_info})" if pkg.extra_info else ""
            print(
                f"  {status_char} {pkg.name:15} {version_str:15} "
                f"- {pkg.description}{priority_mark}{extra}"
            )

        print("\n[Development Packages]:")
        print("-" * 70)
        for pkg in self.results["dev"]:
            version_str = pkg.installed_version or "not installed"
            status_char = pkg.status.value
            extra = f" ({pkg.extra_info})" if pkg.extra_info else ""
            print(f"  {status_char} {pkg.name:15} {version_str:15} - {pkg.description}{extra}")

        print("\n[External Tools]:")
        print("-" * 70)
        for tool in self.results["tools"]:
            status_char = "[OK]" if tool.available else "[MISS]"
            print(f"  {status_char} {tool.name:15} - {tool.info}")
            if not tool.available and tool.install_cmd:
                print(f"      Install: {tool.install_cmd}")

        print("\n" + "=" * 70)
        print("  Summary")
        print("=" * 70)

        req_total = self.results["summary"]["total_required"]
        req_installed = self.results["summary"]["installed_required"]

        print(f"\nRequired Packages: {req_installed}/{req_total} installed")

        if req_installed < req_total:
            print("\n[MISSING] Required packages, please install:")
            for pkg in self.results["required"]:
                if not pkg.can_import and pkg.status != PackageStatus.SKIP:
                    print(f"   {pkg.install_cmd}")
            print("\n[WARNING] Missing required packages, converter cannot run!")

        opt_total = self.results["summary"]["total_optional"]
        opt_installed = self.results["summary"]["installed_optional"]
        print(f"\nOptional Packages: {opt_installed}/{opt_total} installed")

        dev_total = len(self.results["dev"])
        dev_installed = sum(1 for p in self.results["dev"] if p.can_import)
        print(f"Development Packages: {dev_installed}/{dev_total} installed")

        svg_status = "[OK]" if self.results["summary"]["has_svg_converter"] else "[MISS]"
        print(f"\nSVG->PNG Conversion: {svg_status}")
        if self.results["summary"].get("cairo_needed", False):
            print("   [WARN] cairosvg installed but missing Cairo library")
            print("   Install Cairo library:")
            if platform.system() == "Windows":
                print("      pip install cairocffi")
                print(
                    "      or download: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer"
                )
            elif platform.system() == "Darwin":
                print("      brew install cairo")
            else:
                print("      sudo apt-get install libcairo2-dev")
                print("      or: conda install cairo -c conda-forge")
        no_svg_converter = not self.results["summary"]["has_svg_converter"] and not self.results[
            "summary"
        ].get("cairo_needed", False)
        if no_svg_converter:
            print("   Recommendation: pip install wand")
            print("   or: pip install svglib reportlab")

        mermaid_status = "[OK]" if self.results["summary"]["has_mermaid_renderer"] else "[MISS]"
        print(f"\nMermaid Rendering: {mermaid_status}")
        if not self.results["summary"]["has_mermaid_renderer"]:
            print("   Recommendation: npm install -g @mermaid-js/mermaid-cli")
            print("   or: pip install playwright && playwright install chromium")

        if platform.system() == "Windows":
            word_status = "[OK]" if self.results["summary"]["has_word_automation"] else "[MISS]"
            print(f"\nWord Automation: {word_status}")
            if not self.results["summary"]["has_word_automation"]:
                print("   Install: pip install pywin32")

        print("\n" + "=" * 70)

        if req_installed == req_total:
            print("[OK] All required packages installed, converter is ready")

            if self.results["summary"]["has_svg_converter"]:
                print("[OK] SVG->PNG converter available")
            elif self.results["summary"].get("cairo_needed", False):
                print("[WARN] cairosvg needs Cairo library")
            else:
                print("[WARN] Recommend installing SVG->PNG converter: pip install wand")

            pandoc_available = any(t.available for t in self.results["tools"] if t.name == "Pandoc")
            if pandoc_available:
                print("[OK] Pandoc available")
            else:
                print(
                    "[MISS] Pandoc not available, please install: https://pandoc.org/installing.html"
                )
        else:
            print("[MISS] Missing required packages, cannot run")

        print("=" * 70 + "\n")

    def run(self) -> bool:
        self.check_required_packages()
        self.check_optional_packages()
        self.check_dev_packages()
        self.check_tools()
        self.print_report()

        req_total = self.results["summary"]["total_required"]
        req_installed = self.results["summary"]["installed_required"]
        return req_installed == req_total


def main():
    try:
        checker = DependencyChecker()
        success = checker.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[WARN] User interrupted check")
        sys.exit(1)
    except Exception as e:
        print(f"\n[MISS] Check failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
