"""
Pass Base - Pass 模式基类定义

定义 TransformPass 抽象基类和 PassResult 数据结构。
所有管道 Pass 必须继承 TransformPass 并实现 run 方法。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ...ast.nodes import Node
from ...diagnostics.collector import DiagnosticCollector


@dataclass
class PassResult:
    """
    Pass 执行结果。

    包含转换后的 AST、诊断信息和生成的文件列表。

    属性:
        document: 转换后的 AST 根节点
        diagnostics: 执行过程中产生的诊断信息列表
        files: Pass 生成的文件路径列表（如渲染的图片）
        metadata: 附加元数据
    """
    document: Node
    diagnostics: List[Dict[str, Any]] = field(default_factory=list)
    files: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_diagnostic(
        self,
        message: str,
        level: str = "warning",
        code: str = "PASS000",
        location: Optional[str] = None,
    ) -> None:
        """添加诊断信息"""
        self.diagnostics.append({
            "level": level,
            "code": code,
            "message": message,
            "location": location,
        })

    def add_file(self, file_path: str) -> None:
        """添加生成的文件"""
        if file_path not in self.files:
            self.files.append(file_path)

    def merge(self, other: "PassResult") -> "PassResult":
        """合并另一个 PassResult"""
        return PassResult(
            document=other.document,
            diagnostics=self.diagnostics + other.diagnostics,
            files=self.files + other.files,
            metadata={**self.metadata, **other.metadata},
        )

    def has_errors(self) -> bool:
        """检查是否有错误诊断"""
        return any(d.get("level") == "error" for d in self.diagnostics)

    def has_warnings(self) -> bool:
        """检查是否有警告诊断"""
        return any(d.get("level") == "warning" for d in self.diagnostics)


@dataclass(slots=True)
class TransformPass(ABC):
    """
    转换 Pass 抽象基类。

    使用 dataclass 自动生成 __init__，支持 Python 3.13 最佳实践。

    属性:
        config: Pass 配置字典（始终为 dict，不会为 None）
        enabled: 是否启用
        priority: 执行优先级（数字越小越先执行）
        name: Pass 名称
    """
    config: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    priority: int = 100
    name: str = ""

    def __post_init__(self):
        """初始化后设置名称，并确保 config 是字典"""
        # ✅ 确保 config 永远是字典，即使传入 None
        if self.config is None:
            self.config = {}
        if not self.name:
            self.name = self.__class__.__name__

    @abstractmethod
    def run(
        self,
        document: Node,
        diag: DiagnosticCollector,
    ) -> PassResult:
        """
        执行 Pass。

        参数:
            document: AST 根节点
            diag: 诊断收集器

        返回:
            PassResult: 执行结果
        """
        pass

    def configure(self, config: Dict[str, Any]) -> None:
        """
        配置 Pass。

        参数:
            config: 配置字典
        """
        self.config = config or {}

    def is_applicable(self, document: Node) -> bool:
        """
        检查 Pass 是否适用于当前文档。

        默认返回 True，子类可以重写此方法实现条件执行。

        参数:
            document: AST 根节点

        返回:
            bool: 是否适用
        """
        return True

    def before_run(self, document: Node, diag: DiagnosticCollector) -> None:
        """执行前的钩子方法"""
        pass

    def after_run(self, result: PassResult, diag: DiagnosticCollector) -> None:
        """执行后的钩子方法"""
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, priority={self.priority}, enabled={self.enabled})"


# ============================================================
# 辅助 Pass 类
# ============================================================

class NoOpPass(TransformPass):
    """
    空操作 Pass。

    不执行任何转换，直接返回原始文档。
    可用于测试或占位。
    """

    def run(self, document: Node, diag: DiagnosticCollector) -> PassResult:
        return PassResult(document=document)


class CompositePass(TransformPass):
    """
    组合 Pass。

    按顺序执行多个子 Pass。
    """

    def __init__(
        self,
        passes: List[TransformPass],
        name: Optional[str] = None,
        **kwargs
    ):
        """
        初始化组合 Pass。

        参数:
            passes: 子 Pass 列表
            name: Pass 名称
        """
        super().__init__(**kwargs)
        self.passes = passes
        if name:
            self.name = name
        else:
            self.name = f"CompositePass[{','.join(p.name for p in passes)}]"

    def run(self, document: Node, diag: DiagnosticCollector) -> PassResult:
        result = PassResult(document=document)

        for pass_instance in self.passes:
            if not pass_instance.enabled:
                continue

            if not pass_instance.is_applicable(result.document):
                continue

            pass_instance.before_run(result.document, diag)
            sub_result = pass_instance.run(result.document, diag)
            result = result.merge(sub_result)
            pass_instance.after_run(sub_result, diag)

        return result


class ConditionalPass(TransformPass):
    """
    条件 Pass。

    仅在条件满足时执行子 Pass。
    """

    def __init__(
        self,
        pass_instance: TransformPass,
        condition: callable,
        name: Optional[str] = None,
        **kwargs
    ):
        """
        初始化条件 Pass。

        参数:
            pass_instance: 子 Pass
            condition: 条件函数，接受 document 和 diag，返回 bool
            name: Pass 名称
        """
        super().__init__(**kwargs)
        self.pass_instance = pass_instance
        self.condition = condition
        if name:
            self.name = name
        else:
            self.name = f"ConditionalPass[{pass_instance.name}]"

    def run(self, document: Node, diag: DiagnosticCollector) -> PassResult:
        if self.condition(document, diag):
            return self.pass_instance.run(document, diag)
        return PassResult(document=document)


# ============================================================
# 工厂函数
# ============================================================

def create_pass(pass_class: type, config: Optional[Dict[str, Any]] = None) -> TransformPass:
    """
    创建 Pass 实例的工厂函数。

    参数:
        pass_class: Pass 类
        config: Pass 配置

    返回:
        TransformPass: Pass 实例
    """
    if not issubclass(pass_class, TransformPass):
        raise TypeError(f"{pass_class.__name__} must be a subclass of TransformPass")

    return pass_class(config=config or {})