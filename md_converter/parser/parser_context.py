"""
Parser Context - 解析器上下文

提供解析器在解析过程中需要的所有上下文信息，
包括诊断收集器、配置、Frontmatter 等。
使用数据类封装，便于传递和扩展。
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from ..diagnostics.collector import DiagnosticCollector


@dataclass
class ParserContext:
    """
    解析器上下文。

    封装解析过程中需要的所有外部依赖和状态信息。
    采用依赖注入方式，便于测试和扩展。

    属性:
        diag: 诊断收集器
        config: 配置字典
        frontmatter: Frontmatter 元数据
        source_file: 源文件路径（可选）
        source_text: 源文本内容（可选）
        custom_data: 自定义数据存储
    """

    # 核心组件
    diag: DiagnosticCollector

    # 配置
    config: Dict[str, Any] = field(default_factory=dict)

    # Frontmatter 元数据
    frontmatter: Dict[str, Any] = field(default_factory=dict)

    # 源文件信息
    source_file: Optional[Path] = None
    source_text: Optional[str] = None

    # 自定义数据（用于扩展）
    custom_data: Dict[str, Any] = field(default_factory=dict)

    # 解析状态
    _parsed_blocks: int = 0
    _parsed_inlines: int = 0

    # ============================================================
    # 构造器
    # ============================================================

    @classmethod
    def create(
        cls,
        diag: Optional[DiagnosticCollector] = None,
        config: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> "ParserContext":
        """
        创建 ParserContext 的工厂方法。

        参数:
            diag: 诊断收集器，如果为 None 则创建新的
            config: 配置字典
            **kwargs: 其他属性

        返回:
            ParserContext: 上下文实例
        """
        if diag is None:
            diag = DiagnosticCollector()
        if config is None:
            config = {}

        return cls(
            diag=diag,
            config=config,
            **kwargs
        )

    @classmethod
    def from_file(
        cls,
        file_path: Path,
        diag: Optional[DiagnosticCollector] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> "ParserContext":
        """
        从文件创建解析器上下文。

        参数:
            file_path: 源文件路径
            diag: 诊断收集器
            config: 配置字典

        返回:
            ParserContext: 上下文实例
        """
        with open(file_path, "r", encoding="utf-8") as f:
            source_text = f.read()

        return cls.create(
            diag=diag,
            config=config,
            source_file=file_path,
            source_text=source_text
        )

    # ============================================================
    # 配置访问
    # ============================================================

    def get_config(
        self,
        key: str,
        default: Any = None
    ) -> Any:
        """
        获取配置值，支持点号分隔的嵌套键。

        参数:
            key: 键名，支持点号分隔
            default: 默认值

        返回:
            Any: 配置值

        示例:
            >>> ctx.get_config("output_dir", "output")
            'output'
            >>> ctx.get_config("theme.font_size", 12)
            12
        """
        keys = key.split(".")
        current = self.config
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        return current

    def set_config(self, key: str, value: Any) -> None:
        """
        设置配置值，支持点号分隔的嵌套键。

        参数:
            key: 键名，支持点号分隔
            value: 要设置的值
        """
        keys = key.split(".")
        current = self.config
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value

    # ============================================================
    # Frontmatter 访问
    # ============================================================

    def get_frontmatter(
        self,
        key: str,
        default: Any = None
    ) -> Any:
        """
        获取 Frontmatter 元数据。

        参数:
            key: 键名
            default: 默认值

        返回:
            Any: Frontmatter 值
        """
        return self.frontmatter.get(key, default)

    def set_frontmatter(self, key: str, value: Any) -> None:
        """
        设置 Frontmatter 元数据。

        参数:
            key: 键名
            value: 值
        """
        self.frontmatter[key] = value

    def has_frontmatter(self) -> bool:
        """
        检查是否有 Frontmatter 数据。

        返回:
            bool: 是否有 Frontmatter
        """
        return bool(self.frontmatter)

    # ============================================================
    # 诊断辅助
    # ============================================================

    def warning(
        self,
        message: str,
        code: str = "WARN000",
        location=None,
        suggestion: Optional[str] = None
    ) -> None:
        """
        记录警告诊断。

        参数:
            message: 警告消息
            code: 诊断代码
            location: 源码位置
            suggestion: 建议
        """
        self.diag.warning(message, code, location, suggestion)

    def error(
        self,
        message: str,
        code: str = "ERR000",
        location=None,
        suggestion: Optional[str] = None
    ) -> None:
        """
        记录错误诊断。

        参数:
            message: 错误消息
            code: 诊断代码
            location: 源码位置
            suggestion: 建议
        """
        self.diag.error(message, code, location, suggestion)

    def info(
        self,
        message: str,
        code: str = "INFO000",
        location=None,
        suggestion: Optional[str] = None
    ) -> None:
        """
        记录信息诊断。

        参数:
            message: 信息消息
            code: 诊断代码
            location: 源码位置
            suggestion: 建议
        """
        self.diag.info(message, code, location, suggestion)

    # ============================================================
    # 状态管理
    # ============================================================

    def increment_blocks(self, count: int = 1) -> None:
        """
        增加已解析块节点计数。

        参数:
            count: 增加数量
        """
        self._parsed_blocks += count

    def increment_inlines(self, count: int = 1) -> None:
        """
        增加已解析行内节点计数。

        参数:
            count: 增加数量
        """
        self._parsed_inlines += count

    def get_stats(self) -> Dict[str, int]:
        """
        获取解析统计信息。

        返回:
            Dict[str, int]: 统计信息
        """
        return {
            "blocks": self._parsed_blocks,
            "inlines": self._parsed_inlines,
        }

    def reset_stats(self) -> None:
        """重置解析统计信息"""
        self._parsed_blocks = 0
        self._parsed_inlines = 0

    # ============================================================
    # 自定义数据
    # ============================================================

    def get_custom(
        self,
        key: str,
        default: Any = None
    ) -> Any:
        """
        获取自定义数据。

        参数:
            key: 键名
            default: 默认值

        返回:
            Any: 自定义数据
        """
        return self.custom_data.get(key, default)

    def set_custom(self, key: str, value: Any) -> None:
        """
        设置自定义数据。

        参数:
            key: 键名
            value: 值
        """
        self.custom_data[key] = value

    def has_custom(self, key: str) -> bool:
        """
        检查是否有自定义数据。

        参数:
            key: 键名

        返回:
            bool: 是否有自定义数据
        """
        return key in self.custom_data

    # ============================================================
    # 复制和合并
    # ============================================================

    def copy(self) -> "ParserContext":
        """
        创建上下文的深拷贝。

        返回:
            ParserContext: 新的上下文实例
        """
        import copy
        return ParserContext(
            diag=self.diag,  # 共享诊断收集器
            config=copy.deepcopy(self.config),
            frontmatter=copy.deepcopy(self.frontmatter),
            source_file=self.source_file,
            source_text=self.source_text,
            custom_data=copy.deepcopy(self.custom_data),
            _parsed_blocks=self._parsed_blocks,
            _parsed_inlines=self._parsed_inlines,
        )

    def merge(self, other: "ParserContext") -> None:
        """
        合并另一个上下文的数据。

        参数:
            other: 要合并的上下文
        """
        # 合并配置（后者覆盖前者）
        self.config.update(other.config)

        # 合并 Frontmatter
        self.frontmatter.update(other.frontmatter)

        # 合并自定义数据
        self.custom_data.update(other.custom_data)

        # 合并统计信息
        self._parsed_blocks += other._parsed_blocks
        self._parsed_inlines += other._parsed_inlines

    # ============================================================
    # 魔法方法
    # ============================================================

    def __repr__(self) -> str:
        return (
            f"ParserContext("
            f"diag={self.diag}, "
            f"config={len(self.config)} keys, "
            f"frontmatter={len(self.frontmatter)} keys, "
            f"source_file={self.source_file})"
        )