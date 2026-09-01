"""
Golden Environment Preflight（R2）

Runtime capability detection，与 Golden 的 result backend attribution
（test_golden.detect_mermaid_backend）是两个概念，不要混用：
    - inspect_golden_environment(): 真实检查 Playwright 包 + Chromium headless launch
    - detect_mermaid_backend(): 根据转换结果归属 backend

Golden 是 Mandatory Release Suite，环境不满足必须 FAIL，不允许 SKIP。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class GoldenEnvironmentStatus:
    """Golden 环境状态。"""

    playwright_installed: bool
    chromium_launchable: bool
    backend: str
    canonical: bool
    playwright_version: str = ""
    chromium_error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "playwright_installed": self.playwright_installed,
            "chromium_launchable": self.chromium_launchable,
            "backend": self.backend,
            "canonical": self.canonical,
            "playwright_version": self.playwright_version,
            "chromium_error": self.chromium_error,
            "mermaid_source": "jsdelivr",
            "mermaid_version": "10",
        }


def _playwright_version() -> str:
    try:
        from importlib.metadata import version

        return version("playwright")
    except Exception:
        return ""


def inspect_golden_environment() -> GoldenEnvironmentStatus:
    """
    检查 Golden 环境是否可用（实际 headless launch Chromium）。

    返回:
        GoldenEnvironmentStatus: 环境状态
    """
    try:
        import playwright  # noqa: F401

        installed = True
    except Exception:
        installed = False

    launchable = False
    chromium_error: Optional[str] = None
    if installed:
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                browser.close()
            launchable = True
        except Exception as e:
            chromium_error = str(e)

    canonical = installed and launchable
    backend = "playwright" if canonical else "fallback"
    return GoldenEnvironmentStatus(
        playwright_installed=installed,
        chromium_launchable=launchable,
        backend=backend,
        canonical=canonical,
        playwright_version=_playwright_version() if installed else "",
        chromium_error=chromium_error,
    )
