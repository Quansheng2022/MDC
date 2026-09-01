"""
转换器基类

定义 Mermaid 转换器的统一接口与公共工具函数。
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Dict, Optional

from ..model import DiagramFeatures

BOX_DRAWING_RE = re.compile(r"[\u2500-\u257F\u2580-\u259F\u25A0-\u25FF\u2B00-\u2BFF]")


class BaseConverter(ABC):
    """
    Mermaid 转换器抽象基类。

    每个转换器负责一种 Mermaid 图表类型，输入特征分析结果，
    输出 Mermaid 代码字符串；不适用时返回 None。
    """

    diagram_type: str = "unknown"

    @abstractmethod
    def convert(self, features: DiagramFeatures) -> Optional[str]:
        """
        将特征转换为 Mermaid 代码。

        参数:
            features: ASCII 图特征

        返回:
            Optional[str]: Mermaid 代码；不适用时返回 None
        """
        raise NotImplementedError

    @classmethod
    def summarize(cls, mermaid: str) -> Dict[str, int]:
        """
        生成方案摘要（节点/边数量等）。

        参数:
            mermaid: Mermaid 代码

        返回:
            Dict[str, int]: 摘要信息
        """
        return {
            "lines": len(mermaid.splitlines()),
            "edges": len(re.findall(r"--|\.\.|->>|-->>", mermaid)),
            "nodes": len(re.findall(r"^\s*[A-Za-z_][\w]*\s*\[", mermaid, re.M)),
        }


def sanitize_label(text: str) -> str:
    """
    清理 Mermaid 标签文本。

    压缩换行与空白；框线字符（┌─│▼└ 等）在带引号的流程图标签中合法，
    保留不动（例如 "Block: Document │ Heading"）。\x00 占位符一并移除。
    """
    text = str(text or "").replace("\x00", "")
    return re.sub(r"\s+", " ", text).strip()


def strip_box_drawing(text: str) -> str:
    """
    去除框线/几何字符（用于未加引号的时序图 participant 标签与消息）。
    """
    text = str(text or "").replace("\x00", "")
    return BOX_DRAWING_RE.sub(" ", text)


def escape_mermaid_label(text: str) -> str:
    """
    清理并转义 Mermaid 标签中的特殊字符。

    适用于带引号的流程图/类图标签：
    - `"` 转义为 `#quot;`，否则会提前结束引用字符串
    - `` ` `` 转义为 `#96;`，否则触发词法错误
    - `#` 在引号内为合法字面量，无需转义
    - 换行先由 sanitize_label 压缩，避免语法错误

    参数:
        text: 原始文本

    返回:
        str: 适合放入方括号标签的文本
    """
    text = sanitize_label(text)
    return (
        text.replace("&", "&amp;")
        .replace('"', "#quot;")
        .replace("`", "#96;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def escape_mindmap_label(text: str) -> str:
    """
    转义思维导图标签中的特殊字符。

    mindmap 标签不使用引号包裹，`(`/`)`/`~` 会与形状语法冲突，
    需转义为字符实体；`#` 为合法字面量，无需转义。
    """
    text = sanitize_label(text)
    return (
        text.replace("&", "&amp;")
        .replace('"', "#quot;")
        .replace("`", "#96;")
        .replace("(", "#40;")
        .replace(")", "#41;")
        .replace("[", "#91;")
        .replace("]", "#93;")
        .replace("{", "#123;")
        .replace("}", "#125;")
        .replace("~", "#126;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def node_id(index: int) -> str:
    """生成稳定的节点 ID（A、B、…、Z、AA、AB…）。"""
    result = ""
    index += 1
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        result = chr(ord("A") + remainder) + result
    return result
