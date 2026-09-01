"""
Release Evidence 测试（P1-10）。
"""

import json
from pathlib import Path

import pytest

from md_converter.compiler import CompilerContext
from md_converter.release_evidence import (
    REQUIRED_TEST_SUITES,
    ReleaseEvidence,
    build_release_evidence,
    compute_release_result,
    normalize_test_evidence,
    validate_governance_evidence,
    validate_test_evidence,
    write_release_evidence,
)

FULL_TEST_SUITES = {
    "unit": "PASS",
    "integration": "PASS",
    "golden": "PASS",
    "acceptance": "PASS",
}


GOVERNANCE_OK = {
    "spec_version": "1.0",
    "spec_status": "FROZEN",
    "checked_at": "2026-08-30T15:30:00+08:00",
    "checked_by": "Codex governance compliance check",
    "mechanism": "ai-assisted-spec-review",
    "architecture_frozen": True,
    "unauthorized_spec_changes": 0,
    "spec_deviations": 0,
    "regression": {
        "status": "CHECKED",
        "checked_at": "2026-08-30T15:30:00+08:00",
        "baseline": "v1.0.0-baseline",
        "current": "RC-20260830-01",
        "baseline_failures": 0,
        "current_failures": 0,
        "new_failures": 0,
    },
}


def _eligible_evidence() -> ReleaseEvidence:
    evidence = ReleaseEvidence(
        checked_at="2026-08-30T15:30:00+08:00",
        checked_by="Codex governance compliance check",
        mechanism="ai-assisted-spec-review",
        architecture_frozen=True,
        unauthorized_spec_changes=0,
        spec_deviations=0,
        tests={"unit": "PASS", "integration": "PASS", "golden": "PASS", "acceptance": "PASS"},
        qa={
            "static_qa": "PASS",
            "rendered_qa": "PASS",
            "post_processor": "PASS",
            "final_artifact_qa": "PASS",
        },
        repair={"iterations": 0, "remaining_errors": 0},
        regression={
            "status": "CHECKED",
            "checked_at": "2026-08-30T15:30:00+08:00",
            "baseline": "v1.0.0-baseline",
            "current": "RC-20260830-01",
            "baseline_failures": 0,
            "current_failures": 0,
            "new_failures": 0,
        },
        artifact_sha256="a" * 64,
    )
    evidence.result = compute_release_result(evidence)
    return evidence


def test_compute_result_eligible() -> None:
    """全部通过 -> RELEASE_ELIGIBLE。"""
    assert compute_release_result(_eligible_evidence()) == "RELEASE_ELIGIBLE"


def test_compute_result_blocked_on_qa_failure() -> None:
    """质量门 FAIL -> RELEASE_BLOCKED。"""
    evidence = _eligible_evidence()
    evidence.qa["final_artifact_qa"] = "FAIL"
    assert compute_release_result(evidence) == "RELEASE_BLOCKED"


def test_compute_result_blocked_on_spec_deviation() -> None:
    """Spec Deviations > 0 -> RELEASE_BLOCKED。"""
    evidence = _eligible_evidence()
    evidence.spec_deviations = 1
    assert compute_release_result(evidence) == "RELEASE_BLOCKED"


def test_compute_result_blocked_on_remaining_errors() -> None:
    """修复后仍有剩余 error -> RELEASE_BLOCKED。"""
    evidence = _eligible_evidence()
    evidence.repair["remaining_errors"] = 1
    assert compute_release_result(evidence) == "RELEASE_BLOCKED"


@pytest.mark.parametrize(
    "tests,expected",
    [
        ({}, "RELEASE_BLOCKED"),  # 空 tests
        ({"unit": "PASS"}, "RELEASE_BLOCKED"),  # 只有 unit
        ({"unit": "PASS", "integration": "PASS"}, "RELEASE_BLOCKED"),  # 缺 golden/acceptance
        (
            {"unit": "PASS", "integration": "PASS", "acceptance": "PASS"},
            "RELEASE_BLOCKED",
        ),  # 缺 golden
        (
            {"unit": "PASS", "integration": "PASS", "golden": "FAIL", "acceptance": "PASS"},
            "RELEASE_BLOCKED",
        ),  # golden=FAIL
        (
            {"unit": "PASS", "integration": "PASS", "golden": "SKIPPED", "acceptance": "PASS"},
            "RELEASE_BLOCKED",
        ),  # golden=SKIPPED（不得等价 PASS）
        (
            {"unit": "PASS", "integration": "PASS", "golden": "PASS", "acceptance": "NOT_RUN"},
            "RELEASE_BLOCKED",
        ),  # acceptance=NOT_RUN
        (
            {"unit": "PASS", "integration": "PASS", "golden": "PASS", "acceptance": "PASS"},
            "RELEASE_ELIGIBLE",
        ),  # 4 suite 全 PASS
    ],
    ids=[
        "empty",
        "unit_only",
        "unit_plus_integration",
        "missing_golden",
        "golden_fail",
        "golden_skipped",
        "acceptance_not_run",
        "all_required_pass",
    ],
)
def test_release_tests_evidence_matrix(tests, expected) -> None:
    """Required Suite 缺失/非 PASS 一律 BLOCK；全 PASS 才 Eligible。"""
    evidence = _eligible_evidence()
    evidence.tests = tests
    assert compute_release_result(evidence) == expected


def test_optional_suite_not_run_does_not_block() -> None:
    """optional performance=NOT_RUN 不阻断 Release。"""
    evidence = _eligible_evidence()
    evidence.tests["performance"] = "NOT_RUN"
    assert compute_release_result(evidence) == "RELEASE_ELIGIBLE"


def test_normalize_test_evidence_fills_missing_required() -> None:
    """缺失的 Required Suite 补 NOT_RUN。"""
    normalized = normalize_test_evidence({"unit": "PASS"})
    assert normalized == {
        "unit": "PASS",
        "integration": "NOT_RUN",
        "golden": "NOT_RUN",
        "acceptance": "NOT_RUN",
    }
    assert set(REQUIRED_TEST_SUITES) <= set(normalized)


@pytest.mark.parametrize(
    "status",
    ["OK", "SUCCESS", "passed", "PASSED", "skipped", 1],
)
def test_validate_test_evidence_rejects_non_canonical_status(status) -> None:
    """非 Canonical Status 必须 schema reject，不得默默接受。"""
    errors = validate_test_evidence({"unit": status})
    assert errors


def test_validate_test_evidence_accepts_canonical_statuses() -> None:
    """Canonical Status 全部合法。"""
    errors = validate_test_evidence(
        {"unit": "PASS", "integration": "FAIL", "golden": "NOT_RUN", "acceptance": "SKIPPED"}
    )
    assert errors == []


def test_build_release_evidence_from_compiler(tmp_path: Path) -> None:
    """真实编译后构建证据：4 个 Required Suite 全 PASS -> ELIGIBLE。"""
    ctx = CompilerContext.create({"word_com": False})
    out = tmp_path / "evidence.docx"
    ctx.compile("# Title\n\nbody text", None, out)

    evidence = build_release_evidence(
        ctx,
        out,
        tests={
            "unit": "PASS",
            "integration": "PASS",
            "golden": "PASS",
            "acceptance": "PASS",
        },
        governance=GOVERNANCE_OK,
    )

    assert evidence.software_version == "1.0.0"
    assert evidence.spec_version == "1.0"
    assert evidence.spec_status == "FROZEN"
    assert evidence.theme_version == "QS-Word-Default-V1.5"
    assert evidence.qa["static_qa"] == "PASS"
    assert evidence.qa["rendered_qa"] in ("PASS", "PASS_WITH_WARN")
    assert evidence.qa["final_artifact_qa"] == "PASS"
    assert evidence.artifact_sha256
    assert evidence.result == "RELEASE_ELIGIBLE"


def test_build_release_evidence_incomplete_tests_blocked(tmp_path: Path) -> None:
    """真实编译 + 仅 unit/acceptance 证据 -> RELEASE_BLOCKED。"""
    ctx = CompilerContext.create({"word_com": False})
    out = tmp_path / "evidence2.docx"
    ctx.compile("# Title\n\nbody text", None, out)

    evidence = build_release_evidence(
        ctx,
        out,
        tests={"unit": "PASS", "acceptance": "PASS"},
        governance=GOVERNANCE_OK,
    )
    assert evidence.tests["integration"] == "NOT_RUN"
    assert evidence.tests["golden"] == "NOT_RUN"
    assert evidence.result == "RELEASE_BLOCKED"


# ============================================================
# 修改项 3：Measured Governance Evidence（GOV 矩阵）
# ============================================================


def test_build_release_evidence_missing_governance_blocked(tmp_path: Path) -> None:
    """GOV-01: governance evidence 缺失 -> RELEASE_BLOCKED（Default Deny）。"""
    ctx = CompilerContext.create({"word_com": False})
    out = tmp_path / "evidence3.docx"
    ctx.compile("# Title\n\nbody text", None, out)

    evidence = build_release_evidence(
        ctx,
        out,
        tests={
            "unit": "PASS",
            "integration": "PASS",
            "golden": "PASS",
            "acceptance": "PASS",
        },
        governance=None,
    )
    assert evidence.architecture_frozen is None
    assert evidence.unauthorized_spec_changes is None
    assert evidence.spec_deviations is None
    assert evidence.regression["status"] == "NOT_CHECKED"
    assert evidence.result == "RELEASE_BLOCKED"


@pytest.mark.parametrize(
    "mutate,expected",
    [
        (lambda e: setattr(e, "architecture_frozen", None), "RELEASE_BLOCKED"),  # GOV-02
        (lambda e: setattr(e, "architecture_frozen", False), "RELEASE_BLOCKED"),  # GOV-03
        (
            lambda e: setattr(e, "unauthorized_spec_changes", None),
            "RELEASE_BLOCKED",
        ),  # GOV-04
        (
            lambda e: setattr(e, "unauthorized_spec_changes", 1),
            "RELEASE_BLOCKED",
        ),  # GOV-05
        (lambda e: setattr(e, "spec_deviations", None), "RELEASE_BLOCKED"),  # GOV-06
        (lambda e: setattr(e, "spec_deviations", 1), "RELEASE_BLOCKED"),  # GOV-07
        (
            lambda e: e.regression.update({"status": "NOT_CHECKED"}),
            "RELEASE_BLOCKED",
        ),  # GOV-08
        (
            lambda e: e.regression.update({"new_failures": None}),
            "RELEASE_BLOCKED",
        ),  # GOV-09
        (
            lambda e: e.regression.update({"new_failures": 1}),
            "RELEASE_BLOCKED",
        ),  # GOV-10
        (lambda e: setattr(e, "spec_status", "DRAFT"), "RELEASE_BLOCKED"),
        (lambda e: e.qa.pop("final_artifact_qa"), "RELEASE_BLOCKED"),
        (lambda e: setattr(e, "artifact_sha256", ""), "RELEASE_BLOCKED"),
        (lambda e: setattr(e, "repair", {"remaining_errors": None}), "RELEASE_BLOCKED"),
    ],
    ids=[
        "gov02_arch_frozen_none",
        "gov03_arch_frozen_false",
        "gov04_unauthorized_none",
        "gov05_unauthorized_gt0",
        "gov06_spec_deviations_none",
        "gov07_spec_deviations_gt0",
        "gov08_regression_not_checked",
        "gov09_new_failures_none",
        "gov10_new_failures_gt0",
        "spec_status_draft",
        "qa_stage_missing",
        "artifact_sha_missing",
        "repair_remaining_unknown",
    ],
)
def test_governance_decision_matrix(mutate, expected) -> None:
    """GOV 决策矩阵：任何治理证据未检测/异常均 BLOCK。"""
    evidence = _eligible_evidence()
    mutate(evidence)
    assert compute_release_result(evidence) == expected


def test_governance_all_measured_eligible() -> None:
    """GOV-11/12: 治理证据齐全 + 测试/QA 全 PASS -> RELEASE_ELIGIBLE。"""
    evidence = _eligible_evidence()
    assert evidence.architecture_frozen is True
    assert evidence.unauthorized_spec_changes == 0
    assert evidence.spec_deviations == 0
    assert evidence.regression["status"] == "CHECKED"
    assert evidence.regression["new_failures"] == 0
    assert compute_release_result(evidence) == "RELEASE_ELIGIBLE"


def test_validate_governance_evidence_rejects_missing() -> None:
    """governance 缺失/非法 -> schema reject。"""
    assert validate_governance_evidence(None)
    assert validate_governance_evidence({})
    assert validate_governance_evidence({"spec_version": "9.9"})


def test_validate_governance_evidence_accepts_ok() -> None:
    """合法 governance evidence -> 无错误。"""
    assert validate_governance_evidence(GOVERNANCE_OK) == []


def test_markdown_shows_unknown_when_not_checked(tmp_path: Path) -> None:
    """未检测的治理证据在 Markdown 中显示 NOT_CHECKED / UNKNOWN，而非 0。"""
    evidence = ReleaseEvidence(
        tests={"unit": "PASS"},
        qa={"static_qa": "PASS", "rendered_qa": "PASS", "final_artifact_qa": "PASS"},
        repair={"remaining_errors": 0},
    )
    md_text = evidence.to_markdown()
    assert "Checked At: NOT_CHECKED" in md_text
    assert "Checked By: NOT_CHECKED" in md_text
    assert "Mechanism: NOT_CHECKED" in md_text
    assert "Frozen: NOT_CHECKED" in md_text
    assert "Unauthorized Spec Change: NOT_CHECKED" in md_text
    assert "Spec Deviations: NOT_CHECKED" in md_text
    assert "Status: NOT_CHECKED" in md_text
    assert "Baseline: UNKNOWN" in md_text
    assert "Current: UNKNOWN" in md_text
    assert "New Failures: UNKNOWN" in md_text
    assert "integration: NOT_RUN" in md_text
    assert "golden: NOT_RUN" in md_text
    assert "RELEASE_BLOCKED" in md_text


# ============================================================
# F1：负数绕过防御（GOV-NEG + Defense-in-Depth）
# ============================================================


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d.update({"unauthorized_spec_changes": -1}),  # GOV-NEG-01
        lambda d: d.update({"spec_deviations": -1}),  # GOV-NEG-02
        lambda d: d["regression"].update({"new_failures": -1}),  # GOV-NEG-03
        lambda d: d["regression"].update({"baseline_failures": -1}),  # GOV-NEG-04
        lambda d: d["regression"].update({"current_failures": -1}),  # GOV-NEG-05
        lambda d: d["regression"].update({"new_failures": 8, "current_failures": 1}),  # GOV-NEG-06
    ],
    ids=[
        "neg01_unauthorized_negative",
        "neg02_spec_deviations_negative",
        "neg03_new_failures_negative",
        "neg04_baseline_failures_negative",
        "neg05_current_failures_negative",
        "neg06_new_exceeds_current",
    ],
)
def test_governance_negative_schema_rejected(mutate) -> None:
    """负数 / 不一致回归值必须在 schema 层被拒绝（schema escaped = 0）。"""
    data = json.loads(json.dumps(GOVERNANCE_OK))
    mutate(data)
    assert validate_governance_evidence(data)


@pytest.mark.parametrize(
    "attr,value",
    [
        ("unauthorized_spec_changes", -1),
        ("spec_deviations", -1),
    ],
)
def test_direct_negative_governance_cannot_bypass_gate(attr, value) -> None:
    """绕过 validator 直接构造负数 -> Release Predicate 必须 BLOCK。"""
    evidence = _eligible_evidence()
    setattr(evidence, attr, value)
    assert compute_release_result(evidence) == "RELEASE_BLOCKED"


def test_direct_negative_new_failures_cannot_bypass_gate() -> None:
    """regression.new_failures = -1 直接构造 -> BLOCK（!= 0 predicate）。"""
    evidence = _eligible_evidence()
    evidence.regression["new_failures"] = -1
    assert compute_release_result(evidence) == "RELEASE_BLOCKED"


# ============================================================
# F2：PostProcessor 纳入 Release Evidence（POST-EVID）
# ============================================================


def test_post_processor_evidence_pass(tmp_path: Path) -> None:
    """POST-EVID-01: PostProcessor 成功 -> evidence 记录 PASS。"""
    ctx = CompilerContext.create({"word_com": False})
    out = tmp_path / "pp_ok.docx"
    ctx.compile("# Title\n\nbody text", None, out)

    assert ctx.get_quality_gate_report()["post_processor"]["status"] == "PASS"
    evidence = build_release_evidence(ctx, out, tests=FULL_TEST_SUITES, governance=GOVERNANCE_OK)
    assert evidence.qa["post_processor"] == "PASS"
    assert evidence.result == "RELEASE_ELIGIBLE"


def test_post_processor_evidence_not_required(tmp_path: Path) -> None:
    """POST-EVID-02: 全部后处理能力关闭 -> NOT_REQUIRED，不阻塞。"""
    ctx = CompilerContext.create(
        {"word_com": False, "enable_cover": False, "toc": False, "style_tables": False}
    )
    out = tmp_path / "pp_none.docx"
    ctx.compile("# Title\n\nbody text", None, out)

    report = ctx.get_quality_gate_report()
    assert report["post_processor"]["status"] == "NOT_REQUIRED"
    assert report["post_processor"]["required"] is False
    evidence = build_release_evidence(ctx, out, tests=FULL_TEST_SUITES, governance=GOVERNANCE_OK)
    assert evidence.qa["post_processor"] == "NOT_REQUIRED"
    assert evidence.result == "RELEASE_ELIGIBLE"


@pytest.mark.parametrize(
    "status,expected",
    [
        ("NOT_RUN", "RELEASE_BLOCKED"),  # POST-EVID-04
        ("FAIL", "RELEASE_BLOCKED"),  # POST-EVID-05
        ("PASS", "RELEASE_ELIGIBLE"),  # POST-EVID-06
        ("NOT_REQUIRED", "RELEASE_ELIGIBLE"),  # POST-EVID-07
    ],
    ids=["not_run", "fail", "pass", "not_required"],
)
def test_post_processor_stage_decision(status, expected) -> None:
    """PostProcessor 状态决策表（PASS/NOT_REQUIRED 放行，其余 BLOCK）。"""
    evidence = _eligible_evidence()
    evidence.qa["post_processor"] = status
    assert compute_release_result(evidence) == expected


def test_post_processor_missing_stage_blocks() -> None:
    """POST-EVID-03: required post_processor 证据缺失 -> BLOCK。"""
    evidence = _eligible_evidence()
    evidence.qa.pop("post_processor")
    assert compute_release_result(evidence) == "RELEASE_BLOCKED"


# ============================================================
# F3：Governance 审计元数据（GOV-AUD）
# ============================================================


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d.pop("checked_at"),  # GOV-AUD-01
        lambda d: d.update({"checked_at": "yesterday"}),  # GOV-AUD-02
        lambda d: d.update({"checked_by": "  "}),  # GOV-AUD-03
        lambda d: d.update({"mechanism": "made-up-review"}),  # GOV-AUD-04
        lambda d: d["regression"].pop("baseline"),  # GOV-AUD-05
        lambda d: d["regression"].pop("current"),  # GOV-AUD-06
    ],
    ids=[
        "aud01_checked_at_missing",
        "aud02_invalid_timestamp",
        "aud03_checked_by_empty",
        "aud04_mechanism_unknown",
        "aud05_regression_baseline_missing",
        "aud06_regression_current_missing",
    ],
)
def test_governance_audit_schema_rejected(mutate) -> None:
    """审计元数据缺失/非法 -> schema reject。"""
    data = json.loads(json.dumps(GOVERNANCE_OK))
    mutate(data)
    assert validate_governance_evidence(data)


def test_governance_audit_complete_accepted() -> None:
    """GOV-AUD-07: 完整审计元数据 -> accepted。"""
    assert validate_governance_evidence(GOVERNANCE_OK) == []


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d.update({"checked_at": "yesterday"}),  # 顶层非法 ISO
        lambda d: d.update({"checked_at": "2026/08/31"}),  # 非 ISO-8601 格式
        lambda d: d["regression"].pop("checked_at"),  # regression checked_at 缺失
        lambda d: d["regression"].update({"checked_at": "not-a-time"}),  # 非法
    ],
    ids=[
        "schema_top_checked_at_invalid",
        "schema_top_checked_at_slash_format",
        "schema_regression_checked_at_missing",
        "schema_regression_checked_at_invalid",
    ],
)
def test_governance_provenance_schema_rejected(mutate) -> None:
    """provenance 非法（含 regression.checked_at）-> schema reject。"""
    data = json.loads(json.dumps(GOVERNANCE_OK))
    mutate(data)
    assert validate_governance_evidence(data)


# ============================================================
# C1：Final Predicate Defense-in-Depth（GOV-DI，绕过 validator）
# ============================================================


@pytest.mark.parametrize(
    "mutate",
    [
        lambda e: setattr(e, "checked_at", "yesterday"),  # GOV-DI-01
        lambda e: setattr(e, "checked_at", ""),  # GOV-DI-02
        lambda e: setattr(e, "mechanism", "made-up"),  # GOV-DI-03
        lambda e: setattr(e, "checked_by", "   "),  # GOV-DI-04
        lambda e: e.regression.pop("checked_at"),  # GOV-DI-05
        lambda e: e.regression.update({"checked_at": "invalid"}),  # GOV-DI-06
        lambda e: e.regression.update({"baseline": ""}),  # GOV-DI-07
        lambda e: e.regression.update({"current": "  "}),  # GOV-DI-08
    ],
    ids=[
        "di01_checked_at_invalid",
        "di02_checked_at_empty",
        "di03_mechanism_unknown",
        "di04_checked_by_blank",
        "di05_regression_checked_at_missing",
        "di06_regression_checked_at_invalid",
        "di07_regression_baseline_empty",
        "di08_regression_current_empty",
    ],
)
def test_final_predicate_rejects_bypassed_provenance(mutate) -> None:
    """
    GOV-DI-01..08：绕过 schema validator 直接构造 ReleaseEvidence，
    最终 Release Gate 仍必须 Fail Closed。
    """
    evidence = _eligible_evidence()
    mutate(evidence)
    assert compute_release_result(evidence) == "RELEASE_BLOCKED"


# ============================================================
# R1：Regression Evidence 谓词对称（REG-DI，绕过 validator）
# ============================================================


@pytest.mark.parametrize(
    "mutate",
    [
        lambda e: e.regression.update({"baseline_failures": -1}),  # REG-DI-01
        lambda e: e.regression.update({"current_failures": -1}),  # REG-DI-02
        lambda e: e.regression.update({"baseline_failures": "0"}),  # REG-DI-03
        lambda e: e.regression.update({"current_failures": None}),  # REG-DI-04
        lambda e: e.regression.update({"new_failures": -1}),  # REG-DI-05
        lambda e: e.regression.update({"new_failures": True}),  # REG-DI-06
        lambda e: e.regression.update({"current_failures": 1, "new_failures": 2}),  # REG-DI-07
    ],
    ids=[
        "di01_baseline_negative",
        "di02_current_negative",
        "di03_baseline_str",
        "di04_current_none",
        "di05_new_negative",
        "di06_new_bool",
        "di07_new_exceeds_current",
    ],
)
def test_final_predicate_rejects_malformed_regression_counts(mutate) -> None:
    """非法 Regression 计数直接构造 -> Final Gate 必须 BLOCK。"""
    evidence = _eligible_evidence()
    mutate(evidence)
    assert compute_release_result(evidence) == "RELEASE_BLOCKED"


def test_regression_fixed_failures_allowed() -> None:
    """REG-DI-08: 旧失败被修复（baseline=3, current=2, new=0）-> allowed。"""
    evidence = _eligible_evidence()
    evidence.regression.update({"baseline_failures": 3, "current_failures": 2, "new_failures": 0})
    assert compute_release_result(evidence) == "RELEASE_ELIGIBLE"


def test_regression_zero_counts_eligible_candidate() -> None:
    """REG-DI-09: baseline=0, current=0, new=0 -> RELEASE_ELIGIBLE candidate。"""
    evidence = _eligible_evidence()
    assert evidence.regression["baseline_failures"] == 0
    assert evidence.regression["current_failures"] == 0
    assert evidence.regression["new_failures"] == 0
    assert compute_release_result(evidence) == "RELEASE_ELIGIBLE"


# ============================================================
# CP-GOV-FINAL-01：Repair Evidence 谓词 Fail-Closed（REPAIR-DI）
# ============================================================


@pytest.mark.parametrize(
    "value",
    [
        -1,  # REPAIR-DI-01
        None,  # REPAIR-DI-02
        "0",  # REPAIR-DI-03
        True,  # REPAIR-DI-04
        False,  # REPAIR-DI-05
        0.0,  # REPAIR-DI-06
        1,  # REPAIR-DI-07
    ],
    ids=[
        "di01_negative",
        "di02_none",
        "di03_string_zero",
        "di04_true",
        "di05_false",
        "di06_float_zero",
        "di07_positive",
    ],
)
def test_final_predicate_rejects_invalid_remaining_errors(value) -> None:
    """REPAIR-DI-01..07：非法/非零 remaining_errors 直接构造 -> BLOCK。"""
    evidence = _eligible_evidence()
    evidence.repair["remaining_errors"] = value
    assert compute_release_result(evidence) == "RELEASE_BLOCKED"


def test_final_predicate_accepts_zero_remaining_errors() -> None:
    """REPAIR-DI-08: remaining_errors == 0 -> RELEASE_ELIGIBLE candidate。"""
    evidence = _eligible_evidence()
    evidence.repair["remaining_errors"] = 0
    assert compute_release_result(evidence) == "RELEASE_ELIGIBLE"


# ============================================================
# CP-GOV-FINAL-02：顶层 Governance Count 谓词对称（GOV-DI-COUNT）
# ============================================================


@pytest.mark.parametrize(
    "field,value",
    [
        ("unauthorized_spec_changes", False),  # GOV-DI-COUNT-01
        ("unauthorized_spec_changes", 0.0),  # GOV-DI-COUNT-02
        ("spec_deviations", False),  # GOV-DI-COUNT-03
        ("spec_deviations", 0.0),  # GOV-DI-COUNT-04
    ],
    ids=[
        "count01_unauthorized_false",
        "count02_unauthorized_float_zero",
        "count03_spec_deviations_false",
        "count04_spec_deviations_float_zero",
    ],
)
def test_final_predicate_rejects_malformed_governance_counts(field, value) -> None:
    """
    GOV-DI-COUNT-01..04：False / 0.0 直接构造（False==0、0.0==0 陷阱）
    -> Final Predicate 必须 BLOCK。
    """
    evidence = _eligible_evidence()
    setattr(evidence, field, value)
    assert compute_release_result(evidence) == "RELEASE_BLOCKED"


def test_zero_governance_counts_remain_eligible() -> None:
    """合法零计数必须保持 RELEASE_ELIGIBLE（防止 Fail Closed -> Everything Closed）。"""
    evidence = _eligible_evidence()
    evidence.unauthorized_spec_changes = 0
    evidence.spec_deviations = 0
    assert compute_release_result(evidence) == "RELEASE_ELIGIBLE"


def test_write_release_evidence_files(tmp_path: Path) -> None:
    """写出 RELEASE_EVIDENCE.md 与 release_evidence.json。"""
    evidence = _eligible_evidence()
    md_path, json_path = write_release_evidence(evidence, tmp_path)

    assert md_path.exists()
    assert json_path.exists()
    md_text = md_path.read_text(encoding="utf-8")
    assert "Release Candidate" in md_text
    assert "RELEASE_ELIGIBLE" in md_text

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["result"] == "RELEASE_ELIGIBLE"
    assert data["tests"]["acceptance"] == "PASS"
