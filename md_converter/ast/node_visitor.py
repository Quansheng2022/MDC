"""
Node Visitor - AST 访问者模式实现

提供高性能的节点访问器，用于遍历和操作 AST。
使用缓存机制避免重复的 getattr 查找，提高性能。
"""

from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set

from ..constants.node_type import NodeType
from .nodes import Node


class NodeVisitor:
    """
    AST 节点访问器基类。

    使用方式:
        1. 继承 NodeVisitor
        2. 实现 visit_<NodeTypeName> 方法
        3. 调用 visit(node) 开始遍历

    特点:
        - 自动缓存方法查找，提高性能
        - 支持 generic_visit 处理未实现的方法
        - 支持访问前/后钩子

    示例:
        >>> class MyVisitor(NodeVisitor):
        ...     def visit_Heading(self, node):
        ...         print(f"Heading: {node.to_plain_text()}")
        ...         return self.generic_visit(node)
        ...
        >>> visitor = MyVisitor()
        >>> visitor.visit(document)
    """

    def __init__(self):
        """初始化访问器，创建方法缓存"""
        self._cache: Dict[type, Callable[[Node], Any]] = {}
        self._enter_cache: Dict[type, Callable[[Node], Any]] = {}
        self._exit_cache: Dict[type, Callable[[Node], Any]] = {}
        self._depth: int = 0
        self._visited: Set[int] = set()  # 用于防止循环引用

    # ============================================================
    # 主访问入口
    # ============================================================

    def visit(self, node: Node) -> Any:
        """
        访问单个节点。

        自动分发到对应的 visit_<NodeTypeName> 方法。
        如果未找到对应方法，则调用 generic_visit。

        参数:
            node: 要访问的节点

        返回:
            Any: 访问方法的返回值
        """
        if node is None:
            return None

        # 防止循环引用
        node_id = id(node)
        if node_id in self._visited:
            return None
        self._visited.add(node_id)

        try:
            method = self._cache.get(type(node))
            if method is None:
                method_name = f"visit_{type(node).__name__}"
                method = getattr(self, method_name, None)
                self._cache[type(node)] = method

            # 调用 enter 钩子（如果有）
            self._enter_node(node)

            if method:
                result = method(node)
            else:
                result = self.generic_visit(node)

            # 调用 exit 钩子（如果有）
            self._exit_node(node)

            return result
        finally:
            self._visited.remove(node_id)

    def generic_visit(self, node: Node) -> Any:
        """
        通用访问方法，当没有特定的 visit_<Type> 方法时调用。

        默认实现：遍历所有子节点。

        参数:
            node: 要访问的节点

        返回:
            Any: 访问结果
        """
        self._depth += 1
        for child in node.iter_children():
            self.visit(child)
        self._depth -= 1
        return None

    # ============================================================
    # 访问钩子
    # ============================================================

    def _enter_node(self, node: Node) -> None:
        """进入节点时调用"""
        self._depth += 1
        enter_method = self._enter_cache.get(type(node))
        if enter_method is None:
            method_name = f"enter_{type(node).__name__}"
            enter_method = getattr(self, method_name, None)
            self._enter_cache[type(node)] = enter_method
        if enter_method:
            enter_method(node)

    def _exit_node(self, node: Node) -> None:
        """离开节点时调用"""
        exit_method = self._exit_cache.get(type(node))
        if exit_method is None:
            method_name = f"exit_{type(node).__name__}"
            exit_method = getattr(self, method_name, None)
            self._exit_cache[type(node)] = exit_method
        if exit_method:
            exit_method(node)
        self._depth -= 1

    # ============================================================
    # 辅助方法
    # ============================================================

    @property
    def depth(self) -> int:
        """当前访问深度"""
        return self._depth

    def is_top_level(self) -> bool:
        """是否在顶层（文档根节点）"""
        return self._depth <= 1

    def clear_cache(self) -> None:
        """清空方法缓存"""
        self._cache.clear()
        self._enter_cache.clear()
        self._exit_cache.clear()

    def reset(self) -> None:
        """重置访问器状态"""
        self.clear_cache()
        self._depth = 0
        self._visited.clear()


# ============================================================
# 访问器装饰器
# ============================================================

def visit_method(node_type: str):
    """
    装饰器：显式指定访问的节点类型。

    用于当方法名不符合 visit_<NodeTypeName> 命名规范时。

    参数:
        node_type: 节点类型名称

    示例:
        >>> @visit_method("Heading")
        ... def handle_heading(self, node):
        ...     print(f"Heading: {node.level}")
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, node):
            return func(self, node)
        # 存储节点类型信息
        wrapper._node_type = node_type
        return wrapper
    return decorator


# ============================================================
# 访问器变体
# ============================================================

class TransformingVisitor(NodeVisitor):
    """
    转换访问器：可以修改或替换节点。

    子类可以实现 transform_<NodeTypeName> 方法，
    返回新的节点来替换原节点。
    """

    def __init__(self):
        super().__init__()
        self._transform_cache: Dict[type, Callable] = {}

    def transform(self, node: Node) -> Node:
        """
        转换节点，返回新节点。

        如果实现了 transform_<NodeTypeName> 方法，则调用它。
        否则递归转换子节点并重建节点。

        参数:
            node: 要转换的节点

        返回:
            Node: 转换后的节点
        """
        if node is None:
            return None

        # 检查是否有自定义转换方法
        method = self._transform_cache.get(type(node))
        if method is None:
            method_name = f"transform_{type(node).__name__}"
            method = getattr(self, method_name, None)
            self._transform_cache[type(node)] = method

        if method:
            return method(node)

        # 默认：递归转换子节点
        children = list(node.iter_children())
        if children:
            new_children = [self.transform(child) for child in children]
            return node.replace_children(new_children)
        return node


class CollectingVisitor(NodeVisitor):
    """
    收集访问器：收集特定类型的节点。

    示例:
        >>> collector = CollectingVisitor()
        >>> collector.collect(doc, NodeType.HEADING)
        >>> headings = collector.get_collected()
    """

    def __init__(self):
        super().__init__()
        self._collected: Dict[NodeType, List[Node]] = {}
        self._target_types: Set[NodeType] = set()

    def collect(self, node: Node, target_types: Optional[Set[NodeType]] = None) -> List[Node]:
        """
        收集指定类型的节点。

        参数:
            node: 要遍历的根节点
            target_types: 要收集的节点类型集合

        返回:
            List[Node]: 收集到的节点列表
        """
        if target_types:
            self._target_types = target_types
        else:
            self._target_types = set()

        self._collected.clear()
        self.visit(node)
        return self.get_collected()

    def get_collected(self, node_type: Optional[NodeType] = None) -> List[Node]:
        """
        获取收集到的节点。

        参数:
            node_type: 指定节点类型，None 表示返回所有

        返回:
            List[Node]: 收集到的节点列表
        """
        if node_type is None:
            result = []
            for nodes in self._collected.values():
                result.extend(nodes)
            return result
        return self._collected.get(node_type, [])

    def generic_visit(self, node: Node) -> Any:
        if self._target_types and node.node_type in self._target_types:
            if node.node_type not in self._collected:
                self._collected[node.node_type] = []
            self._collected[node.node_type].append(node)
        # 继续遍历子节点
        for child in node.iter_children():
            self.visit(child)


class ChainedVisitor(NodeVisitor):
    """
    链式访问器：依次执行多个访问器。

    示例:
        >>> visitor1 = MyVisitor1()
        >>> visitor2 = MyVisitor2()
        >>> chain = ChainedVisitor([visitor1, visitor2])
        >>> chain.visit(doc)
    """

    def __init__(self, visitors: List[NodeVisitor]):
        super().__init__()
        self.visitors = visitors

    def generic_visit(self, node: Node) -> Any:
        # 依次执行所有访问器
        for visitor in self.visitors:
            visitor.visit(node)
        # 继续遍历子节点
        for child in node.iter_children():
            self.visit(child)


# ============================================================
# 访问器工厂函数
# ============================================================

def create_visitor(methods: Dict[str, Callable]) -> NodeVisitor:
    """
    动态创建访问器。

    参数:
        methods: 方法名到函数的映射

    返回:
        NodeVisitor: 动态创建的访问器

    示例:
        >>> def visit_heading(node):
        ...     print(f"Heading: {node.to_plain_text()}")
        ...
        >>> visitor = create_visitor({"visit_Heading": visit_heading})
    """
    class DynamicVisitor(NodeVisitor):
        pass

    for name, method in methods.items():
        setattr(DynamicVisitor, name, method)

    return DynamicVisitor()