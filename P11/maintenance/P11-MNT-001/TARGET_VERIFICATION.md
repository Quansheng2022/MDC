# P11 Target Verification — P11-MNT-001

## Artifact Header

| Field | Value |
| --- | --- |
| Plan | P11_AGENT_PLAN_B — Maintenance Change Package Execution |
| Work Package | P11-MNT-001 |
| Authority | `Doc/Phase_11_Maintenance_Specification.md` v1.0（§12 / §13） |
| Verification Date | 2026-09-04 |
| Result | **PASS — Dedicated Word COM 3/3，Fatal COM = 0，Unexpected Skip = 0** |

---

# 1. B-09 — Patch State Verification（Human Ratification 后，只读验证）

Human Gate HG-B4（2026-09-04）：**A — RATIFY EXISTING BOUNDED PATCH**。
现有 bounded patch commit：`42394ad3d3541a8a92a7a5790ae2d32af49e6abe`
（仅修改 `md_converter/tests/test_word_com_final_artifact.py`）。

```text
1. module-level Word COM probe removed
   PASS — pre-fix module-level
   pytestmark = pytest.mark.skipif(not _word_com_reachable(), ...)
   已移除；现无 collection / import 期 COM 启动。

2. COM probe isolated in subprocess
   PASS — _word_com_probe() 通过 subprocess.run([sys.executable, "-c",
   _WORD_COM_PROBE_CODE], ...) 在独立子进程执行探测。

3. fixture executes at runtime
   PASS — require_word_com（session-scope）fixture 仅在 test runtime 求值；
   pytest collection 不触发。

4. fatal probe state fail-closed
   PASS — probe 输出扫描 "Windows fatal exception" / 0x800706be /
   0x800706ba；timeout / unstable / unexpected -> "fail" -> pytest.fail；
   仅 Word/pywin32 不可用（WORD_COM_UNAVAILABLE）保留 skip 语义。

5. real integration path retained
   PASS — test 仍执行
   ctx = CompilerContext.create({"word_com": True})
   ctx.compile(markdown, None, out_path)
   并断言 FinalArtifactQA status == "PASS" 与 docx table borders。
```

Collection-only 佐证（2026-09-04）：

```text
Command:
python -m pytest .\md_converter\tests\test_word_com_final_artifact.py
    --collect-only -q
Result:
collected 1 item
无 Word COM 启动 / 无 fatal signature
```

---

# 2. B-10 — Dedicated Word COM Test Gate

## 2.1 执行环境说明（诚实记录）

首次按 PLAN_B 命令以 `-s` 运行遇到控制台编码伪影：

```text
Command:
python -m pytest .\md_converter\tests\test_word_com_final_artifact.py -vv -s

Observed:
UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f4ca'
（产品 post-processor 日志 print 含 emoji；cp1252 控制台无法编码）

判定:
执行环境编码伪影（console code page），非被测 COM 缺陷、非本包代码问题；
不影响 Word COM lifecycle 验证。以 PYTHONUTF8=1 规范化控制台编码后重跑。
```

## 2.2 Dedicated Run（-vv -s，UTF-8 控制台）

```text
Command:
$env:PYTHONUTF8='1'
python -m pytest .\md_converter\tests\test_word_com_final_artifact.py -vv -s

Result:
1 passed in 9.00s
Word COM 真实启动（probe subprocess + Word round-trip + TOC 刷新）
Fatal signature: 0
```

## 2.3 连续 3 次运行

```text
Command:
1..3 | ForEach-Object {
    python -m pytest .\md_converter\tests\test_word_com_final_artifact.py -q -s
    if ($LASTEXITCODE -ne 0) { throw "P11-MNT-001 targeted COM test failed" }
}

Run 1            PASS
Run 2            PASS
Run 3            PASS
Fatal Signature  0
Unexpected Skip  0
```

## 2.4 B-10 Verdict

```text
Targeted COM Test:
PASS — 3/3

Required Skip:
0

Fatal COM Signature:
0
```

---

# 3. 结论

```text
P11-MNT-001 Target Verification:
PASS

状态:
TARGET_VERIFIED（Registry 状态轨迹：OPEN -> VERIFIED -> CLOSED）
```
