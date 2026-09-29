"""TOC Heading Localization - 目录标题按文档语言本地化（THL）

**单一权威**：目录标题文本只在本模块决定。GUI、Presentation Profile、
Renderer、PostProcessor 与测试都不得重复该规则，只能调用本模块的函数。

冻结产品行为（仅“正向检测到中文内容”才使用中文标题）:

    English-only document            -> "Table of Contents"
    Chinese-only document            -> "目录"
    Chinese + English mixed document -> "目录"
    unknown / unreliable language    -> "Table of Contents"

判定输入是**可见文档文本**（由调用方提供，例如 PostProcessor 已持有的
python-docx 文档正文）。本模块只做确定性的纯函数判定：无 Qt、无 IO、
无网络、无全局可变状态、无第三方依赖。

已知局限（有意为之，见 THL 关闭证据）:
    仅以“是否出现汉字”判定中文，因此纯假名/纯谚文文档视为非中文，而含汉字的
    日文文档会得到中文标题。产品当前只要求中文/非中文二分，故不做更细的语言
    分类（避免引入文档语言分类子系统）。
"""

from __future__ import annotations

from typing import Optional

from .language_detection import contains_han_ideograph

__all__ = [
    "CHINESE_TOC_HEADING",
    "DEFAULT_TOC_HEADING",
    "toc_heading_for_document_text",
]

#: 默认目录标题：英文文档与任何无法可靠判定语言的文档。
DEFAULT_TOC_HEADING = "Table of Contents"

#: 正向检测到中文内容时使用的目录标题。
CHINESE_TOC_HEADING = "目录"


def toc_heading_for_document_text(text: Optional[str]) -> str:
    """返回与文档语言匹配的目录标题。

    参数:
        text: 可见文档文本（正文/标题/表格等）。``None``、空文本或不含汉字的
            文本都返回默认英文标题。

    返回:
        str: 检测到汉字时为 ``"目录"``，否则为 ``"Table of Contents"``。

    示例:
        >>> toc_heading_for_document_text("# Guide\\n\\nEnglish prose.")
        'Table of Contents'
        >>> toc_heading_for_document_text("# 标题\\n\\n正文内容。")
        '目录'
    """
    if text and contains_han_ideograph(text):
        return CHINESE_TOC_HEADING
    return DEFAULT_TOC_HEADING
