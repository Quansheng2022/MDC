"""
Golden 环境契约测试（R2）。

Golden 是 Required Release Suite：环境不满足时必须 FAIL，不允许 SKIP。
"""

from md_converter.tests.golden_environment import inspect_golden_environment


def test_canonical_golden_environment() -> None:
    """Canonical Golden 环境：Playwright 包可用 + Chromium 可 headless launch。"""
    status = inspect_golden_environment()

    assert status.playwright_installed, (
        "Playwright package not installed. " 'Run: pip install -e ".[mermaid]"'
    )
    assert status.chromium_launchable, (
        f"Chromium cannot launch: {status.chromium_error}. "
        "Run: python -m playwright install chromium"
    )
    assert status.backend == "playwright"
    assert status.canonical is True
