"""
Golden Test - 回归测试框架

使用 Golden Test 模式验证 Markdown 到 DOCX 的转换质量。
每个测试用例包含一个 Markdown 输入文件和期望的 DOCX 结构输出。
"""

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from md_converter.compiler import CompilerContext
from md_converter.utils.helpers import parse_frontmatter


def _mmdc_available() -> bool:
    """
    与 DiagramPass._check_mmdc 保持一致的探测：
    仅 ``shutil.which`` 找到不够（Windows .CMD shim 无法直接 CreateProcess），
    必须实际执行 ``mmdc --version`` 成功才视为可用。
    """
    try:
        result = subprocess.run(
            ["mmdc", "--version"],
            capture_output=True,
            timeout=5,
            check=False,
        )
        return result.returncode == 0
    except Exception:
        return False


def detect_mermaid_backend(diagnostics: List[Dict[str, Any]]) -> str:
    """
    识别本次 Golden 运行实际使用的 Mermaid 渲染后端（F5）。

    - 出现 DIAG002（Mermaid rendering failed）-> fallback
    - 否则 mmdc 可用 -> mmdc
    - 否则 -> playwright

    Golden baseline 必须与运行环境匹配；不允许“同一条 baseline 跨后端比较”。
    """
    if any(d.get("code") == "DIAG002" for d in diagnostics):
        return "fallback"
    if _mmdc_available():
        return "mmdc"
    return "playwright"


# ============================================================
# Golden Test 类
# ============================================================


class GoldenTest:
    """
    Golden Test 用例。

    管理单个 Golden Test 的输入、期望输出和验证。
    """

    def __init__(
        self,
        name: str,
        input_path: Path,
        expected_path: Path,
        update: bool = False,
    ):
        """
        初始化 Golden Test。

        参数:
            name: 测试名称
            input_path: 输入文件路径
            expected_path: 期望输出文件路径
            update: 是否更新期望输出
        """
        self.name = name
        self.input_path = input_path
        self.expected_path = expected_path
        self.update = update
        self._input_content: Optional[str] = None
        self._expected: Optional[Dict[str, Any]] = None
        self._actual: Optional[Dict[str, Any]] = None
        self._diagnostics: Optional[List[Dict[str, Any]]] = None

    @classmethod
    def from_golden_dir(
        cls,
        name: str,
        golden_dir: Path,
        update: bool = False,
    ) -> "GoldenTest":
        """
        从 Golden 目录创建测试用例。

        参数:
            name: 测试名称
            golden_dir: Golden 目录
            update: 是否更新期望输出

        返回:
            GoldenTest: 测试用例
        """
        input_path = golden_dir / f"{name}.md"
        expected_path = golden_dir / f"{name}.expected.json"
        return cls(name, input_path, expected_path, update)

    def load_input(self) -> str:
        """加载输入内容"""
        if self._input_content is None:
            with open(self.input_path, "r", encoding="utf-8") as f:
                self._input_content = f.read()
        return self._input_content

    def load_expected(self) -> Optional[Dict[str, Any]]:
        """加载期望输出"""
        if self._expected is None:
            if self.expected_path.exists():
                with open(self.expected_path, "r", encoding="utf-8") as f:
                    self._expected = json.load(f)
            else:
                self._expected = None
        return self._expected

    def save_expected(self, data: Dict[str, Any]) -> None:
        """保存期望输出"""
        self.expected_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.expected_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def run(self) -> Dict[str, Any]:
        """
        运行测试，返回实际输出。

        返回:
            Dict[str, Any]: 实际输出结构
        """

        # 解析输入
        content = self.load_input()
        body, meta = parse_frontmatter(content)

        # 创建编译器上下文
        config = {
            "verbose": True,
            "normalize": True,
            "diagram": True,
            "word_com": False,
        }
        ctx = CompilerContext.create(config)

        # 编译
        doc = ctx.compile(body)

        # 提取结构
        import tempfile

        from conftest import extract_docx_structure

        # 保存为临时文件
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            temp_path = f.name
        doc.save(temp_path)

        try:
            structure = extract_docx_structure(temp_path)
        finally:
            Path(temp_path).unlink(missing_ok=True)

        # 添加元数据
        structure["metadata"] = meta
        structure["diagnostics"] = [d.to_dict() for d in ctx.diag.diagnostics]
        structure["renderer_backend"] = detect_mermaid_backend(structure["diagnostics"])

        self._actual = structure
        self._diagnostics = [d.to_dict() for d in ctx.diag.diagnostics]

        return structure

    def compare(self) -> List[str]:
        """
        比较期望和实际输出。

        返回:
            List[str]: 差异列表
        """
        expected = self.load_expected()
        actual = self.run()

        if expected is None:
            # 首次运行，保存期望
            self.save_expected(actual)
            return ["Expected file created (first run)"]

        # F5：Golden 环境契约——运行后端必须与 baseline 后端一致，
        # 不允许在缺 Mermaid renderer 的环境里拿同一条 baseline 假装通过。
        expected_backend = expected.get("renderer_backend")
        actual_backend = actual.get("renderer_backend")
        if expected_backend and actual_backend != expected_backend:
            return [
                "Golden environment mismatch: "
                f"baseline renderer_backend={expected_backend!r}, "
                f"actual renderer_backend={actual_backend!r}. "
                "Run in the canonical Golden environment (see GOLDEN_ENVIRONMENT.md)."
            ]

        # 深度比较
        return self._deep_compare(expected, actual)

    def _deep_compare(
        self,
        expected: Any,
        actual: Any,
        path: str = "",
    ) -> List[str]:
        """
        深度比较两个值。

        参数:
            expected: 期望值
            actual: 实际值
            path: 当前路径

        返回:
            List[str]: 差异列表
        """
        differences = []

        # 不同类型
        if type(expected) is not type(actual):
            differences.append(
                f"{path}: Type mismatch: {type(expected).__name__} vs {type(actual).__name__}"
            )
            return differences

        # 字典
        if isinstance(expected, dict):
            expected_keys = set(expected.keys())
            actual_keys = set(actual.keys())
            volatile_keys = {"timestamp"}

            # 缺失的键
            missing = expected_keys - actual_keys
            for key in missing:
                if key in volatile_keys:
                    continue
                differences.append(f"{path}.{key}: Missing in actual")

            # 多余的键
            extra = actual_keys - expected_keys
            for key in extra:
                if key in volatile_keys:
                    continue
                differences.append(f"{path}.{key}: Extra in actual")

            # 共同键
            common = (expected_keys & actual_keys) - volatile_keys
            for key in common:
                diff = self._deep_compare(
                    expected[key], actual[key], f"{path}.{key}" if path else key
                )
                differences.extend(diff)

        # 列表
        elif isinstance(expected, list):
            if len(expected) != len(actual):
                differences.append(f"{path}: Length mismatch: {len(expected)} vs {len(actual)}")
            else:
                for i in range(len(expected)):
                    diff = self._deep_compare(expected[i], actual[i], f"{path}[{i}]")
                    differences.extend(diff)

        # 基本类型
        else:
            if expected != actual:
                differences.append(f"{path}: {expected} vs {actual}")

        return differences

    def assert_pass(self) -> None:
        """
        断言测试通过。

        异常:
            AssertionError: 如果测试失败
        """
        differences = self.compare()

        # 首次运行
        if len(differences) == 1 and "Expected file created" in differences[0]:
            return

        if differences:
            msg = f"Golden test '{self.name}' failed:\n"
            msg += "\n".join(f"  {d}" for d in differences[:20])
            if len(differences) > 20:
                msg += f"\n  ... and {len(differences) - 20} more differences"
            raise AssertionError(msg)

    def update_expected(self) -> None:
        """
        更新期望输出。
        """
        actual = self.run()
        self.save_expected(actual)


# ============================================================
# Golden Test 收集器
# ============================================================


class GoldenTestCollector:
    """
    Golden Test 收集器。

    发现和管理所有 Golden Test 用例。
    """

    def __init__(self, golden_dir: Path):
        """
        初始化 Golden Test 收集器。

        参数:
            golden_dir: Golden 目录
        """
        self.golden_dir = Path(golden_dir)
        self.tests: Dict[str, GoldenTest] = {}

    def discover(self) -> None:
        """
        发现所有 Golden Test 用例。
        """
        # 查找所有 .md 文件
        for md_file in self.golden_dir.glob("*.md"):
            name = md_file.stem
            self.tests[name] = GoldenTest.from_golden_dir(name, self.golden_dir)

    def get_test_names(self) -> List[str]:
        """获取所有测试名称"""
        return list(self.tests.keys())

    def get_test(self, name: str) -> Optional[GoldenTest]:
        """获取测试用例"""
        return self.tests.get(name)

    def run_all(self, update: bool = False) -> Dict[str, bool]:
        """
        运行所有测试。

        参数:
            update: 是否更新期望输出

        返回:
            Dict[str, bool]: 测试结果
        """
        results = {}
        for name, test in self.tests.items():
            try:
                if update:
                    test.update_expected()
                    results[name] = True
                else:
                    test.assert_pass()
                    results[name] = True
            except AssertionError:
                results[name] = False
        return results


# ============================================================
# Pytest 测试函数
# ============================================================


def pytest_generate_tests(metafunc):
    """
    动态生成 Golden Test 参数。
    """
    if "golden_test" in metafunc.fixturenames:
        # 查找 golden 目录
        golden_dir = Path(metafunc.module.__file__).parent / "golden"
        if golden_dir.exists():
            collector = GoldenTestCollector(golden_dir)
            collector.discover()
            metafunc.parametrize(
                "golden_test",
                list(collector.tests.values()),
                ids=list(collector.tests.keys()),
            )


@pytest.mark.golden
def test_golden(golden_test: GoldenTest):
    """
    运行 Golden Test。

    参数:
        golden_test: Golden Test 用例
    """
    golden_test.assert_pass()


# ============================================================
# 手动运行 Golden Test
# ============================================================


def run_golden_tests(
    golden_dir: Path,
    update: bool = False,
    verbose: bool = True,
) -> Dict[str, bool]:
    """
    手动运行 Golden Test。

    参数:
        golden_dir: Golden 目录
        update: 是否更新期望输出
        verbose: 是否显示详细信息

    返回:
        Dict[str, bool]: 测试结果
    """
    collector = GoldenTestCollector(golden_dir)
    collector.discover()

    if verbose:
        print(f"\n📋 Running {len(collector.tests)} Golden Tests\n")

    results = collector.run_all(update)

    if verbose:
        passed = sum(1 for v in results.values() if v)
        failed = len(results) - passed
        print(f"\n📊 Results: {passed} passed, {failed} failed\n")

        if failed > 0:
            for name, passed in results.items():
                if not passed:
                    print(f"  ❌ {name}")

    return results


# ============================================================
# 命令行入口
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Golden Tests")
    parser.add_argument(
        "--golden-dir",
        type=Path,
        default=Path(__file__).parent / "golden",
        help="Golden directory path",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update expected outputs",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose output",
    )
    args = parser.parse_args()

    results = run_golden_tests(
        args.golden_dir,
        update=args.update,
        verbose=not args.quiet,
    )

    if not all(results.values()):
        exit(1)
