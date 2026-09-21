"""
Release Evidence - 发布证据（P1-10）

把整个多模型流程从“大家认为已经修好了”升级为“有证据证明这个版本可以发布”。

交付物:
    - RELEASE_EVIDENCE.md（给人 / ChatGPT Review 阅读）
    - release_evidence.json（给程序使用）

Release Decision 必须由规则生成，而不是由模型口头判断：
    - RELEASE_ELIGIBLE
    - RELEASE_BLOCKED

Default Deny 原则（修改项 3）:
    - 治理指标不允许默认 0；未检测（None / NOT_CHECKED）与 FAIL 同样 BLOCK。
    - Release Evidence 只读取/汇总证据，不制造证据。
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ============================================================
# Specification 元数据（与 CANONICAL_SPEC.md 头部保持一致）
# ============================================================

SPEC_VERSION = "1.1"
SPEC_STATUS = "FROZEN"
ARCHITECTURE_VERSION = "2.0"
THEME_VERSION = "QS-Word-Default-V1.5"
ACCEPTANCE_BASELINE = "AC001-AC015"
GOVERNANCE_BASELINE = "P0-01..P0-08, P1-09, P1-10"

# Canonical Required / Optional Test Suites（修改项 2）
REQUIRED_TEST_SUITES = ("unit", "integration", "golden", "acceptance")
OPTIONAL_TEST_SUITES = ("performance", "ablation")

# Canonical Test Status（只允许这些；SKIPPED 不得等价于 PASS）
VALID_TEST_STATUSES = ("PASS", "FAIL", "NOT_RUN", "SKIPPED", "BLOCKED")

# Release 必须提供 QA 证据的阶段
REQUIRED_QA_STAGES = (
    "static_qa",
    "rendered_qa",
    "post_processor",
    "final_artifact_qa",
)

# Governance 检查方式（F3：有限集合，保证审计稳定）
VALID_GOVERNANCE_MECHANISMS = (
    "manual-spec-review",
    "ai-assisted-spec-review",
    "automated-spec-check",
    "hybrid-review",
)


@dataclass
class ReleaseEvidence:
    """
    单次 Release Candidate 的完整证据。

    属性:
        software_version: 软件包版本（md_converter.__version__）
        spec_version / spec_status: Canonical Spec 版本与状态
        theme_version: 冻结主题版本
        commit: Git commit（非 git 仓库时为 "n/a"）
        build_id: 构建 ID
        checked_at: Governance Check 完成时间（ISO-8601）
        checked_by: 检查者（Reviewer / CI / checker）
        mechanism: 检查方式（VALID_GOVERNANCE_MECHANISMS）
        architecture_frozen: 架构是否冻结（None = NOT_CHECKED，无默认 True）
        unauthorized_spec_changes: 未经授权的 Spec 变更数（None = NOT_CHECKED）
        tests: 测试摘要（{suite: PASS|FAIL|NOT_RUN|SKIPPED|BLOCKED}）
        qa: 质量门状态（{stage: PASS|PASS_WITH_WARN|FAIL|NOT_RUN}）
        repair: 修复闭环摘要（remaining_errors 可为 None = UNKNOWN）
        regression: 回归摘要（status: CHECKED|NOT_CHECKED；new_failures 可为 None）
        known_warnings: 已知警告数
        spec_deviations: Spec 偏差数（None = NOT_CHECKED）
        artifact_sha256: 最终发布文件 hash（空 = 无证据）
        result: RELEASE_ELIGIBLE | RELEASE_BLOCKED
    """

    software_version: str = ""
    spec_version: str = SPEC_VERSION
    spec_status: str = SPEC_STATUS
    architecture_version: str = ARCHITECTURE_VERSION
    theme_version: str = THEME_VERSION
    acceptance_baseline: str = ACCEPTANCE_BASELINE
    governance_baseline: str = GOVERNANCE_BASELINE
    commit: str = "n/a"
    build_id: str = ""
    generated_at: str = ""
    checked_at: str = ""
    checked_by: str = ""
    mechanism: str = ""
    architecture_frozen: Optional[bool] = None
    unauthorized_spec_changes: Optional[int] = None
    tests: Dict[str, str] = field(default_factory=dict)
    qa: Dict[str, str] = field(default_factory=dict)
    repair: Dict[str, Any] = field(default_factory=dict)
    regression: Dict[str, Any] = field(
        default_factory=lambda: {"status": "NOT_CHECKED", "new_failures": None}
    )
    known_warnings: int = 0
    spec_deviations: Optional[int] = None
    artifact_sha256: str = ""
    output_path: str = ""
    result: str = "RELEASE_BLOCKED"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "software_version": self.software_version,
            "spec_version": self.spec_version,
            "spec_status": self.spec_status,
            "architecture_version": self.architecture_version,
            "theme_version": self.theme_version,
            "acceptance_baseline": self.acceptance_baseline,
            "governance_baseline": self.governance_baseline,
            "commit": self.commit,
            "build_id": self.build_id,
            "generated_at": self.generated_at,
            "checked_at": self.checked_at,
            "checked_by": self.checked_by,
            "mechanism": self.mechanism,
            "architecture_frozen": self.architecture_frozen,
            "unauthorized_spec_changes": self.unauthorized_spec_changes,
            "tests": self.tests,
            "qa": self.qa,
            "repair": self.repair,
            "regression": self.regression,
            "known_warnings": self.known_warnings,
            "spec_deviations": self.spec_deviations,
            "artifact_sha256": self.artifact_sha256,
            "output_path": self.output_path,
            "result": self.result,
        }

    def to_json(self, indent: int = 2) -> str:
        """导出 JSON（给程序使用）。"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def to_markdown(self) -> str:
        """导出 Markdown（给人 / ChatGPT Review 使用）。"""
        lines = [
            "Release Candidate",
            "=================",
            "",
            f"Software Version: {self.software_version}",
            f"Spec Version: {self.spec_version}",
            f"Spec Status: {self.spec_status}",
            f"Architecture Version: {self.architecture_version}",
            f"Theme Version: {self.theme_version}",
            f"Acceptance Baseline: {self.acceptance_baseline}",
            f"Governance Baseline: {self.governance_baseline}",
            f"Commit: {self.commit}",
            f"Build ID: {self.build_id}",
            f"Generated At: {self.generated_at}",
            "",
            "Governance:",
            f"  Checked At: {self.checked_at or 'NOT_CHECKED'}",
            f"  Checked By: {self.checked_by or 'NOT_CHECKED'}",
            f"  Mechanism: {self.mechanism or 'NOT_CHECKED'}",
            "",
            "Architecture:",
            "  Frozen: "
            + (
                "NOT_CHECKED"
                if self.architecture_frozen is None
                else "YES" if self.architecture_frozen else "NO"
            ),
            "  Unauthorized Spec Change: "
            + (
                "NOT_CHECKED"
                if self.unauthorized_spec_changes is None
                else str(self.unauthorized_spec_changes)
            ),
            "",
            "Tests:",
        ]
        normalized = normalize_test_evidence(self.tests)
        for suite in REQUIRED_TEST_SUITES:
            lines.append(f"  {suite}: {normalized.get(suite, 'NOT_RUN')}")
        extra = {k: v for k, v in normalized.items() if k not in REQUIRED_TEST_SUITES}
        for suite, status in sorted(extra.items()):
            lines.append(f"  {suite} (optional): {status}")
        lines.extend(
            [
                "",
                "QA:",
            ]
        )
        for stage, status in sorted(self.qa.items()):
            lines.append(f"  {stage}: {status}")
        lines.extend(
            [
                "",
                "Repair:",
                f"  Iterations: {self.repair.get('iterations', 0)}",
                "  Remaining Errors: "
                + (
                    "UNKNOWN"
                    if self.repair.get("remaining_errors") is None
                    else str(self.repair.get("remaining_errors"))
                ),
                "",
                "Regression:",
                f"  Status: {self.regression.get('status', 'NOT_CHECKED')}",
                "  Baseline: "
                + (
                    "UNKNOWN"
                    if not self.regression.get("baseline")
                    else str(self.regression.get("baseline"))
                ),
                "  Current: "
                + (
                    "UNKNOWN"
                    if not self.regression.get("current")
                    else str(self.regression.get("current"))
                ),
                "  New Failures: "
                + (
                    "UNKNOWN"
                    if self.regression.get("new_failures") is None
                    else str(self.regression.get("new_failures"))
                ),
                "",
                f"Known Warnings: {self.known_warnings}",
                "Spec Deviations: "
                + ("NOT_CHECKED" if self.spec_deviations is None else str(self.spec_deviations)),
                f"Artifact SHA256: {self.artifact_sha256}",
                "",
                "Result:",
                f"  {self.result}",
                "",
            ]
        )
        return "\n".join(lines)


def normalize_test_evidence(tests: Optional[Dict[str, str]]) -> Dict[str, str]:
    """
    归一化测试证据：Required Suite 缺失时补 ``NOT_RUN``。

    例如 ``{"unit": "PASS"}`` ->:
        unit=PASS, integration=NOT_RUN, golden=NOT_RUN, acceptance=NOT_RUN

    缺失键与 PASS 不存在任何默认等价关系。
    """
    src = dict(tests or {})
    result: Dict[str, str] = {}
    for suite in REQUIRED_TEST_SUITES:
        result[suite] = src.get(suite, "NOT_RUN")
    for suite, status in src.items():
        if suite not in REQUIRED_TEST_SUITES:
            result.setdefault(suite, status)
    return result


def validate_test_evidence(tests: Optional[Dict[str, str]]) -> List[str]:
    """
    校验测试证据 schema。

    返回:
        List[str]: 错误列表；空列表表示合法
    """
    if tests is None:
        return []
    if not isinstance(tests, dict):
        return ["test evidence must be a mapping"]
    errors: List[str] = []
    for suite, status in tests.items():
        if not isinstance(status, str) or status not in VALID_TEST_STATUSES:
            errors.append(
                f"invalid test status for '{suite}': {status!r} "
                f"(allowed: {', '.join(VALID_TEST_STATUSES)})"
            )
    return errors


def _is_valid_iso8601(value: Any) -> bool:
    """
    统一 ISO-8601 校验（C1）。

    空字符串、None、非 ISO-8601 文本（如 "yesterday" / "2026/08/31"）
    一律视为非法。
    """
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        datetime.fromisoformat(value)
        return True
    except ValueError:
        return False


def _is_non_negative_int(value: Any) -> bool:
    """统一非负整数校验（R1）：int、非 bool、>= 0。"""
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def validate_governance_evidence(data: Optional[Dict[str, Any]]) -> List[str]:
    """
    校验 Governance Evidence 输入（governance_evidence.json）。

    F1：所有治理计数必须是非负整数（负数会绕过 ``> 0`` Release Predicate）。
    F3：必须包含审计来源（checked_at / checked_by / mechanism）与
    regression baseline / current。

    返回:
        List[str]: 错误列表；空列表表示合法
    """
    if data is None:
        return ["governance evidence is required"]
    if not isinstance(data, dict):
        return ["governance evidence must be a mapping"]
    errors: List[str] = []
    if data.get("spec_version") != SPEC_VERSION:
        errors.append(f"spec_version mismatch: expected {SPEC_VERSION}")
    if data.get("spec_status") != SPEC_STATUS:
        errors.append(f"spec_status mismatch: expected {SPEC_STATUS}")

    # F3：审计来源（谁、何时、用什么方式检查）
    checked_at = data.get("checked_at")
    if not _is_valid_iso8601(checked_at):
        errors.append("checked_at must be a non-empty ISO-8601 timestamp")
    checked_by = data.get("checked_by")
    if not isinstance(checked_by, str) or not checked_by.strip():
        errors.append("checked_by must be a non-empty string")
    mechanism = data.get("mechanism")
    if mechanism not in VALID_GOVERNANCE_MECHANISMS:
        errors.append(f"mechanism must be one of: {', '.join(VALID_GOVERNANCE_MECHANISMS)}")

    if not isinstance(data.get("architecture_frozen"), bool):
        errors.append("architecture_frozen must be a boolean")

    # F1：非负整数（不允许负数绕过 Release Gate）
    for key in ("unauthorized_spec_changes", "spec_deviations"):
        value = data.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            errors.append(f"{key} must be a non-negative integer")

    regression = data.get("regression") or {}
    if regression.get("status") not in ("CHECKED", "NOT_CHECKED"):
        errors.append("regression.status must be CHECKED or NOT_CHECKED")
    regression_checked_at = regression.get("checked_at")
    if not _is_valid_iso8601(regression_checked_at):
        errors.append("regression.checked_at must be a non-empty ISO-8601 timestamp")
    for key in ("baseline", "current"):
        value = regression.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"regression.{key} is required")
    for key in ("baseline_failures", "current_failures", "new_failures"):
        if not _is_non_negative_int(regression.get(key)):
            errors.append(f"regression.{key} must be a non-negative integer")
    current_failures = regression.get("current_failures")
    new_failures = regression.get("new_failures")
    if (
        isinstance(current_failures, int)
        and isinstance(new_failures, int)
        and new_failures > current_failures
    ):
        errors.append("regression.new_failures cannot exceed current_failures")
    return errors


def compute_release_result(evidence: ReleaseEvidence) -> str:
    """
    由规则生成 Release Decision（Default Deny）。

    任一条件命中 -> RELEASE_BLOCKED:
        - Spec Status != FROZEN
        - Governance provenance 非法（checked_at 非 ISO-8601 /
          checked_by 空 / mechanism 非 Canonical）
        - Regression checked_at 非法或 baseline / current 缺失
        - Regression 计数非法（baseline/current/new failures 非负整数，
          new_failures <= current_failures，new_failures == 0）
        - Architecture Frozen 未检测（None）或 False
        - Unauthorized Spec Changes 非法（非负整数校验）或 != 0
        - Spec Deviations 非法（非负整数校验）或 != 0
        - 任一 Required Test Suite != PASS（缺失 = NOT_RUN = BLOCK）
        - 任一 Required QA Stage 缺失 / NOT_RUN / FAIL
          （post_processor 允许 PASS 或 NOT_REQUIRED）
        - Regression 未检测（status != CHECKED）或 new_failures 未知（None）/ != 0
        - Repair remaining_errors 非法（非负整数校验）或 != 0
        - Artifact SHA256 缺失

    核心语义：UNKNOWN 与 FAIL 在 Release Gate 中同样 BLOCK（Fail Closed）。
    """
    if evidence.spec_status != "FROZEN":
        return "RELEASE_BLOCKED"
    # C1：最终 Gate 重新验证 provenance（不信任 dataclass 类型提示，
    # 即使绕过 schema validator 直接构造 ReleaseEvidence 也必须 Fail Closed）
    if not _is_valid_iso8601(evidence.checked_at):
        return "RELEASE_BLOCKED"
    if not isinstance(evidence.checked_by, str) or not evidence.checked_by.strip():
        return "RELEASE_BLOCKED"
    if evidence.mechanism not in VALID_GOVERNANCE_MECHANISMS:
        return "RELEASE_BLOCKED"
    if evidence.architecture_frozen is not True:
        return "RELEASE_BLOCKED"
    # CP-GOV-FINAL-02：顶层 Governance 计数谓词对称——与 Regression / Repair
    # 使用同一 `_is_non_negative_int` 规则（int、非 bool、>= 0）后再要求 == 0，
    # 消除 `False == 0` / `0.0 == 0` 的直接构造绕过。
    if not _is_non_negative_int(evidence.unauthorized_spec_changes):
        return "RELEASE_BLOCKED"
    if evidence.unauthorized_spec_changes != 0:
        return "RELEASE_BLOCKED"
    if not _is_non_negative_int(evidence.spec_deviations):
        return "RELEASE_BLOCKED"
    if evidence.spec_deviations != 0:
        return "RELEASE_BLOCKED"

    normalized_tests = normalize_test_evidence(evidence.tests)
    for suite in REQUIRED_TEST_SUITES:
        if normalized_tests.get(suite) != "PASS":
            return "RELEASE_BLOCKED"

    for stage in REQUIRED_QA_STAGES:
        status = evidence.qa.get(stage)
        if stage == "post_processor":
            if status not in ("PASS", "NOT_REQUIRED"):
                return "RELEASE_BLOCKED"
        elif status not in ("PASS", "PASS_WITH_WARN"):
            return "RELEASE_BLOCKED"

    if evidence.regression.get("status") != "CHECKED":
        return "RELEASE_BLOCKED"
    if not _is_valid_iso8601(evidence.regression.get("checked_at")):
        return "RELEASE_BLOCKED"
    baseline = evidence.regression.get("baseline")
    if not isinstance(baseline, str) or not baseline.strip():
        return "RELEASE_BLOCKED"
    current = evidence.regression.get("current")
    if not isinstance(current, str) or not current.strip():
        return "RELEASE_BLOCKED"
    # R1：Regression Evidence 谓词对称——最终 Gate 重新校验全部计数，
    # 与 schema 使用同一 `_is_non_negative_int` 规则。
    baseline_failures = evidence.regression.get("baseline_failures")
    current_failures = evidence.regression.get("current_failures")
    new_failures = evidence.regression.get("new_failures")
    for value in (baseline_failures, current_failures, new_failures):
        if not _is_non_negative_int(value):
            return "RELEASE_BLOCKED"
    if new_failures > current_failures:
        return "RELEASE_BLOCKED"
    if new_failures != 0:
        return "RELEASE_BLOCKED"

    # CP-GOV-FINAL-01：Repair Evidence 谓词 Fail-Closed，与 Regression
    # 使用同一 `_is_non_negative_int` 规则（int、非 bool、>= 0），
    # 再要求严格 == 0。负数 / None / bool / 字符串 / 浮点均 BLOCK。
    remaining_errors = evidence.repair.get("remaining_errors")
    if not _is_non_negative_int(remaining_errors):
        return "RELEASE_BLOCKED"
    if remaining_errors != 0:
        return "RELEASE_BLOCKED"
    if not evidence.artifact_sha256:
        return "RELEASE_BLOCKED"
    return "RELEASE_ELIGIBLE"


def build_release_evidence(
    compiler: Any,
    output_path: Optional[Path] = None,
    commit: str = "n/a",
    build_id: Optional[str] = None,
    tests: Optional[Dict[str, str]] = None,
    governance: Optional[Dict[str, Any]] = None,
) -> ReleaseEvidence:
    """
    从编译结果构建 Release Evidence。

    Release Evidence 只读取/汇总证据，不制造证据：
    governance 缺失时各项保持 None / NOT_CHECKED，Release 将 BLOCK。

    参数:
        compiler: 已完成 compile() 的 CompilerContext
        output_path: 发布文件路径
        commit: Git commit（可选）
        build_id: 构建 ID（默认自动生成）
        tests: 测试摘要 {suite: PASS|FAIL|...}
        governance: Governance Evidence（governance_evidence.json 内容）

    返回:
        ReleaseEvidence: 完整证据

    异常:
        ValueError: test / governance 证据 schema 非法
    """
    from . import __version__

    report = compiler.get_quality_gate_report()
    normalized_tests = normalize_test_evidence(tests)
    test_errors = validate_test_evidence(normalized_tests)
    if test_errors:
        raise ValueError("Invalid test evidence: " + "; ".join(test_errors))
    governance = governance or {}
    if governance:
        # 提供了 governance 文件但 schema 非法 -> 拒绝
        governance_errors = validate_governance_evidence(governance)
        if governance_errors:
            raise ValueError("Invalid governance evidence: " + "; ".join(governance_errors))

    qa: Dict[str, str] = {}
    for stage in REQUIRED_QA_STAGES:
        stage_result = report.get(stage)
        qa[stage] = stage_result.get("status", "UNKNOWN") if stage_result else "NOT_RUN"

    rendered = report.get("rendered_qa") or {}
    final_qa = report.get("final_artifact_qa") or {}
    remaining_errors = len(rendered.get("errors", [])) + len(final_qa.get("errors", []))
    known_warnings = (
        len((report.get("static_qa") or {}).get("warnings", []))
        + len(rendered.get("warnings", []))
        + len(final_qa.get("warnings", []))
    )
    regression_input = governance.get("regression") or {}

    evidence = ReleaseEvidence(
        software_version=__version__,
        commit=commit,
        build_id=build_id or uuid.uuid4().hex[:12],
        generated_at=datetime.now(timezone.utc).isoformat(),
        checked_at=governance.get("checked_at", ""),
        checked_by=governance.get("checked_by", ""),
        mechanism=governance.get("mechanism", ""),
        tests=normalized_tests,
        qa=qa,
        architecture_frozen=governance.get("architecture_frozen"),
        unauthorized_spec_changes=governance.get("unauthorized_spec_changes"),
        spec_deviations=governance.get("spec_deviations"),
        repair={
            "iterations": len(report.get("repair_evidence", [])),
            "remaining_errors": remaining_errors,
            "max_repair_iterations": report.get("policy", {}).get("max_repair_iterations", 0),
            "records": report.get("repair_evidence", []),
        },
        regression={
            "status": regression_input.get("status", "NOT_CHECKED"),
            "checked_at": regression_input.get("checked_at"),
            "baseline": regression_input.get("baseline"),
            "current": regression_input.get("current"),
            "new_failures": regression_input.get("new_failures"),
            "baseline_failures": regression_input.get("baseline_failures"),
            "current_failures": regression_input.get("current_failures"),
        },
        known_warnings=known_warnings,
        artifact_sha256=report.get("artifact_sha256", ""),
        output_path=str(output_path) if output_path else "",
    )
    evidence.result = compute_release_result(evidence)
    return evidence


def write_release_evidence(
    evidence: ReleaseEvidence,
    directory: Path,
) -> "tuple[Path, Path]":
    """
    写出 RELEASE_EVIDENCE.md 与 release_evidence.json。

    参数:
        evidence: 发布证据
        directory: 输出目录

    返回:
        tuple[Path, Path]: (markdown 路径, json 路径)
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    md_path = directory / "RELEASE_EVIDENCE.md"
    json_path = directory / "release_evidence.json"
    md_path.write_text(evidence.to_markdown(), encoding="utf-8")
    json_path.write_text(evidence.to_json(), encoding="utf-8")
    return md_path, json_path
