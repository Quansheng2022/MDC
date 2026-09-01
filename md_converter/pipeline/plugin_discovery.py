"""
Plugin Discovery - 插件发现机制

通过 Python 的 entry_points 系统发现并加载外部 Pass 插件。
支持从已安装的 Python 包中自动发现 TransformPass 实现。
"""

import inspect
import warnings
from importlib.metadata import EntryPoint, entry_points
from typing import Any, Dict, List, Optional, Set, Type

from .passes.base import TransformPass


class PluginDiscovery:
    """
    插件发现器。

    通过 entry_points 发现并加载 TransformPass 插件。
    支持多种发现策略和过滤。

    属性:
        group: entry_points 组名
        discovered: 已发现的插件类列表
        loaded: 已加载的插件实例列表
    """

    def __init__(self, group: str = "md_converter.passes"):
        """
        初始化插件发现器。

        参数:
            group: entry_points 组名
        """
        self.group = group
        self.discovered: List[Type[TransformPass]] = []
        self.loaded: List[TransformPass] = []
        self._errors: List[Dict[str, Any]] = []

    # ============================================================
    # 发现方法
    # ============================================================

    def discover(self) -> List[Type[TransformPass]]:
        """
        发现所有可用的 TransformPass 插件。

        通过 entry_points 查找，过滤出 TransformPass 的子类。

        返回:
            List[Type[TransformPass]]: 发现的 Pass 类列表
        """
        self.discovered = []
        self._errors = []

        try:
            # 获取 entry_points（兼容新旧 API）
            eps = entry_points(group=self.group)

            # 遍历 entry points
            for ep in eps:
                try:
                    # 加载 entry point
                    cls = self._load_entry_point(ep)

                    if cls is not None and self._is_valid_pass(cls):
                        self.discovered.append(cls)
                except Exception as e:
                    self._errors.append({
                        "name": ep.name,
                        "module": ep.module,
                        "error": str(e),
                    })

        except Exception as e:
            # entry_points 可能抛出异常
            warnings.warn(
                f"Failed to discover plugins for group '{self.group}': {e}",
                RuntimeWarning
            )

        return self.discovered

    def discover_and_load(self) -> List[TransformPass]:
        """
        发现并实例化所有插件。

        返回:
            List[TransformPass]: 实例化的 Pass 列表
        """
        self.discover()
        self.loaded = []
        self._errors = []

        for pass_cls in self.discovered:
            try:
                instance = pass_cls()
                self.loaded.append(instance)
            except Exception as e:
                self._errors.append({
                    "name": pass_cls.__name__,
                    "error": str(e),
                })

        return self.loaded

    def _load_entry_point(self, ep: EntryPoint) -> Optional[Type]:
        """
        加载 entry point。

        参数:
            ep: EntryPoint 对象

        返回:
            Optional[Type]: 加载的类或函数
        """
        try:
            # 加载 entry point
            obj = ep.load()

            # 检查是否是类
            if inspect.isclass(obj):
                return obj

            # 如果是函数，尝试调用获取类
            if callable(obj):
                result = obj()
                if inspect.isclass(result) and self._is_valid_pass(result):
                    return result

            # 如果是模块，尝试查找 TransformPass 子类
            if inspect.ismodule(obj):
                for name, item in inspect.getmembers(obj, inspect.isclass):
                    if self._is_valid_pass(item) and item.__module__ == obj.__name__:
                        return item

            return None

        except Exception as e:
            warnings.warn(
                f"Failed to load entry point '{ep.name}': {e}",
                RuntimeWarning
            )
            raise

    def _is_valid_pass(self, cls: Type) -> bool:
        """
        检查是否为有效的 TransformPass。

        参数:
            cls: 要检查的类

        返回:
            bool: 是否为有效的 TransformPass
        """
        try:
            # 必须是 TransformPass 的子类
            if not issubclass(cls, TransformPass):
                return False

            # 不能是抽象基类
            if inspect.isabstract(cls):
                return False

            # 不能是 TransformPass 本身
            if cls is TransformPass:
                return False

            # 必须有 run 方法
            if not hasattr(cls, 'run'):
                return False

            # 检查 run 方法签名
            sig = inspect.signature(cls.run)
            params = list(sig.parameters.values())
            if len(params) < 2:
                return False

            return True

        except Exception:
            return False

    # ============================================================
    # 查询方法
    # ============================================================

    def get_discovered(self) -> List[Type[TransformPass]]:
        """获取已发现的 Pass 类"""
        return self.discovered

    def get_loaded(self) -> List[TransformPass]:
        """获取已加载的 Pass 实例"""
        return self.loaded

    def get_errors(self) -> List[Dict[str, Any]]:
        """获取发现过程中的错误"""
        return self._errors

    def has_errors(self) -> bool:
        """检查是否有错误"""
        return bool(self._errors)

    def get_names(self) -> List[str]:
        """获取已发现插件的名称列表"""
        return [cls.__name__ for cls in self.discovered]

    # ============================================================
    # 过滤方法
    # ============================================================

    def filter_by_priority(self) -> List[Type[TransformPass]]:
        """
        按优先级排序（如果类有 priority 属性）。

        返回:
            List[Type[TransformPass]]: 排序后的列表
        """
        def get_priority(cls):
            return getattr(cls, 'priority', 100)

        return sorted(self.discovered, key=get_priority)

    def filter_by_name(self, names: Set[str]) -> List[Type[TransformPass]]:
        """
        按名称过滤。

        参数:
            names: 要保留的类名集合

        返回:
            List[Type[TransformPass]]: 过滤后的列表
        """
        return [cls for cls in self.discovered if cls.__name__ in names]

    def filter_exclude(self, names: Set[str]) -> List[Type[TransformPass]]:
        """
        排除指定的 Pass。

        参数:
            names: 要排除的类名集合

        返回:
            List[Type[TransformPass]]: 过滤后的列表
        """
        return [cls for cls in self.discovered if cls.__name__ not in names]

    # ============================================================
    # 验证方法
    # ============================================================

    def validate_plugins(self) -> Dict[str, List[str]]:
        """
        验证所有插件的有效性。

        返回:
            Dict[str, List[str]]: 验证结果
        """
        result = {
            "valid": [],
            "invalid": [],
            "errors": [],
        }

        for cls in self.discovered:
            try:
                if self._validate_plugin(cls):
                    result["valid"].append(cls.__name__)
                else:
                    result["invalid"].append(cls.__name__)
            except Exception as e:
                result["errors"].append(f"{cls.__name__}: {e}")

        return result

    def _validate_plugin(self, cls: Type[TransformPass]) -> bool:
        """
        验证单个插件。

        参数:
            cls: 要验证的类

        返回:
            bool: 是否有效
        """
        # 检查是否是 TransformPass 子类
        if not issubclass(cls, TransformPass):
            return False

        # 检查是否有 run 方法
        if not hasattr(cls, 'run'):
            return False

        # 尝试实例化
        try:
            instance = cls()
            if not isinstance(instance, TransformPass):
                return False
        except Exception:
            return False

        return True


# ============================================================
# 便捷函数
# ============================================================

def discover_passes(
    group: str = "md_converter.passes",
    load: bool = True,
) -> List[TransformPass]:
    """
    发现并加载 TransformPass 插件。

    参数:
        group: entry_points 组名
        load: 是否立即加载

    返回:
        List[TransformPass]: 发现的 Pass 实例列表
    """
    discovery = PluginDiscovery(group)

    if load:
        return discovery.discover_and_load()
    else:
        discovery.discover()
        return discovery.get_loaded()


def discover_pass_classes(
    group: str = "md_converter.passes",
) -> List[Type[TransformPass]]:
    """
    发现 TransformPass 类（不实例化）。

    参数:
        group: entry_points 组名

    返回:
        List[Type[TransformPass]]: 发现的 Pass 类列表
    """
    discovery = PluginDiscovery(group)
    discovery.discover()
    return discovery.get_discovered()


def get_plugin_info(group: str = "md_converter.passes") -> Dict[str, Any]:
    """
    获取插件信息。

    参数:
        group: entry_points 组名

    返回:
        Dict[str, Any]: 插件信息
    """
    discovery = PluginDiscovery(group)
    discovery.discover()

    return {
        "group": group,
        "total": len(discovery.discovered),
        "names": discovery.get_names(),
        "errors": discovery.get_errors(),
        "has_errors": discovery.has_errors(),
    }


def validate_plugins(group: str = "md_converter.passes") -> Dict[str, List[str]]:
    """
    验证所有插件。

    参数:
        group: entry_points 组名

    返回:
        Dict[str, List[str]]: 验证结果
    """
    discovery = PluginDiscovery(group)
    discovery.discover()
    return discovery.validate_plugins()


# ============================================================
# 插件开发装饰器
# ============================================================

def register_pass(
    name: Optional[str] = None,
    priority: int = 100,
    enabled: bool = True,
) -> callable:
    """
    装饰器：将类注册为 TransformPass 插件。

    参数:
        name: Pass 名称（默认使用类名）
        priority: 优先级
        enabled: 是否启用

    返回:
        callable: 装饰器函数

    示例:
        >>> @register_pass(priority=10)
        ... class MyPass(TransformPass):
        ...     def run(self, document, diag):
        ...         return document
    """
    def decorator(cls):
        if not issubclass(cls, TransformPass):
            raise TypeError(f"{cls.__name__} must inherit from TransformPass")

        # 存储元数据
        cls._pass_name = name or cls.__name__
        cls._pass_priority = priority
        cls._pass_enabled = enabled

        # 注册到全局注册表
        from .pass_registry import get_global_registry
        registry = get_global_registry()
        registry.register(cls, name=name, priority=priority, enabled=enabled)

        return cls

    return decorator