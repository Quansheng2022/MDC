"""
转换方案选择器

支持自动优选（最高置信度）与交互式选择两种模式。
"""

from __future__ import annotations

from typing import Callable, Optional

from .model import ConversionPlan, ConversionScheme


def auto_select(plan: ConversionPlan) -> Optional[ConversionScheme]:
    """自动选择最高置信度方案（确定性）。"""
    return plan.best


def interactive_select(
    plan: ConversionPlan,
    prompt_fn: Optional[Callable[[str], str]] = None,
) -> Optional[ConversionScheme]:
    """
    交互式选择方案。

    参数:
        plan: 转换计划
        prompt_fn: 提示函数，接收提示文本返回用户输入；
                   默认使用内置 input()
    """
    if not plan.schemes:
        return None

    prompt_fn = prompt_fn or input
    print("\n[AsciiToMermaid] 检测到转换方案，请选择：")
    for i, scheme in enumerate(plan.schemes, start=1):
        summary = ", ".join(f"{k}={v}" for k, v in scheme.summary.items())
        print(
            f"  {i}. {scheme.diagram_type} "
            f"(置信度 {scheme.confidence:.2f})" + (f" [{summary}]" if summary else "")
        )

    while True:
        if len(plan.schemes) == 1:
            raw = prompt_fn("按回车接受推荐方案（或输入编号）：")
        else:
            raw = prompt_fn(f"选择方案 (1-{len(plan.schemes)})：")
        if not raw.strip():
            return plan.schemes[0]
        try:
            choice = int(raw.strip())
        except (TypeError, ValueError):
            continue
        if 1 <= choice <= len(plan.schemes):
            return plan.schemes[choice - 1]
