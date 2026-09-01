"""
Diagnostic Collector - 诊断收集器

收集和管理诊断信息，提供过滤、统计和输出功能。
支持多种输出格式和诊断级别过滤。
"""

import json
import sys
from collections import defaultdict
from typing import Any, Dict, Iterator, List, Optional

from ..ast.nodes import SourceSpan
from .diagnostic import Diagnostic, Severity


class DiagnosticCollector:
    """
    诊断收集器。

    收集和管理诊断信息，支持：
        - 添加诊断
        - 过滤和查询
        - 统计信息
        - 多种输出格式
        - 严重级别控制

    属性:
        diagnostics: 诊断列表
        max_count: 最大诊断数量（防止内存溢出）
        min_severity: 最低严重级别（低于此级别的诊断不会被收集）

    示例:
        >>> collector = DiagnosticCollector()
        >>> collector.warning("Image not found", code="MD001")
        >>> collector.error("Parse error", code="PARSE001")
        >>> collector.report()
    """

    def __init__(
        self,
        max_count: int = 10000,
        min_severity: Severity = Severity.INFO,
    ):
        """
        初始化诊断收集器。

        参数:
            max_count: 最大诊断数量
            min_severity: 最低严重级别
        """
        self.diagnostics: List[Diagnostic] = []
        self.max_count = max_count
        self.min_severity = min_severity
        self._counts: Dict[str, int] = defaultdict(int)
        self._source_map: Dict[str, List[Diagnostic]] = defaultdict(list)

    # ============================================================
    # 添加诊断
    # ============================================================

    def add(self, diagnostic: Diagnostic) -> None:
        """
        添加诊断。

        参数:
            diagnostic: 诊断信息
        """
        # 检查严重级别
        if diagnostic.severity.value < self.min_severity.value:
            return

        # 检查数量限制
        if len(self.diagnostics) >= self.max_count:
            self.diagnostics.append(
                Diagnostic.error(
                    f"Too many diagnostics (limit {self.max_count})",
                    code="DIAG001",
                )
            )
            return

        self.diagnostics.append(diagnostic)
        self._counts[diagnostic.severity.name] += 1

        if diagnostic.source:
            self._source_map[diagnostic.source].append(diagnostic)

    def info(
        self,
        message: str,
        code: str = "INFO000",
        location: Optional[SourceSpan] = None,
        suggestion: Optional[str] = None,
        source: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """添加信息诊断"""
        self.add(Diagnostic.info(message, code, location, suggestion, source, data))

    def warning(
        self,
        message: str,
        code: str = "WARN000",
        location: Optional[SourceSpan] = None,
        suggestion: Optional[str] = None,
        source: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """添加警告诊断"""
        self.add(Diagnostic.warning(message, code, location, suggestion, source, data))

    def error(
        self,
        message: str,
        code: str = "ERR000",
        location: Optional[SourceSpan] = None,
        suggestion: Optional[str] = None,
        source: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """添加错误诊断"""
        self.add(Diagnostic.error(message, code, location, suggestion, source, data))

    def fatal(
        self,
        message: str,
        code: str = "FATAL000",
        location: Optional[SourceSpan] = None,
        suggestion: Optional[str] = None,
        source: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """添加致命错误诊断"""
        self.add(Diagnostic.fatal(message, code, location, suggestion, source, data))

    # ============================================================
    # 查询方法
    # ============================================================

    def get_diagnostics(
        self,
        severity: Optional[Severity] = None,
        code: Optional[str] = None,
        source: Optional[str] = None,
        min_severity: Optional[Severity] = None,
    ) -> List[Diagnostic]:
        """
        获取诊断列表（支持过滤）。

        参数:
            severity: 按严重级别过滤
            code: 按诊断代码过滤
            source: 按来源过滤
            min_severity: 最低严重级别

        返回:
            List[Diagnostic]: 诊断列表
        """
        result = self.diagnostics

        if severity is not None:
            result = [d for d in result if d.severity == severity]

        if code is not None:
            result = [d for d in result if d.code == code]

        if source is not None:
            result = [d for d in result if d.source == source]

        if min_severity is not None:
            result = [d for d in result if d.severity.value >= min_severity.value]

        return result

    def get_errors(self) -> List[Diagnostic]:
        """获取所有错误（包括 ERROR 和 FATAL）"""
        return [d for d in self.diagnostics if d.is_error()]

    def get_warnings(self) -> List[Diagnostic]:
        """获取所有警告"""
        return [d for d in self.diagnostics if d.is_warning()]

    def get_info(self) -> List[Diagnostic]:
        """获取所有信息"""
        return [d for d in self.diagnostics if d.is_info()]

    def get_by_code(self, code: str) -> List[Diagnostic]:
        """按诊断代码获取"""
        return [d for d in self.diagnostics if d.code == code]

    def get_by_source(self, source: str) -> List[Diagnostic]:
        """按来源获取"""
        return self._source_map.get(source, [])

    def get_first_error(self) -> Optional[Diagnostic]:
        """获取第一个错误"""
        for d in self.diagnostics:
            if d.is_error():
                return d
        return None

    def get_last_error(self) -> Optional[Diagnostic]:
        """获取最后一个错误"""
        for d in reversed(self.diagnostics):
            if d.is_error():
                return d
        return None

    # ============================================================
    # 统计信息
    # ============================================================

    def get_counts(self) -> Dict[str, int]:
        """
        获取诊断统计信息。

        返回:
            Dict[str, int]: 各严重级别的诊断数量
        """
        return dict(self._counts)

    def get_total(self) -> int:
        """获取诊断总数"""
        return len(self.diagnostics)

    def has_errors(self) -> bool:
        """检查是否有错误"""
        return self._counts.get(Severity.ERROR.name, 0) > 0

    def has_fatal(self) -> bool:
        """检查是否有致命错误"""
        return self._counts.get(Severity.FATAL.name, 0) > 0

    def has_warnings(self) -> bool:
        """检查是否有警告"""
        return self._counts.get(Severity.WARNING.name, 0) > 0

    def has_info(self) -> bool:
        """检查是否有信息"""
        return self._counts.get(Severity.INFO.name, 0) > 0

    def get_summary(self) -> Dict[str, Any]:
        """
        获取诊断摘要。

        返回:
            Dict[str, Any]: 摘要信息
        """
        return {
            "total": self.get_total(),
            "counts": self.get_counts(),
            "has_errors": self.has_errors(),
            "has_fatal": self.has_fatal(),
            "has_warnings": self.has_warnings(),
            "has_info": self.has_info(),
            "sources": list(self._source_map.keys()),
        }

    # ============================================================
    # 输出方法
    # ============================================================

    def report(
        self,
        output=None,
        verbose: bool = False,
        colorful: bool = True,
    ) -> None:
        """
        输出诊断报告。

        参数:
            output: 输出流（默认 stdout）
            verbose: 是否显示详细信息
            colorful: 是否使用彩色输出
        """
        if output is None:
            output = sys.stdout

        if not self.diagnostics:
            print("✅ No diagnostics", file=output)
            return

        # 按严重级别排序
        sorted_diags = sorted(
            self.diagnostics,
            key=lambda d: d.severity.value,
            reverse=True,
        )

        for diag in sorted_diags:
            print(diag.format(colorful=colorful), file=output)
            if verbose and diag.data:
                print(f"  Data: {json.dumps(diag.data, ensure_ascii=False)}", file=output)

        # 输出摘要
        summary = self.get_summary()
        print(f"\n📊 Summary: {summary['total']} diagnostics", file=output)
        for severity, count in summary["counts"].items():
            print(f"  {severity}: {count}", file=output)

    def to_json(self, indent: int = 2) -> str:
        """
        导出为 JSON 格式。

        参数:
            indent: 缩进空格数

        返回:
            str: JSON 字符串
        """
        data = {
            "summary": self.get_summary(),
            "diagnostics": [d.to_dict() for d in self.diagnostics],
        }
        return json.dumps(data, ensure_ascii=False, indent=indent)

    def to_dict(self) -> Dict[str, Any]:
        """
        导出为字典。

        返回:
            Dict[str, Any]: 诊断数据
        """
        return {
            "summary": self.get_summary(),
            "diagnostics": [d.to_dict() for d in self.diagnostics],
        }

    @classmethod
    def from_json(cls, json_str: str) -> "DiagnosticCollector":
        """
        从 JSON 导入诊断。

        参数:
            json_str: JSON 字符串

        返回:
            DiagnosticCollector: 诊断收集器
        """
        data = json.loads(json_str)
        collector = cls()
        for diag_data in data.get("diagnostics", []):
            collector.add(Diagnostic.from_dict(diag_data))
        return collector

    # ============================================================
    # 过滤和清理
    # ============================================================

    def filter(
        self,
        severity: Optional[Severity] = None,
        code: Optional[str] = None,
        source: Optional[str] = None,
    ) -> "DiagnosticCollector":
        """
        过滤诊断，返回新的收集器。

        参数:
            severity: 按严重级别过滤
            code: 按诊断代码过滤
            source: 按来源过滤

        返回:
            DiagnosticCollector: 新的诊断收集器
        """
        new_collector = DiagnosticCollector(
            max_count=self.max_count,
            min_severity=self.min_severity,
        )

        for diag in self.get_diagnostics(severity, code, source):
            new_collector.add(diag)

        return new_collector

    def clear(self) -> None:
        """清空所有诊断"""
        self.diagnostics.clear()
        self._counts.clear()
        self._source_map.clear()

    def remove_by_code(self, code: str) -> int:
        """
        移除指定代码的诊断。

        参数:
            code: 诊断代码

        返回:
            int: 移除的诊断数量
        """
        removed = 0
        self.diagnostics = [d for d in self.diagnostics if d.code != code]
        # 重新计算计数
        self._counts.clear()
        for d in self.diagnostics:
            self._counts[d.severity.name] += 1
        return removed

    # ============================================================
    # 迭代器支持
    # ============================================================

    def __iter__(self) -> Iterator[Diagnostic]:
        return iter(self.diagnostics)

    def __len__(self) -> int:
        return len(self.diagnostics)

    def __getitem__(self, index: int) -> Diagnostic:
        return self.diagnostics[index]

    def __repr__(self) -> str:
        summary = self.get_summary()
        return f"DiagnosticCollector(total={summary['total']}, errors={summary['counts'].get('ERROR', 0)}, warnings={summary['counts'].get('WARNING', 0)})"


# ============================================================
# 全局诊断收集器（单例）
# ============================================================

_global_collector: Optional[DiagnosticCollector] = None


def get_global_collector() -> DiagnosticCollector:
    """
    获取全局诊断收集器。

    返回:
        DiagnosticCollector: 全局收集器
    """
    global _global_collector
    if _global_collector is None:
        _global_collector = DiagnosticCollector()
    return _global_collector


def reset_global_collector() -> None:
    """重置全局诊断收集器"""
    global _global_collector
    _global_collector = None


def add_diagnostic(diagnostic: Diagnostic) -> None:
    """添加诊断到全局收集器"""
    get_global_collector().add(diagnostic)


def info(
    message: str,
    code: str = "INFO000",
    location: Optional[SourceSpan] = None,
    suggestion: Optional[str] = None,
    source: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
) -> None:
    """添加信息诊断到全局收集器"""
    get_global_collector().info(message, code, location, suggestion, source, data)


def warning(
    message: str,
    code: str = "WARN000",
    location: Optional[SourceSpan] = None,
    suggestion: Optional[str] = None,
    source: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
) -> None:
    """添加警告诊断到全局收集器"""
    get_global_collector().warning(message, code, location, suggestion, source, data)


def error(
    message: str,
    code: str = "ERR000",
    location: Optional[SourceSpan] = None,
    suggestion: Optional[str] = None,
    source: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
) -> None:
    """添加错误诊断到全局收集器"""
    get_global_collector().error(message, code, location, suggestion, source, data)