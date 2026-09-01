"""
Artifact Contract - 最终产物能力契约（P0-08 收口）

把“用户/配置显式要求的最终产物能力”固化为契约，FinalArtifactQA 依据契约
判断 required feature 缺失是 ERROR 还是可忽略，而不是猜测。

对应 CANONICAL_SPEC.md SPEC-QA-004 与 SPEC-INV-010。

F4：ArtifactContract 不定义默认值，只消费 resolved configuration；
默认值唯一来源是 config.DEFAULT_CONFIG。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class ArtifactContract:
    """
    最终产物能力契约。

    属性:
        cover_required: 封面页是否必需（enable_cover）
        toc_required: TOC 是否必需（toc）
        table_styling_required: 表格样式化是否必需（style_tables）

    C2：本契约不携带任何隐式默认值；``ArtifactContract()`` 必须失败
    （TypeError），只能通过 ``from_config(resolved_config)`` 构造。
    """

    cover_required: bool
    toc_required: bool
    table_styling_required: bool

    @classmethod
    def from_config(cls, config: Optional[Dict[str, Any]] = None) -> "ArtifactContract":
        """
        从 resolved configuration 构建契约。

        ArtifactContract 不拥有第二套默认值：必须提供已解析的完整配置
        （含 enable_cover / toc / style_tables 键），缺失即报错。

        参数:
            config: resolve_config() / load_config() 的完整结果

        异常:
            ValueError: 配置缺少必需键（不是 resolved configuration）
        """
        cfg: Dict[str, Any] = config or {}
        missing = [key for key in ("enable_cover", "toc", "style_tables") if key not in cfg]
        if missing:
            raise ValueError(
                "ArtifactContract.from_config requires resolved configuration; "
                f"missing keys: {', '.join(missing)}"
            )
        return cls(
            cover_required=bool(cfg["enable_cover"]),
            toc_required=bool(cfg["toc"]),
            table_styling_required=bool(cfg["style_tables"]),
        )
