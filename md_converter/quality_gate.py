"""
Quality Gate - 编译质量门（P0-05 / P0-06 / P0-07）

统一 StaticQA / RenderedQA / FinalArtifactQA 的 Gate 语义：

    QualityGatePolicy（配置） -> decide_qa（决策表） -> QualityGateDecision

核心原则:
    - FAIL 不得静默进入下一阶段（默认 fail_on_error=True）。
    - QA 基础设施自身异常 = FAIL CLOSED，必须转为 QualityGateError。
    - Repair 是有界闭环（max_repair_iterations），不允许无限循环。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

# 完整 Gate 序列（CANONICAL_SPEC.md §4）
GATE_SEQUENCE = (
    "static_qa",
    "rendered_qa",
    "repair",
    "post_processor",
    "final_artifact_qa",
)


class QualityGateDecision(str, Enum):
    """质量门决策。"""

    CONTINUE = "CONTINUE"
    REPAIR = "REPAIR"
    ABORT = "ABORT"


@dataclass(frozen=True)
class QualityGatePolicy:
    """
    Governance Policy。

    属性:
        fail_on_error: 存在 error（FAIL）时是否阻止进入下一阶段
        fail_on_warning: 存在 warning（PASS_WITH_WARN）时是否阻止
        max_repair_iterations: 修复闭环最大迭代次数（有界）
    """

    fail_on_error: bool = True
    fail_on_warning: bool = False
    max_repair_iterations: int = 2

    @classmethod
    def from_config(cls, config: Optional[Dict[str, Any]] = None) -> "QualityGatePolicy":
        """
        从配置构建策略。

        优先读取 ``quality_gate`` 配置节；兼容顶层 ``fail_on_error`` /
        ``fail_on_warning`` / ``max_repair_iterations`` 键。
        """
        cfg: Dict[str, Any] = {}
        if config:
            section = config.get("quality_gate") or {}
            if isinstance(section, dict):
                cfg.update(section)
            for key in ("fail_on_error", "fail_on_warning", "max_repair_iterations"):
                if key not in cfg and key in config:
                    cfg[key] = config[key]
        return cls(
            fail_on_error=bool(cfg.get("fail_on_error", True)),
            fail_on_warning=bool(cfg.get("fail_on_warning", False)),
            max_repair_iterations=max(0, int(cfg.get("max_repair_iterations", 2))),
        )


def decide_qa(status: str, repairable: bool, policy: QualityGatePolicy) -> QualityGateDecision:
    """
    质量门决策表。

    参数:
        status: PASS | PASS_WITH_WARN | FAIL
        repairable: 是否存在可用的修复策略
        policy: Governance Policy

    返回:
        QualityGateDecision: CONTINUE / REPAIR / ABORT

    规则:
        PASS                     -> CONTINUE
        PASS_WITH_WARN           -> ABORT if fail_on_warning else REPAIR/ CONTINUE
        FAIL + fail_on_error=False -> CONTINUE（记录警告，非静默）
        FAIL + repairable        -> REPAIR
        FAIL + unrepairable      -> ABORT
    """
    if status == "PASS":
        return QualityGateDecision.CONTINUE
    if status == "PASS_WITH_WARN":
        if policy.fail_on_warning:
            return QualityGateDecision.ABORT
        return QualityGateDecision.REPAIR if repairable else QualityGateDecision.CONTINUE
    # FAIL
    if not policy.fail_on_error:
        return QualityGateDecision.CONTINUE
    return QualityGateDecision.REPAIR if repairable else QualityGateDecision.ABORT


class QualityGateError(Exception):
    """
    质量门失败异常。

    属性:
        stage: static_qa | rendered_qa | repair | post_processor | final_artifact_qa
        result: 对应 QA 结果对象
    """

    def __init__(
        self,
        stage: str,
        result: Any,
        message: Optional[str] = None,
    ):
        self.stage = stage
        self.result = result
        status = getattr(result, "status", "UNKNOWN")
        self.message = message or (f"Quality gate failed at stage '{stage}' with status {status}")
        super().__init__(self.message)


@dataclass
class RepairRecord:
    """
    单次修复的证据记录。

    属性:
        repair_iteration: 第几次修复（0 起）
        original_issue: 触发修复的 issue 描述（code + message）
        selected_strategy: 选中的修复策略
        changed_blocks: 被修改的 block id 列表
        before_status: 修复前 QA 状态
        after_status: 修复后 QA 状态（Re-inspect 结果）
    """

    repair_iteration: int
    original_issue: Dict[str, Any]
    selected_strategy: str
    changed_blocks: List[str] = field(default_factory=list)
    before_status: str = ""
    after_status: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "repair_iteration": self.repair_iteration,
            "original_issue": self.original_issue,
            "selected_strategy": self.selected_strategy,
            "changed_blocks": list(self.changed_blocks),
            "before_status": self.before_status,
            "after_status": self.after_status,
        }
