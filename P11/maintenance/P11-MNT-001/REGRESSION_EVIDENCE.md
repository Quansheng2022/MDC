# P11 Regression Evidence — P11-MNT-001

## Artifact Header

| Field | Value |
| --- | --- |
| Plan | P11_AGENT_PLAN_B — Maintenance Change Package Execution |
| Work Package | P11-MNT-001 |
| Authority | `Doc/Phase_11_Maintenance_Specification.md` v1.0（§10 Test Matrix / §11） |
| Regression Date | 2026-09-04 |
| Result | **PASS — 277/277** |

---

# 1. B-11 — Full Regression Gate

```text
Command:
python -m pytest

Environment:
Python 3.12.14 / pytest 9.1.1 / Windows + Word COM（escalated 运行，
因 COM probe 需派生子进程）

HEAD SHA:
42394ad3d3541a8a92a7a5790ae2d32af49e6abe

Result:
277 passed in 495.97s (0:08:15)
Exit code: 0

Failed:          0
New Failure:     0
Required Skip:   0
Fatal COM:       0
Errors:          0
```

Golden / Acceptance guard（B-13）：

```text
Golden Test:        PASS（包含于 277/277）
Acceptance Test:    PASS（包含于 277/277）
Golden Modification:
0
Acceptance Modification:
0
```

---

# 2. B-12 — Maintenance-Mode Merger Gate（执行顺序说明）

冻结 merger strict 模式要求 Working Tree CLEAN（dirty -> WARN -> strict FAIL），
而 maintenance merged manifest 需包含本包证据文件。因此 B-12 在 Git Closure
commit（工作区 CLEAN）之后执行，快照记录 closed maintenance implementation
state；结果在 ratification record 中补充。

```text
Command:
python .\tools\review\merge_project_for_phase11_review.py
    --mode maintenance
    --run-pytest
    --strict

Result:
见 CLOSURE.md / GIT_CLOSURE.md（B-12 在 closure commit 后执行并记录）
```

---

# 3. 结论

```text
P11-MNT-001 Full Regression:
PASS — 277/277

New Failure:
0

Required Skip:
0

Fatal COM:
0
```
