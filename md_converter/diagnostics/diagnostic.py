"""
Diagnostic - 诊断信息定义

提供统一的诊断信息格式，包括严重级别、代码、消息、位置和建议。
支持诊断的序列化和格式化输出。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, Optional

from ..ast.nodes import SourceSpan


class Severity(Enum):
    """
    诊断严重级别。

    INFO: 信息
    WARNING: 警告
    ERROR: 错误
    FATAL: 致命错误
    """
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    FATAL = auto()

    def __str__(self) -> str:
        return self.name

    @property
    def symbol(self) -> str:
        """获取严重级别的符号表示"""
        symbols = {
            Severity.INFO: "ℹ️",
            Severity.WARNING: "⚠️",
            Severity.ERROR: "❌",
            Severity.FATAL: "💀",
        }
        return symbols.get(self, "•")

    @property
    def color(self) -> str:
        """获取严重级别的颜色代码（用于终端输出）"""
        colors = {
            Severity.INFO: "\033[94m",      # 蓝色
            Severity.WARNING: "\033[93m",   # 黄色
            Severity.ERROR: "\033[91m",     # 红色
            Severity.FATAL: "\033[95m",     # 紫色
        }
        return colors.get(self, "\033[0m")


class DiagnosticCode:
    """
    诊断代码常量。

    格式: [分类][编号]
    分类:
        - MD: Markdown 相关
        - AST: AST 相关
        - PARSE: 解析相关
        - RENDER: 渲染相关
        - PASS: Pass 相关
        - PLUGIN: 插件相关
        - CONFIG: 配置相关
        - IO: 文件 I/O 相关
        - DIAG: 诊断系统本身
    """

    # Markdown 相关
    MD001 = "MD001"  # 图片缺失
    MD002 = "MD002"  # 表格解析错误
    MD003 = "MD003"  # 未知节点类型
    MD004 = "MD004"  # 图表渲染失败
    MD005 = "MD005"  # 链接无效
    MD006 = "MD006"  # 脚注缺失

    # AST 相关
    AST001 = "AST001"  # AST 结构错误
    AST002 = "AST002"  # 节点类型不匹配
    AST003 = "AST003"  # 节点位置缺失

    # 解析相关
    PARSE001 = "PARSE001"  # 解析错误
    PARSE002 = "PARSE002"  # 行内解析错误
    PARSE003 = "PARSE003"  # Frontmatter 解析错误

    # 渲染相关
    RENDER001 = "RENDER001"  # 渲染错误
    RENDER002 = "RENDER002"  # 图片渲染失败
    RENDER003 = "RENDER003"  # 表格渲染失败

    # Pass 相关
    PASS001 = "PASS001"  # Pass 执行错误
    PASS002 = "PASS002"  # Pass 配置错误
    PASS003 = "PASS003"  # Pass 依赖缺失

    # 插件相关
    PLUGIN001 = "PLUGIN001"  # 插件发现错误
    PLUGIN002 = "PLUGIN002"  # 插件加载错误
    PLUGIN003 = "PLUGIN003"  # 插件版本不兼容

    # 配置相关
    CONFIG001 = "CONFIG001"  # 配置加载错误
    CONFIG002 = "CONFIG002"  # 配置验证错误

    # I/O 相关
    IO001 = "IO001"  # 文件读取错误
    IO002 = "IO002"  # 文件写入错误
    IO003 = "IO003"  # 文件不存在

    # 诊断系统
    DIAG001 = "DIAG001"  # 诊断系统内部错误

    @classmethod
    def get_category(cls, code: str) -> str:
        """获取诊断代码的分类"""
        categories = {
            "MD": "Markdown",
            "AST": "AST",
            "PARSE": "Parsing",
            "RENDER": "Rendering",
            "PASS": "Pass",
            "PLUGIN": "Plugin",
            "CONFIG": "Configuration",
            "IO": "I/O",
            "DIAG": "Diagnostic",
        }
        prefix = code[:2]
        return categories.get(prefix, "Unknown")

    @classmethod
    def get_description(cls, code: str) -> str:
        """获取诊断代码的描述"""
        descriptions = {
            cls.MD001: "Image file not found",
            cls.MD002: "Table parsing error",
            cls.MD003: "Unknown node type",
            cls.MD004: "Diagram rendering failed",
            cls.MD005: "Invalid link",
            cls.MD006: "Footnote definition missing",

            cls.AST001: "AST structure error",
            cls.AST002: "Node type mismatch",
            cls.AST003: "Node location missing",

            cls.PARSE001: "Markdown parsing error",
            cls.PARSE002: "Inline parsing error",
            cls.PARSE003: "Frontmatter parsing error",

            cls.RENDER001: "Rendering error",
            cls.RENDER002: "Image rendering failed",
            cls.RENDER003: "Table rendering failed",

            cls.PASS001: "Pass execution error",
            cls.PASS002: "Pass configuration error",
            cls.PASS003: "Pass dependency missing",

            cls.PLUGIN001: "Plugin discovery error",
            cls.PLUGIN002: "Plugin loading error",
            cls.PLUGIN003: "Plugin version incompatible",

            cls.CONFIG001: "Configuration loading error",
            cls.CONFIG002: "Configuration validation error",

            cls.IO001: "File read error",
            cls.IO002: "File write error",
            cls.IO003: "File not found",

            cls.DIAG001: "Diagnostic system error",
        }
        return descriptions.get(code, "Unknown error")


@dataclass
class Diagnostic:
    """
    诊断信息。

    属性:
        severity: 严重级别
        code: 诊断代码
        message: 诊断消息
        location: 源码位置（可选）
        suggestion: 修复建议（可选）
        timestamp: 诊断时间戳
        source: 诊断来源（可选）
        data: 附加数据（可选）
    """
    severity: Severity
    code: str
    message: str
    location: Optional[SourceSpan] = None
    suggestion: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """初始化后验证"""
        if not self.code:
            self.code = "UNKNOWN"

    @classmethod
    def info(
        cls,
        message: str,
        code: str = "INFO000",
        location: Optional[SourceSpan] = None,
        suggestion: Optional[str] = None,
        source: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> "Diagnostic":
        """创建信息诊断"""
        return cls(
            severity=Severity.INFO,
            code=code,
            message=message,
            location=location,
            suggestion=suggestion,
            source=source,
            data=data,
        )

    @classmethod
    def warning(
        cls,
        message: str,
        code: str = "WARN000",
        location: Optional[SourceSpan] = None,
        suggestion: Optional[str] = None,
        source: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> "Diagnostic":
        """创建警告诊断"""
        return cls(
            severity=Severity.WARNING,
            code=code,
            message=message,
            location=location,
            suggestion=suggestion,
            source=source,
            data=data,
        )

    @classmethod
    def error(
        cls,
        message: str,
        code: str = "ERR000",
        location: Optional[SourceSpan] = None,
        suggestion: Optional[str] = None,
        source: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> "Diagnostic":
        """创建错误诊断"""
        return cls(
            severity=Severity.ERROR,
            code=code,
            message=message,
            location=location,
            suggestion=suggestion,
            source=source,
            data=data,
        )

    @classmethod
    def fatal(
        cls,
        message: str,
        code: str = "FATAL000",
        location: Optional[SourceSpan] = None,
        suggestion: Optional[str] = None,
        source: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> "Diagnostic":
        """创建致命错误诊断"""
        return cls(
            severity=Severity.FATAL,
            code=code,
            message=message,
            location=location,
            suggestion=suggestion,
            source=source,
            data=data,
        )

    def is_error(self) -> bool:
        """检查是否为错误（包括 ERROR 和 FATAL）"""
        return self.severity in (Severity.ERROR, Severity.FATAL)

    def is_warning(self) -> bool:
        """检查是否为警告"""
        return self.severity == Severity.WARNING

    def is_info(self) -> bool:
        """检查是否为信息"""
        return self.severity == Severity.INFO

    def get_location_str(self) -> str:
        """获取位置字符串"""
        if self.location:
            return str(self.location)
        return "unknown location"

    def get_category(self) -> str:
        """获取诊断分类"""
        return DiagnosticCode.get_category(self.code)

    def get_description(self) -> str:
        """获取诊断描述"""
        return DiagnosticCode.get_description(self.code)

    def format(self, colorful: bool = True) -> str:
        """
        格式化诊断信息。

        参数:
            colorful: 是否使用彩色输出

        返回:
            str: 格式化的诊断信息
        """
        lines = []

        # 严重级别 + 代码
        if colorful:
            color = self.severity.color
            reset = "\033[0m"
            level_str = f"{color}{self.severity.symbol} {self.severity.name}{reset}"
        else:
            level_str = f"[{self.severity.name}]"

        code_str = f"[{self.code}]" if self.code else ""
        location_str = f" (at {self.get_location_str()})" if self.location else ""

        lines.append(f"{level_str} {code_str} {self.message}{location_str}")

        # 建议
        if self.suggestion:
            lines.append(f"  💡 {self.suggestion}")

        # 来源
        if self.source:
            lines.append(f"  📍 Source: {self.source}")

        # 分类和描述
        if self.code and self.code != "UNKNOWN":
            lines.append(f"  📂 {self.get_category()}: {self.get_description()}")

        # 附加数据
        if self.data:
            import json
            lines.append(f"  📊 Data: {json.dumps(self.data, ensure_ascii=False, indent=2)}")

        return '\n'.join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "severity": self.severity.name,
            "code": self.code,
            "message": self.message,
            "location": {
                "start_line": self.location.start_line,
                "start_col": self.location.start_col,
                "end_line": self.location.end_line,
                "end_col": self.location.end_col,
            } if self.location else None,
            "suggestion": self.suggestion,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "data": self.data,
            "category": self.get_category(),
            "description": self.get_description(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Diagnostic":
        """从字典创建诊断"""
        severity = Severity[data["severity"]]
        location = None
        if data.get("location"):
            loc = data["location"]
            location = SourceSpan(
                start_line=loc["start_line"],
                start_col=loc["start_col"],
                end_line=loc["end_line"],
                end_col=loc["end_col"],
            )
        return cls(
            severity=severity,
            code=data["code"],
            message=data["message"],
            location=location,
            suggestion=data.get("suggestion"),
            source=data.get("source"),
            data=data.get("data"),
        )


# ============================================================
# 诊断比较
# ============================================================

def compare_diagnostics(
    diag1: Diagnostic,
    diag2: Diagnostic,
) -> Dict[str, bool]:
    """
    比较两个诊断是否相同。

    返回:
        Dict[str, bool]: 比较结果
    """
    return {
        "severity": diag1.severity == diag2.severity,
        "code": diag1.code == diag2.code,
        "message": diag1.message == diag2.message,
        "location": diag1.location == diag2.location,
        "suggestion": diag1.suggestion == diag2.suggestion,
    }


def is_same_diagnostic(
    diag1: Diagnostic,
    diag2: Diagnostic,
    ignore_location: bool = False,
) -> bool:
    """
    检查两个诊断是否相同（语义比较）。

    参数:
        diag1: 第一个诊断
        diag2: 第二个诊断
        ignore_location: 是否忽略位置信息

    返回:
        bool: 是否相同
    """
    if diag1.severity != diag2.severity:
        return False
    if diag1.code != diag2.code:
        return False
    if diag1.message != diag2.message:
        return False
    if not ignore_location and diag1.location != diag2.location:
        return False
    return True