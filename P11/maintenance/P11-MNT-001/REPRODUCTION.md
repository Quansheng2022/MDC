# P11 Reproduction Evidence — P11-MNT-001

## Artifact Header

| Field | Value |
| --- | --- |
| Plan | P11_AGENT_PLAN_B — Maintenance Change Package Execution |
| Work Package | P11-MNT-001 |
| Authority | `Doc/Phase_11_Maintenance_Specification.md` v1.0（§9 Root Cause Gate / §12） |
| Date | 2026-09-04 |
| Result | **CONFIRMED**（历史失败证据记录；设计缺陷经代码检视确认；修复后隔离经 evidence 验证） |

---

```text
Issue ID:
P11-MNT-001

Environment:
Windows + installed Word + pywin32（COM/RPC external dependency）；
Python 3.12.13 / pytest 9.1.1

Input:
md_converter/tests/test_word_com_final_artifact.py
pre-fix 形态：module-level
    pytestmark = pytest.mark.skipif(not _word_com_reachable(), ...)
其中 _word_com_reachable() 在 module import / collection 期间调用
win32com.client.DispatchEx("Word.Application")

Prerequisites:
- Windows 主机安装 Word + pywin32
- 以 Phase 11 review merger 执行 pytest（strict fatal detection）

Reproduction Steps:
1. 在 pre-fix commit 上执行:
   python tools/review/merge_project_for_phase11_review.py
       --mode foundation
       --run-pytest
       --strict
2. pytest collection 导入 test_word_com_final_artifact.py
3. module import 阶段求值 skipif -> _word_com_reachable()
   -> DispatchEx("Word.Application")
4. 观察 pytest / merger 输出中的 Windows fatal signature

Expected Behavior:
- pytest collection 不执行 Word COM startup / shutdown
- fatal signature = 0
- Word COM integration 仍在 test runtime 经真实生产路径验证
  （CompilerContext.create({"word_com": True}) -> compile -> FinalArtifactQA）

Expected Authority:
P11_TEST_MATRIX.md §5 Runtime / Word COM Gate
Doc/Phase_11_Maintenance_Specification.md v1.0（§10 / §12）

Actual Behavior:
- Windows fatal exception: code 0x800706be
- 栈: test_word_com_final_artifact.py -> _word_com_reachable -> <module>
  （module import / pytest collection 期间）
- pytest: 277 passed（rc=0）
- Merger（strict）: FAIL（fatal signature 被检测到）

Deviation:
pytest collection 阶段出现 Word COM lifecycle / fatal RPC diagnostic；
pytest rc=0 掩盖 fatal，破坏 evidence trust。

Evidence:
1. 历史同类 fatal（collection 期 module import）:
   RC_EVIDENCE\P10_COM01\P10_COM01_before.txt
   - "Windows fatal exception: code 0x800706be"
   - 栈含 test_word_com_final_artifact.py line 41 in <module>（collection）
2. PLAN_A final validation 失败记录（issue intake 引用）:
   merger --mode foundation --run-pytest --strict
   fatal stack 落在 _word_com_reachable() / <module>
3. Post-fix 全量回归 evidence:
   Merged_Code\merged_MDC_phase11_foundation_review.txt
   - Generated At: 2026-09-04T17:43:45+08:00
   - HEAD: 42394ad3d3541a8a92a7a5790ae2d32af49e6abe
   - Pytest: 277 passed in 168.53s
   - Fatal COM signature: 0
   - Validation: all PASS（RESULT: PASS）
4. Post-fix collection-only 检查（2026-09-04 18:07 +08）:
   python -m pytest .\md_converter\tests\test_word_com_final_artifact.py
       --collect-only -q
   - collected 1 item
   - 无 Word COM 启动 / 无 fatal signature

Deterministic:
NO（Word COM fatal 为 intermittent environmental RPC 现象）；
但 "pytest collection 期启动 Word COM lifecycle" 这一测试设计缺陷
经代码检视为确定性事实，不依赖偶发 fatal。

Reproduction Result:
CONFIRMED

Notes:
Word COM 仍是外部 Windows / Office 自动化依赖；修复移除的是
collection 期 lifecycle coupling，不能数学性消除环境 RPC 偶发性。
```
