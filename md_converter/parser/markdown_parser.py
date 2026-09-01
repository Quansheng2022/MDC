"""
Markdown Parser - Markdown 到 AST 的解析器

使用 markdown-it-py 4.x 解析 Markdown 文本，
通过 BuilderRegistry 构建不可变 AST。

兼容 markdown-it-py 4.2.0+ API:
    - 使用 SyntaxTreeNode 替代 SyntaxTree
    - 使用 token.children 遍历
    - 使用 token.map 获取位置信息
"""

import re
from typing import Any, Dict, List, Optional

import markdown_it.rules_inline.state_inline as _state_inline
from markdown_it import MarkdownIt
from markdown_it.common.utils import isStrSpace
from markdown_it.rules_block.state_block import StateBlock
from markdown_it.token import Token
from markdown_it.tree import SyntaxTreeNode

from ..ast.nodes import Document, Node, SourceSpan
from ..constants.node_type import SYNTAX_TO_NODE_TYPE, NodeType
from ..diagnostics.collector import DiagnosticCollector
from .builder_registry import BuilderRegistry
from .builders.blockquote import BlockQuoteBuilder
from .builders.code import CodeBuilder
from .builders.heading import HeadingBuilder
from .builders.hr import HorizontalRuleBuilder
from .builders.list import ListBuilder
from .builders.paragraph import ParagraphBuilder
from .builders.table import TableBuilder
from .parser_context import ParserContext

# ============================================================
# CJK 加粗兼容补丁
# ============================================================
#
# CommonMark 的 Emphasis 侧翼规则中，`**“内容”**汉字` 或 `**"内容"**汉字`
# 的闭合 `**` 前是标点（`”`/`"`）、后跟汉字（字母），不满足“右翼”条件，
# 导致加粗解析失败；而 `**“底量超顶量”**。` 因后面是句号而成功。
# 这里把汉字（CJK 表意文字）计入“标点”，使闭合 `**` 后跟汉字时也能右翼，
# 修复中文排版中的加粗问题；纯 ASCII 场景行为与 CommonMark 完全一致。

_CJK_IDEOGRAPH_RE = re.compile(r"[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]")
_ORIGINAL_IS_PUNCT = _state_inline.isPunctChar
_CJK_PATCHED = False


def _is_punct_char_cjk(ch: str) -> bool:
    """汉字计入标点（其余行为与 markdown-it 一致）。"""
    if ch and _CJK_IDEOGRAPH_RE.match(ch):
        return True
    return _ORIGINAL_IS_PUNCT(ch)


def _patch_cjk_emphasis_flanking() -> None:
    """应用 CJK 侧翼补丁（幂等，仅生效一次）。"""
    global _CJK_PATCHED
    if _CJK_PATCHED:
        return
    _state_inline.isPunctChar = _is_punct_char_cjk
    _CJK_PATCHED = True


def _hr_rule_no_underscore(
    state: StateBlock,
    startLine: int,
    endLine: int,
    silent: bool,
) -> bool:
    """
    主题分隔线规则（不识别 `_`）。

    CommonMark 允许 `___` / `______` 作为分隔线，但中文模板常用 `______`
    作为填空占位符（如 `1. ______`），会被误解析为 <hr> 导致内容丢失。
    这里仅识别 `*` 与 `-` 作为分隔线标记。
    """
    pos = state.bMarks[startLine] + state.tShift[startLine]
    maximum = state.eMarks[startLine]

    if state.is_code_block(startLine):
        return False

    try:
        marker = state.src[pos]
    except IndexError:
        return False
    pos += 1

    if marker not in ("*", "-"):
        return False

    cnt = 1
    while pos < maximum:
        ch = state.src[pos]
        pos += 1
        if ch != marker and not isStrSpace(ch):
            return False
        if ch == marker:
            cnt += 1

    if cnt < 3:
        return False

    if silent:
        return True

    state.line = startLine + 1
    token = state.push("hr", "hr", 0)
    token.map = [startLine, state.line]
    token.markup = marker * (cnt + 1)
    return True


def _patch_hr_rule(md: MarkdownIt) -> None:
    """禁用 `_` 作为主题分隔线（避免 ______ 填空占位被解析为 <hr>）。"""
    md.block.ruler.at("hr", _hr_rule_no_underscore)


class MarkdownParser:
    """
    Markdown 解析器。

    使用 markdown-it-py 4.x 解析 Markdown，通过 BuilderRegistry
    将 SyntaxTreeNode 转换为 AST 节点。

    工作流程:
        1. 使用 markdown-it-py 解析文本得到 Token 列表
        2. 将 Token 列表转换为 SyntaxTreeNode 树
        3. 遍历 SyntaxTreeNode 树
        4. 对每个节点，从注册表获取对应的 Builder
        5. Builder 将 SyntaxTreeNode 转换为 AST 节点

    属性:
        ctx: ParserContext 上下文
        md: markdown-it-py 实例
        registry: BuilderRegistry 注册表
    """

    def __init__(self, ctx: ParserContext):
        """
        初始化解析器。

        参数:
            ctx: 解析器上下文，包含诊断收集器和配置
        """
        self.ctx = ctx
        # ✅ 使用 'default' 预设（内置表格、删除线、任务列表等）
        self.md = MarkdownIt("default")
        _patch_cjk_emphasis_flanking()
        _patch_hr_rule(self.md)
        self.registry = BuilderRegistry()
        self._register_builders()

    def _register_builders(self) -> None:
        """注册所有 Builder"""
        # 块节点 Builder
        self.registry.register(NodeType.HEADING, HeadingBuilder())
        self.registry.register(NodeType.PARAGRAPH, ParagraphBuilder())
        self.registry.register(NodeType.LIST_BLOCK, ListBuilder())
        self.registry.register(NodeType.TABLE, TableBuilder())
        self.registry.register(NodeType.CODE_BLOCK, CodeBuilder())
        self.registry.register(NodeType.BLOCK_QUOTE, BlockQuoteBuilder())
        self.registry.register(NodeType.HORIZONTAL_RULE, HorizontalRuleBuilder())

    def parse(self, text: str) -> Document:
        """
        解析 Markdown 文本为 Document AST。

        参数:
            text: Markdown 源文本

        返回:
            Document: AST 根节点

        异常:
            解析过程中的异常会被捕获并记录到诊断中
        """
        try:
            # 1. 解析为 Token 列表
            tokens = self.md.parse(text)

            # 2. 构建 SyntaxTreeNode 树 (markdown-it-py 4.x 方式)
            root = SyntaxTreeNode(tokens)

            # 3. 遍历根节点的子节点
            children: List[Node] = []
            for child in root.children:
                nodes = self._parse_node(child)
                children.extend(nodes)

            # 4. 构建 Document
            span = self._get_span(text)
            return Document(children=children, span=span)

        except Exception as e:
            self.ctx.diag.error(
                f"Parser error: {e}",
                code="PARSE001",
                suggestion="Please check your Markdown syntax",
            )
            import traceback

            traceback.print_exc()
            return Document(children=[])

    def _parse_node(self, node: SyntaxTreeNode) -> List[Node]:
        """
        解析单个 SyntaxTreeNode。

        参数:
            node: markdown-it-py 的 SyntaxTreeNode

        返回:
            List[Node]: AST 节点列表
        """
        # 获取节点类型
        node_type = SYNTAX_TO_NODE_TYPE.get(node.type)

        if node_type is None:
            # 未知节点类型，记录警告
            self.ctx.diag.warning(
                f"Unknown node type: '{node.type}'",
                code="MD003",
                location=self._get_node_span(node),
                suggestion="This node type is not supported yet",
            )
            # 尝试递归处理子节点
            children = []
            for child in node.children:
                children.extend(self._parse_node(child))
            return children

        # 获取对应的 Builder
        builder = self.registry.get(node_type)

        if builder is None:
            # 没有注册的 Builder
            self.ctx.diag.warning(
                f"No builder registered for node type: {node_type.name}",
                code="MD003",
                location=self._get_node_span(node),
            )
            return []

        # 使用 Builder 构建 AST
        try:
            ast_nodes = builder.build(node, self.ctx)
            return ast_nodes
        except Exception as e:
            self.ctx.diag.error(
                f"Builder error for {node_type.name}: {e}",
                code="BUILD001",
                location=self._get_node_span(node),
            )
            return []

    def _get_node_span(self, node: SyntaxTreeNode) -> Optional[SourceSpan]:
        """
        从 SyntaxTreeNode 获取源码位置信息。

        参数:
            node: SyntaxTreeNode

        返回:
            Optional[SourceSpan]: 源码位置
        """
        if node.map:
            return SourceSpan(
                start_line=node.map[0],
                start_col=0,
                end_line=node.map[1] - 1,
                end_col=0,
            )
        return None

    def _get_span(self, text: str) -> Optional[SourceSpan]:
        """
        获取文档的源码位置信息。

        参数:
            text: 完整文本

        返回:
            Optional[SourceSpan]: 文档的源码位置
        """
        lines = text.split("\n")
        if not lines:
            return None
        return SourceSpan(
            start_line=0,
            start_col=0,
            end_line=len(lines) - 1,
            end_col=len(lines[-1]) if lines[-1] else 0,
        )

    def parse_tokens(self, tokens: List[Token]) -> Document:
        """
        直接解析 Token 列表（高级用法）。

        参数:
            tokens: markdown-it-py Token 列表

        返回:
            Document: AST 根节点
        """
        try:
            root = SyntaxTreeNode(tokens)

            children: List[Node] = []
            for child in root.children:
                nodes = self._parse_node(child)
                children.extend(nodes)

            return Document(children=children)

        except Exception as e:
            self.ctx.diag.error(f"Parser error: {e}", code="PARSE001")
            return Document(children=[])

    def parse_inline(self, text: str) -> List[Node]:
        """
        解析行内文本（不包含块级元素）。

        用于解析上下文中的行内内容。

        参数:
            text: 行内文本

        返回:
            List[Node]: 行内节点列表
        """
        try:
            self.md.parse_inline(text)
            return []
        except Exception as e:
            self.ctx.diag.warning(f"Inline parse error: {e}", code="PARSE002")
            return []


# ============================================================
# 解析器工厂函数
# ============================================================


def create_parser(
    diag: Optional[DiagnosticCollector] = None, config: Optional[Dict[str, Any]] = None
) -> MarkdownParser:
    """
    创建 Markdown 解析器的工厂函数。

    参数:
        diag: 诊断收集器
        config: 配置字典

    返回:
        MarkdownParser: 解析器实例
    """
    if diag is None:
        diag = DiagnosticCollector()

    if config is None:
        config = {}

    ctx = ParserContext(diag=diag, config=config, frontmatter={})

    return MarkdownParser(ctx)


def parse_markdown(
    text: str, diag: Optional[DiagnosticCollector] = None, config: Optional[Dict[str, Any]] = None
) -> Document:
    """
    解析 Markdown 文本的便捷函数。

    参数:
        text: Markdown 源文本
        diag: 诊断收集器
        config: 配置字典

    返回:
        Document: AST 根节点
    """
    parser = create_parser(diag, config)
    return parser.parse(text)


def parse_markdown_file(
    file_path: str,
    diag: Optional[DiagnosticCollector] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Document:
    """
    解析 Markdown 文件的便捷函数。

    参数:
        file_path: 文件路径
        diag: 诊断收集器
        config: 配置字典

    返回:
        Document: AST 根节点
    """
    from pathlib import Path

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    return parse_markdown(text, diag, config)
