"""
Render Context - 渲染上下文

提供渲染过程中需要的所有状态信息。
包含主题、诊断收集器、编号计数器、书签、脚注等。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..diagnostics.collector import DiagnosticCollector
from .themes.v15_theme import V15Theme


@dataclass
class HeadingNumbering:
    """
    标题编号状态。

    支持多级标题编号（如 1.1, 1.1.1 等）。
    """

    counters: Dict[int, int] = field(default_factory=dict)
    reset_on_level: int = 1

    def increment(self, level: int) -> str:
        """
        增加标题编号并返回编号字符串。

        参数:
            level: 标题级别 (1-6)

        返回:
            str: 编号字符串 (如 "1.2.3")
        """
        # 重置比当前级别深的计数器
        for idx in list(self.counters.keys()):
            if idx > level:
                del self.counters[idx]

        # 增加当前级别计数器
        self.counters[level] = self.counters.get(level, 0) + 1

        # 生成编号字符串
        parts = []
        for idx in range(1, level + 1):
            if idx in self.counters:
                parts.append(str(self.counters[idx]))
            else:
                parts.append("0")

        return ".".join(parts)

    def reset(self) -> None:
        """重置所有计数器"""
        self.counters.clear()


@dataclass
class ListNumbering:
    """
    列表编号状态。

    支持多级嵌套列表编号（如 1, 1.1, 1.1.1 等）。
    """

    counters: Dict[int, int] = field(default_factory=dict)
    ordered: Dict[int, bool] = field(default_factory=dict)

    def increment(self, depth: int, is_ordered: bool) -> str:
        """
        增加列表编号并返回编号字符串。

        参数:
            depth: 列表嵌套深度
            is_ordered: 是否为有序列表

        返回:
            str: 编号字符串
        """
        # 重置比当前深度深的计数器
        for d in list(self.counters.keys()):
            if d > depth:
                del self.counters[d]

        # 记录列表类型
        self.ordered[depth] = is_ordered

        if is_ordered:
            # 有序列表：使用数字
            self.counters[depth] = self.counters.get(depth, 0) + 1
            # 生成嵌套编号
            parts = []
            for d in range(0, depth + 1):
                if d in self.counters:
                    parts.append(str(self.counters[d]))
            return ".".join(parts)
        else:
            # 无序列表：使用符号
            self.counters[depth] = self.counters.get(depth, 0) + 1
            symbols = ["•", "○", "▪", "▫", "◆", "◇"]
            idx = min(depth, len(symbols) - 1)
            return symbols[idx]

    def reset(self) -> None:
        """重置所有计数器"""
        self.counters.clear()
        self.ordered.clear()


@dataclass
class FootnoteState:
    """
    脚注状态管理。
    """

    definitions: Dict[str, str] = field(default_factory=dict)
    references: Dict[str, int] = field(default_factory=dict)
    counter: int = 0

    def add_definition(self, id: str, text: str) -> None:
        """添加脚注定义"""
        self.definitions[id] = text

    def add_reference(self, id: str) -> int:
        """添加脚注引用"""
        if id not in self.references:
            self.counter += 1
            self.references[id] = self.counter
        return self.references[id]

    def get_definition(self, id: str) -> Optional[str]:
        """获取脚注定义"""
        return self.definitions.get(id)

    def get_reference_number(self, id: str) -> Optional[int]:
        """获取脚注引用编号"""
        return self.references.get(id)


@dataclass
class BookmarkState:
    """
    书签状态管理。

    用于交叉引用和内部链接。
    """

    bookmarks: Dict[str, str] = field(default_factory=dict)  # name -> target_id
    counter: int = 0

    def add(self, name: str, target_id: str) -> None:
        """添加书签"""
        self.bookmarks[name] = target_id

    def get(self, name: str) -> Optional[str]:
        """获取书签目标"""
        return self.bookmarks.get(name)

    def generate_id(self, prefix: str = "bookmark") -> str:
        """生成唯一书签 ID"""
        self.counter += 1
        return f"{prefix}_{self.counter}"


@dataclass
class TOCState:
    """
    目录状态管理。
    """

    entries: List[Dict[str, Any]] = field(default_factory=list)
    include_depth: int = 3

    def add_entry(
        self, level: int, text: str, page: Optional[int] = None, anchor: Optional[str] = None
    ) -> None:
        """添加目录条目"""
        if level <= self.include_depth:
            self.entries.append(
                {
                    "level": level,
                    "text": text,
                    "page": page,
                    "anchor": anchor,
                }
            )

    def clear(self) -> None:
        """清空目录"""
        self.entries.clear()


@dataclass
class RenderContext:
    """
    渲染上下文。

    封装渲染过程中需要的所有状态和配置。
    采用分层设计，各个子状态独立管理。

    属性:
        theme: 主题配置
        diag: 诊断收集器
        config: 配置字典
        heading_counts: 标题编号状态（兼容旧代码）
        heading_numbers: 标题编号状态
        list_numbers: 列表编号状态
        footnotes: 脚注状态
        bookmarks: 书签状态
        toc: 目录状态
        custom_data: 自定义数据存储
    """

    # 核心组件
    theme: Any
    diag: DiagnosticCollector
    config: Dict[str, Any] = field(default_factory=dict)

    # 编号计数器（兼容旧代码）
    heading_counts: Dict[int, int] = field(default_factory=dict)

    # 状态子模块
    heading_numbers: HeadingNumbering = field(default_factory=HeadingNumbering)
    list_numbers: ListNumbering = field(default_factory=ListNumbering)
    footnotes: FootnoteState = field(default_factory=FootnoteState)
    bookmarks: BookmarkState = field(default_factory=BookmarkState)
    toc: TOCState = field(default_factory=TOCState)

    # 运行时状态
    current_section: int = 0
    current_page: int = 1
    document_metadata: Dict[str, Any] = field(default_factory=dict)

    # 自定义数据（用于扩展）
    custom_data: Dict[str, Any] = field(default_factory=dict)

    # ============================================================
    # 构造器
    # ============================================================

    def __post_init__(self):
        """初始化后设置 TOC 深度"""
        if self.config:
            self.toc.include_depth = self.config.get("toc_depth", 3)

    @classmethod
    def create(
        cls,
        theme: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None,
        diag: Optional[DiagnosticCollector] = None,
    ) -> "RenderContext":
        """
        创建渲染上下文的工厂方法。

        参数:
            theme: 主题配置
            config: 配置字典
            diag: 诊断收集器

        返回:
            RenderContext: 上下文实例
        """
        if theme is None:
            theme = V15Theme.load_default()
        if config is None:
            config = {}
        if diag is None:
            diag = DiagnosticCollector()

        return cls(
            theme=theme,
            diag=diag,
            config=config,
        )

    # ============================================================
    # 编号辅助方法（兼容旧代码）
    # ============================================================

    def get_heading_number(self, level: int) -> str:
        """
        获取标题编号（兼容旧代码）。

        参数:
            level: 标题级别

        返回:
            str: 编号字符串
        """
        # 更新兼容字典
        self.heading_counts[level] = self.heading_counts.get(level, 0) + 1
        return self.heading_numbers.increment(level)

    def get_list_number(self, depth: int, ordered: bool) -> str:
        """
        获取列表编号（兼容旧代码）。

        参数:
            depth: 列表深度
            ordered: 是否为有序列表

        返回:
            str: 编号字符串
        """
        return self.list_numbers.increment(depth, ordered)

    def reset_numbering(self) -> None:
        """重置所有编号"""
        self.heading_counts.clear()
        self.heading_numbers.reset()
        self.list_numbers.reset()

    # ============================================================
    # 脚注辅助方法
    # ============================================================

    def add_footnote(self, id: str, text: str) -> None:
        """添加脚注定义"""
        self.footnotes.add_definition(id, text)

    def reference_footnote(self, id: str) -> int:
        """引用脚注"""
        return self.footnotes.add_reference(id)

    def get_footnote_text(self, id: str) -> Optional[str]:
        """获取脚注文本"""
        return self.footnotes.get_definition(id)

    # ============================================================
    # 书签辅助方法
    # ============================================================

    def add_bookmark(self, name: str, target_id: str) -> None:
        """添加书签"""
        self.bookmarks.add(name, target_id)

    def get_bookmark(self, name: str) -> Optional[str]:
        """获取书签目标"""
        return self.bookmarks.get(name)

    def generate_bookmark_id(self) -> str:
        """生成书签 ID"""
        return self.bookmarks.generate_id()

    # ============================================================
    # 目录辅助方法
    # ============================================================

    def add_toc_entry(
        self, level: int, text: str, page: Optional[int] = None, anchor: Optional[str] = None
    ) -> None:
        """添加目录条目"""
        self.toc.add_entry(level, text, page, anchor)

    def get_toc_entries(self) -> List[Dict[str, Any]]:
        """获取目录条目"""
        return self.toc.entries

    # ============================================================
    # 配置访问
    # ============================================================

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        获取配置值。

        参数:
            key: 配置键名
            default: 默认值

        返回:
            Any: 配置值
        """
        keys = key.split(".")
        current = self.config
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        return current

    # ============================================================
    # 自定义数据
    # ============================================================

    def get_custom(self, key: str, default: Any = None) -> Any:
        """获取自定义数据"""
        return self.custom_data.get(key, default)

    def set_custom(self, key: str, value: Any) -> None:
        """设置自定义数据"""
        self.custom_data[key] = value

    def has_custom(self, key: str) -> bool:
        """检查是否有自定义数据"""
        return key in self.custom_data

    # ============================================================
    # 状态管理
    # ============================================================

    def reset(self) -> None:
        """重置所有状态"""
        self.heading_counts.clear()
        self.heading_numbers.reset()
        self.list_numbers.reset()
        self.footnotes = FootnoteState()
        self.bookmarks = BookmarkState()
        self.toc.clear()
        self.current_section = 0
        self.current_page = 1

    def copy(self) -> "RenderContext":
        """
        创建上下文的深拷贝。

        返回:
            RenderContext: 新的上下文实例
        """
        import copy

        return RenderContext(
            theme=self.theme,
            diag=self.diag,
            config=copy.deepcopy(self.config),
            heading_counts=copy.deepcopy(self.heading_counts),
            heading_numbers=copy.deepcopy(self.heading_numbers),
            list_numbers=copy.deepcopy(self.list_numbers),
            footnotes=copy.deepcopy(self.footnotes),
            bookmarks=copy.deepcopy(self.bookmarks),
            toc=copy.deepcopy(self.toc),
            current_section=self.current_section,
            current_page=self.current_page,
            document_metadata=copy.deepcopy(self.document_metadata),
            custom_data=copy.deepcopy(self.custom_data),
        )

    # ============================================================
    # 诊断辅助
    # ============================================================

    def warning(
        self, message: str, code: str = "WARN000", location=None, suggestion: Optional[str] = None
    ) -> None:
        """记录警告诊断"""
        self.diag.warning(message, code, location, suggestion)

    def error(
        self, message: str, code: str = "ERR000", location=None, suggestion: Optional[str] = None
    ) -> None:
        """记录错误诊断"""
        self.diag.error(message, code, location, suggestion)

    def info(
        self, message: str, code: str = "INFO000", location=None, suggestion: Optional[str] = None
    ) -> None:
        """记录信息诊断"""
        self.diag.info(message, code, location, suggestion)

    # ============================================================
    # 魔法方法
    # ============================================================

    def __repr__(self) -> str:
        return (
            f"RenderContext("
            f"theme={self.theme.__class__.__name__}, "
            f"heading_counts={len(self.heading_counts)}, "
            f"heading_numbers={len(self.heading_numbers.counters)}, "
            f"list_numbers={len(self.list_numbers.counters)}, "
            f"footnotes={len(self.footnotes.definitions)}, "
            f"bookmarks={len(self.bookmarks.bookmarks)})"
        )
