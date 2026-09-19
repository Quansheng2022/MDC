"""
Pipeline - 文档处理管道

执行一系列 Pass 对 AST 进行转换。
支持插件化扩展，所有 Pass 按注册顺序执行。
"""

from typing import Any, Dict, List, Optional

from ..ast.nodes import Document, Node
from ..diagnostics.collector import DiagnosticCollector
from .passes.base import TransformPass


class Pipeline:
    """
    文档处理管道。

    按顺序执行传入的 Pass 列表，对 AST 进行转换。
    每个 Pass 接收 AST 和诊断收集器，返回转换后的 AST。

    属性:
        passes: Pass 列表
        diagnostics: 执行过程中的诊断信息

    示例:
        >>> pipeline = Pipeline([NormalizePass(), DiagramPass()])
        >>> new_ast = pipeline.run(ast, diag)
    """

    def __init__(self, passes: Optional[List[TransformPass]] = None):
        """
        初始化管道。

        参数:
            passes: Pass 实例列表
        """
        self._passes = passes or []
        self.diagnostics: List[Dict[str, Any]] = []

    def add_pass(self, pass_instance: TransformPass) -> None:
        """
        添加 Pass。

        参数:
            pass_instance: Pass 实例
        """
        self._passes.append(pass_instance)

    def insert_pass(self, index: int, pass_instance: TransformPass) -> None:
        """
        在指定位置插入 Pass。

        参数:
            index: 插入位置
            pass_instance: Pass 实例
        """
        self._passes.insert(index, pass_instance)

    def remove_pass(self, pass_instance: TransformPass) -> bool:
        """
        移除 Pass。

        参数:
            pass_instance: Pass 实例

        返回:
            bool: 是否成功移除
        """
        try:
            self._passes.remove(pass_instance)
            return True
        except ValueError:
            return False

    def clear_passes(self) -> None:
        """清空所有 Pass"""
        self._passes.clear()

    def get_passes(self) -> List[TransformPass]:
        """
        获取所有 Pass。

        返回:
            List[TransformPass]: Pass 列表
        """
        return self._passes

    def run(
        self,
        document: Node,
        diag: Optional[DiagnosticCollector] = None,
    ) -> Node:
        """
        执行管道。

        参数:
            document: AST 根节点
            diag: 诊断收集器（可选）

        返回:
            Node: 转换后的 AST
        """
        if diag is None:
            diag = DiagnosticCollector()

        self.diagnostics.clear()
        current_doc = document

        print(f"[Pipeline] Running with {len(self._passes)} passes: {[p.__class__.__name__ for p in self._passes]}")

        for pass_instance in self._passes:
            try:
                print(f"[Pipeline] Executing pass: {pass_instance.__class__.__name__}")
                result = pass_instance.run(current_doc, diag)

                # 收集诊断
                if result.diagnostics:
                    self.diagnostics.extend(result.diagnostics)

                # 更新文档
                current_doc = result.document

            except Exception as e:
                diag.error(
                    f"Pass '{pass_instance.__class__.__name__}' failed: {e}",
                    code="PIPE001",
                )
                import traceback
                traceback.print_exc()
                # Required pass failure must fail closed; do not bypass the stage.
                raise

        return current_doc

    def run_on_document(
        self,
        document: Document,
        diag: Optional[DiagnosticCollector] = None,
    ) -> Document:
        """
        执行管道（Document 类型安全版本）。

        参数:
            document: Document 节点
            diag: 诊断收集器（可选）

        返回:
            Document: 转换后的 Document
        """
        result = self.run(document, diag)
        if not isinstance(result, Document):
            raise TypeError(f"Pipeline returned {type(result).__name__}, expected Document")
        return result

    def get_stats(self) -> Dict[str, Any]:
        """
        获取管道执行统计信息。

        返回:
            Dict[str, Any]: 统计信息
        """
        return {
            "total_passes": len(self._passes),
            "diagnostics_count": len(self.diagnostics),
            "passes": [p.__class__.__name__ for p in self._passes],
        }

    # ============================================================
    # 魔法方法
    # ============================================================

    def __repr__(self) -> str:
        pass_names = [p.__class__.__name__ for p in self._passes]
        return f"Pipeline(passes={pass_names})"

    def __len__(self) -> int:
        return len(self._passes)

    def __iter__(self):
        return iter(self._passes)

    def __getitem__(self, index: int) -> TransformPass:
        return self._passes[index]
