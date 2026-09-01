"""
Pass Registry - Pass 注册表

管理 TransformPass 的注册和发现。
支持延迟实例化、优先级排序和插件发现。
"""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Type

from .passes.base import TransformPass


@dataclass
class PassEntry:
    """
    Pass 注册条目。

    属性:
        pass_cls: Pass 类
        priority: 优先级（数字越小越先执行）
        enabled: 是否启用
        config: Pass 配置
    """
    pass_cls: Type[TransformPass]
    priority: int = 100
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)


class PassRegistry:
    """
    Pass 注册表。

    管理所有可用的 TransformPass，支持：
        - 注册和注销
        - 优先级排序
        - 启用/禁用
        - 插件发现

    属性:
        _entries: Pass 注册条目字典
        _instances: 已实例化的 Pass 缓存
        _metadata: Pass 元数据

    示例:
        >>> registry = PassRegistry()
        >>> registry.register(NormalizePass, priority=10)
        >>> registry.register(DiagramPass, priority=20)
        >>> passes = registry.get_passes()
    """

    def __init__(self):
        """初始化注册表"""
        self._entries: Dict[str, PassEntry] = {}
        self._instances: Dict[str, TransformPass] = {}
        self._metadata: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self._sorted_cache: Optional[List[TransformPass]] = None
        self._cache_dirty: bool = True

    # ============================================================
    # 注册方法
    # ============================================================

    def register(
        self,
        pass_cls: Type[TransformPass],
        name: Optional[str] = None,
        priority: int = 100,
        enabled: bool = True,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        注册 Pass。

        参数:
            pass_cls: Pass 类
            name: Pass 名称（默认使用类名）
            priority: 优先级（数字越小越先执行）
            enabled: 是否启用
            config: Pass 配置

        异常:
            ValueError: 如果名称已存在
        """
        name = name or pass_cls.__name__

        if name in self._entries:
            raise ValueError(f"Pass '{name}' already registered")

        self._entries[name] = PassEntry(
            pass_cls=pass_cls,
            priority=priority,
            enabled=enabled,
            config=config or {},
        )

        # 清除缓存
        self._cache_dirty = True

    def register_many(
        self,
        passes: List[Tuple[Type[TransformPass], Optional[int]]],
    ) -> None:
        """
        批量注册 Pass。

        参数:
            passes: (Pass类, 优先级) 列表
        """
        for pass_cls, priority in passes:
            self.register(pass_cls, priority=priority or 100)

    def unregister(self, name: str) -> bool:
        """
        注销 Pass。

        参数:
            name: Pass 名称

        返回:
            bool: 是否成功注销
        """
        if name in self._entries:
            del self._entries[name]
            if name in self._instances:
                del self._instances[name]
            if name in self._metadata:
                del self._metadata[name]
            self._cache_dirty = True
            return True
        return False

    def clear(self) -> None:
        """清空所有注册"""
        self._entries.clear()
        self._instances.clear()
        self._metadata.clear()
        self._cache_dirty = True

    # ============================================================
    # 查询方法
    # ============================================================

    def get_pass(self, name: str) -> Optional[TransformPass]:
        """
        获取 Pass 实例（懒加载）。

        参数:
            name: Pass 名称

        返回:
            Optional[TransformPass]: Pass 实例，如果未找到则返回 None
        """
        if name not in self._entries:
            print(f"[PassRegistry] get_pass({name}) - not in _entries")
            return None

        # 如果已缓存，直接返回
        if name in self._instances:
            print(f"[PassRegistry] get_pass({name}) - returning cached instance")
            return self._instances[name]

        # 创建实例
        entry = self._entries[name]
        if not entry.enabled:
            print(f"[PassRegistry] get_pass({name}) - disabled")
            return None

        try:
            print(f"[PassRegistry] get_pass({name}) - instantiating...")
            instance = entry.pass_cls()
            print(f"[PassRegistry] get_pass({name}) - instantiated successfully: {instance}")

            # 应用配置
            if hasattr(instance, 'configure') and entry.config:
                instance.configure(entry.config)

            self._instances[name] = instance
            return instance
        except Exception as e:
            # ✅ 打印完整异常，不吞掉
            import traceback
            print(f"[PassRegistry] get_pass({name}) - FAILED: {e}")
            traceback.print_exc()
            self._metadata[name]['error'] = str(e)
            # ✅ 抛出异常，让上层知道 Pass 实例化失败
            raise RuntimeError(f"Failed to instantiate Pass '{name}': {e}") from e

    def get_passes(
        self,
        enabled_only: bool = True,
        sort_by_priority: bool = True,
    ) -> List[TransformPass]:
        """
        获取所有 Pass 实例（按优先级排序）。

        参数:
            enabled_only: 是否只返回启用的 Pass
            sort_by_priority: 是否按优先级排序

        返回:
            List[TransformPass]: Pass 实例列表
        """
        # 调试输出
        print("[PassRegistry] get_passes() called")
        print(f"[PassRegistry] _entries count: {len(self._entries)}")
        print(f"[PassRegistry] _entries keys: {list(self._entries.keys())}")
        print(f"[PassRegistry] _cache_dirty: {self._cache_dirty}, _sorted_cache: {self._sorted_cache is not None}")
        
        # 检查缓存
        if not self._cache_dirty and self._sorted_cache is not None:
            print(f"[PassRegistry] Returning cached passes: {len(self._sorted_cache)}")
            return self._sorted_cache

        passes = []
        for name, entry in self._entries.items():
            print(f"[PassRegistry] Processing: {name} (enabled: {entry.enabled})")
            if enabled_only and not entry.enabled:
                print(f"[PassRegistry]   Skipping {name} (disabled)")
                continue

            try:
                instance = self.get_pass(name)
                if instance is not None:
                    passes.append((entry.priority, instance))
                    print(f"[PassRegistry]   {name} -> {instance}")
                else:
                    print(f"[PassRegistry]   {name} -> None")
            except Exception as e:
                print(f"[PassRegistry]   {name} - ERROR: {e}")
                # 继续处理其他 Pass

        if sort_by_priority:
            passes.sort(key=lambda x: x[0])

        result = [p for _, p in passes]
        self._sorted_cache = result
        self._cache_dirty = False
        print(f"[PassRegistry] Returning {len(result)} passes: {[p.__class__.__name__ for p in result]}")
        return result

    def get_names(self) -> List[str]:
        """获取所有注册的 Pass 名称"""
        return list(self._entries.keys())

    def get_entries(self) -> Dict[str, PassEntry]:
        """获取所有 Pass 注册条目"""
        return self._entries.copy()

    def is_registered(self, name: str) -> bool:
        """检查 Pass 是否已注册"""
        return name in self._entries

    def is_enabled(self, name: str) -> bool:
        """检查 Pass 是否启用"""
        if name not in self._entries:
            return False
        return self._entries[name].enabled

    # ============================================================
    # 配置方法
    # ============================================================

    def enable(self, name: str) -> bool:
        """
        启用 Pass。

        参数:
            name: Pass 名称

        返回:
            bool: 是否成功
        """
        if name in self._entries:
            self._entries[name].enabled = True
            self._cache_dirty = True
            return True
        return False

    def disable(self, name: str) -> bool:
        """
        禁用 Pass。

        参数:
            name: Pass 名称

        返回:
            bool: 是否成功
        """
        if name in self._entries:
            self._entries[name].enabled = False
            if name in self._instances:
                del self._instances[name]
            self._cache_dirty = True
            return True
        return False

    def set_priority(self, name: str, priority: int) -> bool:
        """
        设置 Pass 优先级。

        参数:
            name: Pass 名称
            priority: 优先级

        返回:
            bool: 是否成功
        """
        if name in self._entries:
            self._entries[name].priority = priority
            self._cache_dirty = True
            return True
        return False

    def set_config(self, name: str, config: Dict[str, Any]) -> bool:
        """
        设置 Pass 配置。

        参数:
            name: Pass 名称
            config: 配置字典

        返回:
            bool: 是否成功
        """
        if name in self._entries:
            self._entries[name].config = config
            if name in self._instances:
                del self._instances[name]
            self._cache_dirty = True
            return True
        return False

    def get_config(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取 Pass 配置。

        参数:
            name: Pass 名称

        返回:
            Optional[Dict[str, Any]]: 配置字典
        """
        if name in self._entries:
            return self._entries[name].config
        return None

    # ============================================================
    # 元数据
    # ============================================================

    def set_metadata(self, name: str, key: str, value: Any) -> None:
        """
        设置 Pass 元数据。

        参数:
            name: Pass 名称
            key: 元数据键
            value: 元数据值
        """
        self._metadata[name][key] = value

    def get_metadata(self, name: str, key: str, default: Any = None) -> Any:
        """
        获取 Pass 元数据。

        参数:
            name: Pass 名称
            key: 元数据键
            default: 默认值

        返回:
            Any: 元数据值
        """
        return self._metadata[name].get(key, default)

    def get_all_metadata(self, name: str) -> Dict[str, Any]:
        """
        获取 Pass 所有元数据。

        参数:
            name: Pass 名称

        返回:
            Dict[str, Any]: 元数据字典
        """
        return self._metadata.get(name, {})

    # ============================================================
    # 统计信息
    # ============================================================

    def get_stats(self) -> Dict[str, Any]:
        """
        获取注册表统计信息。

        返回:
            Dict[str, Any]: 统计信息
        """
        total = len(self._entries)
        enabled = sum(1 for e in self._entries.values() if e.enabled)
        disabled = total - enabled
        instantiated = len(self._instances)

        return {
            "total": total,
            "enabled": enabled,
            "disabled": disabled,
            "instantiated": instantiated,
            "names": self.get_names(),
        }

    # ============================================================
    # 缓存管理
    # ============================================================

    def invalidate_cache(self) -> None:
        """使缓存失效"""
        self._cache_dirty = True
        self._sorted_cache = None

    def clear_cache(self) -> None:
        """清空实例缓存"""
        self._instances.clear()
        self._cache_dirty = True
        self._sorted_cache = None

    def rebuild_cache(self) -> None:
        """重建缓存"""
        self.get_passes()

    # ============================================================
    # 序列化
    # ============================================================

    def to_dict(self) -> Dict[str, Any]:
        """
        导出注册表为字典。

        返回:
            Dict[str, Any]: 注册表数据
        """
        return {
            name: {
                "priority": entry.priority,
                "enabled": entry.enabled,
                "config": entry.config,
                "metadata": self._metadata.get(name, {}),
            }
            for name, entry in self._entries.items()
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """
        从字典导入注册表数据。

        参数:
            data: 注册表数据
        """
        self.clear()
        # 这里需要动态导入类，暂时用占位
        pass

    # ============================================================
    # 魔法方法
    # ============================================================

    def __repr__(self) -> str:
        names = self.get_names()
        return f"PassRegistry({len(names)} passes: {', '.join(names[:5])}{'...' if len(names) > 5 else ''})"

    def __len__(self) -> int:
        return len(self._entries)

    def __contains__(self, name: str) -> bool:
        return self.is_registered(name)

    def __iter__(self):
        return iter(self.get_passes())


# ============================================================
# 全局注册表
# ============================================================

_default_registry: Optional[PassRegistry] = None


def get_global_registry() -> PassRegistry:
    """
    获取全局 Pass 注册表。

    返回:
        PassRegistry: 全局注册表
    """
    global _default_registry
    if _default_registry is None:
        _default_registry = PassRegistry()
    return _default_registry


def reset_global_registry() -> None:
    """重置全局注册表"""
    global _default_registry
    _default_registry = None


def register_pass(
    pass_cls: Type[TransformPass],
    priority: int = 100,
    enabled: bool = True,
) -> None:
    """
    注册 Pass 到全局注册表。

    参数:
        pass_cls: Pass 类
        priority: 优先级
        enabled: 是否启用
    """
    registry = get_global_registry()
    registry.register(pass_cls, priority=priority, enabled=enabled)