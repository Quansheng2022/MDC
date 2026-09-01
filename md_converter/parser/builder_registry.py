"""
Builder Registry - 类型安全的 Builder 注册和查找

提供基于 NodeType 枚举的类型安全 Builder 注册机制，
替代字符串键值的方式，避免拼写错误和类型不匹配。
"""

from typing import Dict, List, Optional, Set

from ..constants.node_type import NodeType
from .builders.base import BlockBuilder


class BuilderRegistry:
    """
    Builder 注册表 - 类型安全的注册和查找。

    使用 NodeType 枚举作为键，确保类型安全。
    支持注册、查找、批量注册和验证。

    属性:
        _builders: NodeType 到 BlockBuilder 的映射
        _aliases: 字符串别名到 NodeType 的映射（向后兼容）

    示例:
        >>> registry = BuilderRegistry()
        >>> registry.register(NodeType.HEADING, HeadingBuilder())
        >>> builder = registry.get(NodeType.HEADING)
        >>> if builder:
        ...     nodes = builder.build(node, ctx)
    """

    def __init__(self):
        """初始化注册表"""
        self._builders: Dict[NodeType, BlockBuilder] = {}
        self._aliases: Dict[str, NodeType] = {}
        self._registered_types: Set[NodeType] = set()

    # ============================================================
    # 核心方法
    # ============================================================

    def register(
        self,
        node_type: NodeType,
        builder: BlockBuilder,
        alias: Optional[str] = None
    ) -> None:
        """
        注册 Builder。

        参数:
            node_type: 节点类型枚举
            builder: Builder 实例
            alias: 可选的字符串别名（向后兼容）

        异常:
            ValueError: 如果 node_type 已经注册
        """
        if node_type in self._builders:
            raise ValueError(
                f"Builder for {node_type.name} already registered. "
                f"Use override=True to force replace."
            )

        self._builders[node_type] = builder
        self._registered_types.add(node_type)

        if alias:
            self._aliases[alias] = node_type

    def register_or_override(
        self,
        node_type: NodeType,
        builder: BlockBuilder,
        alias: Optional[str] = None
    ) -> None:
        """
        注册或覆盖 Builder。

        参数:
            node_type: 节点类型枚举
            builder: Builder 实例
            alias: 可选的字符串别名
        """
        self._builders[node_type] = builder
        self._registered_types.add(node_type)

        if alias:
            self._aliases[alias] = node_type

    def get(self, node_type: NodeType) -> Optional[BlockBuilder]:
        """
        获取 Builder。

        参数:
            node_type: 节点类型枚举

        返回:
            Optional[BlockBuilder]: Builder 实例，如果未找到则返回 None
        """
        return self._builders.get(node_type)

    def get_by_alias(self, alias: str) -> Optional[BlockBuilder]:
        """
        通过字符串别名获取 Builder。

        参数:
            alias: 字符串别名

        返回:
            Optional[BlockBuilder]: Builder 实例，如果未找到则返回 None
        """
        node_type = self._aliases.get(alias)
        if node_type:
            return self.get(node_type)
        return None

    def get_or_raise(self, node_type: NodeType) -> BlockBuilder:
        """
        获取 Builder，如果不存在则抛出异常。

        参数:
            node_type: 节点类型枚举

        返回:
            BlockBuilder: Builder 实例

        异常:
            KeyError: 如果 Builder 未注册
        """
        builder = self.get(node_type)
        if builder is None:
            raise KeyError(f"No builder registered for {node_type.name}")
        return builder

    def is_registered(self, node_type: NodeType) -> bool:
        """
        检查节点类型是否已注册。

        参数:
            node_type: 节点类型枚举

        返回:
            bool: 是否已注册
        """
        return node_type in self._builders

    def get_registered_types(self) -> List[NodeType]:
        """
        获取所有已注册的节点类型。

        返回:
            List[NodeType]: 已注册的节点类型列表
        """
        return sorted(self._registered_types, key=lambda x: x.name)

    # ============================================================
    # 批量操作
    # ============================================================

    def register_many(
        self,
        builders: Dict[NodeType, BlockBuilder]
    ) -> None:
        """
        批量注册 Builder。

        参数:
            builders: NodeType 到 BlockBuilder 的映射
        """
        for node_type, builder in builders.items():
            self.register(node_type, builder)

    def register_many_or_override(
        self,
        builders: Dict[NodeType, BlockBuilder]
    ) -> None:
        """
        批量注册或覆盖 Builder。

        参数:
            builders: NodeType 到 BlockBuilder 的映射
        """
        for node_type, builder in builders.items():
            self.register_or_override(node_type, builder)

    def unregister(self, node_type: NodeType) -> bool:
        """
        注销 Builder。

        参数:
            node_type: 节点类型枚举

        返回:
            bool: 是否成功注销
        """
        if node_type in self._builders:
            del self._builders[node_type]
            self._registered_types.discard(node_type)
            # 清理别名
            for alias, nt in list(self._aliases.items()):
                if nt == node_type:
                    del self._aliases[alias]
            return True
        return False

    def clear(self) -> None:
        """清空所有注册"""
        self._builders.clear()
        self._aliases.clear()
        self._registered_types.clear()

    # ============================================================
    # 验证和调试
    # ============================================================

    def validate_registry(self) -> List[str]:
        """
        验证注册表完整性。

        检查:
            1. 所有 NodeType 是否都有对应的 Builder
            2. 是否有孤儿别名

        返回:
            List[str]: 验证错误信息列表
        """
        errors = []

        # 检查所有节点类型
        from ..constants.node_type import NodeType
        for nt in NodeType:
            if nt != NodeType.DOCUMENT:  # Document 由 Parser 直接创建
                if nt not in self._builders:
                    errors.append(f"Missing builder for {nt.name}")

        # 检查别名
        for alias, nt in self._aliases.items():
            if nt not in self._builders:
                errors.append(f"Alias '{alias}' points to unregistered {nt.name}")

        return errors

    def get_aliases(self) -> Dict[str, NodeType]:
        """
        获取所有别名映射。

        返回:
            Dict[str, NodeType]: 别名到节点类型的映射
        """
        return self._aliases.copy()

    def __repr__(self) -> str:
        return (
            f"BuilderRegistry("
            f"registered={len(self._registered_types)}, "
            f"aliases={len(self._aliases)})"
        )

    def __len__(self) -> int:
        return len(self._builders)

    def __contains__(self, node_type: NodeType) -> bool:
        return self.is_registered(node_type)


# ============================================================
# 注册表工厂函数
# ============================================================

def create_default_registry() -> BuilderRegistry:
    """
    创建包含所有默认 Builder 的注册表。

    返回:
        BuilderRegistry: 完全初始化的注册表
    """
    from .builders.blockquote import BlockQuoteBuilder
    from .builders.code import CodeBuilder
    from .builders.heading import HeadingBuilder
    from .builders.list import ListBuilder
    from .builders.paragraph import ParagraphBuilder
    from .builders.table import TableBuilder

    registry = BuilderRegistry()

    # 注册所有块节点 Builder
    registry.register(NodeType.HEADING, HeadingBuilder())
    registry.register(NodeType.PARAGRAPH, ParagraphBuilder())
    registry.register(NodeType.LIST_BLOCK, ListBuilder())
    registry.register(NodeType.TABLE, TableBuilder())
    registry.register(NodeType.CODE_BLOCK, CodeBuilder())
    registry.register(NodeType.BLOCK_QUOTE, BlockQuoteBuilder())

    return registry


# ============================================================
# 便捷函数
# ============================================================

def get_registry() -> BuilderRegistry:
    """
    获取全局默认注册表（单例模式）。

    返回:
        BuilderRegistry: 全局注册表
    """
    global _default_registry
    if _default_registry is None:
        _default_registry = create_default_registry()
    return _default_registry


_default_registry: Optional[BuilderRegistry] = None


def reset_registry() -> None:
    """重置全局注册表"""
    global _default_registry
    _default_registry = None


def register_builder(node_type: NodeType, builder: BlockBuilder) -> None:
    """
    注册 Builder 到全局注册表。

    参数:
        node_type: 节点类型枚举
        builder: Builder 实例
    """
    registry = get_registry()
    registry.register(node_type, builder)


def get_builder(node_type: NodeType) -> Optional[BlockBuilder]:
    """
    从全局注册表获取 Builder。

    参数:
        node_type: 节点类型枚举

    返回:
        Optional[BlockBuilder]: Builder 实例
    """
    registry = get_registry()
    return registry.get(node_type)