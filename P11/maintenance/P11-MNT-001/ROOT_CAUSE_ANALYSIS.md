# P11 Root Cause Analysis — P11-MNT-001

## Artifact Header

| Field | Value |
| --- | --- |
| Plan | P11_AGENT_PLAN_B — Maintenance Change Package Execution |
| Work Package | P11-MNT-001 |
| Authority | `Doc/Phase_11_Maintenance_Specification.md` v1.0（§9 Root Cause Gate） |
| Date | 2026-09-04 |
| Conclusion | **ROOT CAUSE VERIFIED FOR TEST DESIGN DEFECT**（COM environmental intermittency 仍为 residual risk） |
| Confidence | SUPPORTED（针对 test design defect；非 "100% proven permanent Word COM defect"） |

---

# 1. Verified Facts

```text
Verified Fact 1:
pre-fix 版本在 module level 求值
pytestmark = pytest.mark.skipif(not _word_com_reachable(), ...)
即 _word_com_reachable() 在 pytest collection / module import 阶段执行。

Verified Fact 2:
_word_com_reachable() 调用 win32com.client.DispatchEx("Word.Application")，
并在同一函数内初始化 Visible / DisplayAlerts 后 Quit —— 即完整启动 /
关闭 Word COM lifecycle。

Verified Fact 3:
历史 fatal stack 指向:
md_converter/tests/test_word_com_final_artifact.py
  _word_com_reachable()
  <module>
即 fatal 发生地点为 pytest collection 期间的模块导入路径。

Verified Fact 4:
strict review merger 将 "Windows fatal exception" / 0x800706be /
0x800706ba 视为 pytest fatal signature；即使 pytest rc=0 仍判 FAIL。
```

---

# 2. Hypothesis

```text
Hypothesis:
Word COM startup / shutdown lifecycle 在 pytest collection 主进程内执行，
造成 intermittent RPC 不稳定（Windows fatal exception 0x800706be）；
该现象与外部 Word / Office / RPC 环境状态相关，无法保证每次复现。
```

---

# 3. Post-Fix Evidence

```text
Post-Fix Evidence 1（全量回归）:
Merged_Code\merged_MDC_phase11_foundation_review.txt
- HEAD: 42394ad3d3541a8a92a7a5790ae2d32af49e6abe
- 277 passed in 168.53s
- fatal COM signature = 0
- merger validation all PASS

Post-Fix Evidence 2（collection 隔离）:
module-level COM probe 已移除；探测仅经 subprocess 于 test runtime fixture
中执行（pytest collection 不再启动 Word COM lifecycle）。

Post-Fix Evidence 3（真实生产路径保留）:
test 仍执行 CompilerContext.create({"word_com": True}) -> compile ->
FinalArtifactQA，未降级为 silent skip。
```

---

# 4. Conclusion

```text
ROOT CAUSE VERIFIED FOR TEST DESIGN DEFECT:
pytest collection 期 Word COM availability probe lifecycle 是本次 test
defect 的根因。修复方向正确：把 probe 移出 collection 主进程，隔离到
subprocess 并在 test runtime 执行。

Residual Risk:
Word COM 属于外部 Windows / Office 自动化依赖；intermittent environmental
RPC instability 无法被数学性消除，但 collection-time lifecycle coupling
已被移除，fatal 暴露窗口已收窄至真实 integration test runtime。

Not Claimed:
- 不声称 Word COM 环境缺陷已被永久修复
- 不声称 fatal 不可能再出现
- 不将环境偶发性转成 silent skip（fail-closed 保留）
```
