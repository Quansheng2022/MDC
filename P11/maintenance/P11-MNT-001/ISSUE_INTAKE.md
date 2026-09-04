# P11 Issue Intake — P11-MNT-001

## Artifact Header

| Field | Value |
| --- | --- |
| Plan | P11_AGENT_PLAN_B — Maintenance Change Package Execution |
| Work Package | P11-MNT-001 |
| Authority | `Doc/Phase_11_Maintenance_Specification.md` v1.0（§5 / §7 / §9） |
| Canonical | `CANONICAL_SPEC.md` v1.0 FROZEN |
| Intake Date | 2026-09-04 |
| Registry Status | OPEN（登记完成；Classification / Severity 已确认；等待 Human Gate HG-B4） |

---

```text
Issue ID:
P11-MNT-001

Title:
Isolate Word COM Availability Probe from Pytest Collection

Reporter / Source:
PLAN_A final validation 发现的真实 issue。
执行命令：
python tools/review/merge_project_for_phase11_review.py
    --mode foundation
    --run-pytest
    --strict

Detected Version:
v1.0.0 maintenance line

Environment:
Windows + installed Word + pywin32（外部 COM/RPC 依赖）；
Python 3.12.13 / pytest 9.1.1（据 RC_EVIDENCE\P10_COM01\P10_COM01_before.txt）

Affected Component:
md_converter/tests/test_word_com_final_artifact.py

Problem Statement:
Word COM availability probe 在 pytest collection / module import 阶段直接执行
DispatchEx("Word.Application")，可能在 pytest 主进程内触发 Windows fatal
exception（0x800706be / RPC），而 pytest 仍返回 rc=0；strict review merger
检测到 fatal signature 后判定 FAIL，release / regression evidence trust 受损。

Observed Evidence:
- Windows fatal exception: code 0x800706be
- Stack: test_word_com_final_artifact.py -> _word_com_reachable() -> <module>
  （pytest collection / module import）
- pytest: 277 passed（rc=0）
- Merger（strict）: FAIL，因为 fatal signature 被检测到

Initial Expected Behavior Source:
P11 Test Matrix §5 Runtime / Word COM Gate：
- pytest collection 不得启动 Word COM startup / shutdown lifecycle
- COM integration behavior 仍须经真实生产路径测试
- 不得因 COM 环境偶发性把 required test 改为 silent skip

Initial Actual Behavior:
Module-level skipif 求值期间执行 _word_com_reachable() ->
DispatchEx("Word.Application")；Word COM lifecycle 在 pytest collection
阶段启动，并可能输出 Windows fatal RPC signature。

Reproduction Available:
YES（历史失败证据 + 修复后证据均已存档；fatal 本身为 intermittent，
但 collection 期启动 COM lifecycle 的设计缺陷可确定性确认）

Proposed Classification:
TEST_DEFECT

Proposed Severity:
P2 Major

Potential P12 Boundary:
NO

Status:
OPEN
```

---

# 1. Classification Gate（B-03）

```text
Classification:
TEST_DEFECT

理由:
- Product behavior unchanged（产品编译 / 渲染 / 输出语义不变）
- Canonical semantics unchanged
- Architecture unchanged
- Failure originates in test infrastructure lifecycle（pytest collection 期 COM probe）

若审查发现实际需要产品行为变更:
STOP
RECLASSIFY
```

---

# 2. Severity Gate（B-04）

```text
Severity:
P2 Major

理由:
- pytest rc=0 但存在 fatal Windows COM diagnostic -> 原 review tool 可出现 false PASS
- 破坏 release / regression evidence trust
- 不直接造成产品数据损坏
- 不属于安全漏洞

判定依据与 P11_SEVERITY_RULES.md 一致:
user impact / correctness impact / availability impact / frequency
（禁止依据 LOC / effort / AI confidence 未使用）
```

---

# 3. Governance Sequence Note

```text
Historical Approval Before Patch:
NO / NOT RECORDED

Governance Sequence Deviation:
YES

Reason:
TEST_DEFECT 在 PLAN_A final validation 期间被发现，bounded test correction
已于正式 Change Package 创建前完成并提交（42394ad）。

Current Action:
Retrospective governance reconciliation。

No further implementation changes are authorized until HG-B4。
```

详细记录见 `CHANGE_PACKAGE.md`。
