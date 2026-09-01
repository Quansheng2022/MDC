"""
ASCII → Mermaid 转换的数据模型

定义特征分析产出的纯数据结构，供类型检测器与转换器使用。
所有模型均为不可变 dataclass，保持与编译器架构一致。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class Box:
    """
    ASCII 图中的矩形方框。

    属性:
        x0: 左边界列（含）
        x1: 右边界列（含）
        y0: 上边界行（含）
        y1: 下边界行（含）
        lines: 方框内部文本行
    """

    x0: int
    x1: int
    y0: int
    y1: int
    lines: Tuple[str, ...] = ()

    @property
    def text(self) -> str:
        """方框内部合并文本（多行用换行连接）。"""
        return "\n".join(line.strip() for line in self.lines if line.strip())

    @property
    def center_x(self) -> float:
        return (self.x0 + self.x1) / 2.0

    @property
    def center_y(self) -> float:
        return (self.y0 + self.y1) / 2.0

    def contains_col(self, col: int) -> bool:
        return self.x0 <= col <= self.x1

    def contains_row(self, row: int) -> bool:
        return self.y0 <= row <= self.y1

    def overlaps_x(self, other: "Box") -> bool:
        return self.x0 <= other.x1 and other.x0 <= self.x1


@dataclass(frozen=True)
class Arrow:
    """
    ASCII 图中的箭头。

    属性:
        row: 箭头所在行
        col: 箭头字符所在列
        direction: 'down' | 'up' | 'right' | 'left'
        tail_row: 箭头尾部行（可能等于 row）
        tail_col: 箭头尾部列
        head_row: 箭头头部行（可能等于 row）
        head_col: 箭头头部列
        label: 箭头旁标签（可选）
        token: 原始箭头记号，如 '-->'、'->>'、'v'
    """

    row: int
    col: int
    direction: str
    tail_row: int
    tail_col: int
    head_row: int
    head_col: int
    label: str = ""
    token: str = ""


@dataclass(frozen=True)
class Lifeline:
    """
    时序图中的参与生命线。

    属性:
        col: 生命线所在列
        y0: 生命线起始行
        y1: 生命线结束行
        label: 参与者名称（来自上方标签框或文本）
    """

    col: int
    y0: int
    y1: int
    label: str = ""


@dataclass(frozen=True)
class Message:
    """
    时序图中的消息。

    属性:
        row: 消息所在行
        col0: 起始列
        col1: 结束列
        direction: 'right' | 'left'
        token: 箭头记号，如 '->'、'-->'、'->>'
        text: 消息文本（冒号后的内容）
    """

    row: int
    col0: int
    col1: int
    direction: str
    token: str
    text: str = ""


@dataclass(frozen=True)
class ClassSection:
    """
    类图中的一节内容。

    属性:
        kind: 'title' | 'attributes' | 'methods'
        lines: 该节文本行
    """

    kind: str
    lines: Tuple[str, ...] = ()


@dataclass(frozen=True)
class ClassBox:
    """
    类图中的一个类方框。

    属性:
        box: 原始方框
        name: 类名
        stereotype: 构造型，如 'interface' / 'abstract'（可选）
        sections: 分节内容
    """

    box: Box
    name: str
    stereotype: str = ""
    sections: Tuple[ClassSection, ...] = ()


@dataclass(frozen=True)
class ClassRelation:
    """
    类图关系。

    属性:
        src: 源类名
        dst: 目标类名
        kind: 'inheritance' | 'realization' | 'composition' | 'aggregation'
              | 'association' | 'dependency' | 'link'
        label: 关系标签（可选）
    """

    src: str
    dst: str
    kind: str
    label: str = ""


@dataclass(frozen=True)
class TreeNode:
    """
    思维导图/树结构节点。

    属性:
        text: 节点文本
        depth: 深度（根为 0）
        row: 来源行（用于稳定排序）
    """

    text: str
    depth: int
    row: int


@dataclass(frozen=True)
class DiagramFeatures:
    """
    ASCII 图特征汇总，供类型检测与转换使用。

    属性:
        grid: 规范化字符网格
        boxes: 检测到的方框
        arrows: 检测到的箭头
        lifelines: 检测到的生命线
        messages: 检测到的时序消息
        class_boxes: 检测到的类方框
        class_relations: 检测到的类关系
        tree_nodes: 检测到的树节点
        junction_rows: 存在分支连接符的行号集合
        horizontal_connectors: 水平连接符数量
        vertical_connectors: 垂直连接符数量
    """

    grid: Tuple[str, ...] = ()
    boxes: Tuple[Box, ...] = ()
    arrows: Tuple[Arrow, ...] = ()
    lifelines: Tuple[Lifeline, ...] = ()
    messages: Tuple[Message, ...] = ()
    class_boxes: Tuple[ClassBox, ...] = ()
    class_relations: Tuple[ClassRelation, ...] = ()
    tree_nodes: Tuple[TreeNode, ...] = ()
    junction_rows: Tuple[int, ...] = ()
    horizontal_connectors: int = 0
    vertical_connectors: int = 0

    @property
    def has_structure(self) -> bool:
        """是否存在可识别的图结构。"""
        return bool(
            self.boxes
            or self.arrows
            or self.lifelines
            or self.messages
            or self.class_boxes
            or self.tree_nodes
        )


@dataclass(frozen=True)
class TypeScore:
    """
    某图表类型的检测得分。

    属性:
        diagram_type: 'flowchart' | 'sequence' | 'class' | 'mindmap'
        confidence: 置信度，范围 0..1
        evidence: 证据说明
    """

    diagram_type: str
    confidence: float
    evidence: Tuple[str, ...] = ()


@dataclass(frozen=True)
class ConversionScheme:
    """
    单个 Mermaid 转换方案。

    属性:
        scheme_id: 方案标识，如 'scheme_1_flowchart'
        diagram_type: Mermaid 图类型
        confidence: 置信度
        mermaid: Mermaid 代码
        summary: 方案摘要（节点/边数量等）
    """

    scheme_id: str
    diagram_type: str
    confidence: float
    mermaid: str
    summary: Dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class ConversionPlan:
    """
    ASCII 图的分析与转换计划。

    属性:
        features: 特征分析结果
        detected_type: 自动检测的主类型
        scores: 各类型得分（按置信度降序）
        schemes: 可用转换方案（按置信度降序）
        original: 原始 ASCII 内容
    """

    features: DiagramFeatures
    detected_type: str
    scores: Tuple[TypeScore, ...] = ()
    schemes: Tuple[ConversionScheme, ...] = ()
    original: str = ""

    @property
    def best(self) -> Optional[ConversionScheme]:
        """最高置信度方案。"""
        return self.schemes[0] if self.schemes else None

    def select(
        self,
        mode: str = "auto",
        selector: Optional[callable] = None,
    ) -> Optional[ConversionScheme]:
        """
        按模式选择方案。

        参数:
            mode: 'auto'（最高置信度）、'interactive'（交互选择）、'preview'（最高置信度）
            selector: 交互选择回调，接收 ConversionPlan 返回 ConversionScheme

        返回:
            Optional[ConversionScheme]: 选中的方案；无可用方案时返回 None
        """
        if not self.schemes:
            return None
        if mode == "interactive" and selector is not None and len(self.schemes) > 1:
            chosen = selector(self)
            if chosen in self.schemes:
                return chosen
        return self.schemes[0]
